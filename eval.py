"""Eval table: one read per image in RECEIPT_DIR (default images/), compared with its expected.json.

    python3 eval.py                         # class model
    CHAT_MODEL=xiaomi/mimo-v2.6-flash python3 eval.py
    RECEIPT_DIR=my-receipts python3 eval.py
"""
import json
import os
import sys
from pathlib import Path

from receipts.checker import check
from receipts.eval_compare import same_merchant
from receipts.reader import read_receipt


def main() -> int:
    folder = Path(os.environ.get("RECEIPT_DIR", "images"))
    expected = json.loads((folder / "expected.json").read_text())
    print("| Receipt | Merchant | Date | Items | Total | Checker | Tokens in/out | Notes |")
    print("|---|---|---|---|---|---|---|---|")
    passed = model = 0
    for name in sorted(expected):
        want = expected[name]
        r = read_receipt(folder / name)
        model = r.model
        if r.error:
            print(f"| {name} | – | – | – | – | – | {r.tokens_in}/{r.tokens_out} | failed read: {r.error[:80]} |")
            continue
        got = r.receipt
        problems = check(got)
        cells = {
            "merchant": same_merchant(got.merchant, want["merchant"]),
            "date": got.date == want["date"],
            "items": len(got.items) == want["items"],
            "total": abs(float(got.total) - want["total"]) < 0.001,
            "checker": not problems,
        }
        notes = []
        if not cells["merchant"]:
            notes.append(f"merchant {got.merchant!r}")
        if not cells["date"]:
            notes.append(f"date {got.date}")
        if not cells["items"]:
            notes.append(f"{len(got.items)} items")
        if not cells["total"]:
            notes.append(f"total {got.total}")
        notes += [str(p) for p in problems]
        passed += all(cells.values())
        mark = {True: "pass", False: "FAIL"}
        print(f"| {name} | {mark[cells['merchant']]} | {mark[cells['date']]} | {mark[cells['items']]} | "
              f"{mark[cells['total']]} | {mark[cells['checker']]} | {r.tokens_in}/{r.tokens_out} | "
              f"{'; '.join(notes)} |")
    print(f"\n{model}: {passed}/{len(expected)} receipts fully correct")
    return 0 if passed == len(expected) else 1


if __name__ == "__main__":
    sys.exit(main())
