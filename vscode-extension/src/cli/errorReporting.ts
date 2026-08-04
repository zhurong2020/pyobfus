/**
 * Shared "a pyobfus CLI invocation failed" reporting, used by the M2
 * commands (generateConfig, obfuscateFile, proFunnel). Factored out here
 * because M1 already grew two independent, slightly different copies of
 * this logic (DiagnosticsProvider.handleError's ENOENT-with-actionable-
 * buttons treatment, unmapTrace.ts's plainer reportError) -- a third and
 * fourth near-identical copy would be actual duplication, not just
 * "three similar lines." M1's existing two are left as-is rather than
 * retrofitted, to avoid re-touching already-shipped, already-tested code.
 */
import * as vscode from "vscode";
import { PyobfusCliError, PyobfusJsonParseError } from "./runner";

export function reportCliError(
  err: unknown,
  interpreterPath: string,
  outputChannel: vscode.OutputChannel,
  actionLabel: string,
): void {
  if (err instanceof PyobfusCliError) {
    outputChannel.appendLine(`[pyobfus] ${actionLabel} failed: ${err.message}`);
    if (err.stderr) {
      outputChannel.appendLine(err.stderr);
    }
    void vscode.window.showErrorMessage(
      `pyobfus: ${actionLabel} failed. ${err.stderr.trim() || err.message}`,
    );
    return;
  }
  if (err instanceof PyobfusJsonParseError) {
    outputChannel.appendLine(`[pyobfus] ${actionLabel} output was not valid JSON: ${err.message}`);
    void vscode.window.showErrorMessage(
      `pyobfus: unexpected output from ${actionLabel}. See the pyobfus output channel.`,
    );
    return;
  }
  const nodeErr = err as NodeJS.ErrnoException;
  if (nodeErr?.code === "ENOENT") {
    outputChannel.appendLine(`[pyobfus] interpreter not found or pyobfus not installed: ${interpreterPath}`);
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
  outputChannel.appendLine(`[pyobfus] unexpected error during ${actionLabel}: ${String(err)}`);
  void vscode.window.showErrorMessage(
    `pyobfus: unexpected error during ${actionLabel}. See the pyobfus output channel.`,
  );
}
