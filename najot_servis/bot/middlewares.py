import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select

from .config import config, now
from .db import Master, Owner, Session, User
from .i18n import t

log = logging.getLogger(__name__)


class DbUserMiddleware(BaseMiddleware):
    """Opens a DB session per update and loads/creates the User. Injects: session, user, lang."""

    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]], event: TelegramObject,
                      data: dict[str, Any]) -> Any:
        tg_user = data.get("event_from_user")
        async with Session() as s:
            data["session"] = s
            if tg_user is None or tg_user.is_bot:
                return await handler(event, data)
            user = await s.scalar(select(User).where(User.tg_id == tg_user.id))
            if user is None:
                user = User(tg_id=tg_user.id, username=tg_user.username, full_name=tg_user.full_name or "", lang=None)
                s.add(user)
                await s.flush()
            else:
                user.username = tg_user.username
                if not user.full_name:
                    user.full_name = tg_user.full_name or ""
                user.last_seen = now()
            uname = (tg_user.username or "").lower()
            is_owner_account = tg_user.id in config.owner_ids or (uname and uname in config.owner_usernames)
            owner_row = await s.scalar(select(Owner).where(Owner.user_id == user.id))
            if is_owner_account and user.role != "owner":
                user.role = "owner"
                log.info("tg=%s (@%s) granted owner role from config", tg_user.id, tg_user.username)
            elif user.role == "owner" and not is_owner_account and (config.owner_ids or config.owner_usernames):
                # the admin panel belongs only to the accounts listed in OWNER_IDS / OWNER_USERNAMES
                user.role = "master" if await s.scalar(select(Master).where(Master.user_id == user.id)) else "client"
                if owner_row:
                    await s.delete(owner_row)
                    owner_row = None
                log.warning("tg=%s (@%s) is not in the owner list -> role %s", tg_user.id, tg_user.username, user.role)
            if user.role == "owner" and not owner_row:
                s.add(Owner(user_id=user.id))
            if uname and uname in config.master_usernames:
                m = await s.scalar(select(Master).where(Master.user_id == user.id))
                if m is None:
                    s.add(Master(user_id=user.id, name=user.full_name or tg_user.username))
                    log.info("tg=%s (@%s) registered as mechanic from config", tg_user.id, tg_user.username)
                elif not m.is_active:
                    m.is_active = True
            await s.commit()

            if user.role == "blocked":
                return None
            data["user"] = user
            data["lang"] = user.lang or "ru"
            return await handler(event, data)


class ThrottleMiddleware(BaseMiddleware):
    """Simple per-user anti-flood: drops updates arriving faster than `rate` seconds apart."""

    def __init__(self, cb_rate: float = 0.4, msg_rate: float = 0.1):
        self.cb_rate, self.msg_rate = cb_rate, msg_rate
        self.last: dict[tuple[int, bool], float] = {}

    async def __call__(self, handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        tg_user = data.get("event_from_user")
        if isinstance(event, Message) and event.media_group_id:
            return await handler(event, data)  # album photos arrive together — never drop them
        if tg_user:
            is_cb = isinstance(event, CallbackQuery)
            ts = time.monotonic()
            prev = self.last.get((tg_user.id, is_cb), 0.0)
            self.last[(tg_user.id, is_cb)] = ts
            if ts - prev < (self.cb_rate if is_cb else self.msg_rate):
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer()
                    except Exception:
                        pass
                return None
            if len(self.last) > 50_000:
                self.last.clear()
        return await handler(event, data)


class RoleFilter(BaseFilter):
    """Server-side role check. Applied on whole routers so hidden buttons can't be bypassed."""

    def __init__(self, *roles: str):
        self.roles = set(roles)

    async def __call__(self, event: Message | CallbackQuery, user: User | None = None, **_) -> bool:
        return user is not None and user.role in self.roles


class DenyFallbackFilter(BaseFilter):
    """Matches staff-only callbacks that no role router accepted -> reply 'access denied'."""

    async def __call__(self, event: CallbackQuery, **_) -> bool:
        data = event.data or ""
        return data.startswith(("o:", "m:", "mj:", "ma:", "rt:", "rp:", "st:", "cmt:", "panel"))


async def deny(cb: CallbackQuery, lang: str = "ru", **_) -> None:
    log.warning("access denied: tg=%s data=%s", cb.from_user.id, cb.data)
    await cb.answer(t(lang, "access_denied"), show_alert=True)
