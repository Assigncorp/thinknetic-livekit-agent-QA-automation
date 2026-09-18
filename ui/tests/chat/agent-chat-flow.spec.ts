import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';
import {
  testbed,
  resolveChatCase,
  serialRoutedKbs,
  feedbackScore,
  callerDetails,
} from '../../src/config/testbed.js';
import type { ConversationStep, ConversationVars } from '../../src/pages/ChatWidget.js';
import { citedAnchors } from '../../src/utils/anchors.js';
import { describeSession } from '../../src/utils/session.js';

/**
 * THE POSITIVE PATH - a real caller session in text mode.
 *
 * The caller's side of the conversation is NOT a fixed script. The agent is an
 * LLM: it re-asks for a serial it dropped, answers a question with a question,
 * or opens with a summary of a previous session. So the suite waits for each
 * agent turn to finish streaming, reads it, and answers whatever was actually
 * asked - the mapping lives in `chatFlow.intents` in the config.
 *
 * The shape it normally follows:
 *
 *   1. caller clicks "Talk to me"           -> "Before we start" form opens
 *   2. caller fills in serial, name,
 *      company and phone, "Start call"      -> panel opens, "Listening - go ahead"
 *   3. agent greets                         -> "Hi, this is Jason with Etnyre..."
 *   4. agent already has the machine        -> "I have your Chip Spreader pulled up"
 *   5. caller asks a KB question            -> agent answers
 *   6. caller says that is everything       -> agent closes the call
 *   7. caller ends the session
 *
 * Steps 1-2 are new as of 2026-09-18, and they changed the call itself: the
 * serial is handed over before a word is spoken, so the agent no longer asks
 * for one and no longer reads one back. It opens with the machine already
 * pulled up.
 *
 * Everything variable about that - which serial, which question, how long each
 * step may take, what counts as a pass - is declared in config/testbed.config.json.
 * Nothing in this file needs editing to change the data.
 *
 * These tests open real sessions against a shared dev deployment, so they are
 * tagged @live and run serially.
 */

test.describe.configure({ mode: 'serial' });

/**
 * A conversation is several LLM turns long, so it needs far longer than the
 * global per-test timeout in playwright.config.ts (which is sized for page
 * interactions). Derive it from the budgets rather than hardcoding a number:
 * raise a budget in the config and this follows automatically.
 */
const CHAT_TIMEOUT_MS =
  testbed.budgets.sessionConnectMs +
  testbed.chatFlow.maxTurns * (testbed.budgets.answerMs + testbed.chatFlow.turnQuietMs);

/** The longest any single agent turn may take before the driver gives up. */
const TURN_TIMEOUT_MS = Math.max(
  testbed.budgets.greetingMs,
  testbed.budgets.machineIdentifiedMs,
  testbed.budgets.answerMs,
);

const firstStep = (steps: ConversationStep[], intent: string): ConversationStep | undefined =>
  steps.find((s) => s.intent === intent);

/**
 * Both sides of the exchange. The caller's line is printed under each agent
 * turn it answered, because a transcript of only the agent's half cannot show
 * whether the suite actually replied - and "did we really send that?" is the
 * first question anyone asks of a run like this.
 */
const describeSteps = (steps: ConversationStep[]): string =>
  steps
    .map((s) => {
      const agent = `  [${s.intent}] (${s.ms}ms) ${s.agentTurn}`;
      return s.reply === null ? agent : `${agent}\n      caller -> "${s.reply}"`;
    })
    .join('\n');

test.describe('@live @chat agent chat flow', () => {
  test.beforeEach(({}, testInfo) => {
    testInfo.setTimeout(CHAT_TIMEOUT_MS);
  });

  /**
   * The conversation, both sides, attached to EVERY run - including the ones
   * that blow up mid-call.
   *
   * Doing this inline in the test only covers the path where the call reaches
   * its end. The failures worth reading are the other ones: the agent hanging
   * up in the middle of a walkthrough throws out of `converse()`, and the run
   * then reports "the session ended" with no record of what was said to it.
   * The cached copy survives that, and the call is over by now anyway.
   */
  test.afterEach(async ({ chatWidget }, testInfo) => {
    const transcript = chatWidget.lastTranscript();
    if (transcript.length === 0) return;
    await testInfo.attach('full transcript', {
      body: transcript
        .map((m) => `${m.who === 'agent' ? 'agent ' : 'caller'}: ${m.text}`)
        .join('\n\n'),
      contentType: 'text/plain',
    });
  });

  /**
   * Both answers to "shall I text you the steps?", because they are two
   * different calls and only one of them can be content-checked.
   *
   *   decline - the agent walks the procedure in the chat, one step at a time,
   *             which is the only way the manual's numbers reach the transcript
   *   accept  - the steps go to the phone number given on the intake form.
   *             The facts leave the chat, so the anchor check is skipped here;
   *             what this path proves is that the number the form collects is
   *             actually used, which nothing else exercises.
   */
  for (const textOffer of ['decline', 'accept'] as const) {
    test(`full positive workflow, ${textOffer}s the texted steps: open, identify machine, ask, answer, end`, async ({
      page,
      productPage,
      chatWidget,
      agentSession,
    }, testInfo) => {
      const { scenario, serial, kb } = resolveChatCase();
      const caller = callerDetails(serial.serial);
      const vars: ConversationVars = {
        serial: serial.serial,
        question: scenario.question,
        clarification: testbed.chatFlow.clarificationReply,
        feedback: String(feedbackScore()),
        phone: caller.phone,
        textOffer: testbed.chatFlow.textOfferReplies[textOffer],
      };

      // Recorded on the test so a failure report says exactly which draw it was.
      testInfo.annotations.push(
        { type: 'scenario', description: `${scenario.id} (${kb.id})` },
        { type: 'serial', description: `${serial.serial} - ${serial.description}` },
        { type: 'question', description: scenario.question },
        { type: 'caller', description: `${caller.name}, ${caller.company}, ${caller.phone}` },
        { type: 'text offer', description: `would ${textOffer} the texted steps` },
        { type: 'feedback', description: `would rate the call ${vars.feedback} if asked` },
      );

      await test.step('open the product page', async () => {
        await productPage.open();
        await expect(sel.productPage.assistantOnline(page)).toBeVisible();
      });

      await test.step(
        `start the call as ${caller.name} of ${caller.company}, serial ${caller.serial}`,
        async () => {
          // "Talk to me" opens the "Before we start" form now; the call starts
          // when that form is filled in and accepted.
          await productPage.startVoiceSession(caller);
          await chatWidget.expectOpen();
          await expect(sel.chatWidget.listening(page)).toBeVisible({
            timeout: testbed.budgets.sessionConnectMs,
          });

          // The session opens with the mic live, so a room noise can answer the
          // agent instead of us. Mute before typing anything.
          if (testbed.chatFlow.muteMicOnStart) {
            await chatWidget.muteMicrophone();
            expect(
              await chatWidget.isMicrophoneMuted(),
              'microphone is still live - the agent can hear the room',
            ).toBe(true);
          }
        },
      );

      const { steps, answer, fullAnswer } = await test.step(
        `hold the conversation: serial ${serial.serial}, then "${scenario.question}"`,
        async () => chatWidget.converse(vars, { turnTimeoutMs: TURN_TIMEOUT_MS }),
      );

      testInfo.attach('conversation', { body: describeSteps(steps), contentType: 'text/plain' });

      await test.step('the agent opened with the machine already identified', () => {
        // The caller gave the serial on the form, so the agent should open with
        // the machine in hand - no asking for a serial, no reading one back.
        // VERIFIED 2026-09-18: "Hi, I have your Chip Spreader Variable Hopper
        // pulled up here."
        const greeting = steps[0];
        expect(greeting, 'the agent never said anything at all').toBeDefined();
        expect(greeting!.ms, "time to the agent's first turn").toBeLessThan(
          testbed.budgets.greetingMs,
        );

        const identifiedAt = steps.findIndex((s) => s.intent === 'readyForQuestion');
        expect(
          identifiedAt,
          `agent never confirmed it had the machine pulled up, although serial ` +
            `${caller.serial} was given on the form:\n${describeSteps(steps)}`,
        ).toBeGreaterThanOrEqual(0);

        // Cumulative, not this turn's own duration. With the serial coming from
        // the form, the agent's opening and its "I have your machine" are
        // routinely the same turn - timing that one turn against two budgets
        // would just measure it twice and call it coverage.
        const msToIdentified = steps
          .slice(0, identifiedAt + 1)
          .reduce((total, s) => total + s.ms, 0);
        expect(msToIdentified, 'time until the agent had the machine').toBeLessThan(
          testbed.budgets.machineIdentifiedMs,
        );

        // Asking for a serial the caller already typed into the form means the
        // form did not reach the agent. Recorded rather than failed: the driver
        // answers the re-ask and the call still completes, and one LLM turn
        // going its own way is not worth failing a run whose answer is good.
        // If it shows up in every report, it is a defect, not a wobble.
        const reAsked = firstStep(steps, 'asksForSerial');
        if (reAsked) {
          testInfo.annotations.push({
            type: 'defect',
            description:
              `agent asked for serial ${caller.serial} again, although the caller ` +
              `gave it on the "Before we start" form: "${reAsked.agentTurn}"`,
          });
        }
      });

      await test.step(`the answer to "${scenario.question}" holds up`, () => {
        const answerStep = firstStep(steps, 'answer');
        expect(
          answerStep,
          `the agent never produced an answer - the conversation ran out of turns:\n${describeSteps(steps)}`,
        ).toBeDefined();
        expect(answerStep!.ms, 'time to answer').toBeLessThan(testbed.budgets.answerMs);

        if (testbed.assertions.requireNonEmptyReply) {
          expect(
            answer.trim().length,
            `answer was too short to be a real reply: "${answer}"`,
          ).toBeGreaterThanOrEqual(testbed.assertions.minReplyChars);
        }

        // Does the answer actually come from this machine's knowledge base?
        // Anchors are hard facts from the KB's own answer (pin references, part
        // numbers, measurements), so a hit means the agent quoted the right
        // entry rather than producing something merely plausible. The agent is
        // voice-first and writes "four hundred feet per minute" for "400 FPM",
        // so the spoken form counts too.
        // Skipped when the caller took the SMS: the procedure then goes to the
        // phone instead of the transcript, so there is nothing here to find and
        // a failure would say "the agent did not cite the manual" about a call
        // where the suite asked it not to.
        if (
          textOffer === 'decline' &&
          testbed.assertions.checkExpectedAnchors &&
          scenario.expectAnchors.length > 0
        ) {
          // Checked against everything the agent said in reply, because it
          // walks a procedure across several turns rather than answering in one.
          const cited = citedAnchors(fullAnswer, scenario.expectAnchors);
          expect(
            cited.length,
            `answer did not cite any fact from ${scenario.id} in ${kb.id} ` +
              `(${kb.file}, line ${scenario.sourceLine}).\n` +
              `expected one of: ${JSON.stringify(scenario.expectAnchors)}\n` +
              `question: ${scenario.question}\n` +
              `what the agent said:\n${fullAnswer}`,
          ).toBeGreaterThan(0);
          testInfo.annotations.push({ type: 'cited', description: cited.join(', ') });
        }

        // Off by default: an RC-36 serial should not get an RC-28 answer.
        if (testbed.assertions.failOnWrongControllerFamily && kb.controller) {
          const wrong = kb.controller === 'RC28' ? /RC[- ]?36/i : /RC[- ]?28/i;
          expect(wrong.test(answer), `answer named the wrong controller family: "${answer}"`).toBe(
            false,
          );
        }
      });

      let askedForFeedback = false;
      let signOff: ConversationStep | undefined;

      await test.step('sign off, then rate the call only if the agent asks', async () => {
        // The caller says plainly that they are done before hanging up. A rating
        // is only ever asked for at the natural end of a call, and a caller who
        // just stops typing never gets there - the agent fills the silence with
        // its idle nudges and eventually hangs up itself. The sign-off is what
        // hands the agent its closing turn, which is the turn a feedback request
        // would live in.
        //
        // A rating is still never volunteered. A caller who rates a call
        // unprompted is not realistic, and it would turn the run green whether
        // or not the agent ever asked - which is the one thing being measured
        // here. So the suite signs off, listens, answers if asked, and records
        // what happened either way; `closingStatement` has no score in it.
        //
        // Declining a transfer is allowed here too: the agent often offers to
        // hand the caller to a human on the way out, and saying no is what lets
        // the call reach its natural close.
        const closing = await chatWidget.wrapUp(vars, {
          turnTimeoutMs: testbed.budgets.wrapUpMs,
          only: ['asksForFeedback', 'declinesTransfer'],
          maxTurns: 4,
          closing: testbed.chatFlow.closingStatement,
          stopAfterIntent: 'farewell',
        });

        const ratedAt = closing.findIndex((s) => s.intent === 'asksForFeedback');
        askedForFeedback = ratedAt >= 0;

        // Whatever the agent said once it had the score. A call should not end
        // on the caller's number hanging in the air: the agent acknowledges it
        // and closes. Read here, while the session is still up, so the check is
        // against what the agent actually said rather than an emptied panel.
        signOff = ratedAt >= 0 ? closing[ratedAt + 1] : undefined;
        if (!askedForFeedback) {
          testInfo.annotations.push({
            type: 'defect',
            description:
              'agent did not ask the caller to rate the call, even after the caller ' +
              'signed off, so no rating was given',
          });
        }

        testInfo.attach('call closure', {
          body:
            `caller signed off with: ${testbed.chatFlow.closingStatement}\n` +
            `agent asked for a rating: ${askedForFeedback ? 'yes' : 'NO  <-- defect'}\n` +
            `${describeSteps(closing) || '  (the agent said nothing after the sign-off)'}\n` +
            (askedForFeedback
              ? `caller answered with: ${vars.feedback}\n` +
                `agent closed the call: ${
                  signOff ? `yes  [${signOff.intent}] ${signOff.agentTurn}` : 'NO - it went quiet on the rating'
                }\n`
              : `rating withheld - it is only given on request\n`),
          contentType: 'text/plain',
        });

        // One last read while the panel is still up, to refresh the cached copy
        // the afterEach hook attaches. Failure is fine and expected - the agent
        // often hangs up the moment it has its rating - because the cache
        // already holds everything read up to that point.
        await chatWidget.transcript().catch(() => undefined);

        await chatWidget.end();
        // Ending a session shows "Start again", not the original "Talk to me" -
        // that only comes back on a fresh page load.
        await expect(
          sel.productPage.talkToMe(page).or(sel.productPage.startAgain(page)),
        ).toBeVisible({ timeout: 15_000 });
      });

      // Both asserted last, after the call has been torn down, so a failure here
      // still leaves a cleanly closed session and a complete report rather than
      // a live one dangling. The waiting and the reading happen while the call
      // is still up - it is only the verdict that is deferred.
      await test.step('the agent closed the call after being given a rating', () => {
        if (!testbed.assertions.requireClosingStatement) return;
        if (!askedForFeedback) return; // already reported by the step below

        expect(
          signOff,
          'the agent asked for a rating, was given one, and then said nothing at all.\n' +
            'The caller is left looking at their own score with the call still open, ' +
            'waiting to be hung up on.\n\n' +
            `${describeSession(agentSession)}`,
        ).toBeDefined();

        expect(
          signOff!.agentTurn.trim().length,
          `the agent's closing turn was too short to be a real sign-off: ` +
            `"${signOff!.agentTurn}"`,
        ).toBeGreaterThanOrEqual(testbed.assertions.minReplyChars);
      });

      await test.step('the agent asked the caller to rate the call', () => {
        if (!testbed.assertions.requireFeedbackRequest) return;

        expect(
          askedForFeedback,
          'REGRESSION: the agent ended the call without asking the caller to rate it.\n' +
            `The caller closed the call explicitly ("${testbed.chatFlow.closingStatement}"), so ` +
            'the agent had its natural closing turn and still did not ask.\n' +
            'It did ask on 2026-09-18 - "could you let me know how your experience was today ' +
            'and rate this call from one to ten?" - so this is a behaviour that worked and ' +
            'has stopped, or one that is conditional in a way nobody has pinned down yet. ' +
            'The transcript in the "call closure" attachment is the evidence either way.\n\n' +
            `${describeSession(agentSession)}\n\n` +
            'To silence it while working on something else, set REQUIRE_FEEDBACK_REQUEST=false ' +
            'in .env.',
        ).toBe(true);
      });
    });
  }

  /**
   * One case per serial-routed knowledge base, so a single run touches every
   * machine family rather than whichever one the random draw happened to pick.
   * These stop once the machine is identified - the answer itself is the
   * positive-workflow test's job.
   */
  for (const kb of serialRoutedKbs()) {
    test(`identifies a ${kb.id} machine from its serial`, async ({ chatWidget, productPage }, testInfo) => {
      const { serial, scenario } = resolveChatCase(kb.id);
      testInfo.annotations.push(
        { type: 'serial', description: `${serial.serial} - ${serial.description}` },
        { type: 'scenario', description: scenario.id },
      );

      const caller = callerDetails(serial.serial);
      testInfo.annotations.push({
        type: 'caller',
        description: `${caller.name}, ${caller.company}, ${caller.phone}`,
      });

      await productPage.open();
      await productPage.startVoiceSession(caller);
      await chatWidget.expectOpen();
      if (testbed.chatFlow.muteMicOnStart) await chatWidget.muteMicrophone();

      const { steps } = await chatWidget.converse(
        {
          serial: serial.serial,
          question: scenario.question,
          clarification: testbed.chatFlow.clarificationReply,
          feedback: String(feedbackScore()),
          phone: caller.phone,
          // Never reached: this case stops as soon as the machine is
          // identified, long before any offer to text anything.
          textOffer: testbed.chatFlow.textOfferReplies.decline,
        },
        { turnTimeoutMs: TURN_TIMEOUT_MS, stopAfterIntent: 'readyForQuestion' },
      );

      testInfo.attach('conversation', { body: describeSteps(steps), contentType: 'text/plain' });

      const accepted = firstStep(steps, 'readyForQuestion');
      expect(
        accepted,
        `agent never picked up the machine for serial ${serial.serial} (${kb.id}), which was ` +
          `given on the "Before we start" form:\n${describeSteps(steps)}`,
      ).toBeDefined();
      expect(accepted!.agentTurn.trim().length).toBeGreaterThan(0);

      await chatWidget.end();
    });
  }
});
