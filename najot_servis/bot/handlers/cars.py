"""Client garage: several saved trucks with brand, model, year, body type, plate, optional VIN."""
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import BRANDS, MAIN_BRANDS
from ..db import Car, User
from ..i18n import t
from ..config import BODY_TYPES
from ..ui import body_kb, body_label, brands_kb, btn, chunks, h, markup, nav, show
from .booking import car_prefill, parse_year, start_booking

router = Router(name="cars")
MAX_CARS = 10
PLATE_RE = re.compile(r"^[A-Z0-9]{4,12}$")
VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
CAR_ICONS = ["🚛", "🚚", "🚛", "🚚", "🛻"]


class AddCar(StatesGroup):
    brand = State()
    model = State()
    year = State()
    body = State()
    plate = State()
    vin = State()


@router.callback_query(F.data == "car:list")
async def cb_list(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    await cb.answer()
    await render_cars(cb, session, user, lang)


async def render_cars(event, session: AsyncSession, user: User, lang: str):
    cars = (await session.scalars(select(Car).where(Car.user_id == user.id).order_by(Car.id))).all()
    rows = [[btn(f"{CAR_ICONS[i % len(CAR_ICONS)]} {c.brand} {c.model}" + (f" · {c.plate}" if c.plate else ""), f"car:{c.id}")]
            for i, c in enumerate(cars)]
    rows.append([btn(t(lang, "btn_add_car"), "car:add")])
    rows.append(nav(lang))
    text = t(lang, "cars_title") + ("" if cars else "\n\n" + t(lang, "cars_empty"))
    await show(event, text, markup(*rows))


async def _own_car(session: AsyncSession, user: User, car_id: int) -> Car | None:
    car = await session.get(Car, car_id)
    return car if car and car.user_id == user.id else None


@router.callback_query(F.data.regexp(r"^car:\d+$"))
async def cb_card(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    car = await _own_car(session, user, int(cb.data.split(":")[1]))
    if not car:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    await cb.answer()
    await show(cb, t(lang, "car_card", brand=h(car.brand), model=h(car.model), year=h(car.year), plate=h(car.plate),
                     vin=h(car.vin), body=body_label(lang, car.body_type)),
               markup([btn(t(lang, "btn_book_with_car"), f"car:book:{car.id}")],
                      [btn(t(lang, "btn_delete_car"), f"car:del:{car.id}")], nav(lang, "car:list")))


@router.callback_query(F.data.startswith("car:del:"))
async def cb_delete(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    car = await _own_car(session, user, int(cb.data.split(":")[2]))
    if not car:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    await session.delete(car)
    await session.commit()
    await cb.answer(t(lang, "car_deleted"))
    await render_cars(cb, session, user, lang)


@router.callback_query(F.data.startswith("car:book:"))
async def cb_book(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    car = await _own_car(session, user, int(cb.data.split(":")[2]))
    if not car:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    await cb.answer()
    await start_booking(cb, state, session, user, lang, prefill=car_prefill(car))


# ---------------- add car wizard ----------------

@router.callback_query(F.data == "car:add")
async def cb_add(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    count = await session.scalar(select(func.count(Car.id)).where(Car.user_id == user.id))
    if count >= MAX_CARS:
        return await cb.answer(t(lang, "car_limit", n=MAX_CARS), show_alert=True)
    await cb.answer()
    await state.set_state(AddCar.brand)
    await show(cb, t(lang, "car_brand"), brands_kb(lang, "cb", "car:list"))


@router.callback_query(F.data.startswith("cb:"), AddCar.brand)
async def cb_add_brand(cb: CallbackQuery, state: FSMContext, lang: str):
    val = cb.data.split(":", 1)[1]
    await cb.answer()
    if val == "other":
        return await show(cb, t(lang, "bk_type_brand"), markup(nav(lang, "car:add")))
    brand = MAIN_BRANDS[int(val)] if val.isdigit() and int(val) < len(MAIN_BRANDS) else (val if val in BRANDS else None)
    if not brand:
        return
    await state.update_data(car_brand=brand)
    await state.set_state(AddCar.model)
    await show(cb, t(lang, "car_model", brand=h(brand)), markup(nav(lang, "car:add")))


@router.message(AddCar.brand, F.text)
async def msg_add_brand(message: Message, state: FSMContext, lang: str):
    q = message.text.strip()[:30]
    exact = next((b for b in BRANDS if b.lower() == q.lower()), None)
    found = [b for b in BRANDS if q.lower() in b.lower()][:9]
    if exact or not found or len(q) < 2:
        brand = exact or q
        if len(brand) < 2:
            return await message.answer(t(lang, "bk_type_brand"))
        await state.update_data(car_brand=brand)
        await state.set_state(AddCar.model)
        return await message.answer(t(lang, "car_model", brand=h(brand)), reply_markup=markup(nav(lang, "car:add")))
    rows = chunks([btn(b, f"cb:{b}") for b in found], 3)
    rows.append(nav(lang, "car:add"))
    await message.answer(t(lang, "bk_search_results", q=h(q)), reply_markup=markup(*rows))


@router.message(AddCar.model, F.text)
async def msg_add_model(message: Message, state: FSMContext, lang: str):
    model = message.text.strip()
    if not 1 <= len(model) <= 40:
        return await message.answer(t(lang, "bk_too_long", n=40))
    await state.update_data(car_model=model)
    await state.set_state(AddCar.year)
    await message.answer(t(lang, "car_year"), reply_markup=markup(nav(lang, "car:list")))


@router.message(AddCar.year, F.text)
async def msg_add_year(message: Message, state: FSMContext, lang: str):
    from ..config import now
    y = parse_year(message.text)
    if y is None:
        return await message.answer(t(lang, "bk_bad_year", max=now().year + 1))
    await state.update_data(car_year=y)
    await state.set_state(AddCar.body)
    await message.answer(t(lang, "bk_step_body"), reply_markup=body_kb(lang, "cbody", "car:list"))


@router.callback_query(F.data.startswith("cbody:"), AddCar.body)
async def cb_add_body(cb: CallbackQuery, state: FSMContext, lang: str):
    code = cb.data.split(":")[1]
    if code not in dict(BODY_TYPES):
        return await cb.answer()
    await cb.answer()
    await state.update_data(car_body=code)
    await state.set_state(AddCar.plate)
    await show(cb, t(lang, "car_plate"), markup([btn(t(lang, "btn_skip"), "car:skipplate")], nav(lang, "car:list")))


@router.message(AddCar.plate, F.text)
async def msg_add_plate(message: Message, state: FSMContext, lang: str):
    plate = re.sub(r"[\s\-]", "", message.text.upper())
    if not PLATE_RE.match(plate):
        return await message.answer(t(lang, "car_bad_plate"))
    await state.update_data(car_plate=plate)
    await _ask_vin(message, state, lang)


@router.callback_query(F.data == "car:skipplate", AddCar.plate)
async def cb_skip_plate(cb: CallbackQuery, state: FSMContext, lang: str):
    await cb.answer()
    await state.update_data(car_plate=None)
    await _ask_vin(cb, state, lang)


async def _ask_vin(event, state: FSMContext, lang: str):
    await state.set_state(AddCar.vin)
    await show(event, t(lang, "car_vin"), markup([btn(t(lang, "btn_skip"), "car:skipvin")], nav(lang, "car:list")))


@router.message(AddCar.vin, F.text)
async def msg_add_vin(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str):
    vin = message.text.strip().upper().replace(" ", "")
    if not VIN_RE.match(vin):
        return await message.answer(t(lang, "car_bad_vin"))
    await _save(message, state, session, user, lang, vin)


@router.callback_query(F.data == "car:skipvin", AddCar.vin)
async def cb_skip_vin(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await cb.answer()
    await _save(cb, state, session, user, lang, None)


async def _save(event, state: FSMContext, session: AsyncSession, user: User, lang: str, vin: str | None):
    d = await state.get_data()
    car = Car(user_id=user.id, brand=d["car_brand"], model=d["car_model"], year=d.get("car_year"),
              plate=d.get("car_plate"), vin=vin, body_type=d.get("car_body"))
    session.add(car)
    await session.commit()
    await state.clear()
    await show(event, t(lang, "car_saved") + "\n\n" + t(lang, "car_card", brand=h(car.brand), model=h(car.model),
                                                         year=h(car.year), plate=h(car.plate), vin=h(car.vin),
                                                         body=body_label(lang, car.body_type)),
               markup([btn(t(lang, "btn_book_with_car"), f"car:book:{car.id}")], nav(lang, "car:list")))
