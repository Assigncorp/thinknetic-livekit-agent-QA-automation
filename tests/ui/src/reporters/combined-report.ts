import { spawnSync } from 'node:child_process';
import path from 'node:path';
import type { Reporter } from '@playwright/test/reporter';
import { REPO_ROOT } from '../config/testbed.js';

/**
 * Every browser run ends with report/index.html next to report/playwright/,
 * however it was started - `make`, `npx playwright test`, the VS Code
 * extension (agreed 2026-09-28). The pytest suites do the same through
 * tools/report_hook.py.
 *
 * onExit, not onEnd: it runs after every reporter's onEnd, so Playwright's own
 * HTML and JSON reports (which the combined report reads) are on disk by then.
 * Skipped with LKQA_NO_REPORT=1 - tools/run_parallel.sh builds once at the end.
 */
export default class CombinedReport implements Reporter {
  /** Tests that actually ran: `--list` runs no test and must leave report/ alone. */
  private ran = 0;

  printsToStdio(): boolean {
    return false;
  }

  onTestEnd(): void {
    this.ran += 1;
  }

  async onExit(): Promise<void> {
    if (process.env.LKQA_NO_REPORT === '1' || this.ran === 0) return;
    const done = spawnSync(process.env.PYTHON ?? 'python3', [path.join(REPO_ROOT, 'tools', 'build_report.py')], {
      encoding: 'utf8',
    });
    const out = (done.stdout || done.stderr || String(done.error ?? '')).trim();
    if (out) console.log(`\n${out}`);
  }
}
