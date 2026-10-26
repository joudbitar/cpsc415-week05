# Spec

## Intent
[`intent/receipts.md`](intent/receipts.md).

## Components

### reader
- **What it does:** sends one receipt image to a vision model, takes the JSON out of the reply, and turns it into a `Receipt` (merchant, date, items, subtotal, discount, tax, total). It does no arithmetic.
- **Language:** Python 3.11+. **Why:** Week 4 was Python with only the standard library, and `urllib` plus `base64` cover one HTTPS call with an image. Java would need an HTTP client and a JSON library for the same call. The trade-off is no static types on the parsed JSON, so the parser checks types by hand.
- **Model:** `minimax/minimax-m3` (default) compared with `xiaomi/mimo-v2.6-flash`, both through OpenRouter, both accept images. **Why:** minimax is the class model and reads the faded date only with reasoning on. mimo is the cheaper flash model, but on 2026-10-19 it started spending its whole output budget on hidden reasoning, so it needs `"reasoning": {"enabled": false}`. Reasoning is a per-model setting: a table in the code (minimax on, mimo off), overridable with `CHAT_REASONING=on|off`. Results for both models on the five receipts are in `CHECKS.md`.
- **Interfaces:** `read_receipt(path) -> ReadResult` (the receipt or an error, plus tokens in and out and `finish_reason`). `parse_reply(text) -> Receipt` raises `ReadError`. Environment: `OPENROUTER_API_KEY` (required for a read), `CHAT_MODEL` (default `minimax/minimax-m3`), `CHAT_REASONING`.
- **Dependencies:** none at run time (standard library only).

### checker
- **What it does:** takes a `Receipt` and returns a list of problems, each with what was checked, the expected value, the printed value and the difference. An empty list means the receipt adds up. No model, no network.
- **Language:** Python, same as the reader. **Why:** same package, and the checker is pure functions that are easy to test.
- **Model:** none. The checker exists so that the program does not trust the model's arithmetic.
- **Interfaces:** `check(receipt) -> list[Problem]`.
- **Dependencies:** none.

### Dependencies (development only)
- `pytest`: the test runner. Without it we would write our own discovery, skip markers and assertion messages.
- `ruff`: the linter the lab asks for (`ruff check .`).

## Behavior
1. The reader sends the image as a base64 data URL content part next to a text prompt that asks for one JSON object with the fields above and nothing else.
2. A reply that is not JSON is a failed read (`ReadError` with the first 200 characters of the reply), never a crash.
3. A reply with JSON inside prose or a ```json fence is accepted: the parser takes the outermost `{...}`.
4. An empty reply with `finish_reason: length` is a failed read whose message says the model ran out of output tokens (reasoning budget).
5. Money values are parsed to cents (`Decimal`, rounded to 0.01). Strings such as `"$4.36"` are accepted. A missing subtotal, discount or tax is `null`. A missing total is a failed read.
6. A discount is stored as a positive amount, whatever sign the model or the receipt used.
7. Each item has a name, a quantity (default 1) and a unit price. If the model gives only a line total, the unit price is the line total divided by the quantity.
8. The date is ISO `YYYY-MM-DD`. A two-digit year counts as printed (`10/04/26` is 2026-10-04). When no year is printed at all (`Oct 3`), the date is `null`. The prompt says so, and the parser also turns any date the model did not give as a full ISO date into `null`.
9. The checker compares the sum of quantity times unit price over all items with the subtotal. When there is no subtotal, it compares the items with the total, minus tax, plus discount.
10. The checker compares subtotal minus discount plus tax with the total.
11. A receipt whose numbers do not add up is reported with the check's name, the expected value, the printed value and the difference. Tolerance is one cent per item for rounding of unit prices (for example 3 × 0.89 printed as 2.67).
12. The command line prints the JSON and then either `OK: the numbers add up` or one line per problem, and exits 0 on a successful read even with problems, 1 on a failed read.
13. The eval reads every image in a folder (`images/` by default, `RECEIPT_DIR` to change it) once, and for each image compares merchant, date, number of items and total with `expected.json`, and checks that the checker reports no problems. Merchant matching ignores case, punctuation and word order ("Bake Sale - CS Club" matches "CS Club Bake Sale").

## Failure handling
- No `OPENROUTER_API_KEY`: the command line exits with a message naming the variable. Tests that call a model are skipped.
- HTTP error or timeout (60 s): a failed read with the status and the message from OpenRouter.
- A refusal or a description in prose with no JSON: a failed read (behavior 2).
- A hallucinated number: the reader cannot know, so the checker catches it when it breaks the arithmetic. A misread that still adds up (for example a wrong merchant) only the eval catches.

## Cost estimate
One call per receipt: about 700 to 1,000 tokens in (the image is most of it) and 300 to 600 out with reasoning. At OpenRouter prices for both models that is well under $0.01 per receipt. Ten receipts a week for a semester is a few hundred calls, under a dollar.

## Out of scope
From the intent: fixing misread numbers, multi-receipt photos, PDFs, categories, a front end. The design also rules out a JSON-schema `response_format`, because the lab compares raw replies and behavior 2 has to hold anyway.
