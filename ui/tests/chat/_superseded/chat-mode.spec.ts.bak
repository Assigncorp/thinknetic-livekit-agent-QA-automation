import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';

/**
 * PLACEHOLDER - chat mode.
 *
 * Skipped until chat is enabled on the dev deployment and the widget's real
 * markup is known. When you unskip: fill in sel.chatWidget first, and keep
 * assertions deterministic (the reply arrives, it is non-empty, it lands
 * inside the latency budget) rather than asserting on wording.
 */
test.describe('chat mode', () => {
  test.skip(true, 'chat widget not yet available on the dev deployment');

  test('sends a message and receives a reply', async ({ page, productPage }) => {
    await productPage.open();
    await sel.chatWidget.input(page).fill('What is the hopper capacity?');
    await sel.chatWidget.send(page).click();
    await expect(sel.chatWidget.messages(page)).toContainText(/.+/, { timeout: 30_000 });
  });
});
