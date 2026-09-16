# The agent chat flow

Observed end-to-end on `etnyre-dev` on 2026-09-16, in text mode.

## The contract

| # | Who | What |
|---|---|---|
| 1 | caller | clicks **Talk to me** |
| 2 | app | panel opens: `Connecting…` → `Listening — go ahead`, with a text input, Mute and End |
| 3 | agent | *"Hi, this is Jason with Etnyre Customer Support… Could you start by giving me the serial number of your Chip Spreader?"* |
| 4 | caller | gives a serial, e.g. `K7170` |
| 5 | agent | reads it back digit by digit: *"Let me read that back: K-7-1-7-0. Is that right?"* |
| 6 | caller | confirms |
| 7 | agent | has the machine pulled up and invites the question |
| 8 | caller | asks a KB question |
| 9 | agent | answers |
| 10 | caller | clicks **End** |

Step 5 is easy to miss and will hang a naive test: the agent will not accept a
question until the serial is confirmed.

## Three behaviours that shape the test design

### 1. The agent remembers previous sessions, per serial

After confirming `K7170` it said:

> *"Last time, you asked me to walk you through the operation sequence for the computer
> software, and I provided the full steps verbally after confirming your serial number.
> Would you like to carry on from where we left off?"*

So the turn after confirmation is **not deterministic** — it depends on what previous
runs did with that serial. Two consequences, both handled in config:

- `scenarioSelection.rotateSerials` draws a different serial each run from a pool of
  ~25 per KB, so history accumulates slowly and spread thin.
- The suite asserts that *a* turn arrives, never *which* turn.

### 2. The agent injects unprompted turns

While idle it sends *"Are you still there?"* and *"I'm still here whenever you're
ready."* Any assertion based on message counts, or on "the last message", is flaky
unless those are filtered. `chatFlow.agentIdlePrompts` lists them and
`ChatWidget.agentTurns()` strips them before anything is asserted.

### 3. The transcript has no semantic markup

No roles, no test ids, hashed MUI class names. What *is* stable is the layout: the
agent's turns are left-aligned, the caller's are right-aligned and yellow. So
`ChatWidget.transcript()` runs in the page, walks the message stack and infers the
speaker from computed style.

This is the least pretty thing in the repo and it is a deliberate choice: a hashed
class name like `css-1v8ure2` changes on every build, whereas the left/right layout
contract is the design itself. If the devs ever add `data-role="agent|user"` to the
bubbles, replace the evaluate block with a locator and delete this note.

## What is asserted

Deterministic only, per `assertions` in the config:

- the panel opens and reaches `Listening`
- the greeting asks for a serial, inside `budgets.greetingMs`
- the serial is read back, inside `budgets.serialAcknowledgedMs`
- confirming it produces a new agent turn
- the KB question produces a non-empty answer inside `budgets.answerMs`
- ending returns the page to its pre-session state

Two stricter checks ship switched off: `checkExpectedAnchors` (does the answer contain
terms from the KB's own answer) and `failOnWrongControllerFamily` (did an RC-36 serial
get an RC-28 answer). The second is the higher-value one — it targets cross-contamination
between machine families, which is the defect that would actually mislead an operator.
