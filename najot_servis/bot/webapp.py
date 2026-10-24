"""Telegram Mini App: the NAJOT SERVIS website form (webapp/site.html) opened inside Telegram.

* The bot serves the site page and injects a small bridge script: inside Telegram the form's
  «ОТПРАВИТЬ ЗАЯВКУ» posts to /api/webapp/request instead of the site's own backend.
* Every API call carries Telegram `initData`; its HMAC signature is verified with the bot token,
  so nobody can send requests in someone else's name.
* A public https address is required by Telegram: either MINIAPP_URL from .env, or a free
  Cloudflare quick tunnel started from tools/cloudflared.exe (the URL is picked up automatically).
"""
import asyncio
import base64
import hashlib
import logging
import re
import time
from pathlib import Path

from aiohttp import web
from aiogram import Bot
from aiogram.types import BufferedInputFile, InputMediaPhoto, MenuButtonCommands
from aiogram.utils.web_app import safe_parse_webapp_init_data
from sqlalchemy import select

from .config import CALL_MODES, MINIAPP, config
from .db import Session, User
from .i18n import t
from .services import create_request, get_request, send_service_location
from .ui import btn, markup, nav

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "webapp" / "site.html"
CLOUDFLARED = ROOT / "tools" / "cloudflared.exe"
MAX_AGE = 24 * 3600
COORDS_RE = re.compile(r"q=(-?\d{1,2}\.\d+),(-?\d{1,3}\.\d+)")
ADDR_RE = re.compile(r"Ориентир:\s*(.+?)(?:\s·\s|$)")
SVC_RE = re.compile(r"Услуга:\s*(.+?)(?:\s·\s|$)")

BRIDGE = r"""
<script>
/* ===== NAJOT SERVIS × Telegram Mini App bridge (added by the bot) ===== */
(function(){
  var tg = window.Telegram && window.Telegram.WebApp;
  if (!tg || !tg.initData) return;                 /* opened outside Telegram: the normal website */
  try { tg.ready(); tg.expand(); } catch (e) {}
  document.documentElement.classList.add('in-tg');
  /* inside Telegram show ONLY the request form — no header, titles, other sections or bottom bar */
  var css = document.createElement('style');
  css.textContent =
    'html.in-tg .skip, html.in-tg #hdr, html.in-tg footer, html.in-tg .mbar, html.in-tg .ai-fab,' +
    'html.in-tg #site > main > *:not(#request), html.in-tg #request .req-head { display: none !important; }' +
    'html.in-tg #request { padding: 14px 0 24px !important; margin: 0 !important; min-height: 100vh; }' +
    'html.in-tg #request .req { display: block !important; }' +
    'html.in-tg body { padding-bottom: 0 !important; }' +
    'html.in-tg .reveal { opacity: 1 !important; transform: none !important; }';
  document.head.appendChild(css);
  try { var bg = getComputedStyle(document.body).backgroundColor; tg.setHeaderColor('#111317'); tg.setBackgroundColor(bg); } catch (e) {}

  /* geolocation through Telegram when the app supports it, browser API otherwise */
  var geo = navigator.geolocation;
  if (geo && tg.LocationManager){
    var orig = geo.getCurrentPosition.bind(geo);
    geo.getCurrentPosition = function(ok, fail, opts){
      var LM = tg.LocationManager;
      function viaTg(){
        LM.getLocation(function(l){
          if (l && l.latitude != null) ok({ coords: { latitude: l.latitude, longitude: l.longitude, accuracy: l.horizontal_accuracy || 0 } });
          else orig(ok, fail, opts);
        });
      }
      try {
        if (LM.isInited) { LM.isLocationAvailable ? viaTg() : orig(ok, fail, opts); }
        else LM.init(function(){ LM.isLocationAvailable ? viaTg() : orig(ok, fail, opts); });
      } catch (e) { orig(ok, fail, opts); }
    };
  }

  function api(path, body){
    return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' },
                         body: JSON.stringify(Object.assign({ initData: tg.initData }, body || {})) })
      .then(function(r){ return r.json().then(function(j){
        if (!r.ok || !j.ok){ var e = new Error(j.message || 'server'); e.code = j.code || 'server'; if (j.fields) e.fields = j.fields; throw e; }
        return j; }); });
  }
  function setVal(id, v){
    var i = document.getElementById(id);
    if (i && !i.value && v){ i.value = v; i.dispatchEvent(new Event('input', { bubbles: true })); }
  }
  function goForm(){
    location.hash = '#request';
    var el = document.getElementById('request'); if (el) el.scrollIntoView();
  }
  window.addEventListener('load', function(){
    goForm(); setTimeout(goForm, 600);
    /* «🆘 Сломался в пути» opens the same form with «Вызов мастера» already chosen */
    if (/[?&]sos=1/.test(location.search)){
      var call = document.querySelector('input[name="visit"][value="call"]');
      if (call){ call.checked = true; call.dispatchEvent(new Event('change', { bubbles: true })); }
    }
    api('/api/webapp/me').then(function(j){
      var p = j.prefill || {};
      setVal('f_name', p.name); setVal('f_phone', p.phone); setVal('f_brand', p.brand);
      setVal('f_model', p.model); setVal('f_carDesc', p.carDesc);
    }).catch(function(){});
    if (window.NS && NS.ready){
      NS.ready.then(function(){
        NS.api.createRequest = function(d){
          var v = document.querySelector('input[name="visit"]:checked');
          var a = document.getElementById('f_addr');
          return api('/api/webapp/request', { data: d, visit: v ? v.value : 'self', addr: a ? a.value : '' })
            .then(function(j){
              try { tg.HapticFeedback.notificationOccurred('success'); } catch (e) {}
              setTimeout(function(){ try { tg.close(); } catch (e) {} }, 3500);
              return { no: j.number, id: j.number, phone: j.phone, status: 'new', tg: { status: 'sent' } };
            });
        };
      });
    }
  });
})();
</script>
"""
TG_SCRIPT = '<script src="https://telegram.org/js/telegram-web-app.js"></script>'


def build_page() -> bytes:
    html = SITE.read_text(encoding="utf-8")
    # inside the mini app the bot itself is the backend — switch off the site's Google relay
    html = re.sub(r"window\.NS_TG_RELAY\s*=\s*'[^']*';", "window.NS_TG_RELAY = '';", html, count=1)
    html = html.replace("<head>", "<head>\n" + TG_SCRIPT, 1) if "<head>" in html else TG_SCRIPT + html
    i = html.rfind("</body>")
    html = html[:i] + BRIDGE + html[i:] if i >= 0 else html + BRIDGE
    return html.encode("utf-8")


def _auth(init_data: str):
    """Verify Telegram's signature; returns the WebAppInitData or raises web.HTTPUnauthorized."""
    try:
        data = safe_parse_webapp_init_data(token=config.bot_token, init_data=init_data or "")
    except ValueError:
        raise web.HTTPUnauthorized(text='{"ok":false,"code":"auth"}', content_type="application/json")
    if data.user is None or time.time() - data.auth_date.timestamp() > MAX_AGE:
        raise web.HTTPUnauthorized(text='{"ok":false,"code":"auth"}', content_type="application/json")
    return data


async def _user(s, tg_user) -> User:
    u = await s.scalar(select(User).where(User.tg_id == tg_user.id))
    if u is None:
        u = User(tg_id=tg_user.id, username=tg_user.username,
                 full_name=" ".join(x for x in (tg_user.first_name, tg_user.last_name) if x),
                 lang=(tg_user.language_code or "ru")[:2] if (tg_user.language_code or "")[:2] in ("ru", "uz", "en") else "ru")
        s.add(u)
        await s.flush()
    return u


def _err(code: str, status: int = 400, **extra) -> web.Response:
    return web.json_response({"ok": False, "code": code, **extra}, status=status)


async def page(request: web.Request) -> web.Response:
    return web.Response(body=request.app["page"], content_type="text/html", charset="utf-8",
                        headers={"Cache-Control": "no-store"})


async def me(request: web.Request) -> web.Response:
    from .handlers.booking import remembered
    body = await request.json()
    init = _auth(body.get("initData"))
    async with Session() as s:
        u = await _user(s, init.user)
        await s.commit()
        r = await remembered(s, u)
    prefill = {"name": r.get("name") or u.full_name, "phone": r.get("phone") or u.phone,
               "brand": r.get("brand"), "model": r.get("model"), "carDesc": r.get("car_desc")}
    return web.json_response({"ok": True, "prefill": {k: v for k, v in prefill.items() if v}})


def _decode_photo(data_url: str) -> bytes | None:
    m = re.match(r"data:image/[\w.+-]+;base64,(.+)", data_url or "", re.S)
    if not m:
        return None
    raw = base64.b64decode(m.group(1), validate=False)
    return raw if 0 < len(raw) <= 8 * 1024 * 1024 else None


async def create(request: web.Request) -> web.Response:
    from .handlers.booking import normalize_phone, normalize_plate, parse_year
    body = await request.json()
    init = _auth(body.get("initData"))
    bot: Bot = request.app["bot"]
    d = body.get("data") or {}
    if (d.get("website") or "").strip():           # the site's honeypot field
        return _err("spam")
    name = (d.get("name") or "").strip()[:60]
    phone = normalize_phone(d.get("phone") or "")
    brand = (d.get("brand") or "").strip()[:40]
    problem = (d.get("problem") or "").strip()[:1500]
    bad = {k: 1 for k, ok in (("name", len(name) >= 2), ("phone", bool(phone)), ("brand", bool(brand)),
                              ("problem", len(problem) >= 5)) if not ok}
    if bad:
        return _err("fields", fields=bad)
    comment = d.get("comment") or ""
    call = body.get("visit") == "call"
    lat = lon = None
    m = COORDS_RE.search(comment)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
    addr = (body.get("addr") or "").strip()[:300] or (ADDR_RE.search(comment).group(1) if ADDR_RE.search(comment) else "")
    if call and lat is None and len(addr) < 3:
        return _err("location", message="Отметьте локацию или напишите адрес")
    svc = SVC_RE.search(comment)
    if svc:
        problem = f"{problem}\n🔧 {svc.group(1).strip()}"[:1500]
    car_desc = (d.get("carDesc") or "").strip()[:300]
    year = next((parse_year(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", car_desc) if parse_year(y)), None)
    plate = next((normalize_plate(p) for p in re.findall(r"\b\d{2}\s?[A-Za-z]\s?\d{3}\s?[A-Za-z]{2}\b", car_desc)), None)
    desired = (d.get("desiredDate") or "")[:10] or None

    async with Session() as s:
        u = await _user(s, init.user)
        await s.commit()
        lang = u.lang or "ru"
        # photos: upload them once into the client's chat (that's also their confirmation) to get file_ids
        photo_ids: list[str] = []
        raws = [x for x in (_decode_photo(p) for p in (d.get("photos") or [])[:3]) if x]
        if raws:
            try:
                media = [InputMediaPhoto(media=BufferedInputFile(raw, filename=f"photo{i + 1}.jpg"))
                         for i, raw in enumerate(raws)]
                if len(media) == 1:
                    msg = await bot.send_photo(u.tg_id, media[0].media, caption="📷")
                    photo_ids = [msg.photo[-1].file_id]
                else:
                    msgs = await bot.send_media_group(u.tg_id, media)
                    photo_ids = [x.photo[-1].file_id for x in msgs if x.photo]
            except Exception:
                log.exception("webapp photo upload failed")
        data = {"name": name, "phone": phone, "brand": brand, "model": (d.get("model") or "").strip()[:40],
                "car_desc": car_desc or None, "year": year, "plate": plate, "problem": problem,
                "desired_date": desired, "mobility": "onsite" if call else "drive",
                "latitude": lat, "longitude": lon, "address_note": addr or None,
                "photo_ids": photo_ids, "service": "other"}
        idem = hashlib.sha256(f"{init.user.id}|{init.hash}|{problem}".encode()).hexdigest()[:40]
        r, created = await create_request(s, bot, data, u, for_client=True, idem_key=idem, source="webapp")
        log.info("webapp request %s %s by tg=%s", r.number, "created" if created else "dedup", u.tg_id)
        if created:
            r = await get_request(s, r.id)
            await bot.send_message(u.tg_id, t(lang, "bk_created", number=r.number),
                                   reply_markup=markup([btn(t(lang, "btn_open_request"), f"rq:{r.id}")], nav(lang)))
            if r.mobility not in CALL_MODES:
                await send_service_location(bot, s, u.tg_id, lang, request_id=r.id)
            await s.commit()
    return web.json_response({"ok": True, "number": r.number, "phone": phone})


async def health(request: web.Request) -> web.Response:
    return web.json_response({"app": "najot-bot-miniapp"}, status=404)   # 404 keeps the site in "local" mode


def make_app(bot: Bot) -> web.Application:
    app = web.Application(client_max_size=12 * 1024 * 1024)
    app["bot"] = bot
    app["page"] = build_page()
    app.router.add_get("/", page)
    app.router.add_get("/index.html", page)
    app.router.add_post("/api/webapp/me", me)
    app.router.add_post("/api/webapp/request", create)
    app.router.add_get("/api/health", health)
    app.router.add_get("/ping", lambda r: web.Response(text="ok"))
    return app


# ---------------- public https address ----------------

async def _drain(stream, found: asyncio.Future):
    while True:
        line = await stream.readline()
        if not line:
            break
        text = line.decode("utf-8", "replace")
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", text)
        if m and not found.done():
            found.set_result(m.group(0))


async def start_tunnel(port: int) -> tuple[str | None, asyncio.subprocess.Process | None]:
    if not CLOUDFLARED.exists():
        log.warning("mini app: tools/cloudflared.exe not found and MINIAPP_URL not set — the form stays in chat")
        return None, None
    proc = await asyncio.create_subprocess_exec(
        str(CLOUDFLARED), "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    found: asyncio.Future = asyncio.get_running_loop().create_future()
    asyncio.create_task(_drain(proc.stderr, found))
    asyncio.create_task(_drain(proc.stdout, found))
    try:
        url = await asyncio.wait_for(found, timeout=45)
    except asyncio.TimeoutError:
        log.warning("mini app: Cloudflare tunnel did not start in time")
        proc.terminate()
        return None, None
    return url, proc


async def wait_reachable(url: str, attempts: int = 20) -> bool:
    import aiohttp
    async with aiohttp.ClientSession() as http:
        for _ in range(attempts):
            try:
                async with http.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                pass
            await asyncio.sleep(2)
    return False


async def start_miniapp(bot: Bot) -> asyncio.subprocess.Process | None:
    """Start the local web server and the public address; publish the URL for buttons and the menu."""
    port = config.miniapp_port
    runner = web.AppRunner(make_app(bot))
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", port).start()   # public access only via the tunnel / Caddy
    if config.miniapp_url:
        await _publish(bot, config.miniapp_url)
        return None
    url, proc = await start_tunnel(port)
    if url:
        await _publish(bot, url)
    asyncio.create_task(_watchdog(bot, port, proc))
    return _TUNNEL.get("proc") or proc


_TUNNEL: dict = {}


async def _publish(bot: Bot, url: str) -> None:
    url = url.rstrip("/") + "/"
    ok = await wait_reachable(url + "ping")
    log.info("mini app: %s (%s)", url, "reachable ✓" if ok else "not reachable yet")
    changed = MINIAPP.get("url") != url
    MINIAPP["url"] = url
    try:   # the button left of the input field stays the regular «Меню» (commands list)
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    except Exception:
        log.warning("could not set the menu button", exc_info=True)
    if changed:
        asyncio.create_task(refresh_menus(bot))


async def refresh_menus(bot: Bot) -> None:
    """Re-point «Записать грузовик на ремонт» in clients' latest menus to the new form address."""
    from .db import Setting
    from .ui import client_menu
    cutoff = time.time() - 47 * 3600          # Telegram allows editing messages younger than 48 h
    done = 0
    async with Session() as s:
        rows = (await s.scalars(select(Setting).where(Setting.key.like("menu:%")))).all()
        for row in rows:
            try:
                mid, lang, role, ts = row.value.split("|")
                if float(ts) < cutoff:
                    await s.delete(row)
                    continue
                await bot.edit_message_reply_markup(chat_id=int(row.key.split(":", 1)[1]), message_id=int(mid),
                                                    reply_markup=client_menu(lang, role))
                done += 1
            except Exception as e:     # message deleted / not modified / user blocked the bot
                if "not modified" not in str(e):
                    await s.delete(row)
            await asyncio.sleep(0.05)
        await s.commit()
    log.info("mini app: re-pointed %s client menus to the new address", done)


async def _watchdog(bot: Bot, port: int, proc) -> None:
    """Every minute: if the tunnel died or its address stopped answering, start a new one and republish."""
    _TUNNEL["proc"] = proc
    while True:
        await asyncio.sleep(60)
        try:
            proc = _TUNNEL.get("proc")
            alive = proc is not None and proc.returncode is None
            if alive and MINIAPP.get("url") and await wait_reachable(MINIAPP["url"] + "ping", attempts=3):
                continue
            log.warning("mini app: tunnel down — restarting")
            if alive:
                proc.terminate()
            MINIAPP["url"] = None
            url, proc = await start_tunnel(port)
            _TUNNEL["proc"] = proc
            if url:
                await _publish(bot, url)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("mini app watchdog error")
