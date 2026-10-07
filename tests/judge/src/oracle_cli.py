"""
`make oracle` - score every recorded call deterministically and write the report.

Separate from pytest on purpose. The oracle's own regression suite
(tests/test_oracle.py) belongs in the offline pytest run and gates a PR; THIS
is the thing you point at a directory of real recordings to see what the
deployment is actually doing, and it is useful long before any of the gates in
config.oracle.gates are switched on.

Exit status is decided by gate() alone, which reads config.oracle.gates - every
entry of which ships false. So today this always exits 0 and always writes the
report. That is the intended landing state: collect a fortnight of verdicts,
then turn on crossFamilyForbidden and numericProvenance because the baseline
says they are clean, not because they sound important.

    make oracle                 score judge/recordings/
    make oracle DIR=path/to     score somewhere else
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import oracle, testbed
from .transcript import Transcript

ROOT = Path(__file__).resolve().parents[3]

MARK = {oracle.PASS: "ok  ", oracle.FAIL: "FAIL", oracle.NA: "n/a "}


def score_directory(directory: Path) -> dict:
    calls = [Transcript.load(p) for p in sorted(directory.glob("*.json"))]
    if not calls:
        print(f"no recordings in {directory} - nothing to score")
        return {"calls": [], "totals": {}, "breaches": []}

    results = []
    breaches: list[str] = []
    totals: Counter[str] = Counter()

    for call in calls:
        verdicts = oracle.evaluate(call)
        ok, call_breaches = oracle.gate(verdicts)
        breaches.extend(f"{Path(call.source).name}: {b}" for b in call_breaches)

        print(f"\n{Path(call.source).name}  [{call.kb_id} / {call.scenario_id}]")
        for verdict in verdicts:
            totals[verdict.status] += 1
            print(f"  {MARK[verdict.status]} {verdict.check:<22} {verdict.summary}")
            if verdict.failed:
                for line in verdict.evidence[:5]:
                    print(f"         {line}")
                if verdict.citation:
                    print(f"         says who: {verdict.citation}")

        results.append(
            {
                "recording": Path(call.source).name,
                "scenarioId": call.scenario_id,
                "kbId": call.kb_id,
                "serial": call.serial,
                "gated": not ok,
                "verdicts": [v.to_dict() for v in verdicts],
            }
        )

    return {
        "_note": (
            "Deterministic verdicts - a pure function of the transcript and the "
            "compiled KB index. Reproduce with: make oracle"
        ),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "gatesEnabled": sorted(k for k, v in oracle.oracle_config()["gates"].items() if v),
        "totals": dict(totals),
        "calls": results,
        "aggregate": oracle.aggregate(
            [[v for v in oracle.evaluate(c)] for c in calls]
        ),
        "breaches": breaches,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        default=str(Path(__file__).resolve().parents[1] / "recordings"),
        help="directory of recorded calls (default: judge/recordings)",
    )
    parser.add_argument("--out", default=None, help="where to write the report")
    args = parser.parse_args(argv)

    report = score_directory(Path(args.dir))
    if not report.get("calls"):
        return 0

    out = Path(args.out) if args.out else ROOT / oracle.oracle_config()["reportPath"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    totals = report["totals"]
    print(
        f"\n[oracle] {totals.get('pass', 0)} passed, {totals.get('fail', 0)} failed, "
        f"{totals.get('notApplicable', 0)} not applicable across {len(report['calls'])} call(s)"
    )
    print(f"[oracle] wrote {out.relative_to(ROOT)}")

    if report["breaches"]:
        print("\n[oracle] GATED - these checks are switched on in config.oracle.gates:")
        for breach in report["breaches"]:
            print(f"  {breach}")
        return 1

    if totals.get("fail"):
        enabled = report["gatesEnabled"]
        print(
            f"[oracle] failures above are reported, not gated "
            f"(config.oracle.gates enabled: {enabled or 'none'})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
