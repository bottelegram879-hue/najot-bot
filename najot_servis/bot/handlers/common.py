"""/start, language, main menu, contacts, about, owner bootstrap, invitations."""
import hmac
import time
from pathlib import Path
import logging
from urllib.parse import quote_plus

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import config, parse_coords
from ..services import route_url
from ..db import Invite, Master, Owner, Setting, User, get_settings
from ..i18n import LANGS, all_variants, t
from ..ui import REMOVE_KB, btn, client_menu, h, lang_kb, markup, nav, show, url_btn

log = logging.getLogger(__name__)
router = Router(name="common")


async def render_home(event: Message | CallbackQuery, s: AsyncSession, user: User, lang: str, *, client: bool = False):
    if not client and user.role == "owner":
        from .owner import render_panel
        return await render_panel(event, s, user, lang)
    if not client and user.role == "master":
        from .master import render_panel as master_panel
        return await master_panel(event, s, user, lang)
    msg = await show(event, t(lang, "welcome"), client_menu(lang, user.role))
    await remember_menu(s, user, msg, lang)
    return msg


async def remember_menu(s: AsyncSession, user: User, msg, lang: str) -> None:
    """Keep the user's latest menu message so its «Записать» button can be re-pointed after a restart."""
    if msg is None or not getattr(msg, "message_id", None):
        return
    key = f"menu:{user.tg_id}"
    value = f"{msg.message_id}|{lang}|{user.role}|{int(time.time())}"
    row = await s.get(Setting, key)
    if row:
        row.value = value
    else:
        s.add(Setting(key=key, value=value))
    await s.commit()


async def accept_invite(message: Message, s: AsyncSession, user: User, token: str, bot: Bot) -> bool:
    inv = await s.scalar(select(Invite).where(Invite.token == token, Invite.used_by.is_(None)))
    if not inv:
        return False
    inv.used_by = user.id
    if user.role != "owner":
        user.role = "master"
    m = await s.scalar(select(Master).where(Master.user_id == user.id))
    if m:
        m.is_active = True
    else:
        s.add(Master(user_id=user.id, name=user.full_name or (user.username or str(user.tg_id))))
    await s.commit()
    if inv.created_by:
        creator = await s.get(User, inv.created_by)
        if creator:
            try:
                await bot.send_message(creator.tg_id, t(creator.lang, "inv_used_notify", name=h(user.full_name)))
            except Exception:
                log.warning("cannot notify invite creator")
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext, session: AsyncSession,
                    user: User, lang: str, bot: Bot):
    await state.clear()
    arg = (command.args or "").strip()
    if arg.startswith("m_"):
        ok = await accept_invite(message, session, user, arg[2:], bot)
        await message.answer(t(lang, "inv_ok" if ok else "inv_bad"), reply_markup=REMOVE_KB)
    # language choice always comes first after /start — with the NAJOT SERVIS logo
    caption = "🚛 <b>NAJOT SERVIS 24/7</b>\n\n" + "\n".join(t(c, "choose_lang") for c in LANGS)
    await send_logo(message.bot, session, message.chat.id, caption, lang_kb())


LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.jpg"


async def send_logo(bot: Bot, session: AsyncSession, chat_id: int, caption: str, kb=None) -> None:
    """Send the logo with a caption; the uploaded file_id is cached in settings to avoid re-uploading."""
    row = await session.get(Setting, "logo_file_id")
    try:
        if row:
            await bot.send_photo(chat_id, row.value, caption=caption, reply_markup=kb)
            return
        if LOGO_PATH.exists():
            msg = await bot.send_photo(chat_id, FSInputFile(LOGO_PATH), caption=caption, reply_markup=kb)
            if getattr(msg, "photo", None):
                session.add(Setting(key="logo_file_id", value=msg.photo[-1].file_id))
                await session.commit()
            return
    except Exception as e:  # cached id invalid (e.g. new bot token) — fall back to text
        log.warning("logo send failed: %s", e)
        if row:
            await session.delete(row)
            await session.commit()
    await bot.send_message(chat_id, caption, reply_markup=kb)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    await render_home(message, session, user, lang)


@router.message(Command("lang"))
async def cmd_lang(message: Message, lang: str):
    await message.answer(t(lang, "choose_lang"), reply_markup=lang_kb())


@router.message(Command("cancel"))
@router.message(F.text.in_(all_variants("btn_cancel")))
async def cmd_cancel(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    await message.answer(t(lang, "cancelled"), reply_markup=REMOVE_KB)
    await render_home(message, session, user, lang)


@router.message(Command("owner"))
async def cmd_owner(message: Message, command: CommandObject, session: AsyncSession, user: User, lang: str):
    code = (command.args or "").strip()
    if not config.owner_setup_code or not hmac.compare_digest(code, config.owner_setup_code):
        log.warning("bad owner code attempt from %s", user.tg_id)
        await message.answer(t(lang, "owner_bad"))
        return
    user.role = "owner"
    if not await session.scalar(select(Owner).where(Owner.user_id == user.id)):
        session.add(Owner(user_id=user.id))
    await session.commit()
    log.info("user %s became owner", user.tg_id)
    await message.answer(t(lang, "owner_ok"))
    await render_home(message, session, user, lang)


@router.message(Command("id"))
async def cmd_id(message: Message):
    await message.answer(f"🆔 <code>{message.from_user.id}</code>")


@router.callback_query(F.data.startswith("lang:"))
async def cb_lang(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User):
    code = cb.data.split(":", 1)[1]
    if code not in LANGS:
        return await cb.answer()
    user.lang = code
    await session.commit()
    await state.clear()
    await cb.answer(t(code, "lang_set"))
    await render_home(cb, session, user, code)


@router.callback_query(F.data == "home")
async def cb_home(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    await cb.answer()
    await render_home(cb, session, user, lang)


@router.callback_query(F.data == "menu:client")
async def cb_client_menu(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    await cb.answer()
    await render_home(cb, session, user, lang, client=True)


@router.callback_query(F.data == "noop")
async def cb_noop(cb: CallbackQuery):
    await cb.answer()


@router.callback_query(F.data == "menu:lang")
async def cb_menu_lang(cb: CallbackQuery, lang: str):
    await cb.answer()
    await show(cb, t(lang, "choose_lang"), markup(*lang_kb().inline_keyboard, nav(lang)))


@router.callback_query(F.data == "menu:about")
async def cb_about(cb: CallbackQuery, session: AsyncSession, lang: str):
    st = await get_settings(session)
    await cb.answer()
    text = t(lang, "about_text", hours=h(st["work_hours"]), phone=h(fmt_phone(st["phone"])),
             phone2=h(fmt_phone(st.get("phone2", ""))), address=h(st["address"]))
    kb = markup([btn(t(lang, "btn_book"), "bk:start")],
                [btn(t(lang, "btn_call"), "menu:call"), btn(t(lang, "btn_address"), "menu:address")], nav(lang))
    await send_logo(cb.bot, session, cb.from_user.id, text, kb)


def fmt_phone(p: str) -> str:
    """+998995492447 -> +998 99 549-24-47"""
    d = "".join(ch for ch in p or "" if ch.isdigit())
    if len(d) == 12 and d.startswith("998"):
        return f"+998 {d[3:5]} {d[5:8]}-{d[8:10]}-{d[10:12]}"
    return p


def contacts_kb(lang: str, st: dict):
    coords = parse_coords(st.get("location"))
    if coords:
        map_url = f"https://www.google.com/maps?q={coords[0]:.6f},{coords[1]:.6f}"
        route = [url_btn(t(lang, "btn_map"), map_url), url_btn(t(lang, "btn_route"), route_url(*coords))]
    else:
        route = [url_btn(t(lang, "btn_map"),
                         "https://www.google.com/maps/search/?api=1&query=" + quote_plus(st["address"] + ", Samarqand"))]
    return markup(
        [btn(t(lang, "btn_call"), "menu:call")],
        [url_btn(t(lang, "btn_tg"), f"https://t.me/{st['telegram']}"),
         url_btn(t(lang, "btn_ig"), f"https://instagram.com/{st['instagram']}")],
        route,
        nav(lang),
    )


@router.callback_query(F.data == "menu:address")
async def cb_address(cb: CallbackQuery, session: AsyncSession, lang: str):
    st = await get_settings(session)
    await cb.answer()
    await show(cb, t(lang, "contacts_text", address=h(st["address"]), phone=h(fmt_phone(st["phone"])),
                     phone2=h(fmt_phone(st.get("phone2", ""))),
                     telegram=h(st["telegram"]), instagram=h(st["instagram"]), hours=h(st["work_hours"])),
               contacts_kb(lang, st))
    coords = parse_coords(st.get("location"))
    if coords:
        await cb.message.answer_venue(latitude=coords[0], longitude=coords[1], title="🚛 NAJOT SERVIS",
                                      address=st["address"])


@router.callback_query(F.data == "menu:call")
async def cb_call(cb: CallbackQuery, session: AsyncSession, lang: str):
    """Telegram inline buttons can't open tel: links, so we send a contact card — tapping it starts a call."""
    st = await get_settings(session)
    await cb.answer()
    phones = [p for p in (st["phone"], st.get("phone2")) if p]
    await cb.message.answer(t(lang, "call_text", phone=h(", ".join(fmt_phone(p) for p in phones))))
    for i, p in enumerate(phones):
        await cb.message.answer_contact(phone_number=p, first_name="NAJOT SERVIS" + (f" {i + 1}" if i else ""),
                                        reply_markup=markup(nav(lang)) if i == len(phones) - 1 else None)
