import { test, expect } from '@playwright/test';
import { readTranscriptFromInput } from '../../src/pages/ChatWidget.js';

/**
 * UNIT: the transcript reader against fixed markup - no site, no session.
 *
 * The app ships no test ids, so ChatWidget reads the transcript by layout. Two
 * layouts are pinned: the one this was written against, and the v0.0.19 one
 * (2026-09-28) that put an extra Box around the message list and blinded the
 * old reader - `make chat` and `make demo` failed with "the agent never said
 * anything" while the page plainly showed the greeting.
 */

const turn = (text: string, who: 'agent' | 'user') =>
  `<div class="MuiStack-root" style="display:flex;flex-direction:column;align-items:${who === 'user' ? 'flex-end' : 'flex-start'}"><div class="MuiBox-root">${text}</div></div>`;

const inputRow = `<hr/><div class="MuiStack-root"><div><input placeholder="Type your question…" aria-label="Type your question…"/></div><button aria-label="Send">Send</button></div>`;

const turns = [
  turn('Hi Wes Trimble, this is Jason with Etnyre Customer Support.', 'agent'),
  turn("I've got your Fixed Hopper Chip Spreader pulled up.", 'agent'),
  turn('What is the fan valve pressure?', 'user'),
].join('');

const layouts: Record<string, string> = {
  'pre-v0.0.19: Box > Stack(turns)': `<div class="MuiCard-root"><div class="MuiBox-root"><div class="MuiStack-root">${turns}</div></div>${inputRow}</div>`,
  'v0.0.19: Box > Box > Stack(turns), header above': `<div class="MuiCard-root"><div class="MuiStack-root"><span>Microphone muted</span><button aria-label="Copy call ID">Call ID RM_x</button></div><hr/><div class="MuiBox-root"><div class="MuiBox-root"><div class="MuiStack-root">${turns}</div></div></div>${inputRow}</div>`,
};

test.describe('@unit transcript reader', { tag: ['@positive', '@mock'] }, () => {
  for (const [name, html] of Object.entries(layouts)) {
    test(`reads every turn, with speakers, from the ${name} layout`, async ({ page }) => {
      await page.setContent(`<html><body>${html}</body></html>`);
      const got = await page.locator('input[placeholder^="Type your question"]').evaluate(readTranscriptFromInput);
      expect(got).toEqual([
        { who: 'agent', text: 'Hi Wes Trimble, this is Jason with Etnyre Customer Support.' },
        { who: 'agent', text: "I've got your Fixed Hopper Chip Spreader pulled up." },
        { who: 'user', text: 'What is the fan valve pressure?' },
      ]);
    });
  }
});
