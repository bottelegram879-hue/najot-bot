from aiogram import F, Router
from aiogram.types import CallbackQuery

from ..middlewares import DenyFallbackFilter, deny
from . import ai, booking, cars, client, common, master, owner


def build_routers() -> list[Router]:
    fallback = Router(name="fallback")
    # staff-only callbacks that no role-restricted router accepted -> explicit "access denied"
    fallback.callback_query.register(deny, DenyFallbackFilter())

    @fallback.callback_query(F.data)
    async def stale(cb: CallbackQuery, lang: str = "ru"):
        from ..i18n import t
        await cb.answer(t(lang, "bk_expired"), show_alert=True)

    # order matters: common (/start, cancel) first, AI catch-all text and fallback last
    return [common.router, booking.router, cars.router, client.router, owner.router, master.router,
            master.staff_router, ai.router, fallback]
