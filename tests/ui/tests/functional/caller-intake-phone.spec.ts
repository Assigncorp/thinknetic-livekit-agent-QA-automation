import { test, expect } from '../../src/fixtures/test.js';
import { sel } from '../../src/selectors.js';

/**
 * UI-PH: the "Before we start" phone field against the stated requirement.
 *
 * REQUIREMENT (product owner, 2026-09-28): a US number is accepted with or
 * without the +1 country code.
 *
 * The backend meets it - sdk/tests/test_session_contract.py proves the session
 * endpoint accepts `+14805550142`, `480-555-0142` and `(480) 555-0142`. The
 * field does not. VERIFIED 2026-09-28: it is `maxLength=10`, `inputmode=numeric`,
 * and strips every non-digit AS IT ARRIVES - which makes typing and pasting
 * behave differently, because a paste (and browser autofill) lands all at once
 * and is cut to ten characters BEFORE the separators are removed:
 *
 *                       pasted / autofilled    typed key by key
 *   4805550142          4805550142   ok        4805550142   ok
 *   480-555-0142        48055501     cut       4805550142   ok
 *   (480) 555-0142      480555       cut       4805550142   ok
 *   +1 480 555 0142     1480555      cut       1480555014   WRONG NUMBER
 *   +14805550142        148055501    cut       1480555014   WRONG NUMBER
 *
 * The typed +1 case is the worst of them: the 1 is kept as the first digit and
 * the last digit is dropped, so the field holds a different ten-digit number.
 *
 * Defect cases are `test.fail()`: green while the defect exists, RED the day it
 * is fixed, so the marker is removed deliberately rather than the defect being
 * forgotten. Nothing here submits the form - no call is started.
 */

const NUMBER = '4805550142';

type Entry = 'paste' | 'type';

const cases: { input: string; entry: Entry; defect: boolean }[] = [
  { input: '4805550142', entry: 'paste', defect: false },
  { input: '4805550142', entry: 'type', defect: false },
  { input: '480-555-0142', entry: 'type', defect: false },
  { input: '(480) 555-0142', entry: 'type', defect: false },
  { input: '480-555-0142', entry: 'paste', defect: true },
  { input: '(480) 555-0142', entry: 'paste', defect: true },
  { input: '+1 480 555 0142', entry: 'paste', defect: true },
  { input: '+14805550142', entry: 'paste', defect: true },
  { input: '+1 480 555 0142', entry: 'type', defect: true },
  { input: '+14805550142', entry: 'type', defect: true },
];

test.describe('@regression caller intake phone field', () => {
  test.beforeEach(async ({ productPage }) => {
    await productPage.open();
    await productPage.openCallerForm();
  });

  for (const { input, entry, defect } of cases) {
    const title = `${defect ? 'DEFECT: ' : ''}${entry === 'paste' ? 'pasting' : 'typing'} "${input}" keeps the number ${NUMBER}`;
    const tag = input === NUMBER ? '@positive' : '@edge';
    test(title, { tag }, async ({ page }) => {
      test.fail(defect, 'field is maxLength=10 and strips non-digits as they arrive - see header comment');
      const phone = sel.callerIntake.phone(page);
      if (entry === 'paste') await phone.fill(input);
      else await phone.pressSequentially(input);
      const kept = await phone.inputValue();
      test.info().annotations.push({ type: 'kept', description: `${entry} ${input} -> ${kept}` });
      expect(kept.replace(/\D/g, '').replace(/^1(?=\d{10}$)/, ''), `${entry} "${input}", the field kept "${kept}"`).toBe(NUMBER);
    });
  }
});
