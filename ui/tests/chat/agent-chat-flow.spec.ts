import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';
import { testbed, resolveChatCase, anyOf, serialRoutedKbs } from '../../src/config/testbed.js';

/**
 * THE POSITIVE PATH - a real caller session in text mode.
 *
 * Verified against etnyre-dev on 2026-09-16, the agent's contract is:
 *
 *   1. caller clicks "Talk to me"           -> panel opens, "Listening - go ahead"
 *   2. agent greets and asks for the serial -> "...give me the serial number..."
 *   3. caller gives the serial              -> "Let me read that back: K-7-1-7-0. Is that right?"
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

const greetingAsksForSerial = anyOf(testbed.chatFlow.greetingAsksForSerial);
const readBack = anyOf(testbed.chatFlow.readBackConfirmation);

test.describe('@live @chat agent chat flow', () => {
  test('full positive workflow: open, identify machine, ask, answer, end', async ({
    page,
    productPage,
    chatWidget,
  }, testInfo) => {
    const { scenario, serial, kb } = resolveChatCase();

    // Recorded on the test so a failure report says exactly which draw it was.
    testInfo.annotations.push(
      { type: 'scenario', description: `${scenario.id} (${kb.id})` },
      { type: 'serial', description: `${serial.serial} - ${serial.description}` },
      { type: 'question', description: scenario.question },
    );

    await test.step('open the product page', async () => {
      await productPage.open();
      await expect(sel.productPage.assistantOnline(page)).toBeVisible();
    });

    await test.step('start the agent session', async () => {
      await productPage.startVoiceSession();
      await chatWidget.expectOpen();
      await expect(sel.chatWidget.listening(page)).toBeVisible({
        timeout: testbed.budgets.sessionConnectMs,
      });
    });

    await test.step('agent greets and asks for a serial number', async () => {
      const ms = await chatWidget.waitForAgent(
        greetingAsksForSerial,
        testbed.budgets.greetingMs,
      );
      expect(ms, 'time to greeting').toBeLessThan(testbed.budgets.greetingMs);
    });

    await test.step(`give the serial number ${serial.serial}`, async () => {
      const before = await chatWidget.agentTurns();
      await chatWidget.send(serial.serial);

      // The agent reads the serial back digit by digit and waits for a yes.
      const ms = await chatWidget.waitForAgent(
        readBack,
        testbed.budgets.serialAcknowledgedMs,
        before,
      );
      expect(ms, 'time to serial read-back').toBeLessThan(testbed.budgets.serialAcknowledgedMs);
    });

    await test.step('confirm the read-back', async () => {
      const before = await chatWidget.agentTurns();
      await chatWidget.send(testbed.chatFlow.confirmationReply);
      const reply = await chatWidget.waitForNewAgentTurn(
        before,
        testbed.budgets.serialAcknowledgedMs,
      );
      expect(reply.length, 'agent acknowledged the confirmed serial').toBeGreaterThan(0);
    });

    await test.step(`ask a ${kb.id} question: "${scenario.question}"`, async () => {
      const before = await chatWidget.agentTurns();
      const started = Date.now();
      await chatWidget.send(scenario.question);

      const answer = await chatWidget.waitForNewAgentTurn(before, testbed.budgets.answerMs);
      const elapsed = Date.now() - started;

      expect(elapsed, 'time to answer').toBeLessThan(testbed.budgets.answerMs);

      if (testbed.assertions.requireNonEmptyReply) {
        expect(
          answer.trim().length,
          `answer was too short to be a real reply: "${answer}"`,
        ).toBeGreaterThanOrEqual(testbed.assertions.minReplyChars);
      }

      // Off by default. Turning it on trades false failures on valid
      // paraphrases for real coverage of content correctness.
      if (testbed.assertions.checkExpectedAnchors && scenario.expectAnchors.length > 0) {
        const hit = scenario.expectAnchors.some((a) =>
          answer.toLowerCase().includes(a.toLowerCase()),
        );
        expect(hit, `none of ${JSON.stringify(scenario.expectAnchors)} appeared in the answer`).toBe(
          true,
        );
      }

      // Also off by default: an RC-36 serial should not get an RC-28 answer.
      if (testbed.assertions.failOnWrongControllerFamily && kb.controller) {
        const wrong = kb.controller === 'RC28' ? /RC[- ]?36/i : /RC[- ]?28/i;
        expect(wrong.test(answer), `answer named the wrong controller family: "${answer}"`).toBe(
          false,
        );
      }
    });

    await test.step('end the session', async () => {
      await chatWidget.end();
      await expect(sel.productPage.talkToMe(page)).toBeVisible({ timeout: 15_000 });
    });
  });

  /**
   * One case per serial-routed knowledge base, so a single run touches every
   * machine family rather than whichever one the random draw happened to pick.
   */
  for (const kb of serialRoutedKbs()) {
    test(`identifies a ${kb.id} machine from its serial`, async ({ productPage, chatWidget }, testInfo) => {
      const { serial, scenario } = resolveChatCase(kb.id);
      testInfo.annotations.push(
        { type: 'serial', description: `${serial.serial} - ${serial.description}` },
        { type: 'scenario', description: scenario.id },
      );

      await productPage.open();
      await productPage.startVoiceSession();
      await chatWidget.expectOpen();

      await chatWidget.waitForAgent(greetingAsksForSerial, testbed.budgets.greetingMs);

      const before = await chatWidget.agentTurns();
      await chatWidget.send(serial.serial);
      await chatWidget.waitForAgent(readBack, testbed.budgets.serialAcknowledgedMs, before);

      const afterReadBack = await chatWidget.agentTurns();
      await chatWidget.send(testbed.chatFlow.confirmationReply);
      const accepted = await chatWidget.waitForNewAgentTurn(
        afterReadBack,
        testbed.budgets.serialAcknowledgedMs,
      );

      expect(accepted.trim().length).toBeGreaterThan(0);
      await chatWidget.end();
    });
  }
});
