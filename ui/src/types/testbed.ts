/** Types for config/testbed.config.json and resources/generated/*. */

export interface KnowledgeBase {
  id: string;
  file: string;
  machine: string;
  controller: string | null;
  hopperType: string | null;
  anchorSerial: string | null;
  enabled: boolean;
}

export interface SerialEntry {
  serial: string;
  description: string;
  controller: string;
  hopperType: string;
  sheet: string;
  kbId: string;
}

export interface Scenario {
  id: string;
  kbId: string;
  kind: 'faq' | 'howto' | 'problem';
  section: string;
  question: string;
  expectAnchors: string[];
  sourceLine: number;
}

export interface TestbedConfig {
  resources: { root: string; kbDir: string; serialWorkbook: string; generatedDir: string };
  knowledgeBases: KnowledgeBase[];
  scenarioSelection: {
    mode: 'random' | 'fixed' | 'roundRobin';
    seed: number | null;
    fixedScenarioId: string | null;
    rotateSerials: boolean;
    serialsPerKb: number;
    excludeSerials: string[];
  };
  chatFlow: {
    greetingAsksForSerial: string[];
    readBackConfirmation: string[];
    confirmationReply: string;
    agentIdlePrompts: string[];
  };
  budgets: {
    sessionConnectMs: number;
    greetingMs: number;
    serialAcknowledgedMs: number;
    answerMs: number;
    apiResponseMs: number;
  };
  assertions: {
    requireNonEmptyReply: boolean;
    minReplyChars: number;
    checkExpectedAnchors: boolean;
    failOnWrongControllerFamily: boolean;
  };
}

/** One resolved test case: which serial to give, and what to ask once accepted. */
export interface ChatCase {
  scenario: Scenario;
  serial: SerialEntry;
  kb: KnowledgeBase;
}

/** A single turn as rendered in the transcript. */
export interface TranscriptMessage {
  who: 'agent' | 'user';
  text: string;
}
