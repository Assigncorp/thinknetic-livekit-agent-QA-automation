"""
Fixtures for the judge suite.

The session recorder writes report/data/judge-scores.json on the way out whether
anything passed, failed or scored at all. That is the whole mechanism behind
report-only mode: with judge.requireScoreGate off a low score fails nothing, so
a score that is not written down did not happen.
"""


from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # no __pycache__ in the project, even when run from an IDE

import random
from pathlib import Path
from typing import Any

import pytest

from src import scorer, testbed
from src.report import Recorder
from src.transcript import Transcript, load_recordings

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def judge_config() -> dict[str, Any]:
    return testbed.judge_config()


@pytest.fixture(scope="session")
def recorder(judge_config: dict[str, Any]):
    rec = Recorder(judge_config["reportPath"], judge_config["model"])
    yield rec
    path = rec.write()
    if path:
        summary = rec.summary()
        print(f"\n[judge] scored {summary['callsScored']} call(s), "
              f"{summary['callsNotScored']} not scored")
        if summary["meanByRubric"]:
            for rubric_id, mean in summary["meanByRubric"].items():
                threshold = testbed.rubric_by_id(rubric_id)["threshold"]
                flag = " <- under threshold" if mean < threshold else ""
                print(f"[judge]   {rubric_id:<18} {mean:.3f}  (threshold {threshold}){flag}")
        print(f"[judge] wrote {path.relative_to(ROOT)}")


@pytest.fixture(scope="session")
def recordings() -> list[Transcript]:
    calls = load_recordings()
    if not calls:
        pytest.skip(
            "no recorded calls in judge/recordings/ - capture one with "
            "`make judge-record`, or see judge/recordings/README.md"
        )
    return calls


@pytest.fixture(scope="session")
def judge_available() -> None:
    """Skip, loudly, when the judge cannot run. Never pass instead."""
    ok, why = scorer.available()
    if not ok:
        pytest.skip(f"judge unavailable: {why}")


@pytest.fixture(scope="session")
def rng() -> random.Random:
    """Seeded from scenarioSelection.seed so a run is reproducible when it
    needs to be, and varied when it does not."""
    seed = testbed.config()["scenarioSelection"].get("seed")
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Testing type: positive / negative / edge / security / nonfunctional.
# One rule file for every suite (config/test-types.json); each test gets exactly
# one type as a marker, so `pytest -m negative` works here and
# `make test-type TYPE=negative` works across all suites. Same code in the
# api/, judge/ and sdk/ conftests - independent suites, deliberately no shared
# import. TEST_TYPES_STRICT=1 (make check-types) fails on an unclassified test.
# ---------------------------------------------------------------------------


def _test_type_rules(suite: str) -> list[tuple[str, str]]:
    import json as _json
    from pathlib import Path as _Path

    path = _Path(__file__).resolve().parents[2] / "config" / "test-types.json"
    return [tuple(rule) for rule in _json.loads(path.read_text(encoding="utf-8"))["rules"][suite]]


def pytest_collection_modifyitems(config, items):
    import fnmatch as _fnmatch
    import os as _os

    import pytest as _pytest

    rules = _test_type_rules('judge')
    unclassified = []
    for item in items:
        test_id = item.nodeid.split("[", 1)[0]
        kind = next((t for pattern, t in rules if _fnmatch.fnmatchcase(test_id, pattern)), None)
        if kind is None:
            unclassified.append(test_id)
            continue
        item.add_marker(getattr(_pytest.mark, kind))
        item.user_properties.append(("type", kind))  # into the JUnit XML -> report/index.html
    if unclassified and _os.getenv("TEST_TYPES_STRICT"):
        raise _pytest.UsageError(
            "tests with no testing type in config/test-types.json:\n  " + "\n  ".join(sorted(set(unclassified)))
        )


# ---------------------------------------------------------------------------
# Every run ends with report/index.html, make or not - tools/report_hook.py.
# ---------------------------------------------------------------------------
import importlib.util as _ilu  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_spec = _ilu.spec_from_file_location("report_hook", _Path(__file__).resolve().parents[2] / "tools" / "report_hook.py")
report_hook = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(report_hook)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    report_hook.default_junit(config, "judge")


def pytest_unconfigure(config):
    report_hook.build(config)
