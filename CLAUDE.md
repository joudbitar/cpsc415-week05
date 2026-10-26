# Project conventions

<!-- The agent reads this at the start of every session. Keep it short and current.
     Graded: does it reflect how the team actually works? -->

## What this repository is
A command-line receipt reader: a vision model turns a receipt photo into JSON, and a plain-code checker reports when the numbers do not add up. See [`spec.md`](spec.md).

## Commands
```
.venv/bin/pytest -m "not needs_key"            # no-key tests
.venv/bin/pytest                               # all tests (eval needs OPENROUTER_API_KEY)
.venv/bin/python receipt.py images/receipt-01.png
.venv/bin/ruff check .
```

## Conventions
- Language and style rules the agent must follow.
- Where tests live and how they are named.
- Branch and PR naming.

## Working rules

For an introductory lab, follow its explicitly assigned stages; the full chain below applies to major projects. Week 1 uses its own minimal repository.

- Write or update `intent/` and `spec.md` before code. Get `plan.md` approved before implementing.
- One feature per branch and pull request. Never push to `main` directly.
- Never commit `.env` or `.claude/settings.local.json`.
- This is the Week 5 introductory lab. Stages assigned: intent, spec, plan,
  and tests. No branches or pull requests yet. Commit to main.
- Libraries and build tools are allowed. Name each dependency in spec.md
  under Dependencies, with the reason, before installing it; a hook blocks
  installs that spec.md does not list.
- images/ and images/expected.json are the answer key. Never edit them. If
  a test disagrees with the key, say so and stop.
- Tests live in tests/ (Python) or src/test (Java). Tests that call a model
  are marked and are skipped when no API key is set.

## Common mistakes
Things the agent got wrong before and must not repeat. Add to this list as they happen.
- An example date in the prompt that matched a real receipt (10/04/26) leaked into another receipt's answer. Prompt examples use values that appear on no receipt.
