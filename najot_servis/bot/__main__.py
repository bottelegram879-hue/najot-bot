"""Entry point: python -m bot"""
import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault, ErrorEvent

from .config import config
from .db import init_db, sync_config_roles
from .handlers import build_routers
from .i18n import t
from .middlewares import DbUserMiddleware, ThrottleMiddleware
from .storage import DbStorage  # FSM in the DB: half-filled requests survive restarts

log = logging.getLogger("najot")


def setup_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    file_h = RotatingFileHandler("logs/bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    file_h.setFormatter(fmt)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(config.log_level)
    root.addHandler(file_h)
    root.addHandler(console)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def make_storage():
    if config.redis_url:
        from aiogram.fsm.storage.redis import RedisStorage
        return RedisStorage.from_url(config.redis_url)
    return DbStorage()


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=make_storage())
    throttle = ThrottleMiddleware()
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(throttle)
        observer.outer_middleware(DbUserMiddleware())
    dp.include_routers(*build_routers())

    @dp.errors()
    async def on_error(event: ErrorEvent, bot: Bot):
        log.exception("update %s failed: %s", event.update.update_id, event.exception, exc_info=event.exception)
        upd = event.update
        target = upd.message or (upd.callback_query and upd.callback_query.message)
        chat_id = None
        if upd.callback_query:
            chat_id = upd.callback_query.from_user.id
            try:
                await upd.callback_query.answer()
            except Exception:
                pass
        elif target:
            chat_id = target.chat.id
        if chat_id:
            try:
                await bot.send_message(chat_id, t("ru", "error_generic"))
            except Exception:
                pass
        return True

    return dp


async def set_commands(bot: Bot) -> None:
    for lang in ("ru", "uz", "en"):
        cmds = [BotCommand(command="start", description="🚗 NAJOT SERVIS"),
                BotCommand(command="menu", description=t(lang, "btn_home")),
                BotCommand(command="lang", description=t(lang, "btn_lang")),
                BotCommand(command="cancel", description=t(lang, "btn_cancel"))]
        await bot.set_my_commands(cmds, scope=BotCommandScopeDefault(), language_code=None if lang == "ru" else lang)
    await bot.set_my_description(
        "🚛 NAJOT SERVIS — сервис грузовых автомобилей.\n"
        "Ремонт, диагностика и ТО грузовиков, выездной ремонт и эвакуация. Заявка — прямо в Telegram.")
    await bot.set_my_short_description("🚛 NAJOT SERVIS — ремонт грузовиков. Заявка в Telegram")


async def check_notify_targets(bot: Bot) -> None:
    """Tell the operator at startup whether new-request alerts can actually be delivered."""
    from sqlalchemy import func, select
    from .db import Session, User
    async with Session() as s:
        for target in config.notify_targets:
            name = target.lstrip("@")
            if not target.lstrip("-").isdigit():
                u = await s.scalar(select(User).where(func.lower(User.username) == name.lower()))
                if u:
                    log.info("notify target %s -> chat %s (role=%s) ✓", target, u.tg_id, u.role)
                    continue
            try:
                chat = await bot.get_chat(target if target.lstrip("-").isdigit() else "@" + name)
                log.info("notify target %s -> %s '%s' ✓", target, chat.type, chat.title or chat.full_name)
            except Exception:
                log.warning("notify target %s is NOT reachable yet: if it is a personal account, open the bot from "
                            "it and press /start once; if it is a group/channel, add the bot there as admin.", target)


async def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    """Hosting mode (Render etc.): Telegram webhook + the request-form Mini App on ONE public port."""
    import hashlib

    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    from .webapp import _publish, make_app

    base = config.webhook_url.rstrip("/")
    # Telegram secret header: from .env, or derived from the token so nobody else can post fake updates
    secret = config.webhook_secret or hashlib.sha256(config.bot_token.encode()).hexdigest()[:48]
    app = make_app(bot)                                   # "/" form page + /api/webapp/* + /ping
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=secret).register(app, path=config.webhook_path)
    setup_application(app, dp, bot=bot)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, config.webapp_host, config.webapp_port).start()
    log.info("webhook mode: listening on %s:%s, public %s", config.webapp_host, config.webapp_port, base)
    await bot.set_webhook(base + config.webhook_path, secret_token=secret, drop_pending_updates=False,
                          allowed_updates=dp.resolve_used_update_types())
    if config.miniapp_enabled:
        asyncio.create_task(_publish(bot, base))          # form address for the «Записать» button
    if config.keep_awake:
        asyncio.create_task(keep_awake(base + "/ping"))
    await asyncio.Event().wait()


async def keep_awake(url: str) -> None:
    """Free hosting puts an idle service to sleep after ~15 min; a request every 10 min keeps it awake."""
    import aiohttp
    async with aiohttp.ClientSession() as http:
        while True:
            await asyncio.sleep(600)
            try:
                async with http.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    log.debug("keep-awake ping: %s", resp.status)
            except Exception as e:
                log.warning("keep-awake ping failed: %s", e)


async def keep_polling_mode(bot: Bot) -> None:
    """If an outside service (e.g. a bot constructor) sets a webhook on this token, take the bot back."""
    while True:
        await asyncio.sleep(60)
        try:
            info = await bot.get_webhook_info()
            if info.url:
                log.warning("webhook %s was set by another service — removing it, this bot runs here", info.url)
                await bot.delete_webhook(drop_pending_updates=False)
        except Exception:
            log.debug("webhook check failed", exc_info=True)


async def main() -> None:
    setup_logging()
    if not config.bot_token:
        log.error("BOT_TOKEN is not set (see .env)")
        sys.exit(1)
    await init_db()
    for change in await sync_config_roles():
        log.info("roles from config: %s", change)
    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher()
    me = await bot.me()
    log.info("starting @%s (%s mode, db=%s, ai=%s)", me.username, "webhook" if config.webhook_url else "polling",
             config.database_url.split("://")[0], "claude" if config.anthropic_api_key else "simple")
    try:
        await set_commands(bot)
    except Exception:
        log.warning("could not set bot commands/description", exc_info=True)
    await check_notify_targets(bot)

    if config.webhook_url:
        await run_webhook(bot, dp)
    else:
        await bot.delete_webhook(drop_pending_updates=False)
        asyncio.create_task(keep_polling_mode(bot))
        tunnel = None
        if config.miniapp_enabled:
            try:
                from .webapp import start_miniapp
                tunnel = await start_miniapp(bot)
            except Exception:
                log.exception("mini app failed to start — the request form stays in chat")
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            from .webapp import _TUNNEL
            tunnel = _TUNNEL.get("proc") or tunnel
            if tunnel and tunnel.returncode is None:
                tunnel.terminate()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
