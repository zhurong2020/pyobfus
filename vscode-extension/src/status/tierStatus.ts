/**
 * Community/Trial/Pro tier detection for the status bar (M2). Shells out to
 * the M0 `--json` endpoints (`pyobfus.trial_cli status`, `pyobfus_pro.cli
 * status`) added specifically so this extension has a stable contract
 * instead of scraping ANSI text -- see docs/VSCODE_EXTENSION_PLAN.md's M0
 * entry.
 *
 * `deriveTier` is a pure function (no I/O) so it can be unit-tested
 * directly; `getTierStatus` is the thin async wrapper that actually shells
 * out, exercised by the real-contract integration test instead.
 */
import * as vscode from "vscode";
import { resolveInterpreter } from "../cli/locate";
import { runJsonCommand } from "../cli/runner";
import { LicenseStatusResult, TrialStatusResult } from "../cli/types";

export type Tier = "pro" | "trial" | "community";

export interface TierStatus {
  tier: Tier;
  /** Only set when tier === "trial". */
  trialDaysRemaining?: number;
  /** Only set when tier === "pro". */
  licenseType?: string;
}

/**
 * Pro (unexpired license) outranks Trial (active trial), which outranks
 * Community (neither, or the CLI calls failed -- an older pyobfus without
 * the M0 `--json` flags, or pyobfus not installed at all, degrades to
 * Community rather than showing an error in the status bar).
 */
export function deriveTier(
  license: LicenseStatusResult | undefined,
  trial: TrialStatusResult | undefined,
): TierStatus {
  const licenseStatus = license?.license_status;
  if (licenseStatus && !licenseStatus.expired) {
    return { tier: "pro", licenseType: licenseStatus.type };
  }

  const trialStatus = trial?.trial_status;
  if (trialStatus?.active) {
    return { tier: "trial", trialDaysRemaining: trialStatus.days_remaining };
  }

  return { tier: "community" };
}

export async function getTierStatus(resource?: vscode.Uri): Promise<TierStatus> {
  const interpreter = await resolveInterpreter(resource);
  const [license, trial] = await Promise.all([
    tryRun<LicenseStatusResult>(interpreter.pythonPath, ["-m", "pyobfus_pro.cli", "status", "--json"]),
    tryRun<TrialStatusResult>(interpreter.pythonPath, ["-m", "pyobfus.trial_cli", "status", "--json"]),
  ]);
  return deriveTier(license, trial);
}

async function tryRun<T>(executable: string, args: string[]): Promise<T | undefined> {
  try {
    return await runJsonCommand<T>(executable, args, { allowNonZeroExit: true });
  } catch {
    // Not installed, older pyobfus without --json, or a transient error --
    // the status bar degrades to Community rather than surfacing an error
    // for what's a best-effort informational display, not a user action.
    return undefined;
  }
}
