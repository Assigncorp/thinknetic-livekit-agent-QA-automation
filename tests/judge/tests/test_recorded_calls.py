"""
Score every recorded call against its knowledge base.

Report-only: nothing here fails on a low score unless judge.requireScoreGate or
judge.requireSafetyGate is turned on. That is the contract docs/architecture.md
sets out - semantic scoring reported separately from the pass/fail suite, so a
borderline score never blocks a release on its own - and it is the same shape as
rateLimit.saturation.requireEnforcement and assertions.checkExpectedAnchors,
both of which record findings rather than gate on them.

What this suite is for today is the trend. Every run appends to
report/data/judge-scores.json, and after a fortnight the thresholds in config can be
set from the distribution instead of from a reading of the manuals.
"""

from __future__ import annotations

import pytest

from src import scorer, testbed

pytestmark = [pytest.mark.judged]




def test_recordings_score_against_their_knowledge_base(judge_available, recordings, recorder):
    """
    JS-01: score every recording, report the lot.

    One test over all recordings rather than one per recording, on purpose: the
    useful unit is the distribution, and a parametrised suite that goes half red
    reports the same finding once per call while burying the summary.
    """
    cfg = testbed.judge_config()
    results = [scorer.score_call(call, recorder) for call in recordings]

    scored = [r for r in results if r["scored"]]
    skipped = [r for r in results if not r["scored"]]

    for result in skipped:
        print(f"\n[judge] NOT SCORED {result['scenarioId']}: {result['notScoredReason']}")

    if not scored:
        pytest.skip(
            f"none of the {len(results)} recording(s) had enough answer to judge - "
            f"see the notScored reasons above and in report/data/judge-scores.json"
        )

    for result in scored:
        print(f"\n[judge] {result['scenarioId']} ({result['kbCitation']}) "
              f"overall {result['overall']}")
        for rubric_id, entry in result["rubrics"].items():
            if entry.get("score") is None:
                print(f"[judge]   {rubric_id:<18} MISSING - {entry['justification']}")
                continue
            mark = "!" if entry["score"] < entry["threshold"] else " "
            applies = "" if entry.get("applicable", True) else "  (n/a)"
            print(f"[judge] {mark} {rubric_id:<18} {entry['score']:.2f}{applies}  "
                  f"{entry['justification'][:100]}")

    gate_breaches = [(r["scenarioId"], r["gateBreaches"]) for r in scored if r["gateBreaches"]]
    breaches = [(r["scenarioId"], r["breaches"]) for r in scored if r["breaches"]]

    if cfg["requireSafetyGate"]:
        assert not gate_breaches, (
            f"safety rubrics breached: {gate_breaches}. These are the two failures "
            f"that put an operator on the wrong procedure - a fabricated specification "
            f"and a cross-family answer. See report/data/judge-scores.json for the evidence "
            f"the judge quoted."
        )

    if cfg["requireScoreGate"]:
        assert not breaches, f"rubric thresholds breached: {breaches}"

    if breaches and not cfg["requireScoreGate"]:
        pytest.skip(
            f"{len(breaches)} of {len(scored)} call(s) scored under a threshold: "
            f"{breaches}. Reporting only - set judge.requireScoreGate to fail on this, "
            f"but re-base the thresholds from report/data/judge-scores.json first"
        )


def test_the_judge_and_the_literal_matcher_agree(judge_available, recordings, recorder):
    """
    JS-02: where the LLM and the regex disagree about anchor coverage, say so.

    Not a defect in either on its own. The matcher is literal and the judge is
    not, so "judge says the fact was cited, matcher says it was not" usually
    means the agent paraphrased a measurement in a way anchors.py has no spoken
    form for - which is a gap in the matcher, and the matcher is what the
    browser suite gates on. The reverse direction is more interesting: the
    matcher found the digits and the judge did not accept them, which tends to
    mean the number was cited for the wrong thing.

    Always reports, never fails. It is a pointer at work to do, not a verdict.
    """
    disagreements = []
    for call in recordings:
        result = scorer.score_call(call, recorder)
        if not result["scored"]:
            continue
        judged = result["rubrics"].get("anchorCoverage", {}).get("score")
        literal = result["anchors"]["coverage"]
        if judged is None or literal is None:
            continue
        if abs(judged - literal) >= 0.34:
            disagreements.append(
                {
                    "scenario": result["scenarioId"],
                    "judge": judged,
                    "matcher": literal,
                    "expected": result["anchors"]["expected"],
                    "matched": result["anchors"]["citedDeterministically"],
                    "why": result["rubrics"]["anchorCoverage"]["justification"],
                }
            )

    recorder.note("anchorDisagreements", disagreements)
    for item in disagreements:
        print(f"\n[judge] anchor disagreement on {item['scenario']}: "
              f"judge {item['judge']} vs matcher {item['matcher']}")
        print(f"[judge]   expected {item['expected']}, matcher found {item['matched']}")
        print(f"[judge]   judge said: {item['why']}")

    if disagreements:
        pytest.skip(
            f"{len(disagreements)} anchor disagreement(s) - reported, not failed. "
            f"Each one is either a spoken form missing from anchors.py (and from "
            f"ui/src/utils/anchors.ts) or a number the agent used for the wrong thing"
        )
