import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_key: calls a model; skipped when OPENROUTER_API_KEY is not set")


def pytest_collection_modifyitems(config, items):
    if os.environ.get("OPENROUTER_API_KEY"):
        return
    skip = pytest.mark.skip(reason="OPENROUTER_API_KEY is not set")
    for item in items:
        if "needs_key" in item.keywords:
            item.add_marker(skip)
