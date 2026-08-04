/**
 * "pyobfus: Generate pyobfus.yaml" command -- wraps `pyobfus --init --json`
 * (ranked v1 scope item #3). No core-code changes needed; --init --json
 * already existed before this extension.
 */
import * as vscode from "vscode";
import { resolveInterpreter } from "../cli/locate";
import { runJsonCommand } from "../cli/runner";
import { reportCliError } from "../cli/errorReporting";
import { InitResult } from "../cli/types";

export function registerGenerateConfigCommand(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("pyobfus.generateConfig", () => generateConfig(outputChannel)),
  );
}

async function generateConfig(outputChannel: vscode.OutputChannel): Promise<void> {
  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    void vscode.window.showWarningMessage("pyobfus: open a folder/workspace first.");
    return;
  }

  const interpreter = await resolveInterpreter(folder.uri);
  try {
    const result = await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "pyobfus: generating pyobfus.yaml..." },
      () =>
        runJsonCommand<InitResult>(
          interpreter.pythonPath,
          ["-m", "pyobfus", "--init", folder.uri.fsPath, "--json"],
          { cwd: folder.uri.fsPath, allowNonZeroExit: true },
        ),
    );

    const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(result.config_path));
    await vscode.window.showTextDocument(doc, { preview: false });

    const frameworkNote = result.frameworks_detected.length > 0
      ? ` (${result.frameworks_detected.join(", ")} detected)`
      : "";
    if (result.high_risk_findings > 0) {
      void vscode.window.showWarningMessage(
        `pyobfus: wrote ${result.config_path}${frameworkNote}. ` +
          `${result.high_risk_findings} high-risk pattern(s) detected -- run "pyobfus: Check Workspace" before obfuscating.`,
      );
    } else {
      void vscode.window.showInformationMessage(`pyobfus: wrote ${result.config_path}${frameworkNote}.`);
    }
  } catch (err) {
    reportCliError(err, interpreter.pythonPath, outputChannel, "generating pyobfus.yaml");
  }
}
