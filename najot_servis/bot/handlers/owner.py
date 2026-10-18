"""Owner (👑) control panel. The whole router is restricted to role=owner on the server side."""
import logging
import math
import secrets
from datetime import timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import (ACTIVE_STATUSES, BODY_TYPES, DEFAULT_SETTINGS, DONE_STATUSES, IN_WORK_STATUSES, MOBILITY,
                      SERVICES, STATUSES, config, now, parse_coords)
from ..db import Car, Invite, Master, Owner, Request, RequestHistory, Setting, User, get_settings
from ..i18n import LANGS, t
from ..middlewares import RoleFilter
from ..services import (PermissionDenied, add_history, assign_master, change_status, get_request, request_card)
from ..services import client_note, route_url
from ..ui import (PAGE_SIZE, body_label, btn, chunks, h, markup, mobility_label, nav, pager, service_label, show,
                  status_label, url_btn)
from .booking import normalize_phone, parse_year, start_booking

log = logging.getLogger(__name__)
router = Router(name="owner")
router.message.filter(RoleFilter("owner"))
router.callback_query.filter(RoleFilter("owner"))


class OwnerInput(StatesGroup):
    search = State()
    edit_field = State()
    setting = State()
    master_spec = State()


# ---------------- panel ----------------

async def render_panel(event, s: AsyncSession, user: User, lang: str):
    cnt = lambda *conds: s.scalar(select(func.count(Request.id)).where(*conds))  # noqa: E731
    start = now().replace(hour=0, minute=0, second=0)
    text = t(lang, "o_menu", new=await cnt(Request.status == "new"), work=await cnt(Request.status.in_(IN_WORK_STATUSES)),
             ready=await cnt(Request.status == "ready"), today=await cnt(Request.created_at >= start))
    kb = markup(
        [btn(t(lang, "btn_o_all"), "o:l:all:0"), btn(t(lang, "btn_o_new"), "o:l:new:0")],
        [btn(t(lang, "btn_o_work"), "o:l:work:0"), btn(t(lang, "btn_o_done"), "o:l:done:0")],
        [btn(t(lang, "btn_o_cancelled"), "o:l:cx:0"), btn(t(lang, "btn_o_search"), "o:search")],
        [btn(t(lang, "btn_o_create"), "o:create")],
        [btn(t(lang, "btn_o_masters"), "o:masters"), btn(t(lang, "btn_o_clients"), "o:users:0")],
        [btn(t(lang, "btn_o_cars"), "o:cars:0"), btn(t(lang, "btn_o_stats"), "o:stats")],
        [btn(t(lang, "btn_m_work"), "m:menu")] if await s.scalar(
            select(Master.id).where(Master.user_id == user.id, Master.is_active.is_(True))) else None,
        [btn(t(lang, "btn_o_settings"), "o:set"), btn(t(lang, "btn_lang"), "menu:lang")],
        [btn(t(lang, "btn_client_mode"), "menu:client")],
    )
    await show(event, text, kb)


@router.callback_query(F.data.in_({"o:menu", "panel"}))
async def cb_menu(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    await cb.answer()
    await render_panel(cb, session, user, lang)


@router.message(F.text.in_({"/panel", "/admin"}))
async def cmd_panel(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await state.clear()
    await render_panel(message, session, user, lang)


# ---------------- request lists ----------------

LIST_FILTERS = {
    "all": ("list_all", None),
    "new": ("list_new", Request.status == "new"),
    "work": ("list_work", Request.status.in_(IN_WORK_STATUSES)),
    "done": ("list_done", Request.status.in_(DONE_STATUSES)),
    "cx": ("list_cancelled", Request.status == "cancelled"),
}


def _filter(key: str):
    """Returns (title_key, condition, back). Supports per-master (m<id>) and per-user (u<id>) lists."""
    if key in LIST_FILTERS:
        title, cond = LIST_FILTERS[key]
        return title, cond, "o:menu"
    if key.startswith("m") and key[1:].isdigit():
        return "btn_m_jobs", Request.master_id == int(key[1:]), f"o:mst:{key[1:]}"
    if key.startswith("u") and key[1:].isdigit():
        return "btn_user_requests", Request.client_user_id == int(key[1:]), f"o:u:{key[1:]}"
    return "list_all", None, "o:menu"


async def render_list(event, s: AsyncSession, lang: str, key: str, page: int, conds=None, title_key=None, back=None):
    if conds is None:
        title_key, cond, back = _filter(key)
        conds = [cond] if cond is not None else []
    total = await s.scalar(select(func.count(Request.id)).where(*conds))
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    rows = (await s.scalars(select(Request).where(*conds).order_by(Request.id.desc())
                            .offset(page * PAGE_SIZE).limit(PAGE_SIZE))).all()
    kb = [[btn(f"{STATUSES[r.status]} {r.number} · {r.brand} {r.model} · {r.client_name[:12]}", f"o:r:{r.id}")]
          for r in rows]
    if key:
        kb.append(pager(lang, f"o:l:{key}", page, pages))
    kb.append(nav(lang, back or "o:menu"))
    title = t(lang, title_key)
    if not title.startswith("<b>") and "<b>" not in title:
        title = f"<b>{title}</b>"
    text = f"{title}\n{t(lang, 'list_count', n=total, p=page + 1, pages=pages)}"
    if not total:
        text += "\n\n" + t(lang, "m_empty")
    await show(event, text, markup(*kb))


@router.callback_query(F.data.startswith("o:l:"))
async def cb_list(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    _, _, key, page = cb.data.split(":")
    await state.clear()
    await cb.answer()
    await render_list(cb, session, lang, key, int(page))


@router.callback_query(F.data == "o:search")
async def cb_search(cb: CallbackQuery, state: FSMContext, lang: str):
    await cb.answer()
    await state.set_state(OwnerInput.search)
    await show(cb, t(lang, "o_search_ask"), markup(nav(lang, "o:menu")))


@router.message(OwnerInput.search, F.text)
async def msg_search(message: Message, state: FSMContext, session: AsyncSession, lang: str):
    q = message.text.strip()[:40]
    await state.clear()
    digits = "".join(ch for ch in q if ch.isdigit())
    conds = [Request.client_name.ilike(f"%{q}%"), Request.brand.ilike(f"%{q}%"), Request.model.ilike(f"%{q}%"),
             Request.plate.ilike(f"%{q.replace(' ', '').upper()}%")]
    if digits:
        conds.append(Request.client_phone.like(f"%{digits}%"))
        conds.append(Request.id == int(digits))
    await render_list(message, session, lang, "", 0, conds=[or_(*conds)], title_key="list_search", back="o:menu")


# ---------------- request card ----------------

def owner_req_kb(r: Request, lang: str):
    rows = []
    if r.status == "new":
        rows.append([btn(t(lang, "btn_accept"), f"o:acc:{r.id}")])
    rows += [
        [btn(t(lang, "btn_o_status"), f"o:st:{r.id}"), btn(t(lang, "btn_assign_master"), f"o:as:{r.id}")],
        [btn(t(lang, "btn_o_ready"), f"rt:{r.id}"), btn(t(lang, "btn_m_comment"), f"cmt:{r.id}")],
        [btn(t(lang, "btn_o_edit"), f"o:ed:{r.id}"), btn(t(lang, "btn_history"), f"rq:h:{r.id}")],
        [btn(t(lang, "btn_call_client"), f"o:call:{r.id}"), btn(t(lang, "btn_reply"), f"rp:{r.id}")],
        [url_btn(t(lang, "btn_route"), route_url(r.latitude, r.longitude))] if r.latitude is not None else None,
        [btn(t(lang, "btn_o_delete"), f"o:del:{r.id}")],
        nav(lang, "o:l:all:0"),
    ]
    return markup(*rows)


async def render_request(event, s: AsyncSession, r: Request, lang: str):
    await show(event, request_card(r, lang, staff=True), owner_req_kb(r, lang))


async def _req(cb: CallbackQuery, s: AsyncSession, lang: str, idx: int = 2) -> Request | None:
    r = await get_request(s, int(cb.data.split(":")[idx]))
    if r is None:
        await cb.answer(t(lang, "not_found"), show_alert=True)
    return r


@router.callback_query(F.data.startswith("o:r:"))
async def cb_request(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    await state.clear()
    r = await _req(cb, session, lang)
    if r:
        await cb.answer()
        await render_request(cb, session, r, lang)


@router.callback_query(F.data.startswith("o:acc:"))
async def cb_accept(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, bot: Bot):
    r = await _req(cb, session, lang)
    if not r:
        return
    if r.status == "new":
        res = await change_status(session, bot, r, "accepted", user)
        return await _status_done(cb, session, r, lang, "accepted", res)
    await cb.answer(t(lang, "status_changed", status=status_label(lang, r.status)))
    await render_request(cb, session, await get_request(session, r.id), lang)


@router.callback_query(F.data.startswith("o:call:"))
async def cb_call(cb: CallbackQuery, session: AsyncSession, lang: str):
    r = await _req(cb, session, lang)
    if r:
        await cb.answer()
        await cb.message.answer_contact(phone_number=r.client_phone, first_name=r.client_name[:60], last_name=f"· {r.number}")


@router.callback_query(F.data.startswith("o:st:"))
async def cb_status_menu(cb: CallbackQuery, session: AsyncSession, lang: str):
    r = await _req(cb, session, lang)
    if not r:
        return
    await cb.answer()
    btns = [btn(("• " if code == r.status else "") + status_label(lang, code), f"o:sts:{r.id}:{code}") for code in STATUSES]
    await show(cb, t(lang, "o_choose_status") + f"\n🎫 {r.number}", markup(*chunks(btns, 2), nav(lang, f"o:r:{r.id}")))


@router.callback_query(F.data.startswith("o:sts:"))
async def cb_status_set(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, bot: Bot):
    _, _, rid, code = cb.data.split(":")
    r = await get_request(session, int(rid))
    if r is None or code not in STATUSES:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    res = await change_status(session, bot, r, code, user)
    await _status_done(cb, session, r, lang, code, res)


async def _status_done(cb: CallbackQuery, session: AsyncSession, r: Request, lang: str, code: str, res: str):
    """Pop-up: new status + whether the client got the message."""
    await cb.answer(t(lang, "status_changed", status=status_label(lang, code)) + client_note(lang, res, r),
                    show_alert=res in ("sent", "failed", "no_client"))
    await render_request(cb, session, await get_request(session, r.id), lang)


@router.callback_query(F.data.regexp(r"^o:as:\d+$"))
async def cb_assign_menu(cb: CallbackQuery, session: AsyncSession, lang: str):
    r = await _req(cb, session, lang)
    if not r:
        return
    masters = (await session.scalars(select(Master).where(Master.is_active.is_(True)).order_by(Master.name))).all()
    await cb.answer()
    if not masters:
        return await show(cb, t(lang, "o_no_masters"),
                          markup([btn(t(lang, "btn_add_master"), "o:madd")], nav(lang, f"o:r:{r.id}")))
    # current workload helps the owner choose
    loads = dict((await session.execute(
        select(Request.master_id, func.count(Request.id)).where(Request.status.in_(ACTIVE_STATUSES))
        .group_by(Request.master_id))).all())
    rows = [[btn(("✅ " if m.id == r.master_id else "👨‍🔧 ") + f"{m.name} · 🔧{loads.get(m.id, 0)}"
                 + (f" · {m.specialization}" if m.specialization else ""), f"o:asm:{r.id}:{m.id}")] for m in masters]
    if r.master_id:
        rows.append([btn(t(lang, "btn_unassign"), f"o:asm:{r.id}:0")])
    rows.append(nav(lang, f"o:r:{r.id}"))
    await show(cb, t(lang, "o_choose_master") + f"\n🎫 {r.number}", markup(*rows))


@router.callback_query(F.data.startswith("o:asm:"))
async def cb_assign(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, bot: Bot):
    _, _, rid, mid = cb.data.split(":")
    r = await get_request(session, int(rid))
    if r is None:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    m = await session.get(Master, int(mid)) if mid != "0" else None
    if mid != "0" and (m is None or not m.is_active):
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    await assign_master(session, bot, r, m, user)
    await cb.answer(t(lang, "o_assigned_ok", name=m.name if m else "—"))
    await render_request(cb, session, await get_request(session, r.id), lang)


# ---------------- edit / delete ----------------

EDIT_FIELDS = ["brand", "model", "year", "body", "plate", "problem", "service", "mobility", "name", "phone"]
CHOICE_FIELDS = {  # field -> (options, request attribute, label function)
    "service": (SERVICES, "service_code", service_label),
    "body": (BODY_TYPES, "body_type", body_label),
    "mobility": (MOBILITY, "mobility", mobility_label),
}


@router.callback_query(F.data.regexp(r"^o:ed:\d+$"))
async def cb_edit_menu(cb: CallbackQuery, session: AsyncSession, lang: str):
    r = await _req(cb, session, lang)
    if not r:
        return
    await cb.answer()
    rows = chunks([btn(t(lang, "f_" + f), f"o:edf:{r.id}:{f}") for f in EDIT_FIELDS], 2)
    rows.append(nav(lang, f"o:r:{r.id}"))
    await show(cb, t(lang, "o_edit_what") + f"\n🎫 {r.number}", markup(*rows))


@router.callback_query(F.data.startswith("o:edf:"))
async def cb_edit_field(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    _, _, rid, field = cb.data.split(":")
    if field not in EDIT_FIELDS:
        return await cb.answer()
    await cb.answer()
    if field in CHOICE_FIELDS:
        options, _, label = CHOICE_FIELDS[field]
        btns = [btn(label(lang, code), f"o:eds:{rid}:{field}:{code}") for code, _ in options]
        return await show(cb, t(lang, "o_edit_enter", field=t(lang, "f_" + field)),
                          markup(*chunks(btns, 1), nav(lang, f"o:ed:{rid}")))
    await state.set_state(OwnerInput.edit_field)
    await state.update_data(ed_rid=int(rid), ed_field=field)
    await show(cb, t(lang, "o_edit_enter", field=t(lang, "f_" + field)), markup(nav(lang, f"o:ed:{rid}")))


@router.callback_query(F.data.startswith("o:eds:"))
async def cb_edit_service(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    _, _, rid, field, code = cb.data.split(":")
    r = await get_request(session, int(rid))
    if r is None or field not in CHOICE_FIELDS or code not in dict(CHOICE_FIELDS[field][0]):
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    attr = CHOICE_FIELDS[field][1]
    old = getattr(r, attr)
    setattr(r, attr, code)
    add_history(session, r, user, "edited", f"{field}: {old} → {code}")
    await session.commit()
    await cb.answer(t(lang, "o_edit_saved"))
    await render_request(cb, session, await get_request(session, r.id), lang)


@router.message(OwnerInput.edit_field, F.text)
async def msg_edit_value(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str):
    data = await state.get_data()
    r = await get_request(session, data.get("ed_rid", 0))
    field = data.get("ed_field")
    if r is None or field not in EDIT_FIELDS:
        await state.clear()
        return await message.answer(t(lang, "not_found"))
    raw = message.text.strip()
    attr = {"name": "client_name", "phone": "client_phone"}.get(field, field)
    if field == "year":
        value = parse_year(raw)
        if value is None:
            return await message.answer(t(lang, "bk_bad_year", max=now().year + 1))
    elif field == "phone":
        value = normalize_phone(raw)
        if not value:
            return await message.answer(t(lang, "bk_bad_phone"))
    elif field == "plate":
        value = raw.upper().replace(" ", "")[:20]
    else:
        limit = 1000 if field == "problem" else 60
        if not raw or len(raw) > limit:
            return await message.answer(t(lang, "bk_too_long", n=limit))
        value = raw
    old = getattr(r, attr)
    setattr(r, attr, value)
    add_history(session, r, user, "edited", f"{field}: {old} → {value}")
    await session.commit()
    await state.clear()
    await message.answer(t(lang, "o_edit_saved"))
    await render_request(message, session, await get_request(session, r.id), lang)


@router.callback_query(F.data.regexp(r"^o:del:\d+$"))
async def cb_delete_ask(cb: CallbackQuery, session: AsyncSession, lang: str):
    r = await _req(cb, session, lang)
    if r:
        await cb.answer()
        await show(cb, t(lang, "o_delete_confirm", number=r.number),
                   markup([btn(t(lang, "btn_yes"), f"o:dely:{r.id}"), btn(t(lang, "btn_no"), f"o:r:{r.id}")]))


@router.callback_query(F.data.startswith("o:dely:"))
async def cb_delete(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    r = await _req(cb, session, lang)
    if not r:
        return
    number = r.number
    await session.execute(RequestHistory.__table__.delete().where(RequestHistory.request_id == r.id))
    await session.delete(r)
    await session.commit()
    log.warning("request %s deleted by owner tg=%s", number, user.tg_id)
    await cb.answer(t(lang, "o_deleted", number=number))
    await render_list(cb, session, lang, "all", 0)


# ---------------- create request ----------------

@router.callback_query(F.data == "o:create")
async def cb_create(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    await cb.answer()
    await start_booking(cb, state, session, user, lang, mode="owner")


# ---------------- masters ----------------

@router.callback_query(F.data == "o:masters")
async def cb_masters(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    await state.clear()
    await cb.answer()
    await render_masters(cb, session, lang)


async def render_masters(event, session: AsyncSession, lang: str):
    masters = (await session.scalars(select(Master).order_by(Master.is_active.desc(), Master.name))).all()
    rows = [[btn(("🟢 " if m.is_active else "⚪ ") + m.name + (f" · {m.specialization}" if m.specialization else ""),
                 f"o:mst:{m.id}")] for m in masters]
    rows.append([btn(t(lang, "btn_add_master"), "o:madd")])
    rows.append(nav(lang, "o:menu"))
    await show(event, t(lang, "o_masters_title") + ("" if masters else "\n\n" + t(lang, "m_empty")), markup(*rows))


@router.callback_query(F.data == "o:madd")
async def cb_master_add(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, bot: Bot):
    token = secrets.token_urlsafe(12)
    session.add(Invite(token=token, role="master", created_by=user.id))
    await session.commit()
    me = await bot.me()
    await cb.answer()
    await show(cb, t(lang, "o_invite", link=f"https://t.me/{me.username}?start=m_{token}"), markup(nav(lang, "o:masters")))


async def render_master(event, s: AsyncSession, m: Master, lang: str):
    base = select(func.count(Request.id)).where(Request.master_id == m.id)
    work = await s.scalar(base.where(Request.status.in_(IN_WORK_STATUSES)))
    done = await s.scalar(base.where(Request.status.in_(DONE_STATUSES)))
    tg = f"@{m.user.username}" if m.user and m.user.username else (str(m.user.tg_id) if m.user else "—")
    text = t(lang, "o_master_card", name=h(m.name), active="🟢" if m.is_active else "⚪", tg=h(tg),
             spec=h(m.specialization or "—"), work=work, done=done)
    kb = markup(
        [btn(t(lang, "btn_m_jobs"), f"o:l:m{m.id}:0")],
        [btn(t(lang, "btn_m_spec"), f"o:mspec:{m.id}"),
         btn(t(lang, "btn_m_toggle_off" if m.is_active else "btn_m_toggle_on"), f"o:mtog:{m.id}")],
        [btn(t(lang, "btn_m_remove"), f"o:mrm:{m.id}")],
        nav(lang, "o:masters"),
    )
    await show(event, text, kb)


async def _master(cb: CallbackQuery, s: AsyncSession, lang: str) -> Master | None:
    m = await s.get(Master, int(cb.data.split(":")[2]))
    if m is None:
        await cb.answer(t(lang, "not_found"), show_alert=True)
    return m


@router.callback_query(F.data.startswith("o:mst:"))
async def cb_master(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    await state.clear()
    m = await _master(cb, session, lang)
    if m:
        await cb.answer()
        await render_master(cb, session, m, lang)


@router.callback_query(F.data.startswith("o:mtog:"))
async def cb_master_toggle(cb: CallbackQuery, session: AsyncSession, lang: str):
    m = await _master(cb, session, lang)
    if not m:
        return
    m.is_active = not m.is_active
    await session.commit()
    await cb.answer(t(lang, "done_ok"))
    await render_master(cb, session, m, lang)


@router.callback_query(F.data.startswith("o:mspec:"))
async def cb_master_spec(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    m = await _master(cb, session, lang)
    if not m:
        return
    await cb.answer()
    await state.set_state(OwnerInput.master_spec)
    await state.update_data(mspec_id=m.id)
    await show(cb, t(lang, "o_spec_enter"), markup(nav(lang, f"o:mst:{m.id}")))


@router.message(OwnerInput.master_spec, F.text)
async def msg_master_spec(message: Message, state: FSMContext, session: AsyncSession, lang: str):
    m = await session.get(Master, (await state.get_data()).get("mspec_id", 0))
    await state.clear()
    if not m:
        return await message.answer(t(lang, "not_found"))
    m.specialization = message.text.strip()[:120]
    await session.commit()
    await render_master(message, session, m, lang)


@router.callback_query(F.data.startswith("o:mrm:"))
async def cb_master_remove(cb: CallbackQuery, session: AsyncSession, user: User, lang: str):
    m = await _master(cb, session, lang)
    if not m:
        return
    m.is_active = False
    if m.user and m.user.role == "master":
        m.user.role = "client"
    await session.commit()
    log.info("master %s removed by %s", m.id, user.tg_id)
    await cb.answer(t(lang, "done_ok"))
    await render_masters(cb, session, lang)


# ---------------- users / clients ----------------

@router.callback_query(F.data.startswith("o:users:"))
async def cb_users(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    await state.clear()
    page = int(cb.data.split(":")[2])
    total = await session.scalar(select(func.count(User.id)))
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    req_cnt = select(func.count(Request.id)).where(Request.client_user_id == User.id).scalar_subquery()
    rows = (await session.execute(select(User, req_cnt).order_by(User.id.desc())
                                  .offset(page * PAGE_SIZE).limit(PAGE_SIZE))).all()
    icon = {"owner": "👑", "master": "👨‍🔧", "client": "👤", "blocked": "🚫"}
    kb = [[btn(f"{icon.get(u.role, '👤')} {u.full_name or u.username or u.tg_id} · 📋{n}" + (f" · {u.phone}" if u.phone else ""),
               f"o:u:{u.id}")] for u, n in rows]
    kb.append(pager(lang, "o:users", page, pages))
    kb.append(nav(lang, "o:menu"))
    await cb.answer()
    await show(cb, t(lang, "o_users_title") + "\n" + t(lang, "list_count", n=total, p=page + 1, pages=pages), markup(*kb))


async def render_user(event, s: AsyncSession, u: User, lang: str):
    reqs = await s.scalar(select(func.count(Request.id)).where(Request.client_user_id == u.id))
    cars = await s.scalar(select(func.count(Car.id)).where(Car.user_id == u.id))
    text = t(lang, "o_user_card", name=h(u.full_name or "—"), tg=h(f"@{u.username}" if u.username else "—"), tg_id=u.tg_id,
             phone=h(u.phone or "—"), role=t(lang, "role_" + u.role), ulang=LANGS.get(u.lang or "", "—"), reqs=reqs,
             cars=cars, created=u.created_at.strftime("%d.%m.%Y"))
    rows = [[btn(t(lang, "btn_user_requests"), f"o:l:u{u.id}:0")]]
    role_btns = []
    if u.role != "master":
        role_btns.append(btn(t(lang, "btn_make_master"), f"o:role:{u.id}:master"))
    if u.role not in ("client",):
        role_btns.append(btn(t(lang, "btn_make_client"), f"o:role:{u.id}:client"))
    rows += chunks(role_btns, 2)
    rows.append([btn(t(lang, "btn_unblock"), f"o:role:{u.id}:client")] if u.role == "blocked"
                else [btn(t(lang, "btn_block"), f"o:role:{u.id}:blocked")])
    rows.append(nav(lang, "o:users:0"))
    await show(event, text, markup(*rows))


@router.callback_query(F.data.startswith("o:u:"))
async def cb_user(cb: CallbackQuery, session: AsyncSession, lang: str):
    u = await session.get(User, int(cb.data.split(":")[2]))
    if not u:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    await cb.answer()
    await render_user(cb, session, u, lang)


@router.callback_query(F.data.startswith("o:role:"))
async def cb_role(cb: CallbackQuery, session: AsyncSession, user: User, lang: str, bot: Bot):
    _, _, uid, role = cb.data.split(":")
    if role not in ("client", "master", "blocked"):  # owners are set only in .env (OWNER_USERNAMES)
        return await cb.answer()
    u = await session.get(User, int(uid))
    if not u:
        return await cb.answer(t(lang, "not_found"), show_alert=True)
    if u.id == user.id:
        return await cb.answer(t(lang, "o_cant_self"), show_alert=True)
    protected = u.tg_id in config.owner_ids or (u.username or "").lower() in config.owner_usernames
    if protected and role != "owner":
        return await cb.answer(t(lang, "access_denied"), show_alert=True)
    u.role = role
    m = await session.scalar(select(Master).where(Master.user_id == u.id))
    if role == "master":
        if m:
            m.is_active = True
        else:
            session.add(Master(user_id=u.id, name=u.full_name or (u.username or str(u.tg_id))))
    elif m:
        m.is_active = False
    owner_row = await session.scalar(select(Owner).where(Owner.user_id == u.id))
    if role == "owner" and not owner_row:
        session.add(Owner(user_id=u.id))
    elif role != "owner" and owner_row:
        await session.delete(owner_row)
    await session.commit()
    log.warning("role of tg=%s changed to %s by tg=%s", u.tg_id, role, user.tg_id)
    if role == "master":
        try:
            await bot.send_message(u.tg_id, t(u.lang, "inv_ok"))
        except Exception:
            pass
    await cb.answer(t(lang, "o_role_changed", role=t(lang, "role_" + role)))
    await render_user(cb, session, u, lang)


# ---------------- cars ----------------

@router.callback_query(F.data.startswith("o:cars:"))
async def cb_cars(cb: CallbackQuery, session: AsyncSession, lang: str):
    page = int(cb.data.split(":")[2])
    total = await session.scalar(select(func.count(Car.id)))
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    rows = (await session.execute(select(Car, User).join(User, User.id == Car.user_id, isouter=True)
                                  .order_by(Car.id.desc()).offset(page * PAGE_SIZE).limit(PAGE_SIZE))).all()
    lines = [t(lang, "o_cars_title"), t(lang, "list_count", n=total, p=page + 1, pages=pages), ""]
    kb = []
    for car, u in rows:
        lines.append(f"🚗 <b>{h(car.brand)} {h(car.model)}</b> {h(car.year)} · {h(car.plate or '—')}"
                     + (f" · VIN {h(car.vin)}" if car.vin else "")
                     + (f"\n    👤 {h(u.full_name)} {h(u.phone or '')}" if u else ""))
        if u:
            kb.append([btn(f"👤 {car.brand} {car.model} → {u.full_name[:20]}", f"o:u:{u.id}")])
    kb.append(pager(lang, "o:cars", page, pages))
    kb.append(nav(lang, "o:menu"))
    await cb.answer()
    await show(cb, "\n".join(lines), markup(*kb))


# ---------------- statistics ----------------

@router.callback_query(F.data == "o:stats")
async def cb_stats(cb: CallbackQuery, session: AsyncSession, lang: str):
    s = session
    cnt = lambda *c: s.scalar(select(func.count(Request.id)).where(*c))  # noqa: E731
    current = now()
    day0 = current.replace(hour=0, minute=0, second=0)
    top_rows = (await s.execute(select(Request.service_code, func.count(Request.id).label("n"))
                                .where(Request.status != "cancelled")
                                .group_by(Request.service_code).order_by(func.count(Request.id).desc()).limit(5))).all()
    total_nc = sum(n for _, n in top_rows) or 1
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    top = "\n".join(f"{medals[i]} {service_label(lang, code)} — <b>{n}</b> ({round(n * 100 / total_nc)}%)"
                    for i, (code, n) in enumerate(top_rows)) or "—"
    mrows = (await s.execute(select(Master.name, func.count(Request.id)).join(Request, Request.master_id == Master.id)
                             .where(Request.status.in_(DONE_STATUSES)).group_by(Master.id, Master.name)
                             .order_by(func.count(Request.id).desc()).limit(5))).all()
    mtop = "\n".join(f"👨‍🔧 {h(name)} — <b>{n}</b>" for name, n in mrows) or "—"
    closed = (await s.execute(select(Request.created_at, Request.closed_at)
                              .where(Request.status.in_(DONE_STATUSES), Request.closed_at.is_not(None))
                              .order_by(Request.id.desc()).limit(200))).all()
    if closed:
        hours = sum((c - a).total_seconds() for a, c in closed) / len(closed) / 3600
        avg = f"{hours:.1f} h" if hours < 48 else f"{hours / 24:.1f} d"
    else:
        avg = "—"
    text = t(lang, "stats",
             total=await cnt(), new=await cnt(Request.status == "new"),
             work=await cnt(Request.status.in_(IN_WORK_STATUSES)), done=await cnt(Request.status.in_(DONE_STATUSES)),
             cancelled=await cnt(Request.status == "cancelled"),
             today=await cnt(Request.created_at >= day0),
             week=await cnt(Request.created_at >= day0 - timedelta(days=day0.weekday())),
             month=await cnt(Request.created_at >= day0.replace(day=1)),
             sos=await cnt(Request.mobility.in_(("onsite", "tow"))),
             avg=avg, clients=await s.scalar(select(func.count(User.id)).where(User.role == "client")),
             masters=await s.scalar(select(func.count(Master.id)).where(Master.is_active.is_(True))),
             top=top, mtop=mtop)
    await cb.answer()
    await show(cb, text, markup([btn("🔄", "o:stats")], nav(lang, "o:menu")))


# ---------------- settings ----------------

@router.callback_query(F.data == "o:set")
async def cb_settings(cb: CallbackQuery, state: FSMContext, session: AsyncSession, lang: str):
    await state.clear()
    await cb.answer()
    await _render_settings(cb, session, lang)


async def _render_settings(event, s: AsyncSession, lang: str):
    st = await get_settings(s)
    chat = (" + " + ", ".join(h(x) for x in config.notify_targets)) if config.notify_targets else ""
    text = t(lang, "o_settings", **{k: h(v) for k, v in st.items() if k in DEFAULT_SETTINGS}, chat=chat)
    btns = [btn(t(lang, "set_" + k), f"o:setk:{k}") for k in DEFAULT_SETTINGS]
    await show(event, text, markup(*chunks(btns, 2), nav(lang, "o:menu")))


@router.callback_query(F.data.startswith("o:setk:"))
async def cb_setting_key(cb: CallbackQuery, state: FSMContext, lang: str):
    key = cb.data.split(":")[2]
    if key not in DEFAULT_SETTINGS:
        return await cb.answer()
    await cb.answer()
    await state.set_state(OwnerInput.setting)
    await state.update_data(set_key=key)
    prompt = t(lang, "set_location_hint") if key == "location" else t(lang, "o_edit_enter", field=t(lang, "set_" + key))
    await show(cb, prompt, markup(nav(lang, "o:set")))


@router.message(OwnerInput.setting, F.location)
async def msg_setting_location(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str):
    if (await state.get_data()).get("set_key") != "location":
        return
    await _save_setting(message, state, session, user, lang, "location",
                        f"{message.location.latitude:.6f},{message.location.longitude:.6f}")


async def _save_setting(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str,
                        key: str, value: str):
    await state.clear()
    row = await session.get(Setting, key)
    if row:
        row.value = value
    else:
        session.add(Setting(key=key, value=value))
    await session.commit()
    log.info("setting %s changed by %s", key, user.tg_id)
    await message.answer(t(lang, "o_edit_saved"))
    await _render_settings(message, session, lang)


@router.message(OwnerInput.setting, F.text)
async def msg_setting(message: Message, state: FSMContext, session: AsyncSession, user: User, lang: str):
    key = (await state.get_data()).get("set_key")
    if key not in DEFAULT_SETTINGS:
        return await state.clear()
    value = message.text.strip()[:300]
    if key in ("telegram", "instagram"):
        value = value.lstrip("@").replace("https://t.me/", "").replace("https://instagram.com/", "").strip("/")
    if key == "phone":
        value = normalize_phone(value) or value
    if key == "location":
        coords = parse_coords(value)
        if not coords:
            return await message.answer(t(lang, "set_location_bad") + "\n\n" + t(lang, "set_location_hint"))
        value = f"{coords[0]:.6f},{coords[1]:.6f}"
    await _save_setting(message, state, session, user, lang, key, value)
