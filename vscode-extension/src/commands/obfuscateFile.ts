/**
 * "Obfuscate with pyobfus" command -- right-click a .py file or folder in
 * the Explorer (or the editor tab of an open .py file) to run the real
 * `pyobfus <input> -o <output> --json` obfuscation, not just --check
 * (ranked v1 scope item #4 -- table-stakes parity, ranked below diagnostics
 * and reverse-trace since it's the weakest/most-cloneable differentiator).
 */
import * as vscode from "vscode";
import * as path from "node:path";
import { resolveInterpreter } from "../cli/locate";
import { runJsonCommand } from "../cli/runner";
import { reportCliError } from "../cli/errorReporting";
import { ObfuscateErrorResult, ObfuscateSuccessResult } from "../cli/types";

export function registerObfuscateFileCommand(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("pyobfus.obfuscateFile", (uri?: vscode.Uri) =>
      obfuscateFile(uri, outputChannel),
    ),
  );
}

async function obfuscateFile(uri: vscode.Uri | undefined, outputChannel: vscode.OutputChannel): Promise<void> {
  const target = uri ?? vscode.window.activeTextEditor?.document.uri;
  if (!target) {
    void vscode.window.showWarningMessage("pyobfus: select or open a Python file/folder first.");
    return;
  }

  const defaultOutput = defaultOutputPath(target.fsPath);
  const outputPath = await vscode.window.showInputBox({
    title: "pyobfus: Obfuscate",
    prompt: `Output path for ${path.basename(target.fsPath)}`,
    value: defaultOutput,
  });
  if (!outputPath) {
    return; // user cancelled
  }

  const interpreter = await resolveInterpreter(target);
  try {
    const result = await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: `pyobfus: obfuscating ${path.basename(target.fsPath)}...` },
      () =>
        runJsonCommand<ObfuscateSuccessResult | ObfuscateErrorResult>(
          interpreter.pythonPath,
          ["-m", "pyobfus", target.fsPath, "-o", outputPath, "--json"],
          { allowNonZeroExit: true },
        ),
    );

    if (result.status === "error") {
      await handleObfuscateError(result);
      return;
    }

    const { files_processed, total_names_obfuscated } = result.stats;
    const choice = await vscode.window.showInformationMessage(
      `pyobfus: obfuscated ${files_processed} file(s), ${total_names_obfuscated} name(s) renamed -> ${outputPath}`,
      "Reveal in Explorer",
    );
    if (choice === "Reveal in Explorer") {
      await vscode.commands.executeCommand("revealFileInOS", vscode.Uri.file(outputPath));
    }
  } catch (err) {
    reportCliError(err, interpreter.pythonPath, outputChannel, "obfuscation");
  }
}

async function handleObfuscateError(result: ObfuscateErrorResult): Promise<void> {
  if (result.error_type === "LimitExceededError") {
    const choice = await vscode.window.showWarningMessage(
      `pyobfus: ${result.message}`,
      "Start Free Trial",
    );
    if (choice === "Start Free Trial") {
      await vscode.commands.executeCommand("pyobfus.startTrial");
    }
    return;
  }
  void vscode.window.showErrorMessage(`pyobfus: ${result.message} (${result.suggestion})`);
}

/** `foo.py` -> `foo_obf.py`; `src/` (directory) -> sibling `src_obf/`. */
function defaultOutputPath(inputPath: string): string {
  const dir = path.dirname(inputPath);
  const ext = path.extname(inputPath);
  const base = ext ? path.basename(inputPath, ext) : path.basename(inputPath);
  return path.join(dir, `${base}_obf${ext}`);
}
