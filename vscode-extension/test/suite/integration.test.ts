import * as assert from "node:assert";
import * as os from "node:os";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import * as vscode from "vscode";
import { resolveInterpreter } from "../../src/cli/locate";
import { runJsonCommand } from "../../src/cli/runner";
import {
  CheckReport,
  InitResult,
  LicenseStatusResult,
  ObfuscateErrorResult,
  ObfuscateSuccessResult,
  TrialStatusResult,
} from "../../src/cli/types";
import { DiagnosticsProvider } from "../../src/diagnostics/diagnosticsProvider";
import { deriveTier } from "../../src/status/tierStatus";

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

// M2 real-contract tests: the status bar (tierStatus.ts), "Generate
// pyobfus.yaml" (--init --json), and "Obfuscate with pyobfus" (the main
// obfuscate command's --json success/error shapes) all depend on CLI
// contracts that were verified live 2026-08-04 but never exercised in CI
// before now. Same ENOENT-only-skip discipline as the suite above.

suite("integration: M2 real pyobfus contracts", () => {
  const fixtureFile = path.join(__dirname, "..", "fixtures", "sample_project", "risky.py");

  test("pyobfus.trial_cli status --json and pyobfus_pro.cli status --json feed deriveTier without throwing", async function () {
    this.timeout(20_000);

    const interpreter = await resolveInterpreter(vscode.Uri.file(fixtureFile));
    let trial: TrialStatusResult | undefined;
    let license: LicenseStatusResult | undefined;
    try {
      trial = await runJsonCommand<TrialStatusResult>(
        interpreter.pythonPath,
        ["-m", "pyobfus.trial_cli", "status", "--json"],
        { allowNonZeroExit: true },
      );
      license = await runJsonCommand<LicenseStatusResult>(
        interpreter.pythonPath,
        ["-m", "pyobfus_pro.cli", "status", "--json"],
        { allowNonZeroExit: true },
      );
    } catch (err) {
      if (skipOnEnoent(this, err, interpreter.pythonPath)) {
        return;
      }
      throw err;
    }

    assert.strictEqual(trial.version, 1);
    assert.strictEqual(license.version, 1);
    assert.ok(license.device.fingerprint.length > 0);
    // A fresh CI runner has no trial/license state -- both should report
    // absent (null), which deriveTier must turn into "community" without
    // throwing, not an untested edge case.
    const status = deriveTier(license, trial);
    assert.strictEqual(status.tier, "community");
  });

  test("pyobfus --init --json produces the documented shape", async function () {
    this.timeout(20_000);

    const tmpDir = path.join(os.tmpdir(), `pyobfus-init-test-${randomUUID()}`);
    await vscode.workspace.fs.createDirectory(vscode.Uri.file(tmpDir));
    await vscode.workspace.fs.writeFile(
      vscode.Uri.file(path.join(tmpDir, "app.py")),
      Buffer.from("def foo():\n    return 1\n", "utf-8"),
    );

    const interpreter = await resolveInterpreter(vscode.Uri.file(tmpDir));
    let result: InitResult;
    try {
      result = await runJsonCommand<InitResult>(
        interpreter.pythonPath,
        ["-m", "pyobfus", "--init", tmpDir, "--json"],
        { cwd: tmpDir, allowNonZeroExit: true },
      );
    } catch (err) {
      if (skipOnEnoent(this, err, interpreter.pythonPath)) {
        return;
      }
      throw err;
    }

    assert.strictEqual(result.version, 1);
    assert.strictEqual(result.written, true);
    assert.ok(result.config_path.endsWith("pyobfus.yaml"));
  });

  test("pyobfus --json (real obfuscate, --dry-run) produces the documented success shape", async function () {
    this.timeout(20_000);

    const interpreter = await resolveInterpreter(vscode.Uri.file(fixtureFile));
    let result: ObfuscateSuccessResult | ObfuscateErrorResult;
    try {
      result = await runJsonCommand<ObfuscateSuccessResult | ObfuscateErrorResult>(
        interpreter.pythonPath,
        ["-m", "pyobfus", fixtureFile, "-o", path.join(os.tmpdir(), `pyobfus-obf-test-${randomUUID()}.py`), "--json", "--dry-run"],
        { allowNonZeroExit: true },
      );
    } catch (err) {
      if (skipOnEnoent(this, err, interpreter.pythonPath)) {
        return;
      }
      throw err;
    }

    assert.strictEqual(result.status, "success", `expected success, got: ${JSON.stringify(result)}`);
    const success = result as ObfuscateSuccessResult;
    assert.strictEqual(success.dry_run, true);
    assert.ok(success.stats.files_processed >= 1);
  });
});

function skipOnEnoent(ctx: Mocha.Context, err: unknown, interpreterPath: string): boolean {
  const nodeErr = err as NodeJS.ErrnoException;
  if (nodeErr?.code === "ENOENT") {
    console.log(
      `[integration test] skipping: interpreter not found (${interpreterPath}). ` +
        `Set PYOBFUS_PYTHON_PATH or install pyobfus for a resolvable interpreter to run this test.`,
    );
    ctx.skip();
    return true;
  }
  return false;
}
