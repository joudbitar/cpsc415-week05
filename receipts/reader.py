"""The reader: one vision call per image, and the parser that turns the reply into a Receipt."""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date as Date
from decimal import Decimal
from pathlib import Path

from .model import CENT, Item, ReadError, Receipt, money


def _extract_object(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ReadError(f"reply is not JSON: {text[:200]!r}")
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise ReadError(f"reply is not JSON ({e.msg}): {text[:200]!r}") from None
    if not isinstance(data, dict):
        raise ReadError(f"reply is not a JSON object: {text[:200]!r}")
    return data


def _iso_date(value) -> str | None:
    """Spec 8: only a full YYYY-MM-DD date counts; anything else (no year printed) is null."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return None
    try:
        return Date.fromisoformat(value.strip()).isoformat()
    except ValueError:
        return None


def _item(raw: dict) -> Item:
    if not isinstance(raw, dict):
        raise ReadError(f"item is not an object: {raw!r}")
    quantity = Decimal(str(raw.get("quantity") or 1))
    unit = money(raw.get("unit_price"))
    if unit is None:
        line = money(raw.get("line_total") or raw.get("price") or raw.get("amount"))
        if line is None:
            raise ReadError(f"item has no price: {raw!r}")
        unit = (line / quantity).quantize(CENT)
    return Item(name=str(raw.get("name", "")).strip(), quantity=quantity, unit_price=unit)


def parse_reply(text: str | None, finish_reason: str | None = None) -> Receipt:
    if not text or not text.strip():
        if finish_reason == "length":
            raise ReadError("empty reply with finish_reason=length: the model ran out of output tokens "
                            "(likely spent on hidden reasoning; try CHAT_REASONING=off)")
        raise ReadError(f"empty reply (finish_reason={finish_reason})")
    data = _extract_object(text)
    total = money(data.get("total"))
    if total is None:
        raise ReadError("reply has no total")
    discount = money(data.get("discount"))
    return Receipt(
        merchant=str(data.get("merchant") or "").strip(),
        date=_iso_date(data.get("date")),
        items=[_item(i) for i in data.get("items") or []],
        subtotal=money(data.get("subtotal")),
        discount=None if discount is None else abs(discount),
        tax=money(data.get("tax")),
        total=total,
    )


# --- the vision call -------------------------------------------------------

URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "minimax/minimax-m3"
# Per-model reasoning (see spec, Model): minimax reads the faded date only with reasoning on;
# mimo spends its whole output budget thinking unless reasoning is off.
REASONING = {"minimax/minimax-m3": True, "xiaomi/mimo-v2.6-flash": False}

PROMPT = """Read this receipt and reply with one JSON object and nothing else:
{"merchant": string, "date": "YYYY-MM-DD" or null,
 "items": [{"name": string, "quantity": number, "unit_price": number}],
 "subtotal": number or null, "discount": number or null, "tax": number or null, "total": number}
Rules:
- merchant is the store name as printed at the top.
- date: only if the year is printed on the receipt. If the year is not printed, use null. Never guess a year.
- one entry per item line; unit_price is the price of ONE unit (for "2 x Blue book @ 1.25 ea  2.50" the
  quantity is 2 and the unit_price is 1.25).
- discount is the amount taken off, as a positive number.
- use null for subtotal, discount or tax when the receipt does not print them.
- copy the numbers as printed. Do not correct the arithmetic."""


@dataclass
class ReadResult:
    receipt: Receipt | None
    error: str | None
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    finish_reason: str | None = None


def _reasoning(model: str) -> bool:
    setting = os.environ.get("CHAT_REASONING", "").lower()
    if setting in ("on", "off"):
        return setting == "on"
    return REASONING.get(model, True)


def read_receipt(path, model: str | None = None) -> ReadResult:
    model = model or os.environ.get("CHAT_MODEL", DEFAULT_MODEL)
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return ReadResult(None, "OPENROUTER_API_KEY is not set", model)
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    image = base64.b64encode(path.read_bytes()).decode()
    body = {
        "model": model,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image}"}},
        ]}],
    }
    if not _reasoning(model):
        body["reasoning"] = {"enabled": False}
    request = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.load(response)
    except urllib.error.HTTPError as e:
        return ReadResult(None, f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}", model)
    except (urllib.error.URLError, TimeoutError) as e:
        return ReadResult(None, f"request failed: {e}", model)

    usage = data.get("usage") or {}
    choice = (data.get("choices") or [{}])[0]
    finish = choice.get("finish_reason")
    result = ReadResult(None, None, model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), finish)
    try:
        result.receipt = parse_reply((choice.get("message") or {}).get("content"), finish)
    except ReadError as e:
        result.error = str(e)
    return result
