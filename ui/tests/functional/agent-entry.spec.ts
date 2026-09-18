import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';
import { testbed, callerDetails } from '../../src/config/testbed.js';

/**
 * Functional: the voice session lifecycle as seen from the browser.
 *
 * These tests open a real session against the dev environment, so they are
 * tagged @live and kept serial - do not fan them out across workers.
 */
test.describe.configure({ mode: 'serial' });

test.describe('@live @regression agent session lifecycle', () => {
  /**
   * The gate in front of every call, as of 2026-09-18. It costs no agent
   * session, so it is the test that should go red first if the form changes -
   * rather than every live suite failing at once with "the panel never opened".
   */
  test('"Talk to me" asks who is calling before it connects', async ({ page, productPage }) => {
    await productPage.open();
    await productPage.openCallerForm();

    const form = sel.callerIntake;
    await expect(form.serial(page), 'no serial number field').toBeVisible();
    await expect(form.name(page), 'no caller name field').toBeVisible();
    await expect(form.company(page), 'no company name field').toBeVisible();
    await expect(form.phone(page), 'no phone number field').toBeVisible();
    await expect(form.startCall(page)).toBeVisible();

    // An empty form must not start a call. All four fields are required, so
    // the dialog staying open is the app refusing - and it is worth proving,
    // because a form that submitted empty would hand the agent a call with no
    // machine and no caller.
    await form.startCall(page).click();
    await expect(
      form.dialog(page),
      'the form submitted with every field empty, so a call started with no caller details',
    ).toBeVisible();

    await form.cancel(page).click();
    await expect(form.dialog(page), 'Cancel did not close the form').toBeHidden();
  });

  test('clicking "Talk to me" opens the agent panel', async ({ productPage, voiceWidget }) => {
    await productPage.open();
    await productPage.startVoiceSession(callerDetails());
    await voiceWidget.expectOpen();
    await voiceWidget.end();
  });

  test('the session opens with a live microphone, and mutes on request', async ({
    page,
    productPage,
    voiceWidget,
  }) => {
    await productPage.open();
    await productPage.startVoiceSession(callerDetails());
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
    await productPage.startVoiceSession(callerDetails());
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
