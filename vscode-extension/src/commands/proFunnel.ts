/**
 * "Start 5-Day Pro Trial" / "Unlock Pro Edition" commands (ranked v1 scope
 * item #7 -- reuse pyobfus_mcp's _pro_unlock()/explain_preset() tone and
 * pyobfus/constants.py's values verbatim, don't invent new copy).
 *
 * TypeScript can't import pyobfus/constants.py directly, so these four
 * constants are a manually-synced copy -- see the "DOCS_TO_UPDATE" comment
 * block at the bottom of pyobfus/constants.py, which now names this file.
 */
import * as vscode from "vscode";
import { resolveInterpreter } from "../cli/locate";

const STRIPE_PAYMENT_LINK = "https://buy.stripe.com/00w4gr8ta9F78Fj8oI9k400";
const PRICE_USD = 45;
const MONEY_BACK_DAYS = 30;
const TRIAL_DAYS = 5;

export function registerProFunnelCommands(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("pyobfus.startTrial", startTrial),
    vscode.commands.registerCommand("pyobfus.unlockPro", unlockPro),
  );
}

async function startTrial(): Promise<void> {
  const interpreter = await resolveInterpreter(vscode.workspace.workspaceFolders?.[0]?.uri);
  const terminal = vscode.window.createTerminal("pyobfus trial");
  terminal.show();
  terminal.sendText(`"${interpreter.pythonPath}" -m pyobfus.trial_cli start`);
}

async function unlockPro(): Promise<void> {
  const choice = await vscode.window.showInformationMessage(
    `pyobfus Pro: $${PRICE_USD} one-time, no subscription. ${MONEY_BACK_DAYS}-day money-back guarantee, ` +
      `instant delivery. Prefer to try first? Start a free ${TRIAL_DAYS}-day trial, no card required.`,
    `Buy Pro ($${PRICE_USD})`,
    "Start Free Trial",
  );
  if (choice === `Buy Pro ($${PRICE_USD})`) {
    await vscode.env.openExternal(vscode.Uri.parse(STRIPE_PAYMENT_LINK));
    void vscode.window.showInformationMessage(
      "After checkout, register your license: run 'pyobfus-license register YOUR-KEY' in a terminal.",
    );
  } else if (choice === "Start Free Trial") {
    await vscode.commands.executeCommand("pyobfus.startTrial");
  }
}
