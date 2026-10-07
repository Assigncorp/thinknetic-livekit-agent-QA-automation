"""
Where the scores go.

Every run writes report/data/judge-scores.json whether it passed, failed or scored
nothing at all, for the reason docs/architecture.md gives about the latency
budgets: a threshold invented before there is data either never fires or fires
constantly. The judge's thresholds are currently guesses, and the only way they
stop being guesses is a file of real scores to re-base them from.

The report is also the whole point of report-only mode. With judge.
requireScoreGate off, a low score does not fail anything - so if it is not
written down it did not happen.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


def _commit() -> str | None:
    """The commit under test, so a score can be traced to a deployment."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


class Recorder:
    """Collects scores across a session and writes them once at the end."""

    def __init__(self, report_path: str, model: str) -> None:
        self._path = ROOT / report_path
        self._model = model
        self._calls: list[dict[str, Any]] = []
        self._notes: dict[str, Any] = {}

    def add_call(self, result: dict[str, Any]) -> None:
        self._calls.append(result)

    def note(self, key: str, value: Any) -> None:
        self._notes[key] = value

    def summary(self) -> dict[str, Any]:
        """Per-rubric means across every call scored this session.

        Means, not pass counts: the trend in the mean is what tells you the
        agent changed, and a pass count against a guessed threshold only tells
        you about the guess."""
        scored = [c for c in self._calls if c.get("scored")]
        by_rubric: dict[str, list[float]] = {}
        for call in scored:
            for rubric_id, entry in (call.get("rubrics") or {}).items():
                by_rubric.setdefault(rubric_id, []).append(float(entry["score"]))

        return {
            "callsScored": len(scored),
            "callsNotScored": len(self._calls) - len(scored),
            "meanByRubric": {
                rubric_id: round(sum(values) / len(values), 3)
                for rubric_id, values in sorted(by_rubric.items())
                if values
            },
            "meanOverall": (
                round(
                    sum(float(c["overall"]) for c in scored if c.get("overall") is not None)
                    / len(scored),
                    3,
                )
                if scored
                else None
            ),
        }

    def write(self) -> Path | None:
        if not self._calls and not self._notes:
            return None
        payload = {
            "recordedAt": datetime.now(timezone.utc).isoformat(),
            "commit": _commit(),
            "baseUrl": os.getenv("BASE_URL"),
            "judgeModel": self._model,
            "summary": self.summary(),
            "calls": self._calls,
            "notes": self._notes,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return self._path
