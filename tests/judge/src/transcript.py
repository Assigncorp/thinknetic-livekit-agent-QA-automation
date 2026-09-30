"""
A call, in the shape the judge scores.

Two things produce one of these: the sdk/ suite, which drives a real session,
and `Transcript.load()`, which reads a recording off disk. Keeping them behind
one type is what lets the scoring suite run on a laptop with no credentials at
all - and it is also what makes a failure reproducible, because a call that
scored badly can be replayed through the judge without opening a new session
and getting a different conversation.

The important shape here is `full_answer`, and it comes straight from a finding
in docs/chat-flow.md: this agent is a guided walkthrough, not a Q&A bot. Asked
a question out of the manual it opens with a safety preamble, offers to text
the steps, and then delivers the procedure one step at a time. The manual's
facts are several turns in. Scoring "the reply" therefore scores an
acknowledgement, and the judge would mark a perfectly good call as unsupported.
So the unit of judgement is every agent turn after the question was asked.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import testbed


@dataclass
class Turn:
    """One complete turn, by one speaker, after it stopped streaming."""

    speaker: str  # "agent" | "caller"
    text: str
    elapsed_ms: int | None = None
    intent: str | None = None  # which chatFlow intent the driver matched
    idle: bool = False  # an unprompted "are you still there?"

    def to_dict(self) -> dict[str, Any]:
        return {
            "speaker": self.speaker,
            "text": self.text,
            "elapsedMs": self.elapsed_ms,
            "intent": self.intent,
            "idle": self.idle,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Turn:
        return cls(
            speaker=raw["speaker"],
            text=raw["text"],
            elapsed_ms=raw.get("elapsedMs"),
            intent=raw.get("intent"),
            idle=bool(raw.get("idle", False)),
        )


@dataclass
class Transcript:
    """One call: which scenario drove it, which serial, and every turn."""

    scenario_id: str
    kb_id: str
    serial: str
    controller: str | None
    question: str
    turns: list[Turn] = field(default_factory=list)
    room: str | None = None
    recorded_at: str | None = None
    source: str = "live"  # "live" | a file path

    # -- the thing that gets scored ---------------------------------------

    def agent_turns(self, include_idle: bool = False) -> list[Turn]:
        """Agent turns, with the unprompted nudges stripped.

        The agent injects "Are you still there?" while it waits. Those are
        listed in chatFlow.agentIdlePrompts and carry no content; counting
        them as answers drags every score down for a call that was merely
        slow."""
        return [t for t in self.turns if t.speaker == "agent" and (include_idle or not t.idle)]

    def question_index(self) -> int | None:
        """Where the caller actually asked the scenario's question.

        Matched on the turn text rather than on position, because the driver
        answers whatever the agent asks first - a re-request for the serial, a
        clarifying question - so the question is not at a fixed index."""
        needle = self.question.strip().lower()
        for i, turn in enumerate(self.turns):
            if turn.speaker == "caller" and needle and needle in turn.text.strip().lower():
                return i
        return None

    @property
    def full_answer(self) -> str:
        """
        Every agent turn after the question, joined.

        Falls back to all agent turns when the question cannot be located,
        which happens when a call ended before it was ever asked. That case is
        reported as notScored rather than scored against an empty answer -
        see scorer.score_call.
        """
        start = self.question_index()
        turns = self.turns if start is None else self.turns[start + 1 :]
        return "\n\n".join(t.text.strip() for t in turns if t.speaker == "agent" and not t.idle)

    @property
    def answer_turn_count(self) -> int:
        start = self.question_index()
        turns = self.turns if start is None else self.turns[start + 1 :]
        return len([t for t in turns if t.speaker == "agent" and not t.idle])

    # -- scenario metadata the rubrics need --------------------------------

    def scenario(self) -> dict[str, Any]:
        return testbed.scenario_by_id(self.scenario_id)

    def expect_anchors(self) -> list[str]:
        return list(self.scenario().get("expectAnchors") or [])

    # -- persistence -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenarioId": self.scenario_id,
            "kbId": self.kb_id,
            "serial": self.serial,
            "controller": self.controller,
            "question": self.question,
            "room": self.room,
            "recordedAt": self.recorded_at or datetime.now(timezone.utc).isoformat(),
            "turns": [t.to_dict() for t in self.turns],
        }

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path

    @classmethod
    def from_dict(cls, raw: dict[str, Any], source: str = "live") -> Transcript:
        return cls(
            scenario_id=raw["scenarioId"],
            kb_id=raw["kbId"],
            serial=raw["serial"],
            controller=raw.get("controller"),
            question=raw["question"],
            turns=[Turn.from_dict(t) for t in raw.get("turns", [])],
            room=raw.get("room"),
            recorded_at=raw.get("recordedAt"),
            source=source,
        )

    @classmethod
    def load(cls, path: Path) -> Transcript:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(raw, source=str(path))


def recordings_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "recordings"


def load_recordings() -> list[Transcript]:
    """Every recorded call on disk, sorted by filename so a run is stable."""
    directory = recordings_dir()
    if not directory.exists():
        return []
    return [Transcript.load(p) for p in sorted(directory.glob("*.json"))]
