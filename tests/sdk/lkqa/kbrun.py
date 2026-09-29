"""
The KB-correctness run's plan and results table - shared by the live test
(sdk/tests/test_kb_correctness.py) and by the offline re-score:

    cd tests/sdk && uv run python -m lkqa.kbrun      # rebuild report/kb-correctness.md + report/data/kb-correctness.json from recordings

Re-scoring matters because the verdict is a pure function of (recording, KB
index): fix the grammar or rebuild the index and every past call can be
re-judged without making it again.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from . import cases, grounding
from .bridge import ROOT, Transcript, oracle, testbed

RUN = testbed.config()["livekitSdk"]["kbRun"]


def noisy(scenario: dict[str, Any]) -> bool:
    """Its own expected facts are not in its own KB entry - cannot be judged."""
    from src import numerals

    text, _ = grounding._answer_scope(scenario)
    have = {numerals.key_of(m) for m in numerals.extract(text)}
    want = {numerals.key_of(m) for a in scenario["expectAnchors"] for m in numerals.extract(a)}
    return not want or not want <= have


def plan() -> tuple[list[dict[str, Any]], list[str]]:
    """(scenarios to call, scenario ids excluded as data defects)."""
    chosen, excluded = [], []
    for kb in cases.serial_routed_kbs():
        for s in cases.anchored(kb["id"], RUN["kinds"]):
            if RUN.get("excludeNoisyAnchors") and noisy(s):
                excluded.append(s["id"])
            else:
                chosen.append(s)
    chosen += [testbed.scenario_by_id(i) for i in RUN["procedures"] + RUN["generalProblems"]]
    return chosen, excluded


def row(scenario: dict[str, Any], scored: Any | None, serial: str, error: str | None) -> dict[str, Any]:
    if scored is None:
        return {"scenario": scenario["id"], "kb": scenario["kbId"], "question": scenario["question"],
                "serial": serial, "verdict": "ERROR", "error": error}
    v = {x.check: x for x in scored.grounding.verdicts}
    stated = v.get("sectionValues")
    anchors = v.get("requiredAnchors")
    if scored.grounding.zero_tolerance_failures:
        verdict = "FAIL"
    elif stated is not None and stated.status == oracle.PASS:
        verdict = "PASS"
    else:
        verdict = "NOT SCORED"  # no value of the asked kind reached the transcript
    return {
        "scenario": scenario["id"], "kb": scenario["kbId"], "question": scenario["question"], "serial": serial,
        "expected": scenario["expectAnchors"],
        "stated": stated.evidence if stated else [],
        "verdict": verdict,
        "failures": scored.grounding.zero_tolerance_failures,
        "coverage": anchors.status if anchors else None,
        "offScope": v["offScopeValues"].evidence if "offScopeValues" in v else [],
        "citation": stated.citation if stated else None,
        "recording": scored.recording.name,
    }


def write(rows: list[dict[str, Any]], excluded: list[str]) -> None:
    out, data = ROOT / "report", ROOT / "report" / "data"
    data.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    (data / "kb-correctness.json").write_text(
        json.dumps({"finishedAt": stamp, "excludedDataDefects": excluded, "calls": rows}, indent=2, ensure_ascii=False) + "\n"
    )
    counts = {k: sum(r["verdict"] == k for r in rows) for k in ("PASS", "FAIL", "NOT SCORED", "ERROR")}
    lines = [
        "# KB correctness - live calls judged against resources/kb", "",
        f"{stamp} - {len(rows)} calls: **{counts['PASS']} correct, {counts['FAIL']} wrong, "
        f"{counts['NOT SCORED']} not scored, {counts['ERROR']} errors**", "",
        "| Verdict | Scenario | Question | Expected (KB) | Agent's direct answer | Why | Other values in the call, outside this entry (reported only) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda r: ({"FAIL": 0, "ERROR": 1, "NOT SCORED": 2, "PASS": 3}[r["verdict"]], r["scenario"])):
        why = "; ".join(r.get("failures") or []) or r.get("error") or ""
        lines.append(
            f"| {r['verdict']} | {r['scenario']} | {r['question'][:60]} | {', '.join(r.get('expected') or [])} | "
            f"{', '.join(r.get('stated') or [])} | {why[:160].replace('|', '/')} | {', '.join(r.get('offScope') or [])[:120]} |"
        )
    if excluded:
        lines += ["", f"Excluded as data defects (their expected facts are not in their own KB entry): {', '.join(excluded)}"]
    (out / "kb-correctness.md").write_text("\n".join(lines) + "\n")




def rescore(directory: Path | None = None) -> list[dict[str, Any]]:
    """Latest recording per KB-run scenario, re-judged with today's checks."""
    directory = directory or ROOT / "report" / "data" / "recordings"
    scenarios, excluded = plan()
    wanted = {s["id"]: s for s in scenarios}
    latest: dict[str, Path] = {}
    for path in sorted(directory.glob("sdk-kb-*.json")):
        sid = Transcript.load(path).scenario_id
        if sid in wanted:
            latest[sid] = path  # sorted by name = by timestamp
    rows = []
    for sid, path in sorted(latest.items()):
        transcript = Transcript.load(path)
        verdict = grounding.evaluate(transcript, section_scenario=wanted[sid])
        scored = SimpleNamespace(grounding=verdict, recording=path)
        rows.append(row(wanted[sid], scored, transcript.serial, None))
    for sid in sorted(set(wanted) - set(latest)):
        rows.append(row(wanted[sid], None, "", "no recording - the call never completed"))
    write(rows, excluded)
    return rows


if __name__ == "__main__":
    rows = rescore(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    counts = {k: sum(r["verdict"] == k for r in rows) for k in ("PASS", "FAIL", "NOT SCORED", "ERROR")}
    print(f"[kb] re-scored {len(rows)} calls: {counts} -> report/kb-correctness.md")
