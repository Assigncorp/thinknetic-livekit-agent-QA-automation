"""
Which scenario, which serial, which caller - drawn from config, never hardcoded.

Same rules as the browser suite and the judge: serials rotate because the agent
remembers callers per serial, caller details are drawn from callerIntake's
fictional pools, and phone numbers stay inside the NANP 555-01xx fiction block.
Everything is reproducible when scenarioSelection.seed is set.
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from typing import Any

from .bridge import oracle, testbed


def rng() -> random.Random:
    return random.Random(testbed.config()["scenarioSelection"].get("seed"))


def caller(r: random.Random, serial: str) -> dict[str, str]:
    intake = testbed.config()["callerIntake"]
    phone = (
        intake["phoneFormat"]
        .replace("{{area}}", r.choice(intake["phoneAreaCodes"]))
        .replace("{{line}}", f"{r.randint(0, 99):02d}")
    )
    return {
        "serialNumber": serial,
        "customerName": r.choice(intake["names"]),
        "companyName": r.choice(intake["companies"]),
        "phone": phone,
    }


def serial_routed_kbs() -> list[dict[str, Any]]:
    return [kb for kb in testbed.knowledge_bases(serial_routed_only=True)]


def serial_for(kb_id: str, r: random.Random) -> str:
    serials = testbed.serials_for(kb_id)
    if not serials:
        raise LookupError(f"no serial in the workbook routes to {kb_id} - run `make resources`")
    return r.choice(serials)["serial"]


def anchored(kb_id: str, kinds: list[str] | None = None) -> list[dict[str, Any]]:
    pool = testbed.scenario_pools()["pools"].get(kb_id, [])
    out = [s for s in pool if s.get("expectAnchors") and not s.get("structuralOnly")]
    if kinds:
        out = [s for s in out if s.get("kind") in kinds]
    return out


def kbs_with_scenarios(kinds: list[str] | None = None) -> list[dict[str, Any]]:
    """Serial-routed machines that actually have an anchored scenario of these
    kinds. VHRS36 has no anchored FAQ entry, so any test that picks "a machine"
    and then "one of its FAQs" must pick from this list - it crashed on
    random.choice([]) on 2026-09-28."""
    return [kb for kb in serial_routed_kbs() if anchored(kb["id"], kinds)]


def draw(r: random.Random, kinds: list[str] | None = None, index: int | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """(kb, scenario): a machine with eligible scenarios, and one of them.
    `index` pins the machine deterministically (spread tests across machines)."""
    kbs = kbs_with_scenarios(kinds)
    if not kbs:
        raise LookupError(f"no serial-routed machine has an anchored {kinds} scenario - run `make resources`")
    kb = kbs[index % len(kbs)] if index is not None else r.choice(kbs)
    return kb, r.choice(anchored(kb["id"], kinds))


def grounding_matrix(r: random.Random) -> list[dict[str, Any]]:
    """One or more anchored scenarios per serial-routed KB, plus any pinned ones."""
    cfg = testbed.config()["livekitSdk"]["grounding"]
    picked: list[dict[str, Any]] = []
    for kb in serial_routed_kbs():
        pool = anchored(kb["id"], cfg.get("kinds"))
        if not pool:
            continue
        picked.extend(r.sample(pool, min(int(cfg["perKb"]), len(pool))))
    for scenario_id in cfg.get("pinned", []):
        if all(s["id"] != scenario_id for s in picked):
            picked.append(testbed.scenario_by_id(scenario_id))
    return picked


def _norm(q: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", q.lower()).strip()


def differential_pair() -> tuple[dict[str, Any], dict[str, Any]] | None:
    """
    The same question, asked on two machines whose manuals answer it
    DIFFERENTLY - where one machine's expected figure is FORBIDDEN to the other
    by the differential index (it is in that manual and not in this one).

    That last condition is what makes it a real differential rather than noise.
    Anchors that merely differ are not enough: FHRC28/FHRC36-FAQ-053 ("How do I
    report a safety defect?") carry 12 VDC and 5 VDC, which are scenario-
    extraction bleed from the neighbouring entry, and a pair chosen on that
    basis passed XFM-05 vacuously on 2026-09-28 - neither answer cited anything.

    A model answering from general knowledge, or from the wrong manual, gives
    both callers the same figure; the index says exactly which one is foreign.
    """
    from src import numerals  # judge on path via bridge

    def keys(s: dict[str, Any]) -> set[str]:
        return {numerals.key_of(m) for a in s["expectAnchors"] for m in numerals.extract(a)}

    by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for kb in serial_routed_kbs():
        for s in anchored(kb["id"]):
            by_question[_norm(s["question"])].append(s)

    best: tuple[int, str, tuple[dict[str, Any], dict[str, Any]]] | None = None
    for group in by_question.values():
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                if a["kbId"] == b["kbId"] or keys(a) == keys(b):
                    continue
                foreign = (keys(a) & set(oracle.forbidden_measurements(b["kbId"]))) | (
                    keys(b) & set(oracle.forbidden_measurements(a["kbId"]))
                )
                if not foreign:
                    continue
                candidate = (len(foreign), min(a["id"], b["id"]), (a, b))
                if best is None or candidate[:2] > best[:2]:
                    best = candidate
    return best[2] if best else None


def shared_question_across_kbs(n: int) -> list[dict[str, Any]]:
    """A question asked on `n` different machines - for the concurrency test,
    so three parallel callers ask the same thing and must get their own machine's answer."""
    by_question: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for kb in serial_routed_kbs():
        for s in anchored(kb["id"]):
            by_question[_norm(s["question"])].setdefault(kb["id"], s)
    candidates = sorted(
        (group for group in by_question.values() if len(group) >= n),
        key=lambda g: sorted(s["id"] for s in g.values()),
    )
    if not candidates:
        return []
    # Prefer machines that differ in BOTH hopper type and controller.
    group = candidates[0]
    kbs = sorted(group, key=lambda k: (testbed.kb_by_id(k)["hopperType"], testbed.kb_by_id(k)["controller"]))
    chosen, seen = [], set()
    for kb_id in kbs:
        kb = testbed.kb_by_id(kb_id)
        key = (kb["hopperType"], kb["controller"])
        if key not in seen:
            chosen.append(group[kb_id])
            seen.add(key)
    for kb_id in kbs:
        if len(chosen) >= n:
            break
        if group[kb_id] not in chosen:
            chosen.append(group[kb_id])
    return chosen[:n]


def hopper_word(kb_id: str) -> str:
    return {"FIXED": "fixed", "VARIABLE": "variable"}[testbed.kb_by_id(kb_id)["hopperType"]]


def other_hopper_word(kb_id: str) -> str:
    return {"fixed": "variable", "variable": "fixed"}[hopper_word(kb_id)]
