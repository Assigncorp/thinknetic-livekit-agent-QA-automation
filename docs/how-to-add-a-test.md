# How to add a test

## Decide which layer it belongs to

Ask what would have to break for the test to fail.

| If the failure would be... | It belongs in |
|---|---|
| a wrong status code, missing field, slow endpoint | `api/` |
| something a user can see or click | `ui/` |
| what the agent actually said or how fast it said it | `voice/` (phase 3) |

Push assertions as far down as they will go. An API test runs in 300ms and
fails with an unambiguous message; the browser test covering the same thing
takes 20 seconds and fails with "element not found".

## Adding a UI test

1. **Add the locator to `ui/src/selectors.ts`** - never inline it in the test.
   Use `getByRole` with an accessible name. Mark it `UNVERIFIED` until a run
   proves it.
2. **Put behaviour in a page object** (`ui/src/pages/`). Tests describe intent;
   page objects know how the DOM works.
3. **Add data to `/testdata`**, not to the test body, if it is a value someone
   might reasonably change.
4. **Write the test** in the right folder:
   - `tests/smoke/` - must pass before anything else is worth running
   - `tests/functional/` - core behaviour
   - `tests/negative/` - bad input, bad routes, fail-closed behaviour
   - `tests/chat/` - chat mode (currently skipped)
5. **Tag it** `@live` if it opens a real agent session, so it can be excluded.
6. **Use a budget from `ui/src/constants/timeouts.ts`.** A number typed directly
   into a test is a number nobody will ever find again.

```ts
import { test, expect } from '../../src/fixtures/test.js';

test('describes the behaviour, not the click sequence', async ({ productPage }) => {
  await productPage.open();
  // ...
});
```

## Adding an API test

Use `product_client`, not raw URLs. Mark it `@pytest.mark.smoke` only if a
failure makes everything downstream meaningless.

```python
@pytest.mark.live
def test_something(product_client, org_slug, product_slug):
    r = product_client.get_product(org_slug, product_slug)
    assert r.status_code == 200
```

## Rules that keep the suite trustworthy

- **Assert one thing.** A test named `test_product_page` that checks nine things
  tells you nothing when it goes red.
- **No sleeps.** Wait for a response, a state or an element. `waitForTimeout` in
  a diff is a review comment.
- **No assertions on LLM wording.** Assert that a reply arrived, that it is
  non-empty, that it came back inside budget, that a refusal happened. Never
  that it used a particular sentence.
- **Tests must be order-independent.** They run in parallel.
- **A skipped test states why**, with a condition or a reason string - never a
  bare `skip`.
