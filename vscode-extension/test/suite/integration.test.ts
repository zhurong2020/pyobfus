import * as assert from "node:assert";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import * as vscode from "vscode";
import { resolveInterpreter } from "../../src/cli/locate";
import { runJsonCommand, PyobfusJsonParseError } from "../../src/cli/runner";
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
import { cwdForTarget } from "../../src/commands/obfuscateFile";

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

  // Regression coverage for the real 2026-08-06 bug: obfuscateFile.ts used
  // to pass no `cwd` at all, which (a) crashed when the ambient extension-
  // host cwd happened to be shadowed by a same-named `pyobfus` directory
  // (see cliRunner.test.ts) and (b) even when it didn't crash, silently
  // skipped a project's own pyobfus.yaml -- config_validator.find_config_file
  // only checks `<cwd>/pyobfus.yaml`, no upward directory walk, and
  // runJsonCommand's safe os.tmpdir() default (needed to fix (a)) would by
  // itself reintroduce (b). cwdForTarget is the real function
  // obfuscateFile.ts calls, not a reimplementation, so this proves the
  // actual code path, not just the concept.
  //
  // These two tests use plain --verbose text output (not --json), asserted
  // via PyobfusJsonParseError's captured stdout, not the JSON contract's
  // "preset" field -- that field turns out to only ever echo the raw
  // --preset CLI flag (pyobfus/cli.py's payload dict reuses the same local
  // variable Click bound from the flag, never reassigned after a config
  // file is loaded), so it can't distinguish "no config found" from "config
  // found but its preset isn't surfaced here" -- a separate, pre-existing,
  // minor pyobfus CLI reporting gap, not something this fix should paper
  // over by asserting against a field that wouldn't actually catch a
  // regression here.
  test("cwdForTarget resolves pyobfus.yaml auto-discovery correctly outside any open workspace folder", async function () {
    this.timeout(20_000);

    const projectDir = path.join(os.tmpdir(), `pyobfus-cwd-test-${randomUUID()}`);
    await vscode.workspace.fs.createDirectory(vscode.Uri.file(projectDir));
    const targetFile = path.join(projectDir, "app.py");
    await vscode.workspace.fs.writeFile(vscode.Uri.file(targetFile), Buffer.from("def foo():\n    return 1\n", "utf-8"));
    const configPath = path.join(projectDir, "pyobfus.yaml");
    await vscode.workspace.fs.writeFile(vscode.Uri.file(configPath), Buffer.from("obfuscation:\n  preset: safe\n", "utf-8"));

    // projectDir is a fresh tmpdir, never part of the test workspace
    // (test/fixtures/sample_project, per .vscode-test.mjs) -- exercises the
    // getWorkspaceFolder-returns-undefined fallback branch.
    assert.strictEqual(vscode.workspace.getWorkspaceFolder(vscode.Uri.file(targetFile)), undefined);
    const resolvedCwd = cwdForTarget(vscode.Uri.file(targetFile));
    assert.strictEqual(resolvedCwd, projectDir);

    const interpreter = await resolveInterpreter(vscode.Uri.file(targetFile));
    await assertConfigAutoDiscovered(this, interpreter.pythonPath, targetFile, resolvedCwd, configPath);
  });

  test("cwdForTarget resolves to the enclosing workspace folder when the target is part of one", async function () {
    this.timeout(20_000);

    // The workspace folder actually opened for this test run (per
    // .vscode-test.mjs's workspaceFolder: "test/fixtures/sample_project")
    // -- NOT necessarily the same path as fixtureFile's directory, since
    // fixtureFile is the out/-compiled copy (see copy-test-fixtures.js)
    // while the opened workspace is the source location.
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    assert.ok(workspaceFolder, "expected a workspace folder to be open for this test run");
    const targetInWorkspace = path.join(workspaceFolder!.uri.fsPath, "risky.py");
    assert.ok(fs.existsSync(targetInWorkspace), `expected ${targetInWorkspace} to exist (the checked-in fixture)`);

    const resolvedCwd = cwdForTarget(vscode.Uri.file(targetInWorkspace));
    assert.strictEqual(resolvedCwd, workspaceFolder!.uri.fsPath);

    // Temporarily drop a distinctive pyobfus.yaml into the shared fixture
    // folder to prove auto-discovery actually reads from resolvedCwd, not
    // just that the path string looks right -- cleaned up in `finally` so
    // sibling tests reading this same checked-in fixture folder are
    // unaffected either way.
    const configPath = path.join(workspaceFolder!.uri.fsPath, "pyobfus.yaml");
    await vscode.workspace.fs.writeFile(vscode.Uri.file(configPath), Buffer.from("obfuscation:\n  preset: aggressive\n", "utf-8"));
    try {
      const interpreter = await resolveInterpreter(vscode.Uri.file(targetInWorkspace));
      await assertConfigAutoDiscovered(this, interpreter.pythonPath, targetInWorkspace, resolvedCwd, configPath);
    } finally {
      await vscode.workspace.fs.delete(vscode.Uri.file(configPath));
    }
  });
});

/**
 * Runs a real `--dry-run --verbose` (plain text, not --json) obfuscate
 * invocation and asserts pyobfus reported auto-discovering exactly
 * `configPath` from `cwd` -- direct proof of the cwd-resolution fix, not an
 * inference from a JSON field that doesn't actually carry this signal (see
 * the comment above the two tests that call this).
 */
async function assertConfigAutoDiscovered(
  ctx: Mocha.Context,
  pythonPath: string,
  targetFile: string,
  cwd: string,
  configPath: string,
): Promise<void> {
  try {
    await runJsonCommand(
      pythonPath,
      ["-m", "pyobfus", targetFile, "-o", path.join(os.tmpdir(), `pyobfus-cwd-obf-${randomUUID()}.py`), "--dry-run", "--verbose"],
      { cwd, allowNonZeroExit: true },
    );
    assert.fail("expected plain --verbose text output to fail JSON parsing");
  } catch (err) {
    if (skipOnEnoent(ctx, err, pythonPath)) {
      return;
    }
    if (!(err instanceof PyobfusJsonParseError)) {
      throw err;
    }
    assert.ok(
      err.stdout.includes(`Auto-discovered config: ${configPath}`),
      `expected "Auto-discovered config: ${configPath}" in output, got:\n${err.stdout}`,
    );
  }
}

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
