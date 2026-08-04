/**
 * Wires `pyobfus --check --json` findings into VS Code's native
 * DiagnosticCollection API. This is the headline v1 feature -- see
 * docs/VSCODE_EXTENSION_PLAN.md for why: VS Code's own squiggly-underline +
 * Problems-panel support works immediately from this, and if the user has
 * Error Lens installed, its enhanced inline treatment applies for free,
 * with zero rendering work done here.
 */
import * as vscode from "vscode";
import { resolveInterpreter } from "../cli/locate";
import { runJsonCommand, PyobfusCliError, PyobfusJsonParseError } from "../cli/runner";
import { CheckReport, Risk, Severity } from "../cli/types";

const SEVERITY_MAP: Record<Severity, vscode.DiagnosticSeverity> = {
  high: vscode.DiagnosticSeverity.Error,
  medium: vscode.DiagnosticSeverity.Warning,
  low: vscode.DiagnosticSeverity.Information,
  info: vscode.DiagnosticSeverity.Hint,
};

const DIAGNOSTIC_SOURCE = "pyobfus";

export type CheckScope = "file" | "workspace";

export class DiagnosticsProvider implements vscode.Disposable {
  private readonly collection: vscode.DiagnosticCollection;
  private readonly outputChannel: vscode.OutputChannel;

  constructor(outputChannel: vscode.OutputChannel) {
    this.collection = vscode.languages.createDiagnosticCollection("pyobfus");
    this.outputChannel = outputChannel;
  }

  dispose(): void {
    this.collection.dispose();
  }

  clear(): void {
    this.collection.clear();
  }

  /**
   * Run `pyobfus --check` against `target` (a single file for `scope:
   * "file"`, e.g. on-save; a directory for `scope: "workspace"`, e.g. the
   * manual "Check Workspace" command) and publish the resulting risks as
   * diagnostics.
   *
   * `scope` decides how stale entries are cleared: a single-file check only
   * clears/replaces that one file's diagnostics (so it doesn't wipe out
   * findings for the rest of the workspace on every save); a workspace
   * check clears everything first, since it's producing a fresh complete
   * picture and any file missing from the new results is no longer flagged.
   */
  async checkAndPublish(
    target: vscode.Uri,
    scope: CheckScope,
    cwd?: string,
  ): Promise<CheckReport | undefined> {
    const interpreter = await resolveInterpreter(target);
    try {
      const report = await runJsonCommand<CheckReport>(
        interpreter.pythonPath,
        ["-m", "pyobfus", "--check", target.fsPath, "--json"],
        { cwd, allowNonZeroExit: true },
      );
      this.publish(report, target, scope);
      return report;
    } catch (err) {
      this.handleError(err, interpreter.pythonPath);
      return undefined;
    }
  }

  private publish(report: CheckReport, target: vscode.Uri, scope: CheckScope): void {
    const byFile = new Map<string, vscode.Diagnostic[]>();
    for (const risk of report.risks) {
      const diagnostic = riskToDiagnostic(risk);
      const existing = byFile.get(risk.file);
      if (existing) {
        existing.push(diagnostic);
      } else {
        byFile.set(risk.file, [diagnostic]);
      }
    }

    if (scope === "workspace") {
      this.collection.clear();
    } else {
      // Single-file check: always (re)set this exact file's entry, even to
      // an empty array when clean, so a previously-flagged-then-fixed file
      // has its squiggle removed on the next save.
      this.collection.set(target, byFile.get(target.fsPath) ?? []);
      byFile.delete(target.fsPath);
    }

    for (const [file, diagnostics] of byFile) {
      this.collection.set(vscode.Uri.file(file), diagnostics);
    }
  }

  private handleError(err: unknown, interpreterPath: string): void {
    if (err instanceof PyobfusCliError || err instanceof PyobfusJsonParseError) {
      this.outputChannel.appendLine(`[pyobfus] check failed: ${err.message}`);
      if ("stderr" in err && err.stderr) {
        this.outputChannel.appendLine(err.stderr);
      }
      return;
    }
    const nodeErr = err as NodeJS.ErrnoException;
    if (nodeErr?.code === "ENOENT") {
      this.outputChannel.appendLine(
        `[pyobfus] interpreter not found or pyobfus not installed: ${interpreterPath}`,
      );
      void vscode.window
        .showWarningMessage(
          `pyobfus is not installed for the interpreter at ${interpreterPath}.`,
          "Install pyobfus",
          "Select Interpreter",
        )
        .then((choice) => {
          if (choice === "Install pyobfus") {
            const terminal = vscode.window.createTerminal("pyobfus install");
            terminal.show();
            terminal.sendText(`"${interpreterPath}" -m pip install pyobfus`);
          } else if (choice === "Select Interpreter") {
            void vscode.commands.executeCommand("python.setInterpreter");
          }
        });
      return;
    }
    this.outputChannel.appendLine(`[pyobfus] unexpected error: ${String(err)}`);
  }
}

export function riskToDiagnostic(risk: Risk): vscode.Diagnostic {
  const line = Math.max(0, risk.line - 1); // pyobfus reports 1-based lines
  const col = Math.max(0, risk.col);
  const range = new vscode.Range(line, col, line, col + 1);
  const diagnostic = new vscode.Diagnostic(range, risk.message, SEVERITY_MAP[risk.severity]);
  diagnostic.source = DIAGNOSTIC_SOURCE;
  diagnostic.code = risk.category;
  if (risk.suggestion) {
    diagnostic.relatedInformation = [
      new vscode.DiagnosticRelatedInformation(
        new vscode.Location(vscode.Uri.file(risk.file), range),
        risk.suggestion,
      ),
    ];
  }
  return diagnostic;
}
