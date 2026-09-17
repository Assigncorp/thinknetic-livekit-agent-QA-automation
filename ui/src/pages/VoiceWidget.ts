import { expect, type Page } from '@playwright/test';
import { sel } from '../selectors.js';
import { testbed } from '../config/testbed.js';
import { BasePage } from './BasePage.js';

/**
 * The same session panel as ChatWidget, viewed from the voice side.
 *
 * PHASE 1 SCOPE: connection lifecycle and UI state only - can a user open a
 * session, does it reach a connected state, does it tear down cleanly.
 * Audio content, turn-taking and barge-in live in the `voice/` package, which
 * drives LiveKit directly instead of through the browser.
 */
export class VoiceWidget extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async expectOpen(): Promise<void> {
    await expect(sel.chatWidget.end(this.page)).toBeVisible({
      timeout: testbed.budgets.sessionConnectMs,
    });
  }

  /** Time from open to the panel reporting a connected/listening state. */
  async waitForConnected(timeoutMs = testbed.budgets.sessionConnectMs): Promise<number> {
    const started = Date.now();
    await expect(sel.chatWidget.listening(this.page)).toBeVisible({ timeout: timeoutMs });
    return Date.now() - started;
  }

  /**
   * Mutes the caller's microphone and proves it took effect.
   *
   * A session opens with the mic LIVE. The control is disabled while
   * connecting, then reads "Mute" - it is offering to mute, so audio is
   * already going up. Clicking it blindly, as this used to, could fire before
   * the control was usable and leave the mic hot with nothing to show for it.
   *
   * The button has no text; its accessible name is the action it offers, so
   * "Unmute" appearing is the app confirming the mic is off.
   */
  async mute(): Promise<void> {
    const mute = sel.chatWidget.mute(this.page);
    await expect(
      mute,
      'the microphone control never became usable, so the mic may still be live',
    ).toBeEnabled({ timeout: testbed.budgets.sessionConnectMs });

    await mute.click();

    await expect(
      sel.chatWidget.unmute(this.page),
      'microphone did not mute - the control is still offering "Mute"',
    ).toBeVisible({ timeout: 10_000 });
  }

  async end(): Promise<void> {
    const btn = sel.chatWidget.end(this.page);
    if (await btn.isVisible().catch(() => false)) await btn.click();
  }

  /** Counts WebRTC/LiveKit signalling sockets the page opened. */
  static trackWebSockets(page: Page): string[] {
    const urls: string[] = [];
    page.on('websocket', (ws) => urls.push(ws.url()));
    return urls;
  }
}
