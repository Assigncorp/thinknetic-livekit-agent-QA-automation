"""
Compiles the knowledge bases into the facts the deterministic oracle checks.

Three artefacts, all written to resources/generated/ by build_resources.py and
consumed at runtime by judge/src/oracle.py:

  corpus-numerals.json    every legitimate (value, unit) pair and part
                          reference, per knowledge base. This is what makes the
                          closed-world fabrication check possible: a
                          measurement in a transcript that is not in here was
                          invented.

  differential-index.json per machine, the measurements that belong to a
                          DIFFERENT machine and not to this one. An answer
                          citing one of these to this caller is the
                          cross-contamination defect, and unlike a family NAME
                          a number carries no paraphrase ambiguity.

  oracle.json             per scenario: required anchors, the anchors in KB
                          step order, whether the entry carries a safety
                          instruction, whether it terminates in escalation.

Why compile at all, rather than parse the KBs at assertion time: the browser
suite is TypeScript and the judge is Python, and two hand-written
implementations of one rule is the duplication this design exists to remove
(see judge/src/anchors.py's docstring for what that costs). Both languages can
read JSON. So the grammar lives once, in judge/src/numerals.py, runs once, at
build time, and both suites consume its output as data.

The numeral grammar is imported from judge/src rather than copied. tools/ is a
separate uv project, so the import is by path - deliberate, and asserted by
ORC-07 rather than trusted.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_numerals():
    """judge/src/numerals.py, imported by path with its package intact.

    The relative `from . import anchors` inside numerals.py needs a real
    package, so `judge/` goes on sys.path and the module is imported as
    `src.numerals`. tools/ has no `src` package of its own, so nothing is
    shadowed - but keep this the only place that does it.
    """
    judge_dir = ROOT / "tests" / "judge"
    if not (judge_dir / "src" / "numerals.py").exists():
        sys.exit(
            "judge/src/numerals.py is missing - the oracle artefacts are compiled "
            "from its grammar and cannot be built without it"
        )
    if str(judge_dir) not in sys.path:
        sys.path.insert(0, str(judge_dir))
    spec = importlib.util.find_spec("src.numerals")
    if spec is None:  # pragma: no cover - only if the layout changes
        sys.exit("could not import src.numerals from judge/")
    import src.numerals as numerals  # noqa: PLC0415

    return numerals


N = _load_numerals()


# ---------------------------------------------------------------------------
# Entry-level facts, used to enrich each scenario
# ---------------------------------------------------------------------------

# The KBs write steps as bold run-in labels: `**Step 1 — Check start latch:**`.
STEP_LABEL = re.compile(r"\*\*Step\s+(?P<n>\d+)\s*[—\-–]\s*(?P<title>[^*:]+):?\*\*")

# A safety instruction the answer is expected to carry. Narrower than
# corpus.WARNING_MARKER on purpose: that one decides whether a section has
# anything to warn about, this one decides whether an ANSWER must say it, and
# "never" or "do not" is too weak a trigger to gate on.
SAFETY_TRIGGER = re.compile(
    r"\b(warning|danger|caution|lock ?out|tag ?out|"
    r"shut off the machine|turn (?:the )?machine off|engine off)\b",
    re.IGNORECASE,
)

ESCALATION = re.compile(
    r"\b(contact etnyre|etnyre service|888-586-1899|8885861899)\b", re.IGNORECASE
)


def split_steps(answer: str) -> list[tuple[int, str]]:
    """(step number, step body) for an entry written as numbered steps."""
    matches = list(STEP_LABEL.finditer(answer))
    if not matches:
        return []
    steps: list[tuple[int, str]] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(answer)
        steps.append((int(match.group("n")), answer[match.start() : end]))
    return steps


def ordered_step_anchors(answer: str, anchors: list[str]) -> list[dict[str, Any]]:
    """
    Which step each required anchor lives in, in KB order.

    This is what makes a step-order assertion possible without asserting on
    wording. The agent paraphrases step TITLES freely - "check the start latch"
    becomes "first, let's make sure the start latch isn't holding you" - so
    matching titles would be a wording test wearing a determinism hat. The
    numbers inside the steps do not paraphrase, and their ORDER is the property
    a reordered procedure violates.

    Only useful when two or more distinct steps carry an anchor; otherwise there
    is no order to check and oracle.json records it as unorderable.
    """
    out: list[dict[str, Any]] = []
    for number, body in split_steps(answer):
        for anchor in anchors:
            if anchor.lower() in body.lower() and not any(
                o["anchor"].lower() == anchor.lower() for o in out
            ):
                out.append({"step": number, "anchor": anchor})
    return out


def entry_facts(answer: str, anchors: list[str]) -> dict[str, Any]:
    """The per-scenario block that goes into oracle.json."""
    steps = ordered_step_anchors(answer, anchors)
    distinct_steps = len({s["step"] for s in steps})
    safety = SAFETY_TRIGGER.search(answer)
    escalate = ESCALATION.search(answer)
    return {
        "requiredAnchors": list(anchors),
        "anchorSource": "extracted" if anchors else "none",
        "structuralOnly": not anchors,
        "stepCount": len(split_steps(answer)),
        "orderedAnchors": steps,
        "stepOrderCheckable": distinct_steps >= 2,
        "safetyRequired": bool(safety),
        "safetyEvidence": safety.group(0) if safety else "",
        "escalate": bool(escalate),
        "escalationEvidence": escalate.group(0) if escalate else "",
    }


# ---------------------------------------------------------------------------
# Corpus index
# ---------------------------------------------------------------------------


def measurement_key(measurement) -> str:
    """Delegates to the grammar rather than reformatting the float here - see
    numerals.key_of for what a second copy of this costs."""
    return N.key_of(measurement)


def build_corpus_numerals(cfg: dict[str, Any]) -> dict[str, Any]:
    """Every legitimate measurement and part reference, per knowledge base."""
    kb_dir = ROOT / cfg["resources"]["kbDir"]
    by_kb: dict[str, dict[str, list[str]]] = {}

    for kb in cfg["knowledgeBases"]:
        if not kb.get("enabled"):
            continue
        text = (kb_dir / kb["file"]).read_text(encoding="utf-8")
        measurements = sorted({measurement_key(m) for m in N.extract(text)})
        parts = sorted(set(N.part_references(text)))
        by_kb[kb["id"]] = {"measurements": measurements, "parts": parts}
        print(
            f"  numerals:  {kb['id']:<8} {len(measurements):>4} measurements, "
            f"{len(parts):>3} part refs"
        )

    # The general guide is a shared pool - valid for any machine - so it is
    # named here rather than inferred, and the oracle unions it into every
    # machine's allowed set.
    shared = [
        kb["id"]
        for kb in cfg["knowledgeBases"]
        if kb.get("enabled") and not kb.get("controller") and not kb.get("hopperType")
    ]

    return {
        "_generated": "Do not edit. Regenerate with: make resources",
        "_note": (
            "Closed-world index for judge/src/oracle.py. A measurement the agent "
            "utters that is absent from its machine's set (unioned with `shared`) "
            "was not read out of any manual we hold."
        ),
        "shared": shared,
        "byKb": by_kb,
    }


def build_differential(cfg: dict[str, Any], corpus: dict[str, Any]) -> dict[str, Any]:
    """Per machine, the measurements that belong only to OTHER machines."""
    shared = set(corpus["shared"])
    machines = [
        kb["id"]
        for kb in cfg["knowledgeBases"]
        if kb.get("enabled") and kb["id"] not in shared
    ]
    meta = {kb["id"]: kb for kb in cfg["knowledgeBases"]}

    shared_measurements: set[str] = set()
    for kb_id in shared:
        shared_measurements |= set(corpus["byKb"][kb_id]["measurements"])

    by_kb: dict[str, Any] = {}
    for kb_id in machines:
        own = set(corpus["byKb"][kb_id]["measurements"]) | shared_measurements
        forbidden: dict[str, list[str]] = {}
        for other in machines:
            if other == kb_id:
                continue
            for key in corpus["byKb"][other]["measurements"]:
                if key in own:
                    continue
                forbidden.setdefault(key, []).append(other)
        by_kb[kb_id] = {
            "controller": meta[kb_id].get("controller"),
            "hopperType": meta[kb_id].get("hopperType"),
            "forbidden": {k: sorted(v) for k, v in sorted(forbidden.items())},
        }
        print(f"  differential: {kb_id:<8} {len(forbidden):>4} foreign measurements")

    return {
        "_generated": "Do not edit. Regenerate with: make resources",
        "_note": (
            "A measurement listed under a machine appears in another machine's "
            "manual and NOT in this one's. Citing it to this caller is the "
            "cross-family defect docs/test-plan.md ranks as risk #1."
        ),
        "byKb": by_kb,
    }


def build_oracle(cfg: dict[str, Any], scenarios: dict[str, Any]) -> dict[str, Any]:
    """Per-scenario expectations, flattened for lookup by scenario id."""
    entries: dict[str, Any] = {}
    for kb_id, pool in scenarios["pools"].items():
        for scenario in pool:
            facts = {k: v for k, v in scenario.items() if k in ENTRY_FIELDS}
            entries[scenario["id"]] = {
                "kbId": kb_id,
                "section": scenario.get("section", ""),
                "sourceLine": scenario.get("sourceLine"),
                "question": scenario.get("question", ""),
                **facts,
            }

    checkable = sum(1 for e in entries.values() if not e.get("structuralOnly"))
    orderable = sum(1 for e in entries.values() if e.get("stepOrderCheckable"))
    safety = sum(1 for e in entries.values() if e.get("safetyRequired"))
    escalate = sum(1 for e in entries.values() if e.get("escalate"))
    print(
        f"  oracle:    {len(entries)} scenarios - {checkable} carry a checkable fact, "
        f"{orderable} have an order to check, {safety} require a safety line, "
        f"{escalate} terminate in escalation"
    )

    return {
        "_generated": "Do not edit. Regenerate with: make resources",
        "coverage": {
            "scenarios": len(entries),
            "withAnchors": checkable,
            "stepOrderCheckable": orderable,
            "safetyRequired": safety,
            "escalate": escalate,
        },
        "entries": entries,
    }


ENTRY_FIELDS = {
    "requiredAnchors",
    "anchorSource",
    "structuralOnly",
    "stepCount",
    "orderedAnchors",
    "stepOrderCheckable",
    "safetyRequired",
    "safetyEvidence",
    "escalate",
    "escalationEvidence",
}
