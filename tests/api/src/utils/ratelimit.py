"""
The public API's rate limiter, read as data rather than guessed at.

Every /api/v1 response carries a fixed-window limiter's state:

    x-ratelimit-limit: 100        requests allowed per window
    x-ratelimit-remaining: 99     requests left in THIS window
    x-ratelimit-reset: 60         seconds until the window rolls over

Three facts about it shape the whole API strategy. All three were measured
against etnyre-dev on 2026-09-21, and each one is asserted by a test in
tests/test_rate_limit.py so it cannot quietly stop being true:

  * The bucket is shared across the API prefix, and failures count. A 404 from
    the fail-closed tests decrements `remaining` exactly like a 200 does. So
    does a 304 from a conditional GET. The functional suite therefore spends
    quota that it has never accounted for.
  * 100 requests per minute is the ceiling for the whole suite, not per test
    file. That is why performance work here is sampling, not load generation -
    see docs/api-test-strategy.md on why k6 would be the wrong tool today.
  * /env.js carries no limiter headers at all. It is served as a static asset,
    outside the bucket, and can be measured freely.

`Bucket` is the piece that makes the rest safe to run: it watches every
response the shared client receives, and `reserve()` parks the suite until the
window rolls over rather than letting a performance test starve the functional
tests that run after it.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class RateLimitState:
    """One reading of the limiter, taken from one response's headers."""

    limit: int
    remaining: int
    reset_s: int

    def __str__(self) -> str:  # shows up in assertion messages
        return f"{self.remaining}/{self.limit} left, window resets in {self.reset_s}s"


def read_state(
    response: httpx.Response,
    *,
    limit_header: str = "x-ratelimit-limit",
    remaining_header: str = "x-ratelimit-remaining",
    reset_header: str = "x-ratelimit-reset",
) -> RateLimitState | None:
    """
    The limiter's state as this response reported it, or None if the response
    carried no limiter headers at all.

    None is a meaningful answer, not a failure: static assets are served from
    outside the limiter and legitimately have none. A response with only SOME
    of the three headers is a defect, and is reported as such rather than
    being silently treated as unlimited.
    """
    h = response.headers
    present = [name for name in (limit_header, remaining_header, reset_header) if name in h]
    if not present:
        return None
    if len(present) != 3:
        raise AssertionError(
            f"{response.request.url.path} returned a partial set of rate-limit "
            f"headers ({present}). A client cannot back off correctly against "
            f"half a contract."
        )
    try:
        return RateLimitState(
            limit=int(h[limit_header]),
            remaining=int(h[remaining_header]),
            reset_s=int(h[reset_header]),
        )
    except ValueError as exc:  # non-numeric header - also a contract break
        raise AssertionError(
            f"rate-limit headers on {response.request.url.path} are not integers: "
            f"{ {k: h.get(k) for k in (limit_header, remaining_header, reset_header)} }"
        ) from exc


class Bucket:
    """
    Session-wide view of the limiter, fed by an httpx response event hook.

    Two jobs. It records what the limiter said, so tests can assert on the
    contract without each making their own extra request just to look. And it
    throttles the suite: `reserve(n)` blocks until there is genuinely room for
    n more requests, so a performance sample can never leave the functional
    tests behind it with an empty bucket.

    Thread-safe because the concurrency test drives the same client from a
    thread pool.
    """

    def __init__(self, *, window_s: int, reserve_floor: int, headers: dict[str, str]) -> None:
        self._window_s = window_s
        self._reserve_floor = reserve_floor
        self._headers = headers
        self._lock = threading.Lock()
        self._primer: Callable[[], object] | None = None
        self._primed = False
        self.last: RateLimitState | None = None
        self.low_water: int | None = None
        self.requests_seen = 0
        self.throttled_s = 0.0
        self.windows_seen = 1

    def set_primer(self, primer: Callable[[], object]) -> None:
        """
        How to spend one request finding out where the window stands.

        Needed because the first reservation of a session has nothing to
        reserve against: no response has been seen, so `last` is None and the
        throttle cannot tell a fresh window from an almost-empty one. Left
        unprimed it waves through the largest reservation the suite makes -
        the 23-request warm sample - on no information at all, which is
        exactly the case the throttle exists to handle. Two `make perf` runs
        in the same minute would then collide.

        Lazy rather than an autouse fixture on purpose: the catalogue suite
        makes no network calls at all and must stay that way, and it never
        reserves.
        """
        self._primer = primer

    # -- observation ------------------------------------------------------

    def observe(self, response: httpx.Response) -> None:
        """httpx response event hook. Never raises: a broken header is the
        business of test_rate_limit, not of whichever test happened to fire
        the request that carried it."""
        try:
            state = read_state(response, **self._header_kwargs())
        except AssertionError:
            return
        with self._lock:
            self.requests_seen += 1
            if state is None:
                return
            if self.last is not None and state.reset_s > self.last.reset_s:
                # The countdown went back up: a new window started.
                self.windows_seen += 1
            self.last = state
            if self.low_water is None or state.remaining < self.low_water:
                self.low_water = state.remaining

    def _header_kwargs(self) -> dict[str, str]:
        return {
            "limit_header": self._headers["limit"],
            "remaining_header": self._headers["remaining"],
            "reset_header": self._headers["reset"],
        }

    # -- throttling -------------------------------------------------------

    def reserve(self, n: int, *, why: str = "") -> None:
        """
        Park until n more requests can be made without emptying the bucket
        below its reserve floor.

        The floor exists because this suite is not the only caller: the browser
        suite, a colleague's manual click-through and CI all share one egress
        IP on a shared dev deployment. Spending the last of a window because a
        percentile needed one more sample is a self-inflicted outage.

        Sleeps at most one window. If the limiter never recovers, the test that
        follows fails on a 429 and says so, which is better than hanging.
        """
        with self._lock:
            state = self.last
            prime = self._primer if (state is None and not self._primed) else None
            if prime is not None:
                self._primed = True

        if prime is not None:
            # Outside the lock: the probe's own response feeds observe().
            try:
                prime()
            except Exception:  # a broken probe must not fail somebody else's test
                pass
            with self._lock:
                state = self.last

        if state is None:
            return  # unlimited surface, or the probe could not reach the limiter
        if state.remaining - n >= self._reserve_floor:
            return

        wait = min(state.reset_s + 1, self._window_s + 1)
        if wait <= 0:
            return
        print(
            f"\n[rate limit] {state}; {n} more requested"
            f"{f' for {why}' if why else ''} - waiting {wait}s for the window to roll over"
        )
        time.sleep(wait)
        with self._lock:
            self.throttled_s += wait

    def summary(self) -> dict[str, object]:
        with self._lock:
            return {
                "requestsObserved": self.requests_seen,
                "limit": self.last.limit if self.last else None,
                "lowWaterRemaining": self.low_water,
                "windowsUsed": self.windows_seen,
                "secondsSpentThrottled": round(self.throttled_s, 1),
            }


def partition_streams(readings: list[RateLimitState]) -> list[list[RateLimitState]]:
    """
    Split a run of readings into the independent counters that produced them.

    MEASURED 2026-09-21: the limiter's state is held PER SERVERLESS INSTANCE,
    not per client. When only one instance is warm, 25 consecutive requests
    produce one clean sequence (99 -> 75, reset 60 -> 48). When several are
    warm - which the concurrency probe in test_performance.py itself causes -
    readings from different instances interleave, each with its own count and
    its own window phase:

        stream A:  65 64 63 62 61 60 59 58 57 56 ...   reset 23 -> 13
        stream B:  89       77 76             75 ...   reset  8 ->  6

    A reading only continues a stream if its count went DOWN and its window
    phase is within a few seconds of the previous one. Everything else starts
    a new stream. Grouping is greedy and first-fit, which is good enough to
    tell one instance from several; it is not trying to be a perfect
    reconstruction.

    Why this exists: without it, a test comparing two consecutive readings
    sees a count that jumped UP and concludes the window rolled over. That is
    wrong, and it was silently skipping the decrement tests exactly when the
    deployment was busiest - the moment they are most worth running.
    """
    streams: list[list[RateLimitState]] = []
    for reading in readings:
        for stream in streams:
            previous = stream[-1]
            if reading.remaining < previous.remaining and 0 <= previous.reset_s - reading.reset_s <= 3:
                stream.append(reading)
                break
        else:
            streams.append([reading])
    return streams


def same_stream(first: RateLimitState, second: RateLimitState) -> bool:
    """
    Whether two readings plausibly came from the same instance's counter.

    Same window phase (a couple of seconds of drift at most) and a count that
    did not go up. Used to retry a comparison until both readings land on one
    instance, rather than skipping the assertion when they do not.
    """
    return second.remaining <= first.remaining and 0 <= first.reset_s - second.reset_s <= 3


def saturation_enabled(config_default: bool) -> bool:
    """
    The saturating tests deliberately empty the window, which blocks every
    other caller on this egress IP for up to a minute. Opt-in only, and the
    environment variable wins so CI can enable it on a schedule without an
    edit to the committed config.
    """
    env = os.getenv("RUN_RATE_LIMIT_SATURATION")
    if env is not None:
        return env.strip().lower() in {"1", "true", "yes", "on"}
    return config_default
