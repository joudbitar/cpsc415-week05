"""Key tests: the eval. One model call per image, compared with expected.json in the same folder.

RECEIPT_DIR picks the folder (default images/). CHAT_MODEL picks the model.
"""
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / os.environ.get("RECEIPT_DIR", "images")
EXPECTED = json.loads((FOLDER / "expected.json").read_text())

pytestmark = pytest.mark.needs_key


@pytest.fixture(scope="module")
def reads():
    from receipts.reader import read_receipt
    cache = {}

    def get(name):
        if name not in cache:
            cache[name] = read_receipt(FOLDER / name)
        return cache[name]
    return get


def ok(reads, name):
    result = reads(name)
    assert result.error is None, result.error
    return result.receipt


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_merchant(reads, name):
    from receipts.eval_compare import same_merchant
    assert same_merchant(ok(reads, name).merchant, EXPECTED[name]["merchant"])


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_date(reads, name):
    assert ok(reads, name).date == EXPECTED[name]["date"]


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_item_count(reads, name):
    assert len(ok(reads, name).items) == EXPECTED[name]["items"]


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_total(reads, name):
    assert float(ok(reads, name).total) == pytest.approx(EXPECTED[name]["total"], abs=0.001)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_checker_finds_no_problems(reads, name):
    from receipts.checker import check
    problems = check(ok(reads, name))
    assert problems == [], "; ".join(map(str, problems))
