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
    /**
     * VERIFIED 2026-09-17 - ending a session does not bring back "Talk to
     * me"; the panel shows "Call ended" and this CTA instead, until the page
     * is reloaded.
     */
    startAgain: (p: Page): Locator => p.getByRole('button', { name: /start again/i }),
  },

  /**
   * VERIFIED 2026-09-18 - the "Before we start" dialog. "Talk to me" no longer
   * opens a call: it opens this form, and the call starts on "Start call".
   *
   * All four fields are `required` and carry real `<label>`s, so every one of
   * them resolves by accessible name with no structural CSS. The patterns are
   * narrow because "Your name" and "Company name" both contain "name".
   */
  callerIntake: {
    dialog: (p: Page): Locator => p.getByRole('dialog', { name: /before we start/i }),
    serial: (p: Page): Locator => p.getByRole('textbox', { name: /serial number/i }),
    name: (p: Page): Locator => p.getByRole('textbox', { name: /your name/i }),
    company: (p: Page): Locator => p.getByRole('textbox', { name: /company name/i }),
    phone: (p: Page): Locator => p.getByRole('textbox', { name: /phone number/i }),
    startCall: (p: Page): Locator => p.getByRole('button', { name: /^start call$/i }),
    cancel: (p: Page): Locator => p.getByRole('button', { name: /^cancel$/i }),
    /**
     * Whatever the form is complaining about. Structural, and deliberately so:
     * MUI renders field errors as helper text with no role and no accessible
     * name to hang on to. Only ever read to explain a failure, never asserted
     * on - so a class change costs a worse error message, not a red run.
     */
    fieldErrors: (p: Page): Locator => p.locator('.MuiFormHelperText-root'),
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
    /**
     * VERIFIED 2026-09-17 - the mic control is an icon button with no text, so
     * its accessible name comes from aria-label, and that label is the ACTION
     * it offers rather than the current state:
     *
     *   connecting  -> "Unmute", disabled
     *   connected   -> "Mute",   enabled   <- mic is LIVE
     *   after click -> "Unmute", enabled   <- mic is muted
     *
     * So `mute` only matches while audio is going up, and `unmute` matching is
     * the app confirming the mic is off.
     */
    mute: (p: Page): Locator => p.getByRole('button', { name: /^mute$/i }),
    unmute: (p: Page): Locator => p.getByRole('button', { name: /^unmute$/i }),
    end: (p: Page): Locator => p.getByRole('button', { name: /^end$/i }),
    /**
     * Session state text. "Listening — go ahead" is the connected state;
     * "Connecting…" precedes it.
     */
    connecting: (p: Page): Locator => p.getByText(/connecting/i),
    listening: (p: Page): Locator => p.getByText(/listening/i),
  },
} as const;
