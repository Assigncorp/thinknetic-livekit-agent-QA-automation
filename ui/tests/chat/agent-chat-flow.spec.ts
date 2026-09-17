import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';
import { testbed, resolveChatCase, serialRoutedKbs, feedbackScore } from '../../src/config/testbed.js';
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
 *   1. caller clicks "Talk to me"           -> panel opens, "Listening - go ahead"
 *   2. agent greets and asks for the serial -> "...give me the serial number..."
 *   3. caller gives the serial              -> "K-7-1-7-0. Is that right?"
 *   4. caller confirms                      -> agent has the machine pulled up
 *   5. caller asks a KB question            -> agent answers
 *   6. caller ends the session
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
  testbed.chatFlow.maxTurns * (testbed.budgets.serialAcknowledgedMs + testbed.chatFlow.turnQuietMs);

/** The longest any single agent turn may take before the driver gives up. */
const TURN_TIMEOUT_MS = Math.max(
  testbed.budgets.greetingMs,
  testbed.budgets.serialAcknowledgedMs,
  testbed.budgets.answerMs,
);

const firstStep = (steps: ConversationStep[], intent: string): ConversationStep | undefined =>
  steps.find((s) => s.intent === intent);

const describeSteps = (steps: ConversationStep[]): string =>
  steps.map((s) => `  [${s.intent}] (${s.ms}ms) ${s.agentTurn}`).join('\n');

test.describe('@live @chat agent chat flow', () => {
  test.beforeEach(({}, testInfo) => {
    testInfo.setTimeout(CHAT_TIMEOUT_MS);
  });

  test('full positive workflow: open, identify machine, ask, answer, end', async ({
    page,
    productPage,
    chatWidget,
    agentSession,
  }, testInfo) => {
    const { scenario, serial, kb } = resolveChatCase();
    const vars: ConversationVars = {
      serial: serial.serial,
      question: scenario.question,
      clarification: testbed.chatFlow.clarificationReply,
      feedback: String(feedbackScore()),
    };

    // Recorded on the test so a failure report says exactly which draw it was.
    testInfo.annotations.push(
      { type: 'scenario', description: `${scenario.id} (${kb.id})` },
      { type: 'serial', description: `${serial.serial} - ${serial.description}` },
      { type: 'question', description: scenario.question },
      { type: 'feedback', description: `would rate the call ${vars.feedback}` },
    );

    await test.step('open the product page', async () => {
      await productPage.open();
      await expect(sel.productPage.assistantOnline(page)).toBeVisible();
    });

    await test.step('start the agent session with the microphone muted', async () => {
      await productPage.startVoiceSession();
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
    });

    const { steps, answer, fullAnswer } = await test.step(
      `hold the conversation: serial ${serial.serial}, then "${scenario.question}"`,
      async () => chatWidget.converse(vars, { turnTimeoutMs: TURN_TIMEOUT_MS }),
    );

    testInfo.attach('conversation', { body: describeSteps(steps), contentType: 'text/plain' });

    await test.step('the agent asked for a serial, read it back, and accepted it', () => {
      const greeting = firstStep(steps, 'asksForSerial');
      expect(greeting, `agent never asked for a serial:\n${describeSteps(steps)}`).toBeDefined();
      expect(greeting!.ms, 'time to greeting').toBeLessThan(testbed.budgets.greetingMs);

      const readBack = firstStep(steps, 'readsBackSerial');
      expect(
        readBack,
        `agent never read the serial back - it did not register ${serial.serial}:\n${describeSteps(steps)}`,
      ).toBeDefined();
      expect(readBack!.ms, 'time to serial read-back').toBeLessThan(
        testbed.budgets.serialAcknowledgedMs,
      );

      expect(
        firstStep(steps, 'readyForQuestion'),
        `agent never confirmed the machine was pulled up:\n${describeSteps(steps)}`,
      ).toBeDefined();
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
      if (testbed.assertions.checkExpectedAnchors && scenario.expectAnchors.length > 0) {
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

    await test.step('close the call, rating it only if the agent asks', async () => {
      // A rating is never volunteered. A caller who rates a call unprompted is
      // not realistic, and it would paper over the thing actually worth
      // reporting: that the agent does not ask. So the suite listens, answers
      // if asked, and records what happened either way.
      // Declining a transfer is allowed here too: the agent often offers to
      // hand the caller to a human on the way out, and saying no is what lets
      // the call reach its natural close - which is where a rating would be
      // asked for, if it ever were.
      const closing = await chatWidget.wrapUp(vars, {
        turnTimeoutMs: testbed.budgets.wrapUpMs,
        only: ['asksForFeedback', 'declinesTransfer'],
        maxTurns: 4,
      });

      askedForFeedback = closing.some((s) => s.intent === 'asksForFeedback');
      if (!askedForFeedback) {
        testInfo.annotations.push({
          type: 'defect',
          description: 'agent did not ask the caller to rate the call, so no rating was given',
        });
      }

      testInfo.attach('call closure', {
        body:
          `agent asked for a rating: ${askedForFeedback ? 'yes' : 'NO  <-- defect'}\n` +
          (askedForFeedback
            ? `${describeSteps(closing)}\ncaller answered with: ${vars.feedback}\n`
            : `rating withheld - it is only given on request\n`),
        contentType: 'text/plain',
      });

      await chatWidget.end();
      // Ending a session shows "Start again", not the original "Talk to me" -
      // that only comes back on a fresh page load.
      await expect(
        sel.productPage.talkToMe(page).or(sel.productPage.startAgain(page)),
      ).toBeVisible({ timeout: 15_000 });
    });

    // Asserted last, after the call has been torn down, so a failure here
    // still leaves a cleanly closed session and a complete report rather than
    // a live one dangling.
    await test.step('the agent asked the caller to rate the call', () => {
      if (!testbed.assertions.requireFeedbackRequest) return;

      expect(
        askedForFeedback,
        'DEFECT: the agent ended the call without ever asking the caller to rate it.\n' +
          'It answers a rating when one is volunteered, so the capability exists - it is ' +
          'simply never requested.\n\n' +
          `${describeSession(agentSession)}\n\n` +
          'This assertion fails on every run until the agent is fixed. To silence it while ' +
          'working on something else, set REQUIRE_FEEDBACK_REQUEST=false in .env.',
      ).toBe(true);
    });
  });

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

      await productPage.open();
      await productPage.startVoiceSession();
      await chatWidget.expectOpen();
      if (testbed.chatFlow.muteMicOnStart) await chatWidget.muteMicrophone();

      const { steps } = await chatWidget.converse(
        {
          serial: serial.serial,
          question: scenario.question,
          clarification: testbed.chatFlow.clarificationReply,
          feedback: String(feedbackScore()),
        },
        { turnTimeoutMs: TURN_TIMEOUT_MS, stopAfterIntent: 'readyForQuestion' },
      );

      testInfo.attach('conversation', { body: describeSteps(steps), contentType: 'text/plain' });

      const accepted = firstStep(steps, 'readyForQuestion');
      expect(
        accepted,
        `agent never accepted serial ${serial.serial} for ${kb.id}:\n${describeSteps(steps)}`,
      ).toBeDefined();
      expect(accepted!.agentTurn.trim().length).toBeGreaterThan(0);

      await chatWidget.end();
    });
  }
});
