"""
Draft the KB question bank from the four model knowledge bases.

    uv run --project tests/sdk python tools/build_question_bank.py            # -> kb/question_bank.draft.yaml
    uv run --project tests/sdk python tools/build_question_bank.py --report   # candidates and why others were dropped

It parses every lowest-level section of each KB, pulls out its ordered steps and
its cautions, and keeps only procedures with at least 3 steps AND at least one
caution or warning. Step and caution text is copied verbatim from the KB - this
script never writes a step or caution of its own. Keywords are a first draft
(numbers with units, CAPITALISED positions, bold control names); they are
hand-reviewed into kb/question_bank.yaml, which is the file the tests use.

Step formats recognised:
    1. Do this.                         numbered list (continuation lines indented)
    **Step 3 — Title:** Do this.        troubleshooting walk-through
    **Step 3 — Do this.**               whole step in bold

Caution formats recognised (all of them, wherever they sit):
    > **WARNING:** …  / > **CAUTION:** …         block quote
    **Warning:** …    / **Caution:** …           inline
       > **CAUTION:** …                          nested under a step (indented)
    "Do NOT crank for more than 30 seconds…"     inside a step's own text

A caution quoted between two steps belongs to the step before it; one before
the first step or after the last covers the whole procedure.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "sdk"))

from lkqa.routing import KB_DIR, KB_FILES  # noqa: E402
from lkqa.validator import normalize  # noqa: E402

DRAFT = KB_DIR / "question_bank.draft.yaml"

HEADING = re.compile(r"^(#{2,4})\s+(.*?)\s*$")
NUMBERED = re.compile(r"^(\s{0,3})(\d{1,2})\.\s+(.*)$")
BOLD_STEP = re.compile(r"^\*\*Step\s+(\d{1,2})\s*(?:[—–:-]\s*)?(.*?)\*\*\s*(.*)$", re.IGNORECASE)
QUOTE_CAUTION = re.compile(r"^(\s*)>\s*\*\*(WARNING|CAUTION|DANGER)\b[^*]*\*\*\s*:?\s*(.*)$", re.IGNORECASE)
INLINE_CAUTION = re.compile(r"^(\s*)\*\*(WARNING|CAUTION|DANGER)\s*:?\*\*\s*:?\s*(.*)$", re.IGNORECASE)
IN_STEP_CAUTION = re.compile(
    r"((?:\b(?i:warning|caution|danger)\s*:|\bDo NOT\b|\bDO NOT\b|\bDo not\b|\bNever\b|\bNEVER\b)[^.!]*[.!]?)"
)
# Not procedures: dialogue scripts, reference lists, the KB's own how-to-use notes.
SKIP_HEADINGS = re.compile(
    r"^(?:call script|script \d|section \d+ — (?:how to use|warranty|header)|major systems|"
    r"how to use|key specifications|section \d+ — product overview)", re.IGNORECASE)
POSITIONS = {"PARK", "DRIVE", "IDLE", "RUN", "ON", "OFF", "OPEN", "CLOSED", "NEUTRAL", "START",
             "FORWARD", "REVERSE", "AUTO"}


@dataclass
class Caution:
    text: str
    step: int | str  # step number or "procedure"
    form: str


@dataclass
class Section:
    model: str
    kb_file: str
    heading: str
    level: int
    lines: list[str] = field(default_factory=list)
    steps: list[tuple[int, str]] = field(default_factory=list)
    cautions: list[Caution] = field(default_factory=list)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\\", "")).strip()


def sections(model: str) -> list[Section]:
    kb_file = KB_FILES[model]
    lines = (KB_DIR / kb_file).read_text(encoding="utf-8").splitlines()
    out: list[Section] = []
    cur: Section | None = None
    for line in lines:
        m = HEADING.match(line)
        if m:
            cur = Section(model, kb_file, m.group(2).strip(), len(m.group(1)))
            out.append(cur)
            continue
        if cur is not None:
            cur.lines.append(line)
    for s in out:
        _parse(s)
    return out


def _parse(sec: Section) -> None:
    steps: list[list] = []  # [number, text]
    pending: list[tuple[str, str, int]] = []  # caution text, form, index of preceding step (-1 none)
    in_list = False
    mode = ""  # "bold": paragraph lines after a **Step N** belong to it; "list": only indented ones
    for raw in sec.lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        q = QUOTE_CAUTION.match(line) or INLINE_CAUTION.match(line)
        if q:
            indent, word, body = q.groups()
            form = "nested" if (indent and steps) else ("quote" if line.lstrip().startswith(">") else "inline")
            pending.append((_clean(f"{word.upper()}: {body}"), form, len(steps) - 1))
            continue
        if line.lstrip().startswith(">"):
            # continuation of a quoted caution, or a NOTE (not a caution)
            body = line.lstrip()[1:].strip()
            if pending and pending[-1][2] == len(steps) - 1 and not re.match(r"\*\*NOTE", body, re.I):
                if body:
                    t, f, i = pending[-1]
                    pending[-1] = (_clean(t + " " + body), f, i)
            continue
        b = BOLD_STEP.match(line.strip())
        if b:
            num, title, rest = b.groups()
            text = _clean(" ".join(x for x in (title, rest) if x))
            steps.append([int(num), text])
            in_list, mode = True, "bold"
            continue
        n = NUMBERED.match(line)
        if n and (not n.group(1) or len(n.group(1)) <= 3) and mode != "bold":
            steps.append([int(n.group(2)), _clean(n.group(3))])
            in_list, mode = True, "list"
            continue
        if mode == "bold" and steps:
            stripped = line.strip()
            if re.match(r"^\*\*(?!Step\b)[^*]{0,60}\*\*", stripped) and not re.match(
                    r"^\*\*(?:warning|caution|danger)", stripped, re.I):
                mode, in_list = "", False  # a new bold lead-in ("**Note on …:**") ends the step run
                continue
            if not stripped.startswith(("|", "#")):
                steps[-1][1] = _clean(steps[-1][1] + " " + stripped.lstrip("-* "))
                continue
        if in_list and steps and (raw.startswith("   ") or raw.startswith("\t")) and not raw.strip().startswith(("-", "|")):
            steps[-1][1] = _clean(steps[-1][1] + " " + raw.strip())
            continue
        if in_list and steps and raw.strip().startswith(("- ", "* ")) and raw.startswith(" "):
            steps[-1][1] = _clean(steps[-1][1] + " " + raw.strip()[2:])
            continue
        in_list = in_list and not raw.strip().startswith(("|", "#"))

    # keep the first run of consecutively numbered steps starting at 1
    run: list[tuple[int, str]] = []
    for num, text in steps:
        if num == len(run) + 1:
            run.append((num, text))
        elif run and num == 1:
            break
    sec.steps = run

    last = len(run) - 1
    for text, form, idx in pending:
        if 0 <= idx < last:
            anchor: int | str = run[idx][0]
        elif idx == last and form == "nested":
            anchor = run[idx][0]
        else:
            anchor = "procedure"
        sec.cautions.append(Caution(text, anchor, form))

    for num, text in run:
        for m in IN_STEP_CAUTION.finditer(text):
            sentence = m.group(1).strip()
            if len(sentence.split()) >= 4:
                sec.cautions.append(Caution(sentence, num, "in_step"))


# ---------------------------------------------------------------------------
# Draft keywords
# ---------------------------------------------------------------------------

_VALUE = re.compile(
    r"\d+(?:[.,/]\d+)?(?:\s*(?:–|-|to)\s*\d+(?:[.,]\d+)?)?\s*"
    r"(?:PSI|psi|FPM|RPM|seconds?|minutes?|amps?|°F|VDC|VAC|volts?|inch(?:es)?|\"|gallons?|ohms?|%)"
)
_BOLD = re.compile(r"\*\*([^*]{2,40})\*\*")


def draft_keywords(text: str) -> list[dict]:
    kws: list[dict] = []
    seen: set[str] = set()

    def add(term: str, kind: str) -> None:
        key = normalize(term)
        if key and key not in seen:
            seen.add(key)
            kws.append({"term": term, "kind": kind, "synonyms": []})

    for m in _VALUE.finditer(text):
        add(m.group(0).strip(), "value")
    for m in _BOLD.finditer(text):
        word = m.group(1).strip()
        add(word, "position" if word.upper() in POSITIONS else "term")
    for word in re.findall(r"\b[A-Z]{2,}\b", re.sub(r"\*\*[^*]+\*\*", "", text)):
        if word in POSITIONS:
            add(word, "position")
    return kws


def candidates() -> tuple[list[Section], list[tuple[Section, str]]]:
    kept, dropped = [], []
    for model in KB_FILES:
        for sec in sections(model):
            if SKIP_HEADINGS.match(sec.heading):
                continue
            if len(sec.steps) < 3:
                if sec.cautions and sec.steps:
                    dropped.append((sec, f"only {len(sec.steps)} step(s)"))
                continue
            if not sec.cautions:
                dropped.append((sec, f"{len(sec.steps)} steps but no caution or warning"))
                continue
            kept.append(sec)
    return kept, dropped


def _slug(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", text.upper()).strip("-")[:40]


def to_entry(sec: Section) -> dict:
    question = re.sub(r"^Q:\s*", "", sec.heading)
    return {
        "id": f"{sec.model}-{_slug(question)}",
        "model": sec.model,
        "kb_file": sec.kb_file,
        "kb_section": sec.heading,
        "question": question,
        "steps": [{"n": n, "text": t, "keywords": draft_keywords(t)} for n, t in sec.steps],
        "cautions": [
            {"id": f"C{i}", "text": c.text, "step": c.step, "form": c.form, "keywords": draft_keywords(c.text)}
            for i, c in enumerate(sec.cautions, start=1)
        ],
    }


def main() -> int:
    import yaml

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--report", action="store_true", help="print kept and dropped procedures")
    args = ap.parse_args()

    kept, dropped = candidates()
    if args.report:
        print(f"KEPT {len(kept)}")
        for s in kept:
            forms = sorted({c.form for c in s.cautions})
            print(f"  {s.model:7} {len(s.steps):2} steps {len(s.cautions):2} cautions {forms}  {s.heading}")
        print(f"\nDROPPED {len(dropped)} (had steps or cautions, failed the >=3 steps + >=1 caution rule)")
        for s, why in dropped:
            print(f"  {s.model:7} {why:40}  {s.heading}")
        return 0

    entries = [to_entry(s) for s in kept]
    header = (
        "# DRAFT - generated by tools/build_question_bank.py. Do not edit; hand-review into\n"
        "# kb/question_bank.yaml, which is what the tests read.\n"
    )
    DRAFT.write_text(header + yaml.safe_dump({"entries": entries}, sort_keys=False, allow_unicode=True,
                                             width=110), encoding="utf-8")
    print(f"{len(entries)} entries -> {DRAFT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
