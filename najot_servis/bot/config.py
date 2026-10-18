import os
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _ids(raw: str) -> set[int]:
    return {int(x) for x in raw.replace(" ", "").split(",") if x.lstrip("-").isdigit()}


def _db_url(raw: str) -> str:
    """Accept Render/Heroku style 'postgres://…' URLs and switch them to the async driver."""
    for prefix in ("postgres://", "postgresql://"):
        if raw.startswith(prefix):
            return "postgresql+asyncpg://" + raw[len(prefix):]
    return raw


# On Render the public https address of the service is provided automatically
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    owner_ids: set[int] = field(default_factory=lambda: _ids(os.getenv("OWNER_IDS", "")))
    owner_setup_code: str = os.getenv("OWNER_SETUP_CODE", "")
    # Where new-request alerts go: chat IDs and/or @usernames (accounts, groups or channels)
    notify_targets: tuple[str, ...] = tuple(
        x.strip() for x in os.getenv("NOTIFY_TARGETS", "@Najotservis").split(",") if x.strip())
    # Telegram usernames that automatically get the owner role once they open the bot
    owner_usernames: frozenset[str] = frozenset(
        x.strip().lstrip("@").lower() for x in os.getenv("OWNER_USERNAMES", "Najotservis").split(",") if x.strip())
    # Telegram usernames that are also mechanics (get jobs assigned), even if they are owners
    master_usernames: frozenset[str] = frozenset(
        x.strip().lstrip("@").lower() for x in os.getenv("MASTER_USERNAMES", "").split(",") if x.strip())
    database_url: str = _db_url(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///najot_servis.db"))
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "claude-opus-5-5")
    webhook_url: str = os.getenv("WEBHOOK_URL", "") or RENDER_URL
    webhook_path: str = os.getenv("WEBHOOK_PATH", "/tg/webhook")
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
    webapp_host: str = os.getenv("WEBAPP_HOST", "0.0.0.0")
    webapp_port: int = int(os.getenv("PORT") or os.getenv("WEBAPP_PORT", "8080"))   # Render sets PORT
    # free hosting that sleeps when idle (Render): ping our own public URL to stay awake
    keep_awake: bool = os.getenv("KEEP_AWAKE", "1" if RENDER_URL else "0") not in ("0", "false", "no")
    redis_url: str = os.getenv("REDIS_URL", "")
    # Mini App (website form inside Telegram): your own https address, or empty = free Cloudflare tunnel
    miniapp_url: str = os.getenv("MINIAPP_URL", "") or RENDER_URL
    miniapp_port: int = int(os.getenv("MINIAPP_PORT", "8091"))
    miniapp_enabled: bool = os.getenv("MINIAPP_ENABLED", "1") not in ("0", "false", "no")
    timezone: str = os.getenv("TIMEZONE", "Asia/Tashkent")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
MINIAPP: dict = {"url": None}   # filled at startup when the Mini App address is known
TZ = ZoneInfo(config.timezone)


def now() -> datetime:
    """Local (service) time without tzinfo — all DB timestamps are stored this way."""
    return datetime.now(TZ).replace(tzinfo=None, microsecond=0)


def fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else "—"


# Default contacts (editable by owner in ⚙️ Settings)
DEFAULT_SETTINGS = {
    "address": "Самаркандский район, ул. Бинафша, 41, дом 85",
    "phone": "+998995492447",
    "phone2": "+998955492447",
    "telegram": "Najotservis",
    "instagram": "najot.servis24.7",
    "work_hours": "09:00 – 20:00",
    "location": "39.612700,66.994350",   # service coordinates "lat,lon"
}

TRUCK_BRANDS_MAIN = [
    "Isuzu", "MAN", "KAMAZ", "Shacman", "Howo", "Mercedes-Benz",
    "Volvo", "Scania", "DAF", "FAW", "Foton", "JAC",
    "Dongfeng", "Hyundai", "Iveco", "MAZ", "GAZ", "Hino",
]
BRANDS = TRUCK_BRANDS_MAIN + [
    # extra truck brands available through search
    "Sitrak", "Sinotruk", "Renault Trucks", "Ford Trucks", "Mitsubishi Fuso", "Daewoo", "Ural", "BAW", "Chenglong",
    "Beiben", "SAIC Hongyan", "Kenworth", "Freightliner", "International", "Tatra", "ZIL", "Tata", "Ashok Leyland",
    "Chevrolet", "JMC", "Kia", "Yuejin", "Camc", "XCMG", "Sany",
]
MAIN_BRANDS = TRUCK_BRANDS_MAIN

# Popular models shown as buttons on the model step (the client can still type any model)
TRUCK_MODELS = {
    "Isuzu": ["NQR 90", "NPR 75", "NMR 85", "FVR 34", "FVZ", "Giga"],
    "MAN": ["TGS", "TGX", "TGA", "TGM", "TGL"],
    "KAMAZ": ["65115", "5490", "43118", "6520", "65117", "4308"],
    "Shacman": ["X3000", "F3000", "X6000", "L3000", "H3000"],
    "Howo": ["A7", "T5G", "TX", "T7H", "Max"],
    "Mercedes-Benz": ["Actros", "Axor", "Atego", "Arocs", "Sprinter"],
    "Volvo": ["FH", "FM", "FMX", "FL"],
    "Scania": ["R", "S", "G", "P"],
    "DAF": ["XF", "CF", "LF", "XG"],
    "FAW": ["J6", "J7", "Tiger V", "CA3250"],
    "Foton": ["Auman", "Aumark", "Ollin", "Forland"],
    "JAC": ["N-series", "Gallop", "K7"],
    "Dongfeng": ["KX", "KL", "Captain", "Tianjin"],
    "Hyundai": ["HD65", "HD78", "HD120", "Xcient", "Mighty"],
    "Iveco": ["Stralis", "S-Way", "Trakker", "Eurocargo", "Daily"],
    "MAZ": ["5440", "6430", "5516", "6501", "4370"],
    "GAZ": ["ГАЗель", "ГАЗель Next", "Валдай", "ГАЗон Next", "Садко"],
    "Hino": ["300", "500", "700"],
}

# Truck body types: code -> emoji (names in i18n: body_<code>)
BODY_TYPES = [
    ("tractor", "🚛"), ("dump", "🏗"), ("flatbed", "🚚"), ("van", "📦"),
    ("reefer", "❄️"), ("tanker", "🛢"), ("special", "🚜"), ("light", "🛻"), ("other", "🚚"),
]

# How the truck gets to the service (names in i18n: mob_<code>).
# drive  -> client comes himself, bot sends him the service location
# onsite -> "call": the client's geolocation is required and forwarded to staff
# ("tow" is kept only for labels of old requests)
MOBILITY = [("drive", "🚛"), ("onsite", "🆘")]
CALL_MODES = ("onsite", "tow")


def parse_coords(raw: str | None) -> tuple[float, float] | None:
    """'39.6127,66.99435' or any Google Maps link containing q=/ll=/@lat,lon -> (lat, lon)."""
    import re
    if not raw:
        return None
    m = re.search(r"(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)", raw)
    if not m:
        return None
    lat, lon = float(m.group(1)), float(m.group(2))
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else None

# code, emoji — names are in i18n (svc_<code>)
SERVICES = [
    ("comp_diag", "🔍"),
    ("engine", "🔧"),
    ("fuel", "⛽"),
    ("gearbox", "⚙️"),
    ("chassis", "🛞"),
    ("brakes", "🛑"),
    ("electric", "🔋"),
    ("oil", "🛢️"),
    ("tires", "🛞"),
    ("ecology", "🧪"),
    ("ac", "❄️"),
    ("other", "🔧"),
]

# status code -> emoji; names in i18n (st_<code>)
STATUSES = {
    "new": "🟡",
    "accepted": "🔵",
    "assigned": "👨‍🔧",
    "diagnostics": "🔧",
    "repair": "🛠️",
    "waiting_parts": "⏰",
    "ready": "✅",
    "delivered": "🚛",
    "cancelled": "❌",
}
ACTIVE_STATUSES = ("new", "accepted", "assigned", "diagnostics", "repair", "waiting_parts", "ready")
IN_WORK_STATUSES = ("accepted", "assigned", "diagnostics", "repair", "waiting_parts")
DONE_STATUSES = ("ready", "delivered")
