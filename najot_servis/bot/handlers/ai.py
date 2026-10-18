"""🤖 AI assistant: helps the client describe the problem, then pre-fills a booking.

Uses Claude (Anthropic API) when ANTHROPIC_API_KEY is set; otherwise falls back to a
built-in step-by-step questionnaire so the feature always works.
"""
import json
import logging
import re

import anthropic
from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import config, now
from ..db import User
from ..i18n import t
from ..ui import btn, h, markup, nav, show
from .booking import parse_year, render_form, start_booking

log = logging.getLogger(__name__)
router = Router(name="ai")

_client: anthropic.AsyncAnthropic | None = (
    anthropic.AsyncAnthropic(api_key=config.anthropic_api_key, timeout=60.0, max_retries=2)
    if config.anthropic_api_key else None)

LANG_NAMES = {"ru": "Russian", "uz": "Uzbek (Latin script)", "en": "English"}
MAX_TURNS = 16

SYSTEM_PROMPT = """You are the virtual assistant of NAJOT SERVIS, a service centre in Samarkand, Uzbekistan that \
works ONLY with trucks (cargo vehicles: tractor units, dump trucks, flatbeds, vans, reefers, special vehicles, light \
trucks — brands like Isuzu, MAN, KAMAZ, Shacman, Howo, Mercedes-Benz, Volvo, Scania, DAF, FAW, Foton). You are \
chatting with a customer inside a Telegram bot.

If the customer asks about a passenger car, politely explain that NAJOT SERVIS services only trucks.

Your job is to help the customer describe their truck problem clearly so a mechanic can prepare, and then hand them \
over to booking. Collect, through a short friendly conversation:
- brand, model and year of the truck;
- the symptoms (what exactly happens: sounds, smoke colour, warning lights or error codes, air-pressure behaviour, \
loss of power, leaks);
- when the problem appeared and whether it is constant or occasional (cold/hot engine, loaded/empty);
- any additional signs, and whether the truck can still drive to the service or is stuck on the road.

Ask about one or two missing things at a time; keep replies short (2-5 sentences, Telegram style, a relevant emoji is \
fine). Do not repeat questions that were already answered.

Safety and honesty rules:
- You are not a mechanic and cannot inspect the car. Never state a definitive diagnosis or a guaranteed cause; at most \
mention possibilities in neutral terms ("this could have several causes; the mechanic will check").
- Never give repair instructions that could be dangerous (fuel system, brakes, airbags, high-voltage/EV systems, \
working under a raised car, opening a hot radiator, etc.).
- Never suggest tampering with air-brake lines or spring brake chambers, wheel/rim assemblies under pressure, or \
working under a truck that is not securely supported.
- If symptoms suggest a risk (air-pressure warning or brakes not working, steering problems, smell of fuel, smoke or \
fire, severe overheating, oil-pressure warning, wheel or trailer-coupling problems), clearly advise not to drive the \
truck, to park it safely with hazard lights and warning triangle, and to use the 🆘 button or call the service.
- Do not quote prices or repair times; say the service will confirm them.
- Stay on the topic of the truck and the service.

Output format: always fill every JSON field. Put your message to the customer in `reply`. Fill brand, model, year, \
symptoms, since and extra with what is known so far (empty string if unknown). `symptoms` should be a concise, neutral \
summary for the mechanic in the customer's language. Set `ready` to true once brand, model, year and a reasonably \
clear description of symptoms are known — then in `reply` briefly summarize and suggest creating a request with the \
button below."""

SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "brand": {"type": "string"},
        "model": {"type": "string"},
        "year": {"type": "string"},
        "symptoms": {"type": "string"},
        "since": {"type": "string"},
        "extra": {"type": "string"},
        "ready": {"type": "boolean"},
    },
    "required": ["reply", "brand", "model", "year", "symptoms", "since", "extra", "ready"],
    "additionalProperties": False,
}

FALLBACK_STEPS = ["brand", "model", "year", "symptoms", "since", "extra"]


class AI(StatesGroup):
    chat = State()
    simple = State()


def ai_kb(lang: str, ready: bool, has_form: bool = False):
    rows = []
    if ready:
        rows.append([btn(t(lang, "btn_ai_book"), "ai:book")])
    if has_form:
        rows.append([btn(t(lang, "btn_to_form"), "ai:back")])
    rows.append([btn(t(lang, "btn_ai_end"), "home")])
    return markup(*rows)


async def _has_form(state: FSMContext) -> bool:
    return bool((await state.get_data()).get("form"))


async def ask_claude(history: list[dict], lang: str) -> dict:
    system = [
        {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": f"Always answer in {LANG_NAMES.get(lang, 'Russian')}."},
    ]
    params = dict(model=config.ai_model, max_tokens=4000, system=system, messages=history,
                  output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}})
    try:
        resp = await _client.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **params)
    except (TypeError, anthropic.BadRequestError) as e:
        log.info("fallbacks not available (%s); plain request", type(e).__name__)
        resp = await _client.messages.create(**params)
    if resp.stop_reason == "refusal":
        raise RuntimeError("refusal")
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


def compose_problem(f: dict, lang: str) -> str:
    parts = [f.get("symptoms", "").strip()]
    if f.get("since", "").strip():
        parts.append(f"{t(lang, 'ai_lbl_since')}: {f['since'].strip()}")
    extra = f.get("extra", "").strip()
    if extra and extra.lower() not in ("нет", "no", "yo'q", "yo‘q", "-"):
        parts.append(f"{t(lang, 'ai_lbl_extra')}: {extra}")
    return ". ".join(p for p in parts if p)[:1000]


# ---------------- entry ----------------

@router.callback_query(F.data == "ai:start")
async def cb_start(cb: CallbackQuery, state: FSMContext, lang: str):
    await cb.answer()
    prev = await state.get_data()
    form = prev if prev.get("idem") else prev.get("form")  # opened from the request form: keep it
    await state.clear()
    await state.set_state(AI.chat if _client else AI.simple)
    await state.update_data(ai_hist=[], ai_fields={}, ai_step=0, form=form)
    back = [btn(t(lang, "btn_to_form"), "ai:back")] if form else None
    await show(cb, t(lang, "ai_intro"), markup(back, nav(lang)))


@router.callback_query(F.data == "ai:back")
async def cb_back_to_form(cb: CallbackQuery, state: FSMContext, lang: str):
    form = (await state.get_data()).get("form")
    await cb.answer()
    if not form:
        return await show(cb, t(lang, "bk_expired"), markup(nav(lang)))
    await state.set_data(form)
    await render_form(cb, state, lang)


async def _handle(message: Message, state: FSMContext, lang: str, text: str):
    if await state.get_state() == AI.simple.state:
        return await _simple(message, state, lang, text)
    data = await state.get_data()
    hist: list[dict] = data.get("ai_hist", [])
    hist.append({"role": "user", "content": text[:1500]})
    hist = hist[-MAX_TURNS:]
    while hist and hist[0]["role"] != "user":
        hist.pop(0)
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        out = await ask_claude(hist, lang)
    except Exception:
        log.exception("AI request failed")
        await message.answer(t(lang, "ai_unavailable"))
        await state.set_state(AI.simple)
        await state.update_data(ai_fields={"symptoms": text}, ai_step=0)
        return await _simple_ask(message, state, lang)
    hist.append({"role": "assistant", "content": json.dumps(out, ensure_ascii=False)})
    fields = {k: out.get(k, "") for k in ("brand", "model", "year", "symptoms", "since", "extra")}
    ready = bool(out.get("ready")) and bool(fields["symptoms"])
    await state.update_data(ai_hist=hist, ai_fields=fields)
    reply = h(out.get("reply", ""))
    if ready:
        reply += t(lang, "ai_ready")
    await message.answer(reply, reply_markup=ai_kb(lang, ready, await _has_form(state)))


@router.message(AI.chat, F.text)
@router.message(AI.simple, F.text)
async def msg_ai(message: Message, state: FSMContext, lang: str):
    await _handle(message, state, lang, message.text.strip())


# ---------------- fallback questionnaire ----------------

async def _simple_ask(message: Message, state: FSMContext, lang: str):
    data = await state.get_data()
    fields, step = data.get("ai_fields", {}), data.get("ai_step", 0)
    while step < len(FALLBACK_STEPS) and fields.get(FALLBACK_STEPS[step]):
        step += 1
    await state.update_data(ai_step=step)
    if step >= len(FALLBACK_STEPS):
        car = f"{h(fields.get('brand'))} {h(fields.get('model'))}"
        summary = t(lang, "ai_summary", truck=car, year=h(fields.get("year")), problem=h(compose_problem(fields, lang)))
        return await message.answer(summary + t(lang, "ai_ready"), reply_markup=ai_kb(lang, True, await _has_form(state)))
    await message.answer(t(lang, "ai_q_" + FALLBACK_STEPS[step]), reply_markup=ai_kb(lang, False, await _has_form(state)))


async def _simple(message: Message, state: FSMContext, lang: str, text: str):
    data = await state.get_data()
    fields, step = data.get("ai_fields", {}), data.get("ai_step", 0)
    if not fields and step == 0 and len(text) > 15:
        # first free-form message is most likely the symptom description
        fields["symptoms"] = text
    elif step < len(FALLBACK_STEPS):
        key = FALLBACK_STEPS[step]
        if key == "year" and parse_year(text) is None:
            return await message.answer(t(lang, "bk_bad_year", max=now().year + 1))
        fields[key] = text[:500]
    await state.update_data(ai_fields=fields)
    await _simple_ask(message, state, lang)


# ---------------- hand-off to booking ----------------

@router.callback_query(F.data == "ai:book")
async def cb_book(cb: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, lang: str):
    data = await state.get_data()
    f = data.get("ai_fields") or {}
    await cb.answer()
    year = parse_year(re.sub(r"\D", "", f.get("year", ""))[:4])
    prefill = {"brand": f.get("brand", "").strip()[:40] or None, "model": f.get("model", "").strip()[:40] or None,
               "year": year, "car_desc": str(year) if year else None,
               "problem": compose_problem(f, lang) or None, "source": "ai"}
    prefill = {k: v for k, v in prefill.items() if v}
    form = data.get("form")
    if form and form.get("idem"):
        # the client opened AI from the form: keep what was typed there, fill only the empty fields
        for k, v in prefill.items():
            if not form.get(k):
                form[k] = v
        await state.set_data(form)
        return await render_form(cb, state, lang)
    await start_booking(cb, state, session, user, lang, prefill=prefill)


# ---------------- free text outside of any scenario ----------------

@router.message(StateFilter(None), F.text & ~F.text.startswith("/"))
async def msg_free_text(message: Message, state: FSMContext, user: User, lang: str):
    """A client just writes «Машина не заводится» — start the AI assistant with that message."""
    if user.role != "client":
        return await message.answer(t(lang, "use_buttons"), reply_markup=markup(nav(lang)))
    await state.set_state(AI.chat if _client else AI.simple)
    await state.update_data(ai_hist=[], ai_fields={}, ai_step=0)
    await _handle(message, state, lang, message.text.strip())
