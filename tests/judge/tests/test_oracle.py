"""
ORC-01..10 - the oracle's own regression suite.

Offline, no credentials, no network, no model. This is the half that stops the
expensive half scoring confident nonsense: a deterministic oracle is only worth
gating on if its grammar, its compiled index and its applicability rule are
themselves under test. Two of the cases below (ORC-02, ORC-03) are regressions
on bugs this repo has already been bitten by, both of which failed SILENTLY -
they scored a correct answer as uncited rather than raising.
"""

from __future__ import annotations

import json

import pytest

from src import anchors, numerals, oracle, testbed
from src.transcript import Transcript, Turn, load_recordings

pytestmark = pytest.mark.offline


# ---------------------------------------------------------------------------
# ORC-01  the spoken-number grammar round-trips
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value", [0, 7, 12, 19, 20, 21, 40, 99, 100, 240, 400, 600, 1000, 2500, 12000, 999999]
)
def test_orc01_spelled_integers_parse_back(value: int) -> None:
    """Every form anchors.py generates, numerals.py must read.

    These two are the same grammar used in opposite directions - one to look
    for a known fact, one to find unknown ones - and if they disagree the
    matcher and the fabrication check disagree about the same utterance.
    """
    forms = anchors.spell_integer(value)
    assert forms, f"no spelling generated for {value}"
    for form in forms:
        parsed = numerals.parse_number_words(form.split())
        assert parsed == float(value), f"{form!r} parsed as {parsed}, expected {value}"


def test_orc01_decimals_and_voice_forms() -> None:
    assert numerals.parse_number_words("zero point four zero".split()) == 0.4
    assert numerals.parse_number_words("twenty five hundred".split()) == 2500.0
    assert numerals.parse_number_words("two thousand five hundred".split()) == 2500.0
    assert numerals.parse_number_words(["and"]) is None


def test_orc01_extraction_covers_both_spellings() -> None:
    spoken = numerals.extract("we cap it at four hundred feet per minute")
    written = numerals.extract("we cap it at 400 FPM")
    assert [m.key for m in spoken] == [m.key for m in written] == [(400.0, "fpm")]


def test_orc01_non_measurements_are_not_measurements() -> None:
    """The whitelist problem, solved by construction rather than by a list.

    Step numbers, item references and the support phone number carry no unit,
    so a (value, unit) extractor never sees them. That is why this closed-world
    check can be strict without a growing list of exceptions.
    """
    noise = (
        "Step one: shut off the machine. The Traction Control switch (item 36) "
        "is a maintained switch. Contact Etnyre service at 888-586-1899."
    )
    assert numerals.extract(noise) == []


# ---------------------------------------------------------------------------
# ORC-02  bounded matching - the silent over-credit
# ---------------------------------------------------------------------------

def test_orc02_zero_anchors_do_not_match_inside_larger_numbers() -> None:
    """`0 PSI` is a real anchor - the KBs use it for 'you should read nothing
    here'. Matched as a substring it fires inside `400 PSI`, and the answer
    that cited the charge pressure gets credit for citing the zero reading too."""
    assert not anchors.cites_anchor("charge pressure reads 400 PSI", "0 PSI")
    assert anchors.cites_anchor("the gauge reads 0 PSI at the port", "0 PSI")
    assert not anchors.cites_anchor("it draws 10.00 amps", "0.00 amps")
    assert anchors.cites_anchor("it reads 0.00 amps", "0.00 amps")


def test_orc02_extractor_is_bounded_too() -> None:
    assert [m.key for m in numerals.extract("400 PSI")] == [(400.0, "psi")]
    assert [m.key for m in numerals.extract("10.00 amps")] == [(10.0, "amp")]


# ---------------------------------------------------------------------------
# ORC-03  escaping - the other silent failure
# ---------------------------------------------------------------------------

def test_orc03_hyphenated_anchors_still_compile_to_something_that_matches() -> None:
    """Escape-then-substitute turned `P1-PIN 21` into a pattern matching
    nothing, and scored every pin-reference anchor as uncited without raising."""
    for text in ("check P1-PIN 21", "check P1 PIN 21", "check p1-pin 21"):
        assert anchors.cites_anchor(text, "P1-PIN 21"), text
    assert numerals.part_references("check P1-PIN 21") == ["P1-PIN 21"]


# ---------------------------------------------------------------------------
# ORC-04  the differential index
# ---------------------------------------------------------------------------

def test_orc04_forbidden_never_overlaps_allowed() -> None:
    """A figure cannot be both this machine's and foreign to it. If it can, the
    cross-family check fails a correct answer, which is the fastest way to get
    a safety gate switched off again."""
    for kb_id, block in oracle.differential()["byKb"].items():
        allowed = oracle.allowed_measurements(kb_id)
        overlap = sorted(set(block["forbidden"]) & allowed)
        assert not overlap, f"{kb_id}: {overlap} is both allowed and forbidden"


def test_orc04_every_forbidden_figure_belongs_to_a_real_machine() -> None:
    corpus = oracle.corpus()
    for kb_id, block in oracle.differential()["byKb"].items():
        for key, owners in block["forbidden"].items():
            assert owners, f"{kb_id}: {key} is forbidden but attributed to nobody"
            for owner in owners:
                assert key in corpus["byKb"][owner]["measurements"], (
                    f"{kb_id}: {key} attributed to {owner}, which does not state it"
                )


def test_orc04_differential_is_not_empty() -> None:
    """A silently empty index would make crossFamilyForbidden pass everything -
    coverage that cannot fail, which reads as a green gate and is not one."""
    for kb_id, block in oracle.differential()["byKb"].items():
        assert block["forbidden"], f"{kb_id} has no foreign figures at all - suspicious"


# ---------------------------------------------------------------------------
# ORC-05  the unit table
# ---------------------------------------------------------------------------

def test_orc05_every_anchors_unit_resolves() -> None:
    for written, spoken_forms in anchors.UNITS.items():
        assert numerals.canonical_unit(written), f"{written!r} has no canonical unit"
        for form in spoken_forms:
            if form == '"':
                continue
            assert numerals.canonical_unit(form), f"{form!r} has no canonical unit"


def test_orc05_config_phrase_lists_are_declared_and_non_empty() -> None:
    cfg = oracle.oracle_config()
    for key in ("safetyPhrases", "escalationPhrases", "dontKnowPhrases"):
        assert cfg[key], f"oracle.{key} is empty - the check that reads it cannot fail"
        assert len(cfg[key]) < 25, f"oracle.{key} is too long to audit by eye"


def test_orc05_every_gate_ships_off() -> None:
    """Landing posture, asserted rather than remembered. Turning a gate on is
    then a deliberate commit that also edits this test."""
    gates = oracle.oracle_config()["gates"]
    on = sorted(k for k, v in gates.items() if v)
    assert not on, f"gates enabled without a baseline: {on}"


# ---------------------------------------------------------------------------
# ORC-06  index completeness
# ---------------------------------------------------------------------------

def test_orc06_every_scenario_has_an_oracle_entry() -> None:
    entries = oracle.index()["entries"]
    for scenario in testbed.all_scenarios():
        assert scenario["id"] in entries, f"{scenario['id']} missing from oracle.json"
    assert len(entries) == len(testbed.all_scenarios())


def test_orc06_coverage_counts_match_the_entries() -> None:
    """The coverage block is what the test plan quotes. A stale one is worse
    than none: it reports checking that is not happening."""
    entries = oracle.index()["entries"].values()
    coverage = oracle.index()["coverage"]
    assert coverage["scenarios"] == len(list(entries))
    assert coverage["withAnchors"] == sum(1 for e in entries if not e["structuralOnly"])
    assert coverage["stepOrderCheckable"] == sum(1 for e in entries if e["stepOrderCheckable"])
    assert coverage["safetyRequired"] == sum(1 for e in entries if e["safetyRequired"])
    assert coverage["escalate"] == sum(1 for e in entries if e["escalate"])


def test_orc06_structural_only_scenarios_are_declared_not_hidden() -> None:
    """Scenarios with no checkable fact are a real gap. They are tagged so the
    gap is visible, rather than silently passing every content check."""
    entries = oracle.index()["entries"].values()
    structural = [e for e in entries if e["structuralOnly"]]
    for e in structural:
        assert e["requiredAnchors"] == []
        assert e["anchorSource"] == "none"
    assert structural, "expected some entries to carry no measurable fact"


# ---------------------------------------------------------------------------
# ORC-07  the compiled index still agrees with the live grammar
# ---------------------------------------------------------------------------

def test_orc07_corpus_matches_a_fresh_parse() -> None:
    """The artefact is generated at build time and trusted at assertion time.
    This is the check that stops it going stale after a KB edit without a
    `make resources` - the failure mode where the oracle keeps gating happily
    against a manual that no longer says what it thinks."""
    corpus = oracle.corpus()
    for kb in testbed.knowledge_bases():
        text = testbed.kb_path(kb).read_text(encoding="utf-8")
        fresh = sorted({f"{m.key[0]:g}|{m.key[1]}" for m in numerals.extract(text)})
        assert fresh == corpus["byKb"][kb["id"]]["measurements"], (
            f"{kb['id']}: corpus-numerals.json is stale - run `make resources`"
        )


# ---------------------------------------------------------------------------
# ORC-08  applicability
# ---------------------------------------------------------------------------

def _call(turns: list[Turn], scenario_id: str = "VHRS28-HOW-003") -> Transcript:
    scenario = testbed.scenario_by_id(scenario_id)
    return Transcript(
        scenario_id=scenario_id,
        kb_id=scenario["kbId"],
        serial="K7170",
        controller="RC28",
        question=scenario["question"],
        turns=turns,
    )


def test_orc08_a_run_that_never_reached_the_answer_is_not_a_failure() -> None:
    question = testbed.scenario_by_id("VHRS28-HOW-003")["question"]
    call = _call(
        [
            Turn("agent", "Hi, this is Jason with Etnyre Customer Support."),
            Turn("caller", question),
            Turn("agent", "Can you tell me a bit more about when this happens?", intent="clarifying"),
        ]
    )
    applicable, reason = oracle.applicability(call)
    assert not applicable, reason
    verdict = oracle.required_anchors(call.full_answer, call.scenario_id, applicable)
    assert verdict.status == oracle.NA
    assert not verdict.failed


def test_orc08_the_sms_accept_path_is_excluded() -> None:
    question = testbed.scenario_by_id("VHRS28-HOW-003")["question"]
    call = _call(
        [
            Turn("caller", question),
            Turn("agent", "I can text you the full list of troubleshooting steps."),
            Turn("caller", "Yes, that would be helpful - please send it to 720-555-0198.", intent="offersToText"),
            Turn("agent", "Sent. " + "Let me know how you get on. " * 4),
        ]
    )
    applicable, reason = oracle.applicability(call)
    assert not applicable and "left the chat" in reason


def test_orc08_a_run_that_reached_the_answer_is_applicable() -> None:
    question = testbed.scenario_by_id("VHRS28-HOW-003")["question"]
    call = _call(
        [
            Turn("caller", question),
            Turn(
                "agent",
                "Install a 1000 PSI gauge in port G. At low idle the charge "
                "pressure should read about 400 PSI. If it reads near 0 PSI the "
                "charge pump has failed - contact Etnyre service at 888-586-1899.",
            ),
        ]
    )
    applicable, reason = oracle.applicability(call)
    assert applicable, reason


# ---------------------------------------------------------------------------
# ORC-09/10  end to end, against the synthetic recordings
# ---------------------------------------------------------------------------

def _recordings_by_expectation() -> dict[str, list[Transcript]]:
    out: dict[str, list[Transcript]] = {"high": [], "low": []}
    for path_call in load_recordings():
        raw = json.loads(open(path_call.source, encoding="utf-8").read())
        out.setdefault(raw.get("_expect", "high"), []).append(path_call)
    return out


def test_orc09_a_faithful_call_fails_nothing() -> None:
    """The synthetic faithful call is traceable to vhrs28.md line by line. A
    deterministic oracle that flags it is over-strict, and over-strict is how a
    content gate gets switched off - so this is the false-positive guard."""
    calls = _recordings_by_expectation()["high"]
    if not calls:
        pytest.skip("no faithful recording on disk")
    for call in calls:
        failures = [v for v in oracle.evaluate(call) if v.failed]
        assert not failures, "\n".join(f"{v.check}: {v.summary} {v.evidence}" for v in failures)


def test_orc10_a_defective_call_is_caught_without_a_model() -> None:
    calls = _recordings_by_expectation()["low"]
    if not calls:
        pytest.skip("no defective recording on disk")
    for call in calls:
        failures = [v for v in oracle.evaluate(call) if v.failed]
        assert failures, f"{call.source} is a known-bad call and nothing caught it"


def test_orc10_the_oracle_is_deterministic() -> None:
    """Scored twice, byte-identical. The property the whole design rests on -
    and the one that makes a red build worth investigating rather than re-running."""
    for call in load_recordings():
        first = [v.to_dict() for v in oracle.evaluate(call)]
        second = [v.to_dict() for v in oracle.evaluate(call)]
        assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# ---------------------------------------------------------------------------
# ORC-11/12  the two gate candidates have a fixture that makes them fail
# ---------------------------------------------------------------------------

def _fabricated() -> Transcript:
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "recordings" / "synthetic-vhrs28-wont-drive-fabricated.json"
    if not path.exists():
        pytest.skip("fabrication fixture not on disk")
    return Transcript.load(path)


def test_orc11_a_fabricated_specification_is_caught_spoken_or_written() -> None:
    """The check that is meant to gate first, with the fixture that proves it
    can fail. `975 PSI` is in no manual we hold, and the agent says it the way
    a voice agent does - "nine hundred and seventy five PSI" - so this also
    asserts the spoken path, which is the one a digits-only extractor misses."""
    verdict = next(
        v for v in oracle.evaluate(_fabricated()) if v.check == "numericProvenance"
    )
    assert verdict.failed, verdict.summary
    assert any("975" in e for e in verdict.evidence), verdict.evidence


def test_orc12_a_foreign_figure_is_caught_and_attributed() -> None:
    """1500 PSI is a real specification - for an FHRC machine. Quoted to a
    VHRS28 caller it is the cross-contamination defect, and the verdict has to
    name whose figure it is or nobody can act on it."""
    verdict = next(
        v for v in oracle.evaluate(_fabricated()) if v.check == "crossFamilyForbidden"
    )
    assert verdict.failed, verdict.summary
    assert any("fhrc" in e for e in verdict.evidence), verdict.evidence


def test_orc12_a_correct_answer_is_not_flagged_as_foreign() -> None:
    """The false-positive side of the same check: every figure in the faithful
    call belongs to this machine, so the differential must stay silent."""
    for call in _recordings_by_expectation()["high"]:
        verdict = next(v for v in oracle.evaluate(call) if v.check == "crossFamilyForbidden")
        assert not verdict.failed, verdict.evidence


@pytest.mark.offline
@pytest.mark.parametrize(
    "text,expected",
    [
        ("two hundred and five hundred feet per minute", [(200.0, "fpm"), (500.0, "fpm")]),
        ("three hundred eighty and four hundred twenty PSI", [(380.0, "psi"), (420.0, "psi")]),
        ("two hundred and five PSI", [(205.0, "psi")]),
        ("fifty five to sixty PSI", [(55.0, "psi"), (60.0, "psi")]),
        ("one thousand nine hundred to two thousand one hundred PSI", [(1900.0, "psi"), (2100.0, "psi")]),
        ("step two to open the valve at 400 PSI", [(400.0, "psi")]),
    ],
)
def test_orc01b_spoken_pairs_and_ranges_are_two_numbers(text, expected):
    """ORC-01b. VERIFIED 2026-09-28 on live calls: "two hundred and five hundred
    feet per minute" was read as 20,500 FPM and "three hundred eighty and four
    hundred twenty PSI" as 38,420 PSI, failing numericProvenance on correct
    answers. "and" continues a number only into a smaller part; a number joined
    to a measurement by and/or/to shares its unit, so both ends of a range are
    checked."""
    assert [(m.value, m.unit) for m in numerals.extract(text)] == expected


@pytest.mark.offline
@pytest.mark.parametrize(
    "text,expected",
    [
        ("A: 1300 PSI (acceptable range: 1200–1400 PSI).", [(1300.0, "psi"), (1200.0, "psi"), (1400.0, "psi")]),
        ("Typical chip spreading is done at 200–500 FPM", [(200.0, "fpm"), (500.0, "fpm")]),
        ("2,000 PSI (acceptable range: 1,900–2,100 PSI)", [(2000.0, "psi"), (1900.0, "psi"), (2100.0, "psi")]),
        ("Step 3 - 400 PSI charge", [(400.0, "psi")]),
        ("Contact 1-800-995-2116 at 400 PSI", [(400.0, "psi")]),
    ],
)
def test_orc01c_both_ends_of_a_written_range_carry_the_unit(text, expected):
    """ORC-01c. The KBs write ranges as "1200–1400 PSI"; only the high end used
    to be compiled, so a correct spoken range read as half wrong. A spaced dash
    is punctuation, not a range."""
    assert [(m.value, m.unit) for m in numerals.extract(text)] == expected


@pytest.mark.offline
@pytest.mark.parametrize(
    "text,expected",
    [
        ("one quarter inch chips, three eighths inch chips, five eighths inch chips, and one inch chips",
         [(0.25, "inch"), (0.375, "inch"), (0.625, "inch"), (1.0, "inch")]),
        ("a clearance of one sixteenth of an inch", [(0.0625, "inch")]),
        ("a one and a half inch wrench", [(1.5, "inch")]),
    ],
)
def test_orc01d_spoken_fractions_of_an_inch(text, expected):
    """ORC-01d. VERIFIED 2026-09-28 (FHRC28-FAQ-041): the agent read the KB's
    1/4", 3/8", 5/8" aggregate sizes aloud and only "one inch" was parsed."""
    assert sorted((m.value, m.unit) for m in numerals.extract(text)) == sorted(expected)


@pytest.mark.offline
@pytest.mark.parametrize(
    "text,expected",
    [
        ("zero point nine zero zero and one point zero zero zero amps", [(0.9, "amp"), (1.0, "amp")]),
        ("should be between 0.900 and 1.000 amp", [(0.9, "amp"), (1.0, "amp")]),
        ("Check P1-PIN 21 and 400 PSI", [(400.0, "psi")]),
    ],
)
def test_orc01e_decimal_pairs_and_between_ranges(text, expected):
    """ORC-01e. VERIFIED 2026-09-28 (FHRC36/VHRS36-HOW-018, gate flutter): the KB
    says "between 0.900 and 1.000 amp", the agent said "zero point nine zero zero
    and one point zero zero zero amps" - both read as 0.9 A alone, failing a
    correct answer. "and" makes a range only after "between"."""
    assert sorted((m.value, m.unit) for m in numerals.extract(text)) == sorted(expected)


@pytest.mark.offline
@pytest.mark.parametrize(
    "text,expected",
    [
        ("fifty five and sixty PSI", [(55.0, "psi"), (60.0, "psi")]),
        ("sixty and sixty five PSI", [(60.0, "psi"), (65.0, "psi")]),
        ("two hundred and five PSI", [(205.0, "psi")]),
        ("one thousand and fifty PSI", [(1050.0, "psi")]),
        ("two hundred and five hundred feet per minute", [(200.0, "fpm"), (500.0, "fpm")]),
    ],
)
def test_orc01f_and_joins_one_number_only_after_hundred_or_thousand(text, expected):
    """ORC-01f. VERIFIED 2026-09-28 (VHRS36 interview): "fifty five and sixty PSI"
    - a correct tire pressure answer - was read as 115 PSI and failed as invented."""
    assert sorted((m.value, m.unit) for m in numerals.extract(text)) == sorted(expected)


def test_orc01g_a_zero_reading_is_not_a_figure_to_trace():
    """ORC-01g. "RPM shows 0" is how vhrs28 writes it; "zero RPM" in an answer
    must neither fail provenance nor count as another machine's figure. A
    non-zero invented figure next to it still fails (VERIFIED 2026-09-28)."""
    answer = "If the engine is running but the display shows zero RPM, the engine CAN link is broken."
    assert oracle.numeric_provenance(answer, "vhrs28").status != oracle.FAIL
    assert oracle.cross_family(answer, "vhrs28").status != oracle.FAIL
    assert oracle.numeric_provenance(answer + " Set it to 4321 RPM.", "vhrs28").status == oracle.FAIL
