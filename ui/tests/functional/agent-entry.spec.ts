import { test, expect } from '../../src/fixtures/test.js';

/**
 * Functional: the voice session lifecycle as seen from the browser.
 *
 * These tests open a real session against the dev environment, so they are
 * tagged @live and kept serial - do not fan them out across workers.
 */
test.describe.configure({ mode: 'serial' });

test.describe('@live agent session lifecycle', () => {
  test('clicking "Talk to me" opens the agent panel', async ({ productPage, voiceWidget }) => {
    await productPage.open();
    await productPage.startVoiceSession();
    await voiceWidget.expectOpen();
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
