import * as assert from "node:assert";
import * as vscode from "vscode";
import { riskToDiagnostic } from "../../src/diagnostics/diagnosticsProvider";
import { Risk } from "../../src/cli/types";

// This exercises the real `vscode` Diagnostics API surface (vscode.Range,
// vscode.Diagnostic, DiagnosticSeverity), so it must run inside the
// Extension Host test harness (`npm test` / @vscode/test-cli), not plain
// Node/Mocha -- unlike cliRunner.test.ts, which is pure logic.

function makeRisk(overrides: Partial<Risk> = {}): Risk {
  return {
    category: "dynamic_exec",
    severity: "high",
    file: "/tmp/example.py",
    line: 5,
    col: 4,
    message: "Call to eval() — dynamic code execution cannot be obfuscated safely.",
    suggestion: "Exclude this file via 'exclude_patterns' in pyobfus.yaml.",
    snippet: "",
    ...overrides,
  };
}

suite("diagnostics/riskToDiagnostic", () => {
  test("maps each severity to the correct vscode.DiagnosticSeverity", () => {
    const cases: Array<[Risk["severity"], vscode.DiagnosticSeverity]> = [
      ["high", vscode.DiagnosticSeverity.Error],
      ["medium", vscode.DiagnosticSeverity.Warning],
      ["low", vscode.DiagnosticSeverity.Information],
      ["info", vscode.DiagnosticSeverity.Hint],
    ];
    for (const [severity, expected] of cases) {
      const diagnostic = riskToDiagnostic(makeRisk({ severity }));
      assert.strictEqual(diagnostic.severity, expected, `severity=${severity}`);
    }
  });

  test("converts pyobfus's 1-based line to VS Code's 0-based line", () => {
    const diagnostic = riskToDiagnostic(makeRisk({ line: 5, col: 4 }));
    assert.strictEqual(diagnostic.range.start.line, 4);
    assert.strictEqual(diagnostic.range.start.character, 4);
  });

  test("clamps line 1 to range start line 0, not -1", () => {
    const diagnostic = riskToDiagnostic(makeRisk({ line: 1, col: 0 }));
    assert.strictEqual(diagnostic.range.start.line, 0);
  });

  test("carries the message, source, and category code through", () => {
    const risk = makeRisk({ message: "Custom message", category: "unsafe_deserialization" });
    const diagnostic = riskToDiagnostic(risk);
    assert.strictEqual(diagnostic.message, "Custom message");
    assert.strictEqual(diagnostic.source, "pyobfus");
    assert.strictEqual(diagnostic.code, "unsafe_deserialization");
  });

  test("attaches the suggestion as relatedInformation when present", () => {
    const diagnostic = riskToDiagnostic(makeRisk({ suggestion: "Do X instead." }));
    assert.ok(diagnostic.relatedInformation && diagnostic.relatedInformation.length === 1);
    assert.strictEqual(diagnostic.relatedInformation![0].message, "Do X instead.");
  });

  test("omits relatedInformation when suggestion is empty", () => {
    const diagnostic = riskToDiagnostic(makeRisk({ suggestion: "" }));
    assert.strictEqual(diagnostic.relatedInformation, undefined);
  });
});
