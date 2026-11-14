"""
The answer check: keyword matching. No LLM, no network.

An answer passes when every keyword of kb/smoke.yaml is said somewhere in it - the keyword
itself or one of its synonyms, as whole words - in any order and with any wording around it.
Nothing else is judged: not the order, not the sentences, not what else the agent said.

Both sides are normalised first (case, punctuation, curly quotes, spoken numbers, units,
simple plurals), so "Park/Drive switch" holds "park" and "forty to sixty P S I" matches
"40–60 PSI".
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
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

# Spoken fractions, as clearances are said aloud.
_FRACTIONS = [(re.compile(p), repl) for p, repl in (
    (r"\bone[\s-]+sixteenths?\b", "1/16"),
    (r"\bone[\s-]+thirty[\s-]+seconds?\b(?=\s+(?:of\s+an?\s+)?inch)", "1/32"),
    (r"\bone[\s-]+eighths?\b", "1/8"),
    (r"\bone[\s-]+quarters?\b", "1/4"),
    (r"\bthree[\s-]+eighths?\b", "3/8"),
    (r"\bfive[\s-]+eighths?\b", "5/8"),
    (r"\bone[\s-]+half\b", "1/2"),
    (r"\ba\s+half\b", "1/2"),
)]

# Multi-word unit spellings -> one token. Order matters (longest first).
_UNIT_PHRASES = [(re.compile(p), f" {repl} ") for p, repl in (
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
)]

_RANGE_SEP = re.compile(r"(?<=\d)\s*(?:–|—|-|to|through|and)\s*(?=\d)")
_NUMBER_WORD_SPLIT = re.compile(r"(\s+|-)")
_MARKDOWN = re.compile(r"\*\*|__|`")
_OF_AN_INCH = re.compile(r"(?<=\d)\s+of\s+an?\s+inch")
_THOUSANDS_COMMA = re.compile(r"(?<=\d),(?=\d{3}\b)")
_SPOKEN_POINT = re.compile(r"\b(\d+)\s+point\s+(\d+)\b")
_TRAILING_ZEROS = re.compile(r"\b(\d+)\.(\d*?)0+\b")
_DIGIT_THEN_UNIT = re.compile(r"(?<=\d)(?=[a-z%])")
_VOLT = re.compile(r"\bvolts?\b|\bv\b(?=\s|$)")
_STRAY_DOT = re.compile(r"(?<!\d)\.|\.(?!\d)")
_WORD_SLASH = re.compile(r"(?<=[a-z])\s*/\s*(?=[a-z])")
_NOT_TOKEN = re.compile(r"[^a-z0-9/%.²]+")


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
    tokens = _NUMBER_WORD_SPLIT.split(text)
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


# Pure, and validate() asks for the same keyword terms and synonyms over and over (every window
# of every step, every turn of a live call), so each distinct text is worked out once.
@lru_cache(maxsize=4096)
def normalize(text: str) -> str:
    """One canonical form for both KB keywords and agent text."""
    t = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = _MARKDOWN.sub("", t)  # markdown emphasis
    t = t.lower()
    for pattern, repl in _FRACTIONS:
        t = pattern.sub(repl, t)
    t = _spoken_numbers_to_digits(t)
    t = _OF_AN_INCH.sub(" inch", t)  # 1/16 of an inch -> 1/16 inch
    t = _THOUSANDS_COMMA.sub("", t)  # 7,000 -> 7000
    t = _SPOKEN_POINT.sub(r"\1.\2", t)  # "zero point nine" -> 0.9
    t = _TRAILING_ZEROS.sub(lambda m: m.group(1) + ("." + m.group(2) if m.group(2) else ""), t)  # 4.00 -> 4
    for pattern, repl in _UNIT_PHRASES:
        t = pattern.sub(repl, t)
    t = _DIGIT_THEN_UNIT.sub(" ", t)  # 30psi -> 30 psi, 96rpm
    t = _RANGE_SEP.sub(" to ", t)  # 40–60 / 40-60 / 40 through 60 -> 40 to 60
    t = _VOLT.sub("volt", t)
    # keep '/', '.', '%' inside numbers and units; everything else is a space
    t = _STRAY_DOT.sub(" ", t)
    t = _WORD_SLASH.sub(" ", t)  # park/drive -> park drive
    t = _NOT_TOKEN.sub(" ", t)
    tokens = [_singular(tok) for tok in t.split()]
    return " ".join(tokens)


def contains_phrase(haystack_norm: str, phrase_norm: str) -> bool:
    """The phrase, as whole words, in the text. Both sides come from normalize(): words one space
    apart, no line breaks - so padding with spaces finds word boundaries without a regex per phrase."""
    return bool(phrase_norm) and f" {phrase_norm} " in f" {haystack_norm} "



# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Keyword:
    term: str
    synonyms: tuple[str, ...] = ()

    @classmethod
    def parse(cls, raw: Any) -> Keyword:
        """A keyword from kb/smoke.yaml: a plain word or phrase, or {term, synonyms}."""
        if isinstance(raw, Keyword):
            return raw
        term, synonyms = (raw.get("term"), raw.get("synonyms") or []) if isinstance(raw, dict) else (raw, [])
        if isinstance(synonyms, str):
            synonyms = [synonyms]
        for value in (term, *synonyms):
            if isinstance(value, bool):  # YAML reads a bare on/off/yes/no as true/false
                raise ValueError(f"{raw!r}: YAML read a keyword as {value}; quote it, e.g. 'on'")
            if value is None or not normalize(str(value)):
                raise ValueError(f"{raw!r}: a keyword or synonym is empty")
        return cls(str(term).strip(), tuple(str(s).strip() for s in synonyms))

    def forms(self) -> list[str]:
        return [normalize(x) for x in (self.term, *self.synonyms)]

    def found_in(self, norm_text: str) -> str | None:
        """The form (the term or a synonym, normalised) the text holds; None if it holds none."""
        return next((f for f in self.forms() if contains_phrase(norm_text, f)), None)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class KeywordResult:
    keyword: Keyword
    said_as: str | None = None  # the form found, normalised; None = never said
    said: str = ""  # the sentence of the answer it was found in
    turn: int | None = None  # which answer turn, from 0

    @property
    def term(self) -> str:
        return self.keyword.term

    @property
    def passed(self) -> bool:
        return self.said_as is not None

    def as_dict(self) -> dict[str, Any]:
        return {
            "term": self.term,
            "synonyms": list(self.keyword.synonyms),
            "passed": self.passed,
            "saidAs": self.said_as or "",
            "said": self.said,
            "turn": self.turn,
        }


@dataclass
class Validation:
    items: list[KeywordResult]

    @property
    def passed(self) -> bool:
        """Every keyword was said."""
        return bool(self.items) and all(i.passed for i in self.items)

    @property
    def score(self) -> float:
        return sum(i.passed for i in self.items) / len(self.items) if self.items else 0.0

    @property
    def failures(self) -> list[KeywordResult]:
        return [i for i in self.items if not i.passed]

    def explain(self) -> str:
        lines = [f"{len(self.items) - len(self.failures)} of {len(self.items)} keywords said"]
        for i in self.items:
            lines.append(f"  [{'SAID' if i.passed else 'NOT SAID':>8}] {i.term}" + (f": {i.said}" if i.passed else ""))
        return "\n".join(lines)

    def as_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "score": round(self.score, 4), "items": [i.as_dict() for i in self.items]}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

# Sentence ends, and line breaks (a texted list puts one step per line). A list number ("2. ")
# stays with its step.
_SENTENCE = re.compile(r"(?<=[.!?])(?<!\b\d\.)(?<!\b\d\d\.)\s+|\s*\n\s*")


def _sentences(turn: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(turn) if s.strip()]


def validate(keywords: Iterable[Keyword | str | dict[str, Any]], answer_turns: list[str]) -> Validation:
    """Each keyword against the agent's answer turns (every agent turn after the question, in
    order); for each one found, the first sentence that holds it."""
    turns = [(n, t, normalize(t)) for n, t in enumerate(answer_turns)]
    items = []
    for kw in map(Keyword.parse, keywords):
        result = KeywordResult(kw)
        for n, text, norm in turns:
            if form := kw.found_in(norm):
                # The sentence that says it; the whole turn when it straddles two sentences.
                said = next((s for s in _sentences(text) if kw.found_in(normalize(s))), text)
                result.said_as, result.said, result.turn = form, said, n
                break
        items.append(result)
    return Validation(items)
