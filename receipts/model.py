"""The receipt data shapes and the helpers that turn model output into them."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")


class ReadError(Exception):
    """The model's reply could not be turned into a receipt."""


@dataclass
class Item:
    name: str
    quantity: Decimal
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price


@dataclass
class Receipt:
    merchant: str
    date: str | None
    items: list[Item] = field(default_factory=list)
    subtotal: Decimal | None = None
    discount: Decimal | None = None
    tax: Decimal | None = None
    total: Decimal = Decimal(0)

    def to_json(self) -> dict:
        def num(d):
            return None if d is None else float(d)
        return {
            "merchant": self.merchant,
            "date": self.date,
            "items": [{"name": i.name, "quantity": num(i.quantity), "unit_price": num(i.unit_price)}
                      for i in self.items],
            "subtotal": num(self.subtotal),
            "discount": num(self.discount),
            "tax": num(self.tax),
            "total": num(self.total),
        }


@dataclass
class Problem:
    check: str
    expected: Decimal
    printed: Decimal

    @property
    def difference(self) -> Decimal:
        return self.printed - self.expected

    def __str__(self) -> str:
        return (f"{self.check}: parts add up to {self.expected:.2f}, receipt says {self.printed:.2f} "
                f"(off by {self.difference:+.2f})")


def money(value) -> Decimal | None:
    """A price from the model, as a number or a string like "$4.36", rounded to cents."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ReadError(f"not a money value: {value!r}")
    text = re.sub(r"[^\d.\-]", "", str(value)) if isinstance(value, str) else str(value)
    try:
        return Decimal(text).quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ReadError(f"not a money value: {value!r}") from None
