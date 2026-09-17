import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type {
  ChatCase,
  KnowledgeBase,
  Scenario,
  SerialEntry,
  TestbedConfig,
} from '../types/testbed.js';

const here = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.resolve(here, '..', '..', '..');

function readJson<T>(relativePath: string): T {
  const full = path.join(REPO_ROOT, relativePath);
  try {
    return JSON.parse(readFileSync(full, 'utf-8')) as T;
  } catch (err) {
    throw new Error(
      `Could not read ${relativePath}. If it is under resources/generated, run \`make resources\`. (${String(err)})`,
    );
  }
}

/** Which config file describes the product under test. One env var per product. */
export const TESTBED_CONFIG = process.env.TESTBED_CONFIG ?? 'config/testbed.config.json';

const num = (raw: string | undefined, fallback: number): number => {
  const parsed = Number(raw);
  return raw !== undefined && Number.isFinite(parsed) ? parsed : fallback;
};

const bool = (raw: string | undefined, fallback: boolean): boolean =>
  raw === undefined ? fallback : /^(1|true|yes|on)$/i.test(raw);

/**
 * The single source of truth for the product under test.
 *
 * The file itself is chosen by TESTBED_CONFIG, and the handful of knobs worth
 * changing between runs - budgets, assertion strictness, scenario selection -
 * can be overridden from `.env` without editing it. Everything structural
 * (knowledge bases, serial routing, the conversation contract) stays in the
 * file, because that genuinely differs per product.
 */
const file = readJson<TestbedConfig>(TESTBED_CONFIG);

export const testbed: TestbedConfig = {
  ...file,
  scenarioSelection: {
    ...file.scenarioSelection,
    seed: process.env.SCENARIO_SEED ? num(process.env.SCENARIO_SEED, 0) : file.scenarioSelection.seed,
    fixedScenarioId: process.env.SCENARIO_ID ?? file.scenarioSelection.fixedScenarioId,
    mode: process.env.SCENARIO_ID ? 'fixed' : file.scenarioSelection.mode,
    rotateSerials: bool(process.env.ROTATE_SERIALS, file.scenarioSelection.rotateSerials),
  },
  chatFlow: {
    ...file.chatFlow,
    muteMicOnStart: bool(process.env.MUTE_MIC_ON_START, file.chatFlow.muteMicOnStart),
    turnQuietMs: num(process.env.TURN_QUIET_MS, file.chatFlow.turnQuietMs),
    maxTurns: num(process.env.MAX_TURNS, file.chatFlow.maxTurns),
    maxClarifications: num(process.env.MAX_CLARIFICATIONS, file.chatFlow.maxClarifications),
  },
  budgets: {
    ...file.budgets,
    sessionConnectMs: num(process.env.BUDGET_SESSION_CONNECT_MS, file.budgets.sessionConnectMs),
    greetingMs: num(process.env.BUDGET_GREETING_MS, file.budgets.greetingMs),
    serialAcknowledgedMs: num(process.env.BUDGET_SERIAL_MS, file.budgets.serialAcknowledgedMs),
    answerMs: num(process.env.BUDGET_ANSWER_MS, file.budgets.answerMs),
    wrapUpMs: num(process.env.BUDGET_WRAP_UP_MS, file.budgets.wrapUpMs),
    apiResponseMs: num(process.env.BUDGET_API_MS, file.budgets.apiResponseMs),
  },
  assertions: {
    ...file.assertions,
    checkExpectedAnchors: bool(
      process.env.CHECK_EXPECTED_ANCHORS,
      file.assertions.checkExpectedAnchors,
    ),
    failOnWrongControllerFamily: bool(
      process.env.FAIL_ON_WRONG_CONTROLLER_FAMILY,
      file.assertions.failOnWrongControllerFamily,
    ),
    minReplyChars: num(process.env.MIN_REPLY_CHARS, file.assertions.minReplyChars),
    requireFeedbackRequest: bool(
      process.env.REQUIRE_FEEDBACK_REQUEST,
      file.assertions.requireFeedbackRequest,
    ),
  },
};

const serialIndex = readJson<{ serials: SerialEntry[] }>(
  `${testbed.resources.generatedDir}/serial-index.json`,
);
const scenarioPools = readJson<{ pools: Record<string, Scenario[]> }>(
  `${testbed.resources.generatedDir}/scenarios.json`,
);

export const knowledgeBases = (): KnowledgeBase[] => testbed.knowledgeBases.filter((k) => k.enabled);

export const kbById = (id: string): KnowledgeBase => {
  const kb = knowledgeBases().find((k) => k.id === id);
  if (!kb) throw new Error(`No enabled knowledge base with id "${id}" in testbed.config.json`);
  return kb;
};

/** Knowledge bases reachable by giving the agent a serial number. */
export const serialRoutedKbs = (): KnowledgeBase[] =>
  knowledgeBases().filter((k) => k.controller !== null && k.hopperType !== null);

export const scenariosFor = (kbId: string): Scenario[] => scenarioPools.pools[kbId] ?? [];
export const serialsFor = (kbId: string): SerialEntry[] =>
  serialIndex.serials.filter((s) => s.kbId === kbId);

/**
 * Deterministic-when-seeded picker.
 *
 * Default is a fresh pick per run, on purpose: the agent remembers previous
 * sessions per serial, so hammering one serial changes the agent's own
 * behaviour over time. Set scenarioSelection.seed to reproduce a failing run.
 */
function makeRng(seed: number | null): () => number {
  if (seed === null) return Math.random;
  let state = seed >>> 0 || 1;
  return () => {
    // xorshift32 - small, deterministic, good enough for picking an index.
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return ((state >>> 0) % 1_000_000) / 1_000_000;
  };
}

const pick = <T>(items: T[], rng: () => number): T => {
  if (items.length === 0) throw new Error('Cannot pick from an empty list');
  return items[Math.floor(rng() * items.length) % items.length]!;
};

/**
 * A score to give the agent if it ever asks the caller to rate the call.
 * Fresh per run, or reproducible when scenarioSelection.seed is set.
 */
export function feedbackScore(): number {
  const { min, max } = testbed.chatFlow.feedbackScale;
  const rng = makeRng(testbed.scenarioSelection.seed);
  return min + Math.floor(rng() * (max - min + 1));
}

/**
 * Resolves one runnable chat case: a scenario, and a serial that routes the
 * agent to that scenario's knowledge base.
 *
 * @param kbId  pin to a specific knowledge base; omit to pick across all
 *              serial-routed ones.
 */
export function resolveChatCase(kbId?: string): ChatCase {
  const sel = testbed.scenarioSelection;
  const rng = makeRng(sel.seed);

  if (sel.mode === 'fixed' && sel.fixedScenarioId) {
    const all = Object.values(scenarioPools.pools).flat();
    const scenario = all.find((s) => s.id === sel.fixedScenarioId);
    if (!scenario) throw new Error(`fixedScenarioId "${sel.fixedScenarioId}" not found in scenarios.json`);
    return buildCase(scenario, rng);
  }

  const candidates = kbId ? [kbById(kbId)] : serialRoutedKbs();
  const kb = pick(candidates, rng);
  const pool = scenariosFor(kb.id);
  if (pool.length === 0) {
    throw new Error(`No scenarios generated for "${kb.id}". Run \`make resources\`.`);
  }

  // Only a scenario carrying KB anchors can actually verify an answer against
  // the knowledge base. Drawing an unanchored one with content checking on
  // would skip the check silently and still report green.
  const eligible = testbed.assertions.checkExpectedAnchors
    ? pool.filter((s) => s.expectAnchors.length > 0)
    : pool;
  if (eligible.length === 0) {
    throw new Error(
      `assertions.checkExpectedAnchors is on, but no "${kb.id}" scenario carries anchors, ` +
        `so nothing could be verified. Run \`make resources\`, or switch the flag off.`,
    );
  }
  return buildCase(pick(eligible, rng), rng);
}

function buildCase(scenario: Scenario, rng: () => number): ChatCase {
  const kb = kbById(scenario.kbId);
  const pool = serialsFor(kb.id);

  if (pool.length === 0) {
    if (!kb.anchorSerial) {
      throw new Error(
        `Scenario ${scenario.id} belongs to KB "${kb.id}", which has no serials and no anchorSerial. ` +
          `General-pool scenarios cannot be reached by serial - pin a serial-routed KB instead.`,
      );
    }
    return {
      scenario,
      kb,
      serial: {
        serial: kb.anchorSerial,
        description: kb.machine,
        controller: kb.controller ?? '',
        hopperType: kb.hopperType ?? '',
        sheet: 'config:anchorSerial',
        kbId: kb.id,
      },
    };
  }

  const serial = testbed.scenarioSelection.rotateSerials
    ? pick(pool, rng)
    : (pool.find((s) => s.serial === kb.anchorSerial) ?? pool[0]!);

  return { scenario, kb, serial };
}

/** Builds a case-insensitive regex from the phrase fragments in the config. */
export const anyOf = (fragments: string[]): RegExp =>
  new RegExp(fragments.map((f) => f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'i');
