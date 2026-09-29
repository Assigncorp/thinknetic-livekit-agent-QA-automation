"""
One real call to the deployed agent, driven over the LiveKit SDK.

What the wire actually looks like (VERIFIED 2026-09-28 against etnyre-dev):

  * The agent joins about 0.4 s after we connect, as a kind=AGENT participant
    whose `lk.agent.name` attribute is the worker name.
  * Every agent turn is ONE text stream on `lk.transcription`, closed when the
    turn is finished and flagged `lk.transcription_final=true`. So a completed
    stream is a completed turn - no quiet-timer guesswork.
  * `lk.agent.state` walks listening -> thinking -> speaking -> listening. That
    is the ground truth for "the agent is waiting for us", and it is what the
    driver waits on before it types. A message sent mid-turn is dropped by this
    agent (docs/chat-flow.md, behaviour 3), so this is not politeness.
  * The caller types on `lk.chat`. The agent does not echo it back.

The conversation contract - which agent turn gets which reply - is the same
chatFlow.intents the browser suite and the judge's caller read. Nothing about
the dialogue is hardcoded here.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .audio import AgentAudio, CallerMic
from .bridge import Transcript, Turn, testbed
from src import numerals  # noqa: E402  (judge on path via bridge)
from .session import Grant

AGENT_KIND = 4
EGRESS_KIND = 2


@dataclass
class Segment:
    """One finished transcription stream."""

    speaker: str  # "agent" | "caller"
    text: str
    opened: float
    closed: float
    sender: str
    attributes: dict[str, str] = field(default_factory=dict)
    intent: str | None = None
    idle: bool = False

    @property
    def final(self) -> bool:
        return self.attributes.get("lk.transcription_final") == "true"


@dataclass
class Sent:
    text: str
    at: float
    intent: str | None = None  # the agent intent this answered


@dataclass
class Step:
    intent: str
    agent: str
    reply: str | None
    waited_ms: int


class AgentNeverJoined(TimeoutError):
    pass


class AgentHungUp(RuntimeError):
    """The agent ended the call before the caller was done."""


def _intents() -> list[tuple[str, list[re.Pattern[str]], str | None]]:
    return [
        (i["id"], [re.compile(m, re.I) for m in i["match"]], i.get("reply"))
        for i in testbed.config()["chatFlow"]["intents"]
    ]


def match_intent(text: str) -> tuple[str, str | None] | None:
    for intent_id, patterns, reply in _intents():
        if any(p.search(text) for p in patterns):
            return intent_id, reply
    return None


def is_idle(text: str) -> bool:
    lowered = text.lower()
    return any(p.lower() in lowered for p in testbed.config()["chatFlow"]["agentIdlePrompts"])


def render(template: str, values: dict[str, str]) -> str:
    """Multi-pass, because a value can carry a placeholder: offersToText's reply
    is {{textOffer}}, and the accept answer behind it ends in {{phone}}. Same
    rule as ChatWidget.render()."""
    out = template
    for _ in range(3):
        if "{{" not in out:
            break
        before = out
        for key, value in values.items():
            out = out.replace("{{" + key + "}}", value)
        if out == before:
            break
    return out


class Call:
    """A connected caller. Use as `async with Call(grant) as call:`."""

    def __init__(
        self,
        grant: Grant,
        *,
        keep_pcm: bool = False,
        subscribe_audio: bool = True,
    ) -> None:
        self.grant = grant
        self._lk = testbed.judge_config()["livekit"]
        self._sdk = testbed.config()["livekitSdk"]
        self.room: Any = None
        self.t0 = 0.0
        self.connected_at: float | None = None
        self.agent_identity: str | None = None
        self.agent_attributes: dict[str, str] = {}
        self.agent_joined_at: float | None = None
        self.agent_left_at: float | None = None
        self.agent_audio_track_at: float | None = None
        self.agent_audio_source: int | None = None
        self.others: list[tuple[str, int]] = []  # (identity, kind) of everyone else
        self.states: list[tuple[float, str]] = []
        self.segments: list[Segment] = []
        self.sent: list[Sent] = []
        self.disconnected_at: float | None = None
        self.audio = AgentAudio(float(self._sdk["audio"]["silenceRms"]), keep_pcm=keep_pcm)
        self.mic: CallerMic | None = None
        self._subscribe_audio = subscribe_audio
        self._agent_joined = asyncio.Event()
        self._agent_turns: asyncio.Queue[Segment] = asyncio.Queue()
        self._state_changed = asyncio.Event()
        self._open_streams = 0
        self._tasks: set[asyncio.Task[Any]] = set()

    # -- clock ------------------------------------------------------------

    def ms(self, t: float | None) -> int | None:
        return None if t is None else int((t - self.t0) * 1000)

    @property
    def state(self) -> str | None:
        return self.states[-1][1] if self.states else None

    # -- lifecycle ----------------------------------------------------------

    async def __aenter__(self) -> "Call":
        await self.connect()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.hang_up()

    def _on_agent(self, participant: Any) -> None:
        if self.agent_identity is None:
            self.agent_identity = participant.identity
            self.agent_attributes = dict(participant.attributes)
            self.agent_joined_at = time.monotonic()
            state = participant.attributes.get("lk.agent.state")
            if state:
                self.states.append((self.agent_joined_at, state))
            self._agent_joined.set()

    async def connect(self) -> None:
        from livekit import rtc

        self.room = rtc.Room()
        room = self.room

        @room.on("participant_connected")
        def _joined(p: Any) -> None:
            if int(p.kind) == AGENT_KIND:
                self._on_agent(p)
            else:
                self.others.append((p.identity, int(p.kind)))

        @room.on("participant_disconnected")
        def _left(p: Any) -> None:
            if p.identity == self.agent_identity and self.agent_left_at is None:
                self.agent_left_at = time.monotonic()

        @room.on("participant_attributes_changed")
        def _attrs(changed: dict[str, str], p: Any) -> None:
            if p.identity == self.agent_identity or int(p.kind) == AGENT_KIND:
                self.agent_attributes.update(changed)
                if "lk.agent.state" in changed:
                    self.states.append((time.monotonic(), changed["lk.agent.state"]))
                    self._state_changed.set()

        @room.on("track_subscribed")
        def _track(track: Any, publication: Any, p: Any) -> None:
            if int(p.kind) == AGENT_KIND and int(track.kind) == int(rtc.TrackKind.KIND_AUDIO):
                self.agent_audio_track_at = time.monotonic()
                self.agent_audio_source = int(publication.source)
                if self._subscribe_audio and not self.audio.attached:
                    self.audio.attach(track)

        @room.on("disconnected")
        def _gone(reason: Any = None) -> None:
            self.disconnected_at = time.monotonic()

        def _transcription(reader: Any, sender: str) -> None:
            task = asyncio.create_task(self._read_segment(reader, sender))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

        room.register_text_stream_handler("lk.transcription", _transcription)

        self.t0 = time.monotonic()
        connect_timeout = int(self._lk["connectTimeoutMs"]) / 1000
        await asyncio.wait_for(room.connect(self.grant.server_url, self.grant.token), connect_timeout)
        self.connected_at = time.monotonic()

        # The agent can be in the room before our own connect() returns.
        for p in room.remote_participants.values():
            if int(p.kind) == AGENT_KIND:
                self._on_agent(p)
            elif (p.identity, int(p.kind)) not in self.others:
                self.others.append((p.identity, int(p.kind)))
            for pub in p.track_publications.values():
                if pub.track is not None and int(p.kind) == AGENT_KIND:
                    _track(pub.track, pub, p)

        try:
            await asyncio.wait_for(
                self._agent_joined.wait(), int(self._sdk["budgets"]["agentJoinMs"]) / 1000
            )
        except asyncio.TimeoutError as exc:
            raise AgentNeverJoined(
                f"connected to {self.grant.room!r} but no agent joined within "
                f"{self._sdk['budgets']['agentJoinMs']}ms. The token dispatched "
                f"{[a.get('agentName') for a in self.grant.dispatches]} - if that is not the "
                f"name the worker registers with, the dispatch is accepted and does nothing."
            ) from exc

    async def _read_segment(self, reader: Any, sender: str) -> None:
        opened = time.monotonic()
        self._open_streams += 1
        text = ""
        try:
            async for chunk in reader:
                text += chunk
        except Exception as exc:  # noqa: BLE001
            # A stream still open when the call hangs up ends with StreamError
            # "Disconnected while receiving". Expected at hang-up, noise in a
            # log; anything before hang-up is a real error and is re-raised.
            if self.disconnected_at is None and self.agent_left_at is None:
                raise
            return
        finally:
            self._open_streams -= 1
        attributes = dict(reader.info.attributes or {})
        mine = sender == self.room.local_participant.identity or (
            self.mic is not None and attributes.get("lk.transcribed_track_id") == self.mic.track_sid
        )
        segment = Segment(
            speaker="caller" if mine else "agent",
            text=text.strip(),
            opened=opened,
            closed=time.monotonic(),
            sender=sender,
            attributes=attributes,
        )
        if not segment.text:
            # Recorded, so a test can count empty segments - TRN-04.
            self.segments.append(segment)
            return
        segment.idle = segment.speaker == "agent" and is_idle(segment.text)
        self.segments.append(segment)
        if segment.speaker == "agent":
            await self._agent_turns.put(segment)

    async def hang_up(self) -> None:
        await self.audio.close()
        if self.room is not None and self.disconnected_at is None:
            await self.room.disconnect()
            self.disconnected_at = time.monotonic()
        for task in list(self._tasks):
            task.cancel()

    # -- waiting ------------------------------------------------------------

    async def next_agent_turn(self, timeout_ms: int) -> Segment | None:
        try:
            return await asyncio.wait_for(self._agent_turns.get(), timeout_ms / 1000)
        except asyncio.TimeoutError:
            return None

    async def wait_for_state(self, wanted: set[str], timeout_ms: int, after: float = 0.0) -> float | None:
        """When the agent's state first became one of `wanted` after `after`."""
        deadline = time.monotonic() + timeout_ms / 1000
        while True:
            for t, s in self.states:
                if t >= after and s in wanted:
                    return t
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            self._state_changed.clear()
            try:
                await asyncio.wait_for(self._state_changed.wait(), min(remaining, 0.5))
            except asyncio.TimeoutError:
                pass

    def drain(self) -> int:
        """Mark every agent turn received so far as read. They stay in
        `segments` and in the transcript; they just stop blocking settle()."""
        n = 0
        while not self._agent_turns.empty():
            self._agent_turns.get_nowait()
            n += 1
        return n

    async def settle(self, timeout_ms: int = 60000, stable_ms: int = 1200, drain: bool = False) -> None:
        """Until the agent is listening, no turn is streaming, and it has stayed
        that way for `stable_ms` - it goes listening -> thinking again within
        ~100ms when it has more to say (greeting, then the machine turn).

        Unread agent turns also block it, so a caller never talks past something
        it has not read. A test that is NOT holding a conversation must pass
        drain=True: VERIFIED 2026-09-28, TRN-10 never read the greeting, settled
        for 2 x 60s, and the agent closed the call for silence meanwhile."""
        deadline = time.monotonic() + timeout_ms / 1000
        quiet_since: float | None = None
        while time.monotonic() < deadline:
            if drain:
                self.drain()
            quiet = self.state == "listening" and self._open_streams == 0 and self._agent_turns.empty()
            if quiet:
                quiet_since = quiet_since or time.monotonic()
                if (time.monotonic() - quiet_since) * 1000 >= stable_ms:
                    return
            else:
                quiet_since = None
            await asyncio.sleep(0.1)

    # -- talking ------------------------------------------------------------

    @property
    def agent_gone(self) -> bool:
        return self.agent_left_at is not None or self.disconnected_at is not None

    async def say(self, text: str, *, intent: str | None = None, wait: bool = True) -> float:
        if wait:
            await self.settle()
        if self.agent_gone:
            raise AgentHungUp(f"cannot send {text[:40]!r}: the agent left at {self.ms(self.agent_left_at)}ms")
        try:
            await self.room.local_participant.send_text(text, topic="lk.chat")
        except Exception as exc:  # noqa: BLE001 - StreamError carries only "internal error"
            raise AgentHungUp(
                f"send_text failed ({exc}); agent left at {self.ms(self.agent_left_at)}ms, "
                f"room disconnected at {self.ms(self.disconnected_at)}ms"
            ) from exc
        at = time.monotonic()
        self.sent.append(Sent(text, at, intent))
        return at

    async def speak(self, wav: Path, *, text: str, wait: bool = True) -> tuple[float, float]:
        """Say it out loud: publish the mic on first use, then play the WAV."""
        if wait:
            await self.settle()
        if self.mic is None:
            self.mic = CallerMic()
            await self.mic.publish(self.room)
        start, end = await self.mic.play(wav)
        self.sent.append(Sent(text, start, "spoken"))
        return start, end

    # -- the conversation loop ------------------------------------------------

    def values(self, question: str, text_offer: str = "decline") -> dict[str, str]:
        chat = testbed.config()["chatFlow"]
        scale = chat["feedbackScale"]
        return {
            "serial": self.grant.caller.get("serialNumber", ""),
            "question": question,
            "phone": self.grant.caller.get("phone", ""),
            "textOffer": chat["textOfferReplies"][text_offer],
            "clarification": chat["clarificationReply"],
            "feedback": str(scale["max"]),
        }

    async def converse(
        self, question: str, *, text_offer: str = "decline", ask_as: str = "text", mode: str = "default"
    ) -> list[Step]:
        """
        Answer the agent by intent until our question has been answered.

        Stops when the agent signals the answer is complete ("anything else?"),
        says goodbye, or goes quiet for livekitSdk.answerFollowUpMs after
        answering. Every stop is recorded as a step, so a report shows WHY the
        conversation ended, not just that it did.
        """
        chat = testbed.config()["chatFlow"]
        budgets = testbed.config()["budgets"]
        complete = [p.lower() for p in self._sdk["answerCompletePhrases"]]
        values = self.values(question, text_offer)
        clarification = chat["clarificationReply"]
        faq = mode == "faq"
        single = mode == "single"
        single_clarified = 0
        if faq:
            faq_cfg = self._sdk["faqMode"]
            clarification = faq_cfg["clarificationReply"]
            values["clarification"] = clarification
            values["textOffer"] = faq_cfg["textOfferReply"]
        steps: list[Step] = []
        asked = False
        answered = False
        clarifications = 0
        spoken = self._sdk["spokenQuestion"]

        for _ in range(int(chat["maxTurns"])):
            if not asked:
                wait_ms = int(budgets["greetingMs"])
            elif not answered:
                wait_ms = int(budgets["answerMs"])
            else:
                wait_ms = int(self._sdk["answerFollowUpMs"])
            started = time.monotonic()
            turn = await self.next_agent_turn(wait_ms)
            waited = int((time.monotonic() - started) * 1000)
            if turn is None:
                steps.append(Step("silence" if answered else "timeout", "", None, waited))
                break
            if turn.idle:
                turn.intent = "idle"
                steps.append(Step("idle", turn.text, None, waited))
                continue

            matched = match_intent(turn.text)
            lowered = turn.text.lower()

            if single and asked and not turn.idle and self._is_probe_clarification(turn.text, single_clarified):
                single_clarified += 1
                turn.intent = "clarifying:probe"
                reply = self._sdk["singleMode"]["clarificationReply"]
                await self.say(reply, intent="clarifying:probe")
                steps.append(Step("clarifying:probe", turn.text, reply, waited))
                continue

            if single and asked and not turn.idle:
                # A probe is judged on the agent's first reply to it. Anything
                # the scripted caller says after that can only steer the call
                # somewhere the probe did not ask about - VERIFIED 2026-09-28:
                # a correct off-topic decline, answered "please give me the
                # full troubleshooting steps", became a gate-current procedure.
                turn.intent = "answer"
                steps.append(Step("answer", turn.text, None, waited))
                break

            if faq and asked and numerals.extract(turn.text):
                # The value has been given: that is the whole call for an FAQ.
                turn.intent = "answer"
                steps.append(Step("answer", turn.text, None, waited))
                break

            if matched is not None and matched[0] == "answerComplete":
                # chatFlow's "anything else?" intent (shared with the browser
                # suite): after the question it ends the answer; before it, it
                # is the agent inviting the question. Left to the generic path
                # below, its null reply meant "wait for more" - VERIFIED
                # 2026-09-28, the call idled until the agent hung up.
                if asked:
                    turn.intent = "answerComplete"
                    steps.append(Step("answerComplete", turn.text, None, waited))
                    break
                matched = next(((i, rep) for i, _, rep in _intents() if i == "readyForQuestion"), None)

            if asked and matched is None and any(p in lowered for p in complete):
                turn.intent = "answerComplete"
                steps.append(Step("answerComplete", turn.text, None, waited))
                break

            if matched is not None:
                intent_id, reply = matched
                turn.intent = intent_id
                if intent_id == "farewell" or reply is None:
                    steps.append(Step(intent_id, turn.text, None, waited))
                    if intent_id == "farewell":
                        break
                    continue
                is_question = "{{question}}" in reply
                if is_question and asked:
                    # The agent offering the floor again after answering is the
                    # "anything else?" shape in different words.
                    steps.append(Step("answerComplete", turn.text, None, waited))
                    break
                text = render(reply, values)
                if is_question and ask_as == "voice":
                    await self.speak(Path(testbed.ROOT / spoken["wav"]), text=question)
                else:
                    await self.say(text, intent=intent_id)
                steps.append(Step(intent_id, turn.text, text, waited))
                if is_question:
                    asked = True
                elif asked and intent_id == "stepwiseWalkthrough":
                    # A walkthrough step IS answer content; the offer to text
                    # the steps or a read-back is not, and must not shorten the
                    # wait for the real answer.
                    answered = True
                continue

            # A question back that already carries a value has ANSWERED - it is
            # offering more ("...one hundred RPM. Would you like the procedure on
            # your screen?"), not asking. Answering it as a clarification sent
            # "give me the full troubleshooting steps", the agent went quiet and
            # hung up on its idle timer - VERIFIED 2026-09-29 (cnv06). Same rule
            # as ask() below.
            if (asked and turn.text.rstrip().endswith("?") and not numerals.extract(turn.text)
                    and clarifications < int(chat["maxClarifications"])):
                clarifications += 1
                turn.intent = "clarifying:fallback"
                await self.say(clarification, intent="clarifying:fallback")
                steps.append(Step("clarifying:fallback", turn.text, clarification, waited))
                continue

            if asked:
                turn.intent = "answer"
                answered = True
                steps.append(Step("answer", turn.text, None, waited))
                if any(p in lowered for p in complete):
                    break
                continue

            turn.intent = "greeting" if not steps else "unrecognised"
            steps.append(Step(turn.intent, turn.text, None, waited))

        return steps

    def _is_probe_clarification(self, text: str, already: int) -> bool:
        """A short question back to the caller that neither answers nor refuses."""
        cfg = self._sdk["singleMode"]
        if already >= int(cfg["maxClarifications"]) or not text.rstrip().endswith("?"):
            return False
        if len(text) > int(cfg["clarifyingMaxChars"]):
            return False
        # Curly apostrophes as straight: the agent writes "can\u2019t", the lists "can't" -
        # VERIFIED 2026-09-28, a correct "I actually can\u2019t help with recipes" was
        # taken for a clarifying question, answered, and the second reply judged.
        lowered = text.lower().replace("\u2019", "'").replace("\u2018", "'")
        behaviour = self._sdk["probeBehaviour"]
        refusal = behaviour["decline"] + behaviour["dontKnow"] + behaviour["refuseUnsafe"] + behaviour["emergencyFirst"]
        return not any(p in lowered for p in refusal)

    async def ask(self, question: str) -> tuple[str, list[Step]]:
        """
        One question in the middle of a call; returns (answer text, steps).

        For the adaptive interview, where the next question depends on this
        answer. The agent's own control turns are handled by intent - phone or
        serial read-backs confirmed, a clarifying question answered with "just
        what the manual says", an offer to text declined - and the answer is
        every substantive turn until the agent hands the floor back (a question,
        or "anything else?"). Unread turns are marked read before returning, so
        the next ask() is never blocked behind them.
        """
        chat = testbed.config()["chatFlow"]
        cfg = self._sdk["interview"]
        budgets = testbed.config()["budgets"]
        complete = [p.lower() for p in self._sdk["answerCompletePhrases"]]
        steps: list[Step] = []
        answer: list[str] = []
        clarifications = 0
        # A longer quiet window than a scripted reply needs: VERIFIED 2026-09-28,
        # a question sent 1.2 s into a lull landed while the agent was starting
        # its reaction to "no thanks, don't text it" - the agent drops messages
        # sent while it speaks, so the question was never heard and the reaction
        # was judged as its answer.
        await self.settle(stable_ms=int(cfg["quietBeforeQuestionMs"]), drain=True)
        await self.say(question, intent="interview", wait=False)
        declined = False
        for _ in range(int(chat["maxTurns"])):
            wait = int(budgets["answerMs"]) if not answer else int(self._sdk["answerFollowUpMs"])
            turn = await self.next_agent_turn(wait)
            if turn is None:
                break
            if turn.idle:
                turn.intent = "idle"
                continue
            matched = match_intent(turn.text)
            intent_id = matched[0] if matched else None
            text = turn.text.strip()
            substantive = bool(numerals.extract(text)) or len(text) > 160
            if intent_id in ("readsBackPhone", "readsBackSerial"):
                turn.intent = intent_id
                await self.say(matched[1] or "Yes, that is correct.", intent=intent_id)
                steps.append(Step(intent_id, text, matched[1], 0))
                continue
            if intent_id == "farewell":
                turn.intent = intent_id
                steps.append(Step(intent_id, text, None, 0))
                break
            if intent_id == "offersToText" and not declined:
                turn.intent = "answer" if substantive else intent_id
                if substantive:
                    answer.append(text)
                await self.say(cfg["declineTextReply"], intent="offersToText")
                steps.append(Step(intent_id, text, cfg["declineTextReply"], 0))
                # Keep listening: the agent's reaction to the decline belongs to
                # THIS question, not to the next one.
                declined = True
                continue
            ends_question = text.rstrip().endswith("?")
            # A question back with no value in it is the agent diagnosing before
            # answering - acceptable behaviour for this agent - whatever its
            # length. VERIFIED 2026-09-28: a 200-character "did the engine shut
            # down completely, or is it still running?" was judged as the answer.
            if ends_question and not numerals.extract(text) and not answer and clarifications < int(chat["maxClarifications"]):
                clarifications += 1
                turn.intent = "clarifying:fallback"
                await self.say(cfg["clarificationReply"], intent="clarifying:fallback")
                steps.append(Step("clarifying:fallback", text, cfg["clarificationReply"], 0))
                continue
            turn.intent = "answer"
            answer.append(text)
            steps.append(Step("answer", text, None, 0))
            if ends_question or any(p in text.lower() for p in complete):
                break
        await self.settle(timeout_ms=20000, stable_ms=int(cfg["quietBeforeQuestionMs"]), drain=True)
        return "\n\n".join(answer), steps

    async def wrap_up(self) -> list[Step]:
        """Sign off the way a caller does, answer a rating request, wait for the goodbye."""
        chat = testbed.config()["chatFlow"]
        budget = int(testbed.config()["budgets"]["wrapUpMs"])
        steps: list[Step] = []
        try:
            await self.say(chat["closingStatement"], intent="closing")
        except AgentHungUp as exc:
            steps.append(Step("agentHungUp", str(exc), None, 0))
            return steps
        for _ in range(4):
            turn = await self.next_agent_turn(budget)
            if turn is None:
                steps.append(Step("silence", "", None, budget))
                break
            matched = match_intent(turn.text)
            intent_id = matched[0] if matched else "unrecognised"
            turn.intent = intent_id
            if intent_id == "asksForFeedback":
                reply = str(chat["feedbackScale"]["max"])
                try:
                    await self.say(reply, intent=intent_id)
                except AgentHungUp as exc:
                    steps.append(Step("agentHungUp", str(exc), None, 0))
                    break
                steps.append(Step(intent_id, turn.text, reply, 0))
                continue
            steps.append(Step(intent_id, turn.text, None, 0))
            if intent_id == "farewell":
                break
        return steps

    # -- views --------------------------------------------------------------

    def agent_segments(self, include_idle: bool = False) -> list[Segment]:
        return [s for s in self.segments if s.speaker == "agent" and s.text and (include_idle or not s.idle)]

    def caller_transcriptions(self) -> list[Segment]:
        return [s for s in self.segments if s.speaker == "caller" and s.text]

    def to_transcript(self, scenario: dict[str, Any]) -> Transcript:
        """Into the judge's schema, interleaved by time, so the oracle scores an
        SDK call exactly the way it scores a browser one."""
        events: list[tuple[float, Turn]] = []
        for s in self.agent_segments(include_idle=True):
            events.append(
                (s.closed, Turn("agent", s.text, int((s.closed - s.opened) * 1000), s.intent, s.idle))
            )
        for m in self.sent:
            events.append((m.at, Turn("caller", m.text, None, m.intent)))
        events.sort(key=lambda e: e[0])
        kb_id = scenario.get("kbId") or ""
        return Transcript(
            scenario_id=scenario.get("id", "adhoc"),
            kb_id=kb_id,
            serial=self.grant.caller.get("serialNumber", ""),
            controller=testbed.kb_by_id(kb_id).get("controller") if kb_id else None,
            question=scenario.get("question", ""),
            turns=[t for _, t in events],
            room=self.grant.room,
            source="sdk",
        )
