"""No-key tests: turning a model's reply into a Receipt."""
from decimal import Decimal as D

import pytest

from receipts.model import ReadError
from receipts.reader import parse_reply

CLEAN = """{"merchant": "Long Walk Coffee", "date": "2026-10-06",
 "items": [{"name": "Latte 12oz", "quantity": 1, "unit_price": 4.75},
           {"name": "Croissant", "quantity": 1, "unit_price": 3.50},
           {"name": "Americano", "quantity": 1, "unit_price": 3.25}],
 "subtotal": 11.50, "discount": 1.15, "tax": 0.66, "total": 11.01}"""


def test_clean_json():
    r = parse_reply(CLEAN)
    assert r.merchant == "Long Walk Coffee"
    assert r.date == "2026-10-06"
    assert len(r.items) == 3
    assert r.total == D("11.01")
    assert r.discount == D("1.15")


def test_json_inside_prose():
    r = parse_reply("Sure! Here is the receipt as JSON:\n" + CLEAN + "\nLet me know if you need anything else.")
    assert r.total == D("11.01")


def test_json_inside_a_fence():
    r = parse_reply("```json\n" + CLEAN + "\n```")
    assert r.merchant == "Long Walk Coffee"


def test_reply_that_is_not_json_is_a_failed_read():
    with pytest.raises(ReadError, match="not JSON"):
        parse_reply("This is a receipt from Long Walk Coffee for $11.01.")


def test_broken_json_is_a_failed_read():
    with pytest.raises(ReadError):
        parse_reply('{"merchant": "Long Walk Coffee", "total": 11.01,')


def test_empty_reply_cut_off_by_length_names_the_reasoning_budget():
    with pytest.raises(ReadError, match="ran out of output tokens"):
        parse_reply("", finish_reason="length")


def test_money_strings_are_accepted():
    r = parse_reply('{"merchant": "X", "date": null, "items": [{"name": "A", "quantity": 1, "unit_price": "$4.36"}],'
                    ' "subtotal": "$4.36", "tax": "0", "total": "$4.36"}')
    assert r.items[0].unit_price == D("4.36")
    assert r.total == D("4.36")


def test_negative_discount_becomes_a_positive_amount():
    r = parse_reply(CLEAN.replace('"discount": 1.15', '"discount": -1.15'))
    assert r.discount == D("1.15")


def test_line_total_only_gives_unit_price():
    r = parse_reply('{"merchant": "Bake Sale", "date": null,'
                    ' "items": [{"name": "Cookies", "quantity": 3, "line_total": 3.00}], "total": 3.00}')
    assert r.items[0].quantity == D(3)
    assert r.items[0].unit_price == D("1.00")


def test_quantity_defaults_to_one():
    r = parse_reply('{"merchant": "X", "date": null, "items": [{"name": "A", "unit_price": 2}], "total": 2}')
    assert r.items[0].quantity == D(1)


@pytest.mark.parametrize("date", ["Oct 3", "10-03", "--10-03", "2026-13-40", "unknown"])
def test_date_without_a_full_year_is_null(date):
    r = parse_reply(f'{{"merchant": "X", "date": "{date}", "items": [], "total": 0}}')
    assert r.date is None


def test_missing_total_is_a_failed_read():
    with pytest.raises(ReadError, match="total"):
        parse_reply('{"merchant": "X", "date": null, "items": []}')
