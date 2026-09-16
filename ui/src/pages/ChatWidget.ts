import { expect, type Page } from '@playwright/test';
import { sel } from '../selectors.js';
import { TIMEOUT } from '../constants/timeouts.js';
import { BasePage } from './BasePage.js';

/**
 * Chat mode of the support agent.
 *
 * PHASE 2 - not yet live on the dev deployment. The selectors it uses are
 * UNVERIFIED; confirm them before unskipping ui/tests/chat.
 */
export class ChatWidget extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async send(message: string): Promise<void> {
    await sel.chatWidget.input(this.page).fill(message);
    await sel.chatWidget.send(this.page).click();
  }

  /** Waits for a non-empty reply and returns how long it took, in ms. */
  async awaitReply(timeoutMs = TIMEOUT.agentReply): Promise<number> {
    const started = Date.now();
    await expect(sel.chatWidget.messages(this.page)).toContainText(/\S/, { timeout: timeoutMs });
    return Date.now() - started;
  }

  async lastReplyText(): Promise<string> {
    return (await sel.chatWidget.messages(this.page).last().innerText()).trim();
  }
}
