"""Read one receipt: python3 receipt.py images/receipt-02.png"""
import json
import sys

from receipts.checker import check
from receipts.reader import read_receipt


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    result = read_receipt(sys.argv[1])
    if result.error:
        print(f"failed read ({result.model}): {result.error}", file=sys.stderr)
        return 1
    print(json.dumps(result.receipt.to_json(), indent=2))
    problems = check(result.receipt)
    if not problems:
        print("OK: the numbers add up")
    for p in problems:
        print(f"PROBLEM: {p}")
    print(f"[{result.model}, {result.tokens_in} tokens in, {result.tokens_out} out]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
