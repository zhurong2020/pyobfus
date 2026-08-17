/**
 * "pyobfus: Validate pyobfus.yaml" command -- wraps
 * `pyobfus --validate-config <file> --json`.
 */
import * as vscode from "vscode";
import * as fs from "node:fs";
import * as path from "node:path";
import { resolveInterpreter } from "../cli/locate";
import { reportCliError } from "../cli/errorReporting";
import { runJsonCommand } from "../cli/runner";
import { ValidateConfigResult } from "../cli/types";

export function registerValidateConfigCommand(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("pyobfus.validateConfig", () => validateConfig(outputChannel)),
  );
}

async function validateConfig(outputChannel: vscode.OutputChannel): Promise<void> {
  const configPath = findWorkspaceConfig();
  if (!configPath) {
    void vscode.window.showWarningMessage("pyobfus: no pyobfus.yaml found in the workspace root.");
    return;
  }

  const configUri = vscode.Uri.file(configPath);
  const interpreter = await resolveInterpreter(configUri);
  try {
    const result = await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "pyobfus: validating pyobfus.yaml..." },
      () =>
        runJsonCommand<ValidateConfigResult>(
          interpreter.pythonPath,
          ["-m", "pyobfus", "--validate-config", configPath, "--json"],
          { cwd: path.dirname(configPath), allowNonZeroExit: true },
        ),
    );
    await showValidationResult(result, outputChannel);
  } catch (err) {
    reportCliError(err, interpreter.pythonPath, outputChannel, "validating pyobfus.yaml");
  }
}

export function findWorkspaceConfig(): string | undefined {
  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    return undefined;
  }
  return findConfigInDirectory(folder.uri.fsPath);
}

export function findConfigInDirectory(dir: string): string | undefined {
  for (const name of ["pyobfus.yaml", "pyobfus.yml", ".pyobfus.yaml", ".pyobfus.yml"]) {
    const candidate = path.join(dir, name);
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return undefined;
}

export function validationSummary(result: ValidateConfigResult): string {
  if (result.status === "success") {
    return "pyobfus: config is valid.";
  }
  if (result.status === "warnings") {
    return `pyobfus: config is valid with ${result.warnings.length} warning(s).`;
  }
  return `pyobfus: config is invalid with ${result.errors.length} error(s).`;
}

async function showValidationResult(
  result: ValidateConfigResult,
  outputChannel: vscode.OutputChannel,
): Promise<void> {
  outputChannel.appendLine(`[pyobfus] ${result.summary}: ${result.config_path}`);
  for (const error of result.errors) {
    outputChannel.appendLine(error);
  }
  for (const warning of result.warnings) {
    outputChannel.appendLine(warning);
  }
  for (const suggestion of result.suggestions) {
    outputChannel.appendLine(suggestion);
  }

  const message = validationSummary(result);
  if (result.status === "success") {
    void vscode.window.showInformationMessage(message);
    return;
  }

  const choice = result.status === "warnings"
    ? await vscode.window.showWarningMessage(message, "Open pyobfus.yaml", "Show Output")
    : await vscode.window.showErrorMessage(message, "Open pyobfus.yaml", "Show Output");
  if (choice === "Open pyobfus.yaml") {
    const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(result.config_path));
    await vscode.window.showTextDocument(doc, { preview: false });
  } else if (choice === "Show Output") {
    outputChannel.show();
  }
}
