import * as assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import { findConfigInDirectory, validationSummary } from "../../src/commands/validateConfig";
import { ValidateConfigResult } from "../../src/cli/types";

function result(status: ValidateConfigResult["status"]): ValidateConfigResult {
  return {
    version: 1,
    status,
    valid: status !== "error",
    config_path: "/tmp/pyobfus.yaml",
    errors: status === "error" ? ["[ERROR] bad"] : [],
    warnings: status === "warnings" ? ["[WARNING] check this"] : [],
    suggestions: [],
    summary: "summary",
    ai_hint: "hint",
    exit_code: status === "error" ? 1 : 0,
  };
}

suite("commands/validateConfig helpers", () => {
  test("finds pyobfus config files in CLI discovery order", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), `pyobfus-validate-test-${randomUUID()}-`));
    const hidden = path.join(dir, ".pyobfus.yaml");
    const primary = path.join(dir, "pyobfus.yaml");
    fs.writeFileSync(hidden, "obfuscation:\n  preset: safe\n", "utf-8");
    fs.writeFileSync(primary, "obfuscation:\n  preset: balanced\n", "utf-8");

    assert.strictEqual(findConfigInDirectory(dir), primary);
  });

  test("returns undefined when no config exists", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), `pyobfus-validate-test-${randomUUID()}-`));

    assert.strictEqual(findConfigInDirectory(dir), undefined);
  });

  test("summarizes validation states", () => {
    assert.strictEqual(validationSummary(result("success")), "pyobfus: config is valid.");
    assert.strictEqual(validationSummary(result("warnings")), "pyobfus: config is valid with 1 warning(s).");
    assert.strictEqual(validationSummary(result("error")), "pyobfus: config is invalid with 1 error(s).");
  });
});
