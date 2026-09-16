import { expect, type Page } from '@playwright/test';
import { sel } from '../selectors.js';
import { testbed, anyOf } from '../config/testbed.js';
import type { TranscriptMessage } from '../types/testbed.js';
import { BasePage } from './BasePage.js';

/**
 * The agent session panel, driven in TEXT (chat) mode.
 *
 * Reading the transcript
 * ---------------------
 * The transcript carries no roles, no test ids and hashed MUI class names, so
 * there is nothing stable to target with a CSS locator. What IS stable is the
 * layout contract: the agent's turns are left-aligned, the caller's are
 * right-aligned. So the reader runs in the page, walks the message stack and
 * infers the speaker from computed style. Uglier than a `[data-role]` attribute
 * and considerably more durable than a hashed class name.
 */
export class ChatWidget extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  // ---------------------------------------------------------------- lifecycle

  async expectOpen(): Promise<void> {
    await expect(sel.chatWidget.input(this.page)).toBeVisible({
      timeout: testbed.budgets.sessionConnectMs,
    });
    await expect(sel.chatWidget.send(this.page)).toBeVisible();
    await expect(sel.chatWidget.end(this.page)).toBeVisible();
  }

  async end(): Promise<void> {
    const btn = sel.chatWidget.end(this.page);
    if (await btn.isVisible().catch(() => false)) await btn.click();
  }

  // ------------------------------------------------------------- transcript

  /** Every turn currently rendered, oldest first. */
  async transcript(): Promise<TranscriptMessage[]> {
    return this.page.evaluate(() => {
      // The message stack is the deepest element holding more than one bubble.
      const stacks = Array.from(document.querySelectorAll<HTMLElement>('.MuiStack-root')).filter(
        (el) => el.childElementCount > 1 && el.innerText.trim().length > 0,
      );
      const stack = stacks
        .filter((el) => Array.from(el.children).every((c) => (c as HTMLElement).innerText !== undefined))
        .sort((a, b) => b.childElementCount - a.childElementCount)[0];
      if (!stack) return [];

      return Array.from(stack.children)
        .map((child) => {
          const el = child as HTMLElement;
          const style = window.getComputedStyle(el);
          const rightAligned =
            style.alignItems === 'flex-end' || style.justifyContent === 'flex-end';
          return { who: rightAligned ? 'user' : 'agent', text: (el.innerText || '').trim() };
        })
        .filter((m) => m.text.length > 0) as TranscriptMessage[];
    });
  }

  /**
   * Agent turns only, with the unprompted idle nudges removed.
   *
   * The agent injects "Are you still there?" on its own while waiting, so any
   * assertion anchored on "the last message" or on a message count is flaky
   * unless those are filtered out first.
   */
  async agentTurns(): Promise<string[]> {
    const idle = anyOf(testbed.chatFlow.agentIdlePrompts);
    return (await this.transcript())
      .filter((m) => m.who === 'agent' && !idle.test(m.text))
      .map((m) => m.text);
  }

  async lastAgentTurn(): Promise<string> {
    const turns = await this.agentTurns();
    return turns.at(-1) ?? '';
  }

  // ------------------------------------------------------------------ actions

  async send(message: string): Promise<void> {
    const input = sel.chatWidget.input(this.page);
    await input.fill(message);
    await sel.chatWidget.send(this.page).click();
    // The input clearing is the app's own acknowledgement that it took the turn.
    await expect(input).toHaveValue('', { timeout: 10_000 });
  }

  /**
   * Waits for an agent turn matching `pattern` that was not already present.
   * Returns how long it took, in ms - the number the latency budget asserts on.
   */
  async waitForAgent(pattern: RegExp, timeoutMs: number, ignore: string[] = []): Promise<number> {
    const started = Date.now();
    const seen = new Set(ignore);

    await expect
      .poll(
        async () => (await this.agentTurns()).some((t) => !seen.has(t) && pattern.test(t)),
        {
          timeout: timeoutMs,
          intervals: [500, 1000, 1000, 2000],
          message: `No new agent turn matched ${pattern}. Transcript so far:\n${(
            await this.agentTurns()
          ).join('\n')}`,
        },
      )
      .toBe(true);

    return Date.now() - started;
  }

  /** Waits for any new agent turn beyond the ones already seen. */
  async waitForNewAgentTurn(alreadySeen: string[], timeoutMs: number): Promise<string> {
    const seen = new Set(alreadySeen);
    let found = '';

    await expect
      .poll(
        async () => {
          const fresh = (await this.agentTurns()).filter((t) => !seen.has(t));
          found = fresh.at(-1) ?? '';
          return found.length;
        },
        {
          timeout: timeoutMs,
          intervals: [1000, 1000, 2000, 2000],
          message: 'Agent did not produce a new turn within budget',
        },
      )
      .toBeGreaterThan(0);

    return found;
  }
}
