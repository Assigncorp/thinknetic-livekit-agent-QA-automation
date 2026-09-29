"""
Every number the agent said, in a form that can be checked against a manual.

This is the parsing half of the closed-world oracle described in
docs/deterministic-kb-testing.md. The claim it rests on is narrow and true: the
five knowledge bases contain every legitimate measurement this agent can utter
about a machine. So a measurement in a transcript that does not resolve to the
corpus was invented - and that is decidable by parsing, with no model and no
threshold.

Two directions are needed and they are not symmetric:

  * The KB writes `400 FPM`, `0.40 amps`, `240°F`, `1/16"`.
  * The agent is voice-first and SAYS "four hundred feet per minute", "zero
    point four zero amps", "two hundred forty degrees".

anchors.py already solves this one anchor at a time: given a KB fact, generate
the spoken forms and look for them. That is the right shape for "did it cite
THIS fact" and the wrong shape for "is EVERY number it said legitimate", which
needs the inverse - read arbitrary text and hand back the measurements it
contains, whichever way they were written.

Stdlib only, and deliberately so: tools/build_resources.py imports this module
to compile the corpus index at build time, and tools/ is a separate uv project
whose only dependency is openpyxl. One grammar, two callers, no hand-porting -
the mistake this whole design exists to stop repeating.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import anchors

# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

# anchors.UNITS maps a KB-written unit to the ways it may be SPOKEN. Here we
# need the inverse, collapsed onto one canonical key per physical quantity, so
# that `12 VDC` and "twelve volts" land on the same (value, unit) pair and a
# unit swap is still detectable. Derived from anchors.UNITS rather than retyped:
# adding a spoken form there gains it here, and ORC-05 asserts the two agree.
CANONICAL: dict[str, str] = {
    "fpm": "fpm",
    "psi": "psi",
    "rpm": "rpm",
    "vdc": "vdc",
    "volts": "vdc",
    "volt": "vdc",
    "amps": "amp",
    "amp": "amp",
    "amperes": "amp",
    "amperage": "amp",
    "ohms": "ohm",
    "ohm": "ohm",
    "gallons": "gallon",
    "gallon": "gallon",
    "gal": "gallon",
    "f": "degf",
    "inch": "inch",
    "inches": "inch",
}


def _phrase_map() -> dict[str, str]:
    """Every spoken or written form -> canonical unit, longest phrase first.

    Built from anchors.UNITS so the two modules cannot drift. A form that maps
    to two different canonical units (`volts` is listed under both `vdc` and
    `volts` in anchors.UNITS) resolves through CANONICAL, which is the single
    place that decides what a quantity is called.
    """
    out: dict[str, str] = {}
    for written, spoken_forms in anchors.UNITS.items():
        canon = CANONICAL.get(written.lower(), written.lower())
        out.setdefault(written.lower(), canon)
        for form in spoken_forms:
            form = form.strip().lower()
            if not form:
                continue
            # A bare quote is the inch mark; it is handled by the digit scanner,
            # not the phrase scanner, because it never follows a spoken number.
            if form == '"':
                continue
            out.setdefault(form, CANONICAL.get(form, canon))
    for form, canon in CANONICAL.items():
        out.setdefault(form, canon)
    return out


PHRASES: dict[str, str] = _phrase_map()
# Longest first so "feet per minute" wins over a hypothetical "feet".


def canonical_unit(text: str) -> str | None:
    """Canonical unit for a written or spoken unit phrase, or None."""
    cleaned = re.sub(r"[^a-z/ ]", "", text.strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return PHRASES.get(cleaned)


# ---------------------------------------------------------------------------
# Spoken numbers
# ---------------------------------------------------------------------------

ONES = {word: i for i, word in enumerate(anchors.ONES)}
TENS = {word: i * 10 for i, word in enumerate(anchors.TENS) if word}
MULTIPLIERS = {"hundred": 100, "thousand": 1000}
FILLER = {"and", "a"}
CONJUNCTIONS = {"and", "or", "to"}

NUMBER_WORDS = set(ONES) | set(TENS) | set(MULTIPLIERS) | {"point", "oh"} | FILLER


def parse_number_words(words: list[str]) -> float | None:
    """
    "four hundred" -> 400.0, "twenty five hundred" -> 2500.0,
    "two thousand five hundred" -> 2500.0, "zero point four zero" -> 0.4.

    Returns None when the run is not a number (a bare "and", a stray "a").

    The twenty-five-hundred case is not a curiosity: anchors.spell_integer
    generates it because it is how people say these numbers out loud, so the
    inverse has to accept it or the matcher and the extractor disagree about
    the same utterance. ORC-01 asserts the round trip.
    """
    if not words:
        return None

    if "point" in words:
        cut = words.index("point")
        whole_words, frac_words = words[:cut], words[cut + 1 :]
    else:
        whole_words, frac_words = words, []

    total = 0
    current = 0
    seen_digit = False
    for word in whole_words:
        if word in FILLER:
            continue
        if word in ONES:
            current += ONES[word]
            seen_digit = True
        elif word in TENS:
            current += TENS[word]
            seen_digit = True
        elif word == "hundred":
            current = (current or 1) * 100
            seen_digit = True
        elif word == "thousand":
            total += (current or 1) * 1000
            current = 0
            seen_digit = True
        else:
            return None

    whole = total + current
    if not seen_digit and not frac_words:
        return None

    if not frac_words:
        return float(whole)

    digits = ""
    for word in frac_words:
        if word == "oh":
            digits += "0"
        elif word in ONES and ONES[word] < 10:
            digits += str(ONES[word])
        else:
            break
    if not digits:
        return float(whole) if seen_digit else None
    return float(f"{whole}.{digits}")


# ---------------------------------------------------------------------------
# Measurements
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Measurement:
    """One (value, unit) pair, and the verbatim span it was read from."""

    value: float
    unit: str
    raw: str
    start: int
    end: int

    @property
    def key(self) -> tuple[float, str]:
        # Rounded because 0.40 and 0.4 are the same specification, and because
        # a float read off two different spellings must hash the same. Six
        # places, not four: clearances are written as fractions and 1/32 is
        # 0.03125, which four places rounds into a different number from the
        # one the manual states.
        return (round(self.value, 6), self.unit)

    def __str__(self) -> str:
        return f"{self.value:g} {self.unit}"


def key_of(measurement: Measurement) -> str:
    """The string form of a measurement's identity.

    ONE function, called by tools/oracle_build.py when it compiles the corpus
    and by judge/src/oracle.py when it looks a transcript's numbers up in it.
    Two spellings of this - one rounding, one not - is how an index ends up
    holding `0.03125|inch` while the lookup asks for `0.0312|inch` and every
    clearance silently reads as fabricated.
    """
    value, unit = measurement.key
    return f"{value:g}|{unit}"


# `1000 PSI`, `0.40 amps`, `240°F`, `30-amp`, `1/16"`, `2,500 FPM`.
DIGIT_MEASUREMENT = re.compile(
    r"(?<![0-9A-Za-z.])"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+/\d+|\d+(?:\.\d+)?)"
    r"\s*(?:°\s*)?[-\s]?\s*"
    r"(?P<unit>\"|[A-Za-z]+(?:\s+per\s+[A-Za-z]+|\s+(?:dc|fahrenheit|f))?)",
    re.IGNORECASE,
)

# A number, then a range separator, immediately before a measurement.
# Unspaced dash only ("1200–1400", "55-60"): the KBs always write ranges that
# way, while a SPACED dash is punctuation ("Step 3 - 400 PSI" is not 3 PSI).
# "between X and Y": "and" only after "between", so "pin 21 and 400 PSI" never
# becomes 21 PSI. VERIFIED 2026-09-28: "between 0.900 and 1.000 amp".
RANGE_LOW = re.compile(
    r"(?:(?<![\d.,-])(?P<num>\d[\d,]*(?:\.\d+)?|\.\d+)(?:[\u2013\u2014-]|\s+to\s+)"
    r"|\bbetween\s+(?P<bnum>\d[\d,]*(?:\.\d+)?|\.\d+)\s+and\s+)$",
    re.IGNORECASE,
)

WORD_RUN = re.compile(r"[a-z]+(?:[\s-]+[a-z]+)*", re.IGNORECASE)


def _value_of(raw: str) -> float | None:
    raw = raw.replace(",", "").strip()
    if "/" in raw:
        num, _, den = raw.partition("/")
        try:
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(raw)
    except ValueError:
        return None


def _digit_measurements(text: str) -> list[Measurement]:
    found: list[Measurement] = []
    for match in DIGIT_MEASUREMENT.finditer(text):
        unit_raw = match.group("unit")
        unit = '"' if unit_raw.strip() == '"' else canonical_unit(unit_raw)
        if unit == '"':
            unit = "inch"
        if unit is None:
            # Try the head word alone: "400 FPM gauge" hands back "FPM gauge"
            # only when the two-word branch fired, so retry on the first token.
            head = unit_raw.split()[0] if unit_raw.split() else ""
            unit = canonical_unit(head)
            if unit is None:
                continue
        value = _value_of(match.group("num"))
        if value is None:
            continue
        # The low end of a written range shares the unit: "1200–1400 PSI",
        # "380–420 PSI", "200–500 FPM". Without this only the high end was ever
        # compiled into the corpus, so a correct spoken "twelve hundred to
        # fourteen hundred PSI" read as half wrong (VERIFIED 2026-09-28).
        window = text[max(0, match.start() - 32) : match.start()]
        low = RANGE_LOW.search(window)
        if low:
            group = "num" if low.group("num") else "bnum"
            low_value = _value_of(low.group(group))
            low_start = match.start() - (len(window) - low.start(group))
            if low_value is not None and low_value < value:
                found.append(Measurement(low_value, unit, text[low_start : match.end()].strip(), low_start, match.start()))
        found.append(
            Measurement(value, unit, match.group(0).strip(), match.start(), match.end())
        )
    return found


def _spoken_measurements(text: str) -> list[Measurement]:
    """Number words followed by a unit phrase: 'four hundred feet per minute'."""
    found: list[Measurement] = []
    lowered = text.lower()

    for run in WORD_RUN.finditer(lowered):
        tokens = re.split(r"[\s-]+", run.group(0))
        pending: tuple[float, int, int] | None = None  # (value, start, token index it expects next)
        positions: list[int] = []
        offset = run.start()
        for token in tokens:
            index = lowered.find(token, offset)
            positions.append(index)
            offset = index + len(token)

        i = 0
        while i < len(tokens):
            if tokens[i] not in NUMBER_WORDS or tokens[i] in FILLER:
                i += 1
                continue
            j = i
            while j < len(tokens) and tokens[j] in NUMBER_WORDS:
                j += 1
            # "and" continues a number only into a SMALLER part ("two hundred
            # and five" = 205). Followed by its own hundred/thousand it starts a
            # new one: "two hundred and five hundred feet per minute" is 200 and
            # 500 FPM, not 20,500 - VERIFIED 2026-09-28 on a live call, where the
            # fused reading failed a correct answer.
            for k in range(i + 1, j):
                # ...and a second decimal after "and" is a new number too:
                # "zero point nine and one point zero amp" is 0.9 and 1.0 A.
                # The whole rule: "and" joins parts of ONE number only right
                # after hundred/thousand ("two hundred and five" = 205), and even
                # then not when what follows carries its own magnitude or
                # decimal. Anywhere else it joins two numbers: "fifty five and
                # sixty PSI" is 55 and 60 (VERIFIED 2026-09-28 - read as 115 PSI).
                joins_one = tokens[k - 1] in MULTIPLIERS and not any(
                    t in MULTIPLIERS or t == "point" for t in tokens[k + 1 : j]
                )
                if tokens[k] == "and" and not joins_one and any(t in ONES or t in TENS for t in tokens[i:k]):
                    j = k
                    break
            number_tokens = tokens[i:j]
            # Trim trailing filler so "four hundred and" parses as 400.
            while number_tokens and number_tokens[-1] in FILLER:
                number_tokens.pop()
                j -= 1
            value = parse_number_words(number_tokens)
            if value is None:
                i = j + 1
                continue

            unit = None
            unit_end = j
            for width in (4, 3, 2, 1):
                if j + width > len(tokens):
                    continue
                phrase = " ".join(tokens[j : j + width])
                resolved = PHRASES.get(phrase)
                if resolved:
                    unit, unit_end = resolved, j + width
                    break
            if unit is not None:
                start = positions[i]
                end = positions[unit_end - 1] + len(tokens[unit_end - 1])
                # A unitless number joined to this one by and/or/to shares its
                # unit: "fifty five to sixty PSI", "two hundred and five hundred
                # feet per minute". Without this the first half of every spoken
                # range went unchecked.
                if pending is not None and pending[2] == i:
                    p_value, p_start, _ = pending
                    p_end = positions[i - 2] + len(tokens[i - 2])
                    found.append(Measurement(p_value, unit, text[p_start:p_end], p_start, p_end))
                found.append(Measurement(value, unit, text[start:end], start, end))
                pending = None
            elif j < len(tokens) and tokens[j] in CONJUNCTIONS:
                pending = (value, positions[i], j + 1)
            else:
                pending = None
            i = unit_end if unit is not None else j
    return found


_FRACTION_DENOMINATORS = {
    "half": 2, "halves": 2, "quarter": 4, "quarters": 4, "eighth": 8, "eighths": 8,
    "sixteenth": 16, "sixteenths": 16, "thirty second": 32, "thirty seconds": 32,
    "thirty-second": 32, "thirty-seconds": 32,
}
SPOKEN_FRACTION = re.compile(
    r"\b(?:(?P<whole>[a-z]+)\s+and\s+)?(?:(?P<num>a|an|one|two|three|five|seven|nine|eleven|thirteen|fifteen)\s+)?"
    r"(?P<den>thirty[\s-]seconds?|sixteenths?|eighths?|quarters?|halves|half)"
    r"(?:\s+(?:of\s+)?an?)?\s+(?P<unit>inch(?:es)?)\b",
    re.IGNORECASE,
)


def _spoken_fractions(text: str) -> list[Measurement]:
    """'one quarter inch', 'three eighths inch', 'one and a half inches'.

    The KBs write aggregate sizes and clearances as 1/4", 3/8", 1/16"; the agent
    says them. VERIFIED 2026-09-28 (FHRC28-FAQ-041): a perfect spoken answer
    read as containing only "one inch", because fractions were not parsed."""
    found = []
    for m in SPOKEN_FRACTION.finditer(text):
        den = _FRACTION_DENOMINATORS[m.group("den").lower().replace("-", " ")]
        num_word = (m.group("num") or "one").lower()
        num = 1 if num_word in ("a", "an") else ONES.get(num_word)
        if num is None:
            continue
        value = num / den
        whole_word = (m.group("whole") or "").lower()
        if whole_word:
            whole = ONES.get(whole_word)
            if whole is None:
                continue
            value += whole
        found.append(Measurement(round(value, 6), "inch", m.group(0), m.start(), m.end()))
    return found


def extract(text: str) -> list[Measurement]:
    """Every measurement in `text`, written or spoken, in document order.

    Overlaps are resolved in favour of the digit reading, which is the more
    specific of the two - `12 VDC` must not also be read as a spoken "twelve".
    """
    digits = _digit_measurements(text) + _spoken_fractions(text)
    taken = [(m.start, m.end) for m in digits]
    out = list(digits)
    for spoken in _spoken_measurements(text):
        if any(spoken.start < end and start < spoken.end for start, end in taken):
            continue
        out.append(spoken)
    return sorted(out, key=lambda m: m.start)


# ---------------------------------------------------------------------------
# Part numbers and pin references
# ---------------------------------------------------------------------------

# Deliberately the same shapes tools/build_resources.py already treats as
# anchor-worthy. A part number is a fact the manual commits to exactly as much
# as a pressure is.
PART_PATTERNS = (
    re.compile(r"\b[A-Z]{1,2}\d-PIN\s*\d+\b", re.IGNORECASE),
    re.compile(r"\b\d{6,7}\b"),
    re.compile(r"\bM-\d{3}(?:-\d{2}[A-Z]?)?\b", re.IGNORECASE),
)


def part_references(text: str) -> list[str]:
    """Part numbers and pin references, normalised for comparison."""
    out: list[str] = []
    for pattern in PART_PATTERNS:
        for match in pattern.finditer(text):
            token = re.sub(r"\s+", " ", match.group(0).strip().upper())
            if token not in out:
                out.append(token)
    return out
