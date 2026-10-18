"""Mechanic interface + shared staff actions (status, ready time, comments).

`router` (masters only) — panel and lists of the mechanic's own jobs.
`staff_router` (masters and owners) — job actions; each one re-checks that the user
may manage this specific request (owner, or the assigned mechanic).
"""
import logging
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import ACTIVE_STATUSES, STATUSES, fmt_dt, now
from ..db import Master, Request, User
from ..i18n import t
from ..middlewares import RoleFilter
from ..services import (PermissionDenied, add_comment, assign_master, can_manage, change_status, get_request,
                        master_accept,
                        master_of, request_card, set_ready_at)
from ..services import client_note, route_url
from ..ui import btn, chunks, h, markup, nav, show, status_label, url_btn

log = logging.getLogger(__name__)
router = Router(name="master")
router.message.filter(RoleFilter("master", "owner"))  # owners listed in MASTER_USERNAMES work as mechanics too
router.callback_query.filter(RoleFilter("master", "owner"))

staff_router = Router(name="staff")
staff_router.message.filter(RoleFilter("master", "owner"))
staff_router.callback_query.filter(RoleFilter("master", "owner"))


class RT(StatesGroup):
    date = State()
    time = State()


class Comment(StatesGroup):
    text = State()


def card_cb(user: User, rid: int) -> str:
    return f"o:r:{rid}" if user.role == "owner" else f"mj:{rid}"


# ---------------- panel ----------------

async def render_panel(event, s: AsyncSession, user: User, lang: str):
    m = await master_of(s, user)
    if m is None:
        return await show(event, t(lang, "access_denied"), markup([btn(t(lang, "btn_client_mode"), "menu:client")]))
    new = await s.scalar(select(func.count(Request.id)).where(
        Request.master_id == m.id, Request.master_accepted.is_(False), Request.status.in_(ACTIVE_STATUSES)))
    work = await s.scalar(select(func.count(Request.id)).where(
        Request.master_id == m.id, Request.master_accepted.is_(True), Request.status.in_(ACTIVE_STATUSES)))
    kb = markup(
        [btn(t(lang, "btn_m_new") + (f" ({new})" if new else ""), "m:new"), btn(t(lang, "btn_m_work"), "m:work")],
        [btn(t(lang, "btn_m_deadlines"), "m:dl"), btn(t(lang, "btn_m_history"), "m:hist")],
        [btn(t(lang, "btn_m_profile"), "m:prof"), btn(t(lang, "btn_lang"), "menu:lang")],
        [btn(t(lang, "btn_client_mode"), "menu:client")],
        [btn("👑 " + t(lang, "btn_home"), "o:menu")] if user.role == "owner" else None,
    )
    await show(event, t(lang, "m_menu", name=h(m.name), new=new, work=work), kb)


@router.callback_query(F.data.in_({"m:menu", "panel"}))
async def cb_panel(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    await cb.answer()
    await render_panel(cb, session, user, lang)


async def _jobs(s: AsyncSession, m: Master, kind: str) -> list[Request]:
    q = select(Request).where(Request.master_id == m.id)
    if kind == "new":
        q = q.where(Request.master_accepted.is_(False), Request.status.in_(ACTIVE_STATUSES)).order_by(Request.id)
    elif kind == "work":
        q = q.where(Request.master_accepted.is_(True), Request.status.in_(ACTIVE_STATUSES)).order_by(Request.id)
    elif kind == "dl":
        q = q.where(Request.status.in_(ACTIVE_STATUSES), Request.status != "ready").order_by(
            Request.ready_at.is_(None), Request.ready_at)
    else:  # history
        q = q.where(Request.status.in_(("ready", "delivered", "cancelled"))).order_by(Request.updated_at.desc()).limit(20)
    return list((await s.scalars(q)).all())


@router.callback_query(F.data.in_({"m:new", "m:work", "m:dl", "m:hist"}))
async def cb_lists(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    m = await master_of(session, user)
    if m is None:
        await cb.answer()
        return await render_panel(cb, session, user, lang)
    kind = cb.data.split(":")[1]
    jobs = await _jobs(session, m, kind)
    await cb.answer()
    title = {"new": "btn_m_new", "work": "btn_m_work", "dl": "m_deadlines_title", "hist": "btn_m_history"}[kind]
    text = f"<b>{t(lang, title)}</b>" if kind != "dl" else t(lang, title)
    rows = []
    current = now()
    for r in jobs:
        label = f"{STATUSES[r.status]} {r.number} · {r.brand} {r.model}"
        if kind == "dl":
            if r.ready_at:
                label += f" · ⏰ {r.ready_at.strftime('%d.%m %H:%M')}"
                if r.ready_at < current:
                    label += " 🔴"
            else:
                label += " · —"
        rows.append([btn(label, f"mj:{r.id}")])
    if not jobs:
        text += "\n\n" + t(lang, "m_empty")
    rows.append(nav(lang, "m:menu"))
    await show(cb, text, markup(*rows))


@router.callback_query(F.data == "m:prof")
async def cb_profile(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    m = await master_of(session, user)
    if m is None:
        await cb.answer()
        return await render_panel(cb, session, user, lang)
    base = select(func.count(Request.id)).where(Request.master_id == m.id)
    work = await session.scalar(base.where(Request.status.in_(ACTIVE_STATUSES), Request.status != "ready"))
    done = await session.scalar(base.where(Request.status.in_(("ready", "delivered"))))
    done30 = await session.scalar(base.where(Request.status.in_(("ready", "delivered")),
                                             Request.closed_at >= now() - timedelta(days=30)))
    await cb.answer()
    await show(cb, t(lang, "m_profile", name=h(m.name), spec=h(m.specialization or "—"), work=work, done=done, done30=done30),
               markup(nav(lang, "m:menu")))


# ---------------- job card (shared) ----------------

def job_kb(r: Request, lang: str, user: User):
    rows = []
    if r.status in ACTIVE_STATUSES:
        if r.master and r.master.user_id == user.id and not r.master_accepted:
            rows.append([btn(t(lang, "btn_m_accept"), f"ma:acc:{r.id}")])
        else:
            st_row = []
            if r.status not in ("diagnostics", "ready"):
                st_row.append(btn(t(lang, "btn_m_diag"), f"ma:diagnostics:{r.id}"))
            if r.status not in ("repair", "ready"):
                st_row.append(btn(t(lang, "btn_m_repair"), f"ma:repair:{r.id}"))
            rows += chunks(st_row, 2)
            if r.status not in ("waiting_parts", "ready"):
                rows.append([btn(t(lang, "btn_m_parts"), f"ma:waiting_parts:{r.id}")])
            rows.append([btn(t(lang, "btn_m_ready_time"), f"rt:{r.id}")])
            rows.append([btn(t(lang, "btn_m_comment"), f"cmt:{r.id}")])
            if r.status != "ready":
                rows.append([btn(t(lang, "btn_m_finish"), f"ma:ready:{r.id}")])
    if r.latitude is not None:
        rows.append([url_btn(t(lang, "btn_route"), route_url(r.latitude, r.longitude))])
    rows.append([btn(t(lang, "btn_history"), f"rq:h:{r.id}"), btn(t(lang, "btn_call_client"), f"st:call:{r.id}")])
    if r.client_user_id:
        rows.append([btn(t(lang, "btn_reply"), f"rp:{r.id}")])
    rows.append(nav(lang, "m:work" if user.role == "master" else f"o:r:{r.id}"))
    return markup(*rows)


async def render_job(event, s: AsyncSession, r: Request, lang: str, user: User | None = None):
    if user is None:
        user = await s.scalar(select(User).where(User.tg_id == event.from_user.id))
    await show(event, request_card(r, lang, staff=True), job_kb(r, lang, user))


async def _load_managed(cb: CallbackQuery, s: AsyncSession, user: User, lang: str, rid: int) -> Request | None:
    r = await get_request(s, rid)
    if r is None or not await can_manage(s, user, r):
        await cb.answer(t(lang, "access_denied"), show_alert=True)
        return None
    return r


@staff_router.callback_query(F.data.regexp(r"^mj:\d+$"))
async def cb_job(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    r = await _load_managed(cb, session, user, lang, int(cb.data.split(":")[1]))
    if r:
        await cb.answer()
        await render_job(cb, session, r, lang, user)


@staff_router.callback_query(F.data.startswith("st:call:"))
async def cb_call_client(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    r = await _load_managed(cb, session, user, lang, int(cb.data.split(":")[2]))
    if r:
        await cb.answer()
        await cb.message.answer_contact(phone_number=r.client_phone, first_name=r.client_name[:60],
                                        last_name=f"· {r.number}")


@staff_router.callback_query(F.data.startswith("ma:"))
async def cb_action(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, bot: Bot):
    _, action, rid = cb.data.split(":")
    r = await _load_managed(cb, session, user, lang, int(rid))
    if not r:
        return
    try:
        if action == "acc":
            await master_accept(session, bot, r, user)
            msg = t(lang, "done_ok")
        elif action in ("diagnostics", "repair", "waiting_parts", "ready"):
            if r.master and r.master.user_id == user.id and not r.master_accepted:
                await master_accept(session, bot, r, user)
            res = await change_status(session, bot, r, action, user)
            msg = t(lang, "status_changed", status=status_label(lang, action)) + client_note(lang, res, r)
        else:
            return await cb.answer()
    except PermissionDenied:
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    await cb.answer(msg)
    r = await get_request(session, r.id)
    await render_job(cb, session, r, lang, user)


@staff_router.callback_query(F.data.startswith("mt:take:"))
async def cb_take(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, bot: Bot):
    """First mechanic to tap «🙋 Взять заявку» gets the request."""
    r = await get_request(session, int(cb.data.split(":")[2]))
    m = await master_of(session, user)
    if r is None or m is None:
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    if r.master_id and r.master_id != m.id:
        return await cb.answer(t(lang, "take_taken"), show_alert=True)
    if r.master_id != m.id:
        await assign_master(session, bot, r, m, user)
        await master_accept(session, bot, await get_request(session, r.id), user)
    await cb.answer(t(lang, "take_ok"))
    await render_job(cb, session, await get_request(session, r.id), lang, user)


# ---------------- ready time ----------------

def _date_kb(lang: str, back: str):
    today = now().date()
    days = [today + timedelta(days=i) for i in range(7)]
    labels = [t(lang, "rt_today"), t(lang, "rt_tomorrow")] + [d.strftime("%d.%m") for d in days[2:]]
    btns = [btn(f"📅 {lbl}", f"rt:d:{d.strftime('%Y%m%d')}") for lbl, d in zip(labels, days)]
    return markup(*chunks(btns, 3), nav(lang, back))


def _time_kb(lang: str, back: str):
    times = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "18:30", "19:00",
             "19:30", "20:00"]
    return markup(*chunks([btn(f"🕐 {x}", f"rt:t:{x.replace(':', '')}") for x in times], 4), nav(lang, "rt:back"))


@staff_router.callback_query(F.data.regexp(r"^rt:\d+$"))
async def cb_rt_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    r = await _load_managed(cb, session, user, lang, int(cb.data.split(":")[1]))
    if not r:
        return
    await cb.answer()
    await state.set_state(RT.date)
    await state.update_data(rt_rid=r.id)
    await show(cb, t(lang, "rt_date") + f"\n\n🎫 {r.number}", _date_kb(lang, card_cb(user, r.id)))


async def _rt_set_date(event, state: FSMContext, lang: str, d: datetime):
    await state.update_data(rt_date=d.strftime("%Y-%m-%d"))
    await state.set_state(RT.time)
    await show(event, t(lang, "rt_time", date=d.strftime("%d.%m.%Y")), _time_kb(lang, "rt:back"))


@staff_router.callback_query(F.data == "rt:back")
async def cb_rt_back(cb: CallbackQuery, state: FSMContext, user: User, lang: str):
    data = await state.get_data()
    if not data.get("rt_rid"):
        return await cb.answer(t(lang, "bk_expired"), show_alert=True)
    await cb.answer()
    await state.set_state(RT.date)
    await show(cb, t(lang, "rt_date"), _date_kb(lang, card_cb(user, data["rt_rid"])))


@staff_router.callback_query(F.data.startswith("rt:d:"), RT.date)
async def cb_rt_date(cb: CallbackQuery, state: FSMContext, lang: str):
    await cb.answer()
    await _rt_set_date(cb, state, lang, datetime.strptime(cb.data.split(":")[2], "%Y%m%d"))


@staff_router.message(RT.date, F.text)
async def msg_rt_date(message: Message, state: FSMContext, lang: str):
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
    await _rt_set_date(message, state, lang, d)


async def _rt_finish(event, state: FSMContext, session: AsyncSession, user: User, lang: str, bot: Bot, hhmm: str):
    data = await state.get_data()
    try:
        when = datetime.strptime(f"{data['rt_date']} {hhmm}", "%Y-%m-%d %H:%M")
    except (KeyError, ValueError):
        return await show(event, t(lang, "rt_bad_time"))
    if when < now():
        return await show(event, t(lang, "rt_past"), _time_kb(lang, "rt:back"))
    r = await get_request(session, data["rt_rid"])
    try:
        if r is None:
            raise PermissionDenied
        await set_ready_at(session, bot, r, when, user)
    except PermissionDenied:
        await state.clear()
        return await show(event, t(lang, "access_denied"))
    await state.clear()
    await show(event, t(lang, "rt_saved", when=when.strftime("%d.%m.%Y в %H:%M") if lang == "ru" else fmt_dt(when)),
               markup([btn(t(lang, "btn_open_request"), card_cb(user, r.id))], nav(lang)))


@staff_router.callback_query(F.data.startswith("rt:t:"), RT.time)
async def cb_rt_time(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str, bot: Bot):
    raw = cb.data.split(":")[2]
    await cb.answer()
    await _rt_finish(cb, state, session, user, lang, bot, f"{raw[:2]}:{raw[2:]}")


@staff_router.message(RT.time, F.text)
async def msg_rt_time(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str, bot: Bot):
    raw = message.text.strip().replace(".", ":").replace(" ", "")
    try:
        hhmm = datetime.strptime(raw, "%H:%M").strftime("%H:%M")
    except ValueError:
        return await message.answer(t(lang, "rt_bad_time"))
    await _rt_finish(message, state, session, user, lang, bot, hhmm)


# ---------------- comments ----------------

@staff_router.callback_query(F.data.startswith("cmt:"))
async def cb_comment(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    r = await _load_managed(cb, session, user, lang, int(cb.data.split(":")[1]))
    if not r:
        return
    await cb.answer()
    await state.set_state(Comment.text)
    await state.update_data(cmt_rid=r.id)
    await show(cb, t(lang, "comment_write") + f"\n\n🎫 {r.number}", markup(nav(lang, card_cb(user, r.id))))


@staff_router.message(Comment.text, F.text)
async def msg_comment(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str, bot: Bot):
    data = await state.get_data()
    r = await get_request(session, data.get("cmt_rid", 0))
    text = message.text.strip()[:1500]
    try:
        if r is None:
            raise PermissionDenied
        await add_comment(session, bot, r, text, user)
    except PermissionDenied:
        await state.clear()
        return await message.answer(t(lang, "access_denied"))
    await state.clear()
    await message.answer(t(lang, "comment_saved"),
                         reply_markup=markup([btn(t(lang, "btn_open_request"), card_cb(user, r.id))], nav(lang)))
