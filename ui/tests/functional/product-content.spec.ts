import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';

/**
 * Functional: the rendered page agrees with the payload it was built from.
 * Using the API as the oracle keeps these assertions honest without hardcoding
 * copy that marketing will change next week.
 */
test.describe('product content', () => {
  test('page heading matches the product name from the API', async ({ page, productPage }) => {
    await productPage.open();
    const payload = (await productPage.productPayload()) as Record<string, any>;

    const name: string | undefined =
      payload?.name ?? payload?.data?.name ?? payload?.product?.name;
    test.skip(!name, 'API payload shape differs - map the name field in this test');

    await expect(page.getByText(name!, { exact: false }).first()).toBeVisible();
  });

  test('product gallery renders at least one image', async ({ productPage }) => {
    await productPage.open();
    expect(await productPage.galleryCount()).toBeGreaterThan(0);
  });

  test('image lightbox opens and closes', async ({ page, productPage }) => {
    await productPage.open();
    await sel.productPage.expandPhoto(page).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toBeHidden();
  });
});
