import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';
import { testbed } from '../../src/config/testbed.js';

/**
 * Functional: the voice session lifecycle as seen from the browser.
 *
 * These tests open a real session against the dev environment, so they are
 * tagged @live and kept serial - do not fan them out across workers.
 */
test.describe.configure({ mode: 'serial' });

test.describe('@live @regression agent session lifecycle', () => {
  test('clicking "Talk to me" opens the agent panel', async ({ productPage, voiceWidget }) => {
    await productPage.open();
    await productPage.startVoiceSession();
    await voiceWidget.expectOpen();
    await voiceWidget.end();
  });

  test('the session opens with a live microphone, and mutes on request', async ({
    page,
    productPage,
    voiceWidget,
  }) => {
    await productPage.open();
    await productPage.startVoiceSession();
    await voiceWidget.expectOpen();

    // Documents the behaviour every other live test has to work around: the
    // caller is on an open mic the moment the session connects, so anything
    // said in the room reaches the agent until something mutes it.
    await expect(
      sel.chatWidget.mute(page),
      'expected the session to open with the mic live (control offering "Mute")',
    ).toBeEnabled({ timeout: testbed.budgets.sessionConnectMs });

    await voiceWidget.mute();

    await expect(
      sel.chatWidget.unmute(page),
      'microphone did not mute',
    ).toBeVisible();

    await voiceWidget.end();
  });

  test('session establishes a realtime connection', async ({
    productPage,
    voiceWidget,
    socketUrls,
  }) => {
    await productPage.open();
    await productPage.startVoiceSession();
    await voiceWidget.expectOpen();

    const connectMs = await voiceWidget.waitForConnected();
    // Budget, not a guess: tighten once you have a week of baseline numbers.
    expect(connectMs, 'time to connected state').toBeLessThan(15_000);

    expect(
      socketUrls.some((u) => /livekit|wss:/i.test(u)),
      `no realtime socket opened; sockets seen: ${socketUrls.join(', ') || 'none'}`,
    ).toBeTruthy();

    await voiceWidget.end();
  });
});
