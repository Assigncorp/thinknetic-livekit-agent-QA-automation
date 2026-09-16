/**
 * Single source of truth for environment-dependent values.
 * Nothing in tests or page objects should read process.env directly.
 */
export const env = {
  baseUrl: process.env.BASE_URL ?? 'https://etnyre-dev.thinknetic.app',
  orgSlug: process.env.ORG_SLUG ?? 'e',
  productSlug: process.env.PRODUCT_SLUG ?? 'chip-spreader',
} as const;

export const routes = {
  /** Public product support page - the current system under test. */
  product: (slug: string = env.productSlug) => `/${env.orgSlug}/products/${slug}`,
} as const;

export const api = {
  /** Public product payload the SPA hydrates from. Useful as a test oracle. */
  publicProduct: (slug: string = env.productSlug) =>
    `/api/v1/public/organizations/${env.orgSlug}/products/${slug}`,
} as const;
