"""
The KB-steps smoke call: one live call to the deployed agent, seventeen timed checkpoints.

    call_started  greeted  question_asked  answer_received  answer_valid  image_triggered
    image_requested  text_asked  text_triggered  callback_asked  callback_task_created  thanks_sent
    feedback_asked  feedback_answered  call_closed  text_valid  call_log_complete

After the KB steps, the caller asks to see one image from the product's knowledge base
(kb/images.yaml, picked with the seed). image_requested is judged from the agent's image tool
call (`share_images`) in its logs: it passes only when the tool shares that image, matched by
its description.

The caller asks for the steps by text to SMS_TEST_PHONE (a number other than the caller's).
text_triggered is judged from the agent's own logs (`lk agent logs`, followed for the whole
call) BEFORE the call moves on to thanks and feedback. text_valid, after the call, checks
what the text said against the KB like the spoken answer.

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

So the caller declines the text, declines the offer to put the steps on screen,
asks for the complete procedure including cautions, says "done, what's next?"
after every step, and stops collecting as soon as the validator has every KB
step and caution - or the turn limit hits, after reading the agent's reply to
its last "what's next?". Agent turns left unread before a new request (text,
callback, thanks) are dropped, so they are never taken as its reply.
"""

from __future__ import annotations

import asyncio
import os
import random
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from . import agentlogs
from .call import Call, agent_token, is_holding
from .expect import text_matches
from .validator import PASS_THRESHOLD, Validation, validate

AGENT_JOIN_TIMEOUT_S = 15
GREETING_TIMEOUT_S = 30
TURN_TIMEOUT_S = 75  # a KB search can take a while; the agent fills after 5 s
QUIET_S = 8  # after a statement that asks nothing, how long before the caller speaks
FEEDBACK_TIMEOUT_S = 60
CLOSE_TIMEOUT_S = 30
TEXT_LOG_WAIT_S = 25  # how long to wait for the text to show in the agent's logs
IMAGE_LOG_WAIT_S = 5  # images ride along with the steps, so their pushes are logged by the time the answer ends
CALLBACK_LOG_WAIT_S = 30  # how long to wait for the callback task to show in the agent's logs
ANSWER_DEADLINE_S = 180  # one step per turn at 15-25 s each, plus the preface and any offers
ATTEMPT_DEADLINE_S = 8 * 60  # only against a hung call; a normal call is far shorter
CALL_TARGET_S = 4 * 60 + 59  # how long a call should take, join to hang-up; reported, never enforced
IMAGE_REQUEST_WAIT_S = 40  # from asking for an image until the agent's image tool must have settled
KB_CALL_STEPS = int(os.getenv("KB_CALL_STEPS") or "3")  # KB steps the caller asks for before "that's it" (2-3)

CHECKPOINTS = [
    ("call_started", "Call started"),
    ("greeted", "Greetings"),
    ("question_asked", "KB question asked"),
    ("answer_received", "Agent answered"),
    ("answer_valid", "KB steps matched"),
    ("image_triggered", "Image shown"),
    ("image_requested", "Requested image shown"),
    ("text_asked", "Text asked"),
    ("text_triggered", "Text sent"),
    ("callback_asked", "Callback asked"),
    ("callback_task_created", "Callback task created"),
    ("thanks_sent", "Thanks said"),
    ("feedback_asked", "Rating asked"),
    ("feedback_answered", "Rating given"),
    ("call_closed", "Call ended"),
    ("text_valid", "Text matched"),
    ("call_log_complete", "Call log sent"),
]
# Checkpoints that are noted but never fail the call: the agent may skip the rating question.
OPTIONAL = {"feedback_asked", "feedback_answered"}
CALL_LOG_WAIT_S = 120  # after the call: the record is analysed by an LLM, then POSTed to the webhook

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
SCREEN_OFFER = [r"on (your|the) screen", r"show (you|them) on"]
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
TEXT_PHONE = PHONE_ASK + [r"phone number", r"your number", r"mobile", r"number .{0,30}text"]
TEXT_SENT = [r"\bsent\b", r"on its way", r"texted (it|them|that|you)", r"just texted", r"you should (see|get|receive)"]
TEXT_FAILED = [r"didn'?t go through", r"couldn'?t (send|text)", r"landline", r"wasn'?t able to", r"unable to (send|text)",
               r"can'?t receive texts"]
CALLBACK_DONE = [r"callback (is|has been|was) (arranged|requested|set|scheduled|created|logged)",
                 r"(arranged|scheduled|requested|logged) (the|your|a) call ?back", r"someone .{0,40}will (call|reach)",
                 r"\bwill (call|reach out to) you"]
CLOSING = [r"thank you so much for calling", r"take care", r"have a great (one|day)", r"goodbye"]

# --- what the caller says -------------------------------------------------
REQUEST_FULL = ("Please walk me through the complete step-by-step procedure, "
                "including any cautions or warnings that go with it.")
DECLINE_TEXT = "No thanks, please don't text it. " + REQUEST_FULL
DECLINE_SCREEN = "No thanks, just walk me through it here. " + REQUEST_FULL
CLARIFY = "It's happening right now on the machine. " + REQUEST_FULL
NEXT_STEP = "Done. What's the next step?"
NOT_FIXED = "No, that didn't fix it yet. What's the next step?"
DECLINE_TRANSFER = "No thanks, I'd rather keep going here. What's the next step?"
ASK_REMAINING = ("Is that the complete procedure? Please give me any remaining steps, "
                 "and any cautions or warnings that go with them.")
THANKS = "Okay, that's it, thank you - I'm all set."
NOTHING_ELSE = "No, that's everything. Thanks."
STILL_HERE = "Yes, I'm still here."
ASK_TEXT = ("Could you also text me those steps? Please send me the complete list of steps, "
            "including the cautions or warnings.")
CONFIRM = "Yes, that is correct."
ASK_IMAGE = 'Can you share a picture of the "{description}"?'
CONFIRM_IMAGE = "Yes, please share that picture."
ASK_CALLBACK = ("Actually, can you have someone call me back about this? Please create a callback request. "
                "The callback number is my own number, not the one I gave you for the text: {spoken}.")
CALLBACK_CONFIRM = "Yes, that's right, my own number, {spoken}. Any time today is fine."


@dataclass
class Checkpoint:
    name: str
    label: str
    passed: bool | None = None  # None = not reached
    optional: bool = False  # a miss is noted ("not asked"), not failed
    at_ms: int | None = None
    took_ms: int | None = None
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "label": self.label, "passed": self.passed, "optional": self.optional,
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
    duration_ms: int = 0  # the whole attempt, the post-call log checks included
    call_ms: int = 0  # the call itself, join to hang-up
    call_started_at: str = ""  # wall clock, UTC ISO: when the test joined the room
    call_ended_at: str = ""  # wall clock, UTC ISO: when the room closed (or the test hung up)
    log: list[str] = field(default_factory=list)
    worker_log: list[str] = field(default_factory=list)
    worker_log_note: str = ""
    text_message: str = ""
    text_to: str = ""
    text_delivery: str = ""
    text_validation: Validation | None = None
    sms_phone: str = ""  # the number the text must go to; never written to the published report
    caller_phone: str = ""
    images: list[dict[str, Any]] = field(default_factory=list)  # the agent's image pushes, from its logs
    images_received: list[dict[str, Any]] = field(default_factory=list)  # what reached the test caller's screen
    image_request: dict[str, Any] = field(default_factory=dict)  # the image asked for, and what came back
    text_tool_trace: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checkpoints.values() if not c.optional)

    def _safe(self, text: str) -> str:
        """Text for the published report: the SMS number masked, however it was spoken or written."""
        return agentlogs.redact(text, self.sms_phone)

    def _safe_log(self, text: str) -> str:
        """A log line for the published report: both test numbers masked, and no line longer than 2000 characters."""
        return agentlogs.redact(text, self.sms_phone, self.caller_phone)[:2000]

    def as_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "room": self.room,
            "roomSid": self.room_sid,
            "agentIdentity": self.agent_identity,
            "startedAt": self.started_at,
            "answer": [self._safe(t) for t in self.answer_turns],
            "passed": self.passed,
            "durationMs": self.duration_ms,
            "callMs": self.call_ms,
            "callStartedAt": self.call_started_at,
            "callEndedAt": self.call_ended_at,
            "callTargetMs": CALL_TARGET_S * 1000,
            "error": self.error,
            "rating": self.rating,
            "checkpoints": [{**c.as_dict(), "detail": self._safe(c.detail)} for c in self.checkpoints.values()],
            "events": [{**e, "text": self._safe(e["text"])} for e in self.events],
            "validation": self.validation.as_dict() if self.validation else None,
            "text": {
                "to": agentlogs.mask(self.text_to) if self.text_to else "",
                "message": self._safe(self.text_message),
                "delivery": self.text_delivery,
                "validation": self.text_validation.as_dict() if self.text_validation else None,
            },
            "workerLogLines": len(self.worker_log),
            "images": {"pushes": self.images, "received": self.images_received, "request": self.image_request},
            "textToolTrace": self.text_tool_trace,
            "workerLog": [self._safe_log(x) for x in self.worker_log],
            "workerLogNote": self.worker_log_note,
            "callLog": [self._safe_log(x) for x in self.log],
        }


class _Flow:
    def __init__(self, call: Call, attempt: Attempt) -> None:
        self.call = call
        self.attempt = attempt
        self.tail: agentlogs.LogTail | None = None  # the agent's logs for this room, followed live
        self._last_mark = 0
        for name, label in CHECKPOINTS:
            attempt.checkpoints[name] = Checkpoint(name, label, optional=name in OPTIONAL)

    def mark(self, name: str, passed: bool, detail: str = "") -> None:
        cp = self.attempt.checkpoints[name]
        now = self.call.ms(self.call._now()) or 0
        cp.passed, cp.at_ms, cp.took_ms, cp.detail = (None if cp.optional and not passed else passed), now, now - self._last_mark, detail
        self._last_mark = now
        print(f"[kb] {'PASS' if passed else ('NOTE' if cp.optional else 'FAIL')} {name} @{now / 1000:.1f}s {detail}")

    async def say(self, text: str, tag: str = "") -> None:
        await self.call.wait_listening(TURN_TIMEOUT_S)
        await self.call.say(text, tag)

    def drop_unread(self) -> None:
        """Before a new request: agent turns that arrived during a log wait answer the step
        before, and read now they would be taken as the reply to this one."""
        if n := self.call.drop_unread_turns():
            print(f"[kb] dropped {n} late agent turn(s) before the next request")

    async def turn(self, timeout: float = TURN_TIMEOUT_S) -> str | None:
        try:
            _, text = await self.call.next_agent_turn(timeout)
            return text
        except asyncio.TimeoutError:
            return None


async def run_attempt(number: int, entry: dict[str, Any], serial: str, model: str,
                      product: dict[str, str], caller: dict[str, str], rng: random.Random,
                      sms_phone: str, image: dict[str, Any] | None = None) -> Attempt:
    entry = short_entry(entry)
    attempt = Attempt(number)
    attempt.sms_phone, attempt.caller_phone = sms_phone, caller["phone"]
    caller = {**caller, "serial": serial}
    room, token = agent_token(product, caller)
    attempt.room = room
    attempt.started_at = datetime.now(timezone.utc).isoformat()
    call = Call(os.environ["LIVEKIT_URL"], token)
    flow = _Flow(call, attempt)
    loop = asyncio.get_running_loop()
    started = loop.time()
    print(f"\n[kb] attempt {number}: room={room} serial={serial} model={model} question={entry['id']}")

    async def _run() -> None:
        if (why := agentlogs.available()) is None:
            try:
                flow.tail = agentlogs.LogTail(room)
                await flow.tail.start()
            except Exception as exc:  # noqa: BLE001 - reported on the text checks; the call still runs
                flow.tail, attempt.worker_log_note = None, f"could not follow the agent's logs: {type(exc).__name__}: {exc}"
        else:
            attempt.worker_log_note = f"worker logs not read: {why}"
        # 1 call_started -------------------------------------------------
        try:
            await call.connect(AGENT_JOIN_TIMEOUT_S)
            attempt.room_sid, attempt.agent_identity = call.room_sid, call.agent_identity or ""
            print(f"[kb] room sid={call.room_sid or '-'} agent={call.agent_identity}")
            flow.mark("call_started", True, f"agent joined after {call.ms(call.agent_joined_at)} ms")
        except AssertionError as exc:
            attempt.room_sid = call.room_sid
            flow.mark("call_started", False, str(exc))
            return

        # 2 greeted + intake until the agent is ready for the question ----
        greeting = await flow.turn(GREETING_TIMEOUT_S)
        if greeting is None:
            flow.mark("greeted", False, f"no greeting within {GREETING_TIMEOUT_S}s")
            return
        call.tag_last_agent_turn("greeting")
        flow.mark("greeted", True)
        if not await _intake(flow, greeting, entry, serial, model):
            return

        # 3-4 question and answer ---------------------------------------
        await _collect_answer(flow, entry)

        # 5 answer_valid --------------------------------------------------
        attempt.validation = validate(entry, attempt.answer_turns)
        v = attempt.validation
        print("[kb] validation:\n" + v.explain())
        matched = len(v.items) - len(v.failures)
        score = f"{matched} of {len(v.items)} KB items matched ({v.score:.0%}, pass at {PASS_THRESHOLD:.0%})"
        if v.passed:
            detail = "every step and caution matched"
        elif v.meets_threshold():
            detail = f"{score}; passed on the threshold. Missed: " + "; ".join(f"{i.ref} ({i.reason})" for i in v.failures)
        elif v.wrong_values:
            detail = f"{score}; failed: wrong value in " + ", ".join(i.ref for i in v.wrong_values)
        else:
            detail = f"{score}; below the threshold"
        flow.mark("answer_valid", v.meets_threshold(), detail)

        await _check_image_triggered(flow)  # images ride along with the answer, so judge them now

        # one named image from the product's knowledge base, by the agent's image tool ----
        await _request_image(flow, image)

        # the same steps by text; the text itself is checked from the agent's logs at the end
        await _request_text(flow, caller["phone"], sms_phone)
        await _check_text_triggered(flow, sms_phone)  # before thanks and the feedback step

        # callback request: the agent must create a task, read from its logs ----
        await _request_callback(flow, caller["phone"])
        await _check_callback_task(flow, caller["phone"])

        # 6-8 thanks, feedback ask, rating ------------------------------
        flow.drop_unread()
        await flow.say(THANKS, "thanks")
        flow.mark("thanks_sent", True)
        await _feedback(flow, rng)  # optional: if no rating is asked, the rest of the call is still checked

        # 9 call_closed ---------------------------------------------------
        await _wait_close(flow)

    try:
        await asyncio.wait_for(_run(), ATTEMPT_DEADLINE_S)
        return attempt
    except asyncio.TimeoutError:
        attempt.error = f"the call did not finish within {ATTEMPT_DEADLINE_S // 60} min - stopped"
        print(f"[kb] attempt {number} error: {attempt.error}")
        return attempt
    except Exception as exc:  # noqa: BLE001 - recorded, the report needs the transcript
        attempt.error = f"{type(exc).__name__}: {exc}"
        print(f"[kb] attempt {number} error: {attempt.error}")
        return attempt
    finally:
        await call.hang_up()
        attempt.call_ms = call.ms(call.room_closed_at or call.agent_left_at or call._now()) or 0
        if call.started_at:
            attempt.call_started_at = call.started_at.isoformat(timespec="milliseconds")
            attempt.call_ended_at = (call.started_at + timedelta(milliseconds=attempt.call_ms)).isoformat(timespec="milliseconds")
        if attempt.call_ms > CALL_TARGET_S * 1000:
            print(f"[kb] NOTE the call took {_mmss(attempt.call_ms / 1000)}, over the {_mmss(CALL_TARGET_S)} target")
        attempt.log = call.log_lines
        try:
            await _worker_logs(flow, entry, sms_phone)
        except Exception as exc:  # noqa: BLE001 - debugging aid; never hides the call's own result
            attempt.worker_log_note = f"{type(exc).__name__}: {exc}"
            print(f"[kb] worker logs failed: {attempt.worker_log_note}")
            if flow.tail is not None:
                await flow.tail.stop()
        _write_call_log(attempt)
        attempt.events = call.events
        attempt.duration_ms = int((loop.time() - started) * 1000)
        for cp in attempt.checkpoints.values():
            if cp.passed is None:
                if cp.optional:
                    cp.detail = cp.detail or "not asked"
                else:
                    cp.passed, cp.detail = False, cp.detail or "not reached"



def _write_call_log(attempt: Attempt) -> None:
    """Everything the room delivered, for engineers: report-internal/call-log-attempt-N.txt.
    Not part of the management report."""
    from .routing import ROOT

    path = ROOT / "report-internal" / f"call-log-attempt-{attempt.number}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    head = f"room={attempt.room} sid={attempt.room_sid or '-'} agent={attempt.agent_identity or '-'}\n"
    path.write_text(head + "\n".join(attempt.log) + "\n", encoding="utf-8")
    print(f"[kb] call log -> {path.relative_to(ROOT)}")
    wpath = path.with_name(f"worker-log-attempt-{attempt.number}.txt")
    wpath.write_text(head + (attempt.worker_log_note + "\n" if attempt.worker_log_note else "")
                     + "\n".join(attempt.worker_log) + "\n", encoding="utf-8")
    print(f"[kb] worker log -> {wpath.relative_to(ROOT)}")


async def _request_text(flow: _Flow, caller_phone: str, sms_phone: str) -> bool:
    """Ask for the steps by text to a DIFFERENT number than the caller's. The agent first offers
    the caller's own number; the caller refuses it and gives the SMS number, then confirms the
    read-back. Stops once the agent says whether the text went. What was sent, and to whom, is
    read later from the agent's logs."""
    import re

    call = flow.call
    new, old = agentlogs.last10(sms_phone), agentlogs.last10(caller_phone)
    spoken = " ".join(new)
    flow.drop_unread()
    await flow.say(ASK_TEXT, "ask text")
    gave = 0
    for _ in range(10):
        turn = await flow.turn(TURN_TIMEOUT_S)
        if turn is None:
            break
        if is_holding(turn):
            call.tag_last_agent_turn("holding")
            continue
        asks = turn.rstrip().endswith("?")
        said = re.sub(r"\D", "", turn)  # the digits the agent spoke or wrote
        # A refusal ("that number can't receive texts ... which number?") also asks for a
        # number, so it is checked first.
        if text_matches(turn, TEXT_FAILED):
            call.tag_last_agent_turn("text result")
            flow.mark("text_asked", True, "the agent answered the text request (it could not text this number)")
            return True
        if asks and new in said:
            await flow.say(CONFIRM, "confirm number")
        elif asks and old in said and gave < 3:
            gave += 1
            await flow.say(f"No, that's not the right number. Please text it to a different number: {spoken}", "different number")
        elif asks and text_matches(turn, READ_BACK + TEXT_PHONE) and gave < 3:
            gave += 1
            await flow.say(f"Please use this number: {spoken}", "different number")
        elif text_matches(turn, TEXT_SENT):
            call.tag_last_agent_turn("text result")
            flow.mark("text_asked", True, "the agent answered the text request")
            return True
        elif text_matches(turn, IDLE):
            await flow.say(STILL_HERE)
        elif asks and gave < 3:
            await flow.say("Yes, please text the steps to me.", "confirm text")
        # else a statement on the way to the result ("Sure, I'll send that now."): keep listening
    flow.mark("text_asked", False, "the agent never confirmed the text")
    return False


async def _request_callback(flow: _Flow, caller_phone: str) -> bool:
    """Ask for a call back. The agent confirms the number (the caller's own); the caller agrees.
    Stops once the agent says the callback is arranged. Whether a task was really created is
    read from the agent's logs, not from what it says."""
    call = flow.call
    spoken = " ".join(agentlogs.last10(caller_phone))
    flow.drop_unread()
    await flow.say(ASK_CALLBACK.format(spoken=spoken), "ask callback")
    confirmed = 0
    for _ in range(6):
        turn = await flow.turn(TURN_TIMEOUT_S)
        if turn is None:
            break
        if is_holding(turn):
            call.tag_last_agent_turn("holding")
            continue
        if text_matches(turn, CALLBACK_DONE):
            call.tag_last_agent_turn("callback result")
            flow.mark("callback_asked", True, "the agent answered the callback request")
            return True
        if text_matches(turn, IDLE):
            await flow.say(STILL_HERE)
        elif turn.rstrip().endswith("?") and confirmed < 3:
            confirmed += 1
            await flow.say(CALLBACK_CONFIRM.format(spoken=spoken), "confirm callback")
        # else a statement on the way to the result ("I'll get that set up."): keep listening
    flow.mark("callback_asked", False, "the agent never confirmed the callback")
    return False


def _check_call_log(flow: _Flow, lines: list[dict[str, Any]], caller_turns: int) -> None:
    """After the call: did the agent write the call record with everything, and deliver it?
    Judged from its logs - the record's content itself goes to the webhook, so what we can see is
    that the transcript was analysed (turns), the summary and notes were extracted, and the record was
    accepted (2xx)."""
    attempt = flow.attempt
    if flow.tail is None:
        flow.mark("call_log_complete", False, attempt.worker_log_note or "the agent's logs could not be followed")
        return
    rec = agentlogs.call_record(lines)
    if attempt.error and rec["delivered"] is None:
        # The call broke down before its record was sent: that failure is already reported by the
        # checkpoint that broke, so this one is "not reached" rather than a second failure.
        attempt.checkpoints["call_log_complete"].detail = (
            f"not checked: the call ended early ({attempt.error[:90]}), so no call log was sent")
        return
    problems = []
    if rec["failure"]:
        problems.append(rec["failure"])
    if rec["delivered"] is None:
        problems.append("the call log was never delivered to the webhook")
    elif not 200 <= rec["delivered"] < 300:
        problems.append(f"the webhook answered {rec['delivered']}")
    if rec["turns"] is None:
        problems.append("the transcript was never analysed")
    elif rec["turns"] == 0:
        problems.append(f"the transcript was empty, the caller spoke {caller_turns} times")
    for f in ("call_summary", "notes"):
        if f not in rec["fields"]:
            problems.append(f"no {f} extracted")
    detail = (f"delivered {rec['delivered']}, {rec['turns']} transcript turns (the caller spoke {caller_turns} times), "
              f"fields {rec['fields']}, summary from {rec['summary_source'] or '-'}")
    flow.mark("call_log_complete", not problems, "; ".join(problems) if problems else detail)


async def _check_callback_task(flow: _Flow, caller_phone: str) -> None:
    """Did the agent create the callback task, for the caller's number? Judged from its logs:
    the `request_callback` tool call and an accepted (2xx) reply from the task service."""
    attempt, tail = flow.attempt, flow.tail
    if tail is None:
        flow.mark("callback_task_created", False, attempt.worker_log_note or "the agent's logs could not be followed")
        return
    await tail.wait_until(lambda lines: agentlogs.callback_created(lines) is not None, CALLBACK_LOG_WAIT_S)
    tasks = agentlogs.callback_tasks(tail.lines)
    if not tasks:
        flow.mark("callback_task_created", False, f"no request_callback call in the agent's logs within {CALLBACK_LOG_WAIT_S}s")
        return
    made = agentlogs.callback_created(tail.lines)
    if made is None:
        last = tasks[-1]
        flow.mark("callback_task_created", False,
                  "the task service did not accept the task (" +
                  (f"HTTP {last['status']}" if last["status"] is not None else "no reply logged") + ")")
        return
    if agentlogs.last10(made["phone"]) != agentlogs.last10(caller_phone):
        flow.mark("callback_task_created", False,
                  f"the task was made for the {agentlogs.mask(made['phone'])}, not the caller's {agentlogs.mask(caller_phone)}")
        return
    flow.mark("callback_task_created", True,
              f"task created (HTTP {made['status']}) for the {agentlogs.mask(made['phone'])}: {made['reason']}")


def _texts_by_destination(lines: list[dict[str, Any]], sms_phone: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    texts = agentlogs.sent_texts(lines)
    return texts, agentlogs.texts_to(texts, sms_phone)


async def _check_image_triggered(flow: _Flow) -> None:
    """Did the agent's image tool fire while it talked the caller through the steps? Judged from its
    logs: it searches its image store, picks the relevant pictures and pushes them to the caller's
    screen (`pushing_images`). The trigger is what is tested; whether the test caller's screen
    received them is recorded next to it."""
    attempt, tail = flow.attempt, flow.tail
    if tail is None:
        flow.mark("image_triggered", False, attempt.worker_log_note or "the agent's logs could not be followed")
        return
    await tail.wait_until(lambda lines: bool(agentlogs.image_pushes(lines)), IMAGE_LOG_WAIT_S)
    pushes = attempt.images = agentlogs.image_pushes(tail.lines)
    attempt.images_received = list(flow.call.images)
    if not pushes:
        seen = agentlogs.image_outcomes(tail.lines)
        why = ", ".join(f"{k} x{n}" for k, n in sorted(seen.items())) or "no image activity at all"
        if seen.get("searches") and not seen.get("searches_with_candidates"):
            # The tool ran but the image store holds nothing for this topic: noted, not failed.
            attempt.checkpoints["image_triggered"].optional = True
            flow.mark("image_triggered", False,
                      f"the image tool searched {seen['searches']} time(s) but the store has no image for this topic ({why})")
            return
        flow.mark("image_triggered", False, f"the agent never pushed an image to the caller ({why})")
        return
    shown = sum(p["images"] for p in pushes)
    got = len(attempt.images_received)
    queries = "; ".join(sorted({p["query"] for p in pushes if p["query"]}))
    flow.mark("image_triggered", True,
              f"{len(pushes)} image push(es), {shown} image(s), for: {queries or '-'}; "
              f"{got} received by the test caller")


def _same_image(received: dict[str, Any], wanted: dict[str, Any]) -> bool:
    """The agent sends the stored description with each image, so that is what identifies it."""
    def norm(text: str) -> str:
        return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())
    return norm(received.get("description", "")) == norm(wanted["description"])


async def _request_image(flow: _Flow, image: dict[str, Any] | None) -> None:
    """Ask for one knowledge-base image by its description. Judged only from the agent's image tool
    call (`share_images`) in its logs: the tool must run for the request and settle with that image
    picked and shared. `discarded` - the same picture was shared just before - counts as shared."""
    call, attempt, tail = flow.call, flow.attempt, flow.tail
    if image is None:
        attempt.checkpoints["image_requested"].optional = True
        flow.mark("image_requested", False, "no image list for this model in kb/images.yaml")
        return
    request = attempt.image_request = {"description": image["description"], "id": image["id"],
                                       "tool": None, "matched": False}
    if tail is None:
        flow.mark("image_requested", False, attempt.worker_log_note or "the agent's logs could not be followed")
        return
    log_from = len(tail.lines)
    flow.drop_unread()
    await flow.say(ASK_IMAGE.format(description=image["description"]), "ask image")
    loop = asyncio.get_running_loop()
    deadline = loop.time() + IMAGE_REQUEST_WAIT_S
    replies = 0
    while loop.time() < deadline and not any(r["status"] for r in agentlogs.image_requests(tail.lines[log_from:])):
        turn = await flow.turn(min(2.0, max(0.1, deadline - loop.time())))
        if turn is None:
            if call.closed:
                break
            continue
        if is_holding(turn):
            call.tag_last_agent_turn("holding")
            continue
        call.tag_last_agent_turn("image reply")
        if text_matches(turn, IDLE):
            await flow.say(STILL_HERE)
        elif turn.rstrip().endswith("?") and replies < 2:
            replies += 1
            await flow.say(CONFIRM_IMAGE, "confirm image")

    lines = tail.lines[log_from:]
    calls = agentlogs.image_requests(lines)
    wanted = f'"{image["description"]}"'
    if not calls:
        seen = agentlogs.image_outcomes(lines)
        why = ", ".join(f"{k} x{n}" for k, n in sorted(seen.items())) or "no image activity in its logs"
        flow.mark("image_requested", False, f"asked for {wanted}; the agent never called its image tool ({why})")
        return
    hit = next((c for c in calls if c["status"] in ("shared", "discarded")
                and any(_same_image({"description": d}, image) for d in c["descriptions"])), None)
    used = hit or calls[-1]
    request["tool"] = {"query": used["query"], "status": used["status"], "picked": used["descriptions"]}
    tool = f'share_images query="{used["query"]}" settled {used["status"] or "-"}'
    if hit:
        request["matched"] = True
        flow.mark("image_requested", True, f"{wanted} shared by the image tool ({tool})")
    elif used["status"] in ("shared", "discarded"):
        flow.mark("image_requested", False, f"asked for {wanted} but the image tool shared: "
                  + (", ".join(f'"{d}"' for d in used["descriptions"]) or "-") + f" ({tool})")
    elif used["status"] is None:
        flow.mark("image_requested", False,
                  f"asked for {wanted}; the image tool had not finished within {IMAGE_REQUEST_WAIT_S}s ({tool})")
    else:
        flow.mark("image_requested", False, f"asked for {wanted}; the image tool did not share it ({tool})")


async def _check_text_triggered(flow: _Flow, sms_phone: str) -> None:
    """Did the agent send the text to the SMS number? Judged from its logs right after the text
    request, so it comes before the call moves on to thanks and feedback."""
    attempt, tail = flow.attempt, flow.tail
    if tail is None:
        flow.mark("text_triggered", False, attempt.worker_log_note or "the agent's logs could not be followed")
        return
    arrived = await tail.wait_until(lambda lines: bool(agentlogs.texts_to(agentlogs.sent_texts(lines), sms_phone)),
                                    TEXT_LOG_WAIT_S)
    texts, mine = _texts_by_destination(tail.lines, sms_phone)
    if not texts:
        flow.mark("text_triggered", False, f"no text appeared in the agent's logs within {TEXT_LOG_WAIT_S}s")
        return
    if not arrived:
        flow.mark("text_triggered", False, "the agent texted " + ", ".join(sorted({agentlogs.mask(t["to"]) for t in texts}))
                  + f", not the {agentlogs.mask(sms_phone)} it was given")
        return
    sent = mine[-1]
    failures = agentlogs.text_failures(tail.lines)
    # The trigger is what is tested. A refused delivery is recorded but never fails the call.
    attempt.text_delivery = ("not delivered: " + "; ".join(failures)) if failures else "accepted by the SMS provider"
    attempt.text_tool_trace = agentlogs.text_tool_trace(tail.lines)
    flow.mark("text_triggered", True, f"text sent to the {agentlogs.mask(sent['to'])} (delivery: {attempt.text_delivery}); "
              f"tool trace: {' > '.join(attempt.text_tool_trace)}")


async def _worker_logs(flow: _Flow, entry: dict[str, Any], sms_phone: str) -> None:
    """After the call: take the agent's logs to the end, print them, and check what the text said."""
    attempt, tail = flow.attempt, flow.tail
    lines: list[dict[str, Any]] = []
    if tail is not None:
        lines = await tail.finish(CALL_LOG_WAIT_S)
        attempt.worker_log = agentlogs.render(lines)
        attempt.images = agentlogs.image_pushes(lines)  # the whole call, not just up to the check
        attempt.images_received = list(flow.call.images)
        if not lines:
            attempt.worker_log_note = "the agent's logs had no lines for this room"
    print(f"[kb] worker logs for {attempt.room}: {len(lines)} line(s)" +
          (f" - {attempt.worker_log_note}" if attempt.worker_log_note else ""))
    for line in attempt.worker_log:
        print(f"  [worker] {line}")
    if attempt.checkpoints["call_started"].passed:
        _check_call_log(flow, lines, sum(1 for e_ in flow.call.events if e_["role"] == "caller"))
    if attempt.checkpoints["text_asked"].passed is None:
        return  # the call never got as far as asking for a text

    _, mine = _texts_by_destination(lines, sms_phone)
    if not mine:
        flow.mark("text_valid", False, "no text to the SMS number to check")
        return
    sent = mine[-1]
    attempt.text_to, attempt.text_message = sent["to"], sent["message"]
    failures = agentlogs.text_failures(lines)
    attempt.text_delivery = ("not delivered: " + "; ".join(failures)) if failures else "accepted by the SMS provider"
    v = attempt.text_validation = validate(entry, [sent["message"]])
    print("[kb] text validation:\n" + v.explain())
    matched = len(v.items) - len(v.failures)
    flow.mark("text_valid", v.meets_threshold(),
              f"{matched} of {len(v.items)} KB items matched ({v.score:.0%}, pass at {PASS_THRESHOLD:.0%})")


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


def short_entry(entry: dict[str, Any], steps: int | None = None) -> dict[str, Any]:
    """The part of a KB entry a 3-minute call checks: its first steps only. Cautions are left out,
    as they usually belong to later steps."""
    n = max(1, steps or KB_CALL_STEPS)
    return {**entry, "steps": list(entry.get("steps") or [])[:n], "cautions": []}


def _outstanding(entry: dict[str, Any], turns: list[str]) -> list[str]:
    v = validate(entry, turns)
    return [i.ref for i in v.items if i.result in ("missing", "missing_caution")]


async def _collect_answer(flow: _Flow, entry: dict[str, Any]) -> None:
    call, attempt = flow.call, flow.attempt
    loop = asyncio.get_running_loop()
    deadline = loop.time() + ANSWER_DEADLINE_S
    max_turns = 3 * len(entry["steps"]) + 3
    endings = 0
    timeout = TURN_TIMEOUT_S
    timed_out = False
    for _ in range(max_turns):
        if loop.time() > deadline:
            break
        turn = await flow.turn(timeout)
        if turn is None and call.closed:
            print("[kb] the agent left the call during the answer")
            break
        if turn is None:
            if timeout == QUIET_S and call.agent_waiting:
                await flow.say(NEXT_STEP, "next")
                timeout = TURN_TIMEOUT_S
                continue
            timed_out = True
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
        elif text_matches(turn, SCREEN_OFFER) and asks:
            await flow.say(DECLINE_SCREEN, "decline screen")
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
    # Stopped on the deadline or turn limit right after asking for more: the agent's reply to that
    # is still part of the answer, and left unread it would be taken as the reply to the text request.
    if not timed_out and not call.closed and call.caller_spoke_last:
        await _read_owed_reply(flow)
    if not attempt.answer_turns:
        flow.mark("answer_received", False, "no answer after the question")
    missing = _outstanding(entry, attempt.answer_turns)
    if missing:
        print(f"[kb] stopped collecting with {len(missing)} item(s) still not said: {', '.join(missing)}")


async def _read_owed_reply(flow: _Flow) -> None:
    """Wait for the agent's reply to the caller's last message and keep it as answer text."""
    call, attempt = flow.call, flow.attempt
    for _ in range(3):
        turn = await flow.turn(TURN_TIMEOUT_S)
        if turn is None:
            return
        if is_holding(turn):
            call.tag_last_agent_turn("holding")
            continue
        if text_matches(turn, IDLE) and len(turn) < 80:
            call.tag_last_agent_turn("idle")
            return
        attempt.answer_turns.append(turn)
        call.tag_last_agent_turn("answer")
        return


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


def _mmss(seconds: float) -> str:
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


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
        took = (call.ms(call.room_closed_at or call.agent_left_at or call._now()) or 0) / 1000
        flow.mark("call_closed", True,
                  f"the agent left and closed the room; the call took {_mmss(took)} (target under {_mmss(CALL_TARGET_S)})")
    else:
        flow.mark("call_closed", False, f"the agent did not end the call within {CLOSE_TIMEOUT_S}s of the rating")
