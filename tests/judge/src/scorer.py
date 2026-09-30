"""
The judge: scores one call against the knowledge base it should have answered
from.

Three design choices carry this module, and all three are corrections of the
obvious way to do it.

1. THE KB IS THE ARBITER, NOT THE MODEL. The judge never answers the caller's
   question itself and is never asked "is this right?". It is asked "is every
   claim here supported by THIS text?", with the relevant KB section supplied.
   Asked the other way it grades against its own training data, which contains
   no Etnyre manual - so it rewards fluency and punishes a correct, terse
   answer. This is the difference between a test of the deployment and a test
   of whichever model is judging.

2. THE WHOLE ANSWER IS THE UNIT. Per docs/chat-flow.md the agent is a guided
   walkthrough: safety preamble, offer to text the steps, then one step per
   turn. Scoring a single reply scores an acknowledgement. Transcript.
   full_answer accumulates every agent turn after the question.

3. EVERY SCORE CARRIES EVIDENCE. Each rubric returns a verbatim quote from the
   transcript and, where it found one, from the KB. A judge that returns 0.4
   and a paragraph of reasoning cannot be audited; one that returns 0.4 and the
   sentence it objected to can be argued with, which is the only way the
   thresholds ever get re-based from guesses to measurements.

Cost: one request per call scored, with the rubric definitions cached as a
stable prefix. The KB section and transcript vary per call and sit after the
cache breakpoint.
"""

from __future__ import annotations

import json
import os
from typing import Any

from . import anchors, corpus, testbed
from .transcript import Transcript

# The rubric definitions and the instructions are identical for every call in a
# run, so they go in the system prompt with a cache breakpoint. Only the KB
# section and the transcript change.
SYSTEM_PREAMBLE = """\
You are grading a support agent's answer against the machine manual it was \
supposed to answer from. You are NOT answering the caller's question yourself, \
and you are NOT judging whether the answer sounds good.

The manual extract you are given is the ONLY source of truth. If a claim is not \
supported by that extract, it is unsupported - even if you happen to believe it \
is true of chip spreaders in general. Your own knowledge of this equipment is \
not evidence and must not influence a score.

Things that must NOT cost the agent marks:
- Speaking numbers as words. This is a voice agent: "four hundred feet per \
minute" is the same fact as "400 FPM", and "two hundred forty degrees" is "240°F".
- Delivering a procedure one step at a time across several turns, or opening \
with a safety warning before the steps. That is the intended behaviour.
- Asking the caller a diagnostic question before answering.
- Being terse, as long as it is correct and complete for what was asked.
- Offering to text the steps to the caller.

Things that MUST cost the agent marks:
- Any specification, measurement, part number, pin reference or threshold that \
does not appear in the extract.
- Describing a procedure for a different controller family than the caller's.
- Presenting a guess as a fact instead of saying it does not know.

Score each rubric from 0.0 to 1.0. Quote your evidence verbatim - a short span \
from the transcript, and from the manual extract where one applies. If a rubric \
does not apply to this call, score it 1.0 and say so in the justification; do \
not penalise an answer for not doing something it was never asked to do.\
"""

RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "rubrics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rubricId": {"type": "string"},
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                    "justification": {
                        "type": "string",
                        "description": "One or two sentences. Say what you found, not what you looked for.",
                    },
                    "transcriptEvidence": {
                        "type": "string",
                        "description": "A short verbatim span from the agent's answer. Empty string if the rubric did not apply.",
                    },
                    "manualEvidence": {
                        "type": "string",
                        "description": "A short verbatim span from the manual extract, where one is relevant. Empty string otherwise.",
                    },
                    "applicable": {
                        "type": "boolean",
                        "description": "False when this rubric had nothing to judge on this call.",
                    },
                },
                "required": [
                    "rubricId",
                    "score",
                    "justification",
                    "transcriptEvidence",
                    "manualEvidence",
                    "applicable",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["rubrics"],
    "additionalProperties": False,
}


class JudgeUnavailable(RuntimeError):
    """No credential, or the SDK is not installed. A reason to skip, never to
    pass: a judged test that silently stops judging is worse than no test."""


def available() -> tuple[bool, str]:
    """Whether the judge can run, and why not if it cannot."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False, (
            "the `anthropic` package is not installed - run: "
            "cd tests/judge && uv sync --extra judge"
        )
    # Ask the SDK what it would actually send, rather than checking for an env
    # var. An unset ANTHROPIC_API_KEY does not mean there is no credential: the
    # client also resolves ANTHROPIC_AUTH_TOKEN, an `ant auth login` profile on
    # disk, and workload identity federation. Checking the env var alone would
    # skip the suite on a machine that is perfectly able to run it.
    #
    # And the constructor is no use as a check either - it does NOT raise
    # without a credential. `anthropic.Anthropic()` returns a client happily and
    # the TypeError arrives at the first request, which for this suite means
    # after the first call was already driven. `auth_headers` is what the client
    # would put on the wire, so an empty dict is the real answer.
    import anthropic

    try:
        headers = anthropic.Anthropic().auth_headers
    except Exception as exc:  # noqa: BLE001 - any construction failure is a skip
        return False, f"could not construct an Anthropic client: {exc}"

    if not headers:
        return False, (
            "no Anthropic credential found. Set ANTHROPIC_API_KEY in .env, or "
            "run `ant auth login`"
        )
    return True, ""


def _client():
    ok, why = available()
    if not ok:
        raise JudgeUnavailable(why)
    import anthropic

    return anthropic.Anthropic()


def build_prompt(call: Transcript) -> tuple[str, str]:
    """
    (system, user) for one call. Pure - no network - so the offline suite can
    assert on what the judge is actually shown.

    That assertion matters more than it looks: the single most likely way this
    whole layer goes quietly wrong is the prompt ending up with the wrong KB
    section in it, and every score after that is confidently meaningless.
    """
    scenario = call.scenario()
    section = corpus.section_for(scenario)
    wrong_families = corpus.other_controller_families(call.kb_id)
    expect = call.expect_anchors()

    rubric_lines = []
    for rubric in testbed.rubrics():
        rubric_lines.append(f"- `{rubric['id']}`: {rubric['description']}")
    rubrics_block = "\n".join(rubric_lines)

    system = f"{SYSTEM_PREAMBLE}\n\nRUBRICS\n{rubrics_block}"

    anchors_block = (
        "\n".join(f"- {a}" for a in expect)
        if expect
        else "(none - this scenario carries no checkable fact, so score "
        "anchorCoverage 1.0 and mark it not applicable)"
    )

    family_block = (
        f"The caller's machine uses the {section.controller} controller. "
        f"An answer that describes {', '.join(wrong_families)} behaviour to this "
        f"caller is a cross-family error and scores 0.0 on controllerFamily."
        if section.controller and wrong_families
        else "This question is not specific to a controller family, so score "
        "controllerFamily 1.0 and mark it not applicable."
    )

    truncation_note = (
        "\n\nNOTE: this extract was trimmed to fit. If a claim looks unsupported "
        "only because the supporting text may have been trimmed away, say so in "
        "the justification and do not score below 0.5 for it."
        if section.truncated
        else ""
    )

    user = f"""\
MACHINE: {section.machine}
CONTROLLER: {section.controller or "not family-specific"}
SERIAL: {call.serial}

{family_block}

MANUAL EXTRACT ({section.citation()})
\"\"\"
{section.text}
\"\"\"{truncation_note}

WHAT THE CALLER ASKED
{call.question}

THE AGENT'S ANSWER (every turn it took after the question, in order)
\"\"\"
{call.full_answer}
\"\"\"

FACTS A CORRECT ANSWER SHOULD REACH (for the anchorCoverage rubric)
{anchors_block}

Score every rubric listed in the system prompt. Return one entry per rubric."""

    return system, user


def score_call(call: Transcript, recorder: Any = None) -> dict[str, Any]:
    """
    Score one call. Returns a result dict; never raises on a low score.

    A call is NOT scored - and says so rather than scoring zero - when the
    agent's accumulated answer is too short to judge. That happens when a call
    ended before the question landed, or when every turn was a clarifying
    question. Scoring it produces a confident zero that describes the test
    harness, not the agent.
    """
    cfg = testbed.judge_config()
    scenario = call.scenario()
    section = corpus.section_for(scenario)

    base: dict[str, Any] = {
        "scenarioId": call.scenario_id,
        "kbId": call.kb_id,
        "serial": call.serial,
        "question": call.question,
        "kbCitation": section.citation(),
        "source": call.source,
        "answerTurns": call.answer_turn_count,
        "answerChars": len(call.full_answer),
    }

    if len(call.full_answer) < int(cfg["minScoredTurnChars"]):
        result = {
            **base,
            "scored": False,
            "notScoredReason": (
                f"the agent's accumulated answer is {len(call.full_answer)} characters, "
                f"under judge.minScoredTurnChars ({cfg['minScoredTurnChars']}). The call "
                f"produced nothing to judge - check the transcript before reading this "
                f"as an agent failure"
            ),
        }
        if recorder:
            recorder.add_call(result)
        return result

    system, user = build_prompt(call)
    client = _client()

    response = client.messages.create(
        model=cfg["model"],
        max_tokens=int(cfg["maxTokens"]),
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": system,
                # Stable across every call in a run; the KB extract and the
                # transcript below it are not, and sit after this breakpoint.
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user}],
        output_config={
            "effort": cfg["effort"],
            "format": {"type": "json_schema", "schema": RESULT_SCHEMA},
        },
    )

    if response.stop_reason == "refusal":
        raise JudgeUnavailable(
            f"the judge model declined to score this call "
            f"(stop_reason=refusal, details={getattr(response, 'stop_details', None)}). "
            f"Scenario {call.scenario_id}."
        )

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise JudgeUnavailable(
            f"the judge returned no text block for {call.scenario_id} "
            f"(stop_reason={response.stop_reason})"
        )

    parsed = json.loads(text)
    return _assemble(call, base, parsed, recorder)


def _assemble(
    call: Transcript, base: dict[str, Any], parsed: dict[str, Any], recorder: Any
) -> dict[str, Any]:
    """Fold the judge's raw scores into a result, with the deterministic
    anchor check alongside the judged one."""
    by_id = {entry["rubricId"]: entry for entry in parsed.get("rubrics", [])}

    rubrics: dict[str, Any] = {}
    weighted_sum = 0.0
    weight_total = 0
    breaches: list[str] = []
    gate_breaches: list[str] = []

    for spec in testbed.rubrics():
        rubric_id = spec["id"]
        entry = by_id.get(rubric_id)
        if entry is None:
            # A rubric the judge skipped. Recorded, not silently dropped: a
            # missing rubric changes the overall mean and would otherwise look
            # like the agent improved.
            rubrics[rubric_id] = {
                "score": None,
                "missing": True,
                "justification": "the judge returned no entry for this rubric",
            }
            continue

        score = float(entry["score"])
        rubrics[rubric_id] = {
            "score": score,
            "threshold": spec["threshold"],
            "applicable": bool(entry.get("applicable", True)),
            "justification": entry.get("justification", ""),
            "transcriptEvidence": entry.get("transcriptEvidence", ""),
            "manualEvidence": entry.get("manualEvidence", ""),
            "gate": bool(spec.get("gate", False)),
        }

        weighted_sum += score * int(spec["weight"])
        weight_total += int(spec["weight"])

        if score < float(spec["threshold"]):
            breaches.append(rubric_id)
            if spec.get("gate"):
                gate_breaches.append(rubric_id)

    expect = call.expect_anchors()
    cited = anchors.cited_anchors(call.full_answer, expect)

    result = {
        **base,
        "scored": True,
        "overall": round(weighted_sum / weight_total, 3) if weight_total else None,
        "rubrics": rubrics,
        "breaches": breaches,
        "gateBreaches": gate_breaches,
        # The deterministic count, kept beside the judged one on purpose. When
        # they disagree it is worth knowing which: the matcher is literal and
        # the judge is not, so "judge says covered, matcher says not" usually
        # means the agent paraphrased a fact the matcher has no spoken form for,
        # and that is a gap in anchors.py rather than in the agent.
        "anchors": {
            "expected": expect,
            "citedDeterministically": cited,
            "coverage": round(len(cited) / len(expect), 3) if expect else None,
        },
    }

    if recorder:
        recorder.add_call(result)
    return result
