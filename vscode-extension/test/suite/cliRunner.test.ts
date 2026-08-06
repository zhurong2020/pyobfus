import * as assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { runJsonCommand, PyobfusCliError, PyobfusJsonParseError } from "../../src/cli/runner";

// Fixture scripts that stand in for `python -m pyobfus ...` invocations,
// so these tests are deterministic and don't require pyobfus installed.
// Each is a tiny Node script (fast, no Python dependency) that prints
// canned JSON matching the shapes verified live against the real pyobfus
// CLI (see docs/VSCODE_EXTENSION_PLAN.md).
const FIXTURES_DIR = path.join(__dirname, "..", "fixtures", "cli-scripts");

suite("cli/runner", () => {
  test("parses well-formed JSON stdout", async () => {
    const result = await runJsonCommand<{ version: number; ok: boolean }>(
      process.execPath,
      [path.join(FIXTURES_DIR, "echo-json.js"), JSON.stringify({ version: 1, ok: true })],
    );
    assert.deepStrictEqual(result, { version: 1, ok: true });
  });

  test("succeeds on non-zero exit when allowNonZeroExit is true (default)", async () => {
    const result = await runJsonCommand<{ version: number }>(
      process.execPath,
      [path.join(FIXTURES_DIR, "exit-with-json.js"), "1", JSON.stringify({ version: 1 })],
    );
    assert.deepStrictEqual(result, { version: 1 });
  });

  test("throws PyobfusCliError on non-zero exit when allowNonZeroExit is false", async () => {
    await assert.rejects(
      runJsonCommand(
        process.execPath,
        [path.join(FIXTURES_DIR, "exit-with-json.js"), "1", JSON.stringify({ version: 1 })],
        { allowNonZeroExit: false },
      ),
      (err: unknown) => err instanceof PyobfusCliError,
    );
  });

  test("throws PyobfusJsonParseError on malformed stdout", async () => {
    await assert.rejects(
      runJsonCommand(process.execPath, [path.join(FIXTURES_DIR, "echo-raw.js"), "not json"]),
      (err: unknown) => err instanceof PyobfusJsonParseError,
    );
  });

  test("throws PyobfusCliError on empty stdout", async () => {
    await assert.rejects(
      runJsonCommand(process.execPath, [path.join(FIXTURES_DIR, "echo-raw.js"), ""]),
      (err: unknown) => err instanceof PyobfusCliError,
    );
  });

  test("rejects with ENOENT for a nonexistent executable", async () => {
    await assert.rejects(
      runJsonCommand("pyobfus-this-binary-does-not-exist-anywhere", ["--json"]),
      (err: unknown) => (err as NodeJS.ErrnoException).code === "ENOENT",
    );
  });

  // Regression test for a real bug found 2026-08-06: `-m pyobfus` puts cwd
  // first on sys.path, so an unset/inherited ambient cwd is a hazard --
  // if it (or a sibling) happens to be named `pyobfus`, Python resolves
  // `import pyobfus` to that directory (a namespace package) instead of
  // the real pip-installed one, failing with "No module named
  // pyobfus.__main__; 'pyobfus' is a package and cannot be directly
  // executed" even against a perfectly good interpreter. Reproduced live
  // against the maintainer's own `~/projects/pyobfus` symlink. The fix is
  // a safe default cwd in runJsonCommand itself, not a per-call-site fix,
  // so every current and future caller that doesn't have a more
  // meaningful cwd to supply is covered automatically.
  test("defaults cwd to a safe temp directory, not the ambient process cwd", async () => {
    const result = await runJsonCommand<{ cwd: string }>(process.execPath, [
      path.join(FIXTURES_DIR, "print-cwd.js"),
    ]);
    assert.strictEqual(fs.realpathSync(result.cwd), fs.realpathSync(os.tmpdir()));
    assert.notStrictEqual(fs.realpathSync(result.cwd), fs.realpathSync(process.cwd()));
  });

  test("honors an explicit cwd override (e.g. generateConfig's workspace folder)", async () => {
    const explicitCwd = fs.realpathSync(os.homedir());
    const result = await runJsonCommand<{ cwd: string }>(
      process.execPath,
      [path.join(FIXTURES_DIR, "print-cwd.js")],
      { cwd: explicitCwd },
    );
    assert.strictEqual(fs.realpathSync(result.cwd), explicitCwd);
  });
});
