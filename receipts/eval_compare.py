"""How the eval compares a read with expected.json."""
import re


def _words(name: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", name.lower()))


def same_merchant(read: str, expected: str) -> bool:
    """Spec 13: ignore case, punctuation and word order."""
    return _words(read) == _words(expected)
