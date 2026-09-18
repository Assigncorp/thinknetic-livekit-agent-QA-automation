# The agent chat flow

Observed end-to-end on `etnyre-dev` on 2026-09-16, and re-verified on 2026-09-18 after
the caller intake form landed, in text mode.

## The contract

| # | Who | What |
|---|---|---|
| 1 | caller | clicks **Talk to me** |
| 2 | app | **"Before we start"** dialog opens: Serial number, Your name, Company name, Phone number — all four required — with **Cancel** and **Start call** |
| 3 | caller | fills all four and clicks **Start call** |
| 4 | app | panel opens: `Connecting…` → `Listening — go ahead`, with a text input, Mute and End |
| 5 | agent | *"Hi, this is Jason with Etnyre Customer Support. I can help you with your Chip Spreader."* |
| 6 | agent | already has the machine: *"Hi, I have your Chip Spreader Variable Hopper pulled up here… Would you like to pick up where we left off, or is there something else I can help you with today?"* |
| 7 | caller | asks a KB question |
| 8 | agent | answers |
| 9 | caller | signs off: *"That answers it, thank you — I'm all set and that's everything I needed today."* |
| 10 | agent | closes the call |
| 11 | caller | clicks **End** |

## The caller intake form — new on 2026-09-18

**"Talk to me" no longer starts a call.** It opens a dialog titled *Before we start*
asking for four required fields, and the call begins on **Start call**:

| Field | `name` | Where the suite's value comes from |
|---|---|---|
| Serial number | `serialNumber` | the drawn test case, straight from `resources/serials/hopper-classification.xlsx` — it is what routes the agent to a knowledge base |
| Your name | `customerName` | drawn per run from `callerIntake.names` |
| Company name | `companyName` | drawn per run from `callerIntake.companies` |
| Phone number | `phone` | generated per run inside the fictional block (below) |

Every field carries a real `<label>`, so all four and both buttons resolve by
accessible name — no structural CSS anywhere in `sel.callerIntake`.

The identity is drawn rather than fixed for the same reason serials rotate: the agent
remembers callers, and a suite that always calls in as the same person from the same
company trains the deployment on somebody who does not exist. `scenarioSelection.seed`
reproduces a specific draw.

### This changed the call itself

The serial is handed over before a word is spoken, so **the agent no longer asks for a
serial and no longer reads one back**. It opens with the machine already in hand. The
old three-turn handshake — ask, read back, confirm — is gone, and with it the
assertions that timed it. What replaces them: the agent's first turn inside
`budgets.greetingMs`, and the machine confirmed inside `budgets.machineIdentifiedMs` —
which is **cumulative** from the start of the conversation, because that confirmation is
routinely the *same turn* as the greeting, and timing one turn against two budgets
measures it twice and calls it coverage.

Both numbers were re-based on 2026-09-18 and `serialAcknowledgedMs` retired with the
handshake it named. The agent's first turn now carries the whole opening — it loads that
serial's history and composes a recap of the last call — and one was measured at **26.0s**
against the old 25s gate. A budget that flips red and green at random is worse than none,
so `greetingMs` is now 45s. Still placeholders: collect baselines and reset to ~p95.

`asksForSerial` and `readsBackSerial` stay in `chatFlow.intents` anyway. If the agent
does ask, the driver answers instead of hanging — and the chat suite records a `defect`
annotation saying the form did not reach the agent. Recorded, not failed: one LLM turn
going its own way is not worth failing a run whose answer is good, but it showing up in
every report is a defect.

### The phone field rejects its own placeholder

The field runs a real phone validator, and the form will not submit until it passes.
Verified 2026-09-18:

| Value | Result |
|---|---|
| `555-0100` — **the field's own placeholder** | *Enter a valid phone number* |
| `555-555-0142` | *Enter a valid phone number* |
| `480-555-0142` | accepted |
| `+1 480 555 0142` | accepted |

The 555 *area* code is not usable — only the 555 *exchange* is. So the suite generates
`<real area code>-555-01<nn>`, which is the block NANP reserves for fiction: it passes
the validator and cannot ring a real person. `phoneFormat` in the config carries that
guarantee and `api/tests/test_scenario_catalog.py` asserts it, because loosening the
format would quietly end it.

Suggesting a value in the placeholder that the field then refuses is a product defect,
and it is the first thing that will confuse anyone filling this form by hand.

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

### Feedback at the end of a call — the caller has to end it

**The agent does ask the caller to rate the call. It asks only when the call reaches its
natural end, and a call only gets there when the caller says so.** Verified on
`etnyre-dev` 2026-09-18:

> *"Glad I could help. Before we finish, could you let me know how your experience was
> today and rate this call from one to ten?"*

That request had never once been seen before, across every session recorded up to
2026-09-17. Those sessions ended by simply stopping — the suite got its answer and hung
up — and the agent filled the silence with its idle nudges (*"Are you still there?"*,
*"I'm still here whenever you're ready"*) until it let the caller go. The rating request
lives on the other side of a closing turn that a call ending that way never reaches.

So it was never a missing capability. It was a call that never ended.

**The caller closes the call, and only then listens.** `ChatWidget.wrapUp()` first sends
`chatFlow.closingStatement` — *"That answers it, thank you — I'm all set and that's
everything I needed today."* — which hands the agent its closing turn, and the request
comes back in it. `asksForFeedback` catches it on `rate this call`; the rest of that
intent's phrases are still guesses and still cost nothing when they do not match.

**A rating is never volunteered.** The sign-off is a sign-off: it carries no score, and
the catalogue suite fails if a number or the word "rate" ever appears in it. A caller who
rates a call unprompted is not realistic, and it would turn a run green whether or not
the agent ever asked — which is precisely the thing this is here to measure. After
sending it, `wrapUp()` listens for up to four more turns (`budgets.wrapUpMs` each) and
answers `asksForFeedback` if it fires.

When it does not fire, the test **fails** (`assertions.requireFeedbackRequest`). That is
now a regression gate on a behaviour the deployment demonstrably has, rather than a
standing bug report. The assertion deliberately runs *after* the call is torn down, so a
failing run still leaves a cleanly closed session, a full transcript and the
`call closure` attachment.

Told the caller is done, the agent may say goodbye and end the session itself. That is
a call ending normally, so `wrapUp()` records a `sessionEnded` step and stops rather
than failing a run whose answer has already been verified.

### Waiting for the agent to close the call

Once the rating is sent, the suite waits for the agent to close — it should not be left
hanging in the air — verifies that closing turn, and only then ends the session. Verified
2026-09-18 on both text-offer paths:

> *"Thank you so much for calling Etnyre. Take care, and have a great one"* (4.8s, 5.4s)

`wrapUp()` takes `stopAfterIntent: 'farewell'`, so it stops the moment that lands instead
of sitting out the rest of its budget. `assertions.requireClosingStatement` then checks a
closing turn exists and is long enough to be a real sign-off rather than a fragment.

**That turn is easy to lose.** The agent hangs up in the same breath as saying it, and the
app removes the transcript from the DOM when a call ends — so the read that would confirm
the turn throws, and the turn is discarded even though it was seen. A run failed exactly
that way, reporting *"the agent went quiet on the rating"* about a call the agent had
closed politely. `wrapUp()` now recovers trailing turns from the cached transcript when a
live read fails.

Worth being precise about the cause, because the obvious explanation was wrong: it was
**not** a budget timeout. Both closing turns land inside 15s and `budgets.wrapUpMs` was 20s
at the time. The budget was raised to 45s for headroom, but the hang-up race is what broke
it.

The verdicts for both this and the rating fire *after* the call is torn down, matching
`requireFeedbackRequest`: the waiting, reading and capture all happen while the call is
live, and only the judgement is deferred, so a failure still leaves a cleanly closed
session and a complete report.

`wrapUp()` takes a whitelist of intent ids rather than matching everything, because the
agent's closing turn is often *"anything else I can help with?"* — which matches
`readyForQuestion` and would otherwise re-ask a question already answered.

**Sample size: four calls**, all on 2026-09-18 and across four knowledge bases. Every one
reached the request — but the fourth one nearly went unrecorded, and that is the more
useful finding:

> *"Glad we could get that sorted out. Before you go, could you let me know how your
> experience was today, on a scale from one to ten?"*

That did not match. `scale of` does not catch *"scale from"*, and `rate your experience`
does not catch *"how your experience was"*. The suite withheld a rating the agent had
asked for, and then reported the request as missing — a false defect, which is the worst
kind of test failure because it reads like a real one.

The phrases now come from what the four calls have **in common** — `how your experience
was`, `one to ten`, `on a scale` — rather than from whichever one was observed most
recently. The lesson generalises: this agent rephrases itself every call, so any match
list built from a single transcript will eventually report a behaviour as absent when it
is merely worded differently.

If the request ever turns out to be conditional — on the KB, on session history, on how
the call went — this section is the first thing to revisit.

## Six behaviours that shape the test design

### 1. The agent remembers previous sessions, per serial

After confirming `K7170` it said:

> *"Last time, you asked me to walk you through the operation sequence for the computer
> software, and I provided the full steps verbally after confirming your serial number.
> Would you like to carry on from where we left off?"*

Still true with the intake form, just earlier — the memory now lands in the agent's
opening turn, before the caller has said anything. Verified 2026-09-18 on `K7294`:

> *"Hi, I have your Chip Spreader Variable Hopper pulled up here. Last time, you reached
> out but hadn't specified exactly what you needed help with… Would you like to pick up
> where we left off, or is there something else I can help you with today?"*

So the agent's opening is **not deterministic** — it depends on what previous
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

- the intake form opens, carries all four required fields, and refuses to submit empty
- the form is accepted and the panel opens and reaches `Listening`
- the agent greets, inside `budgets.greetingMs`
- the agent confirms it has the machine from the form's serial, inside
  `budgets.machineIdentifiedMs` (cumulative from the conversation starting)
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

Three intents carry that load: `offersToText` answers the offer to SMS the steps,
`stepwiseWalkthrough` answers *"let me know when you've done that"* with *"Done. What is
the next step?"*, and `clarifying` handles the diagnostic questions in between.
`converse()` accumulates every turn the agent takes after the question into `fullAnswer`,
and the content check runs against all of it rather than any single turn — because no
single turn contains the answer.

`chatFlow.maxTurns` bounds the walk, so a procedure that never reaches the facts fails
rather than running forever.

### "Shall I text you the steps?" — both answers are tested

A real caller answers that either way, so `offersToText` has no fixed reply. Its reply is
`{{textOffer}}`, and the full positive workflow runs **once per answer** from
`chatFlow.textOfferReplies`:

| | What the caller says | What it buys |
|---|---|---|
| `decline` | *"Please don't text it. Give me the full steps here in this chat instead."* | the procedure stays in the chat, one step at a time — the only path on which the manual's numbers ever reach the transcript, so content checking depends on it |
| `accept` | *"Yes, that would be helpful — please send it to `{{phone}}`."* | the number the intake form collects is actually used; nothing else exercises it |

The accept reply hands the number over unprompted, which also answers the older *"what's
the best number to text that to?"* shape of the offer in the same turn instead of looping
back into the same intent.

The anchor check is **skipped on the accept path**. With the steps going to a phone there
is nothing in the transcript to find, and leaving it on would fail a call with "the agent
did not cite the manual" when the suite is what asked it not to.

#### The accept path cannot actually receive a text

Verified 2026-09-18. The agent reads the number back digit by digit, tries it, and comes
back with:

> *"It looks like that number can't receive texts — it's likely a landline. I'll walk you
> through the steps verbally, one at a time."*

The `555-01xx` fictional block is not textable, and the only alternative is texting a real
person, so **this path does not and cannot prove an SMS arrives.** What it does prove is
the whole journey up to and including the fallback — which is exactly what a real caller
on a landline gets, and worth having a test for.

That read-back is also why `readsBackPhone` exists. Without it the turn *"I have seven two
zero, five five five, zero one nine eight. Is that correct?"* falls through to the
ends-in-a-question-mark fallback and gets answered with `clarificationReply`, which talks
about troubleshooting steps and has nothing to do with a phone number. It only ever
appeared to work because that reply happens to open with *"Yes, that is right"*.

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
