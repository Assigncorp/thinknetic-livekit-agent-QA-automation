"""
The same KB question, the way real callers actually type it.

`rewrite(variant, question)` is a pure, deterministic function: the same
question and variant always give the same text, so a failing call can be
repeated word for word. The variants are listed in livekitSdk.phrasing.variants;
tests/test_phrasing.py asks each one on a live call and requires the KB value.
"""

from __future__ import annotations

import re

# Words that carry no topic. What is left of a question once they are gone is
# how a hurried caller types it: "main relief pressure steering".
_FILLER = {
    "what", "which", "how", "is", "are", "the", "should", "be", "set", "to", "at", "run",
    "for", "of", "does", "do", "a", "an", "on", "my", "this", "machine", "i",
}

# No digits or number words: the caller's text must never put a figure in the call.
_PREAMBLE = (
    "I'm out on a job site with the crew, we've had the machine running since early this "
    "morning and it has been fine so far, but before we start the next stretch of road "
    "I want to double check a setting with you so nobody is guessing. "
)


def keywords(question: str) -> str:
    words = re.findall(r"[A-Za-z0-9/'-]+", question)
    kept = [w for w in words if w.lower() not in _FILLER]
    return " ".join(kept) or question.rstrip("?")


def _typo(word: str) -> str:
    """Swap the two middle letters: 'pressure' -> 'presusre'."""
    i = len(word) // 2 - 1
    return word[:i] + word[i + 1] + word[i] + word[i + 2 :]


def typos(question: str) -> str:
    """Two typos, in the two longest words (5+ letters) - the words a question hangs on."""
    words = question.split(" ")
    longest = sorted(
        (i for i, w in enumerate(words) if len(re.sub(r"\W", "", w)) >= 5),
        key=lambda i: -len(words[i]),
    )[:2]
    for i in longest:
        core = re.match(r"^(\w+)(\W*)$", words[i])
        if core and core.group(1)[len(core.group(1)) // 2 - 1] != core.group(1)[len(core.group(1)) // 2]:
            words[i] = _typo(core.group(1)) + core.group(2)
    return " ".join(words)


def rewrite(variant: str, question: str) -> str:
    q = question.strip()
    lower = q[0].lower() + q[1:]
    kw = keywords(q)
    table = {
        "lowercase": q.lower().rstrip("?"),
        "allCaps": q.upper(),
        "typos": typos(q),
        "politeFiller": f"Hi Jason, hope your day is going well! Quick question for you - {lower} Thanks a lot, really appreciate it.",
        "keywordsOnly": f"{kw}?",
        "statement": f"I need to know {lower.rstrip('?')} on this machine.",
        "spokenDisfluency": f"um, so... uh, {q.lower().rstrip('?')}, I mean the, the {kw}?",
        "longPreamble": _PREAMBLE + q,
    }
    if variant not in table:
        raise KeyError(f"unknown phrasing variant {variant!r}; one of {sorted(table)}")
    return table[variant]
