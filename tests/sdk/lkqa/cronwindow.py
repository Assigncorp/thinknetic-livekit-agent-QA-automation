"""Minute-grid evaluation of `transfer.destinations[].available` cron windows."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from croniter import croniter

MONDAY = datetime(2026, 1, 5)  # a Monday; naive wall-clock, read in the desk timezone


def is_open(dest: dict, wall: datetime) -> bool:
    """`wall` is naive wall-clock time in the transfer timezone. No `available` = always open."""
    windows = dest.get("available")
    if windows is None:
        return True
    return any(croniter.match(c, wall) for c in windows)


def week_grid(destinations: list[dict], keyword: str) -> list[list[int]]:
    """For every minute of a week, the indexes of destinations open for `keyword`
    (in file order - the first one wins, as settings.yaml documents)."""
    cand = [(i, d) for i, d in enumerate(destinations) if keyword in (d.get("keywords") or [])]
    grid = []
    for m in range(7 * 24 * 60):
        t = MONDAY + timedelta(minutes=m)
        grid.append([i for i, d in cand if is_open(d, t)])
    return grid


def first_open(destinations: list[dict], keyword: str, tz: str, now: datetime) -> dict | None:
    wall = now.astimezone(ZoneInfo(tz)).replace(tzinfo=None, second=0, microsecond=0)
    for d in destinations:
        if keyword in (d.get("keywords") or []) and is_open(d, wall):
            return d
    return None
