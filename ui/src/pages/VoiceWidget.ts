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

  async mute(): Promise<void> {
    await sel.chatWidget.mute(this.page).click();
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
