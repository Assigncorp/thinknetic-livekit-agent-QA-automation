# Recorded calls

One JSON file per call, scored by `judge/tests/test_recorded_calls.py`.

Recordings exist so a bad score can be argued with. An LLM judge disagrees with
itself at the margin, so a score is only useful if the exact call that produced
it can be replayed — through a different model, a changed rubric, or a colleague
who thinks the verdict is wrong. Re-running the agent instead gets a different
conversation and settles nothing.

## Capturing one

Real calls are captured by the LiveKit SDK suite and the browser chat suite,
both into `reports/recordings/` (runtime output, gitignored):

    make livekit-grounding     # SDK calls, one recording each
    make chat                  # browser calls, same schema
    make oracle DIR=reports/recordings

A call cannot be replayed - ask the same question twice and the agent, which
remembers previous sessions per serial, answers differently - which is why every
call is recorded before it is scored. This folder keeps only the synthetic
fixtures the oracle's own tests rely on.

## Shape

```jsonc
{
  "scenarioId": "VHRS28-HOW-003",   // must exist in resources/generated/scenarios.json
  "kbId": "vhrs28",
  "serial": "K7170",
  "controller": "RC28",
  "question": "The machine will not move / won't drive",
  "room": "qa-judge-K7170-1a2b3c4d",
  "recordedAt": "2026-09-21T09:14:02+00:00",
  "turns": [
    { "speaker": "agent",  "text": "...", "elapsedMs": 4200, "intent": "readyForQuestion" },
    { "speaker": "caller", "text": "..." },
    { "speaker": "agent",  "text": "...", "idle": true }
  ]
}
```

`speaker` is the only required field on a turn. `idle` marks the agent's
unprompted "are you still there?" nudges so they are stripped before scoring —
leaving them in drags every score down for a call that was merely slow.

## Never commit a real customer call

These are fictional callers talking to a dev deployment. A recording of a real
support call does not belong in a git repository, and `callerIntake` generates
`<area>-555-01xx` numbers precisely so a run can never produce one that reaches
a real person.
