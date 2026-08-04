import * as vscode from "vscode";
import { DiagnosticsProvider } from "./diagnostics/diagnosticsProvider";
import { registerCheckCommands } from "./commands/checkWorkspace";
import { registerUnmapTraceCommand } from "./commands/unmapTrace";
import { clearInterpreterCache } from "./cli/locate";

const ON_SAVE_DEBOUNCE_MS = 500;

export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel("pyobfus");
  context.subscriptions.push(outputChannel);

  const diagnostics = new DiagnosticsProvider(outputChannel);
  context.subscriptions.push(diagnostics);

  registerCheckCommands(context, diagnostics);
  registerUnmapTraceCommand(context, outputChannel);

  registerCheckOnSave(context, diagnostics);
  registerInterpreterChangeListener(context);

  outputChannel.appendLine("pyobfus extension activated.");
}

export function deactivate(): void {
  // All disposables are registered via context.subscriptions; nothing
  // extra to clean up here.
}

function registerCheckOnSave(
  context: vscode.ExtensionContext,
  diagnostics: DiagnosticsProvider,
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
        void diagnostics.checkAndPublish(document.uri, "file");
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
function registerInterpreterChangeListener(context: vscode.ExtensionContext): void {
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
