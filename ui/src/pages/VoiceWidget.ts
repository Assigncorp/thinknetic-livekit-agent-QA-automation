import { expect, type Page } from '@playwright/test';
import { sel } from '../selectors.js';

/**
 * Voice agent panel opened by "Talk to me".
 *
 * PHASE 1 SCOPE: connection lifecycle and UI state only - can the user open a
 * session, does it reach a connected state, does it tear down cleanly.
 * Audio content and turn-taking assertions live in the `voice/` package,
 * which drives LiveKit directly instead of through the browser.
 */
export class VoiceWidget {
  constructor(private readonly page: Page) {}

  async expectOpen(timeoutMs = 15_000): Promise<void> {
    await expect(sel.voiceWidget.panel(this.page)).toBeVisible({ timeout: timeoutMs });
  }

  /** Time from click to the widget reporting a connected/listening state. */
  async waitForConnected(timeoutMs = 20_000): Promise<number> {
    const started = Date.now();
    await expect(sel.voiceWidget.statusText(this.page)).toContainText(
      /connected|listening|speaking/i,
      { timeout: timeoutMs },
    );
    return Date.now() - started;
  }

  async end(): Promise<void> {
    const btn = sel.voiceWidget.endCall(this.page);
    if (await btn.isVisible().catch(() => false)) await btn.click();
  }

  /** Counts WebRTC/LiveKit signalling sockets the page opened. */
  static trackWebSockets(page: Page): string[] {
    const urls: string[] = [];
    page.on('websocket', (ws) => urls.push(ws.url()));
    return urls;
  }
}
