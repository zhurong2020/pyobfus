/**
 * Status bar item: current tier (Community/Trial/Pro) + last check-result
 * summary. Click opens a QuickPick menu (ranked v1 scope item #5) -- see
 * docs/VSCODE_EXTENSION_PLAN.md.
 */
import * as vscode from "vscode";
import { CheckReport } from "../cli/types";
import { getTierStatus, Tier } from "../status/tierStatus";

const TIER_LABEL: Record<Tier, string> = {
  pro: "Pro",
  trial: "Trial",
  community: "Community",
};

export const SHOW_MENU_COMMAND = "pyobfus.showMenu";

export class StatusBarController implements vscode.Disposable {
  private readonly item: vscode.StatusBarItem;
  private tierStatus: { tier: Tier; trialDaysRemaining?: number } = { tier: "community" };
  private lastReport: CheckReport | undefined;

  constructor() {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.item.name = "pyobfus";
    this.item.command = SHOW_MENU_COMMAND;
    this.render();
    this.item.show();
  }

  dispose(): void {
    this.item.dispose();
  }

  getTier(): Tier {
    return this.tierStatus.tier;
  }

  async refreshTier(resource?: vscode.Uri): Promise<void> {
    this.tierStatus = await getTierStatus(resource);
    this.render();
  }

  setLastReport(report: CheckReport | undefined): void {
    this.lastReport = report;
    this.render();
  }

  private render(): void {
    const tierLabel = TIER_LABEL[this.tierStatus.tier];
    const tierSuffix =
      this.tierStatus.tier === "trial" && this.tierStatus.trialDaysRemaining !== undefined
        ? ` (${this.tierStatus.trialDaysRemaining}d left)`
        : "";

    let checkSuffix = "";
    if (this.lastReport) {
      const { high, medium, low } = this.lastReport.severity_counts;
      const total = high + medium + low;
      checkSuffix = total === 0 ? " $(check)" : ` $(warning) ${total}`;
    }

    this.item.text = `$(shield) pyobfus: ${tierLabel}${tierSuffix}${checkSuffix}`;
    this.item.tooltip = this.buildTooltip(tierLabel, tierSuffix);
  }

  private buildTooltip(tierLabel: string, tierSuffix: string): vscode.MarkdownString {
    const md = new vscode.MarkdownString();
    md.appendMarkdown(`**pyobfus** — Tier: ${tierLabel}${tierSuffix}\n\n`);
    if (this.lastReport) {
      const { high, medium, low } = this.lastReport.severity_counts;
      const total = high + medium + low;
      md.appendMarkdown(
        total === 0
          ? "Last check: no obfuscation risks found.\n\n"
          : `Last check: ${total} finding(s) — ${high} high, ${medium} medium, ${low} low.\n\n`,
      );
    } else {
      md.appendMarkdown("No check run yet this session.\n\n");
    }
    md.appendMarkdown("Click for actions.");
    return md;
  }
}
