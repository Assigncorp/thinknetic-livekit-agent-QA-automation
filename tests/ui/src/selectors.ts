import type { Locator, Page } from '@playwright/test';

/**
 * Every locator the UI test uses, in one place. The app ships no data-testid
 * attributes, so these are role/text based: when the UI is restyled this is the
 * only file that should need editing.
 */
export const sel = {
  /** The "Welcome!" dialog on page load, asking for the microphone up front. */
  welcome: {
    dialog: (p: Page): Locator => p.getByRole('dialog', { name: /^welcome/i }),
    notNow: (p: Page): Locator => p.getByRole('button', { name: /^not now$/i }),
    enableMic: (p: Page): Locator => p.getByRole('button', { name: /^enable microphone$/i }),
  },

  productPage: {
    heading: (p: Page): Locator => p.getByRole('heading').first(),
    assistantOnline: (p: Page): Locator => p.getByText(/assistant online/i),
    talkToMe: (p: Page): Locator => p.getByRole('button', { name: /talk to me/i }),
    expandPhoto: (p: Page): Locator => p.getByRole('button', { name: /expand photo/i }),
    /** Gallery thumbnails render as "View <filename>" buttons. */
    galleryThumbs: (p: Page): Locator => p.getByRole('button', { name: /^View .+\.(png|jpe?g|webp)$/i }),
  },

  /** The "Before we start" dialog "Talk to me" opens; the call starts on "Start call". */
  callerIntake: {
    dialog: (p: Page): Locator => p.getByRole('dialog', { name: /before we start/i }),
    serial: (p: Page): Locator => p.getByRole('textbox', { name: /serial number/i }),
    name: (p: Page): Locator => p.getByRole('textbox', { name: /your name/i }),
    company: (p: Page): Locator => p.getByRole('textbox', { name: /company name/i }),
    phone: (p: Page): Locator => p.getByRole('textbox', { name: /phone number/i }),
    startCall: (p: Page): Locator => p.getByRole('button', { name: /^start call$/i }),
    cancel: (p: Page): Locator => p.getByRole('button', { name: /^cancel$/i }),
  },

  /**
   * The session panel once a call is up. The mic control's accessible name is
   * the ACTION it offers: "Mute" while the mic is live, "Unmute" once muted.
   */
  callPanel: {
    /** The status pill reads Listening / Thinking / Speaking once connected. */
    live: (p: Page): Locator => p.getByText(/^(listening|thinking|speaking)/i).first(),
    mute: (p: Page): Locator => p.getByRole('button', { name: /^mute$/i }),
    unmute: (p: Page): Locator => p.getByRole('button', { name: /^unmute$/i }),
    end: (p: Page): Locator => p.getByRole('button', { name: /^end$/i }),
    /** Ending a call shows "Call ended" and this, not "Talk to me" again. */
    startAgain: (p: Page): Locator => p.getByRole('button', { name: /start again/i }),
  },
} as const;
