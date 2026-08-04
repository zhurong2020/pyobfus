/**
 * TypeScript interfaces mirroring pyobfus CLI's `--json` output shapes.
 *
 * These were verified live against a running `pyobfus` CLI (not written
 * from memory) — see docs/VSCODE_EXTENSION_PLAN.md in the repo root for
 * the exact commands and captured output. Keep in sync with
 * pyobfus/core/preflight.py (Risk/PreflightReport) and the JSON branches
 * in pyobfus/cli.py — there is no schema file to codegen from yet.
 */

export type Severity = "high" | "medium" | "low" | "info";

export interface Risk {
  category: string;
  severity: Severity;
  file: string;
  line: number;
  col: number;
  message: string;
  suggestion: string;
  snippet: string;
}

export interface FrameworkHit {
  name: string;
  evidence: string[];
  files: string[];
}

/** `pyobfus --check <path> --json` */
export interface CheckReport {
  version: number;
  root: string;
  files_scanned: number;
  parse_errors: string[];
  severity_counts: Record<Severity, number>;
  category_counts: Record<string, number>;
  frameworks: FrameworkHit[];
  suggested_preset: string | null;
  suggested_excludes: string[];
  risks: Risk[];
  ai_hint: string;
  exit_code: number;
}

/** `pyobfus --init <path> --json` */
export interface InitResult {
  version: number;
  config_path: string;
  preset: string | null;
  excludes: string[];
  frameworks_detected: string[];
  files_scanned: number;
  high_risk_findings: number;
  written: boolean;
  status: "success" | "warnings" | "error";
  ai_hint: string;
}

export interface MappingStats {
  modules: number;
  original_names: number;
  unique_obfuscated: number;
}

/** `pyobfus --unmap --trace <path> --mapping <path> --json` */
export interface UnmapResult {
  version: number;
  mapping: string;
  mapping_stats: MappingStats;
  original_trace: string;
  unmapped_trace: string;
  ai_hint: string;
}

/** `pyobfus-trial status --json` -- see pyobfus/trial.py get_trial_status() */
export interface TrialStatus {
  active: boolean;
  expires: string;
  expires_formatted: string;
  started: string;
  days_remaining: number;
  device_id: string;
}

export interface TrialStatusResult {
  version: number;
  trial_status: TrialStatus | null;
}

/** `pyobfus-license status --json` -- see pyobfus_pro/license.py get_license_status() */
export interface LicenseStatus {
  key: string;
  type: string;
  expires: string;
  expired: boolean;
  verified_ago_days: number;
  cache_valid: boolean;
  device_id?: string;
}

export interface DeviceInfo {
  fingerprint: string;
  name: string;
  system: string;
  release: string;
  machine: string;
  processor: string;
}

export interface VerifyResult {
  valid: boolean;
  message: string;
}

export interface LicenseStatusResult {
  version: number;
  device: DeviceInfo;
  license_status: LicenseStatus | null;
  verify_result?: VerifyResult;
}

/** Shared shape for the two commands' structured error envelope (--json + exception). */
export interface JsonErrorEnvelope {
  version: number;
  status: "error";
  error_type: string;
  message: string;
}
