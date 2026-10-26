# Intent: receipts to data

## Goal
A command-line program takes one photo of a paper receipt, asks a vision model to turn it into JSON (merchant, date, items with quantity and unit price, subtotal, discount, tax, total), and then checks in plain code that the numbers add up. It reports what does not add up. It never fixes the numbers.

## Who it is for
Me, as a student who keeps receipts from the dining hall, the bookstore and the pharmacy. Today I type the totals into my budget by hand, or I don't do it at all.

## Constraints
- Python, so it runs with what is already on my laptop.
- Models through OpenRouter with the key in `OPENROUTER_API_KEY`. The key is never in the repo.
- Two models compared: the class model `minimax/minimax-m3` and `xiaomi/mimo-v2.6-flash`.
- One model call per image. Well under a cent per receipt.
- Due Monday, October 26, 2026, 1:30 PM.

## Not in scope
- Fixing or guessing numbers the model misread.
- Multi-page receipts, PDFs, or more than one receipt in a photo.
- Currency conversion, categories, or writing into a budget app.
- A web front end.

## Success looks like
1. `python3 receipt.py images/receipt-02.png` prints JSON with Trinity Bookstore, 2026-09-29, six items and a total of 73.00, and says the numbers add up.
2. A receipt whose items do not add up to the subtotal is reported with the expected value, the printed value and the difference.
3. The bake-sale receipt, which prints "Oct 3" with no year, comes back with `date: null` instead of a guessed year.

## Open questions
- Is a discount stored as a negative number (as printed) or a positive amount that gets subtracted? Settled in the spec: a positive amount, and the checker accepts either sign.

**Approved by:** Joud Bitar, 2026-10-26
