# Caller audio fixtures

Reference recordings published into the LiveKit room as the synthetic caller.

Format: **16 kHz, mono, 16-bit PCM WAV**. Name them after the case they drive,
e.g. `FUNC-001-hopper-capacity.wav`, matching the IDs in
`/testdata/prompts/functional-queries.json`.

Keep them short — a 4-second clip is plenty for a turn-taking assertion and keeps
the repo light. Do not commit recordings of real customer calls.
