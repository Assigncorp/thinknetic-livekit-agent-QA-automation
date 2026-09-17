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

## The caller's side is not a script

That table is the *shape* a call usually takes, not a sequence the suite replays. The
agent is an LLM and departs from it constantly — it re-asks for a serial it dropped,
answers a question with a question, opens with a summary of a previous session, or
volunteers an idle nudge. A fixed send-order gets one turn out of step and then asserts
against the wrong message.

So `ChatWidget.converse()` runs a loop instead:

1. wait for the next agent turn to **finish streaming**
2. read it, and match it top-to-bottom against `chatFlow.intents`
3. send that intent's reply (`{{serial}}` and `{{question}}` are substituted per case)
4. repeat, until a turn arrives that is no control turn at all — that is the answer

```jsonc
{ "id": "asksForSerial", "match": ["serial number", "read it out for me"],
  "reply": "{{serial}}" }
```

Adding a behaviour the agent starts showing means adding an intent, not editing a test.
Order matters: `readsBackSerial` is listed before `asksForSerial`, because a read-back
can mention "serial number" too and would otherwise be answered with the serial again.
The catalogue suite enforces that ordering, the required intents, and that no reply
interpolates a value `converse()` does not supply.

Each turn is returned as a `ConversationStep` carrying the matched intent and how long
it took, so budgets are asserted per stage and a failure prints the whole exchange.

### Feedback at the end of a call — a confirmed defect

**No feedback, rating or score request has been observed on `etnyre-dev` in any
recorded session.** Sessions were driven through to the agent's own wrap-up
(*"I haven't heard back, so I'll let you go…"*) and through an explicit *"That is all,
thank you. Goodbye."*, and neither produced one. Ending the call just leaves
`Call ended` and a **Start again** button.

**A rating is never volunteered.** A caller who rates a call unprompted is not
realistic, and it would hide the thing worth reporting. `ChatWidget.wrapUp()` listens
for one more turn (`budgets.wrapUpMs`, deliberately short) after the answer and answers
`asksForFeedback` if it fires.

When it does not fire — which is every run so far — the test **fails**
(`assertions.requireFeedbackRequest`). That assertion deliberately runs *after* the call
is torn down, so a failing run still leaves a cleanly closed session, a full transcript
and the `call closure` attachment to attach to the bug report.

The agent does handle a rating when given one — an earlier experiment that volunteered
"I would rate this call 9 out of 10" got *"Thank you so much for calling. Take care"*
and the agent then ended the session itself. So the capability exists; it is simply
never solicited. That experiment was removed: it made every transcript look like
feedback was working.

`wrapUp()` takes a whitelist of intent ids rather than matching everything, because the
agent's closing turn is often *"anything else I can help with?"* — which matches
`readyForQuestion` and would otherwise re-ask a question already answered.

**Confirm the real wording before trusting this.** The match phrases are guesses.

## Six behaviours that shape the test design

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

### 3. A message sent mid-stream is dropped

Turns stream in token by token, so a pattern match like `/serial number/` lands while
the agent is still mid-sentence. Sending then gets the message swallowed: verified on
2026-09-17, a serial sent the instant the greeting matched was ignored and the agent
asked for it again, while the identical serial sent once the agent had gone quiet was
read back immediately.

`ChatWidget.send()` therefore calls `waitForQuiet()` first, which waits for the newest
agent turn to stop growing. This is also why the suite does **not** retry a dropped
serial: with the race removed, a serial the agent still ignores is a real defect and
should go red.

### 4. The agent answers a question with a question

The first reply to a KB question is very often not an answer at all. The agent
troubleshoots: *"Just to confirm, are you saying the machine still won't move? Yes or
no?"*, or *"Is this a new issue, or has it been happening for a while? Also, are there
any warning lights showing on the display?"*

Its phrasing is free-form, so no list of phrases keeps up. The `clarifying` intent
catches the common shapes, and behind it `converse()` falls back on the structure:
once our question is out, **a turn ending in a question mark is asking us something,
not answering us**. It gets `chatFlow.clarificationReply` — which both answers and
pushes back towards the manual, because a bare "Yes." usually just earns another
question — and the loop keeps reading, up to `maxClarifications` so a dialogue that
never lands fails instead of looping.

### 5. The session opens on a live microphone

Verified on etnyre-dev 2026-09-17. The mic control is an icon button with no text,
and its accessible name is the *action it offers*, not the current state:

| Moment | Accessible name | Disabled | Mic |
|---|---|---|---|
| right after **Talk to me** | `Unmute` | yes | connecting |
| ~1s later | `Mute` | no | **live** |
| after clicking | `Unmute` | no | muted |

So the caller is on an open mic from the moment the session connects. In text mode
that matters: anything said in the room reaches the agent and steers the very
conversation the suite is driving, and it would do so invisibly — the transcript shows
agent turns with no hint of what prompted them.

Every session therefore mutes before typing a word (`chatFlow.muteMicOnStart`), and
proves it: `ChatWidget.muteMicrophone()` waits for the control to become *enabled*
rather than clicking blind, then requires `Unmute` to appear, which is the app's own
confirmation the mic is off. `tests/functional/agent-entry.spec.ts` asserts the
behaviour directly, so if a future build ever opens muted, that test — not a
mysteriously flaky chat run — is what goes red.

### 6. The transcript has no semantic markup

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

Content is deliberately NOT asserted: `checkExpectedAnchors` ships off because the
agent never gets to the manual's facts inside a bounded call (see below).

### It is a guided walkthrough, not a Q&A bot

This is the single most important thing to understand about testing this agent, and it
was not obvious until a live call was driven all the way through. Asked a question
straight out of the manual, it does **not** reply with the manual's answer. It:

1. opens with a safety preamble for that subsystem,
2. offers to **text** the steps rather than type them — *"What's the best number to
   text that to? I'll send you the full troubleshooting steps right away."*,
3. and, if told to answer in the chat, delivers the procedure **one step at a time**:

> *"Here's the first step: Step one: shut off the machine completely. Let me know when
> you've done that, and I'll walk you through the next step."*

So the facts worth verifying — `1,200 PSI`, `P2-PIN 19`, `240 ohms` — are not in the
first reply. They are several steps into an interactive procedure, and only reachable
by playing the caller who actually performs each step.

Three intents carry that load: `offersToText` declines the SMS and asks for the steps
in the chat, `stepwiseWalkthrough` answers *"let me know when you've done that"* with
*"Done. What is the next step?"*, and `clarifying` handles the diagnostic questions in
between. `converse()` accumulates every turn the agent takes after the question into
`fullAnswer`, and the content check runs against all of it rather than any single turn
— because no single turn contains the answer.

`chatFlow.maxTurns` bounds the walk, so a procedure that never reaches the facts fails
rather than running forever.

### The agent speaks its numbers

It is a voice-first agent and writes the way it talks. Asked about a speed limit it
replies:

> *"having the machine top out at **four hundred feet per minute** in four-wheel drive
> or **six hundred feet per minute** in two-wheel drive"*

never `400 FPM`. A literal match on the KB's numeral finds nothing, so
`ui/src/utils/anchors.ts` matches either form — the number in digits or in words, the
unit abbreviated or spelled out, including how people actually say them
(`2,500 FPM` → *"twenty five hundred feet per minute"* as well as *"two thousand five
hundred"*).

### Answer-vs-knowledge-base checking

`expectAnchors` holds only what a correct answer cannot paraphrase away: pin
references (`P1-PIN 21`), part numbers (`6703670`), and measurements with units —
`1000 PSI`, `12 VDC`, `96 RPM`, `240°F`, `7 gallons`, `4.00 inches`, `1/16"`. It
deliberately holds no ordinary vocabulary. An earlier version padded each scenario
out to six terms with words like `switch` and `display`; combined with the
`.some()` match that made the assertion impossible to fail, which is worse than no
assertion because it reads as coverage.

Two later attempts to widen coverage with *vocabulary* were abandoned for the same
reason. A hand-written jargon list and then a corpus-rarity measure both kept
selecting words like `confirm`, `actual` and `position` — these KBs are plain-English
troubleshooting prose, and their only durable content is the numbers. Widening the
fact patterns instead took coverage from 94 to **118 of 221** scenarios without
weakening a single assertion. The other 103 have no checkable fact in them; their
answers need a human, and the failure message prints the KB file and line number so
one can look. With the flag on, `resolveChatCase` draws
only from those — otherwise a run could pick an unanchored scenario, skip the check
and still report green. `tools/build_resources.py` enforces the anchor shapes and
`api/tests/test_scenario_catalog.py` guards against the padding returning.

`failOnWrongControllerFamily` still ships off: did an RC-36 serial get an RC-28
answer. It targets cross-contamination between machine families, which is the defect
that would actually mislead an operator.
