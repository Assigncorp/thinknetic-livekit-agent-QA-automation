"""
RoadSaver knowledge base (Bearcat, /b/products/roadsaver) - offline checks on
the KB file itself and on the scenarios generated from it. No agent calls.

Reads config/roadsaver.config.json directly rather than TESTBED_CONFIG, so it
runs on every `make catalog` / `make api` whichever product .env points at: a
RoadSaver KB edit that breaks an entry, a cross-reference or the generated pool
goes red here before a live RoadSaver call is ever spent on it.

The KB is a draft for Etnyre technical review (v2.0, 2026-10-22). Where it is
known to be incomplete, the gap is pinned below by name - a new one fails, and
so does a fixed one, until the list is brought up to date.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "config" / "roadsaver.config.json"

FAQ_ID = r"(?:GEN|OP|MNT|CMP|CAL|RPL|SPEC|APP)-\d+"
ENTRY_HEADING = re.compile(
    rf"^(?:###\s*(?P<ts>TS-\d+)\s*—\s*.+|\*\*(?P<faq>{FAQ_ID})\s*—\s*.+\*\*)\s*$",
    re.MULTILINE,
)

# Entries the KB's own appendix flags `safety_flag` but which carry no
# **Safety:** line for the agent to speak. Raised for Etnyre review 2026-10-26.
SAFETY_FLAGGED_WITHOUT_SAFETY_LINE = {"TS-20", "MNT-03", "CAL-02", "CAL-03"}

# FAQ entries with no spoken **A:** - only technician-reference detail, which
# the appendix says is stripped before speech, leaving the agent nothing to say.
FAQ_WITHOUT_SPOKEN_ANSWER = {"CMP-10"}

# Facts a correct RoadSaver answer cannot paraphrase away, read off the KB
# 2026-10-26. A KB revision that changes one of these must change it here too,
# on purpose - the live suites judge the agent against the same numbers.
GOLDEN_FACTS = [
    ("OP-02", "600 RPM"),             # jackshaft starting point
    ("OP-02", "90 to 110 RPM"),       # pugmill, Type II slurry / micro
    ("OP-01", "160 degrees"),         # warm-up before running the emulsion pump
    ("SPEC-02", "130 gallons per minute at 110 PSI"),
    ("SPEC-03", "Cummins QSB3.3 Tier III, 110 horsepower"),
    ("SPEC-04", "0.5 to 5 gallons per minute"),
    ("SPEC-09", "maximum 2,100"),
    ("TS-20", "5 PSI"),               # low-oil alarm clears above 5 PSI and rising
]


@lru_cache(maxsize=1)
def config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def kb() -> dict[str, Any]:
    (only,) = [k for k in config()["knowledgeBases"] if k.get("enabled")]
    return only


@lru_cache(maxsize=1)
def kb_text() -> str:
    return (ROOT / config()["resources"]["kbDir"] / kb()["file"]).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def entries() -> dict[str, str]:
    """Entry id -> body, up to the next entry or section heading."""
    text = kb_text()
    found = list(ENTRY_HEADING.finditer(text))
    out: dict[str, str] = {}
    for i, match in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        body = re.split(r"^#{1,2} ", text[match.end():end], flags=re.MULTILINE)[0]
        entry_id = match.group("ts") or match.group("faq")
        assert entry_id not in out, f"{entry_id} is defined twice in {kb()['file']}"
        out[entry_id] = body
    return out


def ts_ids() -> list[str]:
    return [e for e in entries() if e.startswith("TS-")]


def faq_ids() -> list[str]:
    return [e for e in entries() if not e.startswith("TS-")]


def generated(name: str) -> dict[str, Any]:
    path = ROOT / config()["resources"]["generatedDir"] / name
    if not path.exists():
        pytest.fail(f"{path.relative_to(ROOT)} is missing - run `make roadsaver-resources`")
    return json.loads(path.read_text(encoding="utf-8"))


def scenarios() -> list[dict[str, Any]]:
    return generated("scenarios.json")["pools"][kb()["id"]]


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

@pytest.mark.smoke
def test_config_declares_exactly_one_roadsaver_kb():
    enabled = [k for k in config()["knowledgeBases"] if k.get("enabled")]
    assert [k["id"] for k in enabled] == ["roadsaver"], enabled


def test_every_roadsaver_serial_is_in_the_index():
    """RS1001-RS1007, anchor first. The intake form needs one even though one
    KB serves every machine."""
    serials = generated("serial-index.json")["serials"]
    assert [s["serial"] for s in serials] == [f"RS{n}" for n in range(1001, 1008)]
    assert serials[0]["serial"] == kb()["anchorSerial"]
    assert {s["kbId"] for s in serials} == {kb()["id"]}


def test_generated_resources_do_not_share_the_chip_spreader_directory():
    """Regenerating one product must never overwrite the other's pool."""
    assert config()["resources"]["generatedDir"] != "resources/generated"


# --------------------------------------------------------------------------
# The KB file
# --------------------------------------------------------------------------

@pytest.mark.smoke
def test_kb_file_is_present_and_clean_utf8():
    text = kb_text()
    assert len(text) > 50_000, "roadsaver.md is suspiciously small - truncated copy?"
    # docs/deterministic-kb-testing.md: mojibake has reached a RoadSaver source before.
    corrupt = re.findall(r"Ã.|â€|�", text)
    assert not corrupt, f"encoding corruption in roadsaver.md: {corrupt[:5]}"


def test_troubleshooting_ids_are_contiguous():
    numbers = sorted(int(e.split("-")[1]) for e in ts_ids())
    assert numbers == list(range(1, len(numbers) + 1)), f"gaps in TS numbering: {numbers}"


def test_index_table_matches_the_troubleshooting_entries():
    section_a = kb_text().split("# SECTION B", 1)[0]
    index = section_a.split("**Index**", 1)[1].split("> **Note", 1)[0]
    listed = set(re.findall(r"^\|\s*(TS-\d+)\s*\|", index, re.MULTILINE))
    assert listed == set(ts_ids()), (
        f"index lists {sorted(listed - set(ts_ids()))} with no entry, "
        f"entries {sorted(set(ts_ids()) - listed)} missing from the index"
    )


def test_every_cross_reference_resolves():
    """'go to TS-02' or 'see FAQ OP-01' must land on an entry that exists."""
    referenced = set(re.findall(rf"\b(TS-\d+|{FAQ_ID})\b", kb_text()))
    dangling = referenced - set(entries())
    assert not dangling, f"references to entries that do not exist: {sorted(dangling)}"


def test_global_safety_rules_are_all_present():
    rules = kb_text().split("### 0.5", 1)[1].split("### 0.6", 1)[0]
    numbered = re.findall(r"^\d+\.\s", rules, re.MULTILINE)
    assert len(numbered) == 11, f"expected the 11 global safety rules, found {len(numbered)}"


def test_every_troubleshooting_entry_states_its_confidence():
    missing = [e for e in ts_ids() if "Confidence" not in entries()[e]]
    assert not missing, f"entries with no confidence rating: {missing}"


def test_every_faq_cites_a_source():
    missing = [e for e in faq_ids() if "Source" not in entries()[e]]
    assert not missing, f"FAQ entries with no source: {missing}"


def test_faq_entries_without_a_spoken_answer_are_only_the_known_ones():
    missing = {e for e in faq_ids() if "**A:**" not in entries()[e]}
    assert missing == FAQ_WITHOUT_SPOKEN_ANSWER, (
        f"new: {sorted(missing - FAQ_WITHOUT_SPOKEN_ANSWER)}, "
        f"fixed (drop from FAQ_WITHOUT_SPOKEN_ANSWER): {sorted(FAQ_WITHOUT_SPOKEN_ANSWER - missing)}"
    )


def test_safety_flagged_entries_carry_a_safety_line_except_known_gaps():
    """The appendix names the entries that need a safety instruction spoken."""
    appendix = kb_text().split("## Appendix", 1)[1]
    flag_line = re.search(r"safety_flag`\s*\(true for ([^)]+)\)", appendix)
    assert flag_line, "the appendix no longer lists safety_flag entries"
    flagged: set[str] = set()
    for part in re.split(r"[;,]\s*", flag_line.group(1).rstrip(".")):
        part = part.strip()
        # "TS-01, 02, 04" lists later TS numbers without the prefix.
        flagged.add(part if "-" in part else f"TS-{part}")
    assert flagged <= set(entries()), f"safety_flag names unknown entries: {sorted(flagged - set(entries()))}"

    without = {e for e in flagged if "**Safety:**" not in entries()[e]}
    assert without == SAFETY_FLAGGED_WITHOUT_SAFETY_LINE, (
        f"new: {sorted(without - SAFETY_FLAGGED_WITHOUT_SAFETY_LINE)}, fixed (drop from "
        f"SAFETY_FLAGGED_WITHOUT_SAFETY_LINE): {sorted(SAFETY_FLAGGED_WITHOUT_SAFETY_LINE - without)}"
    )


@pytest.mark.parametrize(("entry_id", "fact"), GOLDEN_FACTS, ids=[f"{e}:{f}" for e, f in GOLDEN_FACTS])
def test_golden_fact_is_still_in_its_entry(entry_id, fact):
    assert fact in entries()[entry_id], f"{entry_id} no longer says {fact!r}"


# --------------------------------------------------------------------------
# The generated scenario pool
# --------------------------------------------------------------------------

def _entry_at(source_line: int) -> str | None:
    match = ENTRY_HEADING.match(kb_text().splitlines()[source_line - 1])
    return (match.group("ts") or match.group("faq")) if match else None


def test_every_kb_entry_became_exactly_one_scenario():
    covered = [_entry_at(s["sourceLine"]) for s in scenarios()]
    assert None not in covered, "a scenario's sourceLine is not an entry heading - run `make roadsaver-resources`"
    assert sorted(covered) == sorted(entries()), (
        f"entries with no scenario: {sorted(set(entries()) - set(covered))}"
    )


def test_scenario_kinds_match_the_kb_sections():
    kinds = {_entry_at(s["sourceLine"]): s["kind"] for s in scenarios()}
    wrong = {e: k for e, k in kinds.items() if k != ("problem" if e.startswith("TS-") else "faq")}
    assert not wrong, f"troubleshooting/FAQ entries extracted as the wrong kind: {wrong}"


def test_troubleshooting_prompts_use_the_kb_customer_phrasing():
    """A caller says 'my mixer won't come on', not 'TS-01 Pugmill won't turn on'."""
    wrong = []
    for scenario in scenarios():
        entry_id = _entry_at(scenario["sourceLine"])
        if not entry_id.startswith("TS-"):
            continue
        quotes = re.search(r"\*\*Customer questions?:?\*\*:?\s*(?:\n-\s*)?[\"“](.+?)[\"”]", entries()[entry_id])
        if quotes and scenario["question"] != quotes.group(1).strip().rstrip("."):
            wrong.append((entry_id, scenario["question"], quotes.group(1)))
    assert not wrong, f"prompt is not the entry's first customer question: {wrong[:5]}"


def test_every_anchor_is_in_its_own_entry():
    """An anchor the entry does not contain would fail a correct answer.

    Joined on `[\\s-]*` like anchors._loose(): extraction writes the KB's
    "12-volt" as "12 volt" on purpose, and it is the same fact."""

    def loose(anchor: str) -> re.Pattern[str]:
        parts = [re.escape(p) for p in re.split(r"[\s-]+", anchor)]
        return re.compile(r"[\s-]*".join(parts), re.IGNORECASE)

    stray = [
        (s["id"], a)
        for s in scenarios()
        for a in s["expectAnchors"]
        if not loose(a).search(entries()[_entry_at(s["sourceLine"])])
    ]
    assert not stray, f"anchors not found in their source entry: {stray[:10]}"


def test_some_scenarios_carry_checkable_facts():
    anchored = [s for s in scenarios() if s["expectAnchors"]]
    assert len(anchored) >= 15, f"only {len(anchored)} RoadSaver scenarios carry an anchor"
