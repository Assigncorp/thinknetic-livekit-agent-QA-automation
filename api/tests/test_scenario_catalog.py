"""
Scenario catalogue tests - the API-level scenario suite, with no agent calls.

These run in under a second and need no browser and no session. They guard the
data the expensive browser suite depends on: if a KB file is renamed, a serial
stops routing, or a scenario loses its question text, this goes red first and
names the exact cause, instead of a 45-second chat test failing with "the agent
did not reply".

Run before any @live suite. In CI this job gates the browser job.
"""

from __future__ import annotations

import re

import pytest

from src.utils import testbed

CONFIG = testbed.config()
KBS = testbed.knowledge_bases()
ROUTED_KBS = testbed.knowledge_bases(serial_routed_only=True)


# --------------------------------------------------------------------------
# Configuration integrity
# --------------------------------------------------------------------------

@pytest.mark.smoke
def test_config_declares_knowledge_bases():
    assert KBS, "no enabled knowledge bases in testbed.config.json"


@pytest.mark.smoke
@pytest.mark.parametrize("kb", KBS, ids=lambda k: k["id"])
def test_every_declared_kb_file_exists(kb):
    path = testbed.kb_path(kb)
    assert path.exists(), f"{kb['id']} declares {kb['file']}, which is not in resources/kb"
    assert path.stat().st_size > 1000, f"{path.name} is suspiciously small"


def test_kb_ids_are_unique():
    ids = [k["id"] for k in KBS]
    assert len(ids) == len(set(ids)), f"duplicate knowledge base ids: {ids}"


def test_serial_routing_is_unambiguous():
    """No two KBs may claim the same controller + hopper combination."""
    seen: dict[tuple[str, str], str] = {}
    for kb in ROUTED_KBS:
        key = (kb["controller"], kb["hopperType"])
        assert key not in seen, f"{kb['id']} and {seen[key]} both claim {key}"
        seen[key] = kb["id"]


def test_feedback_scale_is_usable():
    scale = CONFIG["chatFlow"]["feedbackScale"]
    assert scale["min"] <= scale["max"], f"feedbackScale is inverted: {scale}"
    assert scale["min"] >= 0, "a negative feedback score makes no sense"


def test_budgets_are_ordered_sensibly():
    b = CONFIG["budgets"]
    assert b["sessionConnectMs"] < b["answerMs"], "connecting should not be budgeted slower than a full answer"
    assert b["apiResponseMs"] < b["greetingMs"], "an API call should be budgeted faster than an LLM greeting"
    assert all(v > 0 for k, v in b.items() if not k.startswith("_")), "a budget of zero will never pass"
    assert b["machineIdentifiedMs"] >= b["greetingMs"], (
        "machineIdentifiedMs is cumulative from the start of the conversation and the "
        "greeting is inside it, so it can never be the tighter of the two"
    )


# --------------------------------------------------------------------------
# Serial index
# --------------------------------------------------------------------------

@pytest.mark.smoke
def test_serial_index_is_populated():
    assert testbed.serial_index()["serials"], "serial index is empty - run `make resources`"


@pytest.mark.parametrize("kb", ROUTED_KBS, ids=lambda k: k["id"])
def test_every_routed_kb_has_serials(kb):
    serials = testbed.serials_for(kb["id"])
    assert serials, f"no serials route to {kb['id']} - check the workbook sheets in config"


@pytest.mark.parametrize("kb", ROUTED_KBS, ids=lambda k: k["id"])
def test_anchor_serial_is_present_and_routes_correctly(kb):
    """The hand-checked serial for each KB must survive regeneration."""
    anchor = kb["anchorSerial"]
    assert anchor, f"{kb['id']} has no anchorSerial"
    match = [s for s in testbed.serials_for(kb["id"]) if s["serial"] == anchor]
    assert match, f"anchor serial {anchor} is not in the generated index for {kb['id']}"
    assert match[0]["controller"] == kb["controller"]
    assert match[0]["hopperType"] == kb["hopperType"]


def test_serials_are_globally_unique():
    serials = [s["serial"] for s in testbed.serial_index()["serials"]]
    dupes = {s for s in serials if serials.count(s) > 1}
    assert not dupes, f"a serial routes to more than one KB: {sorted(dupes)}"


def test_serials_look_like_part_numbers():
    bad = [s["serial"] for s in testbed.serial_index()["serials"] if not re.fullmatch(r"[A-Z]\d{4,6}", s["serial"])]
    assert not bad, f"serials that do not match the K-number shape: {bad[:10]}"


def test_excluded_serials_are_absent():
    excluded = {s.upper() for s in CONFIG["scenarioSelection"].get("excludeSerials", [])}
    present = {s["serial"] for s in testbed.serial_index()["serials"]} & excluded
    assert not present, f"excludeSerials are still in the index: {sorted(present)}"


# --------------------------------------------------------------------------
# Scenario pool
# --------------------------------------------------------------------------

@pytest.mark.smoke
def test_scenario_pool_is_populated():
    assert testbed.all_scenarios(), "no scenarios generated - run `make resources`"


@pytest.mark.parametrize("kb", ROUTED_KBS, ids=lambda k: k["id"])
def test_every_routed_kb_has_scenarios(kb):
    assert testbed.scenarios_for(kb["id"]), f"no scenarios extracted from {kb['file']}"


def test_scenario_ids_are_unique():
    ids = [s["id"] for s in testbed.all_scenarios()]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"duplicate scenario ids: {sorted(dupes)[:10]}"


def test_every_scenario_belongs_to_a_declared_kb():
    declared = {k["id"] for k in KBS}
    orphans = {s["kbId"] for s in testbed.all_scenarios()} - declared
    assert not orphans, f"scenarios reference unknown KBs: {orphans}"


def test_scenario_questions_are_usable_as_caller_prompts():
    minimum = CONFIG["scenarioExtraction"]["minQuestionLength"]
    bad = [
        s["id"]
        for s in testbed.all_scenarios()
        if len(s["question"].strip()) < minimum or s["question"].strip().startswith("#")
    ]
    assert not bad, f"scenarios whose question would not work as a caller prompt: {bad[:10]}"


def test_scenarios_carry_source_provenance():
    """Every scenario must be traceable back to a line in its KB file."""
    bad = [s["id"] for s in testbed.all_scenarios() if not s.get("section") or not s.get("sourceLine")]
    assert not bad, f"scenarios with no traceable source: {bad[:10]}"


ANCHOR_SHAPES = (
    re.compile(r"^[A-Z]{1,2}\d-PIN\s*\d+$", re.IGNORECASE),
    re.compile(r"^\d{6,7}$"),
    re.compile(
        r"^[\d,]+(?:\.\d+)?\s?(?:PSI|FPM|RPM|ohms?|volts?|VDC|amps?|gallons?)$",
        re.IGNORECASE,
    ),
    re.compile(r"^\d+(?:\.\d+)?\s?°?\s?F$", re.IGNORECASE),
    re.compile(r"^\d+(?:\.\d+)?\s?(?:inch|inches)$", re.IGNORECASE),
    re.compile(r'^\d+/\d+\s?(?:inch|inches|")$', re.IGNORECASE),
)


def test_anchors_are_hard_facts_not_ordinary_words():
    """
    An anchor must be something a correct answer cannot paraphrase away - a pin
    reference, a part number, a measurement. Ordinary vocabulary ("switch",
    "display") appears in almost any plausible reply, so asserting on it would
    pass whether or not the agent used the right KB: a check that cannot fail.
    """
    offenders = [
        (s["id"], a)
        for s in testbed.all_scenarios()
        for a in s.get("expectAnchors", [])
        if not any(shape.match(a.strip()) for shape in ANCHOR_SHAPES)
    ]
    assert not offenders, (
        "expectAnchors must be hard facts only; these would make the content "
        f"check unfalsifiable: {offenders[:10]}"
    )


def test_content_checking_has_scenarios_to_verify():
    """If answer-vs-KB checking is on, every routed KB needs anchored scenarios."""
    if not CONFIG["assertions"]["checkExpectedAnchors"]:
        pytest.skip("assertions.checkExpectedAnchors is off")

    bare = [
        kb["id"]
        for kb in ROUTED_KBS
        if not [s for s in testbed.scenarios_for(kb["id"]) if s.get("expectAnchors")]
    ]
    assert not bare, (
        f"checkExpectedAnchors is on but these KBs have no anchored scenario "
        f"to verify against: {bare}"
    )


@pytest.mark.parametrize("scenario", testbed.sample_scenarios(20), ids=lambda s: s["id"])
def test_sampled_scenario_text_appears_in_its_source_file(scenario):
    """Guards against a stale generated file after a KB is edited."""
    kb = next(k for k in KBS if k["id"] == scenario["kbId"])
    text = testbed.kb_path(kb).read_text(encoding="utf-8")
    needle = scenario["question"].split("/")[0].strip()[:40]
    assert needle in text, (
        f"{scenario['id']} quotes text not found in {kb['file']} - "
        f"resources/generated is stale, run `make resources`"
    )


# --------------------------------------------------------------------------
# End-to-end resolvability - the same resolution the browser suite performs
# --------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.parametrize("kb", ROUTED_KBS, ids=lambda k: k["id"])
def test_a_runnable_case_can_be_resolved_for_every_kb(kb):
    """Proves the browser suite will find a serial and a question for this KB."""
    serials = testbed.serials_for(kb["id"])
    scenarios = testbed.scenarios_for(kb["id"])
    assert serials and scenarios
    assert serials[0]["kbId"] == kb["id"]
    assert scenarios[0]["kbId"] == kb["id"]


def test_rotation_pool_is_large_enough_to_be_worth_rotating():
    """
    The agent remembers previous sessions per serial. If rotation is on but the
    pool is tiny, runs will still collide and the agent's behaviour will drift.
    """
    if not CONFIG["scenarioSelection"]["rotateSerials"]:
        pytest.skip("serial rotation is disabled in config")
    for kb in ROUTED_KBS:
        assert len(testbed.serials_for(kb["id"])) >= 5, (
            f"only {len(testbed.serials_for(kb['id']))} serials for {kb['id']}; "
            f"raise scenarioSelection.serialsPerKb"
        )


def test_chat_flow_phrases_are_non_empty():
    flow = CONFIG["chatFlow"]
    assert flow["agentIdlePrompts"], "chatFlow.agentIdlePrompts is empty"
    assert flow["intents"], "chatFlow.intents is empty - the chat suite cannot answer anything"

    for intent in flow["intents"]:
        assert intent.get("id"), f"an intent has no id: {intent}"
        assert intent.get("match"), f"intent {intent['id']} matches nothing"
        assert all(p.strip() for p in intent["match"]), f"intent {intent['id']} has a blank phrase"


def test_chat_flow_intents_cover_the_conversation():
    """The driver cannot get through a call without these three."""
    ids = [i["id"] for i in CONFIG["chatFlow"]["intents"]]
    for required in ("asksForSerial", "readsBackSerial", "readyForQuestion"):
        assert required in ids, f"chatFlow.intents is missing {required}; have {ids}"

    assert len(ids) == len(set(ids)), f"duplicate intent ids: {ids}"

    # The read-back repeats the serial and can mention "serial number" itself,
    # so it has to be matched before the broader asksForSerial rule.
    assert ids.index("readsBackSerial") < ids.index("asksForSerial"), (
        "readsBackSerial must come before asksForSerial, or a read-back gets "
        "answered with the serial again instead of a confirmation"
    )

    # Intents are matched top to bottom and the first hit wins, so a specific
    # request has to outrank a generic one. The rating request is phrased as an
    # ordinary polite question - "could you tell me how your experience was
    # today, and rate the call from one to ten?" - which clarifying matches on
    # "could you tell me". Ordered the wrong way round, that turn is answered as
    # a diagnostic question, no rating is ever sent, and the run then reports
    # the request as missing. Observed doing exactly that on 2026-09-18.
    # The agent's session-memory opener recaps the previous call - "Last time, I
    # helped confirm the serial number for your machine" - and asksForSerial
    # matches on exactly that phrase. Ordered the wrong way round, the suite
    # reads a recap as a request and types the serial at an agent that already
    # has it from the intake form. Observed on 2026-09-18.
    assert ids.index("readyForQuestion") < ids.index("asksForSerial"), (
        "readyForQuestion must come before asksForSerial, or a recap that merely "
        "mentions the serial number gets answered with the serial"
    )

    for generic in ("clarifying", "stepwiseWalkthrough"):
        assert ids.index("asksForFeedback") < ids.index(generic), (
            f"asksForFeedback must come before {generic}, or a rating request "
            f"phrased as an ordinary question gets swallowed by it and the "
            f"caller never answers with a score"
        )


def test_both_answers_to_the_text_offer_exist():
    """
    The agent offers to SMS the troubleshooting steps, and the chat suite runs
    the whole workflow once for each answer. Neither may go missing: losing
    `decline` would take the manual's numbers out of the transcript for good,
    and losing `accept` would leave the phone number the intake form collects
    entirely unexercised.
    """
    replies = CONFIG["chatFlow"]["textOfferReplies"]
    for answer in ("accept", "decline"):
        assert replies.get(answer, "").strip(), f"chatFlow.textOfferReplies.{answer} is empty"

    assert "{{phone}}" in replies["accept"], (
        "the accept answer should hand over the caller's number, so the older "
        "'what is the best number to text that to?' shape of the offer is answered "
        "in one go rather than asked again"
    )
    # These are substituted into an intent reply that is itself a placeholder,
    # so anything unknown in here survives both passes and gets typed at the
    # agent verbatim.
    for answer, text in replies.items():
        if answer.startswith("_"):
            continue
        unknown = set(re.findall(r"\{\{(\w+)\}\}", text)) - {"phone"}
        assert not unknown, f"textOfferReplies.{answer} uses unknown placeholders {unknown}"


def test_caller_intake_pools_are_usable():
    """The "Before we start" form is filled from these, and it rejects blanks."""
    intake = CONFIG["callerIntake"]
    assert len(intake["names"]) >= 5, "too few caller names to be worth drawing from"
    assert len(intake["companies"]) >= 5, "too few companies to be worth drawing from"
    assert intake["phoneAreaCodes"], "no area codes to build a phone number from"
    for field in ("names", "companies"):
        assert all(v.strip() for v in intake[field]), f"callerIntake.{field} has a blank entry"


def test_generated_phone_numbers_can_never_reach_a_real_person():
    """
    Every run types a phone number into a live product. NANP reserves
    <area code>-555-0100..0199 for fiction, so a number built inside that block
    cannot ring anybody. Loosening the format would quietly end that guarantee,
    which is why it is asserted rather than left to the comment next to it.
    """
    intake = CONFIG["callerIntake"]
    for area in intake["phoneAreaCodes"]:
        assert re.fullmatch(r"[2-9]\d{2}", area), (
            f"{area!r} is not a usable NANP area code - the form's validator will "
            f"reject it, exactly as it rejects its own 555 placeholder"
        )

    for line in ("00", "42", "99"):
        number = intake["phoneFormat"].replace("{{area}}", "480").replace("{{line}}", line)
        assert re.fullmatch(r"480-555-01\d{2}", number), (
            f"callerIntake.phoneFormat produced {number!r}, which is outside the "
            f"555-0100..0199 fictional block - it could be somebody's real number"
        )


def test_closing_statement_signs_off_without_volunteering_a_rating():
    """
    The caller closes the call themselves, because a rating is only ever asked
    for at a call's natural end and a caller who just stops typing never gets
    there. But the sign-off must stay a sign-off: a score in it would answer the
    question the agent is supposed to ask, and the run would go green on a
    defect that is still there.
    """
    closing = CONFIG["chatFlow"]["closingStatement"]
    assert closing and closing.strip(), (
        "chatFlow.closingStatement is empty - the call would just go quiet, and "
        "the agent hangs up on its own instead of reaching its closing turn"
    )
    assert not re.search(r"\d", closing), (
        f"chatFlow.closingStatement contains a number: {closing!r}. It must never "
        f"volunteer a rating - the whole point is to find out whether the agent asks"
    )
    scoring = re.search(r"\b(rate|rating|score|out of|stars?)\b", closing, re.I)
    assert not scoring, (
        f"chatFlow.closingStatement offers a rating ({scoring.group(0)!r}): {closing!r}. "
        f"It is a sign-off only - the agent has to ask"
    )


def test_chat_flow_intent_placeholders_are_known():
    """A reply may only interpolate values converse() actually supplies."""
    known = {"serial", "question", "clarification", "feedback", "phone", "textOffer"}
    for intent in CONFIG["chatFlow"]["intents"]:
        reply = intent.get("reply")
        if not reply:
            continue
        unknown = set(re.findall(r"\{\{(\w+)\}\}", reply)) - known
        assert not unknown, f"intent {intent['id']} uses unknown placeholders {unknown}"
