"""
The server's view of a call, through the LiveKit API.

The caller sees what the agent chooses to send. The server sees who is actually
in the room, which agent was dispatched with what metadata, and when the room
really closes - things a caller cannot observe and a real defect can hide in
(an orphaned agent still burning a worker slot after the caller hung up, a
dispatch carrying the wrong serial). Read-only apart from `create_room` /
`delete_room`, which only the auth tests use, on rooms of their own.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any


def _http_url() -> str:
    return os.environ["LIVEKIT_URL"].replace("wss://", "https://").replace("ws://", "http://")


@dataclass
class ParticipantView:
    identity: str
    kind: int
    attributes: dict[str, str]
    tracks: list[dict[str, Any]]


class Admin:
    def __init__(self) -> None:
        from livekit import api

        self._api = api
        self.lk = api.LiveKitAPI(_http_url(), os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])

    async def close(self) -> None:
        await self.lk.aclose()

    async def room_exists(self, room: str) -> bool:
        rooms = await self.lk.room.list_rooms(self._api.ListRoomsRequest(names=[room]))
        return any(r.name == room for r in rooms.rooms)

    async def participants(self, room: str) -> list[ParticipantView]:
        try:
            got = await self.lk.room.list_participants(self._api.ListParticipantsRequest(room=room))
        except Exception as exc:  # noqa: BLE001 - a closed room is an answer, not an error
            # A room that is gone answers 404 not_found; one caught while it is
            # closing answers 409 "room has already closed" - VERIFIED 2026-09-28,
            # it broke the whole conversation fixture after a fast hang-up.
            if any(k in str(exc) for k in ("not_found", "does not exist", "already closed")):
                return []
            raise
        return [
            ParticipantView(
                identity=p.identity,
                kind=int(p.kind),
                attributes=dict(p.attributes),
                tracks=[
                    {"sid": t.sid, "type": int(t.type), "source": int(t.source), "muted": bool(t.muted), "name": t.name}
                    for t in p.tracks
                ],
            )
            for p in got.participants
        ]

    async def dispatches(self, room: str) -> list[Any]:
        return list(await self.lk.agent_dispatch.list_dispatch(room))

    async def wait_until(self, predicate: Any, timeout_ms: int, poll_s: float = 1.0) -> float | None:
        """Monotonic time the async predicate first held, or None."""
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            if await predicate():
                return time.monotonic()
            await asyncio.sleep(poll_s)
        return None

    async def create_room(self, name: str) -> None:
        await self.lk.room.create_room(self._api.CreateRoomRequest(name=name, empty_timeout=30))

    async def delete_room(self, name: str) -> None:
        try:
            await self.lk.room.delete_room(self._api.DeleteRoomRequest(room=name))
        except Exception:  # noqa: BLE001 - already gone is fine
            pass

    async def dispatch(self, room: str, agent_name: str, metadata: str = "") -> None:
        await self.lk.agent_dispatch.create_dispatch(
            self._api.CreateAgentDispatchRequest(room=room, agent_name=agent_name, metadata=metadata)
        )
