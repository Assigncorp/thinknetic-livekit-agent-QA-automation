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
 * VERIFIED   - confirmed present on etnyre-dev as of 2026-09-16.
 * UNVERIFIED - written from expected markup; confirm on first run and fix here.
 */
export const sel = {
  productPage: {
    /** VERIFIED - opens the voice agent. */
    talkToMe: (p: Page): Locator => p.getByRole('button', { name: /talk to me/i }),
    /** VERIFIED - lightbox trigger on the hero image. */
    expandPhoto: (p: Page): Locator => p.getByRole('button', { name: /expand photo/i }),
    /** VERIFIED - gallery thumbnails render as "View <filename>" buttons. */
    galleryThumbs: (p: Page): Locator => p.getByRole('button', { name: /^View .+\.(png|jpe?g|webp)$/i }),
    heading: (p: Page): Locator => p.getByRole('heading').first(),
    logo: (p: Page): Locator => p.getByRole('img', { name: /etnyre/i }).first(),
  },

  voiceWidget: {
    /** UNVERIFIED - confirm the real accessible names on first run. */
    panel: (p: Page): Locator => p.getByRole('dialog'),
    endCall: (p: Page): Locator => p.getByRole('button', { name: /end|hang ?up|stop|close/i }),
    muteToggle: (p: Page): Locator => p.getByRole('button', { name: /mute|unmute|microphone/i }),
    statusText: (p: Page): Locator => p.getByText(/connecting|connected|listening|speaking/i),
  },

  chatWidget: {
    /** UNVERIFIED - fill in once chat mode is enabled on dev. */
    input: (p: Page): Locator => p.getByRole('textbox'),
    send: (p: Page): Locator => p.getByRole('button', { name: /send/i }),
    messages: (p: Page): Locator => p.getByRole('log'),
  },
} as const;
