/**
 * "pyobfus: Check Workspace/File for Obfuscation Risks" commands -- manual
 * triggers for the same diagnostics pipeline that runs automatically
 * on-save (see extension.ts).
 */
import * as vscode from "vscode";
import { DiagnosticsProvider } from "../diagnostics/diagnosticsProvider";
import { CheckReport } from "../cli/types";

export function registerCheckCommands(
  context: vscode.ExtensionContext,
  diagnostics: DiagnosticsProvider,
  onReport?: (report: CheckReport | undefined) => void,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("pyobfus.checkFile", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.document.languageId !== "python") {
        void vscode.window.showWarningMessage("pyobfus: open a Python file first.");
        return;
      }
      await runCheckWithProgress(diagnostics, editor.document.uri, "file", "Checking file...", onReport);
    }),
    vscode.commands.registerCommand("pyobfus.checkWorkspace", async () => {
      const folder = vscode.workspace.workspaceFolders?.[0];
      if (!folder) {
        void vscode.window.showWarningMessage("pyobfus: open a folder/workspace first.");
        return;
      }
      await runCheckWithProgress(
        diagnostics,
        folder.uri,
        "workspace",
        "Checking workspace for obfuscation risks...",
        onReport,
      );
    }),
  );
}

async function runCheckWithProgress(
  diagnostics: DiagnosticsProvider,
  target: vscode.Uri,
  scope: "file" | "workspace",
  title: string,
  onReport?: (report: CheckReport | undefined) => void,
): Promise<void> {
  await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title }, async () => {
    const report = await diagnostics.checkAndPublish(target, scope);
    onReport?.(report);
    if (!report) {
      return; // error already surfaced by DiagnosticsProvider
    }
    const { high, medium, low } = report.severity_counts;
    const total = high + medium + low;
    if (total === 0) {
      void vscode.window.showInformationMessage("pyobfus: no obfuscation risks found.");
    } else {
      void vscode.window.showInformationMessage(
        `pyobfus: ${total} finding(s) — ${high} high, ${medium} medium, ${low} low. See the Problems panel.`,
      );
    }
  });
}
