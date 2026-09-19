// Temp-directory bookkeeping for tests that create real directories under
// os.tmpdir(). Mocha's tdd interface has no per-test tmpdir the way pytest's
// tmp_path fixture does, so suites that create temp dirs wrap them with
// trackTempDir() and register suiteTeardown(cleanupTrackedTempDirs) once.
// Before this helper existed, every test run leaked its mkdtempSync/mkdtemp
// directories (see docs/TODO.md "测试 fixture 漏临时目录").
import * as fs from "node:fs";

const tracked: string[] = [];

/** Wrap a freshly-created temp directory so teardown removes it later. */
export function trackTempDir(dir: string): string {
  tracked.push(dir);
  return dir;
}

/** Remove every tracked temp directory; register via suiteTeardown(). */
export function cleanupTrackedTempDirs(): void {
  for (const dir of tracked.splice(0)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}
