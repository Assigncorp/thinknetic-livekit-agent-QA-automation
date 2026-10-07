import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const testDataDir = path.resolve(here, '..', '..', '..', '..', 'resources', 'testdata');

function load<T>(relativePath: string): T {
  return JSON.parse(readFileSync(path.join(testDataDir, relativePath), 'utf-8')) as T;
}

export interface InvalidProductFixture {
  slug: string;
  org: string;
  expectedStatus: number;
}

export const testData = {
  invalidProducts: (): InvalidProductFixture[] =>
    load<{ invalidProducts: InvalidProductFixture[] }>('products.json').invalidProducts,
} as const;
