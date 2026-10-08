"""
Deterministic KB-steps validator. No LLM, no network.

An answer passes only when every KB step and every KB caution of the question
bank entry passes. A step passes when all of its required keywords (or a listed
synonym for each) appear in the agent's text for that step, whatever the
sentence around them. Six ways to fail:

  missing      a KB step whose keywords are found nowhere in the answer
  out_of_order the steps are there, but not in KB order
  merged       two KB steps matched inside one agent step (or collapsed into one line)
  missing_caution    a KB caution whose keywords are found nowhere
  misplaced_caution  a step caution that is not in, or right next to, its step
  wrong_value  a number or position that differs from the KB (60 s for 30 s, IDLE for RUN)

Both sides are normalised first (case, punctuation, curly quotes, spoken numbers,
units, simple plurals), so "forty to sixty P S I" matches "40–60 PSI".

The answer is split into steps on the agent's own markers - numbering
("1.", "Step 2"), ordinals ("first", "next", "then", "after that", "finally") -
and each agent turn starts a new step. With no markers at all it falls back to
sentences. The split is part of the result so a failure can be checked by eye.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_UNITS_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19,
}
_TENS_WORDS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fourty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
_SCALE_WORDS = {"hundred": 100, "thousand": 1000}
_NUMBER_WORDS = set(_UNITS_WORDS) | set(_TENS_WORDS) | set(_SCALE_WORDS)

# Spoken fractions the KBs use for clearances.
_FRACTIONS = {
    r"\bone[\s-]+sixteenths?\b": "1/16",
    r"\bone[\s-]+thirty[\s-]+seconds?\b(?=\s+(?:of\s+an?\s+)?inch)": "1/32",
    r"\bone[\s-]+eighths?\b": "1/8",
    r"\bone[\s-]+quarters?\b": "1/4",
    r"\bthree[\s-]+eighths?\b": "3/8",
    r"\bfive[\s-]+eighths?\b": "5/8",
    r"\bone[\s-]+half\b": "1/2",
    r"\ba\s+half\b": "1/2",
}

# Multi-word unit spellings -> one token. Order matters (longest first).
_UNIT_PHRASES = [
    (r"\bpounds?\s+per\s+square\s+inch\b", "psi"),
    (r"\bp\s*\.?\s*s\s*\.?\s*i\b\.?", "psi"),
    (r"\bfeet\s+per\s+minute\b", "fpm"),
    (r"\bf\s*\.?\s*p\s*\.?\s*m\b\.?", "fpm"),
    (r"\brevolutions?\s+per\s+minute\b", "rpm"),
    (r"\br\s*\.?\s*p\s*\.?\s*m\b\.?", "rpm"),
    (r"\bpounds?\s+per\s+square\s+yards?\b", "lbyd2"),
    (r"\blbs?\s*/\s*yd\s*(?:2|²)", "lbyd2"),
    (r"\bvolts?\s+(?:dc|d\s*c)\b|\bvdc\b", "volt dc"),
    (r"\bvolts?\s+(?:ac|a\s*c)\b|\bvac\b", "volt ac"),
    (r"\bdegrees?\s+(?:fahrenheit|f)\b", "degf"),
    (r"°\s*f\b", "degf"),
    (r"\bamperes?\b|\bamps?\b", "amp"),
    (r"\bseconds?\b|\bsecs?\b", "second"),
    (r"\bminutes?\b|\bmins?\b", "minute"),
    (r"\binch(?:es)?\b|(?<=\d)\s*\"", "inch"),
    (r"\bgallons?\b", "gallon"),
    (r"\bohms?\b|Ω", "ohm"),
]

UNIT_TOKENS = {"psi", "fpm", "rpm", "lbyd2", "degf", "amp", "second", "minute",
               "inch", "gallon", "ohm", "volt", "%"}

_RANGE_SEP = re.compile(r"(?<=\d)\s*(?:–|—|-|to|through|and)\s*(?=\d)")


def _words_to_number(words: list[str]) -> int | None:
    total, current, seen = 0, 0, False
    for w in words:
        if w in _UNITS_WORDS:
            current += _UNITS_WORDS[w]
        elif w in _TENS_WORDS:
            current += _TENS_WORDS[w]
        elif w == "hundred":
            current = (current or 1) * 100
        elif w == "thousand":
            total += (current or 1) * 1000
            current = 0
        else:
            return None
        seen = True
    return total + current if seen else None


def _spoken_numbers_to_digits(text: str) -> str:
    """'forty to sixty' -> '40 to 60'; 'twenty two hundred' -> '2200';
    'seven thousand' -> '7000'. Runs of number words become one number."""
    tokens = re.split(r"(\s+|-)", text)
    out: list[str] = []
    run: list[str] = []
    pending_sep: list[str] = []

    def flush() -> None:
        if not run:
            return
        words = [w for w in run if w != "and"]
        # "twenty two hundred" (spoken 2200): tens+units then 'hundred'
        if len(words) >= 3 and words[-1] == "hundred" and words[0] in _TENS_WORDS:
            head = _words_to_number(words[:-1])
            out.append(str(head * 100) if head is not None else " ".join(run))
        else:
            n = _words_to_number(words)
            out.append(str(n) if n is not None else " ".join(run))
        run.clear()

    for tok in tokens:
        if tok in ("", None):
            continue
        low = tok.lower()
        if low in _NUMBER_WORDS or (low == "and" and run):
            if run and pending_sep:
                pending_sep.clear()
            run.append(low)
            continue
        if run and (tok.isspace() or tok == "-"):
            pending_sep.append(tok)
            continue
        if run and run[-1] == "and":
            run.pop()
            flush()
            out.append(" and ")
        else:
            flush()
        out.extend(pending_sep)
        pending_sep.clear()
        out.append(tok)
    if run and run[-1] == "and":
        run.pop()
    flush()
    out.extend(pending_sep)
    return "".join(out)


def _singular(token: str) -> str:
    if len(token) > 4 and token.endswith(("ches", "shes", "sses", "xes", "zes")):
        return token[:-2]
    if len(token) > 3 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def normalize(text: str) -> str:
    """One canonical form for both KB keywords and agent text."""
    t = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"\*\*|__|`", "", t)  # markdown emphasis
    t = t.lower()
    for pattern, repl in _FRACTIONS.items():
        t = re.sub(pattern, repl, t)
    t = _spoken_numbers_to_digits(t)
    t = re.sub(r"(?<=\d)\s+of\s+an?\s+inch", " inch", t)  # 1/16 of an inch -> 1/16 inch
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)  # 7,000 -> 7000
    t = re.sub(r"\b(\d+)\s+point\s+(\d+)\b", r"\1.\2", t)  # "zero point nine" -> 0.9
    t = re.sub(r"\b(\d+)\.(\d*?)0+\b", lambda m: m.group(1) + ("." + m.group(2) if m.group(2) else ""), t)  # 4.00 -> 4
    for pattern, repl in _UNIT_PHRASES:
        t = re.sub(pattern, f" {repl} ", t)
    t = re.sub(r"(?<=\d)(?=[a-z%])", " ", t)  # 30psi -> 30 psi, 96rpm
    t = _RANGE_SEP.sub(" to ", t)  # 40–60 / 40-60 / 40 through 60 -> 40 to 60
    t = re.sub(r"\bvolts?\b|\bv\b(?=\s|$)", "volt", t)
    # keep '/', '.', '%' inside numbers and units; everything else is a space
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)
    t = re.sub(r"(?<=[a-z])\s*/\s*(?=[a-z])", " ", t)  # park/drive -> park drive
    t = re.sub(r"[^a-z0-9/%.²]+", " ", t)
    tokens = [_singular(tok) for tok in t.split()]
    return " ".join(tokens)


def contains_phrase(haystack_norm: str, phrase_norm: str) -> bool:
    if not phrase_norm:
        return False
    return re.search(r"(?:^| )" + re.escape(phrase_norm) + r"(?: |$)", haystack_norm) is not None


# ---------------------------------------------------------------------------
# Splitting the answer into steps
# ---------------------------------------------------------------------------

_ORDINALS = (
    r"first(?:ly)?|second(?:ly)?|third(?:ly)?|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
    r"next|then|after that|afterwards|finally|lastly|last"
)
# Markers count only at the start of a turn or of a sentence, so "a warning
# first:" or "the next step" mid-sentence never splits a step in two.
_MARKER = re.compile(
    r"(?:^|(?<=[.;:!?]))\s*(?P<m>"
    r"(?:step\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen)\b\s*[:.,—–-]?)"
    r"|(?:\(?\d{1,2}[.)]\s)"
    r"|(?:(?:" + _ORDINALS + r")\b\s*,?)"
    r")",
    re.IGNORECASE,
)
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


@dataclass
class Segment:
    index: int
    turn: int
    text: str
    norm: str


def split_steps(turns: list[str]) -> tuple[list[Segment], str]:
    """(segments, method). method is 'markers' when the agent's own numbering or
    ordinals were used, 'sentences' when it fell back to sentence boundaries."""
    has_markers = any(_MARKER.search(t) for t in turns)
    pieces: list[tuple[int, str]] = []
    for ti, turn in enumerate(turns):
        if has_markers:
            starts = [m.start("m") for m in _MARKER.finditer(turn)]
            bounds = sorted(set([0] + starts + [len(turn)]))
            parts = [turn[a:b] for a, b in zip(bounds, bounds[1:])]
        else:
            parts = _SENTENCE.split(turn)
        for p in parts:
            p = p.strip(" \n\t-•*")
            if re.search(r"[A-Za-z0-9]", p):
                pieces.append((ti, p))
    segments = [Segment(i, ti, txt, normalize(txt)) for i, (ti, txt) in enumerate(pieces)]
    return segments, ("markers" if has_markers else "sentences")


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------

# Positions/settings that contradict each other when one replaces the other.
POSITION_GROUPS = [
    {"park", "drive"},
    {"idle", "run"},
    {"on", "off"},
    {"open", "closed", "close"},
    {"neutral", "forward", "reverse"},
    {"up", "down"},
    {"left", "right"},
    {"clockwise", "counterclockwise"},
    {"extend", "retract"},
    {"start", "stop"},
]


@dataclass
class Keyword:
    term: str
    synonyms: list[str] = field(default_factory=list)
    kind: str = "term"  # term | value | position

    @classmethod
    def parse(cls, raw: Any) -> "Keyword":
        if isinstance(raw, str):
            raw = {"term": raw}
        term = str(raw["term"])
        kind = raw.get("kind") or _infer_kind(term)
        return cls(term=term, synonyms=[str(s) for s in raw.get("synonyms", []) or []], kind=kind)

    def forms(self) -> list[str]:
        return [f for f in (normalize(x) for x in [self.term, *self.synonyms]) if f]

    def found_in(self, norm_text: str) -> str | None:
        for f in self.forms():
            if contains_phrase(norm_text, f):
                return f
        return None


def _infer_kind(term: str) -> str:
    n = normalize(term)
    if re.search(r"\d", n):
        return "value"
    if any(n in g for g in POSITION_GROUPS):
        return "position"
    return "term"


_NUM_UNIT = re.compile(r"(\d+(?:\.\d+)?(?:/\d+)?(?: to \d+(?:\.\d+)?)?) (" + "|".join(
    re.escape(u) for u in sorted(UNIT_TOKENS, key=len, reverse=True)) + r")\b")


def numbers_with_units(norm_text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _NUM_UNIT.finditer(norm_text)]


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

RESULT_LABELS = {
    "pass": "Pass",
    "missing": "Missing",
    "out_of_order": "Out of order",
    "merged": "Merged",
    "missing_caution": "Missing",
    "misplaced_caution": "Misplaced caution",
    "wrong_value": "Wrong value",
}


@dataclass
class ItemResult:
    kind: str  # step | caution
    ref: str  # "Step 3" / "Caution C1 (step 6)"
    kb_text: str
    result: str  # key of RESULT_LABELS
    reason: str = ""
    segments: list[int] = field(default_factory=list)
    said: str = ""
    found: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.result == "pass"

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "ref": self.ref,
            "kbText": self.kb_text,
            "result": self.result,
            "resultLabel": RESULT_LABELS[self.result],
            "reason": self.reason,
            "segments": self.segments,
            "said": self.said,
            "keywordsFound": self.found,
            "keywordsMissing": self.missing,
        }


# The live call passes when this share of KB items (steps and cautions) matched
# and none of the misses is a wrong value. Override with KB_PASS_THRESHOLD (0-1).
PASS_THRESHOLD = float(os.getenv("KB_PASS_THRESHOLD") or "0.95")  # blank (unset CI input) = default


@dataclass
class Validation:
    items: list[ItemResult]
    segments: list[Segment]
    split_method: str

    @property
    def passed(self) -> bool:
        """Strict: every item matched. The unit tests and the question bank check use this."""
        return bool(self.items) and all(i.passed for i in self.items)

    @property
    def score(self) -> float:
        return sum(i.passed for i in self.items) / len(self.items) if self.items else 0.0

    @property
    def wrong_values(self) -> list[ItemResult]:
        return [i for i in self.items if i.result == "wrong_value"]

    def meets_threshold(self, threshold: float | None = None) -> bool:
        """What the live call uses: enough items matched, and never a wrong value, because
        a wrong number or position is the agent giving wrong guidance."""
        threshold = PASS_THRESHOLD if threshold is None else threshold
        return bool(self.items) and not self.wrong_values and self.score + 1e-9 >= threshold

    @property
    def failures(self) -> list[ItemResult]:
        return [i for i in self.items if not i.passed]

    def explain(self) -> str:
        lines = [f"split by {self.split_method} into {len(self.segments)} part(s)"]
        for i in self.items:
            mark = "PASS" if i.passed else RESULT_LABELS[i.result].upper()
            lines.append(f"  [{mark:>17}] {i.ref}: {i.reason or 'ok'}")
        return "\n".join(lines)

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": round(self.score, 4),
            "threshold": PASS_THRESHOLD,
            "meetsThreshold": self.meets_threshold(),
            "splitMethod": self.split_method,
            "segments": [{"index": s.index, "turn": s.turn, "text": s.text} for s in self.segments],
            "items": [i.as_dict() for i in self.items],
        }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _window_text(segments: list[Segment], start: int, size: int) -> str:
    return " ".join(s.norm for s in segments[start:start + size])


def _windows(keywords: list[Keyword], segments: list[Segment]) -> list[tuple[int, int]]:
    """Windows (start, size) whose text holds every keyword given. Single segments
    first; a window of two only when no single segment does (a step spoken over
    two sentences)."""
    for size in (1, 2):
        wins = [(i, size) for i in range(len(segments) - size + 1)
                if all(k.found_in(_window_text(segments, i, size)) for k in keywords)]
        if wins:
            return wins
    return []


def _anchors(keywords: list[Keyword]) -> list[Keyword]:
    """The keywords that locate a step: its terms. Values and positions are then
    judged inside the located step, so a contradicted value is reported as
    Wrong value rather than the whole step going Missing."""
    for kind in ("term", "value"):
        found = [k for k in keywords if k.kind == kind]
        if found:
            return found
    return keywords


def _locate(keywords: list[Keyword], segments: list[Segment]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """(windows with every keyword, windows with the anchor keywords)."""
    return _windows(keywords, segments), _windows(_anchors(keywords), segments)


def _judge_values(keywords: list[Keyword], text_norm: str) -> tuple[str, str, list[str]]:
    """Inside a located step: every value/position keyword said as in the KB ->
    pass; replaced by a different one -> wrong_value; simply not said -> missing.
    A KB value that is said is never contradicted by an extra number elsewhere in
    the step (the agent may mention a gauge size or a range mid-point)."""
    wrong: list[str] = []
    absent: list[str] = []
    said_numbers = numbers_with_units(text_norm)
    for k in keywords:
        if k.found_in(text_norm):
            continue
        if k.kind == "value":
            kb_vals = [nu for f in k.forms() for nu in numbers_with_units(f)]
            units = {u for _, u in kb_vals}
            allowed = {v for v, _ in kb_vals}
            rivals = [f"{v} {u}" for v, u in said_numbers
                      if u in units and v not in allowed and not any(_within_range(v, a) for a in allowed)]
            if rivals:
                wrong.append(f"said {rivals[0]} where the KB says {k.term}")
                continue
        elif k.kind == "position":
            mine = normalize(k.term)
            group = next((g for g in POSITION_GROUPS if mine in g), set())
            rivals = [p for p in group if p != mine and contains_phrase(text_norm, p)]
            if rivals:
                wrong.append(f"said {rivals[0].upper()} where the KB says {k.term.upper()}")
                continue
        absent.append(k.term)
    if wrong:
        return "wrong_value", "; ".join(wrong), absent
    if absent:
        return "missing", f"never said: {', '.join(absent)}", absent
    return "pass", "", []


def _within_range(value: str, allowed: str) -> bool:
    """A single number the agent said that sits inside a KB range ('50' in '40 to 60')
    is not a contradiction."""
    m = re.fullmatch(r"(\d+(?:\.\d+)?) to (\d+(?:\.\d+)?)", allowed)
    try:
        v = float(value)
    except ValueError:
        return False
    return bool(m) and float(m.group(1)) <= v <= float(m.group(2))


def _said(segments: list[Segment], win: tuple[int, int]) -> str:
    return " ".join(s.text for s in segments[win[0]:win[0] + win[1]])


def validate(entry: dict[str, Any], answer_turns: list[str]) -> Validation:
    """Check every KB step and caution of a question bank entry against the
    agent's answer turns (every agent turn after the question, in order)."""
    segments, method = split_steps(answer_turns)
    items: list[ItemResult] = []
    whole = _window_text(segments, 0, len(segments))

    steps = entry.get("steps") or []
    step_windows: dict[int, tuple[int, int]] = {}
    prev_start = -1
    used_single: dict[int, int] = {}  # segment index -> step number that claimed it alone

    for n, step in enumerate(steps, start=1):
        number = int(step.get("n", n))
        keywords = [Keyword.parse(k) for k in step.get("keywords", [])]
        ref = f"Step {number}"
        kb_text = str(step.get("text", "")).strip()
        if not keywords:
            items.append(ItemResult("step", ref, kb_text, "missing",
                                    "question bank entry has no keywords for this step"))
            continue

        full, anchored = _locate(keywords, segments)
        if not anchored:
            absent = [k.term for k in keywords if not k.found_in(whole)]
            reason = (f"never mentioned: {', '.join(absent)}" if absent else
                      "the step's keywords are spread across several parts of the answer, never stated as one step")
            items.append(ItemResult("step", ref, kb_text, "missing", reason,
                                    found=[k.term for k in keywords if k.found_in(whole)], missing=absent))
            continue

        # Prefer, in order: a full match after the previous step, an anchor match
        # after it, then a match in the previous step's own part (merged), then
        # one before it (out of order).
        result, reason = "pass", ""
        after_full = [w for w in full if w[0] > prev_start]
        after_anchor = [w for w in anchored if w[0] > prev_start]
        same = [w for w in full + anchored if w[0] == prev_start]
        if after_full:
            win = after_full[0]
        elif after_anchor:
            win = after_anchor[0]
        elif same:
            win = same[0]
            result = "merged"
            reason = f"stated in the same part of the answer as step {used_single.get(win[0], number - 1)}"
        else:
            win = (full or anchored)[0]
            result = "out_of_order"
            reason = "given before an earlier KB step"

        if result == "pass" and win[1] == 1 and win[0] in used_single:
            result = "merged"
            reason = f"stated in the same part of the answer as step {used_single[win[0]]}"

        text = _window_text(segments, *win)
        verdict, why, absent = _judge_values(keywords, text)
        if result == "pass" and verdict != "pass":
            result, reason = verdict, why

        items.append(ItemResult("step", ref, kb_text, result, reason,
                                segments=list(range(win[0], win[0] + win[1])), said=_said(segments, win),
                                found=[k.term for k in keywords if k.term not in absent], missing=absent))
        step_windows[number] = win
        if win[1] == 1:
            used_single.setdefault(win[0], number)
        if result != "out_of_order":
            prev_start = max(prev_start, win[0])

    # Two KB steps that share one part of the answer are both marked merged, so
    # the earlier one shows in the report too.
    by_segment: dict[int, list[ItemResult]] = {}
    for it in items:
        if it.kind == "step" and len(it.segments) == 1:
            by_segment.setdefault(it.segments[0], []).append(it)
    for its in by_segment.values():
        if len(its) > 1:
            for it in its:
                if it.result == "pass":
                    others = [o.ref for o in its if o is not it]
                    it.result = "merged"
                    it.reason = f"stated in the same part of the answer as {', '.join(others).lower()}"

    for ci, caution in enumerate(entry.get("cautions") or [], start=1):
        keywords = [Keyword.parse(k) for k in caution.get("keywords", [])]
        cid = caution.get("id", f"C{ci}")
        anchor = caution.get("step", "procedure")
        ref = f"Caution {cid}" + ("" if anchor == "procedure" else f" (step {anchor})")
        kb_text = str(caution.get("text", "")).strip()
        if not keywords:
            items.append(ItemResult("caution", ref, kb_text, "missing_caution",
                                    "question bank entry has no keywords for this caution"))
            continue
        full, anchored = _locate(keywords, segments)
        if not anchored:
            absent = [k.term for k in keywords if not k.found_in(whole)]
            items.append(ItemResult(
                "caution", ref, kb_text, "missing_caution",
                f"caution never given: {', '.join(absent)}" if absent
                else "caution's keywords are spread across the answer, never stated together",
                found=[k.term for k in keywords if k.found_in(whole)], missing=absent))
            continue

        result, reason = "pass", ""
        pool = full or anchored
        chosen = pool[0]
        if anchor != "procedure":
            sw = step_windows.get(int(anchor))
            if sw is not None:
                lo, hi = sw[0] - 1, sw[0] + sw[1]  # inside the step, or the part right before/after
                def near(ws: list[tuple[int, int]]) -> list[tuple[int, int]]:
                    return [w for w in ws if lo <= w[0] and w[0] + w[1] - 1 <= hi]
                if near(full) or near(anchored):
                    chosen = (near(full) or near(anchored))[0]
                else:
                    result = "misplaced_caution"
                    reason = f"given, but not with step {anchor}"
        verdict, why, absent = _judge_values(keywords, _window_text(segments, *chosen))
        if result == "pass" and verdict != "pass":
            result, reason = ("missing_caution", f"caution given without: {', '.join(absent)}") \
                if verdict == "missing" else (verdict, why)
        items.append(ItemResult("caution", ref, kb_text, result, reason,
                                segments=list(range(chosen[0], chosen[0] + chosen[1])),
                                said=_said(segments, chosen),
                                found=[k.term for k in keywords if k.term not in absent], missing=absent))

    return Validation(items=items, segments=segments, split_method=method)
