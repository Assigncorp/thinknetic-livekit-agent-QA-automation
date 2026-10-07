"""
The KB-steps smoke call: one live call to the deployed agent, nine timed checkpoints.

    call_started  greeted  question_asked  answer_received  answer_valid
    thanks_sent   feedback_asked  feedback_answered  call_closed

The caller reads each FINISHED agent turn and replies to what it asked; nothing
is a fixed script. What the agent does, from its own prompt and phrase catalog
(thinknetic-livekit-agents, enterprises-product-support-assistant):

  * Opening: greets, looks the dispatch-metadata serial up by itself and says
    "…pulled up. What can I help you with today?" - or, after a call on the
    same serial within 7 days, recaps it and asks whether to carry on.
  * Procedures: ONE step per turn, waiting for the caller each time. It offers
    to text the steps instead. A hazard tied to a step is said before that step;
    procedure-wide ones as a preface. Numbers are written out as words.
  * "Let me check." is a filler while a slow KB search runs.
  * After the caller is all set: asks for a 1-10 rating, then says
    "Thank you so much for calling … Take care, and have a great one" and
    deletes the room straight away.
  * After 15 s of caller silence: "Are you still there?".

So the caller declines the text, asks for the complete procedure including
cautions, says "done, what's next?" after every step, and stops collecting as
soon as the validator has every KB step and caution - or the turn limit hits.
"""

from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .call import Call, agent_token, is_holding
from .expect import text_matches
from .validator import Validation, validate

AGENT_JOIN_TIMEOUT_S = 15
GREETING_TIMEOUT_S = 30
TURN_TIMEOUT_S = 75  # a KB search can take a while; the agent fills after 5 s
QUIET_S = 8  # after a statement that asks nothing, how long before the caller speaks
FEEDBACK_TIMEOUT_S = 60
CLOSE_TIMEOUT_S = 30
ANSWER_DEADLINE_S = 12 * 60

CHECKPOINTS = [
    ("call_started", "The call connected and the agent joined"),
    ("greeted", "The agent greeted the caller"),
    ("question_asked", "Our test caller asked the knowledge-base question"),
    ("answer_received", "The agent answered"),
    ("answer_valid", "The answer matched the knowledge base, step by step"),
    ("thanks_sent", "Our test caller said thank you"),
    ("feedback_asked", "The agent asked the caller to rate the call"),
    ("feedback_answered", "Our test caller gave a rating from 1 to 10"),
    ("call_closed", "The agent ended the call"),
]

# --- what the agent says --------------------------------------------------
READ_BACK = [r"read that back", r"is that right", r"is that correct", r"did i get that right"]
NOT_FOUND = [r"couldn'?t find a product", r"can'?t find a product", r"still can'?t find"]
MULTIPLE = [r"matches a few products", r"which one is yours"]
WANTS_SERIAL = [r"serial number", r"read it (out )?(to|for) me"]
RECAP = [r"carry on", r"pick (things )?up where", r"last time", r"continue (with|working on) that"]
READY = [r"what can i help you with", r"how can i help", r"help you with today", r"pulled up",
         r"what (do you need|would you like) help with", r"tell me what you'?d like help with"]
IDLE = [r"are you still there", r"still here whenever you'?re ready"]
TEXT_OFFER = [r"\btext (you|it|them|that|those)\b", r"send (you )?the (full )?(list of )?steps",
              r"send you the", r"full list of steps", r"steps for the troubleshooting",
              r"so you have them in front of you"]
PHONE_ASK = [r"best number to text", r"number (should|can) i text", r"what'?s the best number"]
TRANSFER = [r"connect you", r"someone in the office", r"transfer you", r"put you through"]
ANYTHING_ELSE = [r"anything else", r"something else i can help", r"any other question",
                 r"help (you )?with anything else"]
RESOLVED_ASK = [r"did (that|this) (fix|resolve|solve|sort|help)", r"(has|is) (that|it) (fixed|resolved|working)",
                r"resolved the issue", r"is it working now"]
NO_INFO = [r"don'?t have that information"]
FEEDBACK_ASK = [r"\b(1|one) to (10|ten)\b", r"scale of", r"on a scale", r"\brate (the|this|your|our)\b",
                r"how (was|would you rate) your experience", r"how your experience was", r"how did i do",
                r"out of (10|ten)"]
CLOSING = [r"thank you so much for calling", r"take care", r"have a great (one|day)", r"goodbye"]

# --- what the caller says -------------------------------------------------
REQUEST_FULL = ("Please walk me through the complete step-by-step procedure, "
                "including any cautions or warnings that go with it.")
DECLINE_TEXT = "No thanks, please don't text it. " + REQUEST_FULL
CLARIFY = "It's happening right now on the machine. " + REQUEST_FULL
NEXT_STEP = "Done. What's the next step?"
NOT_FIXED = "No, that didn't fix it yet. What's the next step?"
DECLINE_TRANSFER = "No thanks, I'd rather keep going here. What's the next step?"
ASK_REMAINING = ("Is that the complete procedure? Please give me any remaining steps, "
                 "and any cautions or warnings that go with them.")
THANKS = "That's everything I needed, thank you - I'm all set."
NOTHING_ELSE = "No, that's everything. Thanks."
STILL_HERE = "Yes, I'm still here."


@dataclass
class Checkpoint:
    name: str
    label: str
    passed: bool | None = None  # None = not reached
    at_ms: int | None = None
    took_ms: int | None = None
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "label": self.label, "passed": self.passed,
                "atMs": self.at_ms, "tookMs": self.took_ms, "detail": self.detail}


@dataclass
class Attempt:
    number: int
    room: str = ""
    room_sid: str = ""
    agent_identity: str = ""
    started_at: str = ""
    checkpoints: dict[str, Checkpoint] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    answer_turns: list[str] = field(default_factory=list)
    validation: Validation | None = None
    rating: int | None = None
    error: str = ""
    duration_ms: int = 0

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checkpoints.values())

    def as_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "room": self.room,
            "roomSid": self.room_sid,
            "agentIdentity": self.agent_identity,
            "startedAt": self.started_at,
            "answer": self.answer_turns,
            "passed": self.passed,
            "durationMs": self.duration_ms,
            "error": self.error,
            "rating": self.rating,
            "checkpoints": [c.as_dict() for c in self.checkpoints.values()],
            "events": self.events,
            "validation": self.validation.as_dict() if self.validation else None,
        }


class _Flow:
    def __init__(self, call: Call, attempt: Attempt) -> None:
        self.call = call
        self.attempt = attempt
        self._last_mark = 0
        for name, label in CHECKPOINTS:
            attempt.checkpoints[name] = Checkpoint(name, label)

    def mark(self, name: str, passed: bool, detail: str = "") -> None:
        cp = self.attempt.checkpoints[name]
        now = self.call.ms(self.call._now()) or 0
        cp.passed, cp.at_ms, cp.took_ms, cp.detail = passed, now, now - self._last_mark, detail
        self._last_mark = now
        print(f"[kb] {'PASS' if passed else 'FAIL'} {name} @{now / 1000:.1f}s {detail}")

    async def say(self, text: str, tag: str = "") -> None:
        await self.call.wait_listening(TURN_TIMEOUT_S)
        await self.call.say(text, tag)

    async def turn(self, timeout: float = TURN_TIMEOUT_S) -> str | None:
        try:
            _, text = await self.call.next_agent_turn(timeout)
            return text
        except asyncio.TimeoutError:
            return None


async def run_attempt(number: int, entry: dict[str, Any], serial: str, model: str,
                      product: dict[str, str], caller: dict[str, str], rng: random.Random) -> Attempt:
    attempt = Attempt(number)
    caller = {**caller, "serial": serial}
    room, token = agent_token(product, caller)
    attempt.room = room
    attempt.started_at = datetime.now(timezone.utc).isoformat()
    call = Call(os.environ["LIVEKIT_URL"], token)
    flow = _Flow(call, attempt)
    loop = asyncio.get_running_loop()
    started = loop.time()
    print(f"\n[kb] attempt {number}: room={room} serial={serial} model={model} question={entry['id']}")
    try:
        # 1 call_started -------------------------------------------------
        try:
            await call.connect(AGENT_JOIN_TIMEOUT_S)
            attempt.room_sid, attempt.agent_identity = call.room_sid, call.agent_identity or ""
            print(f"[kb] room sid={call.room_sid or '-'} agent={call.agent_identity}")
            flow.mark("call_started", True, f"agent joined after {call.ms(call.agent_joined_at)} ms")
        except AssertionError as exc:
            attempt.room_sid = call.room_sid
            flow.mark("call_started", False, str(exc))
            return attempt

        # 2 greeted + intake until the agent is ready for the question ----
        greeting = await flow.turn(GREETING_TIMEOUT_S)
        if greeting is None:
            flow.mark("greeted", False, f"no greeting within {GREETING_TIMEOUT_S}s")
            return attempt
        call.tag_last_agent_turn("greeting")
        flow.mark("greeted", True)
        if not await _intake(flow, greeting, entry, serial, model):
            return attempt

        # 3-4 question and answer ---------------------------------------
        await _collect_answer(flow, entry)

        # 5 answer_valid --------------------------------------------------
        attempt.validation = validate(entry, attempt.answer_turns)
        v = attempt.validation
        print("[kb] validation:\n" + v.explain())
        flow.mark("answer_valid", v.passed,
                  "every step and caution matched" if v.passed else
                  f"{len(v.failures)} of {len(v.items)} KB items failed")

        # 6-8 thanks, feedback ask, rating ------------------------------
        await flow.say(THANKS, "thanks")
        flow.mark("thanks_sent", True)
        if not await _feedback(flow, rng):
            return attempt

        # 9 call_closed ---------------------------------------------------
        await _wait_close(flow)
        return attempt
    except Exception as exc:  # noqa: BLE001 - recorded, the report needs the transcript
        attempt.error = f"{type(exc).__name__}: {exc}"
        print(f"[kb] attempt {number} error: {attempt.error}")
        return attempt
    finally:
        await call.hang_up()
        attempt.events = call.events
        attempt.duration_ms = int((loop.time() - started) * 1000)
        for cp in attempt.checkpoints.values():
            if cp.passed is None:
                cp.passed, cp.detail = False, cp.detail or "not reached"
        print(call.dialogue())


async def _intake(flow: _Flow, turn: str, entry: dict[str, Any], serial: str, model: str) -> bool:
    """Answer whatever the agent asks until it is ready for the question, then ask it."""
    call = flow.call
    for _ in range(8):
        if text_matches(turn, NOT_FOUND):
            flow.mark("question_asked", False, f"the agent could not find serial {serial}")
            return False
        if text_matches(turn, MULTIPLE):
            choice = _pick_option(turn, model)
            await flow.say(choice, "pick product")
        elif text_matches(turn, READ_BACK):
            await flow.say("Yes, that is correct.", "confirm")
        elif text_matches(turn, RECAP) and turn.rstrip().endswith("?"):
            await flow.say("Something else, please. " + entry["question"], "question")
            flow.mark("question_asked", True, "after the agent's recap of an earlier call")
            return True
        elif text_matches(turn, READY):
            await flow.say(entry["question"], "question")
            flow.mark("question_asked", True)
            return True
        elif text_matches(turn, WANTS_SERIAL) and turn.rstrip().endswith("?"):
            # The agent looks the metadata serial up by itself right after the
            # greeting; give that a moment before reading the serial out.
            nxt = await flow.turn(QUIET_S)
            if nxt is not None:
                turn = nxt
                continue
            await flow.say(serial, "serial")
        elif text_matches(turn, IDLE):
            await flow.say(STILL_HERE)
        elif turn.rstrip().endswith("?"):
            await flow.say(entry["question"], "question")
            flow.mark("question_asked", True, "the agent asked an open question")
            return True
        nxt = await flow.turn(QUIET_S if not turn.rstrip().endswith("?") else TURN_TIMEOUT_S)
        if nxt is None:
            if call.agent_waiting:
                await flow.say(entry["question"], "question")
                flow.mark("question_asked", True, "the agent went quiet after its greeting")
                return True
            nxt = await flow.turn(TURN_TIMEOUT_S)
            if nxt is None:
                break
        turn = nxt
    flow.mark("question_asked", False, "the agent never got to the point of taking a question")
    return False


def _pick_option(turn: str, model: str) -> str:
    """'Option 1, Variable Hopper … Option 2, Fixed Hopper …' -> the option for this model."""
    import re

    want = "variable" if model.startswith("V") else "fixed"
    for num, desc in re.findall(r"option (\d+)[,:]?\s*([^.]*)", turn, re.IGNORECASE):
        if want in desc.lower():
            return f"Option {num}."
    return "Option 1."


def _outstanding(entry: dict[str, Any], turns: list[str]) -> list[str]:
    v = validate(entry, turns)
    return [i.ref for i in v.items if i.result in ("missing", "missing_caution")]


async def _collect_answer(flow: _Flow, entry: dict[str, Any]) -> None:
    call, attempt = flow.call, flow.attempt
    loop = asyncio.get_running_loop()
    deadline = loop.time() + ANSWER_DEADLINE_S
    max_turns = max(12, 3 * len(entry["steps"]) + 6)
    endings = 0
    timeout = TURN_TIMEOUT_S
    for _ in range(max_turns):
        if loop.time() > deadline:
            break
        turn = await flow.turn(timeout)
        if turn is None:
            if timeout == QUIET_S and call.agent_waiting:
                await flow.say(NEXT_STEP, "next")
                timeout = TURN_TIMEOUT_S
                continue
            break
        timeout = TURN_TIMEOUT_S
        if is_holding(turn):
            call.tag_last_agent_turn("holding")
            continue
        if text_matches(turn, IDLE) and len(turn) < 80:
            call.tag_last_agent_turn("idle")
            await flow.say(STILL_HERE)
            continue

        attempt.answer_turns.append(turn)
        call.tag_last_agent_turn("answer")
        if len(attempt.answer_turns) == 1:
            flow.mark("answer_received", True)
        if not _outstanding(entry, attempt.answer_turns):
            break  # every KB step and caution has been said

        asks = turn.rstrip().endswith("?")
        if text_matches(turn, PHONE_ASK):
            await flow.say("Actually, please don't text it. " + REQUEST_FULL, "decline text")
        elif text_matches(turn, TEXT_OFFER) and asks:
            await flow.say(DECLINE_TEXT, "decline text")
        elif text_matches(turn, TRANSFER) and asks:
            await flow.say(DECLINE_TRANSFER, "decline transfer")
        elif text_matches(turn, NO_INFO):
            endings += 1
            await flow.say(ASK_REMAINING, "ask remaining")
        elif text_matches(turn, ANYTHING_ELSE):
            endings += 1
            await flow.say(ASK_REMAINING, "ask remaining")
        elif text_matches(turn, RESOLVED_ASK):
            await flow.say(NOT_FIXED, "next")
        elif asks and len(attempt.answer_turns) == 1:
            await flow.say(CLARIFY, "clarify")
        elif asks or text_matches(turn, [r"let me know", r"once you'?ve", r"when you'?re (done|ready)"]):
            await flow.say(NEXT_STEP, "next")
        else:
            timeout = QUIET_S  # a statement: it may go on by itself
        if endings >= 2:
            break
    if not attempt.answer_turns:
        flow.mark("answer_received", False, "no answer after the question")
    missing = _outstanding(entry, attempt.answer_turns)
    if missing:
        print(f"[kb] stopped collecting with {len(missing)} item(s) still not said: {', '.join(missing)}")


async def _feedback(flow: _Flow, rng: random.Random) -> bool:
    call = flow.call
    loop = asyncio.get_running_loop()
    deadline = loop.time() + FEEDBACK_TIMEOUT_S
    while loop.time() < deadline:
        turn = await flow.turn(max(1.0, deadline - loop.time()))
        if turn is None:
            break
        if is_holding(turn):
            continue
        if text_matches(turn, FEEDBACK_ASK):
            call.tag_last_agent_turn("feedback ask")
            flow.mark("feedback_asked", True)
            rating = rng.randint(1, 10)
            flow.attempt.rating = rating
            await flow.say(str(rating), "rating")
            flow.mark("feedback_answered", True, f"rated {rating}")
            return True
        if text_matches(turn, IDLE):
            await flow.say(STILL_HERE)
        elif text_matches(turn, ANYTHING_ELSE) or text_matches(turn, RESOLVED_ASK):
            await flow.say(NOTHING_ELSE, "all set")
        elif turn.rstrip().endswith("?"):
            await flow.say(THANKS, "all set")
        if call.closed:
            break
    flow.mark("feedback_asked", False,
              "the agent closed the call without asking for a rating" if call.closed
              else f"no rating request within {FEEDBACK_TIMEOUT_S}s of the thank-you")
    return False


async def _wait_close(flow: _Flow) -> None:
    call = flow.call
    loop = asyncio.get_running_loop()
    deadline = loop.time() + CLOSE_TIMEOUT_S
    while not call.closed and loop.time() < deadline:
        turn = await flow.turn(min(2.0, max(0.1, deadline - loop.time())))
        if turn and text_matches(turn, CLOSING):
            call.tag_last_agent_turn("closing")
        elif turn and turn.rstrip().endswith("?") and not call.closed:
            await flow.say("No, that's all. Goodbye.", "goodbye")
    closed = await call.wait_closed(max(0.0, deadline - loop.time()))
    if closed:
        flow.mark("call_closed", True, "the agent left and closed the room")
    else:
        flow.mark("call_closed", False, f"the agent did not end the call within {CLOSE_TIMEOUT_S}s of the rating")
