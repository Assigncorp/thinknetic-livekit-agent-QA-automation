"""
`make probe-agent` - find out what the deployed agent worker is actually called.

This exists because of one failure mode, and it is the nastiest in the whole
LiveKit path: `judge.livekit.agentName` is the string explicit dispatch targets,
and a WRONG value does not error. The dispatch call succeeds, no agent ever
joins, and it surfaces thirty seconds later as a join timeout - which reads like
a slow deployment rather than a typo.

So rather than guess, ask the deployment. The probe:

  1. calls ListRooms, which proves the credentials and the URL are good before
     anything else is blamed;
  2. creates an empty room and dispatches config's agentName into it;
  3. watches for a participant and prints its identity, name and kind - that is
     the answer, whatever it turns out to be;
  4. if nothing joins, creates a second room and dispatches NOTHING, because a
     worker registered without an agent_name auto-dispatches into every new room
     and would need no name at all;
  5. deletes both rooms.

No WebRTC: this is the server API only, so it runs anywhere the REST endpoint is
reachable and cannot fail for media reasons. It does open a real agent session on
a shared deployment, briefly, in a room of its own - the same footprint as one
`make demo`.

NOTE: it has to run somewhere that can reach the LiveKit host. The Cowork
container and its device VM both deny it by egress policy (DNS failure there,
403 on CONNECT here), so run this on the machine that owns the .env.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid

from . import testbed

WAIT_SECONDS = 30
POLL_SECONDS = 2


def _http_url() -> str:
    url = os.getenv("LIVEKIT_URL", "")
    if not url:
        sys.exit("LIVEKIT_URL is not set in .env")
    return url.replace("wss://", "https://").replace("ws://", "http://")


async def _watch(lk, api, room_name: str, label: str) -> list[str]:
    """Participants that appear in `room_name` within the window."""
    print(f"  watching {room_name} for {WAIT_SECONDS}s ({label})...")
    for _ in range(WAIT_SECONDS // POLL_SECONDS):
        await asyncio.sleep(POLL_SECONDS)
        got = await lk.room.list_participants(api.ListParticipantsRequest(room=room_name))
        joined = [p for p in got.participants]
        if joined:
            for p in joined:
                kind = getattr(p, "kind", "?")
                print(
                    f"  JOINED  identity={p.identity!r}  name={p.name!r}  "
                    f"kind={kind}  metadata={p.metadata!r}"
                )
            return [p.identity for p in joined]
    print("  nothing joined")
    return []


async def main() -> int:
    try:
        from livekit import api
    except ImportError:
        sys.exit("the livekit SDK is not installed - run: cd tests/judge && uv sync --extra live")

    cfg = testbed.judge_config()["livekit"]
    agent_name = cfg["agentName"]
    lk = api.LiveKitAPI(
        _http_url(), os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"]
    )
    created: list[str] = []
    found: list[str] = []

    try:
        rooms = await lk.room.list_rooms(api.ListRoomsRequest())
        print(f"credentials OK - {len(rooms.rooms)} room(s) open on this project")
        for room in rooms.rooms[:10]:
            print(f"  existing: {room.name}  participants={room.num_participants}")

        # 1. explicit dispatch, by the configured name
        explicit = f"qa-probe-explicit-{uuid.uuid4().hex[:8]}"
        await lk.room.create_room(api.CreateRoomRequest(name=explicit))
        created.append(explicit)
        print(f"\nexplicit dispatch of agentName={agent_name!r} into {explicit}")
        try:
            await lk.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(room=explicit, agent_name=agent_name)
            )
            print("  dispatch accepted (this NEVER proves the name is right)")
        except Exception as exc:  # noqa: BLE001 - any failure is information
            print(f"  dispatch rejected: {type(exc).__name__}: {exc}")
        found = await _watch(lk, api, explicit, f"expecting {agent_name!r}")

        # 2. automatic dispatch - a worker with no agent_name joins every room
        if not found:
            auto = f"qa-probe-auto-{uuid.uuid4().hex[:8]}"
            await lk.room.create_room(api.CreateRoomRequest(name=auto))
            created.append(auto)
            print(f"\nno explicit dispatch - creating {auto} with NO dispatch at all")
            found = await _watch(lk, api, auto, "auto-dispatch")

        print("\n" + "=" * 72)
        if found:
            print("The worker joins. Put this in config/testbed.config.json:")
            print(f'  judge.livekit.agentName = "{agent_name}"   <- if explicit dispatch worked')
            print(f"  identities seen: {found}")
            print("If only the auto-dispatch room got a participant, the worker registers")
            print("WITHOUT an agent_name: explicit dispatch is not needed, and sdk/lkqa")
            print("should skip it rather than target a name that does not exist.")
        else:
            print("No agent joined either room. One of these, in order of likelihood:")
            print(f"  * the worker registers under a name other than {agent_name!r};")
            print("  * the worker is not running against this LiveKit project;")
            print("  * this project is not the one the dev deployment uses.")
            print("Ask whoever deploys the worker for its `agent_name` and its LiveKit URL.")
        print("=" * 72)
        return 0 if found else 1
    finally:
        for name in created:
            try:
                await lk.room.delete_room(api.DeleteRoomRequest(room=name))
                print(f"cleaned up {name}")
            except Exception as exc:  # noqa: BLE001
                print(f"could not delete {name}: {exc}")
        await lk.aclose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
