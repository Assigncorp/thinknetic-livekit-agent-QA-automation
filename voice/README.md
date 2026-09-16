# Voice suite (phase 3)

Not active yet. This package exists so the structure is settled before the work starts.

## Why it bypasses the browser

Driving voice through Playwright means fake audio devices, browser autoplay policy and
WebRTC internals all sit between you and the agent. With `LIVEKIT_URL` + API key/secret
you mint your own token, join the room as a participant, publish a WAV and subscribe to
the agent's track directly. Deterministic, headless, and roughly an order of magnitude
faster.

The browser suite still owns one thing the SDK cannot see: whether a real user can
actually start a session from the page. That stays in `ui/tests/functional/agent-entry.spec.ts`.

## What goes here when it is switched on

| Concern | Approach |
|---|---|
| Connection integrity | join, publish, subscribe, reconnect after a forced drop |
| Turn-taking | `webrtcvad` on the agent track - detect speech onset/offset boundaries |
| Latency | time from end-of-user-speech to first agent audio frame, per component budget |
| Content correctness | `faster-whisper` transcribes the agent track locally, then deterministic checks |
| Barge-in | publish over the agent mid-utterance, assert it yields |

## Setup when the time comes

```bash
cd voice
uv sync --extra live
# fill LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET in the repo-root .env
uv run pytest -v
```

Put reference caller audio in `voice/fixtures/` as 16 kHz mono WAV.
