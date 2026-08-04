import * as assert from "node:assert";
import * as path from "node:path";
import * as vscode from "vscode";
import { DiagnosticsProvider } from "../../src/diagnostics/diagnosticsProvider";

// Real contract test: runs the DiagnosticsProvider against an actually-
// installed `pyobfus` (whatever interpreter is on PATH in the test
// environment -- CI installs pyobfus from the parent repo before running
// this suite; see .github/workflows/vscode-extension-ci.yml). This is the
// test that would catch pyobfus's `--check --json` output shape silently
// drifting out from under this extension.
//
// Skips gracefully (rather than failing) if pyobfus isn't importable by
// the interpreter this test environment resolves, so a contributor running
// `npm test` without pyobfus installed still sees the rest of the suite
// pass -- this suite is the one exception that needs the real CLI.

suite("integration: DiagnosticsProvider against a real pyobfus", () => {
  const fixtureFile = path.join(
    __dirname,
    "..",
    "fixtures",
    "sample_project",
    "risky.py",
  );

  test("publishes a high-severity diagnostic for the fixture's eval() call", async function () {
    this.timeout(20_000);

    const outputChannel = vscode.window.createOutputChannel("pyobfus-test");
    const provider = new DiagnosticsProvider(outputChannel);
    try {
      const report = await provider.checkAndPublish(vscode.Uri.file(fixtureFile), "file");
      if (!report) {
        // checkAndPublish returns undefined on a resolution/spawn failure
        // (e.g. pyobfus not installed for the resolved interpreter in this
        // environment) -- treat as a skip, not a failure, since this
        // suite's job is to catch *output-shape drift* in an environment
        // that does have pyobfus, not to enforce that every environment
        // running `npm test` has it.
        this.skip();
        return;
      }

      assert.ok(report.risks.length >= 1, "expected at least one risk finding");
      const evalRisk = report.risks.find((r) => r.category === "dynamic_exec");
      assert.ok(evalRisk, "expected a dynamic_exec finding for the eval() call");
      assert.strictEqual(evalRisk!.severity, "high");
      assert.ok(evalRisk!.line > 0);

      const diagnostics = vscode.languages.getDiagnostics(vscode.Uri.file(fixtureFile));
      assert.ok(diagnostics.length >= 1, "expected the finding published as a real Diagnostic");
      assert.strictEqual(diagnostics[0].severity, vscode.DiagnosticSeverity.Error);
    } finally {
      provider.dispose();
      outputChannel.dispose();
    }
  });
});
