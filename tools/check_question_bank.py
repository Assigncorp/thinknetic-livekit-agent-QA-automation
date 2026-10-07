"""
Check a question bank file against the knowledge bases. Deterministic, offline.

    uv run --project tests/sdk python tools/check_question_bank.py                 # kb/question_bank.yaml
    uv run --project tests/sdk python tools/check_question_bank.py some/file.yaml

Exits non-zero and lists every problem. The same checks run as unit tests
(tests/sdk/tests/test_question_bank.py), so a bank that fails here fails CI.

What it guarantees:
  * nothing invented - every step and caution text is copied verbatim from the
    KB, under the exact kb_section heading of the entry's own model;
  * every keyword is grounded - its term appears in that step's/caution's own text;
  * entries obey the rule: >= 3 ordered steps and >= 1 caution;
  * keywords are distinctive - no step's keywords are all satisfied by a
    different step's text (that would make the validator call a correct answer
    "merged" or "out of order");
  * the bank is satisfiable - a transcript made of the KB text itself, one step
    per turn with each caution next to its step, passes the validator.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "sdk"))

from lkqa.routing import KB_DIR, KB_FILES  # noqa: E402
from lkqa.validator import Keyword, contains_phrase, normalize, validate  # noqa: E402

BANK = KB_DIR / "question_bank.yaml"
ID_RE = re.compile(r"^(VHRS28|VHRS36|FHRC28|FHRC36)-[A-Z0-9-]+$")
LABEL_RE = re.compile(r"^(?:WARNING|CAUTION|DANGER)\s*:\s*", re.IGNORECASE)


def canon(text: str) -> str:
    """Markdown-blind, whitespace-blind form for the verbatim check."""
    t = text.replace("\\", "").replace("**", "").replace("__", "")
    t = re.sub(r"^\s*>\s?", "", t, flags=re.MULTILINE)
    t = re.sub(r"^\s*[-*•]\s+", "", t, flags=re.MULTILINE)  # list bullets
    t = t.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", t).strip()


def _headings(kb_text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^#{2,4}\s+(.*?)\s*$", kb_text, re.MULTILINE)]


def _section_text(kb_text: str, heading: str) -> str:
    lines = kb_text.splitlines()
    out, inside, level = [], False, 0
    for line in lines:
        m = re.match(r"^(#{2,4})\s+(.*?)\s*$", line)
        if m:
            if inside and len(m.group(1)) <= level:
                break
            if m.group(2).strip() == heading and not inside:
                inside, level = True, len(m.group(1))
                continue
        if inside:
            out.append(line)
    return "\n".join(out)


def kb_transcript(entry: dict) -> list[str]:
    """The KB itself as an agent would ideally say it: procedure-wide cautions as
    a preface, then each step as its own turn with its cautions just before it."""
    turns: list[str] = []
    procedure = [c["text"] for c in entry.get("cautions", []) if c.get("step") == "procedure"]
    if procedure:
        turns.append(" ".join(LABEL_RE.sub("", t) for t in procedure))
    for step in entry.get("steps", []):
        n = step["n"]
        before = [LABEL_RE.sub("", c["text"]) for c in entry.get("cautions", [])
                  if str(c.get("step")) == str(n)]
        turns.append(" ".join(before + [step["text"]]) if before else step["text"])
    return turns


def check_entry(entry: dict, kb_cache: dict[str, str]) -> list[str]:
    eid = entry.get("id", "<no id>")
    p: list[str] = []

    def err(msg: str) -> None:
        p.append(f"{eid}: {msg}")

    for key in ("id", "model", "kb_file", "kb_section", "question", "steps", "cautions"):
        if not entry.get(key):
            err(f"missing {key}")
    if p:
        return p
    if not ID_RE.match(eid):
        err("id must look like MODEL-UPPER-KEBAB")
    model = entry["model"]
    if model not in KB_FILES:
        return p + [f"{eid}: unknown model {model!r}"]
    if not eid.startswith(model + "-"):
        err(f"id does not start with its model {model}")
    if entry["kb_file"] != KB_FILES[model]:
        err(f"kb_file {entry['kb_file']!r} is not {model}'s KB ({KB_FILES[model]})")
        return p
    kb_text = kb_cache.setdefault(model, (KB_DIR / KB_FILES[model]).read_text(encoding="utf-8"))
    if entry["kb_section"] not in _headings(kb_text):
        err(f"kb_section {entry['kb_section']!r} is not a heading in {entry['kb_file']}")
        section = kb_text
    else:
        section = _section_text(kb_text, entry["kb_section"])
    section_c = canon(section)

    steps = entry["steps"]
    if len(steps) < 3:
        err(f"only {len(steps)} steps; the rule is >= 3")
    if len(entry["cautions"]) < 1:
        err("no cautions; the rule is >= 1")
    for i, step in enumerate(steps, start=1):
        if step.get("n") != i:
            err(f"step numbers must run 1..N in order (found {step.get('n')} at position {i})")
        text = str(step.get("text", ""))
        if canon(text) not in section_c:
            err(f"step {i} text is not verbatim from section {entry['kb_section']!r}: {text[:80]!r}")
        kws = step.get("keywords") or []
        if not kws:
            err(f"step {i} has no keywords")
        _check_keywords(err, f"step {i}", kws, text)

    numbers = {s["n"] for s in steps}
    for c in entry["cautions"]:
        cid = c.get("id", "?")
        text = str(c.get("text", ""))
        body = LABEL_RE.sub("", canon(text))
        if canon(body) not in section_c:
            err(f"caution {cid} text is not verbatim from section {entry['kb_section']!r}: {text[:80]!r}")
        anchor = c.get("step")
        if anchor != "procedure" and anchor not in numbers:
            err(f"caution {cid} is anchored to step {anchor!r}, which does not exist")
        kws = c.get("keywords") or []
        if not kws:
            err(f"caution {cid} has no keywords")
        _check_keywords(err, f"caution {cid}", kws, text)

    # distinctive: no step's keywords are all met by another step's text
    norms = {s["n"]: normalize(s["text"]) for s in steps}
    for s in steps:
        kws = [Keyword.parse(k) for k in s.get("keywords") or []]
        if not kws:
            continue
        for other, text in norms.items():
            if other != s["n"] and all(k.found_in(text) for k in kws):
                err(f"step {s['n']} keywords are all met by step {other}'s text too - add a keyword "
                    f"only step {s['n']} says")

    if not p:
        result = validate(entry, kb_transcript(entry))
        if not result.passed:
            err("the KB's own text does not pass the validator:\n      " +
                result.explain().replace("\n", "\n      "))
    if canon(entry["question"]).lower() in section_c.lower() and len(entry["question"]) > 40:
        err("question is copied from the KB; phrase it the way an operator would ask")
    return p


def _check_keywords(err, where: str, kws: list, text: str) -> None:
    norm = normalize(text)
    for raw in kws:
        try:
            k = Keyword.parse(raw)
        except Exception as exc:  # noqa: BLE001
            err(f"{where}: bad keyword {raw!r} ({exc})")
            continue
        if k.kind not in ("term", "value", "position"):
            err(f"{where}: keyword {k.term!r} has kind {k.kind!r}")
        if not contains_phrase(norm, normalize(k.term)):
            err(f"{where}: keyword {k.term!r} does not appear in its own KB text")
        for syn in k.synonyms:
            if not normalize(syn):
                err(f"{where}: keyword {k.term!r} has an empty synonym")


def check_bank(entries: list[dict]) -> list[str]:
    problems: list[str] = []
    cache: dict[str, str] = {}
    seen: set[str] = set()
    for e in entries:
        if e.get("id") in seen:
            problems.append(f"{e.get('id')}: duplicate id")
        seen.add(e.get("id"))
        problems += check_entry(e, cache)
    models = {e.get("model") for e in entries}
    for m in KB_FILES:
        if m not in models:
            problems.append(f"bank has no entry for {m}; every model needs at least one")
    return problems


def load(path: Path = BANK) -> list[dict]:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data["entries"] if isinstance(data, dict) else data


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else BANK
    entries = load(path)
    problems = check_bank(entries) if len(argv) <= 2 or argv[2] != "--no-coverage" else [
        x for e in entries for x in check_entry(e, {})]
    if problems:
        print(f"{path}: {len(problems)} problem(s)")
        for x in problems:
            print("  - " + x)
        return 1
    print(f"{path}: {len(entries)} entries OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
