import { test, expect } from '../../src/fixtures/test.js';
import type { Page } from '@playwright/test';
import { sel } from '../../src/selectors.js';
import { callerDetails } from '../../src/config/testbed.js';

/**
 * NEG-SES: the call cannot start - does the page say so, or hang?
 *
 * Each case breaks one link between "Start call" and a connected room, using
 * Playwright's own interception: the session endpoint failing, being
 * rate-limited, handing back a token LiveKit cannot use, and LiveKit being
 * unreachable. None of them can reach an agent, so none costs a session.
 *
 * VERIFIED 2026-09-28: every case lands on the same state within ~3s and stays
 * there - an alert reading "Couldn't start the call. Please try again." and a
 * "Start again" button. The thing guarded against is the other outcome: a panel
 * stuck on "Connecting…" forever, which a caller reads as the product being
 * down.
 */

const FAIL_CLOSED_MS = 15_000;

const breakers: Record<string, (page: Page) => Promise<unknown>> = {
  'the session endpoint returns 500': (page) =>
    page.route(/\/assistant-session\b/, (r) =>
      r.fulfill({ status: 500, contentType: 'application/json', body: '{"statusCode":500,"message":"Internal server error"}' }),
    ),
  'the session endpoint is rate-limited (429)': (page) =>
    page.route(/\/assistant-session\b/, (r) =>
      r.fulfill({
        status: 429,
        contentType: 'application/json',
        headers: { 'retry-after': '30' },
        body: '{"statusCode":429,"message":"ThrottlerException: Too Many Requests"}',
      }),
    ),
  'the token is not a JWT': (page) =>
    page.route(/\/assistant-session\b/, (r) =>
      r.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ server_url: process.env.LIVEKIT_URL ?? 'wss://example.livekit.cloud', participant_token: 'not.a.jwt' }),
      }),
    ),
  'LiveKit is unreachable': async (page) => {
    await page.route(/livekit\.cloud/, (r) => r.abort('connectionrefused'));
    await page.routeWebSocket(/livekit\.cloud/, (ws) => ws.close({ code: 1011, reason: 'blocked by test' }));
  },
};

test.describe('@negative call start fails closed', { tag: ['@negative', '@mock'] }, () => {
  for (const [name, breakIt] of Object.entries(breakers)) {
    test(`${name}: the caller is told, and can try again`, async ({ page, productPage }) => {
      await breakIt(page);
      await productPage.open();
      await productPage.openCallerForm();

      const caller = callerDetails();
      const form = sel.callerIntake;
      await form.serial(page).fill(caller.serial);
      await form.name(page).fill(caller.name);
      await form.company(page).fill(caller.company);
      await form.phone(page).fill(caller.phone);
      await form.startCall(page).click();

      await expect(page.getByRole('alert'), 'no error was shown to the caller').toContainText(
        /couldn.t start the call/i,
        { timeout: FAIL_CLOSED_MS },
      );
      await expect(sel.productPage.startAgain(page)).toBeVisible();
      await expect(sel.chatWidget.input(page), 'a chat box is offered for a call that never connected').toBeHidden();

      // Still failed-closed a while later - not a transient flash before a hang.
      await page.waitForTimeout(5_000);
      await expect(sel.chatWidget.connecting(page)).toBeHidden();
      await expect(sel.productPage.startAgain(page)).toBeVisible();
    });
  }
});
