import * as assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import { findPyobfusConfigInCwd, isConfigValidationError } from "../../src/commands/obfuscateFile";
import { ObfuscateErrorResult } from "../../src/cli/types";

function errorResult(overrides: Partial<ObfuscateErrorResult>): ObfuscateErrorResult {
  return {
    version: 1,
    status: "error",
    error_type: "ValueError",
    message: "Unknown configuration key: typo_key",
    suggestion: "Unexpected error",
    ai_hint: "pyobfus --verbose",
    exit_code: 1,
    ...overrides,
  };
}

suite("commands/obfuscateFile config error helpers", () => {
  test("recognizes pyobfus unknown-key config errors", () => {
    assert.strictEqual(isConfigValidationError(errorResult({})), true);
  });

  test("does not treat unrelated ValueError results as config validation errors", () => {
    assert.strictEqual(isConfigValidationError(errorResult({ message: "something else" })), false);
  });

  test("finds the same pyobfus.yaml names the CLI auto-discovers", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), `pyobfus-config-test-${randomUUID()}-`));
    const configPath = path.join(dir, ".pyobfus.yml");
    fs.writeFileSync(configPath, "obfuscation:\n  preset: safe\n", "utf-8");

    assert.strictEqual(findPyobfusConfigInCwd(dir), configPath);
  });

  test("returns undefined when no pyobfus config exists in cwd", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), `pyobfus-config-test-${randomUUID()}-`));

    assert.strictEqual(findPyobfusConfigInCwd(dir), undefined);
  });
});
