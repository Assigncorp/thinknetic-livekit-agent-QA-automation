"""
One call to the deployed agent, driven over the LiveKit SDK.

We mint our own token with the project's API key and put the agent dispatch in
its room config, so the agent joins the moment we do. On the wire:

  * the agent is a kind=AGENT participant;
  * each agent turn is one text stream on `lk.transcription`;
  * `lk.agent.state` walks listening -> thinking -> speaking -> listening, and a
    message sent while the agent is not listening is dropped;
  * the caller types on `lk.chat`.
"""

from __future__ import annotations

import asyncio
import json
import os
import ssl
import uuid
from datetime import timedelta
from typing import Any

AGENT_KIND = 4

HOLDING_PHRASES = (
    "let me check",
    "let me look",
    "let me pull",
    "let me find",
    "one moment",
    "just a moment",
    "give me a moment",
    "give me a second",
    "hold on",
    "bear with me",
)


def is_holding(text: str) -> bool:
    """A short 'let me check' turn is the agent still looking, not the answer."""
    low = text.lower()
    return len(low) <= 60 and any(p in low for p in HOLDING_PHRASES)


def missing_credentials() -> list[str]:
    return [n for n in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET") if not os.getenv(n)]


def agent_token(product: dict[str, str], caller: dict[str, str], room: str | None = None) -> tuple[str, str]:
    """A caller token that dispatches the agent into a fresh room, carrying the
    same metadata the product backend's own session endpoint puts there."""
    from livekit import api

    room = room or f"qa-kb-{uuid.uuid4().hex[:8]}"
    metadata = json.dumps(
        {
            **product,
            "product_serial_number": caller["serial"],
            "remote_participant_name": caller["name"],
            "remote_participant_company": caller["company"],
            "remote_participant_phone": caller["phone"],
        }
    )
    token = (
        api.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
        .with_identity(f"qa-caller-{uuid.uuid4().hex[:8]}")
        .with_name(caller["name"])
        .with_ttl(timedelta(minutes=15))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(
            api.RoomConfiguration(
                metadata=metadata,
                agents=[api.RoomAgentDispatch(agent_name=os.environ["AGENT_NAME"], metadata=metadata)],
            )
        )
        .to_jwt()
    )
    return room, token


def _use_certifi() -> None:
    try:
        import certifi

        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())  # noqa: SLF001
    except ImportError:  # pragma: no cover
        pass


class AgentNeverJoined(AssertionError):
    pass


class Call:
    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token
        self.room: Any = None
        self.room_sid = ""  # LiveKit's room ID (RM_...), the reference to look the call up by
        self.agent_identity: str | None = None
        self.agent_state: str | None = None
        # Every turn, in order: {"role": "agent"|"caller", "text", "atMs", "openedMs", "tag"}.
        # Times are ms since connect() started.
        self.events: list[dict[str, Any]] = []
        self.t0 = 0.0
        self.agent_joined_at: float | None = None
        self.agent_left_at: float | None = None
        self.room_closed_at: float | None = None
        self._closed = asyncio.Event()
        self._agent_joined = asyncio.Event()
        self._state_changed = asyncio.Event()
        self._turns: asyncio.Queue[tuple[float, str]] = asyncio.Queue()  # (opened, text)
        self.open_streams = 0
        self.last_said_at = 0.0
        self._tasks: set[asyncio.Task] = set()

    async def connect(self, agent_join_timeout_s: float) -> None:
        from livekit import rtc

        _use_certifi()
        self.room = rtc.Room()
        room = self.room

        @room.on("participant_connected")
        def _joined(p: Any) -> None:
            self._maybe_agent(p)

        @room.on("participant_disconnected")
        def _left(p: Any) -> None:
            if p.identity == self.agent_identity and self.agent_left_at is None:
                self.agent_left_at = self._now()
                self._closed.set()

        @room.on("disconnected")
        def _gone(*_: Any) -> None:
            if self.room_closed_at is None:
                self.room_closed_at = self._now()
            self._closed.set()

        @room.on("participant_attributes_changed")
        def _attrs(changed: dict[str, str], p: Any) -> None:
            if p.identity == self.agent_identity and "lk.agent.state" in changed:
                self.agent_state = changed["lk.agent.state"]
                self._state_changed.set()

        def _transcription(reader: Any, sender: str) -> None:
            task = asyncio.create_task(self._read_turn(reader, sender))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

        room.register_text_stream_handler("lk.transcription", _transcription)

        self.t0 = asyncio.get_running_loop().time()
        await room.connect(self.url, self.token)
        try:
            self.room_sid = await asyncio.wait_for(room.sid, 5)
        except Exception:  # noqa: BLE001 - the room name still identifies the call
            pass
        for p in room.remote_participants.values():
            self._maybe_agent(p)
        try:
            await asyncio.wait_for(self._agent_joined.wait(), agent_join_timeout_s)
        except asyncio.TimeoutError as exc:
            raise AgentNeverJoined(
                f"connected but no agent joined within {agent_join_timeout_s:.0f}s - "
                f"check AGENT_NAME={os.getenv('AGENT_NAME')!r} is the name the worker registers with"
            ) from exc

    def _maybe_agent(self, p: Any) -> None:
        if int(p.kind) == AGENT_KIND and self.agent_identity is None:
            self.agent_identity = p.identity
            self.agent_state = p.attributes.get("lk.agent.state")
            self.agent_joined_at = self._now()
            self._agent_joined.set()

    def _now(self) -> float:
        return asyncio.get_running_loop().time()

    def ms(self, t: float | None) -> int | None:
        return None if t is None else int((t - self.t0) * 1000)

    async def _read_turn(self, reader: Any, sender: str) -> None:
        opened = asyncio.get_running_loop().time()
        text = ""
        self.open_streams += 1
        try:
            async for chunk in reader:
                text += chunk
        except Exception:  # noqa: BLE001 - a stream cut off by hang-up
            return
        finally:
            self.open_streams -= 1
        text = text.strip()
        if not text or sender == self.room.local_participant.identity:
            return
        self.events.append({"role": "agent", "text": text, "openedMs": self.ms(opened),
                            "atMs": self.ms(self._now()), "tag": ""})
        self._log("AGENT ", text)
        await self._turns.put((opened, text))

    def _log(self, who: str, text: str) -> None:
        """Each turn as it happens, so a long call shows progress instead of looking hung."""
        short = text if len(text) <= 160 else text[:157] + "..."
        print(f"  [call {(self.ms(self._now()) or 0) / 1000:6.1f}s] {who}: {short}", flush=True)

    async def next_agent_turn(self, timeout_s: float) -> tuple[float, str]:
        """(when the turn started streaming, its text). Gives up at once - with
        TimeoutError - when the agent has left and nothing is left to read."""
        if not self._turns.empty():
            return self._turns.get_nowait()
        get = asyncio.ensure_future(self._turns.get())
        closed = asyncio.ensure_future(self._closed.wait())
        try:
            done, _ = await asyncio.wait({get, closed}, timeout=timeout_s, return_when=asyncio.FIRST_COMPLETED)
        finally:
            closed.cancel()
            if not get.done():
                get.cancel()
        if get in done:
            return get.result()
        raise asyncio.TimeoutError

    @property
    def agent_waiting(self) -> bool:
        """Nothing streaming and the agent listening: it is the caller's turn."""
        return self.open_streams == 0 and self.agent_state in (None, "listening")

    async def wait_listening(self, timeout_s: float) -> None:
        """Messages sent while the agent is thinking or speaking are dropped."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_s
        while self.agent_state not in (None, "listening"):
            self._state_changed.clear()
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise AssertionError(f"agent stuck in state {self.agent_state!r}")
            try:
                await asyncio.wait_for(self._state_changed.wait(), remaining)
            except asyncio.TimeoutError:
                pass

    async def say(self, text: str, tag: str = "") -> None:
        if self.closed:
            raise AssertionError(f"the agent left the call before the caller could say: {text!r}")
        self.last_said_at = self._now()
        self.events.append({"role": "caller", "text": text, "openedMs": self.ms(self.last_said_at),
                            "atMs": self.ms(self.last_said_at), "tag": tag})
        self._log("CALLER", text)
        await asyncio.wait_for(self.room.local_participant.send_text(text, topic="lk.chat"), 15)

    def tag_last_agent_turn(self, tag: str) -> None:
        for e in reversed(self.events):
            if e["role"] == "agent":
                e["tag"] = e["tag"] or tag
                return

    @property
    def closed(self) -> bool:
        return self._closed.is_set()

    async def wait_closed(self, timeout_s: float) -> bool:
        """True once the agent has left or the room is gone (the agent deletes
        the room right after its closing line)."""
        try:
            await asyncio.wait_for(self._closed.wait(), timeout_s)
            return True
        except asyncio.TimeoutError:
            return False

    async def hang_up(self) -> None:
        """Always safe: never leave a room open, even if it is already gone."""
        if self.room is not None and self.room_closed_at is None:
            try:
                await asyncio.wait_for(self.room.disconnect(), 10)
            except Exception:  # noqa: BLE001 - already closed by the agent
                pass
        for task in list(self._tasks):
            task.cancel()

    @property
    def transcript(self) -> list[tuple[str, str]]:
        return [(e["role"], e["text"]) for e in self.events]

    def dialogue(self) -> str:
        return "\n".join(
            f"  {e['atMs'] / 1000:6.1f}s {'AGENT ' if e['role'] == 'agent' else 'CALLER'}"
            f"{' [' + e['tag'] + ']' if e['tag'] else ''}: {e['text']}" for e in self.events)
