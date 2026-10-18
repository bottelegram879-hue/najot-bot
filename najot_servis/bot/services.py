"""Business logic: request lifecycle, permissions, history and notifications.

Every state-changing operation goes through here, and each one checks permissions on the
server side (never relying only on which buttons were shown).
"""
import json
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InputMediaPhoto
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .config import CALL_MODES, STATUSES, config, fmt_dt, now, parse_coords
from .db import Client, Master, Notification, Request, RequestHistory, User, get_settings
from .i18n import t
from .ui import body_label, btn, h, markup, mobility_label, service_label, status_label, url_btn

log = logging.getLogger(__name__)


class PermissionDenied(Exception):
    pass


def number_for(req_id: int) -> str:
    return f"NS-{req_id:06d}"


async def get_request(s: AsyncSession, req_id: int) -> Request | None:
    return await s.get(Request, req_id, populate_existing=True)


# ---------------- permissions ----------------

async def master_of(s: AsyncSession, user: User) -> Master | None:
    if user.role not in ("master", "owner"):  # an owner can also work as a mechanic
        return None
    return await s.scalar(select(Master).where(Master.user_id == user.id, Master.is_active.is_(True)))


async def can_view(s: AsyncSession, user: User, r: Request) -> bool:
    if user.role == "owner":
        return True
    if user.role == "master":
        m = await master_of(s, user)
        if m and r.master_id == m.id:
            return True
    return r.client_user_id == user.id


async def can_manage(s: AsyncSession, user: User, r: Request) -> bool:
    """Owner, or the master the request is assigned to."""
    if user.role == "owner":
        return True
    m = await master_of(s, user)
    return bool(m and r.master_id == m.id)


def require_owner(user: User) -> None:
    if user.role != "owner":
        raise PermissionDenied


# ---------------- rendering ----------------

def map_url(lat: float, lon: float) -> str:
    return f"https://maps.google.com/?q={lat:.6f},{lon:.6f}"


def route_url(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat:.6f},{lon:.6f}"


async def send_service_location(bot: Bot, s: AsyncSession, chat_id: int, lang: str, *, with_text: bool = True,
                                request_id: int | None = None) -> None:
    """Send the service pin (venue) so the client can build a route — used for «Приеду сам»."""
    st = await get_settings(s)
    coords = parse_coords(st.get("location"))
    if with_text:
        await send(bot, s, chat_id, t(lang, "bk_come_here", address=h(st["address"]), hours=h(st["work_hours"])),
                   markup([url_btn(t(lang, "btn_route"), route_url(*coords))]) if coords else None,
                   kind="service_location", request_id=request_id)
    if coords:
        try:
            await bot.send_venue(chat_id, latitude=coords[0], longitude=coords[1], title="🚛 NAJOT SERVIS",
                                 address=st["address"])
        except Exception as e:
            log.warning("send_venue to %s failed: %s", chat_id, e)


def _details(lang: str, d: dict) -> list[str]:
    """Truck + problem + client lines shared by preview, card and staff alert."""
    truck = " ".join(x for x in (d.get("brand"), d.get("model")) if x)
    lines = [f"{t(lang, 'lbl_car')}: <b>{h(truck or None)}</b>"]
    if d.get("body_type"):
        lines.append(f"{t(lang, 'lbl_body')}: {body_label(lang, d['body_type'])}")
    if d.get("year"):
        lines.append(f"{t(lang, 'lbl_year')}: {h(d['year'])}")
    if d.get("plate"):
        lines.append(f"{t(lang, 'lbl_plate')}: {h(d['plate'])}")
    if d.get("car_desc"):
        lines.append(f"{t(lang, 'lbl_car_desc')}: {h(d['car_desc'])}")
    services = [x for x in (d.get("services") or ([d["service"]] if d.get("service") else [])) if x]
    if services and services != ["other"]:
        lines.append(f"{t(lang, 'lbl_service')}: " + ", ".join(service_label(lang, x) for x in services))
    lines.append(f"{t(lang, 'lbl_problem')}: {h(d.get('problem'))}")
    if d.get("desired_date"):
        lines.append(f"{t(lang, 'lbl_date')}: <b>{h(_fmt_date(d['desired_date']))}</b>")
    n_photos = len(d.get("photo_ids") or ([d["photo_id"]] if d.get("photo_id") else []))
    if n_photos:
        lines.append(f"{t(lang, 'lbl_photo')}: {n_photos}")
    lines.append(f"{t(lang, 'lbl_mobility')}: <b>{mobility_label(lang, d.get('mobility'))}</b>")
    if d.get("latitude") is not None:
        lines.append(f"{t(lang, 'lbl_location')}: <a href=\"{map_url(d['latitude'], d['longitude'])}\">"
                     f"{t(lang, 'map_link')}</a>")
    if d.get("address_note"):
        lines.append(f"{t(lang, 'lbl_location')}: {h(d['address_note'])}")
    lines += ["", f"{t(lang, 'lbl_client')}: {h(d.get('name'))}", f"{t(lang, 'lbl_phone')}: {h(d.get('phone'))}"]
    return lines


def _fmt_date(v) -> str:
    if isinstance(v, datetime):
        return v.strftime("%d.%m.%Y")
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return str(v)


def _parse_date(v) -> datetime | None:
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d") if v else None
    except ValueError:
        return None


def photos_of(r: Request) -> list[str]:
    if r.photo_ids:
        try:
            return list(json.loads(r.photo_ids))[:3]
        except ValueError:
            pass
    return [r.photo_id] if r.photo_id else []


def _req_dict(r: Request) -> dict:
    return {"brand": r.brand, "model": r.model, "body_type": r.body_type, "year": r.year, "plate": r.plate,
            "car_desc": r.car_desc, "desired_date": r.desired_date, "photo_ids": photos_of(r),
            "services": json.loads(r.service_list) if r.service_list else None,
            "service": r.service_code, "problem": r.problem, "photo_id": r.photo_id, "mobility": r.mobility,
            "latitude": r.latitude, "longitude": r.longitude, "address_note": r.location_note,
            "name": r.client_name, "phone": r.client_phone}


def request_card(r: Request, lang: str, *, staff: bool = False) -> str:
    lines = [
        t(lang, "req_title", number=r.number),
        f"{t(lang, 'lbl_status')}: <b>{status_label(lang, r.status)}</b>",
        "",
        *_details(lang, _req_dict(r)),
    ]
    if r.master:
        lines.append(f"{t(lang, 'lbl_master')}: {h(r.master.name)}")
    if r.ready_at:
        lines.append(f"{t(lang, 'lbl_ready')}: <b>{fmt_dt(r.ready_at)}</b>")
    lines.append(f"{t(lang, 'lbl_created')}: {fmt_dt(r.created_at)}")
    if staff and r.source != "telegram":
        lines.append(f"🏷 {r.source}")
    return "\n".join(lines)


def preview_card(d: dict, lang: str) -> str:
    return "\n".join(_details(lang, d))


async def history_text(s: AsyncSession, r: Request, lang: str) -> str:
    rows = (await s.scalars(select(RequestHistory).where(RequestHistory.request_id == r.id)
                            .order_by(RequestHistory.at, RequestHistory.id))).all()
    out = [t(lang, "history_title", number=r.number), ""]
    for e in rows:
        details = e.details
        if e.action == "status":
            details = status_label(lang, e.details)
        action = t(lang, "h_" + e.action, d=h(details))
        who = f"{h(e.actor_name)}, {t(lang, 'role_' + e.actor_role)}" if e.actor_name else t(lang, "role_system")
        out.append(f"🕐 {fmt_dt(e.at)} — {action}\n      <i>👤 {who}</i>")
    return "\n".join(out)


# ---------------- notifications ----------------

async def send(bot: Bot, s: AsyncSession, chat_id: int | str, text: str, kb: InlineKeyboardMarkup | None = None,
               *, kind: str = "info", request_id: int | None = None, photo_id: str | None = None,
               photos: list[str] | None = None, location: tuple[float, float] | None = None) -> bool:
    ok, err = True, ""
    photos = list(photos or ([photo_id] if photo_id else []))
    try:
        if len(photos) == 1 and len(text) <= 1024:
            await bot.send_photo(chat_id, photos[0], caption=text, reply_markup=kb)
        else:
            if len(photos) == 1:
                await bot.send_photo(chat_id, photos[0])
            elif photos:
                await bot.send_media_group(chat_id, [InputMediaPhoto(media=p) for p in photos[:10]])
            await bot.send_message(chat_id, text, reply_markup=kb, disable_web_page_preview=True)
        if location:
            await bot.send_location(chat_id, latitude=location[0], longitude=location[1])
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        ok, err = False, str(e)
        log.warning("notify %s failed: %s", chat_id, e)
    except Exception as e:  # network etc. — never break the business operation
        ok, err = False, repr(e)
        log.exception("notify %s failed", chat_id)
    s.add(Notification(request_id=request_id, chat_id=chat_id if isinstance(chat_id, int) else 0,
                       kind=kind if isinstance(chat_id, int) else f"{kind} {chat_id}"[:32],
                       text=text[:4000], ok=ok, error=err))
    return ok


async def owners(s: AsyncSession) -> list[User]:
    return list((await s.scalars(select(User).where(User.role == "owner"))).all())


async def notify_client(bot: Bot, s: AsyncSession, r: Request, key: str, **kw) -> bool:
    if not r.client_user_id:
        return False
    u = await s.get(User, r.client_user_id)
    if not u or u.role == "blocked":
        return False
    lang = u.lang or "ru"
    text = t(lang, key, number=r.number, **kw)
    kb = markup([btn(t(lang, "btn_open_request"), f"rq:{r.id}")], [btn(t(lang, "btn_home"), "home")])
    return await send(bot, s, u.tg_id, text, kb, kind=key, request_id=r.id)


async def staff_recipients(s: AsyncSession) -> list[tuple[int | str, str]]:
    """Everyone who must receive new-request alerts, without duplicates:
    owners in DB, OWNER_IDS, and NOTIFY_TARGETS (e.g. @Najotservis — resolved to the
    account's chat id once that account has opened the bot; otherwise sent by @username,
    which works for public groups/channels where the bot is a member/admin)."""
    recipients: list[tuple[int | str, str]] = [(u.tg_id, u.lang or "ru") for u in await owners(s)]
    known: set = {cid for cid, _ in recipients}
    for oid in config.owner_ids:
        if oid not in known:
            recipients.append((oid, "ru"))
            known.add(oid)
    for target in config.notify_targets:
        if target.lstrip("-").isdigit():
            cid: int | str = int(target)
            lang = "ru"
        else:
            name = target.lstrip("@")
            u = await s.scalar(select(User).where(func.lower(User.username) == name.lower()))
            cid, lang = (u.tg_id, u.lang or "ru") if u else ("@" + name, "ru")
        if cid not in known:
            recipients.append((cid, lang))
            known.add(cid)
    return recipients


async def notify_staff_new(bot: Bot, s: AsyncSession, r: Request) -> None:
    location = (r.latitude, r.longitude) if r.latitude is not None else None
    for chat_id, lang in await staff_recipients(s):
        urgent = t(lang, "urgent") if r.mobility in ("onsite", "tow") else ""
        text = t(lang, "n_new_staff", urgent=urgent, number=r.number, card="\n".join(_details(lang, _req_dict(r))))
        kb = markup(
            [btn(t(lang, "btn_accept"), f"o:acc:{r.id}"), btn(t(lang, "btn_assign_master"), f"o:as:{r.id}")],
            [btn(t(lang, "btn_call_client"), f"o:call:{r.id}"), btn(t(lang, "btn_open_request"), f"o:r:{r.id}")],
            [url_btn(t(lang, "btn_route"), route_url(*location))] if location else None,
        )
        await send(bot, s, chat_id, text, kb, kind="new_request", request_id=r.id, photos=photos_of(r),
                   location=location)


async def notify_owners_update(bot: Bot, s: AsyncSession, r: Request, what: str, actor: User) -> None:
    """When a master changes something, keep owners informed (owners don't get their own echoes)."""
    if actor.role == "owner":
        return
    for u in await owners(s):
        lang = u.lang or "ru"
        await send(bot, s, u.tg_id, t(lang, "staff_update", number=r.number, what=what(lang) if callable(what) else what,
                                       who=h(actor.full_name)),
                   markup([btn(t(lang, "btn_open_request"), f"o:r:{r.id}")]), kind="staff_update", request_id=r.id)


# ---------------- operations ----------------

def add_history(s: AsyncSession, r: Request, actor: User | None, action: str, details: str = "") -> None:
    s.add(RequestHistory(
        request_id=r.id, at=now(), actor_user_id=actor.id if actor else None,
        actor_name=(actor.full_name if actor else ""), actor_role=(actor.role if actor else "system"),
        action=action, details=details[:2000]))


async def upsert_client(s: AsyncSession, user: User | None, name: str, phone: str) -> Client:
    c = None
    if user:
        c = await s.scalar(select(Client).where(Client.user_id == user.id))
    if c is None:
        c = await s.scalar(select(Client).where(Client.phone == phone, Client.user_id.is_(None)))
    if c is None:
        c = Client(user_id=user.id if user else None, name=name, phone=phone)
        s.add(c)
    else:
        c.name, c.phone = name, phone
    await s.flush()
    return c


async def create_request(s: AsyncSession, bot: Bot, d: dict, creator: User, *, for_client: bool,
                         idem_key: str, source: str = "telegram") -> tuple[Request, bool]:
    """Create a request exactly once per idempotency key. Returns (request, created_now)."""
    existing = await s.scalar(select(Request).where(Request.idempotency_key == idem_key))
    if existing:
        return existing, False
    client_user = creator if for_client else None
    if for_client:
        creator.phone = d["phone"]
    client = await upsert_client(s, client_user, d["name"], d["phone"])
    r = Request(
        idempotency_key=idem_key, client_user_id=client_user.id if client_user else None, client_id=client.id,
        car_id=d.get("car_id"), created_by_user_id=creator.id, brand=d["brand"], model=d["model"],
        year=d.get("year"), plate=d.get("plate"), body_type=d.get("body_type"), mobility=d.get("mobility") or "drive",
        latitude=d.get("latitude"), longitude=d.get("longitude"), location_note=d.get("address_note"),
        photo_id=(d.get("photo_ids") or [None])[0] or d.get("photo_id"),
        photo_ids=json.dumps(d.get("photo_ids")) if d.get("photo_ids") else None,
        car_desc=d.get("car_desc"), desired_date=_parse_date(d.get("desired_date")),
        service_code=(d.get("services") or [d.get("service") or "other"])[0],
        service_list=json.dumps(d["services"]) if d.get("services") else None, problem=d["problem"],
        client_name=d["name"], client_phone=d["phone"], status="new", source=source)
    s.add(r)
    try:
        await s.flush()
    except IntegrityError:
        await s.rollback()
        existing = await s.scalar(select(Request).where(Request.idempotency_key == idem_key))
        if existing:
            return existing, False
        raise
    r.number = number_for(r.id)
    add_history(s, r, creator, "created")
    await s.commit()
    await notify_staff_new(bot, s, r)
    await s.commit()
    await auto_dispatch(s, bot, r)
    return r, True


async def auto_dispatch(s: AsyncSession, bot: Bot, r: Request) -> None:
    """New request goes to mechanics automatically:
    one active mechanic -> assigned to him right away; several -> everyone gets «🙋 Взять заявку»."""
    masters = list((await s.scalars(select(Master).where(Master.is_active.is_(True)))).all())
    if len(masters) == 1:
        await assign_master(s, bot, r, masters[0], None)
        return
    for m in masters:
        if not m.user or m.user.role == "blocked":
            continue
        ml = m.user.lang or "ru"
        kb = markup([btn(t(ml, "btn_take"), f"mt:take:{r.id}")],
                    [url_btn(t(ml, "btn_route"), route_url(r.latitude, r.longitude))] if r.latitude is not None else None)
        await send(bot, s, m.user.tg_id, t(ml, "m_take_offer", card=request_card(r, ml, staff=True)), kb,
                   kind="take_offer", request_id=r.id, photos=photos_of(r),
                   location=(r.latitude, r.longitude) if r.latitude is not None else None)
    await s.commit()


CLIENT_STATUS_KEYS = {
    "accepted": "cn_accepted", "diagnostics": "cn_diagnostics", "repair": "cn_repair",
    "waiting_parts": "cn_waiting_parts", "ready": "cn_ready", "delivered": "cn_delivered",
    "cancelled": "cn_cancelled", "new": "cn_new",
}


async def notify_client_status(s: AsyncSession, bot: Bot, r: Request, status: str) -> str:
    """Tell the client about the status. Returns 'sent' | 'failed' | 'no_client' | 'none'."""
    if not r.client_user_id:
        return "no_client"
    ok = None
    if status == "assigned" and r.master:
        ok = await notify_client(bot, s, r, "cn_assigned", master=h(r.master.name))
    elif status in CLIENT_STATUS_KEYS:
        extra = {}
        if status == "ready":
            extra["address"] = h((await get_settings(s))["address"])
        ok = await notify_client(bot, s, r, CLIENT_STATUS_KEYS[status], **extra)
        if status == "ready" and r.mobility not in CALL_MODES:
            client = await s.get(User, r.client_user_id)
            if client:  # pin of the service so the client can come and pick the truck up
                await send_service_location(bot, s, client.tg_id, client.lang or "ru", with_text=False, request_id=r.id)
    if ok is None:
        return "none"
    return "sent" if ok else "failed"


def client_note(lang: str, result: str, r: Request) -> str:
    if result == "sent":
        return "\n" + t(lang, "cl_sent")
    if result == "failed":
        return "\n" + t(lang, "cl_failed", phone=r.client_phone)
    if result == "no_client":
        return "\n" + t(lang, "cl_no_client", phone=r.client_phone)
    return ""


async def change_status(s: AsyncSession, bot: Bot, r: Request, status: str, actor: User) -> str:
    """Change the status and notify the client. Choosing the current status again re-sends the notification.
    Returns the client notification result (see notify_client_status)."""
    if status not in STATUSES:
        raise ValueError(status)
    if actor.role == "client":
        # client may only cancel their own new/accepted request
        if not (status == "cancelled" and r.client_user_id == actor.id and r.status in ("new", "accepted")):
            raise PermissionDenied
    elif not await can_manage(s, actor, r):
        raise PermissionDenied
    if actor.role == "master" and status in ("cancelled", "delivered", "new"):
        raise PermissionDenied
    if r.status == status:
        if actor.role == "client":
            return "none"
        result = await notify_client_status(s, bot, r, status)   # staff re-selected it: remind the client
        await s.commit()
        return result
    r.status = status
    r.updated_at = now()
    r.closed_at = now() if status in ("ready", "delivered", "cancelled") else None
    add_history(s, r, actor, "status", status)
    await s.commit()

    result = await notify_client_status(s, bot, r, status)
    if actor.role != "owner":
        await notify_owners_update(bot, s, r, lambda lang: status_label(lang, status), actor)
    # tell the master when owner/client changes status of their job
    if r.master and r.master.user and r.master.user.id != actor.id and status in ("cancelled", "delivered"):
        ml = r.master.user.lang or "ru"
        await send(bot, s, r.master.user.tg_id, t(ml, "staff_update", number=r.number,
                                                   what=status_label(ml, status), who=h(actor.full_name)),
                   kind="staff_update", request_id=r.id)
    await s.commit()
    return result


async def assign_master(s: AsyncSession, bot: Bot, r: Request, master: Master | None, actor: User | None) -> None:
    """actor=None means automatic assignment by the system."""
    if actor is not None and actor.role != "owner" and not (master and master.user_id == actor.id):
        raise PermissionDenied
    old = r.master
    r.master_id = master.id if master else None
    r.master_accepted = False
    r.updated_at = now()
    if master:
        add_history(s, r, actor, "assigned", master.name)
        if r.status in ("new", "accepted"):
            r.status = "assigned"
            add_history(s, r, actor, "status", "assigned")
    else:
        add_history(s, r, actor, "assigned", "—")
    await s.commit()
    await s.refresh(r)
    if old and (not master or old.id != master.id) and old.user:
        await send(bot, s, old.user.tg_id, t(old.user.lang or "ru", "m_job_removed", number=r.number),
                   kind="job_removed", request_id=r.id)
    if master:
        ml = master.user.lang or "ru"
        kb = markup([btn(t(ml, "btn_m_accept"), f"ma:acc:{r.id}")], [btn(t(ml, "btn_open_request"), f"mj:{r.id}")],
                    [url_btn(t(ml, "btn_route"), route_url(r.latitude, r.longitude))] if r.latitude is not None else None)
        location = (r.latitude, r.longitude) if r.latitude is not None else None
        await send(bot, s, master.user.tg_id, t(ml, "m_new_job", card=request_card(r, ml, staff=True)), kb,
                   kind="new_job", request_id=r.id, photos=photos_of(r), location=location)
        await notify_client(bot, s, r, "cn_assigned", master=h(master.name))
    await s.commit()


async def set_ready_at(s: AsyncSession, bot: Bot, r: Request, when: datetime, actor: User) -> None:
    if not await can_manage(s, actor, r):
        raise PermissionDenied
    r.ready_at = when
    r.updated_at = now()
    add_history(s, r, actor, "ready_at", fmt_dt(when))
    await s.commit()
    await notify_client(bot, s, r, "cn_ready_time", when=when.strftime("%d.%m.%Y — %H:%M"))
    await notify_owners_update(bot, s, r, lambda lang: f"⏰ {fmt_dt(when)}", actor)
    await s.commit()


async def add_comment(s: AsyncSession, bot: Bot, r: Request, text: str, actor: User) -> None:
    if not await can_manage(s, actor, r):
        raise PermissionDenied
    add_history(s, r, actor, "comment", text)
    await s.commit()
    await notify_client(bot, s, r, "cn_comment", text=h(text))
    await notify_owners_update(bot, s, r, lambda lang: f"📝 {h(text[:200])}", actor)
    await s.commit()


async def master_accept(s: AsyncSession, bot: Bot, r: Request, actor: User) -> None:
    m = await master_of(s, actor)
    if not m or r.master_id != m.id:
        raise PermissionDenied
    if r.master_accepted:
        return
    r.master_accepted = True
    add_history(s, r, actor, "master_accepted")
    await s.commit()
    await notify_owners_update(bot, s, r, lambda lang: t(lang, "h_master_accepted"), actor)
    await s.commit()
