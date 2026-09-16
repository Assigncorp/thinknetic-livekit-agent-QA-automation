"""
Loader for config/testbed.config.json and resources/generated/*.

Same data the TypeScript suite reads, so a scenario that passes catalogue
validation here is the same scenario the browser suite will run.
"""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "testbed.config.json"


@lru_cache(maxsize=1)
def config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _generated(name: str) -> dict[str, Any]:
    path = ROOT / config()["resources"]["generatedDir"] / name
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing - run `make resources`")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def serial_index() -> dict[str, Any]:
    return _generated("serial-index.json")


@lru_cache(maxsize=1)
def scenario_pools() -> dict[str, Any]:
    return _generated("scenarios.json")


def knowledge_bases(serial_routed_only: bool = False) -> list[dict[str, Any]]:
    kbs = [k for k in config()["knowledgeBases"] if k.get("enabled")]
    if serial_routed_only:
        kbs = [k for k in kbs if k.get("controller") and k.get("hopperType")]
    return kbs


def kb_path(kb: dict[str, Any]) -> Path:
    return ROOT / config()["resources"]["kbDir"] / kb["file"]


def scenarios_for(kb_id: str) -> list[dict[str, Any]]:
    return scenario_pools()["pools"].get(kb_id, [])


def all_scenarios() -> list[dict[str, Any]]:
    return [s for pool in scenario_pools()["pools"].values() for s in pool]


def serials_for(kb_id: str) -> list[dict[str, Any]]:
    return [s for s in serial_index()["serials"] if s["kbId"] == kb_id]


def sample_scenarios(n: int, seed: int = 7) -> list[dict[str, Any]]:
    """A stable sample, for tests that should not iterate all 200+ scenarios."""
    pool = all_scenarios()
    return random.Random(seed).sample(pool, min(n, len(pool)))
