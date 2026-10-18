"""Truck repair request as ONE form card — the same fields as the NAJOT SERVIS website form:

Имя* · Телефон* · Марка* · Модель · Описание автомобиля · Описание проблемы* · Желаемая дата ·
Где ремонтировать* (Приеду сам / Вызов мастера) · Где находится машина* (only for a call-out) ·
Фото (up to 3) · 📤 Отправить заявку

The card shows every field with its value; tapping a field asks for it and returns to the card.
«➡️ Далее» always points to the next empty required field, so a new client just keeps tapping it.
"""
import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import BRANDS, CALL_MODES, MAIN_BRANDS, SERVICES, TRUCK_MODELS, now
from ..db import Car, Request, User, get_settings
from ..i18n import t
from ..services import create_request, get_request, request_card, send_service_location
from ..ui import (REMOVE_KB, brands_kb, btn, chunks, h, location_kb, markup, mobility_label, nav, phone_kb,
                  service_label, show, webapp_btn)

log = logging.getLogger(__name__)
router = Router(name="booking")

PHONE_RE = re.compile(r"^\+?\d{9,15}$")
PLATE_RE = re.compile(r"^[A-Z0-9]{4,12}$")
MAX_PHOTOS = 3
_locks: dict[int, asyncio.Lock] = {}


class Form(StatesGroup):
    card = State()
    name = State()
    phone = State()
    brand = State()
    brand_custom = State()
    model = State()
    car_desc = State()
    problem = State()
    date = State()
    location = State()
    photos = State()


# ---------------- helpers ----------------

def normalize_phone(raw: str) -> str | None:
    p = re.sub(r"[\s\-()]", "", raw or "")
    if p.isdigit() and len(p) == 9:          # local Uzbek number without country code
        p = "+998" + p
    elif p.isdigit() and not p.startswith("+"):
        p = "+" + p
    return p if PHONE_RE.match(p) else None


def normalize_plate(raw: str) -> str | None:
    p = re.sub(r"[\s\-]", "", (raw or "").upper())
    return p if PLATE_RE.match(p) else None


def parse_year(raw: str) -> int | None:
    raw = (raw or "").strip()
    if raw.isdigit() and 1960 <= int(raw) <= now().year + 1:
        return int(raw)
    return None


def _needs_location(d: dict) -> bool:
    return d.get("mobility") in CALL_MODES


def missing(d: dict) -> list[str]:
    out = [f for f in ("name", "phone", "brand", "problem") if not d.get(f)]
    if _needs_location(d) and d.get("latitude") is None and not d.get("address_note"):
        out.append("location")
    return out


def _value(lang: str, d: dict, field: str) -> str | None:
    if field == "location":
        if d.get("latitude") is not None:
            return t(lang, "ff_location_set") + (f" · {d['address_note']}" if d.get("address_note") else "")
        return d.get("address_note")
    if field == "date":
        v = d.get("desired_date")
        return datetime.strptime(v, "%Y-%m-%d").strftime("%d.%m.%Y") if v else None
    if field == "photos":
        return t(lang, "ff_photos_val", n=len(d.get("photo_ids") or []))
    if field == "mobility":
        return mobility_label(lang, d.get("mobility"))
    if field == "services":
        return ", ".join(service_label(lang, x) for x in d.get("services") or []) or None
    v = d.get(field)
    return str(v) if v else None


def form_text(lang: str, d: dict) -> str:
    title = t(lang, "form_title_sos" if d.get("sos") else "form_title")
    fields = ["name", "phone", "brand", "model", "car_desc", "services", "problem", "date", "mobility"]
    if _needs_location(d):
        fields.append("location")
    fields.append("photos")
    required = {"name", "phone", "brand", "problem", "mobility", "location"}
    lines = [title, ""]
    if d.get("remembered"):
        lines += [t(lang, "form_remembered"), ""]
    for f in fields:
        val = _value(lang, d, f)
        mark = ("✅ " if val else "▫️ ") if f in required else ""
        star = "*" if f in required else ""
        shown = f"<b>{h(val[:300])}</b>" if val else "—"
        lines.append(f"{mark}{t(lang, 'ff_' + f)}{star}: {shown}")
    lines += ["", t(lang, "form_agree")]
    return "\n".join(lines)


def form_kb(lang: str, d: dict):
    def lab(f: str) -> str:
        label = t(lang, "ff_" + f)
        return ("✅ " + label.split(" ", 1)[1]) if _value(lang, d, f) else label

    rows = []
    miss = missing(d)
    if miss:
        rows.append([btn(t(lang, "btn_next_field", field=t(lang, "ff_" + miss[0])), f"bf:{miss[0]}")])
    rows += [
        [btn(lab("name"), "bf:name"), btn(lab("phone"), "bf:phone")],
        [btn(lab("brand"), "bf:brand"), btn(lab("model"), "bf:model")],
        [btn(lab("car_desc"), "bf:car_desc"), btn(lab("date"), "bf:date")],
        [btn(lab("services"), "bf:services"), btn(lab("problem"), "bf:problem")],
        [btn(("✅ " if not _needs_location(d) else "") + mobility_label(lang, "drive"), "bf:mob:drive"),
         btn(("✅ " if _needs_location(d) else "") + mobility_label(lang, "onsite"), "bf:mob:onsite")],
    ]
    if _needs_location(d):
        rows.append([btn(("✅ " if _value(lang, d, "location") else "") + t(lang, "btn_mark_location"), "bf:location")])
    rows.append([btn(t(lang, "btn_add_photo", n=len(d.get("photo_ids") or [])), "bf:photos")])
    if d.get("remembered"):
        rows.append([btn(t(lang, "btn_other_truck"), "bf:newtruck")])
    rows.append([btn(t(lang, "btn_send_request"), "bf:send")])
    home = "o:menu" if d.get("mode") == "owner" else "home"
    rows.append([btn(t(lang, "btn_ask_ai"), "ai:start"), btn(t(lang, "btn_home"), home)])
    return markup(*rows)


async def render_form(event, state: FSMContext, lang: str):
    await state.set_state(Form.card)
    d = await state.get_data()
    await show(event, form_text(lang, d), form_kb(lang, d))


def back_kb(lang: str, *extra_rows):
    return markup(*extra_rows, [btn(t(lang, "btn_to_form"), "bf:card")])


async def remembered(s: AsyncSession, user: User, *, with_truck: bool = True) -> dict:
    """What the client already told us last time: name, phone and the truck (not the problem/date/photos/place)."""
    last = await s.scalar(select(Request).where(Request.client_user_id == user.id).order_by(Request.id.desc()))
    if last is None:
        return {}
    out = {"name": last.client_name, "phone": last.client_phone}
    if with_truck:
        out.update(brand=last.brand, model=last.model or None, car_desc=last.car_desc, year=last.year,
                   plate=last.plate, body_type=last.body_type, car_id=last.car_id, remembered=True)
    return {k: v for k, v in out.items() if v not in (None, "")}


async def start_booking(event: Message | CallbackQuery, state: FSMContext, s: AsyncSession, user: User, lang: str,
                        *, mode: str = "client", prefill: dict | None = None, first_step: str | None = None,
                        sos: bool = False):
    """Open a fresh form. `first_step` is kept for compatibility; the form card is always shown first."""
    await state.clear()
    data = {"mode": mode, "idem": uuid.uuid4().hex, "mobility": "onsite" if sos else "drive", "sos": sos,
            "photo_ids": []}
    if mode == "client":
        data["phone"] = user.phone
        if (user.full_name or "").strip():
            data["name"] = user.full_name.strip()[:60]
        data.update(await remembered(s, user, with_truck=not (prefill or {}).get("brand")))
    data.update({k: v for k, v in (prefill or {}).items() if v not in (None, "")})
    await state.update_data(**data)
    await render_form(event, state, lang)


async def _saved(event, state: FSMContext, lang: str, **values):
    """Store values and come back to the form card."""
    await state.update_data(**values)
    await render_form(event, state, lang)


async def _alive(cb: CallbackQuery, state: FSMContext, lang: str) -> dict | None:
    d = await state.get_data()
    if not d.get("idem"):
        await cb.answer(t(lang, "bk_expired"), show_alert=True)
        return None
    return d


# ---------------- entry points ----------------

@router.callback_query(F.data == "bk:start")
async def cb_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await cb.answer()
    await start_booking(cb, state, session, user, lang)


@router.callback_query(F.data == "bk:open")
async def cb_open_form(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    """Hand out a fresh «open form» button (the Mini App address changes after each restart)."""
    await cb.answer()
    await state.clear()
    open_btn = webapp_btn(t(lang, "btn_open_form"), lang)
    if open_btn is None:   # Mini App is not available right now — use the form in chat
        return await start_booking(cb, state, session, user, lang)
    await show(cb, t(lang, "open_form_text"),
               markup([open_btn], [btn(t(lang, "btn_fill_in_chat"), "bk:start")], nav(lang)))


@router.callback_query(F.data == "sos")
async def cb_sos(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    await state.clear()
    await cb.answer()
    st = await get_settings(session)
    await show(cb, t(lang, "sos_intro", phone=h(st["phone"])),
               markup([btn(t(lang, "btn_sos_start"), "sos:go")], [btn(t(lang, "btn_call"), "menu:call")], nav(lang)))


@router.callback_query(F.data == "sos:go")
async def cb_sos_go(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await cb.answer()
    await start_booking(cb, state, session, user, lang, sos=True)


@router.callback_query(F.data == "bf:card")
async def cb_card(cb: CallbackQuery, state: FSMContext, lang: str):
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    if await state.get_state() in (Form.phone.state, Form.location.state):
        await cb.message.answer("👌", reply_markup=REMOVE_KB)  # hide the contact/location keyboard
    await render_form(cb, state, lang)


@router.callback_query(F.data == "bf:newtruck")
async def cb_new_truck(cb: CallbackQuery, state: FSMContext, lang: str):
    """Client came with a different truck: forget the remembered one."""
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    await state.update_data(brand=None, model=None, car_desc=None, year=None, plate=None, body_type=None,
                            car_id=None, remembered=False)
    await render_form(cb, state, lang)


# ---------------- field: name / phone ----------------

@router.callback_query(F.data == "bf:name")
async def cb_name(cb: CallbackQuery, state: FSMContext, lang: str):
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    await state.set_state(Form.name)
    await show(cb, t(lang, "q_name"), back_kb(lang))


@router.message(Form.name, F.text)
async def msg_name(message: Message, state: FSMContext, lang: str):
    name = message.text.strip()
    if not 2 <= len(name) <= 60:
        return await message.answer(t(lang, "bk_too_long", n=60))
    await _saved(message, state, lang, name=name)


@router.callback_query(F.data == "bf:phone")
async def cb_phone(cb: CallbackQuery, state: FSMContext, lang: str):
    d = await _alive(cb, state, lang)
    if d is None:
        return
    await cb.answer()
    await state.set_state(Form.phone)
    await show(cb, t(lang, "bk_step_phone"), back_kb(lang))
    if d.get("mode") == "client":
        await cb.message.answer("👇", reply_markup=phone_kb(lang))


async def _phone_in(message: Message, state: FSMContext, lang: str, raw: str):
    phone = normalize_phone(raw)
    if not phone:
        return await message.answer(t(lang, "bk_bad_phone"))
    await message.answer(t(lang, "bk_phone_ok"), reply_markup=REMOVE_KB)
    await _saved(message, state, lang, phone=phone)


@router.message(Form.phone, F.contact)
async def msg_contact(message: Message, state: FSMContext, lang: str):
    await _phone_in(message, state, lang, message.contact.phone_number)


@router.message(Form.phone, F.text)
async def msg_phone(message: Message, state: FSMContext, lang: str):
    await _phone_in(message, state, lang, message.text)


# ---------------- field: brand / model ----------------

@router.callback_query(F.data == "bf:brand")
async def cb_brand_field(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    d = await _alive(cb, state, lang)
    if d is None:
        return
    await cb.answer()
    await state.set_state(Form.brand)
    cars = []
    text = t(lang, "bk_step_brand")
    if d.get("mode") == "client":
        cars = (await session.scalars(select(Car).where(Car.user_id == user.id).order_by(Car.id.desc()).limit(5))).all()
        if cars:
            text += t(lang, "bk_saved_cars")
    await show(cb, text, brands_kb(lang, "bk:b", "bf:card", cars))


@router.callback_query(F.data.startswith("bk:b:"), Form.brand)
async def cb_brand(cb: CallbackQuery, state: FSMContext, lang: str):
    val = cb.data.split(":", 2)[2]
    await cb.answer()
    if val == "other":
        await state.set_state(Form.brand_custom)
        return await show(cb, t(lang, "bk_type_brand"), back_kb(lang))
    if val.isdigit() and int(val) < len(MAIN_BRANDS):
        await _brand_chosen(cb, state, lang, MAIN_BRANDS[int(val)])


@router.callback_query(F.data.startswith("bk:bn:"), Form.brand)
async def cb_brand_named(cb: CallbackQuery, state: FSMContext, lang: str):
    name = cb.data.split(":", 2)[2]
    await cb.answer()
    if name in BRANDS:
        await _brand_chosen(cb, state, lang, name)


@router.callback_query(F.data == "bk:typed", Form.brand)
async def cb_brand_typed(cb: CallbackQuery, state: FSMContext, lang: str):
    d = await state.get_data()
    await cb.answer()
    if d.get("typed"):
        await _brand_chosen(cb, state, lang, d["typed"])


async def _brand_chosen(event, state: FSMContext, lang: str, brand: str):
    """After the brand, offer the model right away (one less tap) — it can be skipped."""
    d = await state.get_data()
    changed = brand != d.get("brand")
    await state.update_data(brand=brand, car_id=None, **({"model": None} if changed else {}))
    if TRUCK_MODELS.get(brand) and (changed or not d.get("model")):
        return await _ask_model(event, state, lang)
    await render_form(event, state, lang)


def car_prefill(car: Car) -> dict:
    desc = ", ".join(x for x in (str(car.year) if car.year else "", car.plate or "",
                                 f"VIN {car.vin}" if car.vin else "") if x)
    return {"brand": car.brand, "model": car.model, "year": car.year, "plate": car.plate, "body_type": car.body_type,
            "car_desc": desc or None, "car_id": car.id}


@router.callback_query(F.data.startswith("bk:car:"), Form.brand)
async def cb_saved_car(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    car = await session.get(Car, int(cb.data.split(":")[2]))
    if not car or car.user_id != user.id:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    await cb.answer()
    await _saved(cb, state, lang, **car_prefill(car))


@router.message(Form.brand, F.text)
async def msg_brand_search(message: Message, state: FSMContext, lang: str):
    q = message.text.strip()[:30]
    exact = next((b for b in BRANDS if b.lower() == q.lower()), None)
    if exact:
        return await _brand_chosen(message, state, lang, exact)
    found = [b for b in BRANDS if q.lower() in b.lower()][:9]
    await state.update_data(typed=q)
    rows = chunks([btn(b, f"bk:bn:{b}") for b in found], 3)
    rows.append([btn(t(lang, "btn_use_typed", q=q), "bk:typed")])
    await message.answer(t(lang, "bk_search_results", q=h(q)), reply_markup=back_kb(lang, *rows))


@router.message(Form.brand_custom, F.text)
async def msg_brand_custom(message: Message, state: FSMContext, lang: str):
    brand = message.text.strip()[:40]
    if len(brand) < 2:
        return await message.answer(t(lang, "bk_type_brand"))
    await _brand_chosen(message, state, lang, brand)


async def _ask_model(event, state: FSMContext, lang: str):
    d = await state.get_data()
    await state.set_state(Form.model)
    models = TRUCK_MODELS.get(d.get("brand") or "", [])
    rows = chunks([btn(m, f"bk:m:{i}") for i, m in enumerate(models)], 3)
    rows.append([btn(t(lang, "btn_skip"), "bf:card")])
    await show(event, t(lang, "bk_step_model", brand=h(d.get("brand") or "—")), back_kb(lang, *rows))


@router.callback_query(F.data == "bf:model")
async def cb_model_field(cb: CallbackQuery, state: FSMContext, lang: str):
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    await _ask_model(cb, state, lang)


@router.callback_query(F.data.startswith("bk:m:"), Form.model)
async def cb_model(cb: CallbackQuery, state: FSMContext, lang: str):
    models = TRUCK_MODELS.get((await state.get_data()).get("brand") or "", [])
    idx = cb.data.split(":")[2]
    await cb.answer()
    if idx.isdigit() and int(idx) < len(models):
        await _saved(cb, state, lang, model=models[int(idx)], car_id=None)


@router.message(Form.model, F.text)
async def msg_model(message: Message, state: FSMContext, lang: str):
    model = message.text.strip()
    if not 1 <= len(model) <= 40:
        return await message.answer(t(lang, "bk_too_long", n=40))
    await _saved(message, state, lang, model=model, car_id=None)


# ---------------- field: services (several can be selected) ----------------

def services_kb(lang: str, selected: list[str]):
    rows = [[btn(("✅ " if code in selected else "") + service_label(lang, code), f"bf:sv:{code}")]
            for code, _ in SERVICES]
    return back_kb(lang, *rows, [btn(t(lang, "btn_done"), "bf:card")])


@router.callback_query(F.data == "bf:services")
async def cb_services(cb: CallbackQuery, state: FSMContext, lang: str):
    d = await _alive(cb, state, lang)
    if d is None:
        return
    await cb.answer()
    await state.set_state(Form.card)
    await show(cb, t(lang, "q_services"), services_kb(lang, d.get("services") or []))


@router.callback_query(F.data.startswith("bf:sv:"))
async def cb_service_toggle(cb: CallbackQuery, state: FSMContext, lang: str):
    d = await _alive(cb, state, lang)
    if d is None:
        return
    code = cb.data.split(":")[2]
    if code not in dict(SERVICES):
        return await cb.answer()
    selected = list(d.get("services") or [])
    selected.remove(code) if code in selected else selected.append(code)
    await state.update_data(services=selected)
    await cb.answer()
    await show(cb, t(lang, "q_services"), services_kb(lang, selected))


# ---------------- field: car description / problem / date ----------------

@router.callback_query(F.data == "bf:car_desc")
async def cb_car_desc(cb: CallbackQuery, state: FSMContext, lang: str):
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    await state.set_state(Form.car_desc)
    await show(cb, t(lang, "q_car_desc"), back_kb(lang))


@router.message(Form.car_desc, F.text)
async def msg_car_desc(message: Message, state: FSMContext, lang: str):
    text = message.text.strip()
    if len(text) > 500:
        return await message.answer(t(lang, "bk_too_long", n=500))
    extra = {}
    year = next((parse_year(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", text) if parse_year(y)), None)
    if year:
        extra["year"] = year
    plate = next((normalize_plate(p) for p in re.findall(r"\b\d{2}\s?[A-Za-z]\s?\d{3}\s?[A-Za-z]{2}\b", text)), None)
    if plate:
        extra["plate"] = plate
    await _saved(message, state, lang, car_desc=text, **extra)


@router.callback_query(F.data == "bf:problem")
async def cb_problem(cb: CallbackQuery, state: FSMContext, lang: str):
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    await state.set_state(Form.problem)
    await show(cb, t(lang, "q_problem"), back_kb(lang))


@router.message(Form.problem, F.text)
async def msg_problem(message: Message, state: FSMContext, lang: str):
    text = message.text.strip()
    if len(text) < 5:
        return await message.answer(t(lang, "bk_problem_short"))
    if len(text) > 1000:
        return await message.answer(t(lang, "bk_too_long", n=1000))
    await _saved(message, state, lang, problem=text)


@router.message(Form.problem, F.photo)
async def msg_problem_photo(message: Message, state: FSMContext, user: User, lang: str):
    await _add_photo(message, state, user)
    caption = (message.caption or "").strip()
    if len(caption) >= 5:
        return await _saved(message, state, lang, problem=caption[:1000])
    await message.answer(t(lang, "photo_added", n=len((await state.get_data()).get("photo_ids") or [])) + "\n\n"
                         + t(lang, "q_problem"), reply_markup=back_kb(lang))


@router.callback_query(F.data == "bf:date")
async def cb_date(cb: CallbackQuery, state: FSMContext, lang: str):
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    await state.set_state(Form.date)
    today = now().date()
    days = [today + timedelta(days=i) for i in range(7)]
    labels = [t(lang, "rt_today"), t(lang, "rt_tomorrow")] + [d.strftime("%d.%m") for d in days[2:]]
    btns = [btn(f"📅 {lbl}", f"bf:d:{d.isoformat()}") for lbl, d in zip(labels, days)]
    await show(cb, t(lang, "q_date"), back_kb(lang, *chunks(btns, 3), [btn(t(lang, "btn_no_date"), "bf:d:none")]))


@router.callback_query(F.data.startswith("bf:d:"), Form.date)
async def cb_date_pick(cb: CallbackQuery, state: FSMContext, lang: str):
    val = cb.data.split(":", 2)[2]
    await cb.answer()
    await _saved(cb, state, lang, desired_date=None if val == "none" else val)


@router.message(Form.date, F.text)
async def msg_date(message: Message, state: FSMContext, lang: str):
    raw = message.text.strip().replace("/", ".").replace("-", ".")
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%d.%m"):
        try:
            d = datetime.strptime(raw, fmt)
            if fmt == "%d.%m":
                d = d.replace(year=now().year)
            break
        except ValueError:
            continue
    else:
        return await message.answer(t(lang, "rt_bad_date"))
    if d.date() < now().date():
        return await message.answer(t(lang, "rt_past"))
    await _saved(message, state, lang, desired_date=d.date().isoformat())


# ---------------- field: where to repair / location ----------------

@router.callback_query(F.data.startswith("bf:mob:"))
async def cb_mobility(cb: CallbackQuery, state: FSMContext, lang: str):
    d = await _alive(cb, state, lang)
    if d is None:
        return
    code = cb.data.split(":")[2]
    if code not in ("drive", "onsite"):
        return await cb.answer()
    await cb.answer()
    await state.update_data(mobility=code)
    if code == "onsite" and d.get("latitude") is None and not d.get("address_note"):
        return await _ask_location(cb, state, lang)   # «Вызов мастера» needs the truck's location
    await render_form(cb, state, lang)


async def _ask_location(event, state: FSMContext, lang: str):
    await state.set_state(Form.location)
    await show(event, t(lang, "q_location"), back_kb(lang))
    await event.bot.send_message(event.from_user.id, "👇", reply_markup=location_kb(lang))


@router.callback_query(F.data == "bf:location")
async def cb_location(cb: CallbackQuery, state: FSMContext, lang: str):
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    await _ask_location(cb, state, lang)


@router.message(Form.location, F.location)
async def msg_location(message: Message, state: FSMContext, lang: str):
    await message.answer(t(lang, "bk_location_ok"), reply_markup=REMOVE_KB)
    await _saved(message, state, lang, latitude=message.location.latitude, longitude=message.location.longitude)


@router.message(Form.location, F.text)
async def msg_location_text(message: Message, state: FSMContext, lang: str):
    note = message.text.strip()[:300]
    if len(note) < 3:
        return await message.answer(t(lang, "bk_need_location"), reply_markup=location_kb(lang))
    await message.answer(t(lang, "bk_location_ok"), reply_markup=REMOVE_KB)
    await _saved(message, state, lang, address_note=note)


# ---------------- field: photos (up to 3) ----------------

@router.callback_query(F.data == "bf:photos")
async def cb_photos(cb: CallbackQuery, state: FSMContext, lang: str):
    d = await _alive(cb, state, lang)
    if d is None:
        return
    await cb.answer()
    n = len(d.get("photo_ids") or [])
    if n >= MAX_PHOTOS:
        return await show(cb, t(lang, "photos_full"),
                          back_kb(lang, [btn(t(lang, "btn_clear_photos"), "bf:photos:clear")]))
    await state.set_state(Form.photos)
    await show(cb, t(lang, "q_photos", left=MAX_PHOTOS - n), back_kb(lang, [btn(t(lang, "btn_done"), "bf:card")]))


@router.callback_query(F.data == "bf:photos:clear")
async def cb_photos_clear(cb: CallbackQuery, state: FSMContext, lang: str):
    if await _alive(cb, state, lang) is None:
        return
    await cb.answer()
    await _saved(cb, state, lang, photo_ids=[])


async def _add_photo(message: Message, state: FSMContext, user: User) -> int:
    # album photos arrive as parallel updates — serialize per user so none is lost
    lock = _locks.setdefault(-user.tg_id, asyncio.Lock())
    async with lock:
        d = await state.get_data()
        photos = list(d.get("photo_ids") or [])
        if len(photos) < MAX_PHOTOS:
            photos.append(message.photo[-1].file_id)
            await state.update_data(photo_ids=photos)
        return len(photos)


@router.message(Form.photos, F.photo)
async def msg_photo(message: Message, state: FSMContext, user: User, lang: str):
    n = await _add_photo(message, state, user)
    if n >= MAX_PHOTOS:
        return await render_form(message, state, lang)
    await message.answer(t(lang, "photo_added", n=n), reply_markup=back_kb(lang, [btn(t(lang, "btn_done"), "bf:card")]))


# ---------------- send ----------------

@router.callback_query(F.data == "bf:send")
async def cb_send(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str, bot: Bot):
    lock = _locks.setdefault(user.tg_id, asyncio.Lock())
    if lock.locked():
        return await cb.answer(t(lang, "bk_processing"))
    async with lock:
        d = await state.get_data()
        if not d.get("idem"):
            return await cb.answer(t(lang, "bk_expired"), show_alert=True)
        miss = missing(d)
        if miss:
            return await cb.answer(t(lang, "form_missing", fields=", ".join(t(lang, "ff_" + f) for f in miss)),
                                   show_alert=True)
        mode = d.get("mode", "client")
        if mode == "owner" and user.role != "owner":
            return await cb.answer(t(lang, "access_denied"), show_alert=True)
        d.setdefault("service", "other")
        d["model"] = d.get("model") or ""
        source = d.get("source") or ("owner" if mode == "owner" else ("sos" if d.get("sos") else "telegram"))
        r, created = await create_request(session, bot, d, user, for_client=(mode == "client"),
                                          idem_key=d["idem"], source=source)
        await state.clear()
        await cb.answer()
        log.info("request %s %s by tg=%s", r.number, "created" if created else "dedup", user.tg_id)
        if mode == "owner":
            r = await get_request(session, r.id)
            return await show(cb, t(lang, "bk_created_owner", number=r.number) + "\n\n"
                              + request_card(r, lang, staff=True),
                              markup([btn(t(lang, "btn_open_request"), f"o:r:{r.id}")], nav(lang, "o:menu")))
        rows = [[btn(t(lang, "btn_open_request"), f"rq:{r.id}")]]
        text = t(lang, "bk_created", number=r.number)
        if created and not d.get("car_id"):
            count = await session.scalar(select(func.count(Car.id)).where(Car.user_id == user.id))
            dup = await session.scalar(select(Car.id).where(Car.user_id == user.id, Car.brand == r.brand,
                                                            Car.model == r.model))
            if count < 10 and not dup:
                text += "\n\n" + t(lang, "bk_save_car_q")
                rows.insert(0, [btn("💾 " + t(lang, "btn_yes"), f"bk:savecar:{r.id}")])
        rows.append(nav(lang))
        await show(cb, text, markup(*rows))
        if created and r.mobility not in CALL_MODES:
            # «Приеду сам» — send the service pin so the client can build a route
            await send_service_location(bot, session, user.tg_id, lang, request_id=r.id)
            await session.commit()


@router.callback_query(F.data.startswith("bk:savecar:"))
async def cb_savecar(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    r = await get_request(session, int(cb.data.split(":")[2]))
    if not r or r.client_user_id != user.id:
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    dup = await session.scalar(select(Car.id).where(Car.user_id == user.id, Car.brand == r.brand, Car.model == r.model))
    if not dup:
        car = Car(user_id=user.id, brand=r.brand, model=r.model, year=r.year, plate=r.plate, body_type=r.body_type)
        session.add(car)
        await session.flush()
        r.car_id = car.id
        await session.commit()
    await cb.answer(t(lang, "car_saved"))
    await show(cb, t(lang, "bk_created", number=r.number),
               markup([btn(t(lang, "btn_open_request"), f"rq:{r.id}")], [btn(t(lang, "btn_my_cars"), "car:list")],
                      nav(lang)))


# Typed while the form card is shown: if the problem is still empty, take the text as the problem
@router.message(Form.card, F.text)
async def msg_on_card(message: Message, state: FSMContext, lang: str):
    d = await state.get_data()
    text = message.text.strip()
    if not d.get("problem") and len(text) >= 5:
        return await _saved(message, state, lang, problem=text[:1000])
    await message.answer(t(lang, "use_buttons"))
    await render_form(message, state, lang)


@router.message(Form.card, F.photo)
async def msg_photo_on_card(message: Message, state: FSMContext, user: User, lang: str):
    await _add_photo(message, state, user)
    caption = (message.caption or "").strip()
    if not (await state.get_data()).get("problem") and len(caption) >= 5:
        await state.update_data(problem=caption[:1000])
    await render_form(message, state, lang)
