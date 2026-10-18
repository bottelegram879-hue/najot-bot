"""Client: my requests, request card, history, cancellation, chat with the mechanic."""
import logging
import math

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import ACTIVE_STATUSES, STATUSES
from ..db import Request, User
from ..i18n import t
from ..services import (PermissionDenied, add_history, can_manage, can_view, change_status, get_request,
                        history_text, owners, request_card, send)
from ..ui import PAGE_SIZE, btn, h, markup, nav, pager, show

log = logging.getLogger(__name__)
router = Router(name="client")


class Chat(StatesGroup):
    to_staff = State()
    to_client = State()


def client_req_kb(r: Request, lang: str, back: str) -> object:
    rows = [[btn(t(lang, "btn_history"), f"rq:h:{r.id}")]]
    if r.status in ACTIVE_STATUSES:
        rows.append([btn(t(lang, "btn_contact_master"), f"cm:{r.id}")])
    if r.status in ("new", "accepted"):
        rows.append([btn(t(lang, "btn_cancel_request"), f"rq:cx:{r.id}")])
    rows.append(nav(lang, back))
    return markup(*rows)


@router.callback_query(F.data.startswith("menu:list:"))
async def cb_my_requests(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    page = int(cb.data.split(":")[2])
    total = await session.scalar(select(func.count(Request.id)).where(Request.client_user_id == user.id))
    await cb.answer()
    if not total:
        return await show(cb, t(lang, "no_requests"), markup([btn(t(lang, "btn_book"), "bk:start")], nav(lang)))
    pages = math.ceil(total / PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    rows = (await session.scalars(select(Request).where(Request.client_user_id == user.id)
                                  .order_by(Request.id.desc()).offset(page * PAGE_SIZE).limit(PAGE_SIZE))).all()
    kb = [[btn(f"{STATUSES[r.status]} {r.number} · {r.brand} {r.model}", f"rq:{r.id}")] for r in rows]
    kb.append(pager(lang, "menu:list", page, pages))
    kb.append(nav(lang))
    await show(cb, t(lang, "my_requests_title"), markup(*kb))


@router.callback_query(F.data == "menu:last")
async def cb_last(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    r = await session.scalar(select(Request).where(Request.client_user_id == user.id,
                                                   Request.status.in_(ACTIVE_STATUSES)).order_by(Request.id.desc()))
    if r is None:
        r = await session.scalar(select(Request).where(Request.client_user_id == user.id).order_by(Request.id.desc()))
    await cb.answer()
    if r is None:
        return await show(cb, t(lang, "no_requests"), markup([btn(t(lang, "btn_book"), "bk:start")], nav(lang)))
    r = await get_request(session, r.id)
    await show(cb, request_card(r, lang), client_req_kb(r, lang, "home"))


@router.callback_query(F.data.regexp(r"^rq:\d+$"))
async def cb_open(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    """Universal 'open request' — routes staff to their own view, clients to theirs."""
    r = await get_request(session, int(cb.data.split(":")[1]))
    if r is None:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    if r.client_user_id != user.id:
        if user.role == "owner":
            from .owner import render_request
            await cb.answer()
            return await render_request(cb, session, r, lang)
        if user.role == "master" and await can_manage(session, user, r):
            from .master import render_job
            await cb.answer()
            return await render_job(cb, session, r, lang)
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    await cb.answer()
    await show(cb, request_card(r, lang), client_req_kb(r, lang, "menu:list:0"))


@router.callback_query(F.data.startswith("rq:h:"))
async def cb_history(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    r = await get_request(session, int(cb.data.split(":")[2]))
    if r is None or not await can_view(session, user, r):
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    await cb.answer()
    back = f"o:r:{r.id}" if user.role == "owner" else (f"mj:{r.id}" if r.client_user_id != user.id else f"rq:{r.id}")
    await show(cb, await history_text(session, r, lang), markup(nav(lang, back)))


@router.callback_query(F.data.startswith("rq:cx:"))
async def cb_cancel_ask(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    r = await get_request(session, int(cb.data.split(":")[2]))
    if r is None or r.client_user_id != user.id:
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    if r.status not in ("new", "accepted"):
        return await cb.answer(t(lang, "cannot_cancel"), show_alert=True)
    await cb.answer()
    await show(cb, t(lang, "cancel_confirm", number=r.number),
               markup([btn(t(lang, "btn_yes"), f"rq:cxy:{r.id}"), btn(t(lang, "btn_no"), f"rq:{r.id}")]))


@router.callback_query(F.data.startswith("rq:cxy:"))
async def cb_cancel_yes(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, bot: Bot):
    r = await get_request(session, int(cb.data.split(":")[2]))
    if r is None or r.client_user_id != user.id:
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    try:
        await change_status(session, bot, r, "cancelled", user)
    except PermissionDenied:
        return await cb.answer(t(lang, "cannot_cancel"), show_alert=True)
    # tell owners the client cancelled
    for o in await owners(session):
        ol = o.lang or "ru"
        await send(bot, session, o.tg_id, t(ol, "staff_update", number=r.number, what=t(ol, "st_cancelled"),
                                            who=h(user.full_name)), markup([btn(t(ol, "btn_open_request"), f"o:r:{r.id}")]),
                   kind="staff_update", request_id=r.id)
    await session.commit()
    await cb.answer(t(lang, "done_ok"))
    r = await get_request(session, r.id)
    await show(cb, request_card(r, lang), client_req_kb(r, lang, "menu:list:0"))


# ---------------- chat: client -> mechanic/owner ----------------

@router.callback_query(F.data == "cm:start")
async def cb_contact_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    reqs = (await session.scalars(select(Request).where(Request.client_user_id == user.id,
                                                        Request.status.in_(ACTIVE_STATUSES))
                                  .order_by(Request.id.desc()).limit(8))).all()
    await cb.answer()
    if not reqs:
        return await show(cb, t(lang, "cm_no_active"),
                          markup([btn(t(lang, "btn_call"), "menu:call")], [btn(t(lang, "btn_book"), "bk:start")], nav(lang)))
    if len(reqs) == 1:
        return await _ask_message(cb, state, reqs[0], lang)
    kb = [[btn(f"{STATUSES[r.status]} {r.number} · {r.brand} {r.model}", f"cm:{r.id}")] for r in reqs]
    kb.append(nav(lang))
    await show(cb, t(lang, "cm_choose"), markup(*kb))


async def _ask_message(cb: CallbackQuery, state: FSMContext, r: Request, lang: str):
    await state.set_state(Chat.to_staff)
    await state.update_data(chat_rid=r.id)
    await show(cb, t(lang, "cm_write", number=r.number), markup(nav(lang, "cm:start")))


@router.callback_query(F.data.regexp(r"^cm:\d+$"))
async def cb_contact_req(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    r = await get_request(session, int(cb.data.split(":")[1]))
    if r is None or r.client_user_id != user.id:
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    await cb.answer()
    await _ask_message(cb, state, r, lang)


@router.message(Chat.to_staff, F.text)
async def msg_to_staff(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str, bot: Bot):
    data = await state.get_data()
    r = await get_request(session, data.get("chat_rid", 0))
    if r is None or r.client_user_id != user.id:
        await state.clear()
        return await message.answer(t(lang, "access_denied"))
    text = message.text.strip()[:2000]
    add_history(session, r, user, "message", text)
    recipients = []
    if r.master and r.master.user:
        recipients.append(r.master.user)
    recipients += [o for o in await owners(session) if o.id not in {x.id for x in recipients}]
    for u in recipients:
        ul = u.lang or "ru"
        await send(bot, session, u.tg_id,
                   t(ul, "msg_from_client", number=r.number, name=h(r.client_name), phone=h(r.client_phone), text=h(text)),
                   markup([btn(t(ul, "btn_reply"), f"rp:{r.id}"), btn(t(ul, "btn_open_request"), f"rq:{r.id}")]),
                   kind="client_message", request_id=r.id)
    await session.commit()
    await state.clear()
    await message.answer(t(lang, "cm_sent"), reply_markup=markup([btn(t(lang, "btn_open_request"), f"rq:{r.id}")], nav(lang)))


# ---------------- chat: staff -> client (permission-checked) ----------------

@router.callback_query(F.data.startswith("rp:"))
async def cb_reply(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    r = await get_request(session, int(cb.data.split(":")[1]))
    if r is None or not await can_manage(session, user, r):
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    await cb.answer()
    if not r.client_user_id:
        return await cb.message.answer(t(lang, "client_unreachable", phone=h(r.client_phone)))
    await state.set_state(Chat.to_client)
    await state.update_data(reply_rid=r.id)
    await cb.message.answer(t(lang, "reply_write", number=r.number), reply_markup=markup(nav(lang, f"rq:{r.id}")))


@router.message(Chat.to_client, F.text)
async def msg_to_client(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str, bot: Bot):
    data = await state.get_data()
    r = await get_request(session, data.get("reply_rid", 0))
    if r is None or not await can_manage(session, user, r):
        await state.clear()
        return await message.answer(t(lang, "access_denied"))
    text = message.text.strip()[:2000]
    client = await session.get(User, r.client_user_id) if r.client_user_id else None
    if client:
        cl = client.lang or "ru"
        await send(bot, session, client.tg_id, t(cl, "msg_from_service", number=r.number, name=h(user.full_name), text=h(text)),
                   markup([btn(t(cl, "btn_contact_master"), f"cm:{r.id}")], [btn(t(cl, "btn_open_request"), f"rq:{r.id}")]),
                   kind="staff_message", request_id=r.id)
    add_history(session, r, user, "message", text)
    await session.commit()
    await state.clear()
    await message.answer(t(lang, "reply_sent"), reply_markup=markup([btn(t(lang, "btn_open_request"), f"rq:{r.id}")], nav(lang)))
