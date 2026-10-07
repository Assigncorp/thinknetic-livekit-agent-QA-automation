import fs from 'node:fs';
import path from 'node:path';
import { REPO_ROOT } from '../config/testbed.js';
import type { TranscriptMessage } from '../types/testbed.js';
import type { ConversationStep } from '../pages/ChatWidget.js';

/**
 * Writes a browser call in the judge's transcript schema, so the deterministic
 * oracle scores it exactly as it scores an SDK call.
 *
 * docs/deterministic-kb-testing.md §8(b): Playwright collects, Python scores -
 * one schema, one oracle. A browser transcript and an SDK transcript of the
 * same question then get the same verdict, and a divergence is a real
 * difference between the deployment's two front doors rather than noise.
 *
 *   make oracle DIR=report/data/recordings
 *
 * Intents come from the conversation steps where a turn can be matched to one;
 * the oracle uses them to tell call handling apart from the answer, and to
 * spot the accept-the-SMS path, where the facts leave the chat.
 */
export interface RecordingMeta {
  scenarioId: string;
  kbId: string;
  serial: string;
  controller: string | null;
  question: string;
  room: string | null;
}

export function writeRecording(
  meta: RecordingMeta,
  messages: TranscriptMessage[],
  steps: ConversationStep[],
  label: string,
): string {
  const agentIntent = new Map<string, string>();
  const callerIntent = new Map<string, string>();
  for (const s of steps) {
    if (s.agentTurn) agentIntent.set(s.agentTurn, s.intent);
    if (s.reply) callerIntent.set(s.reply, s.intent);
  }

  const turns = messages.map((m) => ({
    speaker: m.who === 'agent' ? 'agent' : 'caller',
    text: m.text,
    elapsedMs: null,
    intent: (m.who === 'agent' ? agentIntent.get(m.text) : callerIntent.get(m.text)) ?? null,
    idle: false,
  }));

  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
  const file = path.join(REPO_ROOT, 'report', 'data', 'recordings', `ui-${label}-${meta.serial}-${stamp}.json`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(
    file,
    JSON.stringify({ ...meta, recordedAt: new Date().toISOString(), source: 'browser', turns }, null, 2) + '\n',
  );
  return file;
}
