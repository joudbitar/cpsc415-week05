"""The reader: one vision call per image, and the parser that turns the reply into a Receipt."""
from __future__ import annotations

import json
import re
from datetime import date as Date
from decimal import Decimal

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
