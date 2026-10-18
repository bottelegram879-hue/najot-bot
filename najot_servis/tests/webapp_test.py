"""Mini App backend test: page, Telegram signature check, request creation (photo + location).

Run from the project folder:  python tests/webapp_test.py
"""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import sys
import tempfile
import time
from urllib.parse import urlencode

DB = os.path.join(tempfile.gettempdir(), "najot_webapp_test.db").replace("\\", "/")
if os.path.exists(DB):
    os.remove(DB)
TOKEN = "123456:TEST_TOKEN"
os.environ.update(DATABASE_URL=f"sqlite+aiosqlite:///{DB}", BOT_TOKEN=TOKEN, OWNER_IDS="222", OWNER_USERNAMES="",
                  MASTER_USERNAMES="", NOTIFY_TARGETS="", ANTHROPIC_API_KEY="")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiohttp.test_utils import TestClient, TestServer  # noqa: E402
from aiogram import Bot  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.methods import GetMe, SendMediaGroup, SendMessage, SendPhoto, SendVenue, TelegramMethod  # noqa: E402
from aiogram.types import Chat, Message, PhotoSize, User as TgUser  # noqa: E402
from sqlalchemy import select  # noqa: E402

from bot.db import Request, Session, User, init_db  # noqa: E402
from bot.webapp import build_page, make_app  # noqa: E402

SENT = []
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
        def m(i):
            return Message(message_id=i, date=int(time.time()), chat=Chat(id=1, type="private"),
                           photo=[PhotoSize(file_id=f"FILE{i}", file_unique_id=f"u{i}", width=1, height=1)])
        if isinstance(method, GetMe):
            return TgUser(id=1, is_bot=True, first_name="b")
        if isinstance(method, SendMediaGroup):
            SENT.append((method.chat_id, f"[ALBUM {len(method.media)}]"))
            return [m(i) for i in range(len(method.media))]
        if isinstance(method, SendPhoto):
            SENT.append((method.chat_id, "[PHOTO] " + (method.caption or "")))
            return m(9)
        if isinstance(method, SendVenue):
            SENT.append((method.chat_id, "[VENUE]"))
            return m(8)
        if isinstance(method, SendMessage):
            SENT.append((method.chat_id, method.text))
            return Message(message_id=7, date=int(time.time()), chat=Chat(id=1, type="private"), text=method.text)
        return True


def sign(user: dict, token: str = TOKEN) -> str:
    fields = {"auth_date": str(int(time.time())), "query_id": "AAH", "user": json.dumps(user, separators=(",", ":"))}
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


PNG = "data:image/png;base64," + base64.b64encode(
    bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8ffff3f0005fe02fea7d6a4"
                  "4c0000000049454e44ae426082")).decode()


async def main():
    await init_db()
    page = build_page().decode("utf-8")
    check("telegram-web-app.js" in page and "Mini App bridge" in page and "window.NS_TG_RELAY = '';" in page
          and 'id="reqForm"' in page, "site page served with Telegram bridge, Google relay off")

    bot = Bot(TOKEN, session=FakeSession())
    client = TestClient(TestServer(make_app(bot)))
    await client.start_server()
    user = {"id": 555, "first_name": "Ali", "username": "ali", "language_code": "ru"}
    init = sign(user)

    r = await client.get("/")
    check(r.status == 200 and "reqForm" in await r.text(), "GET / returns the form page")

    r = await client.post("/api/webapp/request", json={"initData": sign(user, "999:WRONG"), "data": {}})
    check(r.status == 401, "forged Telegram signature rejected (401)")

    r = await client.post("/api/webapp/request", json={"initData": init, "data": {"name": "A"}, "visit": "self"})
    j = await r.json()
    check(r.status == 400 and j.get("code") == "fields" and {"name", "phone", "brand", "problem"} <= set(j["fields"]),
          "missing fields reported back to the form")

    r = await client.post("/api/webapp/request", json={"initData": init, "visit": "call", "addr": "",
                                                       "data": {"name": "Ali", "phone": "+998 90 123 45 67", "brand": "Howo",
                                                                "problem": "Не заводится утром", "comment": "ВЫЗОВ МАСТЕРА НА МЕСТО"}})
    j = await r.json()
    check(r.status == 400 and j.get("code") == "location", "call-out without location rejected")

    payload = {"initData": init, "visit": "call", "addr": "Трасса M39, 25 км",
               "data": {"name": "Ali", "phone": "+998 90 123 45 67", "brand": "Shacman", "model": "X3000",
                        "carDesc": "2020, 30 A 777 BC", "problem": "Травит воздух, давление падает",
                        "desiredDate": "2026-10-05", "photos": [PNG, PNG],
                        "comment": "ВЫЗОВ МАСТЕРА НА МЕСТО · Локация: https://maps.google.com/?q=39.654200,66.959700 · "
                                   "Ориентир: Трасса M39, 25 км · Услуга: Тормоза и пневматика"}}
    r = await client.post("/api/webapp/request", json=payload)
    j = await r.json()
    check(r.status == 200 and j.get("ok") and j.get("number") == "NS-000001", "request created from the mini app")
    r2 = await client.post("/api/webapp/request", json=payload)
    check((await r2.json()).get("number") == "NS-000001", "same submission twice -> no duplicate")

    async with Session() as s:
        req = await s.scalar(select(Request))
        u = await s.scalar(select(User).where(User.tg_id == 555))
        n = len((await s.scalars(select(Request))).all())
    check(n == 1, "exactly one request")
    check(req.mobility == "onsite" and abs(req.latitude - 39.6542) < 1e-6 and req.location_note == "Трасса M39, 25 км",
          "call-out with location + landmark stored")
    check(req.year == 2020 and req.plate == "30A777BC" and req.desired_date is not None and "FILE0" in (req.photo_ids or ""),
          "year/plate parsed, date and 2 photos stored")
    check("Тормоза" in req.problem and req.source == "webapp" and req.client_user_id == u.id, "service + source + client")
    check(any("[ALBUM 2]" == x[1] for x in SENT if x[0] == 555), "photos uploaded to client's chat")
    check(any("Заявка успешно создана" in (x[1] or "") for x in SENT if x[0] == 555), "client gets confirmation in chat")

    r = await client.post("/api/webapp/me", json={"initData": init})
    p = (await r.json()).get("prefill", {})
    check(p.get("phone") == "+998901234567" and p.get("brand") == "Shacman" and p.get("model") == "X3000",
          "next time the form is prefilled (remembered)")

    await client.close()
    print(f"\nTOTAL: {len(FAILS)} failed", FAILS)


asyncio.run(main())
