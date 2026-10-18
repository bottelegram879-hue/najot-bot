"""End-to-end simulation of NAJOT SERVIS with a fake Telegram API (no network, separate test DB).

Run from the project folder:  python tests/e2e_test.py
"""
import asyncio
import os
import sys
import tempfile
from datetime import datetime, timedelta

DB = os.path.join(tempfile.gettempdir(), "najot_e2e.db").replace("\\", "/")
if os.path.exists(DB):
    os.remove(DB)
os.environ.update(DATABASE_URL=f"sqlite+aiosqlite:///{DB}", OWNER_IDS="222", ANTHROPIC_API_KEY="",
                  OWNER_USERNAMES="Najotservis,Ai_dasturchi_bola", MASTER_USERNAMES="Najotservis",
                  OWNER_SETUP_CODE="", NOTIFY_TARGETS="@Najotservis")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.client.session.base import BaseSession  # noqa: E402
from aiogram.methods import (AnswerCallbackQuery, EditMessageText, GetMe, SendContact, SendLocation,  # noqa: E402
                             SendMediaGroup, SendMessage, SendPhoto, SendVenue, TelegramMethod)
from aiogram.types import (CallbackQuery, Chat, Contact, Location, Message, PhotoSize, Update,  # noqa: E402
                           User as TgUser)
from sqlalchemy import func, select  # noqa: E402

import bot.middlewares as mw  # noqa: E402
mw.ThrottleMiddleware.__init__.__defaults__ = (0.0, 0.0)
from bot.__main__ import build_dispatcher  # noqa: E402
from bot.db import Master, Notification, Request, Session, User, init_db, sync_config_roles  # noqa: E402

SENT: list[tuple] = []          # (chat_id, text, reply_markup)
ALERTS: dict[str, str] = {}
MID = [1000]
UID = [0]
BOT_USER = TgUser(id=999, is_bot=True, first_name="NAJOT", username="najot_test_bot")
USERS = {111: ("Mansurjon", None), 222: ("Owner", None), 333: ("Master Aziz", None), 444: ("Najot servis", "Najotservis"),
         555: ("Driver", None)}
FAILS: list[str] = []


def msg(chat_id, text):
    MID[0] += 1
    return Message(message_id=MID[0], date=datetime.now(), chat=Chat(id=chat_id if isinstance(chat_id, int) else 0,
                   type="private"), text=text, from_user=BOT_USER)


class FakeSession(BaseSession):
    async def close(self):
        pass

    async def stream_content(self, *a, **k):
        yield b""

    async def make_request(self, bot, method: TelegramMethod, timeout=None):
        if isinstance(method, GetMe):
            return BOT_USER
        cid = getattr(method, "chat_id", 0)
        cid = int(cid) if str(cid).lstrip("-").isdigit() else cid
        if isinstance(method, SendPhoto):
            SENT.append((cid, f"[PHOTO {method.photo}] " + (method.caption or ""), method.reply_markup))
            return msg(cid, "")
        if isinstance(method, SendMediaGroup):
            SENT.append((cid, f"[ALBUM {len(method.media)}]", None))
            return [msg(cid, "")]
        if isinstance(method, SendLocation):
            SENT.append((cid, f"[LOCATION {method.latitude},{method.longitude}]", None))
            return msg(cid, "")
        if isinstance(method, SendVenue):
            SENT.append((cid, f"[VENUE {method.latitude},{method.longitude}]", None))
            return msg(cid, "")
        if isinstance(method, SendContact):
            SENT.append((cid, f"[CONTACT {method.phone_number}]", None))
            return msg(cid, "")
        if isinstance(method, (SendMessage, EditMessageText)):
            SENT.append((cid, method.text, method.reply_markup))
            return msg(cid, method.text)
        if isinstance(method, AnswerCallbackQuery):
            if method.text:
                ALERTS[method.callback_query_id] = method.text
            return True
        return True


def tg(uid):
    return TgUser(id=uid, is_bot=False, first_name=USERS[uid][0], username=USERS[uid][1], language_code="ru")


async def text(dp, b, uid, t=None, contact=None, photo=None, location=None, album=None):
    UID[0] += 1
    m = Message(message_id=UID[0], date=datetime.now(), chat=Chat(id=uid, type="private"), from_user=tg(uid),
                text=None if (photo or location or contact) else t, caption=t if photo else None, contact=contact,
                photo=[PhotoSize(file_id=photo, file_unique_id=photo, width=10, height=10)] if photo else None,
                location=location, media_group_id=album)
    await dp.feed_update(b, Update(update_id=UID[0], message=m))


async def click(dp, b, uid, data):
    UID[0] += 1
    cid = f"cb{UID[0]}"
    cb = CallbackQuery(id=cid, from_user=tg(uid), chat_instance="x", data=data, message=msg(uid, "screen"))
    await dp.feed_update(b, Update(update_id=UID[0], callback_query=cb))
    return ALERTS.get(cid)


def last(uid, n=1):
    return [x[1] for x in SENT if x[0] == uid][-n:]


def buttons(uid) -> list[str]:
    kb = next((x[2] for x in reversed(SENT) if x[0] == uid and x[2] is not None), None)
    if kb is None or not hasattr(kb, "inline_keyboard"):
        return []
    return [b.callback_data or b.url for row in kb.inline_keyboard for b in row]


def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILS.append(label)


async def main():
    await init_db()
    b = Bot("1:TEST", session=FakeSession(), default=DefaultBotProperties(parse_mode="HTML"))
    dp = build_dispatcher()

    # ---------- onboarding ----------
    for uid in (111, 222, 444):
        await text(dp, b, uid, "/start")
        await click(dp, b, uid, "lang:ru")
    check("Добро пожаловать" in last(111)[0], "client main menu")
    check("Панель управления" in last(222)[0], "owner (OWNER_IDS) panel")
    check("Панель управления" in last(444)[0], "@Najotservis gets owner panel automatically")
    await sync_config_roles()
    async with Session() as s:
        m444 = await s.scalar(select(Master).join(User, User.id == Master.user_id).where(User.tg_id == 444))
    check(m444 is not None, "@Najotservis registered as mechanic")
    await text(dp, b, 111, "/start")
    check("Выберите язык" in last(111)[0] and "[PHOTO" in last(111)[0], "/start always shows logo + language first")
    await click(dp, b, 111, "lang:ru")
    await click(dp, b, 111, "menu:about")
    about = last(111)[0]
    check(about.startswith("[PHOTO") and "Najot.Servis Грузовых" in about and "+998 95 549-24-47" in about
          and "Бинафша" in about, "«О сервисе» = logo + text from the post, two phones")

    # ---------- the request FORM (like the website) ----------
    await click(dp, b, 111, "bk:start")
    form = last(111)[0]
    check("Заявка на ремонт грузовика" in form and "Имя" in form and "Mansurjon" in form
          and "Описание автомобиля" in form and "Желаемая дата" in form and "Приеду сам" in form,
          "form card shows all website fields, name prefilled")
    check(buttons(111)[0] == "bf:phone", "«Далее» points to the first empty required field (phone)")
    a = await click(dp, b, 111, "bf:send")
    check(a and "Телефон" in a and "Марка" in a and "Описание проблемы" in a, "send blocked, missing fields listed")

    await click(dp, b, 111, "bf:phone")
    await text(dp, b, 111, "12345")
    check("Неверный номер" in last(111)[0], "bad phone rejected")
    await text(dp, b, 111, contact=Contact(phone_number="998901234567", first_name="M", user_id=111))
    check("+998901234567" in last(111)[0] and buttons(111)[0] == "bf:brand", "phone saved, next → brand")

    await click(dp, b, 111, "bf:brand")
    await click(dp, b, 111, "bk:b:1")          # MAN -> model buttons right away
    check("модель" in last(111)[0].lower() and "bk:m:0" in buttons(111), "model buttons offered after brand")
    await click(dp, b, 111, "bk:m:0")          # TGS
    check("MAN" in last(111)[0] and "TGS" in last(111)[0], "brand+model on the card")

    await click(dp, b, 111, "bf:car_desc")
    await text(dp, b, 111, "2019, D2066, пробег 600 тыс, 30 A 123 BC")
    check("D2066" in last(111)[0], "car description saved")

    await click(dp, b, 111, "bf:services")
    await click(dp, b, 111, "bf:sv:engine")
    await click(dp, b, 111, "bf:sv:fuel")
    kb = next(x[2] for x in reversed(SENT) if x[0] == 111 and x[2] is not None)
    texts = [b_.text for row in kb.inline_keyboard for b_ in row]
    check(sum(t_.startswith("✅") for t_ in texts) >= 2, "services toggled with ✅")
    await click(dp, b, 111, "bf:card")
    check("Ремонт двигателя" in last(111)[0] and "Топливная система" in last(111)[0], "two services on the form")
    await click(dp, b, 111, "bf:problem")
    await text(dp, b, 111, "Не набирает мощность, чёрный дым")
    await click(dp, b, 111, "bf:date")
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    await click(dp, b, 111, f"bf:d:{tomorrow.isoformat()}")
    check(tomorrow.strftime("%d.%m.%Y") in last(111)[0], "desired date saved")

    await click(dp, b, 111, "bf:photos")
    await text(dp, b, 111, photo="P1", album="g1")
    await text(dp, b, 111, photo="P2", album="g1")
    check("2/3" in last(111)[0], "album photos added (2/3)")
    await click(dp, b, 111, "bf:card")
    check("2 из 3" in last(111)[0] and "bf:send" in buttons(111) and "bf:phone" != buttons(111)[0],
          "form complete: all required filled")

    await click(dp, b, 111, "bf:send")
    await click(dp, b, 111, "bf:send")  # double tap
    async with Session() as s:
        n = await s.scalar(select(func.count(Request.id)))
        r = await s.scalar(select(Request))
    check(n == 1 and r.number == "NS-000001", "exactly one request created")
    check(r.car_desc and r.year == 2019 and r.plate == "30A123BC" and r.desired_date is not None
          and r.photo_ids and "P2" in r.photo_ids, "all form fields stored (year/plate parsed from description)")
    check(any("Заявка успешно создана" in x for x in last(111, 4)), "client success message")
    check(any(x.startswith("[VENUE 39.6127") for x in last(111, 3)), "«Приеду сам» → service pin to client")
    to444 = last(444, 4)
    check(any("НОВАЯ ЗАЯВКА" in x and "NS-000001" in x and "D2066" in x for x in to444),
          "request delivered to @Najotservis automatically")
    check(any(x.startswith("[ALBUM 2]") for x in to444), "@Najotservis gets the photos as album")
    check(any("НОВАЯ ЗАЯВКА" in x for x in last(222, 6)), "owner from OWNER_IDS also notified")
    async with Session() as s:
        r1 = await s.get(Request, 1)
    check(r1.master_id == m444.id and r1.status == "assigned" and "fuel" in (r1.service_list or ""),
          "single mechanic → request auto-assigned, services stored")
    check(any("Новое задание" in x for x in last(444, 8)), "mechanic got the job automatically")
    check(any("Мастер назначен" in x for x in last(111, 4)), "client told the mechanic is assigned")

    # ---------- second request: the bot remembers name, phone and truck ----------
    await click(dp, b, 111, "bk:start")
    f2 = last(111)[0]
    check("прошлой заявке" in f2 and "+998901234567" in f2 and "MAN TGS" not in f2 and "MAN" in f2
          and "TGS" in f2 and "D2066" in f2 and "Не набирает" not in f2,
          "new form prefilled from last request (no old problem)")
    check(buttons(111)[0] == "bf:problem", "only the problem is left to fill")
    await click(dp, b, 111, "bf:newtruck")
    f3 = last(111)[0]
    check("D2066" not in f3 and "+998901234567" in f3 and buttons(111)[0] == "bf:brand",
          "«Другой грузовик» clears truck, keeps name/phone")
    await click(dp, b, 111, "home")

    # ---------- call-out: location required ----------
    await text(dp, b, 555, "/start")
    await click(dp, b, 555, "lang:ru")
    await click(dp, b, 555, "sos")
    await click(dp, b, 555, "sos:go")
    check("Срочная заявка" in last(555)[0] and "Где находится машина" in last(555)[0], "SOS form with location field")
    await click(dp, b, 555, "bf:brand")
    await text(dp, b, 555, "shacman")          # exact typed brand → model step
    await click(dp, b, 555, "bk:m:0")
    await click(dp, b, 555, "bf:problem")
    await text(dp, b, 555, "Травит воздух, давление падает", photo="P9")
    await click(dp, b, 555, "bf:phone")
    await text(dp, b, 555, "+998935556677")
    a = await click(dp, b, 555, "bf:send")
    check(a and "Где находится машина" in a, "call-out cannot be sent without location")
    await click(dp, b, 555, "bf:location")
    await text(dp, b, 555, location=Location(latitude=39.6542, longitude=66.9597))
    check("точка на карте" in last(555)[0], "location on the form")
    await click(dp, b, 555, "bf:send")
    to444 = [x[1] for x in SENT if x[0] == 444]
    check(any("СРОЧНО" in x and "NS-000002" in x for x in to444), "urgent alert to @Najotservis")
    check(any("[LOCATION 39.6542,66.9597]" in x for x in to444), "client location forwarded to @Najotservis")
    check(not any(x.startswith("[VENUE") for x in last(555, 3)), "call-out client doesn't get service pin")

    # ---------- switching «Приеду сам» → «Вызов мастера» asks location ----------
    await click(dp, b, 111, "bk:start")
    await click(dp, b, 111, "bf:mob:onsite")
    check("Где находится машина" in last(111, 2)[0], "choosing «Вызов мастера» asks for location")
    await text(dp, b, 111, "Трасса M39, 25 км, заправка Uzbekneftegaz")
    check("Трасса M39" in last(111)[0], "address/landmark accepted instead of pin")
    await click(dp, b, 111, "home")

    # ---------- owner assigns @Najotservis as mechanic ----------
    await click(dp, b, 222, f"o:asm:2:{m444.id}")
    check(any("Новое задание" in x for x in last(444, 5)), "@Najotservis gets the job")
    check(any("[LOCATION 39.6542" in x for x in last(444, 5)), "mechanic gets client location")
    a = await click(dp, b, 444, "ma:acc:2")
    check(a == "✅ Готово.", "@Najotservis accepts the job")
    await click(dp, b, 444, "ma:repair:2")
    check(any("Ремонт начат" in x for x in last(555, 2)), "client notified: repair started")

    # ---------- several mechanics: first to tap «Взять заявку» gets it ----------
    await click(dp, b, 222, "o:madd")
    import re as _re
    token = _re.search(r"start=m_([\w-]+)", last(222)[0]).group(1)
    await text(dp, b, 333, f"/start m_{token}")
    await click(dp, b, 333, "lang:ru")
    await click(dp, b, 111, "bk:start")
    await click(dp, b, 111, "bf:brand")
    await click(dp, b, 111, "bk:b:0")
    await click(dp, b, 111, "bf:card")
    await click(dp, b, 111, "bf:problem")
    await text(dp, b, 111, "Течёт масло из двигателя")
    await click(dp, b, 111, "bf:send")
    check(any("кто возьмёт" in x for x in last(333, 3)) and any("кто возьмёт" in x for x in last(444, 6)),
          "both mechanics get «Взять заявку»")
    a = await click(dp, b, 333, "mt:take:3")
    check(a == "✅ Заявка ваша!", "first mechanic takes the job")
    a = await click(dp, b, 444, "mt:take:3")
    check(a and "уже взял" in a, "second mechanic sees it's taken")

    # ---------- owner picks a status -> client is notified (again on re-select) ----------
    a = await click(dp, b, 222, "o:sts:1:delivered")
    check(a and "Клиент уведомлён" in a, "owner sees «Клиент уведомлён»")
    check(any("Грузовик выдан" in x for x in last(111, 2)), "client got «Грузовик выдан»")
    before = sum("Грузовик выдан" in x[1] for x in SENT if x[0] == 111)
    a = await click(dp, b, 222, "o:sts:1:delivered")
    after = sum("Грузовик выдан" in x[1] for x in SENT if x[0] == 111)
    check(after == before + 1 and "Клиент уведомлён" in (a or ""), "re-selecting the same status re-sends to client")

    # ---------- security ----------
    a = await click(dp, b, 111, "o:menu")
    check(a == "⛔ Нет доступа.", "client can't open owner panel")
    await text(dp, b, 555, "/owner NAJOT")
    check("Неверный код" in last(555)[0], "/owner disabled")

    # ---------- AI from the form keeps typed data ----------
    await click(dp, b, 111, "bk:start")
    await click(dp, b, 111, "bf:problem")
    await text(dp, b, 111, "Стучит двигатель на холостых")
    await click(dp, b, 111, "ai:start")
    check("ai:back" in buttons(111), "AI opened from form offers «К заявке»")
    await click(dp, b, 111, "ai:back")
    check("Стучит двигатель" in last(111)[0], "back from AI: form data kept")

    # ---------- restart keeps the half-filled form ----------
    from bot.storage import DbStorage
    dp.fsm.storage = DbStorage()
    await click(dp, b, 111, "bf:card")
    check("Стучит двигатель" in last(111)[0], "half-filled form survives restart")

    # ---------- Mini App: menu button hands out the CURRENT form address ----------
    from bot.config import MINIAPP
    MINIAPP["url"] = "https://new-address.trycloudflare.com/"
    await text(dp, b, 111, "/menu")
    kb = next(x[2] for x in reversed(SENT) if x[0] == 111 and x[2] is not None)
    first = kb.inline_keyboard[0][0]
    check(first.web_app and first.web_app.url == "https://new-address.trycloudflare.com/?lang=ru",
          "«Записать грузовик на ремонт» opens the form directly")
    from bot.webapp import refresh_menus
    from aiogram.methods import EditMessageReplyMarkup
    edits = []
    orig = FakeSession.make_request

    async def spy(self, bot_, method, timeout=None):
        if isinstance(method, EditMessageReplyMarkup):
            edits.append(method.reply_markup.inline_keyboard[0][0].web_app.url)
            return True
        return await orig(self, bot_, method, timeout)
    FakeSession.make_request = spy
    MINIAPP["url"] = "https://after-restart.trycloudflare.com/"
    await refresh_menus(b)
    FakeSession.make_request = orig
    check("https://after-restart.trycloudflare.com/?lang=ru" in edits, "after restart the saved menu gets the new address")
    await click(dp, b, 111, "lang:uz")
    kb = next(x[2] for x in reversed(SENT) if x[0] == 111 and x[2] is not None)
    check(kb.inline_keyboard[0][0].web_app.url.endswith("?lang=uz"), "form opens in the language chosen in the bot (uz)")
    await click(dp, b, 111, "lang:ru")
    MINIAPP["url"] = None

    async with Session() as s:
        failed = await s.scalar(select(func.count(Notification.id)).where(Notification.ok.is_(False)))
    check(failed == 0, f"all notifications delivered ({failed} failed)")
    print(f"\nTOTAL: {len(FAILS)} failed", FAILS)


asyncio.run(main())
