"""
Config and resource loader for the judge package.

Deliberately a sibling of api/src/utils/testbed.py rather than an import of
it. The two packages are independent uv projects that share exactly two
things - config/testbed.config.json and the repo-root .env - and that seam is
what lets the API suite land in a different pipeline later without dragging
this one with it. Reaching across it for a fifty-line loader would be the
first thing to break that.

What is NOT duplicated is the data. Both loaders read the same file, so a
knowledge base renamed in one place is renamed for both.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]

load_dotenv(ROOT / ".env")

# The python.org macOS installer ships an OpenSSL with no CA bundle until someone
# runs its "Install Certificates.command", and the symptom is CERTIFICATE_VERIFY_FAILED
# against livekit.cloud - whose chain is fine, curl accepts it. Point OpenSSL at
# certifi's bundle unless the caller already chose one (a corporate CA, say).
try:
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

DEFAULT_CONFIG = "config/testbed.config.json"


def config_path() -> Path:
    return ROOT / os.getenv("TESTBED_CONFIG", DEFAULT_CONFIG)


@lru_cache(maxsize=1)
def config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. TESTBED_CONFIG is "
            f"{os.getenv('TESTBED_CONFIG', DEFAULT_CONFIG)!r} - check .env"
        )
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def judge_config() -> dict[str, Any]:
    cfg = config()
    if "judge" not in cfg:
        raise KeyError(
            f"{config_path()} has no `judge` block. The judge suite is entirely "
            f"config-driven; without it there are no rubrics to score against. "
            f"Copy the block from config/testbed.config.json."
        )
    return cfg["judge"]


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


def kb_by_id(kb_id: str) -> dict[str, Any]:
    for kb in knowledge_bases():
        if kb["id"] == kb_id:
            return kb
    raise KeyError(f"no enabled knowledge base with id {kb_id!r}")


def kb_path(kb: dict[str, Any]) -> Path:
    return ROOT / config()["resources"]["kbDir"] / kb["file"]


def all_scenarios() -> list[dict[str, Any]]:
    return [s for pool in scenario_pools()["pools"].values() for s in pool]


def scenario_by_id(scenario_id: str) -> dict[str, Any]:
    for scenario in all_scenarios():
        if scenario["id"] == scenario_id:
            return scenario
    raise KeyError(f"no scenario with id {scenario_id!r}")


def serials_for(kb_id: str) -> list[dict[str, Any]]:
    return [s for s in serial_index()["serials"] if s["kbId"] == kb_id]


def rubrics() -> list[dict[str, Any]]:
    return judge_config()["rubrics"]


def rubric_by_id(rubric_id: str) -> dict[str, Any]:
    for rubric in rubrics():
        if rubric["id"] == rubric_id:
            return rubric
    raise KeyError(f"no rubric with id {rubric_id!r}")
