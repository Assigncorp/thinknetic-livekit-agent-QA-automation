"""
Latency sampling for the public API.

Deliberately small. This is not a load-testing framework and must not grow
into one: the deployment allows 100 requests a minute across the entire
suite, so the only honest thing to measure at this layer is the latency
distribution of a handful of well-spaced requests. See
docs/api-test-strategy.md for why that ceiling rules k6 out today, and what
would have to change for it to be the right tool.

What this file gives the tests:

  * `measure()` - one timed request, recorded with its status and wire size.
  * `Samples`  - the percentile summary over a set of those.
  * `Recorder` - writes every sample to report/data/api-perf.json so a run's
                 numbers can be compared against the last one instead of
                 against somebody's memory of what "felt slow".

A budget assertion that only ever says "too slow" is a budget assertion that
gets muted, so `assert_within` prints the whole distribution and the budget's
headroom on failure.
"""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Sample:
    """One timed request."""

    label: str
    method: str
    path: str
    status: int
    elapsed_ms: float
    bytes_down: int


def measure(label: str, call: Callable[[], httpx.Response]) -> tuple[Sample, httpx.Response]:
    """
    Time one request on the wall clock rather than trusting the transport.

    `httpx.Response.elapsed` stops when the response is *read*, which for a
    streamed body is not when the caller can use it. A perf number nobody can
    reconcile with a stopwatch is a perf number nobody believes, so this times
    the whole call.
    """
    start = time.perf_counter()
    response = call()
    body = response.content  # force the body; lazily-read bytes are unmeasured time
    elapsed_ms = (time.perf_counter() - start) * 1000
    sample = Sample(
        label=label,
        method=response.request.method,
        path=response.request.url.path,
        status=response.status_code,
        elapsed_ms=round(elapsed_ms, 1),
        bytes_down=len(body),
    )
    return sample, response


def percentile(values: Iterable[float], p: float) -> float:
    """
    Nearest-rank percentile: the smallest observed value at or above the p-th
    position.

    Nearest-rank rather than interpolated on purpose. These runs take tens of
    samples, not thousands, and an interpolated p95 over 20 points reports a
    latency that no request actually had - which is exactly the kind of number
    that survives a review and then cannot be reproduced.
    """
    ordered = sorted(values)
    if not ordered:
        raise ValueError("no samples to take a percentile of")
    rank = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


@dataclass
class Samples:
    """A set of timings, summarised."""

    label: str
    samples: list[Sample] = field(default_factory=list)

    def add(self, sample: Sample) -> None:
        self.samples.append(sample)

    @property
    def times(self) -> list[float]:
        return [s.elapsed_ms for s in self.samples]

    @property
    def n(self) -> int:
        return len(self.samples)

    @property
    def p50(self) -> float:
        return percentile(self.times, 50)

    @property
    def p95(self) -> float:
        return percentile(self.times, 95)

    @property
    def maximum(self) -> float:
        return max(self.times)

    @property
    def minimum(self) -> float:
        return min(self.times)

    @property
    def spread(self) -> float:
        """p95/p50. A healthy warm endpoint sits near 1; a bimodal one - warm
        responses interleaved with cold starts - climbs, and climbs long before
        the p95 budget itself is breached."""
        return self.p95 / self.p50 if self.p50 else math.inf

    def statuses(self) -> dict[int, int]:
        counts: dict[int, int] = {}
        for s in self.samples:
            counts[s.status] = counts.get(s.status, 0) + 1
        return counts

    def summary(self) -> dict[str, object]:
        return {
            "label": self.label,
            "n": self.n,
            "minMs": round(self.minimum, 1),
            "p50Ms": round(self.p50, 1),
            "p95Ms": round(self.p95, 1),
            "maxMs": round(self.maximum, 1),
            "spread": round(self.spread, 2),
            "statuses": {str(k): v for k, v in sorted(self.statuses().items())},
        }

    def describe(self) -> str:
        return (
            f"{self.label}: n={self.n} min={self.minimum:.0f} p50={self.p50:.0f} "
            f"p95={self.p95:.0f} max={self.maximum:.0f} ms, statuses={self.statuses()}"
        )

    def assert_within(self, budget_ms: float, *, at: str = "p95") -> None:
        actual = {"p50": self.p50, "p95": self.p95, "max": self.maximum}[at]
        headroom = (1 - actual / budget_ms) * 100 if budget_ms else 0
        assert actual <= budget_ms, (
            f"{self.label} {at} was {actual:.0f}ms against a {budget_ms:.0f}ms budget "
            f"({-headroom:.0f}% over).\n  {self.describe()}\n"
            f"  slowest: {sorted(self.times, reverse=True)[:5]}"
        )


class Recorder:
    """
    Collects every measured set in a run and writes one JSON report.

    Budgets here start as placeholders, the same as the agent budgets in
    testbed.config.json. They only become real once there are baselines to set
    them from, and there are only baselines if every run leaves its numbers
    behind. That is this class's entire reason to exist.
    """

    def __init__(self, base_url: str, report_path: str) -> None:
        self.base_url = base_url
        self.path = ROOT / report_path
        self.sets: list[Samples] = []
        self.notes: dict[str, object] = {}

    def record(self, samples: Samples) -> Samples:
        self.sets.append(samples)
        return samples

    def note(self, key: str, value: object) -> None:
        self.notes[key] = value

    def write(self) -> Path | None:
        if not self.sets and not self.notes:
            return None
        payload = {
            "recordedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "baseUrl": self.base_url,
            "commit": os.getenv("GITHUB_SHA", "")[:12] or None,
            "measurements": [s.summary() for s in self.sets],
            "notes": self.notes,
            "samples": [asdict(s) for group in self.sets for s in group.samples],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return self.path
