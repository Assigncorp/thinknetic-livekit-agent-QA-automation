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


def test_budgets_are_ordered_sensibly():
    b = CONFIG["budgets"]
    assert b["sessionConnectMs"] < b["answerMs"], "connecting should not be budgeted slower than a full answer"
    assert b["apiResponseMs"] < b["greetingMs"], "an API call should be budgeted faster than an LLM greeting"
    assert all(v > 0 for k, v in b.items() if not k.startswith("_")), "a budget of zero will never pass"


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
    for key in ("greetingAsksForSerial", "readBackConfirmation", "agentIdlePrompts"):
        assert flow[key], f"chatFlow.{key} is empty - the chat suite cannot anchor on anything"
    assert flow["confirmationReply"].strip(), "chatFlow.confirmationReply is empty"
