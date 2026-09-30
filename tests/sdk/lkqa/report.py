"""
report/data/livekit-sdk.*.json - what every live test measured, pass or fail.

The budgets in livekitSdk.budgets are placeholders until there is a baseline,
and a baseline is only ever a pile of these files. So every live test records
its timings and observations here whether it passed, failed or was report-only,
and every conversation is saved as a transcript the oracle can re-score later
(`make oracle DIR=report/data/recordings`).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bridge import ROOT, Transcript, testbed


class Report:
    def __init__(self) -> None:
        self.started = datetime.now(timezone.utc).isoformat()
        self.entries: list[dict[str, Any]] = []
        self.findings: list[dict[str, Any]] = []

    def record(self, test_id: str, **data: Any) -> None:
        self.entries.append({"id": test_id, **data})

    def finding(self, test_id: str, summary: str, **evidence: Any) -> None:
        """A report-only observation: real, but not gated (livekitSdk.gates)."""
        print(f"\n[lkqa] FINDING {test_id}: {summary}")
        self.findings.append({"id": test_id, "summary": summary, **evidence})

    def save_transcript(self, transcript: Transcript, label: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = ROOT / "report" / "data" / "recordings" / f"sdk-{label}-{transcript.serial}-{stamp}.json"
        return transcript.save(path)

    def write(self) -> Path | None:
        if not self.entries and not self.findings:
            return None
        path = ROOT / testbed.config()["livekitSdk"]["reportPath"]
        # One file per make target (LKQA_REPORT_TAG=livekit-grounding ->
        # livekit-sdk.livekit-grounding.json): parallel runs must not overwrite
        # each other, and neither should the steps of a sequential `make all`.
        # tools/build_report.py merges them all.
        tag = os.getenv("LKQA_REPORT_TAG", "").strip()
        if tag:
            path = path.with_name(f"{path.stem}.{tag}{path.suffix}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "startedAt": self.started,
                    "finishedAt": datetime.now(timezone.utc).isoformat(),
                    "agentName": testbed.judge_config()["livekit"]["agentName"],
                    "entries": self.entries,
                    "findings": self.findings,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return path
