/**
 * Status bar click target: a QuickPick of the actions the status bar's
 * "Click for actions" tooltip promises. Item set depends on the current
 * tier so a Pro user never sees an upsell for a purchase they already made.
 */
import * as vscode from "vscode";
import { SHOW_MENU_COMMAND, StatusBarController } from "../statusBar/statusBarController";

interface MenuItem extends vscode.QuickPickItem {
  command: string;
}

export function registerShowMenuCommand(
  context: vscode.ExtensionContext,
  statusBar: StatusBarController,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(SHOW_MENU_COMMAND, async () => {
      const tier = statusBar.getTier();
      const items: MenuItem[] = [
        { label: "$(search) Check Workspace for Obfuscation Risks", command: "pyobfus.checkWorkspace" },
        { label: "$(gear) Generate pyobfus.yaml", command: "pyobfus.generateConfig" },
      ];
      if (tier === "community") {
        items.push({
          label: "$(rocket) Start 5-Day Pro Trial",
          detail: "No credit card required.",
          command: "pyobfus.startTrial",
        });
      }
      if (tier !== "pro") {
        items.push({
          label: "$(unlock) Unlock Pro Edition ($45 one-time)",
          detail: "30-day money-back guarantee, instant delivery.",
          command: "pyobfus.unlockPro",
        });
      }

      const picked = await vscode.window.showQuickPick(items, { title: "pyobfus" });
      if (picked) {
        await vscode.commands.executeCommand(picked.command);
      }
    }),
  );
}
