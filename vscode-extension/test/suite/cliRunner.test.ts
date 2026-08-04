import * as assert from "node:assert";
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
});
