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
    if (isStalePyobfusInstall(err.stderr)) {
      void vscode.window
        .showWarningMessage(
          `pyobfus at ${interpreterPath} is too old to run as a module (this extension needs ` +
            `\`python -m pyobfus\` support). Upgrade it, or select a different interpreter.`,
          "Upgrade pyobfus",
          "Select Interpreter",
        )
        .then((choice) => {
          if (choice === "Upgrade pyobfus") {
            const terminal = vscode.window.createTerminal("pyobfus upgrade");
            terminal.show();
            terminal.sendText(`"${interpreterPath}" -m pip install --upgrade pyobfus`);
          } else if (choice === "Select Interpreter") {
            void vscode.commands.executeCommand("python.setInterpreter");
          }
        });
      return;
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

/**
 * Detects Python's stock "package cannot be directly executed" error for
 * `-m pyobfus`, which fires whenever the resolved interpreter has a
 * `pyobfus` importable but lacking `pyobfus/__main__.py` -- in practice
 * this means a pyobfus version predating module-invocation support (added
 * around the AI-native CLI work, v0.4.0), not a corrupt install. Found
 * live 2026-08-06: the maintainer's own environment resolved a shared
 * research venv with `pyobfus==0.2.3` (installed ~Dec 2025) still on it,
 * and the raw Python error text ("No module named pyobfus.__main__;
 * 'pyobfus' is a package and cannot be directly executed") gives zero
 * indication of what's actually wrong or how to fix it. Exported for unit
 * testing without needing a real subprocess.
 */
export function isStalePyobfusInstall(stderr: string): boolean {
  return stderr.includes("pyobfus.__main__") && stderr.includes("cannot be directly executed");
}
