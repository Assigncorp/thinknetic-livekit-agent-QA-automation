"""
Fixtures for the LiveKit SDK suite.

One event loop for the whole session (pyproject: asyncio_default_*_loop_scope),
because the LiveKit SDK binds its FFI handles to the loop they were created on
and a module-scoped call fixture outlives any per-test loop.
"""


from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # no __pycache__ in the project, even when run from an IDE

import os
import random
from typing import Any

import pytest

from lkqa import cases
from lkqa.bridge import ROOT, testbed
from lkqa.report import Report
from lkqa.session import credentials_available


@pytest.fixture(scope="session")
def report():
    rep = Report()
    yield rep
    path = rep.write()
    if path:
        print(f"\n[lkqa] {len(rep.entries)} measurement(s), {len(rep.findings)} finding(s) -> {path.relative_to(ROOT)}")
        for f in rep.findings:
            print(f"[lkqa]   FINDING {f['id']}: {f['summary']}")


@pytest.fixture(scope="session")
def r() -> random.Random:
    return cases.rng()


@pytest.fixture(scope="session")
def admin_available() -> None:
    ok, why = credentials_available()
    if not ok:
        pytest.skip(f"LiveKit server API unavailable: {why}")


@pytest.fixture
async def admin(admin_available):
    from lkqa.admin import Admin

    a = Admin()
    yield a
    await a.close()


def gate(name: str) -> bool:
    return bool(testbed.config()["livekitSdk"]["gates"].get(name, False))


def grounding_runs() -> int:
    return int(os.getenv("GROUNDING_RUNS", testbed.config()["livekitSdk"]["grounding"]["runs"]))


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

    rules = _test_type_rules('sdk')
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
    report_hook.default_junit(config, "sdk")


def pytest_unconfigure(config):
    report_hook.build(config)
