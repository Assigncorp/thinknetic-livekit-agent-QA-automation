import type { Page, Locator } from '@playwright/test';

/**
 * CENTRAL SELECTOR MAP
 *
 * The app under test ships no `data-testid` attributes and we are not allowed
 * to change its code, so every locator here is role/text based. That is more
 * brittle than test ids, which is exactly why they all live in this one file:
 * when the UI is restyled, this is the only file that should need editing.
 *
 * Rules (see docs/locator-strategy.md):
 *   1. getByRole + accessible name first.
 *   2. Stable text second.
 *   3. Structural CSS only as a last resort, and always commented.
 *
 * VERIFIED   - confirmed against etnyre-dev on 2026-09-16.
 * UNVERIFIED - written from expected markup; confirm on first run and fix here.
 */
export const sel = {
  productPage: {
    /** VERIFIED - opens the agent session (voice + text). */
    talkToMe: (p: Page): Locator => p.getByRole('button', { name: /talk to me/i }),
    /** VERIFIED - lightbox trigger on the hero image. */
    expandPhoto: (p: Page): Locator => p.getByRole('button', { name: /expand photo/i }),
    /** VERIFIED - gallery thumbnails render as "View <filename>" buttons. */
    galleryThumbs: (p: Page): Locator =>
      p.getByRole('button', { name: /^View .+\.(png|jpe?g|webp)$/i }),
    /** VERIFIED - header status pill, present before a session is opened. */
    assistantOnline: (p: Page): Locator => p.getByText(/assistant online/i),
    heading: (p: Page): Locator => p.getByRole('heading').first(),
  },

  /**
   * VERIFIED 2026-09-16 - the session panel. Same panel serves voice and text;
   * these are the text-mode controls.
   */
  chatWidget: {
    /** Placeholder uses a real ellipsis character, so match loosely. */
    input: (p: Page): Locator => p.getByRole('textbox', { name: /type your question/i })
      .or(p.locator('input[placeholder^="Type your question"]'))
      .first(),
    send: (p: Page): Locator => p.getByRole('button', { name: /^send$/i }),
    mute: (p: Page): Locator => p.getByRole('button', { name: /^mute$/i }),
    end: (p: Page): Locator => p.getByRole('button', { name: /^end$/i }),
    /**
     * Session state text. "Listening — go ahead" is the connected state;
     * "Connecting…" precedes it.
     */
    connecting: (p: Page): Locator => p.getByText(/connecting/i),
    listening: (p: Page): Locator => p.getByText(/listening/i),
  },

  /**
   * Voice-specific controls beyond the shared panel.
   * UNVERIFIED - phase 2. Mute/End above are the verified ones.
   */
  voiceWidget: {
    panel: (p: Page): Locator => p.getByRole('dialog'),
    statusText: (p: Page): Locator => p.getByText(/connecting|listening|speaking/i),
  },
} as const;
