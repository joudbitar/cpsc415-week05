# Plan

## Files to create or change
| File | Purpose |
|---|---|
| `receipts/model.py` | `Receipt`, `Item`, `Problem`, `ReadError`, money and date helpers |
| `receipts/checker.py` | `check(receipt)`: behaviors 9 to 11 |
| `receipts/reader.py` | `parse_reply(text)` (behaviors 2 to 8) and `read_receipt(path)` (behavior 1, the HTTP call) |
| `receipt.py` | command line: behavior 12 |
| `eval.py` | runs every image in a folder once and prints the per-receipt table with tokens (behavior 13) |
| `tests/test_checker.py` | no-key tests for the checker |
| `tests/test_parse.py` | no-key tests for the parser on hand-written replies |
| `tests/test_eval.py` | key tests: one model call per image, compared with `expected.json` |
| `tests/conftest.py` | the `needs_key` marker that skips when `OPENROUTER_API_KEY` is unset |
| `requirements-dev.txt` | `pytest`, `ruff` |
| `CHECKS.md`, `README.md` | results and how to run |

## Order of work
1. Dev tools: `.venv` with `pytest` and `ruff` from `requirements-dev.txt`.
2. Checker: write `tests/test_checker.py` (a receipt that adds up, items that miss the subtotal, a wrong total, a discount with either sign, rounding on 3 × 0.89, no subtotal). Run it red. Write `model.py` and `checker.py`. Run it green.
3. Parser: write `tests/test_parse.py` (clean JSON, JSON in prose, JSON in a fence, not JSON, empty reply with `finish_reason: length`, `"$4.36"` strings, negative discount, line total only, date without a year, missing total). Run it red. Write `parse_reply`. Run it green.
4. Reader and eval: write `tests/test_eval.py` with a module-scoped fixture that reads each image once, and one test per field. Run it with no key (all skipped) and with the key (red until `read_receipt` exists). Write `read_receipt`, `receipt.py`, `eval.py`. Run it green on minimax, then on mimo.
5. `ruff check .`, then `CHECKS.md` and `README.md`.

## Risks
- **The model is right and `expected.json` is wrong.** The eval cannot tell. A failing eval test is a question, not an order: compare with the image by eye, and if the key looks wrong, say so and stop. The guard hook blocks edits to `images/`.
- **Discount sign.** The receipt prints `-1.15`. If the parser kept the sign and the checker subtracted it, the total check would be off by 2.30. Behavior 6 fixes the sign at parse time and step 2 tests both signs.
- **Line total vs unit price.** "2 x Blue book @ 1.25 ea 2.50" can come back as unit price 2.50 with quantity 2. The checker then reports items 2.50 too high. That is a real misread, and the checker is supposed to catch it, not hide it.
- **Reasoning budget.** mimo returns empty content with `finish_reason: length` when reasoning is on. Step 4 would show five failed reads, and behavior 4 makes the message say why.
- **Cost and speed.** If the eval called the model once per test, five fields × five images is 25 calls. The fixture caches one read per image.
- **Blast radius.** The checker and the parser have no network, so a bug there shows in the no-key tests. A bug in `read_receipt` only shows in the key tests.

## Proof
- **No key needed** (`pytest -m "not needs_key"`): the checker tests prove the arithmetic, the sign rule and the tolerance on numbers I wrote by hand. The parser tests prove that bad replies are failed reads, not crashes, and that dates without a year become `null`. Together they prove the code is correct for any reply. They do not prove a model can read a receipt.
- **Key needed** (`pytest -m needs_key`, or `python3 eval.py`): one call per image in `images/`, compared with `images/expected.json` on merchant, date, item count and total, plus "the checker found no problems". This proves the models read these five receipts. It compares against the key, so if the key is wrong it fails a correct model; that case is in Risks.
- Lint: `ruff check .` with the findings recorded in `CHECKS.md`.

## Subagents and parallel work
None. The steps depend on each other in order.

**Approved by:** Joud Bitar, 2026-10-26
