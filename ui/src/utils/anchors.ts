/**
 * Matching a KB fact against what the agent actually says.
 *
 * The agent is voice-first: it speaks its answers and writes them the same way,
 * so a KB fact of "400 FPM" comes back as "four hundred feet per minute" and
 * "2,500 FPM" as "twenty five hundred feet per minute". A literal substring
 * match on the numeral therefore never fires, which would make the content
 * check permanently red rather than meaningfully strict.
 *
 * So an anchor matches if EITHER the written form or the spoken form appears:
 * the number in digits or in words, and the unit in its abbreviation or spelled
 * out.
 */

const UNITS: Record<string, string[]> = {
  fpm: ['fpm', 'feet per minute', 'ft per minute', 'feet/minute'],
  psi: ['psi', 'pounds per square inch', 'pounds of pressure'],
  rpm: ['rpm', 'revolutions per minute', 'revs per minute'],
  vdc: ['vdc', 'volts dc', 'volts d c', 'volts', 'volt'],
  volts: ['volts', 'volt', 'vdc'],
  volt: ['volt', 'volts', 'vdc'],
  amps: ['amps', 'amp', 'amperes', 'amperage'],
  amp: ['amp', 'amps', 'amperes'],
  ohms: ['ohms', 'ohm'],
  ohm: ['ohm', 'ohms'],
  gallons: ['gallons', 'gallon', 'gal'],
  gallon: ['gallon', 'gallons', 'gal'],
  // "240°F" is spoken "two hundred forty degrees" - usually without the "F".
  f: ['f', '°f', 'degrees f', 'degrees fahrenheit', 'degrees', 'degree'],
  inch: ['inch', 'inches', '"'],
  inches: ['inches', 'inch', '"'],
};

const ONES = [
  'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
  'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
  'seventeen', 'eighteen', 'nineteen',
];
const TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];

/** Spellings an integer may be spoken as, e.g. 2500 -> "two thousand five hundred", "twenty five hundred". */
function spellInteger(n: number): string[] {
  if (!Number.isInteger(n) || n < 0 || n > 999_999) return [];

  const under100 = (v: number): string => {
    if (v < 20) return ONES[v]!;
    const tens = TENS[Math.floor(v / 10)]!;
    const ones = v % 10;
    return ones === 0 ? tens : `${tens} ${ONES[ones]!}`;
  };

  const under1000 = (v: number): string => {
    if (v < 100) return under100(v);
    const hundreds = `${ONES[Math.floor(v / 100)]!} hundred`;
    const rest = v % 100;
    return rest === 0 ? hundreds : `${hundreds} ${under100(rest)}`;
  };

  const forms = new Set<string>();

  if (n < 1000) {
    forms.add(under1000(n));
  } else {
    const thousands = Math.floor(n / 1000);
    const rest = n % 1000;
    const base = `${under1000(thousands)} thousand`;
    forms.add(rest === 0 ? base : `${base} ${under1000(rest)}`);

    // "twenty five hundred" for 2500 - how people actually say these.
    if (n < 10_000 && n % 100 === 0) {
      forms.add(`${under100(n / 100)} hundred`);
    }
  }

  return [...forms];
}

const escape = (s: string): string => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** Loose whitespace, so "four  hundred" and "four-hundred" both match. */
const loose = (s: string): string => escape(s).replace(/[\s-]+/g, '[\\s-]*');

/**
 * Every way the agent might write this KB fact.
 * Exported for the catalogue suite, which asserts the forms stay sane.
 */
export function anchorPatterns(anchor: string): RegExp[] {
  const trimmed = anchor.trim();
  const patterns = new Set<string>([loose(trimmed)]);

  // "240°F" and "1/16 inch" both split into a number and a unit; the degree
  // sign is dropped because the spoken form never has it.
  const measurement = /^([\d.,/]+)\s*°?\s*([A-Za-z"]+)$/.exec(trimmed);
  if (measurement) {
    const [, rawNumber, rawUnit] = measurement;
    const unit = rawUnit!.toLowerCase();
    const units = UNITS[unit] ?? [unit];
    const numeric = Number(rawNumber!.replace(/,/g, ''));

    const numberForms = new Set<string>([rawNumber!, rawNumber!.replace(/,/g, '')]);
    if (Number.isFinite(numeric)) {
      numberForms.add(String(numeric));
      for (const spelled of spellInteger(numeric)) numberForms.add(spelled);
    }

    for (const num of numberForms) {
      for (const u of units) {
        patterns.add(`${loose(num)}[\\s-]*${loose(u)}`);
      }
    }
  }

  return [...patterns].map((p) => new RegExp(p, 'i'));
}

/** Does the agent's reply cite this KB fact, written or spoken? */
export function citesAnchor(answer: string, anchor: string): boolean {
  return anchorPatterns(anchor).some((p) => p.test(answer));
}

/** The KB facts the reply cites - empty means it cited none of them. */
export function citedAnchors(answer: string, anchors: string[]): string[] {
  return anchors.filter((a) => citesAnchor(answer, a));
}
