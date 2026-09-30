"""
The deterministic half of the judge: a verdict that is a pure function of the
transcript.

`scorer.py` asks a model whether an answer is faithful to a manual. It is the
right tool for a question with no crisp answer, and it is why it reports rather
than gates. This module asks the questions that DO have crisp answers:

    Did the agent say a number that appears in no manual we hold?
    Did it quote a figure that belongs to a different machine?
    Did it reach the facts the manual commits to?
    Did the safety line come before the first step, or after it?

None of those need a model. They need the knowledge bases compiled into an
index - which tools/oracle_build.py does at `make resources` time - and string
and number matching against it. Same transcript in, same verdict out, on any
machine, offline, forever. That is what makes these gateable where a score is
not.

Two design rules, both learned from what is already in this repo:

1. EVERY VERDICT CARRIES EVIDENCE. A check that returns False and nothing else
   cannot be argued with, and an argument is how a threshold gets re-based from
   a guess to a measurement. Each Verdict carries the spans it found and the
   spans it wanted.

2. A CHECK THAT COULD NOT APPLY IS `notApplicable`, NEVER `fail`. The agent is a
   stepwise walkthrough: on the accept-the-SMS path the procedure leaves the
   chat entirely, so the manual's numbers never enter the transcript. Failing
   an anchor check on that run measures the harness, not the agent. This is the
   exact reason assertions.checkExpectedAnchors ships off today, and
   `applicability()` is the fix - not a looser assertion.

Gating is deliberately NOT decided here. `gate()` reads config.oracle.gates,
every entry of which ships false, so this lands reporting-only beside
judge.requireScoreGate and rateLimit.saturation.requireEnforcement. Turn one on
when its baseline says so.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Iterable

from . import anchors, numerals, testbed
from .transcript import Transcript

PASS = "pass"
FAIL = "fail"
NA = "notApplicable"


# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    """One check, its outcome, and what it saw."""

    check: str
    status: str
    summary: str
    evidence: list[str] = field(default_factory=list)
    expected: list[str] = field(default_factory=list)
    citation: str | None = None

    @property
    def failed(self) -> bool:
        return self.status == FAIL

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "status": self.status,
            "summary": self.summary,
            "evidence": self.evidence,
            "expected": self.expected,
            "citation": self.citation,
        }


# ---------------------------------------------------------------------------
# Config and compiled artefacts
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, Any] = {
    "enabled": True,
    "gates": {},
    "nonAnswerIntents": [
        "clarifying",
        "asksForSerial",
        "readsBackSerial",
        "readsBackPhone",
        "asksForFeedback",
        "readyForQuestion",
        "farewell",
    ],
    "applicability": {
        "minAnswerChars": 40,
        "minAgentTurns": 1,
        "requireQuestionAsked": True,
        "skipTextOfferAccepted": True,
    },
    "aggregate": {
        "runs": 5,
        "requiredAnchorsPassRate": 0.8,
        "minApplicabilityRate": 0.4,
    },
    "safetyPhrases": [
        "shut off the machine",
        "shut the machine off",
        "turn the machine off",
        "turn off the machine",
        "engine off",
        "lock out",
        "lockout",
        "tag out",
        "tagout",
        "before servicing",
    ],
    "escalationPhrases": [
        "contact etnyre",
        "etnyre service",
        "888-586-1899",
        "eight eight eight",
    ],
    "dontKnowPhrases": [
        "i don't have",
        "i do not have",
        "not in the manual",
        "i'm not able to",
        "i am not able to",
        "i don't know",
        "i do not know",
        "can't confirm",
        "cannot confirm",
    ],
    "reportPath": "report/data/oracle-verdicts.json",
}


@lru_cache(maxsize=1)
def oracle_config() -> dict[str, Any]:
    """config.oracle, over DEFAULTS. Absent block = defaults, all gates off."""
    cfg = dict(DEFAULTS)
    declared = testbed.config().get("oracle") or {}
    for key, value in declared.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict) and isinstance(cfg.get(key), dict):
            merged = dict(cfg[key])
            merged.update({k: v for k, v in value.items() if not k.startswith("_")})
            cfg[key] = merged
        else:
            cfg[key] = value
    return cfg


def _generated(name: str) -> dict[str, Any]:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    path = root / testbed.config()["resources"]["generatedDir"] / name
    if not path.exists():
        raise FileNotFoundError(
            f"{path} is missing - run `make resources`. The oracle is compiled "
            f"from the knowledge bases, not parsed at assertion time."
        )
    import json

    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def index() -> dict[str, Any]:
    return _generated("oracle.json")


@lru_cache(maxsize=1)
def corpus() -> dict[str, Any]:
    return _generated("corpus-numerals.json")


@lru_cache(maxsize=1)
def differential() -> dict[str, Any]:
    return _generated("differential-index.json")


def entry(scenario_id: str) -> dict[str, Any] | None:
    return index()["entries"].get(scenario_id)


@lru_cache(maxsize=16)
def allowed_measurements(kb_id: str) -> frozenset[str]:
    """This machine's measurements, unioned with the shared general guide."""
    data = corpus()
    keys = set(data["byKb"].get(kb_id, {}).get("measurements", []))
    for shared in data.get("shared", []):
        keys |= set(data["byKb"].get(shared, {}).get("measurements", []))
    return frozenset(keys)


@lru_cache(maxsize=16)
def allowed_parts(kb_id: str) -> frozenset[str]:
    data = corpus()
    keys = set(data["byKb"].get(kb_id, {}).get("parts", []))
    for shared in data.get("shared", []):
        keys |= set(data["byKb"].get(shared, {}).get("parts", []))
    return frozenset(keys)


@lru_cache(maxsize=16)
def allowed_values(kb_id: str) -> frozenset[float]:
    """Values without their units - used only to tell a unit swap apart from an
    invention, because the two are different defects with different fixes."""
    return frozenset(
        float(key.split("|", 1)[0]) for key in allowed_measurements(kb_id)
    )


def forbidden_measurements(kb_id: str) -> dict[str, list[str]]:
    return differential()["byKb"].get(kb_id, {}).get("forbidden", {})


# ---------------------------------------------------------------------------
# Applicability
# ---------------------------------------------------------------------------


def substantive_answer(call: Transcript) -> str:
    """The agent's answer with the call handling taken out.

    An agent turn the driver matched to `clarifying`, `asksForSerial` or
    `asksForFeedback` is the agent running the call, not answering the
    question. Counting those towards "did the reply carry a fact" is how a
    conversation that consisted entirely of follow-up questions reads as a
    substantive answer that happened to omit every number - a confident zero
    that describes the harness.

    `full_answer` is deliberately left alone: the LLM judge wants the whole
    thing, including the preamble it is asked not to penalise.
    """
    skip = set(oracle_config().get("nonAnswerIntents") or [])
    start = call.question_index()
    turns = call.turns if start is None else call.turns[start + 1 :]
    return "\n\n".join(
        t.text.strip()
        for t in turns
        if t.speaker == "agent" and not t.idle and (t.intent or "") not in skip
    ).strip()


def applicability(call: Transcript) -> tuple[bool, str]:
    """
    Whether this run could have carried the manual's facts at all.

    A run that never reached the answer must not be scored as though the agent
    withheld it. Three ways that happens, all observed on etnyre-dev:

      * the call ended before the question landed;
      * every agent turn was a clarifying question;
      * the caller accepted the texted steps, so the procedure left the chat.

    Returns (applicable, reason). The reason is recorded either way - a rising
    rate of inapplicable runs is itself a finding, because it means the
    conversation contract drifted and the harness stopped reaching answers.
    """
    rules = oracle_config()["applicability"]

    if rules.get("requireQuestionAsked", True) and call.question_index() is None:
        return False, "the scenario question never appears in the transcript"
    if call.answer_turn_count < int(rules.get("minAgentTurns", 1)):
        return False, "no agent turn followed the question"

    answer = substantive_answer(call)
    if len(answer) < int(rules.get("minAnswerChars", 40)):
        return False, (
            f"only {len(answer)} chars of the reply were an answer - the rest was "
            f"clarifying questions and call handling"
        )
    if rules.get("skipTextOfferAccepted", True):
        for turn in call.turns:
            if turn.speaker == "caller" and turn.intent == "offersToText":
                if re.search(r"\b(yes|please send|that would be helpful)\b", turn.text, re.I):
                    return False, "caller accepted the texted steps - the procedure left the chat"
    return True, "reached the answer"


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def _identifying(measurement: numerals.Measurement) -> bool:
    """A zero is a reading ("RPM shows 0", "0.00 amps"), not a specification a
    manual owns, so it can prove neither provenance nor another machine's
    manual. VERIFIED 2026-09-28: vhrs28 says "if engine is running but RPM
    shows 0" (unit before number, so never indexed as 0 rpm), and a correct
    "zero RPM" failed both checks. A wrong zero given AS the answer to a
    question is still caught by sectionValues."""
    return measurement.value != 0


def numeric_provenance(answer: str, kb_id: str) -> Verdict:
    """Every measurement uttered must exist in this machine's manuals."""
    allowed = allowed_measurements(kb_id)
    found = [m for m in numerals.extract(answer) if _identifying(m)]
    if not found:
        return Verdict(
            "numericProvenance", NA, "the answer states no measurement", [], []
        )

    unsupported = [m for m in found if numerals_key(m) not in allowed]
    if not unsupported:
        return Verdict(
            "numericProvenance",
            PASS,
            f"all {len(found)} measurements trace to {kb_id}",
            [m.raw for m in found],
        )
    return Verdict(
        "numericProvenance",
        FAIL,
        f"{len(unsupported)} of {len(found)} measurements appear in no manual for {kb_id}",
        [f"{m.raw!r} -> {m}" for m in unsupported],
        citation=f"corpus-numerals.json:{kb_id}",
    )


def numerals_key(measurement: numerals.Measurement) -> str:
    """The same key tools/oracle_build.py compiled the corpus with."""
    return numerals.key_of(measurement)


def unit_consistency(answer: str, kb_id: str) -> Verdict:
    """A corpus-valid number spoken with the wrong unit.

    Separated from numericProvenance because `400 PSI` where the manual says
    `400 FPM` is a different failure from inventing 900 PSI: the agent found
    the right fact and mangled it, which points at the retrieval formatting
    rather than at hallucination. Both fail; they should not read the same.
    """
    allowed = allowed_measurements(kb_id)
    values = allowed_values(kb_id)
    swaps = [
        m
        for m in numerals.extract(answer)
        if numerals_key(m) not in allowed and round(m.value, 4) in values
    ]
    if not swaps:
        return Verdict("unitConsistency", PASS, "no unit swaps", [])
    return Verdict(
        "unitConsistency",
        FAIL,
        f"{len(swaps)} value(s) stated with a unit the manual does not pair them with",
        [f"{m.raw!r} -> {m}" for m in swaps],
        citation=f"corpus-numerals.json:{kb_id}",
    )


def part_provenance(answer: str, kb_id: str) -> Verdict:
    allowed = allowed_parts(kb_id)
    found = numerals.part_references(answer)
    if not found:
        return Verdict("partProvenance", NA, "the answer cites no part or pin reference")
    unsupported = [p for p in found if p not in allowed]
    if not unsupported:
        return Verdict(
            "partProvenance", PASS, f"all {len(found)} part references trace to {kb_id}", found
        )
    return Verdict(
        "partProvenance",
        FAIL,
        f"{len(unsupported)} part/pin reference(s) appear in no manual for {kb_id}",
        unsupported,
        citation=f"corpus-numerals.json:{kb_id}",
    )


def cross_family(answer: str, kb_id: str) -> Verdict:
    """A figure that belongs to a different machine and not to this one."""
    forbidden = forbidden_measurements(kb_id)
    if not forbidden:
        return Verdict("crossFamilyForbidden", NA, f"{kb_id} has no differential index")

    hits: list[str] = []
    for measurement in numerals.extract(answer):
        key = numerals_key(measurement)
        if key in forbidden and _identifying(measurement):
            owners = ", ".join(forbidden[key])
            hits.append(f"{measurement.raw!r} ({measurement}) belongs to {owners}")
    if not hits:
        return Verdict("crossFamilyForbidden", PASS, "no foreign figures", [])
    return Verdict(
        "crossFamilyForbidden",
        FAIL,
        f"{len(hits)} figure(s) from another machine were quoted to a {kb_id} caller",
        hits,
        citation=f"differential-index.json:{kb_id}",
    )


def cited_anchors(answer: str, wanted: list[str]) -> tuple[list[str], set[str]]:
    """Which facts the reply cites, allowing a unit to be elided once it is
    established.

    The strict matcher wants `0 PSI` or "zero PSI". Real speech does not repeat
    a unit it has already set up: "install a one thousand PSI gauge... that
    should read approximately four hundred PSI. If it's sitting near zero, the
    charge pump has failed" states the zero reading perfectly clearly, and a
    strict matcher calls it missing. That single false negative is enough to
    fail a faithful call, and a content check that fails faithful calls is one
    that gets switched off - which is the state CHT-06 is in today.

    So a bare number counts, but only under two constraints that keep it from
    becoming a check that cannot fail:

      * the unit must already be ESTABLISHED in the same answer by another
        measurement carrying it, and
      * the bare number must not sit inside a measurement of a DIFFERENT unit,
        or `400 PSI` would satisfy an anchor of `400 FPM` and quietly mask the
        unit swap that unitConsistency exists to catch.

    Returns (cited, the subset credited by elision) so a report can show which
    credits were soft.
    """
    cited = list(anchors.cited_anchors(answer, wanted))
    elided: set[str] = set()
    outstanding = [a for a in wanted if a not in cited]
    if not outstanding:
        return cited, elided

    present = numerals.extract(answer)
    established = {m.unit for m in present}

    for anchor in outstanding:
        parsed = numerals.extract(anchor)
        if not parsed:
            continue
        target = parsed[0]
        if target.unit not in established:
            continue
        number = f"{target.value:g}"
        for pattern in anchors.bare_number_patterns(number):
            for match in pattern.finditer(answer):
                inside_other_unit = any(
                    m.start <= match.start() < m.end and m.unit != target.unit
                    for m in present
                )
                if inside_other_unit:
                    continue
                cited.append(anchor)
                elided.add(anchor)
                break
            if anchor in cited:
                break
    return [a for a in wanted if a in cited], elided


def required_anchors(answer: str, scenario_id: str, applicable: bool = True) -> Verdict:
    facts = entry(scenario_id)
    if facts is None:
        return Verdict("requiredAnchors", NA, f"{scenario_id} is not in oracle.json")
    wanted = list(facts.get("requiredAnchors") or [])
    if not wanted:
        return Verdict(
            "requiredAnchors", NA, "this entry carries no checkable fact (structural only)"
        )
    if not applicable:
        return Verdict(
            "requiredAnchors", NA, "run did not reach the answer", expected=wanted
        )

    cited, elided = cited_anchors(answer, wanted)
    missing = [a for a in wanted if a not in cited]
    evidence = [f"{a} (unit elided)" if a in elided else a for a in cited]
    if not missing:
        return Verdict(
            "requiredAnchors", PASS, f"all {len(wanted)} facts cited", evidence, wanted
        )
    return Verdict(
        "requiredAnchors",
        FAIL,
        f"cited {len(cited)} of {len(wanted)} facts; missing {', '.join(missing)}",
        evidence,
        wanted,
        citation=f"oracle.json:{scenario_id}",
    )


def step_order(answer: str, scenario_id: str) -> Verdict:
    """Facts must appear in the order the manual's steps put them in."""
    facts = entry(scenario_id)
    if facts is None or not facts.get("stepOrderCheckable"):
        return Verdict("stepSequence", NA, "fewer than two steps carry a checkable fact")

    seen: list[tuple[int, int, str]] = []
    for item in facts["orderedAnchors"]:
        for pattern in anchors.anchor_patterns(item["anchor"]):
            match = pattern.search(answer)
            if match:
                seen.append((match.start(), int(item["step"]), item["anchor"]))
                break
    if len(seen) < 2:
        return Verdict("stepSequence", NA, "fewer than two of the ordered facts were cited")

    seen.sort()
    steps = [s for _, s, _ in seen]
    inversions = [
        f"{seen[i][2]} (step {steps[i]}) before {seen[i - 1][2]} (step {steps[i - 1]})"
        for i in range(1, len(steps))
        if steps[i] < steps[i - 1]
    ]
    if not inversions:
        return Verdict(
            "stepSequence",
            PASS,
            f"{len(seen)} facts delivered in manual order",
            [a for _, _, a in seen],
        )
    return Verdict(
        "stepSequence",
        FAIL,
        f"{len(inversions)} step inversion(s) - the procedure was reordered",
        inversions,
        citation=f"oracle.json:{scenario_id}",
    )


def _first_index(text: str, phrases: Iterable[str]) -> int | None:
    lowered = text.lower()
    hits = [lowered.find(p.lower()) for p in phrases]
    hits = [h for h in hits if h >= 0]
    return min(hits) if hits else None


def safety_preamble(answer: str, scenario_id: str) -> Verdict:
    """The safety line has to come BEFORE the first step, not after it.

    Position is the whole check. "Be careful out there" appended to the end of a
    procedure the caller has already carried out is not a safety instruction,
    and a presence-only assertion would score it as one.
    """
    facts = entry(scenario_id)
    if facts is None or not facts.get("safetyRequired"):
        return Verdict("safetyPreamble", NA, "this entry carries no safety instruction")

    cfg = oracle_config()
    where = _first_index(answer, cfg["safetyPhrases"])
    if where is None:
        return Verdict(
            "safetyPreamble",
            FAIL,
            "the manual entry carries a safety instruction; the answer states none",
            [],
            cfg["safetyPhrases"][:4],
            citation=f"oracle.json:{scenario_id}",
        )

    first_fact = None
    for anchor in facts.get("requiredAnchors") or []:
        for pattern in anchors.anchor_patterns(anchor):
            match = pattern.search(answer)
            if match and (first_fact is None or match.start() < first_fact):
                first_fact = match.start()
    if first_fact is None:
        found = numerals.extract(answer)
        first_fact = found[0].start if found else None

    if first_fact is None:
        return Verdict(
            "safetyPreamble", PASS, "safety instruction stated; no step facts to precede",
            [answer[where : where + 60]],
        )
    if where < first_fact:
        return Verdict(
            "safetyPreamble", PASS, "safety instruction precedes the first step fact",
            [answer[where : where + 60]],
        )
    return Verdict(
        "safetyPreamble",
        FAIL,
        "the safety instruction arrives after the caller has already been sent into the procedure",
        [answer[where : where + 60]],
        citation=f"oracle.json:{scenario_id}",
    )


def escalation(answer: str, scenario_id: str) -> Verdict:
    facts = entry(scenario_id)
    if facts is None or not facts.get("escalate"):
        return Verdict("escalation", NA, "this entry does not terminate in escalation")
    cfg = oracle_config()
    where = _first_index(answer, cfg["escalationPhrases"])
    if where is None:
        return Verdict(
            "escalation",
            FAIL,
            "the manual ends this entry by handing the caller to Etnyre; the answer never does",
            [],
            cfg["escalationPhrases"][:3],
            citation=f"oracle.json:{scenario_id}",
        )
    return Verdict("escalation", PASS, "escalation offered", [answer[where : where + 60]])


def refusal_on_unknown(answer: str) -> Verdict:
    """For a question no manual answers: cite nothing, and say so.

    Closed world, stated as an assertion: nothing to cite means nothing should
    be cited. A measurement in this answer is fabricated by construction,
    whatever it happens to be.
    """
    found = numerals.extract(answer)
    marker = _first_index(answer, oracle_config()["dontKnowPhrases"])
    if found:
        return Verdict(
            "refusalOnUnknown",
            FAIL,
            f"answered an unsupported question with {len(found)} measurement(s)",
            [f"{m.raw!r} -> {m}" for m in found],
        )
    if marker is None:
        return Verdict(
            "refusalOnUnknown",
            FAIL,
            "cited nothing, but never said it does not know",
            [],
            oracle_config()["dontKnowPhrases"][:3],
        )
    return Verdict(
        "refusalOnUnknown", PASS, "declined without inventing a figure",
        [answer[marker : marker + 60]],
    )


# ---------------------------------------------------------------------------
# Whole-call evaluation
# ---------------------------------------------------------------------------


def evaluate(call: Transcript) -> list[Verdict]:
    """Every applicable check, against one call."""
    answer = call.full_answer
    applicable, reason = applicability(call)
    verdicts = [
        Verdict(
            "applicability",
            PASS if applicable else NA,
            reason,
            [f"{call.answer_turn_count} agent turns, {len(answer)} chars"],
        )
    ]

    if entry(call.scenario_id) is None and not call.kb_id:
        verdicts.append(refusal_on_unknown(answer))
        return verdicts

    verdicts.extend(
        [
            numeric_provenance(answer, call.kb_id),
            unit_consistency(answer, call.kb_id),
            part_provenance(answer, call.kb_id),
            cross_family(answer, call.kb_id),
            required_anchors(answer, call.scenario_id, applicable),
            step_order(answer, call.scenario_id),
            safety_preamble(answer, call.scenario_id),
            escalation(answer, call.scenario_id),
        ]
    )
    return verdicts


def gate(verdicts: Iterable[Verdict]) -> tuple[bool, list[str]]:
    """
    Whether these verdicts should fail a build, per config.oracle.gates.

    Every gate ships false. That is not timidity, it is the same rule the rest
    of this repo already follows: a gate whose threshold was read off a manual
    rather than measured from calls goes red on a good deployment, and a gate
    that does that gets muted within a fortnight. Turn one on when its baseline
    says so - `crossFamilyForbidden` and `numericProvenance` first, because
    those two are the defects that can reach an operator.
    """
    gates = oracle_config()["gates"]
    breaches = [
        f"{v.check}: {v.summary}"
        for v in verdicts
        if v.failed and gates.get(v.check, False)
    ]
    return (not breaches), breaches


def aggregate(runs: list[list[Verdict]]) -> dict[str, Any]:
    """
    The statistic k runs of one scenario are gated on.

    A pure verdict function still sits downstream of a non-deterministic agent,
    so one run is not evidence. Zero-tolerance checks (a fabricated figure, a
    foreign figure) are counted raw: one is enough. Coverage checks are rated
    over the runs that were applicable, which is what stops a run that never
    reached the answer being counted as a withheld fact.
    """
    summary: dict[str, Any] = {}
    checks = {v.check for run in runs for v in run}
    for check in sorted(checks):
        outcomes = [v for run in runs for v in run if v.check == check]
        decided = [v for v in outcomes if v.status in (PASS, FAIL)]
        passed = [v for v in decided if v.status == PASS]
        summary[check] = {
            "runs": len(outcomes),
            "applicable": len(decided),
            "passed": len(passed),
            "failed": len(decided) - len(passed),
            "passRate": (len(passed) / len(decided)) if decided else None,
            "applicabilityRate": (len(decided) / len(outcomes)) if outcomes else None,
        }
    return summary
