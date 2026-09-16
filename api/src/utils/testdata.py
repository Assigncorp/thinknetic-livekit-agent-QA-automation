"""Loads the shared, language-neutral fixtures in /testdata."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

TESTDATA_DIR = Path(__file__).resolve().parents[3] / "testdata"


@lru_cache(maxsize=None)
def _load(name: str) -> dict[str, Any]:
    return json.loads((TESTDATA_DIR / name).read_text(encoding="utf-8"))


def products() -> list[dict[str, Any]]:
    return _load("products.json")["products"]


def invalid_products() -> list[dict[str, Any]]:
    return _load("products.json")["invalidProducts"]
