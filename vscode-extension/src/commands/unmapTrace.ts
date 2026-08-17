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
import { reportCliError } from "../cli/errorReporting";
import { runJsonCommand } from "../cli/runner";
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

  const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri;
  const mappingHintText = mappingHintSourceText(traceText);
  const defaultMappingUri = mappingDialogDefaultUri(mappingHintText, workspaceFolder);
  const mappingUris = await vscode.window.showOpenDialog({
    title: "Select the pyobfus mapping.json produced by --save-mapping",
    defaultUri: defaultMappingUri,
    canSelectMany: false,
    filters: { "Mapping JSON": ["json"] },
  });
  if (!mappingUris || mappingUris.length === 0) {
    return;
  }
  const mappingPath = mappingUris[0].fsPath;

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
    reportCliError(err, interpreter.pythonPath, outputChannel, "reversing stack trace");
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
  if (clipboard.trim().length > 0) {
    return clipboard;
  }
  return undefined;
}

function mappingHintSourceText(traceText: string): string {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    return traceText;
  }
  return `${traceText}\n${editor.document.getText()}`;
}

export function mappingDialogDefaultUri(
  traceText: string,
  workspaceFolder?: vscode.Uri,
): vscode.Uri | undefined {
  const mappingRef = mappingReferenceFromText(traceText);
  if (!mappingRef) {
    return workspaceFolder;
  }
  if (path.isAbsolute(mappingRef)) {
    return vscode.Uri.file(mappingRef);
  }
  if (!workspaceFolder) {
    return undefined;
  }
  return vscode.Uri.joinPath(workspaceFolder, mappingRef);
}

export function mappingReferenceFromText(text: string): string | undefined {
  const markerMatch = text.match(/^# pyobfus:obfuscated\b.*\bmapping=([^\s]+)/m);
  if (markerMatch) {
    return cleanMappingReference(markerMatch[1]);
  }

  const commandMatch = text.match(/\bpyobfus\s+--unmap\b[^\n\r]*\s--mapping\s+([^\s]+)/);
  if (commandMatch) {
    return cleanMappingReference(commandMatch[1]);
  }
  return undefined;
}

function cleanMappingReference(ref: string): string {
  return ref.replace(/^["']|["'.,;:)]+$/g, "");
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
