"""Hosting (webhook) mode test: one port serves the Telegram webhook, the form page and /ping.

Run from the project folder:  python tests/webhook_test.py
"""
import asyncio
import hashlib
import os
import sys
import tempfile
import time

DB = os.path.join(tempfile.gettempdir(), "najot_webhook_test.db").replace("\\", "/")
if os.path.exists(DB):
    os.remove(DB)
TOKEN = "123456:TEST_TOKEN"
os.environ.update(DATABASE_URL=f"sqlite+aiosqlite:///{DB}", BOT_TOKEN=TOKEN, RENDER_EXTERNAL_URL="http://127.0.0.1:18080",
                  PORT="18080", OWNER_IDS="", OWNER_USERNAMES="", NOTIFY_TARGETS="", KEEP_AWAKE="0")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp  # noqa: E402
from aiogram import Bot  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.methods import GetMe, SendMessage, SendPhoto, SetWebhook, TelegramMethod  # noqa: E402
from aiogram.types import Chat, Message, User as TgUser  # noqa: E402

import bot.__main__ as main_mod  # noqa: E402
from bot.db import init_db  # noqa: E402

CALLS = []
FAILS = []


def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILS.append(label)


class FakeSession(BaseSession):
    async def close(self):
        pass

    async def stream_content(self, *a, **k):
        yield b""

    async def make_request(self, bot, method: TelegramMethod, timeout=None):
        CALLS.append(method)
        if isinstance(method, GetMe):
            return TgUser(id=1, is_bot=True, first_name="b", username="b")
        if isinstance(method, (SendMessage, SendPhoto)):
            return Message(message_id=1, date=int(time.time()), chat=Chat(id=1, type="private"), text="x")
        return True


async def main():
    await init_db()
    bot = Bot(TOKEN, session=FakeSession())
    dp = main_mod.build_dispatcher()
    task = asyncio.create_task(main_mod.run_webhook(bot, dp))
    await asyncio.sleep(1.5)
    secret = hashlib.sha256(TOKEN.encode()).hexdigest()[:48]
    hooks = [c for c in CALLS if isinstance(c, SetWebhook)]
    check(hooks and hooks[0].url == "http://127.0.0.1:18080/tg/webhook" and hooks[0].secret_token == secret,
          "webhook registered at the public URL with a secret")
    update = {"update_id": 1, "message": {"message_id": 5, "date": int(time.time()), "chat": {"id": 777, "type": "private"},
                                          "from": {"id": 777, "is_bot": False, "first_name": "Ali"}, "text": "/start"}}
    async with aiohttp.ClientSession() as http:
        async with http.get("http://127.0.0.1:18080/ping") as r:
            check(r.status == 200, "/ping answers (keep-awake target)")
        async with http.get("http://127.0.0.1:18080/") as r:
            check(r.status == 200 and "reqForm" in await r.text(), "form page served on the same port")
        async with http.post("http://127.0.0.1:18080/tg/webhook", json=update) as r:
            check(r.status == 401, "update without Telegram secret rejected")
        async with http.post("http://127.0.0.1:18080/tg/webhook", json=update,
                             headers={"X-Telegram-Bot-Api-Secret-Token": secret}) as r:
            check(r.status == 200, "update with secret accepted")
    await asyncio.sleep(1.5)
    sent = [c for c in CALLS if isinstance(c, (SendMessage, SendPhoto)) and getattr(c, "chat_id", None) == 777]
    check(bool(sent), "bot answered /start through the webhook")
    task.cancel()
    print(f"\nTOTAL: {len(FAILS)} failed", FAILS)


asyncio.run(main())
