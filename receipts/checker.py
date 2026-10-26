"""Plain-code arithmetic checks. No model: this is what keeps us from trusting the model's math."""
from __future__ import annotations

from decimal import Decimal

from .model import CENT, Problem, Receipt


def check(receipt: Receipt) -> list[Problem]:
    problems: list[Problem] = []
    discount = abs(receipt.discount or Decimal(0))      # spec 6: either sign means the same amount off
    tax = receipt.tax or Decimal(0)
    items = sum((i.line_total for i in receipt.items), Decimal(0))
    item_tolerance = CENT * len(receipt.items)            # spec 11: a cent per item for unit-price rounding

    if receipt.subtotal is not None:
        if abs(items - receipt.subtotal) > item_tolerance:
            problems.append(Problem("items vs subtotal", items.quantize(CENT), receipt.subtotal))
        computed = receipt.subtotal - discount + tax
        if computed != receipt.total:
            problems.append(Problem("subtotal - discount + tax vs total", computed, receipt.total))
    else:
        printed = receipt.total - tax + discount
        if abs(items - printed) > item_tolerance:
            problems.append(Problem("items vs total - tax + discount", items.quantize(CENT), printed))
    return problems
