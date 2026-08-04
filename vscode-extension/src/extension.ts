import * as vscode from "vscode";
import { DiagnosticsProvider } from "./diagnostics/diagnosticsProvider";
import { registerCheckCommands } from "./commands/checkWorkspace";
import { registerUnmapTraceCommand } from "./commands/unmapTrace";
import { registerGenerateConfigCommand } from "./commands/generateConfig";
import { registerObfuscateFileCommand } from "./commands/obfuscateFile";
import { registerProFunnelCommands } from "./commands/proFunnel";
import { registerShowMenuCommand } from "./commands/showMenu";
import { StatusBarController } from "./statusBar/statusBarController";
import { clearInterpreterCache } from "./cli/locate";
import { CheckReport } from "./cli/types";

const ON_SAVE_DEBOUNCE_MS = 500;

export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel("pyobfus");
  context.subscriptions.push(outputChannel);

  const diagnostics = new DiagnosticsProvider(outputChannel);
  context.subscriptions.push(diagnostics);

  const statusBar = new StatusBarController();
  context.subscriptions.push(statusBar);
  const onReport = (report: CheckReport | undefined) => statusBar.setLastReport(report);

  registerCheckCommands(context, diagnostics, onReport);
  registerUnmapTraceCommand(context, outputChannel);
  registerGenerateConfigCommand(context, outputChannel);
  registerObfuscateFileCommand(context, outputChannel);
  registerProFunnelCommands(context);
  registerShowMenuCommand(context, statusBar);

  registerCheckOnSave(context, diagnostics, onReport);
  registerInterpreterChangeListener(context, statusBar);

  void statusBar.refreshTier(vscode.workspace.workspaceFolders?.[0]?.uri);

  outputChannel.appendLine("pyobfus extension activated.");
}

export function deactivate(): void {
  // All disposables are registered via context.subscriptions; nothing
  // extra to clean up here.
}

function registerCheckOnSave(
  context: vscode.ExtensionContext,
  diagnostics: DiagnosticsProvider,
  onReport: (report: CheckReport | undefined) => void,
): void {
  let debounceTimer: NodeJS.Timeout | undefined;

  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      if (document.languageId !== "python") {
        return;
      }
      const enabled = vscode.workspace
        .getConfiguration("pyobfus", document.uri)
        .get<boolean>("checkOnSave", true);
      if (!enabled) {
        return;
      }
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
      debounceTimer = setTimeout(() => {
        void diagnostics.checkAndPublish(document.uri, "file").then(onReport);
      }, ON_SAVE_DEBOUNCE_MS);
    }),
  );
}

/**
 * ms-python.python's active interpreter can change (user switches venv,
 * opens a different workspace folder, etc.) -- invalidate the resolved-
 * interpreter cache so the next check picks up the new one, rather than
 * silently continuing to run against a stale interpreter path.
 */
function registerInterpreterChangeListener(
  context: vscode.ExtensionContext,
  statusBar: StatusBarController,
): void {
  const pythonExtension = vscode.extensions.getExtension("ms-python.python");
  if (!pythonExtension) {
    return;
  }
  void pythonExtension.activate().then(async () => {
    try {
      const { PythonExtension } = await import("@vscode/python-extension");
      const pythonApi = await PythonExtension.api();
      context.subscriptions.push(
        pythonApi.environments.onDidChangeActiveEnvironmentPath(() => {
          clearInterpreterCache();
          // The new interpreter may have a different pyobfus install (or
          // none), which changes trial/license visibility -- refresh
          // rather than showing a stale tier for the previous interpreter.
          void statusBar.refreshTier(vscode.workspace.workspaceFolders?.[0]?.uri);
        }),
      );
    } catch {
      // ms-python's API shape changed or activation failed -- the
      // interpreter cache simply won't auto-invalidate; a reload/restart
      // still picks up the new interpreter, which is an acceptable
      // degradation rather than a hard failure.
    }
  });
}
