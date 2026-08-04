import * as assert from "node:assert";
import { deriveTier } from "../../src/status/tierStatus";
import { LicenseStatusResult, TrialStatusResult } from "../../src/cli/types";

// Pure-logic tests for deriveTier -- no process spawning, no vscode API
// surface, so (unlike getTierStatus itself) these can run under plain
// Node/Mocha as well as the Extension Host harness.

function license(overrides: Partial<NonNullable<LicenseStatusResult["license_status"]>> = {}): LicenseStatusResult {
  return {
    version: 1,
    device: { fingerprint: "abc", name: "host", system: "Linux", release: "6.0", machine: "x86_64", processor: "x86_64" },
    license_status: {
      key: "PYOB-XXXX",
      type: "commercial",
      expires: "2027-01-01",
      expired: false,
      verified_ago_days: 1,
      cache_valid: true,
      ...overrides,
    },
  };
}

function trial(overrides: Partial<NonNullable<TrialStatusResult["trial_status"]>> = {}): TrialStatusResult {
  return {
    version: 1,
    trial_status: {
      active: true,
      expires: "2026-08-09",
      expires_formatted: "2026-08-09",
      started: "2026-08-04",
      days_remaining: 5,
      device_id: "abc",
      ...overrides,
    },
  };
}

suite("status/tierStatus/deriveTier", () => {
  test("no license, no trial -> community", () => {
    assert.deepStrictEqual(deriveTier(undefined, undefined), { tier: "community" });
  });

  test("license present but expired, no trial -> community", () => {
    const result = deriveTier(license({ expired: true }), undefined);
    assert.strictEqual(result.tier, "community");
  });

  test("license present but expired, active trial -> trial (license doesn't block trial fallback)", () => {
    const result = deriveTier(license({ expired: true }), trial({ days_remaining: 2 }));
    assert.strictEqual(result.tier, "trial");
    assert.strictEqual(result.trialDaysRemaining, 2);
  });

  test("unexpired license -> pro, regardless of trial state", () => {
    const result = deriveTier(license({ type: "commercial" }), trial());
    assert.strictEqual(result.tier, "pro");
    assert.strictEqual(result.licenseType, "commercial");
  });

  test("no license, inactive trial record (expired trial) -> community", () => {
    const result = deriveTier(undefined, trial({ active: false }));
    assert.strictEqual(result.tier, "community");
  });

  test("no license, active trial -> trial with days remaining", () => {
    const result = deriveTier(undefined, trial({ days_remaining: 3 }));
    assert.deepStrictEqual(result, { tier: "trial", trialDaysRemaining: 3 });
  });

  test("license_status null (envelope present but no license) -> falls through to trial check", () => {
    const noLicense: LicenseStatusResult = {
      version: 1,
      device: { fingerprint: "abc", name: "host", system: "Linux", release: "6.0", machine: "x86_64", processor: "x86_64" },
      license_status: null,
    };
    const result = deriveTier(noLicense, trial({ days_remaining: 1 }));
    assert.strictEqual(result.tier, "trial");
  });

  test("both undefined (CLI calls failed -- older pyobfus or not installed) -> community, no throw", () => {
    assert.doesNotThrow(() => deriveTier(undefined, undefined));
  });
});
