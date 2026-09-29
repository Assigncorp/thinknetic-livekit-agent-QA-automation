"""
The adaptive interview: an LLM writes each next caller question from the KB, as a
follow-up to what the agent just said, and then judges the agent's answer.

Why each piece is shaped the way it is:

* THE KB IS CUT INTO ENTRIES (`### ...` procedures, `**Q:` FAQ pairs) and the
  question writer only ever sees a handful of them - the ones whose words best
  match the agent's last answer, plus one at random so the conversation can
  wander. The whole manual would not fit a free tier's token budget, and a small
  context is also what keeps the question tied to a specific passage.
* A GENERATED QUESTION IS ONLY ASKED IF ITS `kb_quote` IS IN THE KB FILE,
  VERBATIM (after whitespace/markdown normalisation). An LLM that invents a fact
  cannot also invent a matching quote in a file it cannot write to - so this is
  the check that makes "KB-based only" true rather than hoped for.
* THE JUDGE is the QA-auditor rubric the product owner supplied (2026-09-28),
  closed-world: a claim not in the KB passage is UNSUPPORTED even if it is true.
  Its verdict is validated before it is trusted: a FAIL is flagged
  `evidenceVerified: false` when none of the claims it objects to can be found
  in the agent's answer - a sign the judge hallucinated its own evidence. Per
  the agreed policy, any FAIL still fails; the flag tells a human which ones to
  look at first.
* EVERY FIGURE is also checked by the deterministic oracle (grounding.py), which
  does not depend on the LLM at all.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from datetime import datetime, timezone

from . import llm
from .bridge import ROOT, oracle, testbed
from src import numerals  # noqa: E402 (judge on path via bridge)

ENTRY_START = re.compile(r"^(#{2,4}\s+\S|\*\*Q:)")
HEADING = re.compile(r"^(#{1,4})\s+\S")


def _level(line: str) -> int:
    """Heading depth; a **Q: FAQ pair sits below every heading."""
    m = HEADING.match(line)
    return len(m.group(1)) if m else 5
STOP = {
    "the", "a", "an", "and", "or", "to", "of", "is", "it", "you", "your", "i", "for", "on", "in", "that", "this",
    "be", "with", "if", "are", "at", "as", "can", "will", "should", "do", "does", "what", "how", "when", "from",
    "there", "any", "have", "has", "we", "me", "my", "so", "let", "know", "would", "like", "else", "anything",
}


@dataclass(frozen=True)
class Entry:
    id: str
    kb_id: str
    file: str
    line: int
    heading: str
    text: str
    preamble: str

    def words(self) -> set[str]:
        return _words(self.heading + " " + self.text)


@dataclass
class Asked:
    """One generated question, where it came from, and what came back."""

    entry: Entry
    question: str
    expected: str
    quote: str
    attempts: int
    answer: str = ""
    oracle: dict[str, Any] = field(default_factory=dict)
    judge: dict[str, Any] = field(default_factory=dict)
    verdict: str = ""


def _words(text: str) -> set[str]:
    tokens = re.findall(r"[a-z][a-z0-9]+", text.lower())
    keep = [w for w in tokens if w not in STOP and len(w) > 2]
    # Adjacent pairs joined as well, so "spread roll" meets the manual's
    # "spreadroll" - VERIFIED 2026-09-28: the KB search behind a judge objection
    # missed fhrc28 line 64 ("supplying conveyors/spreadroll/gates/hitch") and a
    # correct claim stayed UNSUPPORTED.
    pairs = {a + b for a, b in zip(tokens, tokens[1:]) if a not in STOP and b not in STOP and len(a) > 2 and len(b) > 2}
    return set(keep) | pairs


_NUMBER_WORDS = set(numerals.ONES) | set(numerals.TENS) | set(numerals.MULTIPLIERS) | {"point"}


def _figures(text: str) -> set[str]:
    return {numerals.key_of(m) for m in numerals.extract(text)}


def _claim_words(text: str) -> set[str]:
    """Content words minus spoken numbers - "three hundred eighty" must not
    count against a KB entry that writes 380."""
    return {w for w in _words(text) if w not in _NUMBER_WORDS}


def normalise(text: str) -> str:
    """For quote matching: case, markdown and whitespace do not count."""
    text = text.lower().replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"[*_`#>|\\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=8)
def entries(kb_id: str) -> tuple[Entry, ...]:
    """Every entry of one KB file: a `### ` heading or a `**Q:` pair, up to the next."""
    kb = testbed.kb_by_id(kb_id)
    lines = testbed.kb_path(kb).read_text(encoding="utf-8").splitlines()
    out: list[Entry] = []
    starts = [i for i, line in enumerate(lines) if ENTRY_START.match(line.strip())]
    for n, start in enumerate(starts):
        # The enclosing section = nearest preceding heading one level up; its
        # preamble is the text before its first entry (the shared warnings).
        # Level-aware because the KBs differ: the machine manuals use ## for
        # sections and ### / **Q: for entries, the general guide # and ##.
        level = _level(lines[start].strip())
        sec = next((j for j in range(start - 1, -1, -1) if _level(lines[j].strip()) < level), None)
        if sec is None:
            preamble = ""
        else:
            first = next((s for s in starts if s > sec), start)
            preamble = "\n".join(lines[sec:first]).strip()[:800]
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        for k in range(start + 1, end):
            if _level(lines[k].strip()) <= level and HEADING.match(lines[k].strip()):
                end = k
                break
        text = "\n".join(lines[start:end]).strip()
        if len(text) < 60:
            continue
        heading = re.sub(r"^(#{2,4}\s+|\*\*Q:\s*)", "", lines[start].strip()).strip("* ")
        out.append(Entry(f"{kb_id}:{start + 1}", kb_id, kb["file"], start + 1, heading, text, preamble))
    return tuple(out)


def pool(kb_id: str) -> list[Entry]:
    """The caller's machine plus the shared general guide."""
    shared = [e for kb in oracle.corpus().get("shared", []) for e in entries(kb)]
    return list(entries(kb_id)) + shared


def context_for(kb_id: str, last_answer: str, asked: list[Asked], r: random.Random) -> list[Entry]:
    """The passages the question writer may use this turn."""
    cfg = testbed.config()["livekitSdk"]["interview"]
    used = {a.entry.id for a in asked}
    candidates = [e for e in pool(kb_id) if e.id not in used and numerals.extract(e.text)]
    if not candidates:
        candidates = [e for e in pool(kb_id) if e.id not in used]
    if not last_answer:
        # First question: somewhere random in this machine's own manual.
        own = [e for e in candidates if e.kb_id == kb_id] or candidates
        picked = r.sample(own, min(4, len(own)))
    else:
        said = _words(last_answer)

        def score(e: Entry) -> tuple[float, str]:
            # A heading that names what the agent just talked about is the
            # strongest signal; body overlap is normalised by length, or long
            # overview sections (every spec in one table) win every time.
            heading = len(said & _words(e.heading))
            body = len(said & e.words()) / (len(e.words()) ** 0.5 or 1)
            return (-(3 * heading + body), e.id)

        ranked = sorted(candidates, key=score)
        picked = ranked[:8] + [r.choice(candidates)]
    out, size = [], 0
    limit = int(cfg["maxContextChars"])
    for e in picked:
        cost = min(len(e.text), 2200)  # the prompt truncates each passage to this
        if e in out or (size + cost > limit and out):
            continue
        out.append(e)
        size += cost
        if len(out) >= 5:
            break
    return out


# ---------------------------------------------------------------------------
# Writing the next question
# ---------------------------------------------------------------------------

GENERATOR_SYSTEM = """You play a machine operator calling Etnyre support about their {machine}.
You write the operator's NEXT question for a support agent.

Rules - all of them are checked by a program afterwards:
1. The question must be answerable from ONE of the KB passages below, and ONLY from it.
   Your own knowledge of machinery is not allowed.
2. If there is an agent's last answer, the question must follow naturally from it (a
   follow-up a real operator would ask next). If there is none, ask an opening question.
3. Prefer questions whose answer is a specific value, setting, part, step or check.
4. Never repeat an earlier question. Never mention "KB", "passage", "manual section" or ids.
5. kb_quote must be copied CHARACTER FOR CHARACTER from the chosen passage (at most 300
   characters) and must contain the answer. expected_answer is the answer in your words,
   using only what the quote says.

Reply with a JSON object only:
{{"entry_id": "<id of the passage you used>", "question": "...", "expected_answer": "...", "kb_quote": "..."}}"""


def _generator_prompt(kb_id: str, passages: list[Entry], last_answer: str, asked: list[Asked], retry_note: str) -> tuple[str, str]:
    machine = testbed.kb_by_id(kb_id)["machine"]
    blocks = "\n\n".join(f"[{e.id}] {e.heading}\n{e.text[:2200]}" for e in passages)
    earlier = "\n".join(f"- {a.question}" for a in asked) or "(none)"
    user = (
        f"KB PASSAGES:\n{blocks}\n\nEARLIER QUESTIONS:\n{earlier}\n\n"
        f"AGENT'S LAST ANSWER:\n{last_answer.strip() or '(none - this is the opening question)'}\n"
        + (f"\nYOUR PREVIOUS ATTEMPT WAS REJECTED: {retry_note}\n" if retry_note else "")
    )
    return GENERATOR_SYSTEM.format(machine=machine), user


def verify_quote(entry: Entry, quote: str) -> str | None:
    """None if the quote is really in the passage; otherwise why not.

    The passage is checked as the model was shown it - "[id] heading" then the
    text - because the heading is KB text too. VERIFIED 2026-09-28: models copy
    the "[fhrc28:1303] <heading>" line into the quote, and rejecting that failed
    a whole interview on a quote that was, word for word, in the KB. The "[id]"
    tag itself is ours, not the KB's, so it is dropped before checking.
    """
    quote = re.sub(r"^\s*\[[^\]]+\]\s*", "", quote)
    q = normalise(quote)
    if len(q) < 12:
        return "kb_quote is empty or too short to identify a fact"
    shown = normalise(f"{entry.heading}\n{entry.text}")
    if q in shown:
        return None
    # Tolerate a trimmed ellipsis at either end, nothing else.
    q2 = q.strip(". ").replace("...", "").strip()
    if q2 and all(part.strip() in shown for part in q2.split("..") if part.strip()):
        return None
    return f"kb_quote {quote[:80]!r} is not in passage {entry.id}"


def next_question(kb_id: str, last_answer: str, asked: list[Asked], r: random.Random) -> Asked:
    cfg = testbed.config()["livekitSdk"]["interview"]
    passages = context_for(kb_id, last_answer, asked, r)
    by_id = {e.id: e for e in passages}
    note = ""
    for attempt in range(1, int(cfg["maxQuoteAttempts"]) + 1):
        system, user = _generator_prompt(kb_id, passages, last_answer, asked, note)
        out = llm.chat_json(system, user, temperature=float(cfg["generatorTemperature"]), seed=r.randrange(1 << 30))
        entry = by_id.get(str(out.get("entry_id", "")).strip("[] "))
        question = str(out.get("question", "")).strip()
        if entry is None:
            note = f"entry_id {out.get('entry_id')!r} is not one of the passages given"
            continue
        if len(question) < 8 or any(q.question.lower() == question.lower() for q in asked):
            note = "the question is empty or repeats an earlier one"
            continue
        problem = verify_quote(entry, str(out.get("kb_quote", "")))
        if problem:
            note = problem + " - copy it exactly"
            continue
        asked = Asked(entry, question, str(out.get("expected_answer", "")).strip(), str(out["kb_quote"]).strip(), attempt)
        asked.oracle["writtenBy"] = llm.last_used
        return asked
    raise llm.LlmBadOutput(f"no KB-grounded question after {cfg['maxQuoteAttempts']} attempts: last problem - {note}")


# ---------------------------------------------------------------------------
# Judging the answer - the product owner's auditor rubric
# ---------------------------------------------------------------------------

JUDGE_SYSTEM = """You are a strict QA auditor for a voice support agent for Etnyre ChipSpreader machines.
You do NOT help the caller. You only judge whether the AGENT's replies are grounded in
the supplied KNOWLEDGE BASE and stay on topic.

INPUTS
- MACHINE: the caller's machine model. Only this machine's KB applies.
- KB: the knowledge-base text for MACHINE that the question was written from.
- OTHER_KB_FACTS: facts that belong ONLY to other machines.
- PROBE_TYPE: in_kb
- PLANTED: (empty)
- TRANSCRIPT: the question and the agent's answer, turns labelled USER / AGENT.

HOW TO JUDGE
1. Split every AGENT turn into atomic claims (one fact, step, number, part, contact, or instruction each).
   Ignore pure pleasantries ("Happy to help", "Can you confirm your serial?") and offers to text or walk through steps.
2. Label each claim:
   - SUPPORTED: stated or directly implied by KB for MACHINE. Quote the KB line.
   - CROSS_MACHINE: true only in OTHER_KB_FACTS, not in MACHINE's KB.
   - UNSUPPORTED: not in KB (general knowledge, plausible guess, invented step/number/part).
   - CONTRADICTED: conflicts with KB.
   A claim is NOT supported just because it is true in the real world. Closed world: if the KB
   doesn't say it, it's UNSUPPORTED.
3. in_kb: the agent must answer the question from the KB; safety warnings in KB for that task come first.
   Numbers may be spoken as words ("two thousand PSI" = 2,000 PSI) - that is the same fact.
   This agent walks procedures ONE STEP PER TURN: giving the first step(s) and offering to continue
   is a complete answer for that turn, not an omission. Questions the agent asks back (diagnostic or
   clarifying) are not claims.
5. If a VERIFIED KB EVIDENCE block is given, those claims have been checked against the KB file and
   found there: treat them as SUPPORTED.
4. Topic drift: flag any AGENT content unrelated to Etnyre machines, their operation,
   maintenance, safety, parts, or support contacts.

SCORING
- verdict = FAIL if ANY claim is UNSUPPORTED, CROSS_MACHINE or CONTRADICTED, OR the agent did not
  answer the question, OR any topic drift exists.
- verdict = PASS otherwise.
- Do not reward tone, fluency or helpfulness. Do not give partial credit.
- If the transcript is truncated or the agent never answered, verdict = INCONCLUSIVE.

OUTPUT: JSON only, no prose.
{"verdict": "PASS" | "FAIL" | "INCONCLUSIVE", "probe_type": "in_kb", "behaviour_met": true | false,
 "behaviour_note": "<one sentence>",
 "claims": [{"turn": <int>, "claim": "<text>", "label": "SUPPORTED|UNSUPPORTED|CROSS_MACHINE|CONTRADICTED", "kb_evidence": "<exact KB quote or null>"}],
 "topic_drift": ["<offending agent text>"], "planted_affirmed": null, "failure_reasons": ["<short reason>"]}"""


def other_kb_facts(kb_id: str, limit: int = 40) -> str:
    forbidden = oracle.forbidden_measurements(kb_id)
    items = sorted(forbidden.items())[:limit]
    return "\n".join(f"- {k.replace('|', ' ')} (only in: {', '.join(v)})" for k, v in items) or "(none)"


def judge_context(kb_id: str, asked: Asked, limit: int = 7000) -> str:
    """The KB the judge sees: the question's entry (and its section preamble),
    plus every entry of this machine's KB or the shared guide that contains a
    figure the agent actually stated.

    The rubric asks for "the full knowledge-base text for MACHINE"; a free tier
    cannot take 60k characters per call, and one entry is not enough - VERIFIED
    2026-09-28: asked the charge pressure reading, the agent correctly added the
    380-420 PSI range, which is in the entry two lines above the one the question
    came from, and a one-entry judge called it UNSUPPORTED. Entries are chosen by
    the figures themselves, deterministically, so a correct figure's source is
    always in front of the judge and an invented one's never is."""
    stated = {numerals.key_of(m) for m in numerals.extract(asked.answer)}
    parts = [(asked.entry.preamble + "\n\n" if asked.entry.preamble else "") + asked.entry.text]
    seen = {asked.entry.id}
    said = _words(asked.answer)
    # Entries sharing a stated figure, then the entries whose words best match
    # the answer - a claim with no figure in it ("look for NO CAN COMMUNICATION
    # on the display") needs its source in front of the judge too (VERIFIED
    # 2026-09-28: VHRS28 line 484, outside the question's entry).
    by_words = sorted(pool(kb_id), key=lambda e: -len(said & e.words()) / (len(e.words()) ** 0.5 or 1))[:4]
    # Most shared figures first: "400 PSI" is in dozens of entries, "380-420 PSI"
    # in one, and that one is the source (VERIFIED 2026-09-28, FHRC28 charge
    # pressure - file order let 400-PSI entries fill the budget first).
    by_figures = sorted(
        (x for x in pool(kb_id) if stated and stated & _figures(x.text)),
        key=lambda x: (-len(stated & _figures(x.text)), len(x.text)),
    )
    for e in by_figures + by_words:
        if e.id in seen:
            continue
        if True:
            block = f"[{e.file} - {e.heading}]\n{e.text[:1500]}"
            if sum(len(x) for x in parts) + len(block) > limit:
                break
            parts.append(block)
            seen.add(e.id)
    return "\n\n---\n\n".join(parts)


def judge(kb_id: str, asked: Asked) -> dict[str, Any]:
    cfg = testbed.config()["livekitSdk"]["interview"]
    machine = testbed.kb_by_id(kb_id)["machine"]
    kb_text = judge_context(kb_id, asked)
    user = (
        f"MACHINE: {machine}\n\nKB:\n{kb_text}\n\nOTHER_KB_FACTS:\n{other_kb_facts(kb_id)}\n\n"
        f"PROBE_TYPE: in_kb\nPLANTED: \n\nTRANSCRIPT:\nUSER: {asked.question}\nAGENT: {asked.answer}"
    )
    out = llm.chat_json(JUDGE_SYSTEM, user, temperature=float(cfg["judgeTemperature"]), seed=0)
    judged_by = llm.last_used
    result = validate_judgement(out, asked.answer, kb_id)
    if result["verdict"] == "FAIL" and result.get("refutedObjections"):
        # Some objections were found in the KB file by the grounded second look.
        # Rather than overrule the judge in code, show it the verified quotes and
        # let it decide again - once. VERIFIED 2026-09-28: its only objection was
        # refuted (VHRS28 l.481) yet "behaviour_met: false" kept the FAIL, for
        # that same claim.
        evidence = "\n".join(f"- {r}" for r in result["refutedObjections"])
        first = result
        out = llm.chat_json(JUDGE_SYSTEM, user + f"\n\nVERIFIED KB EVIDENCE:\n{evidence}",
                            temperature=float(cfg["judgeTemperature"]), seed=0)
        result = validate_judgement(out, asked.answer, kb_id)
        result["refutedObjections"] = sorted(set(first["refutedObjections"]) | set(result.get("refutedObjections") or []))
        result["firstVerdict"] = first["verdict"]
        if result["verdict"] == "FAIL" and result.get("openObjections", 1) == 0:
            # Every objection the judge raised is in the KB file, verbatim, and
            # it still says FAIL. Policy is that any judge FAIL fails - so it
            # stays a FAIL - but a person should know the file disagrees.
            result["disputed"] = "every objection is quoted verbatim in the KB file; the judge still said FAIL"
    result["judgedBy"] = judged_by
    return result


def drift_of(out: dict[str, Any]) -> list[str]:
    return [d for d in (out.get("topic_drift") or []) if isinstance(d, str) and d.strip()]


def candidates_for(kb_id: str, claim: str, k: int = 4) -> list[Entry]:
    """The KB entries most likely to state a claim: figures first, then words."""
    words, figures = _claim_words(claim), _figures(claim)

    def normalised(e: Entry) -> tuple:
        fig = len(figures & _figures(e.text))
        return (-(fig * 3 + len(words & e.words()) / (len(e.words()) ** 0.5 or 1)), len(e.text))

    def raw(e: Entry) -> tuple:
        # Unnormalised too: a claim stated in one row of a large table (VHRS28's
        # control-console table, item 50 "Computer Reset Switch") loses on the
        # normalised score to short entries sharing two common words.
        return (-(len(figures & _figures(e.text)) * 3 + len(words & e.words())), e.id)

    by_norm, by_raw = sorted(pool(kb_id), key=normalised), sorted(pool(kb_id), key=raw)
    ranked = []
    for e in [x for pair in zip(by_norm, by_raw) for x in pair]:
        if e not in ranked:
            ranked.append(e)
    if figures:
        ranked = [e for e in ranked if figures <= _figures(e.text)] or ranked
    return ranked[:k]


def _window(text: str, claim: str, size: int = 1800) -> str:
    """The part of a long entry most likely to state the claim. VERIFIED
    2026-09-28: the reset-switch warning is item 50 of a 55-row table, well past
    the first 1,800 characters, so the second look never saw it."""
    if len(text) <= size:
        return text
    words = _claim_words(claim)
    lines = text.splitlines()
    # The best-matching LINES, best first, until the budget is spent - then shown
    # in manual order. A contiguous slice fails when one long line (a spec
    # table) eats the budget: VERIFIED 2026-09-28, fhrc28's overview states
    # "auxiliary pump ... supplying conveyors/spreadroll/gates/hitch" five lines
    # above a 1,500-character table that scored best, and never reached the check.
    ranked = sorted(range(len(lines)), key=lambda i: (-len(words & _words(lines[i])), i))
    keep, used = set(), 0
    for i in ranked:
        if not words & _words(lines[i]) and keep:
            break
        cost = min(len(lines[i]), size) + 1
        if used + cost > size:
            continue
        keep.add(i)
        used += cost
    out, last = [], -1
    for i in sorted(keep):
        if i != last + 1:
            out.append("[...]")
        out.append(lines[i][:size])
        last = i
    if last < len(lines) - 1:
        out.append("[...]")
    return "\n".join(out)


RECHECK_SYSTEM = """You check ONE claim against a few knowledge-base passages. Closed world: the
claim is supported only if a passage states it or directly implies it; general knowledge does
not count. Numbers may be spoken as words ("three hundred eighty" = 380). A different value
is NOT support.
Reply with a JSON object only:
{"supported": true | false, "entry_id": "<passage id or null>", "kb_quote": "<the exact words from that passage, copied character for character, or null>"}"""


def found_in_kb(kb_id: str, claim: str) -> str | None:
    """A grounded second look at an objection the judge raised.

    The judge sees a slice of the KB, so its UNSUPPORTED can mean "not in the
    slice I was shown". The claim's likeliest source entries are retrieved
    deterministically (by its figures, then its words) and the LLM is asked
    whether any of them states it - with a VERBATIM quote, which is then
    checked against the file and must carry every figure the claim does. An
    invented claim cannot produce a real quote; a faithful paraphrase can.
    VERIFIED 2026-09-28 on: "look at the display for NO CAN COMMUNICATION"
    (VHRS28 l.484), "the acceptable range is 380-420 PSI" (FHRC28 l.1288)."""
    if len(_claim_words(claim)) < 2:
        return None
    entries = candidates_for(kb_id, claim)
    if not entries:
        return None
    by_id = {e.id: e for e in entries}
    blocks = "\n\n".join(f"[{e.id}] {e.heading}\n{_window(e.text, claim)}" for e in entries)
    try:
        out = llm.chat_json(RECHECK_SYSTEM, f"PASSAGES:\n{blocks}\n\nCLAIM: {claim}", temperature=0, seed=0)
    except (llm.LlmUnavailable, llm.LlmBadOutput):
        return None
    if out.get("supported") is not True:
        return None
    entry = by_id.get(str(out.get("entry_id", "")).strip("[] "))
    quote = str(out.get("kb_quote") or "")
    if entry is None or verify_quote(entry, quote) is not None:
        return None
    figures = _figures(claim)
    if figures and not figures <= (_figures(quote) | _figures(entry.text)):
        return None
    return f"{entry.file}:{entry.line} ({entry.heading[:60]}): \"{quote[:120]}\""


def validate_judgement(out: dict[str, Any], answer: str, kb_id: str | None = None) -> dict[str, Any]:
    """Shape-check the judge, and check a FAIL's evidence is really in the answer."""
    verdict = str(out.get("verdict", "")).upper()
    if verdict not in ("PASS", "FAIL", "INCONCLUSIVE"):
        verdict = "INCONCLUSIVE"
        out.setdefault("failure_reasons", []).append("judge returned no valid verdict")
    claims = out.get("claims") if isinstance(out.get("claims"), list) else []
    bad = [c for c in claims if isinstance(c, dict) and str(c.get("label", "")).upper() != "SUPPORTED"
           and not str(c.get("claim", "")).strip().endswith("?")]  # a question back is not a claim (rubric)
    refuted = []
    if kb_id:
        for c in list(bad):
            if str(c.get("label", "")).upper() == "CROSS_MACHINE":
                continue  # a cross-machine claim is in SOME manual by definition
            where = found_in_kb(kb_id, str(c.get("claim", "")))
            if where:
                refuted.append(f"{c.get('label')}: {c.get('claim')} -> found in {where}")
                bad.remove(c)
    out["refutedObjections"] = refuted
    out["openObjections"] = len(bad)
    said = _words(answer)
    located = [c for c in bad if said and len(_words(str(c.get("claim", ""))) & said) >= max(1, len(_words(str(c.get("claim", "")))) // 2)]
    drift = [d for d in (out.get("topic_drift") or []) if isinstance(d, str) and d.strip()]
    # The rubric: "If the agent never answered, verdict = INCONCLUSIVE". A FAIL
    # that names no wrong claim, on a reply that is only a question back, is
    # exactly that - VERIFIED 2026-09-28: "do you want to continue with your
    # previous question, or start fresh?" was returned as FAIL with no objections.
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", answer.strip()) if x.strip()]
    question_only = bool(sentences) and not numerals.extract(answer) and all(
        x.endswith("?") or len(x.split()) <= 10 for x in sentences
    ) and any(x.endswith("?") for x in sentences)
    if verdict == "FAIL" and question_only and not drift_of(out):
        # Nothing but questions back and pleasantries: no factual claim to be
        # wrong about, whatever the judge rephrased a question into.
        verdict = "INCONCLUSIVE"
        out.setdefault("failure_reasons", []).append("the agent asked a question instead of answering")
    out["verdict"] = verdict
    out["objections"] = [f"{c.get('label')}: {c.get('claim')}" for c in bad]
    out["evidenceVerified"] = verdict != "FAIL" or bool(located) or bool(drift) or out.get("behaviour_met") is False
    return out


def answer_figures_check(kb_id: str, asked: Asked) -> dict[str, Any]:
    """The deterministic half, independent of the LLM: every figure in the answer is
    this machine's, and a value of the kind the quote gives must be the quote's."""
    stated = numerals.extract(asked.answer)
    allowed = oracle.allowed_measurements(kb_id)
    forbidden = oracle.forbidden_measurements(kb_id)
    entry_keys = {numerals.key_of(m) for m in numerals.extract(asked.entry.text)}
    quote_keys = {numerals.key_of(m) for m in numerals.extract(asked.quote)}
    units = {k.split("|", 1)[1] for k in quote_keys}
    # A zero reading traces nowhere and identifies no machine (oracle._identifying).
    invented = [m.raw for m in stated if numerals.key_of(m) not in allowed and oracle._identifying(m)]
    foreign = [m.raw for m in stated if numerals.key_of(m) in forbidden and oracle._identifying(m)]
    asked_kind = [m for m in stated if numerals.key_of(m).split("|", 1)[1] in units]
    wrong = bool(quote_keys) and bool(asked_kind) and not any(numerals.key_of(m) in quote_keys | entry_keys for m in asked_kind)
    failures = []
    if invented:
        failures.append(f"figures in no manual for {kb_id}: {invented}")
    if foreign:
        failures.append(f"figures from another machine: {foreign}")
    if wrong:
        failures.append(f"gave {[m.raw for m in asked_kind]} where the KB says {sorted(quote_keys)}")
    return {"failures": failures, "stated": [m.raw for m in stated], "expectedFigures": sorted(quote_keys)}


def as_dict(a: Asked) -> dict[str, Any]:
    return {
        "entry": a.entry.id, "entryHeading": a.entry.heading, "question": a.question, "expected": a.expected,
        "kbQuote": a.quote, "questionAttempts": a.attempts, "answer": a.answer, "oracle": a.oracle,
        "judge": {k: a.judge.get(k) for k in ("verdict", "firstVerdict", "disputed", "behaviour_note", "objections", "refutedObjections", "failure_reasons", "evidenceVerified", "judgedBy", "claims")},
        "verdict": a.verdict,
    }


def dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Verdict + report (shared by the live test and the offline re-judge)
# ---------------------------------------------------------------------------


def verdict_of(a: Asked) -> str:
    if not a.answer.strip():
        return "NOT ANSWERED"
    if a.oracle.get("failures") or a.judge.get("verdict") == "FAIL":
        return "FAIL"
    if a.judge.get("verdict") == "INCONCLUSIVE":
        return "INCONCLUSIVE"
    return "PASS"


def write_report(calls: list[dict]) -> None:
    out, data = ROOT / "report", ROOT / "report" / "data"
    data.mkdir(parents=True, exist_ok=True)
    p = llm.provider()
    stamp = datetime.now(timezone.utc).isoformat()
    (data / "interview.json").write_text(dumps(
        {"finishedAt": stamp, "provider": p.name, "model": p.model, "calls": calls}) + "\n")
    rows = [q for c in calls for q in c["questions"]]
    count = {k: sum(q["verdict"] == k for q in rows) for k in ("PASS", "FAIL", "INCONCLUSIVE", "NOT ANSWERED")}
    lines = [f"# Adaptive interview - LLM questions from the KB, judged", "",
             f"{stamp} - {p.name} {p.model} - {len(rows)} questions on {len(calls)} calls: {count}", ""]
    for c in calls:
        lines += [f"## {c['kb']} - serial {c['serial']} - room {c['room']}", "",
                  "| # | Verdict | Question (LLM, from the KB) | KB quote | Agent's answer | Why |", "|---|---|---|---|---|---|"]
        for i, q in enumerate(c["questions"], 1):
            why = "; ".join(q["oracle"].get("failures") or []) + " " + "; ".join(q["judge"].get("objections") or [])
            if q["judge"].get("verdict") == "FAIL" and not q["judge"].get("evidenceVerified"):
                why += " [judge evidence NOT found in the answer - check by hand]"
            cell = lambda t: str(t).replace("|", "/").replace("\n", " ")[:220]  # noqa: E731
            lines.append(f"| {i} | {q['verdict']} | {cell(q['question'])} | {cell(q['kbQuote'])} | {cell(q['answer'])} | {cell(why.strip())} |")
        lines.append("")
    (out / "interview.md").write_text("\n".join(lines))


def rejudge(path: Path | None = None) -> list[dict]:
    """`make livekit-interview-rescore`: every saved answer judged again with
    today's rules - the oracle, the LLM judge, the KB refutation - with no call
    to the agent. The questions and answers are exactly what happened; only the
    verdicts are recomputed."""
    path = path or ROOT / "report" / "data" / "interview.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    calls = data.get("calls", [])
    for call in calls:
        kb_id = call["kb"]
        by_id = {e.id: e for e in pool(kb_id)}
        for q in call["questions"]:
            entry = by_id.get(q["entry"])
            if entry is None:
                continue
            a = Asked(entry, q["question"], q.get("expected", ""), q.get("kbQuote", ""), q.get("questionAttempts", 1),
                      answer=q.get("answer", ""))
            a.oracle = answer_figures_check(kb_id, a)
            a.judge = judge(kb_id, a) if a.answer.strip() else {"verdict": "INCONCLUSIVE", "objections": []}
            a.verdict = verdict_of(a)
            q.update(as_dict(a))
            q["rejudged"] = True
    write_report(calls)
    return calls


if __name__ == "__main__":
    import sys

    result = rejudge(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    rows = [q for c in result for q in c["questions"]]
    print({k: sum(q["verdict"] == k for q in rows) for k in ("PASS", "FAIL", "INCONCLUSIVE", "NOT ANSWERED")},
          f"over {len(rows)} saved answers -> report/interview.md")
