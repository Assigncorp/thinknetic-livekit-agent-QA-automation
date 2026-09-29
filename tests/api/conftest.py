
import sys

sys.dont_write_bytecode = True  # no __pycache__ in the project, even when run from an IDE
import json
import os
from pathlib import Path
from typing import Any

import httpx
import pytest
from dotenv import load_dotenv

from src.clients.product_client import ProductClient
from src.utils import testbed
from src.utils.perf import Recorder
from src.utils.ratelimit import Bucket

ROOT = Path(__file__).resolve().parents[2]

# Both toolchains read the same .env at the repo root.
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("BASE_URL", "https://etnyre-dev.thinknetic.app")
ORG_SLUG = os.getenv("ORG_SLUG", "e")
PRODUCT_SLUG = os.getenv("PRODUCT_SLUG", "chip-spreader")

# Slugs that must NOT exist, for the fail-closed checks.
UNKNOWN_ORG_SLUG = os.getenv("UNKNOWN_ORG_SLUG", "zz-not-an-org")
UNKNOWN_PRODUCT_SLUG = os.getenv("UNKNOWN_PRODUCT_SLUG", "definitely-not-a-real-product")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL.rstrip("/")


# ---------------------------------------------------------------------------
# Rate limiting
#
# The deployment allows 100 requests a minute across the whole API prefix, and
# counts 404s and 304s against it. That is a suite-wide budget, not a per-file
# one, so the bucket is session-scoped and every client feeds it. Tests that
# are about to spend a lot call bucket.reserve() first and are parked until
# there is room, rather than leaving the tests behind them to fail on a 429
# that has nothing to do with what they were checking.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def rate_limit_config() -> dict[str, Any]:
    return testbed.config()["rateLimit"]


@pytest.fixture(scope="session")
def perf_config() -> dict[str, Any]:
    return testbed.config()["apiPerformance"]


@pytest.fixture(scope="session")
def bucket(rate_limit_config: dict[str, Any]) -> Bucket:
    return Bucket(
        window_s=rate_limit_config["windowSeconds"],
        reserve_floor=int(os.getenv("RATE_LIMIT_RESERVE_FLOOR", rate_limit_config["reserveFloor"])),
        headers=rate_limit_config["headers"],
    )


@pytest.fixture(scope="session")
def client(base_url: str, bucket: Bucket):
    with httpx.Client(
        base_url=base_url,
        timeout=20.0,
        follow_redirects=True,
        event_hooks={"response": [bucket.observe]},
    ) as c:
        yield c


@pytest.fixture(scope="session")
def perf_client(base_url: str, bucket: Bucket, product_path: str):
    """
    A client for timing, kept separate from the functional one.

    It does not follow redirects, because a redirect that appears later would
    otherwise show up as latency quietly doubling rather than as a status that
    is no longer 200 - and "the endpoint got slower" is a much harder thing to
    diagnose than "the endpoint moved". Its timeout is deliberately longer than
    the functional client's so a slow response is reported as a breached budget
    with a number attached, not as a timeout with none.
    """
    with httpx.Client(
        base_url=base_url,
        timeout=30.0,
        follow_redirects=False,
        event_hooks={"response": [bucket.observe]},
    ) as c:
        # One request, spent only if something reserves before anything else has
        # been sent, so the throttle knows whether it is looking at a fresh
        # window or the tail of one. See Bucket.set_primer.
        bucket.set_primer(lambda: c.get(product_path))
        yield c


@pytest.fixture(scope="session")
def recorder(base_url: str, perf_config: dict[str, Any], bucket: Bucket):
    """Writes report/data/api-perf.json at the end of the session. Budgets can only
    be re-based from baselines, and there are only baselines if every run
    leaves its numbers behind."""
    rec = Recorder(base_url, perf_config["reportPath"])
    yield rec
    rec.note("rateLimit", bucket.summary())
    path = rec.write()
    if path:
        print(f"\n[perf] wrote {path.relative_to(ROOT)}")


@pytest.fixture(scope="session")
def product_client(client) -> ProductClient:
    return ProductClient(client)


@pytest.fixture(scope="session")
def org_slug() -> str:
    return ORG_SLUG


@pytest.fixture(scope="session")
def product_slug() -> str:
    return PRODUCT_SLUG


@pytest.fixture(scope="session")
def unknown_org_slug() -> str:
    return UNKNOWN_ORG_SLUG


@pytest.fixture(scope="session")
def unknown_product_slug() -> str:
    return UNKNOWN_PRODUCT_SLUG


@pytest.fixture(scope="session")
def product_path(org_slug: str, product_slug: str) -> str:
    return ProductClient.product_path(org_slug, product_slug)


@pytest.fixture(scope="session")
def unknown_product_path(org_slug: str, unknown_product_slug: str) -> str:
    return ProductClient.product_path(org_slug, unknown_product_slug)


@pytest.fixture(scope="session")
def product_schema() -> dict:
    schema = Path(__file__).parent / "src" / "schemas" / "product.schema.json"
    return json.loads(schema.read_text(encoding="utf-8"))


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

    rules = _test_type_rules('api')
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
    report_hook.default_junit(config, "api")


def pytest_unconfigure(config):
    report_hook.build(config)
