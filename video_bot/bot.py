"""Video downloader bot: send a link (TikTok, YouTube, Instagram, ...) -> get the video back.

Under every video: «📥 Скачать файлом», «🎵 Аудио», «📞 Позвонить» and the phone numbers.
Uses yt-dlp; picks a single-file format (video+audio together), so ffmpeg is not required.
"""
import asyncio
import logging
import os
import re
import secrets
import shutil
import sys
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yt_dlp
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import (BotCommand, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup,
                           Message)
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))
# VIDEO_BOT_TOKEN when both bots share one hosting service (Render); BOT_TOKEN from the local .env otherwise
TOKEN = os.getenv("VIDEO_BOT_TOKEN") or os.getenv("BOT_TOKEN", "")
PHONES = [p.strip() for p in os.getenv("PHONES", "").split(",") if p.strip()]
FOOTER_TITLE = os.getenv("FOOTER_TITLE", "")
FOOTER_BOT = os.getenv("FOOTER_BOT", "")
MAX_BYTES = int(float(os.getenv("MAX_MB", "49")) * 1024 * 1024)

URL_RE = re.compile(r"https?://\S+", re.I)
BASE_DIR = Path(__file__).resolve().parent
TMP = Path(tempfile.gettempdir()) / "video_bot"
log = logging.getLogger("video_bot")

dp = Dispatcher()
_links: dict[str, str] = {}            # short key -> url (callback_data is limited to 64 bytes)
_busy: set[int] = set()                # one download per user at a time
_slots = asyncio.Semaphore(3)          # at most 3 downloads at once


def fmt_phone(p: str) -> str:
    d = "".join(ch for ch in p if ch.isdigit())
    if len(d) == 12 and d.startswith("998"):
        return f"+998 {d[3:5]} {d[5:8]}-{d[8:10]}-{d[10:12]}"
    return p


def footer() -> str:
    lines = []
    if FOOTER_TITLE:
        lines.append(f"<b>{FOOTER_TITLE}</b>")
    if PHONES:
        lines.append("📞 " + " · ".join(fmt_phone(p) for p in PHONES))
    if FOOTER_BOT:
        lines.append(f"🤖 {FOOTER_BOT}")
    return "\n".join(lines)


def video_kb(key: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="💾 Сохранить в галерею", callback_data="gallery", style="primary")],
            [InlineKeyboardButton(text="📥 Файлом", callback_data=f"file:{key}", style="primary"),
             InlineKeyboardButton(text="🎵 Аудио", callback_data=f"audio:{key}", style="primary")]]
    if PHONES:
        rows.append([InlineKeyboardButton(text="📞 Позвонить", callback_data="call", style="success")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


try:  # ffmpeg bundled as a Python package — needed to join separate video+audio tracks (YouTube)
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg")


def _formats(audio: bool, height: int) -> str:
    if audio:
        return "ba[ext=m4a]/ba"
    single = f"b[ext=mp4][height<={height}]/b[height<={height}]"
    if not FFMPEG:
        return single + "/b"
    # separate best video + audio (merged to mp4 by ffmpeg), or a ready single file
    return f"bv*[ext=mp4][height<={height}]+ba[ext=m4a]/bv*[height<={height}]+ba/{single}/b"


def _download(url: str, audio: bool) -> tuple[Path, dict]:
    """Blocking yt-dlp download (run in a thread). Returns (file, info).
    Tries 720p first and steps down until the file fits Telegram's 50 MB bot limit."""
    last_error: Exception = ValueError("too_big")
    for height in ((0,) if audio else (720, 480, 360, 240)):
        workdir = TMP / secrets.token_hex(6)
        workdir.mkdir(parents=True, exist_ok=True)
        opts = {
            "format": _formats(audio, height), "outtmpl": str(workdir / "%(id)s.%(ext)s"), "noplaylist": True,
            "quiet": True, "no_warnings": True, "noprogress": True, "socket_timeout": 30, "retries": 2,
            "restrictfilenames": True, "merge_output_format": "mp4",
        }
        if FFMPEG:
            opts["ffmpeg_location"] = FFMPEG
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info.get("_type") == "playlist" and info.get("entries"):
                    info = info["entries"][0]
        except Exception as e:
            shutil.rmtree(workdir, ignore_errors=True)
            raise e
        files = [f for f in workdir.iterdir() if f.is_file() and not f.name.endswith((".part", ".ytdl"))]
        if files:
            best = max(files, key=lambda f: f.stat().st_size)
            if best.stat().st_size <= MAX_BYTES:
                return best, info
        shutil.rmtree(workdir, ignore_errors=True)
        last_error = ValueError("too_big")
    raise last_error


def _friendly_error(e: Exception) -> str:
    text = str(e).lower()
    if "too_big" in text or "max-filesize" in text or "larger than" in text:
        return "⚠️ Видео больше 50 МБ — Telegram не позволяет ботам отправлять такие файлы. Попробуйте более короткое видео."
    if "private" in text or "login" in text or "sign in" in text or "cookies" in text:
        return "🔒 Видео закрытое или требует входа в аккаунт — скачать не получится."
    if "unsupported url" in text:
        return "⚠️ Эта ссылка не поддерживается. Пришлите ссылку на видео (TikTok, YouTube, Instagram и др.)."
    return "⚠️ Не удалось скачать видео. Проверьте ссылку и попробуйте ещё раз."


async def fetch(url: str, audio: bool) -> tuple[Path, dict]:
    """YouTube sometimes answers 403 on the first try — retry a couple of times before giving up."""
    async with _slots:
        for attempt in range(3):
            try:
                return await asyncio.to_thread(_download, url, audio)
            except Exception as e:
                if attempt == 2 or not any(x in str(e) for x in ("403", "Forbidden", "timed out", "10054")):
                    raise
                log.info("retry %s after: %s", attempt + 1, str(e)[:120])
                await asyncio.sleep(1.5 * (attempt + 1))


def _cleanup(path: Path) -> None:
    shutil.rmtree(path.parent, ignore_errors=True)


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎬 <b>Скачать видео</b>\n\n"
        "Отправьте ссылку на видео — TikTok, YouTube, Instagram, Facebook, Likee, Pinterest и другие — "
        "и я пришлю его сюда.\n\n"
        "🇺🇿 Video havolasini yuboring — videoni shu yerga yuboraman.\n\n"
        "💾 <i>Чтобы видео сами сохранялись в галерею: Telegram → Настройки → Данные и память → "
        "«Сохранять в галерею» → «Личные чаты».</i>\n\n" + footer())


@dp.message(F.text.regexp(URL_RE))
async def on_link(message: Message, bot: Bot):
    url = URL_RE.search(message.text).group(0).rstrip(").,]")
    uid = message.from_user.id
    if uid in _busy:
        return await message.answer("⏳ Подождите, предыдущее видео ещё скачивается…")
    _busy.add(uid)
    status = await message.answer("⏳ Скачиваю видео…")
    path = None
    try:
        await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
        path, info = await fetch(url, audio=False)
        key = secrets.token_urlsafe(6)
        _links[key] = url
        if len(_links) > 5000:
            _links.pop(next(iter(_links)))
        title = (info.get("title") or "").strip()[:200]
        caption = (f"🎬 {title}\n\n" if title else "") + footer()
        await bot.send_video(message.chat.id, FSInputFile(path), caption=caption[:1024], supports_streaming=True,
                             width=info.get("width"), height=info.get("height"),
                             duration=int(info["duration"]) if info.get("duration") else None,
                             reply_markup=video_kb(key))
        log.info("sent video uid=%s url=%s size=%.1fMB", uid, url, path.stat().st_size / 1e6)
    except Exception as e:
        log.warning("download failed uid=%s url=%s: %s", uid, url, e)
        await message.answer(_friendly_error(e))
    finally:
        _busy.discard(uid)
        if path:
            _cleanup(path)
        try:
            await status.delete()
        except TelegramBadRequest:
            pass


async def _send_variant(cb: CallbackQuery, bot: Bot, audio: bool):
    key = cb.data.split(":", 1)[1]
    url = _links.get(key)
    if not url:
        return await cb.answer("⚠️ Ссылка устарела — отправьте её ещё раз.", show_alert=True)
    uid = cb.from_user.id
    if uid in _busy:
        return await cb.answer("⏳ Подождите, идёт загрузка…")
    _busy.add(uid)
    await cb.answer("⏳ Готовлю файл…")
    path = None
    try:
        path, info = await fetch(url, audio=audio)
        title = (info.get("title") or "video").strip()[:60]
        if audio:
            await bot.send_audio(cb.from_user.id, FSInputFile(path, filename=f"{title}{path.suffix}"),
                                 title=title, caption=footer()[:1024])
        else:
            await bot.send_document(cb.from_user.id, FSInputFile(path, filename=f"{title}{path.suffix}"),
                                    caption=footer()[:1024])
    except Exception as e:
        log.warning("variant failed uid=%s audio=%s: %s", uid, audio, e)
        await bot.send_message(cb.from_user.id, _friendly_error(e))
    finally:
        _busy.discard(uid)
        if path:
            _cleanup(path)


@dp.callback_query(F.data.startswith("file:"))
async def on_file(cb: CallbackQuery, bot: Bot):
    await _send_variant(cb, bot, audio=False)


@dp.callback_query(F.data.startswith("audio:"))
async def on_audio(cb: CallbackQuery, bot: Bot):
    await _send_variant(cb, bot, audio=True)


GALLERY_HINT = (  # alert limit is 200 characters
    "💾 Автосохранение (1 раз):\n"
    "Telegram → Настройки → Данные и память → «Сохранять в галерею» → включите «Личные чаты».\n"
    "Дальше все видео сохраняются сами ✅"
)

AUTOSAVE_GUIDE = (
    "💾 <b>Как включить автосохранение в галерею</b>\n"
    "Делается один раз — потом каждое видео из бота само попадает в галерею.\n\n"
    "📱 <b>Android</b>: Telegram → ☰ → <b>Настройки</b> → <b>Данные и память</b> → "
    "<b>Сохранять в галерею</b> → включите <b>Личные чаты</b>.\n\n"
    "🍏 <b>iPhone</b>: Telegram → <b>Настройки</b> → <b>Данные и память</b> → "
    "<b>Сохранять в Фото</b> → включите <b>Личные чаты</b>.\n\n"
    "Сохранить одно видео вручную: откройте его → ⋮ / ⋯ → «Сохранить в галерею»."
)


@dp.callback_query(F.data == "gallery")
async def on_gallery(cb: CallbackQuery):
    """Bots can't write to the phone's gallery. Telegram's own auto-save setting does it with zero taps."""
    await cb.answer(GALLERY_HINT, show_alert=True)
    await cb.message.answer(AUTOSAVE_GUIDE)


@dp.callback_query(F.data == "call")
async def on_call(cb: CallbackQuery):
    """Inline buttons can't open tel: links — send contact cards, tapping one starts a call."""
    await cb.answer()
    for i, p in enumerate(PHONES):
        await cb.message.answer_contact(phone_number=p, first_name="NAJOT SERVIS" + (f" {i + 1}" if i else ""))


@dp.message()
async def other(message: Message):
    await message.answer("🔗 Отправьте ссылку на видео — я его скачаю.\n🇺🇿 Video havolasini yuboring.")


async def main():
    (BASE_DIR / "logs").mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    fh = RotatingFileHandler(BASE_DIR / "logs" / "bot.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), handlers=[fh, sh])
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    if not TOKEN:
        sys.exit("BOT_TOKEN is not set in .env")
    shutil.rmtree(TMP, ignore_errors=True)
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    me = await bot.me()
    log.info("starting @%s", me.username)
    try:
        await bot.set_my_commands([BotCommand(command="start", description="🎬 Скачать видео")])
    except Exception:
        pass
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
