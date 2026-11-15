"""
LiveKit-style assertions over a live call.

LiveKit's own test API (`AgentSession.run()` -> `RunResult.expect`) drives the
agent's Python class in-process; it cannot reach a deployed agent in a room.
This mirrors its shape - `next_event()`, `is_message(role=…)`,
`contains_message(…)` - over the events a real call recorded, so the tests read
the way LiveKit tests read. Where LiveKit offers `.judge(llm, intent=…)`, this
offers `matching=patterns`: deterministic phrase matching, no LLM.

    run = RunResult(call.events)
    run.expect.next_event().is_message(role="assistant")
    run.expect.contains_message(role="assistant", matching=FEEDBACK_ASK)
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

ROLES = {"assistant": "agent", "user": "caller", "agent": "agent", "caller": "caller"}


class ExpectationError(AssertionError):
    pass


def _compile(patterns: Iterable[str] | str) -> list[re.Pattern[str]]:
    if isinstance(patterns, str):
        patterns = [patterns]
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def text_matches(text: str, patterns: Iterable[str] | str) -> str | None:
    """The first pattern that matches (curly quotes folded), or None."""
    folded = text.replace("’", "'").replace("‘", "'")
    for p in _compile(patterns):
        if p.search(folded):
            return p.pattern
    return None


@dataclass
class MessageAssert:
    event: dict[str, Any]

    @property
    def text(self) -> str:
        return self.event["text"]


@dataclass
class EventAssert:
    event: dict[str, Any] | None
    index: int

    def is_message(self, role: str = "assistant") -> MessageAssert:
        if self.event is None:
            raise ExpectationError(f"expected a {role} message at event {self.index}, but there are no more events")
        if self.event["role"] != ROLES[role]:
            raise ExpectationError(
                f"expected a {role} message at event {self.index}, got {self.event['role']}: {self.event['text']!r}")
        return MessageAssert(self.event)


class EventRangeAssert:
    def __init__(self, events: list[dict[str, Any]], start: int = 0) -> None:
        self._events = events
        self._pos = start

    def next_event(self) -> EventAssert:
        ev = self._events[self._pos] if self._pos < len(self._events) else None
        a = EventAssert(ev, self._pos)
        self._pos += 1
        return a

    def contains_message(self, role: str = "assistant", matching: Iterable[str] | str | None = None,
                         *, what: str = "message") -> MessageAssert:
        for ev in self._events[self._pos:]:
            if ev["role"] == ROLES[role] and (matching is None or text_matches(ev["text"], matching)):
                return MessageAssert(ev)
        raise ExpectationError(f"no {role} {what} among {len(self._events) - self._pos} event(s)")


class RunResult:
    """The recorded events of a call (or part of one), LiveKit-style."""

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self.events = events

    @property
    def expect(self) -> EventRangeAssert:
        return EventRangeAssert(self.events)
