import * as assert from "node:assert";
import * as path from "node:path";
import * as vscode from "vscode";
import { resolveInterpreter } from "../../src/cli/locate";
import { runJsonCommand } from "../../src/cli/runner";
import { CheckReport } from "../../src/cli/types";
import { DiagnosticsProvider } from "../../src/diagnostics/diagnosticsProvider";

// Real contract test: runs against an actually-installed `pyobfus` (CI
// installs it from the parent repo before running this suite; see
// .github/workflows/vscode-extension-ci.yml). This is the test that would
// catch pyobfus's `--check --json` output shape silently drifting out
// from under this extension.
//
// Deliberately calls runJsonCommand directly (not through
// DiagnosticsProvider, which swallows every error into a single
// `undefined` return so a real UI never crashes on a bad environment) --
// that swallowing previously made this test silently skip in CI with zero
// diagnostic information about *why*, across two failed debugging
// iterations (2026-08-04). Only a genuine ENOENT (interpreter truly not
// found) is treated as a skip; every other failure surfaces with a full
// error message/stack in the Mocha report.

suite("integration: real pyobfus contract", () => {
  const fixtureFile = path.join(__dirname, "..", "fixtures", "sample_project", "risky.py");

  test("pyobfus --check --json produces the documented shape for the fixture's eval()", async function () {
    this.timeout(20_000);

    const interpreter = await resolveInterpreter(vscode.Uri.file(fixtureFile));
    console.log(`[integration test] resolved interpreter: ${interpreter.pythonPath} (source: ${interpreter.source})`);

    let report: CheckReport;
    try {
      report = await runJsonCommand<CheckReport>(
        interpreter.pythonPath,
        ["-m", "pyobfus", "--check", fixtureFile, "--json"],
        { allowNonZeroExit: true },
      );
    } catch (err) {
      const nodeErr = err as NodeJS.ErrnoException;
      if (nodeErr?.code === "ENOENT") {
        console.log(
          `[integration test] skipping: interpreter not found (${interpreter.pythonPath}). ` +
            `Set PYOBFUS_PYTHON_PATH or install pyobfus for a resolvable interpreter to run this test.`,
        );
        this.skip();
        return;
      }
      // Anything else (JSON parse failure, non-ENOENT spawn error,
      // pyobfus itself erroring) is a real signal -- let it fail loudly
      // rather than silently skipping.
      throw err;
    }

    assert.ok(report.risks.length >= 1, "expected at least one risk finding");
    const evalRisk = report.risks.find((r) => r.category === "dynamic_exec");
    assert.ok(evalRisk, `expected a dynamic_exec finding; got categories: ${report.risks.map((r) => r.category).join(", ")}`);
    assert.strictEqual(evalRisk!.severity, "high");
    assert.ok(evalRisk!.line > 0);

    // Also confirm DiagnosticsProvider correctly turns this real report
    // into a real published vscode.Diagnostic.
    const outputChannel = vscode.window.createOutputChannel("pyobfus-test");
    const provider = new DiagnosticsProvider(outputChannel);
    try {
      const publishedReport = await provider.checkAndPublish(vscode.Uri.file(fixtureFile), "file");
      assert.ok(publishedReport, "DiagnosticsProvider.checkAndPublish should succeed once runJsonCommand did");
      const diagnostics = vscode.languages.getDiagnostics(vscode.Uri.file(fixtureFile));
      assert.ok(diagnostics.length >= 1, "expected the finding published as a real Diagnostic");
      assert.strictEqual(diagnostics[0].severity, vscode.DiagnosticSeverity.Error);
    } finally {
      provider.dispose();
      outputChannel.dispose();
    }
  });
});
