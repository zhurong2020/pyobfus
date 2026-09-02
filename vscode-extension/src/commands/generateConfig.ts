/**
 * "pyobfus: Generate pyobfus.yaml" command -- wraps `pyobfus --init --json`
 * (ranked v1 scope item #3). No core-code changes needed; --init --json
 * already existed before this extension.
 */
import * as vscode from "vscode";
import * as fs from "fs/promises";
import * as path from "path";
import { resolveInterpreter } from "../cli/locate";
import { runJsonCommand } from "../cli/runner";
import { reportCliError } from "../cli/errorReporting";
import { InitResult } from "../cli/types";

// A public, stable URL -- NOT a local extension-install path. This
// modeline gets written into a file the user may commit to their own
// repo, so it must keep resolving after this extension is updated,
// uninstalled, or opened by a teammate who never installed it at all
// (as long as they have redhat.vscode-yaml, this alone is enough for
// IntelliSense). The declarative `contributes.yamlValidation` entry in
// package.json (a relative `./schemas/...` path, resolved fresh against
// whichever extension version is actually installed) is the primary,
// more robust mechanism for users who do have this extension --  this
// modeline is a cross-editor/no-extension-installed fallback, not the
// main path.
export const SCHEMA_URL =
  "https://raw.githubusercontent.com/zhurong2020/pyobfus/main/vscode-extension/schemas/pyobfus.schema.json";
const SCHEMA_MODELINE = `# yaml-language-server: $schema=${SCHEMA_URL}\n`;

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

    await addSchemaModelineIfMissing(result.config_path, folder.uri.fsPath);

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

/**
 * Prepend the yaml-language-server schema modeline to a freshly-generated
 * pyobfus.yaml -- gives IntelliSense to anyone who opens the file with
 * redhat.vscode-yaml, even without this extension installed at all
 * (this extension's own declarative `contributes.yamlValidation` entry
 * in package.json is the primary, more robust mechanism for users who
 * do have it -- see SCHEMA_URL's comment above). `--init` always writes
 * a fresh file with no prior modeline, so this only guards against a
 * hypothetical future where that stops being true, not a real steady
 * state today.
 */
export async function validateGeneratedConfigPath(configPath: string, workspaceRoot: string): Promise<void> {
  const [realConfigPath, realWorkspaceRoot] = await Promise.all([
    fs.realpath(configPath),
    fs.realpath(workspaceRoot),
  ]);
  const relative = path.relative(realWorkspaceRoot, realConfigPath);
  if (
    path.basename(realConfigPath) !== "pyobfus.yaml" ||
    relative === "" ||
    relative.startsWith(`..${path.sep}`) ||
    path.isAbsolute(relative)
  ) {
    throw new Error("pyobfus returned a config path outside the current workspace");
  }
}

export async function addSchemaModelineIfMissing(
  configPath: string,
  workspaceRoot: string,
): Promise<void> {
  await validateGeneratedConfigPath(configPath, workspaceRoot);
  const uri = vscode.Uri.file(configPath);
  const bytes = await vscode.workspace.fs.readFile(uri);
  const text = Buffer.from(bytes).toString("utf-8");
  if (text.startsWith("# yaml-language-server:")) {
    return;
  }
  await vscode.workspace.fs.writeFile(uri, Buffer.from(SCHEMA_MODELINE + text, "utf-8"));
}
