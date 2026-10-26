"""No-key tests: the checker on receipts written by hand.

expected = what the parts add up to, printed = the figure on the receipt,
difference = printed - expected.
"""
from decimal import Decimal as D

from receipts.checker import check
from receipts.model import Item, Receipt


def receipt(items, subtotal, total, discount=None, tax=None):
    return Receipt(merchant="Test", date=None,
                   items=[Item(name, D(q), D(p)) for name, q, p in items],
                   subtotal=None if subtotal is None else D(subtotal),
                   discount=None if discount is None else D(discount),
                   tax=None if tax is None else D(tax),
                   total=D(total))


def test_hardware_receipt_adds_up():
    r = receipt([("Duct tape", 1, "6.49"), ("Hooks", 1, "3.99"), ("Cord", 1, "11.25"), ("AA", 1, "9.79")],
                subtotal="31.52", tax="2.00", total="33.52")
    assert check(r) == []


def test_items_do_not_add_up_to_subtotal():
    r = receipt([("A", 1, "4.75"), ("B", 1, "3.50"), ("C", 1, "3.25")], subtotal="12.50", total="12.50")
    problems = check(r)
    assert len(problems) == 1
    p = problems[0]
    assert p.check == "items vs subtotal"
    assert p.expected == D("11.50")
    assert p.printed == D("12.50")
    assert p.difference == D("1.00")


def test_wrong_total_is_reported_with_the_discrepancy():
    r = receipt([("A", 1, "10.00")], subtotal="10.00", tax="0.64", total="13.96")
    problems = check(r)
    assert [p.check for p in problems] == ["subtotal - discount + tax vs total"]
    assert problems[0].expected == D("10.64")
    assert problems[0].difference == D("3.32")


def test_discount_is_subtracted():
    r = receipt([("Latte", 1, "4.75"), ("Croissant", 1, "3.50"), ("Americano", 1, "3.25")],
                subtotal="11.50", discount="1.15", tax="0.66", total="11.01")
    assert check(r) == []


def test_negative_discount_is_treated_as_the_same_amount():
    r = receipt([("Latte", 1, "4.75"), ("Croissant", 1, "3.50"), ("Americano", 1, "3.25")],
                subtotal="11.50", discount="-1.15", tax="0.66", total="11.01")
    assert check(r) == []


def test_quantity_times_unit_price():
    r = receipt([("Blue book", 2, "1.25"), ("Gel pen", 3, "0.89"), ("Hoodie", 1, "44.00")],
                subtotal="49.17", total="49.17")
    assert check(r) == []


def test_unit_price_mistaken_for_line_total_is_caught():
    r = receipt([("Blue book", 2, "2.50")], subtotal="2.50", total="2.50")
    problems = check(r)
    assert problems[0].check == "items vs subtotal"
    assert problems[0].expected == D("5.00")
    assert problems[0].difference == D("-2.50")


def test_one_cent_per_item_rounding_is_tolerated():
    r = receipt([("Cookie", 3, "0.33")], subtotal="1.00", total="1.00")
    assert check(r) == []


def test_no_subtotal_compares_items_with_total():
    r = receipt([("Brownie", 1, "2.00"), ("Cookies", 3, "1.00"), ("Lemonade", 1, "1.50")],
                subtotal=None, total="6.50")
    assert check(r) == []


def test_no_subtotal_and_items_off():
    r = receipt([("Brownie", 1, "2.00"), ("Lemonade", 1, "1.50")], subtotal=None, total="6.50")
    problems = check(r)
    assert [p.check for p in problems] == ["items vs total - tax + discount"]
    assert problems[0].difference == D("3.00")
