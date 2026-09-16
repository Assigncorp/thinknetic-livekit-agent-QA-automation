/**
 * Minimal structured logging. Playwright's reporter owns pass/fail output -
 * this is only for the context you wish you had when a run fails at 2am.
 */
type Level = 'info' | 'warn' | 'error';

const emit = (level: Level, msg: string, meta?: Record<string, unknown>): void => {
  const line = `[${new Date().toISOString()}] ${level.toUpperCase()} ${msg}`;
  const out = meta ? `${line} ${JSON.stringify(meta)}` : line;
  if (level === 'error') console.error(out);
  else if (level === 'warn') console.warn(out);
  else console.log(out);
};

export const log = {
  info: (msg: string, meta?: Record<string, unknown>) => emit('info', msg, meta),
  warn: (msg: string, meta?: Record<string, unknown>) => emit('warn', msg, meta),
  error: (msg: string, meta?: Record<string, unknown>) => emit('error', msg, meta),
} as const;
