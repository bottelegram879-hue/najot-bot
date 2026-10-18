"""Keyboard builders and the `show` helper that edits the current screen in place."""
import logging
from html import escape

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo)

from .config import BODY_TYPES, MAIN_BRANDS, MINIAPP, MOBILITY, SERVICES, STATUSES
from .i18n import LANGS, t

log = logging.getLogger(__name__)

PAGE_SIZE = 8
BUTTON_STYLE = "primary"  # Telegram button colour: primary = blue (success = green, danger = red)


def h(value) -> str:
    """HTML-escape user content."""
    return escape(str(value)) if value is not None else "—"


def btn(text: str, cb: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=cb, style=BUTTON_STYLE)


def url_btn(text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, url=url, style=BUTTON_STYLE)


def markup(*rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows if r])


def nav(lang: str, back: str | None = "home") -> list[InlineKeyboardButton]:
    row = []
    if back and back != "home":
        row.append(btn(t(lang, "btn_back"), back))
    row.append(btn(t(lang, "btn_home"), "home"))
    return row


def chunks(items: list, n: int) -> list[list]:
    return [items[i:i + n] for i in range(0, len(items), n)]


def status_label(lang: str, code: str) -> str:
    return f"{STATUSES.get(code, '')} {t(lang, 'st_' + code)}"


def service_label(lang: str, code: str) -> str:
    emoji = dict(SERVICES).get(code, "🔧")
    return f"{emoji} {t(lang, 'svc_' + code)}"


# ---------------- keyboards ----------------

def webapp_btn(text: str, lang: str = "ru") -> InlineKeyboardButton | None:
    """Button that opens the request form (Mini App) at its CURRENT address, in the client's language."""
    if not MINIAPP.get("url"):
        return None
    url = f"{MINIAPP['url']}?lang={lang if lang in ('ru', 'uz', 'en') else 'ru'}"
    return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url), style=BUTTON_STYLE)


def lang_kb() -> InlineKeyboardMarkup:
    return markup(*[[btn(name, f"lang:{code}")] for code, name in LANGS.items()])


def client_menu(lang: str, role: str = "client") -> InlineKeyboardMarkup:
    # opens the website form right away; menus are re-pointed to the new address after each restart
    book = webapp_btn(t(lang, "btn_book"), lang) or btn(t(lang, "btn_book"), "bk:start")
    rows = [
        [book],
        [btn(t(lang, "btn_sos"), "sos")],
        [btn(t(lang, "btn_my_request"), "menu:last"), btn(t(lang, "btn_my_requests"), "menu:list:0")],
        [btn(t(lang, "btn_my_cars"), "car:list"), btn(t(lang, "btn_contact_master"), "cm:start")],
        [btn(t(lang, "btn_ai"), "ai:start")],
        [btn(t(lang, "btn_address"), "menu:address"), btn(t(lang, "btn_call"), "menu:call")],
        [btn(t(lang, "btn_about"), "menu:about"), btn(t(lang, "btn_lang"), "menu:lang")],
    ]
    if role in ("owner", "master"):
        rows.append([btn(t(lang, "btn_staff_panel"), "panel")])
    return markup(*rows)


def brands_kb(lang: str, prefix: str, back: str, saved_cars=None) -> InlineKeyboardMarkup:
    rows = []
    for car in saved_cars or []:
        rows.append([btn(f"⭐ {car.brand} {car.model}" + (f" · {car.plate}" if car.plate else ""), f"bk:car:{car.id}")])
    brand_btns = [btn(b, f"{prefix}:{i}") for i, b in enumerate(MAIN_BRANDS)]
    rows += chunks(brand_btns, 3)
    rows.append([btn(t(lang, "btn_other_brand"), f"{prefix}:other")])
    rows.append(nav(lang, back))
    return markup(*rows)


def services_kb(lang: str, back: str, prefix: str = "bk:svc") -> InlineKeyboardMarkup:
    rows = [[btn(service_label(lang, code), f"{prefix}:{code}")] for code, _ in SERVICES]
    rows.append(nav(lang, back))
    return markup(*rows)


def body_label(lang: str, code: str | None) -> str:
    if not code:
        return "—"
    return f"{dict(BODY_TYPES).get(code, '🚚')} {t(lang, 'body_' + code)}"


def mobility_label(lang: str, code: str | None) -> str:
    code = code or "drive"
    return f"{dict(MOBILITY).get(code, '🚛')} {t(lang, 'mob_' + code)}"


def body_kb(lang: str, prefix: str, back: str) -> InlineKeyboardMarkup:
    btns = [btn(body_label(lang, code), f"{prefix}:{code}") for code, _ in BODY_TYPES]
    return markup(*chunks(btns, 2), nav(lang, back))


def mobility_kb(lang: str, back: str) -> InlineKeyboardMarkup:
    return markup(*[[btn(mobility_label(lang, code), f"bk:mob:{code}")] for code, _ in MOBILITY], nav(lang, back))


def location_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "btn_send_location"), request_location=True, style=BUTTON_STYLE)],
                  [KeyboardButton(text=t(lang, "btn_cancel"), style=BUTTON_STYLE)]],
        resize_keyboard=True, one_time_keyboard=True)


def phone_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "btn_send_phone"), request_contact=True, style=BUTTON_STYLE)],
                  [KeyboardButton(text=t(lang, "btn_cancel"), style=BUTTON_STYLE)]],
        resize_keyboard=True, one_time_keyboard=True)


REMOVE_KB = ReplyKeyboardRemove()


def pager(lang: str, base: str, page: int, pages: int) -> list[InlineKeyboardButton]:
    if pages <= 1:
        return []
    row = []
    if page > 0:
        row.append(btn(t(lang, "btn_prev"), f"{base}:{page - 1}"))
    row.append(btn(f"{page + 1}/{pages}", "noop"))
    if page < pages - 1:
        row.append(btn(t(lang, "btn_next"), f"{base}:{page + 1}"))
    return row


# ---------------- screen rendering ----------------

async def show(event: Message | CallbackQuery, text: str, kb: InlineKeyboardMarkup | None = None) -> Message | None:
    """Edit the current screen when coming from a button, otherwise send a new message."""
    if isinstance(event, CallbackQuery):
        msg = event.message
        if msg is not None and getattr(msg, "text", None) is not None:
            try:
                return await msg.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    return msg
                log.debug("edit failed, sending new: %s", e)
        return await event.bot.send_message(event.from_user.id, text, reply_markup=kb, disable_web_page_preview=True)
    return await event.answer(text, reply_markup=kb, disable_web_page_preview=True)
