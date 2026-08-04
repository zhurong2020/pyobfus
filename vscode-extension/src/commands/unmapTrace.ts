/**
 * "pyobfus: Reverse Stack Trace" command. Wraps `pyobfus --unmap --json`,
 * which already returns a fully-formed JSON contract -- no core-code
 * changes needed. See docs/VSCODE_EXTENSION_PLAN.md for why this is a
 * ranked-#2 v1 feature (reinforces the AI-debuggable-obfuscation story).
 */
import * as vscode from "vscode";
import * as os from "node:os";
import * as path from "node:path";
import { randomUUID } from "node:crypto";
import { promises as fs } from "node:fs";
import { resolveInterpreter } from "../cli/locate";
import { runJsonCommand, PyobfusCliError, PyobfusJsonParseError } from "../cli/runner";
import { UnmapResult } from "../cli/types";

export function registerUnmapTraceCommand(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("pyobfus.unmapTrace", () => unmapTrace(outputChannel)),
  );
}

async function unmapTrace(outputChannel: vscode.OutputChannel): Promise<void> {
  const traceText = await getTraceText();
  if (!traceText) {
    void vscode.window.showWarningMessage(
      "pyobfus: no stack trace found. Select text containing the trace, or copy it to the clipboard, then run this command again.",
    );
    return;
  }

  const mappingUris = await vscode.window.showOpenDialog({
    title: "Select the pyobfus mapping.json produced by --save-mapping",
    canSelectMany: false,
    filters: { "Mapping JSON": ["json"] },
  });
  if (!mappingUris || mappingUris.length === 0) {
    return;
  }
  const mappingPath = mappingUris[0].fsPath;

  const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri;
  const interpreter = await resolveInterpreter(workspaceFolder);

  const tmpTraceFile = path.join(os.tmpdir(), `pyobfus-trace-${randomUUID()}.txt`);
  await fs.writeFile(tmpTraceFile, traceText, "utf-8");

  try {
    const result = await runJsonCommand<UnmapResult>(
      interpreter.pythonPath,
      ["-m", "pyobfus", "--unmap", "--trace", tmpTraceFile, "--mapping", mappingPath, "--json"],
      { allowNonZeroExit: false },
    );
    await showUnmappedTrace(result);
  } catch (err) {
    reportError(err, outputChannel);
  } finally {
    await fs.unlink(tmpTraceFile).catch(() => {
      /* best-effort cleanup; a stray temp file is harmless */
    });
  }
}

async function getTraceText(): Promise<string | undefined> {
  const editor = vscode.window.activeTextEditor;
  if (editor && !editor.selection.isEmpty) {
    return editor.document.getText(editor.selection);
  }
  const clipboard = await vscode.env.clipboard.readText();
  return clipboard.trim().length > 0 ? clipboard : undefined;
}

async function showUnmappedTrace(result: UnmapResult): Promise<void> {
  const stats = result.mapping_stats;
  const header =
    `# pyobfus reverse-mapped trace\n` +
    `# mapping: ${result.mapping} (${stats.unique_obfuscated} identifiers, ${stats.modules} module(s))\n\n`;
  const doc = await vscode.workspace.openTextDocument({
    content: header + result.unmapped_trace,
    language: "plaintext",
  });
  await vscode.window.showTextDocument(doc, { preview: false });
  void vscode.window.setStatusBarMessage(
    `pyobfus: reversed ${stats.unique_obfuscated} identifier(s)`,
    5000,
  );
}

function reportError(err: unknown, outputChannel: vscode.OutputChannel): void {
  if (err instanceof PyobfusCliError) {
    outputChannel.appendLine(`[pyobfus] unmap failed: ${err.message}`);
    if (err.stderr) {
      outputChannel.appendLine(err.stderr);
    }
    void vscode.window.showErrorMessage(
      `pyobfus: could not reverse the trace. ${err.stderr.trim() || err.message}`,
    );
    return;
  }
  if (err instanceof PyobfusJsonParseError) {
    outputChannel.appendLine(`[pyobfus] unmap output was not valid JSON: ${err.message}`);
    void vscode.window.showErrorMessage("pyobfus: unexpected output from --unmap. See the pyobfus output channel.");
    return;
  }
  const nodeErr = err as NodeJS.ErrnoException;
  if (nodeErr?.code === "ENOENT") {
    void vscode.window.showErrorMessage(
      "pyobfus: interpreter not found or pyobfus not installed. Set pyobfus.pythonPath or install pyobfus for the active interpreter.",
    );
    return;
  }
  outputChannel.appendLine(`[pyobfus] unexpected error during unmap: ${String(err)}`);
  void vscode.window.showErrorMessage("pyobfus: unexpected error reversing the trace. See the pyobfus output channel.");
}
