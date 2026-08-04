# VS Code extension design plan (ROADMAP P2-2)

**Status**: M1 **published** 2026-08-04 as `pyobfus` v0.1.0 on the VS Code
Marketplace (publisher `zhurong2020`) —
https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus —
via manual `.vsix` web upload, ~4 days ahead of the original 2026-08-08
gate (see "Marketplace publishing note" below for why). M1's full test
suite (13 tests, including a real contract test against actually-installed
pyobfus) passed in real CI (`.github/workflows/vscode-extension-ci.yml`)
before publish. **M2 code-complete 2026-08-04** (status bar, generate-config
command, right-click obfuscate, Pro trial/unlock funnel commands), held for
release — eligible from **2026-08-06** (2 days after M1's actual publish
date, spacing Marketplace releases from each other the same way PyPI
releases are spaced). 24/24 tests pass locally against the real installed
pyobfus (`PYOBFUS_PYTHON_PATH=venv/bin/python3 npm test`), including 4 new
real-contract tests (trial/license status, `--init --json`, real obfuscate
`--json --dry-run`) and 8 new pure-logic tests for `deriveTier`. M0
(pyobfus core `--json` prerequisites) is still code-complete-but-held, on
its own separate PyPI release-spacing gate (see `docs/ROADMAP.md`'s P2-2
entry / `CLAUDE.md` for the exact date) — M1/M2's early Marketplace
publishing doesn't pull M0 forward, since M0 is a pyobfus-core PyPI release
and the gate exists to space out *that* package's release traffic.
**Recorded**: 2026-08-04

## Marketplace publishing note (2026-08-04)

**Full step-by-step registration process + troubleshooting log**:
[`docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md`](VSCODE_MARKETPLACE_PUBLISHER_SETUP.md)
— what was tried against Azure DevOps org creation (exact errors, both
sign-ins tried, both subscriptions confirmed valid, both attempted fixes),
and the exact manual-upload steps that worked. Summary:

CLI/PAT-based `vsce publish` needs a VS Code Marketplace publisher backed
by an Azure DevOps organization. Azure DevOps org creation hit an
unresolved "no subscription found" error against two valid subscriptions
(both Owner role, Azure Plan) under an M365 Developer Program (E5 sandbox)
tenant — a documented gap where Dev Program subscriptions aren't recognized
as valid Azure DevOps billing anchors, distinct from the "stale
cross-tenant token" failure mode (which has a known fix: force
re-authentication via the Azure Portal directory switcher, not the org
picker inside the DevOps flow itself — tried, did not resolve this case).

Worked around by using the Marketplace web UI directly:
`marketplace.visualstudio.com/manage/publishers/<publisher>` → "New
extension" → "Visual Studio Code" → upload a locally-built `.vsix`
(`npx vsce package --no-dependencies`, run outside the blocked Azure
DevOps path — packaging itself never needed it). This path uses the
Marketplace web session's own auth and never touches Azure DevOps/PAT
machinery. Confirmed working: "[Succeeded] Extension publish on Visual
Studio Marketplace" email + live listing within minutes.

**Consequence for M4** (CI auto-publish on `vscode-v*.*.*` tags): a classic
PAT is off the table for now (org creation is blocked), and the Entra
ID/federated-credential approach still needs an Azure DevOps org too. M4
may need to stay a manual-upload process, or the org-creation bug may
resolve itself later (worth a periodic recheck) — not launch-blocking
since M1 shipped without it.

This is the design doc behind `docs/ROADMAP.md`'s P2-2 entry — same "satellite
package, own design doc" shape as `docs/MCP_PRIMITIVES_DESIGN.md`.

## Why this scope, not the original stub

The roadmap line used to read "Right-click obfuscate + yaml IntelliSense +
status bar," with no research behind it. Before committing 1-2 weeks and
asking the maintainer to register a new external account (VS Code Marketplace
publisher), real market/competitive research was done first:

- **No competitor has a VS Code extension.** PyArmor, Nuitka, and
  Sourcedefender all lack one — pyobfus would be first-mover in "Python code
  protection" on the Marketplace.
- **Real trust risk to design around**: in April 2025, a malicious extension
  literally named "Python Obfuscator for VSCode" (publisher "Mark H") was
  part of a 10-extension malware campaign (XMRig cryptominer via PowerShell
  loader), reaching 300,000+ installs before removal (BleepingComputer / CSO
  Online / ExtensionTotal researcher Yuval Ronen coverage). The "python
  obfuscator" category on the Marketplace currently has a poisoned
  reputation. pyobfus already has real, verifiable trust infrastructure
  (OpenSSF Best Practices badge, PEP 740 attestations, a build-provenance
  manifest, and — as of 2026-08-04 — a tool-description integrity manifest
  for the companion MCP server) that a generic malware clone can't fake; the
  listing needs to say so explicitly, not imply it.
- **2026 VS Code extension trend research**: the highest-adoption
  differentiator pattern is inline diagnostics (Error Lens-style) — and Error
  Lens doesn't generate diagnostics itself, it just re-renders whatever
  already went through VS Code's native `DiagnosticCollection` API.
  `pyobfus --check --json` already returns a fully-formed,
  line/col/severity-tagged risk report today — wiring that into the native
  Diagnostics API is a much stronger hook than "right-click to obfuscate"
  (any competitor could clone that trivially) and costs zero core-code
  changes.

## v1 scope (ranked)

1. **Diagnostics** (headline) — `pyobfus --check --json` →
   `vscode.languages.createDiagnosticCollection`. `high/medium/low/info` →
   `Error/Warning/Information/Hint`. Triggered on save (debounced) + manual
   command.
2. **"pyobfus: Reverse Stack Trace"** — wraps
   `--unmap --trace <selection|clipboard|file> --mapping <picked> --json`
   (already fully JSON-ready). Reinforces the "AI-debuggable obfuscation"
   story vs. PyArmor's opaque bytecode.
3. **"pyobfus: Generate pyobfus.yaml"** — wraps `--init --json`.
4. **Right-click "Obfuscate with pyobfus"** — table-stakes parity feature,
   ranked below the above three because it's the weakest differentiator
   (trivially cloneable).
5. **Status bar** — tier (community/trial/pro) + last-check summary; click →
   QuickPick (Run Check / Generate Config / Start Trial / Unlock Pro).
6. **`pyobfus.yaml` YAML IntelliSense** — no JSON Schema exists in the repo
   today; generate one from `ObfuscationConfig`'s 34 fields + `preset` enum,
   register via `redhat.vscode-yaml`'s contributor API.
7. **Trial/Pro funnel copy** — reuse `pyobfus/constants.py`
   (`STRIPE_PAYMENT_LINK`, `$45`, 5-day/no-card trial, 30-day money-back) and
   the MCP server's `_pro_unlock()`/`explain_preset()` tone verbatim, don't
   invent new copy.

**Non-goals for v1**: no LSP (a discrete CLI-invocation-per-check has no
incremental state worth protocol-izing — revisit only if non-VS-Code editor
demand appears), no bundled/vendored Python or pyobfus, no telemetry/network
calls beyond the user-initiated Stripe link (itself a trust asset given the
malware-precedent context), no auto-publish CI until M4.

**Trust positioning** (bake into README/listing copy from v1, not a
follow-up edit): explicitly state "open source, OpenSSF Best Practices
verified, PEP 740 attested releases, build-provenance + tool-integrity
manifests" in the listing description. `displayName`/`publisher` should read
unambiguously as "pyobfus," not a generic "Python Obfuscator" string that
could echo the malicious listing's old name.

## Staged milestones (publish 1-2 days apart, each independently demoable)

- **M0** (pyobfus core, tiny standalone release) — ✅ code-complete
  2026-08-04, held for release. Added `--json` to `pyobfus-trial status` and
  `pyobfus-license status`, returning `get_trial_status()` /
  `get_license_status(masked=True)` verbatim — same pattern as the existing
  `--check --json`/`--unmap --json` code. Chosen over replicating the MCP
  server's `python -c "from pyobfus.trial import ..."` shell-out workaround:
  a versioned `--json` flag is a stable documented contract; a second ad-hoc
  "reach into internal Python module" call site doubles the surface that
  breaks if trial/license internals ever change, for ~zero extra
  implementation cost. 12 new tests
  (`tests/test_trial_cli.py::TestTrialStatusJson`,
  `tests/test_license_cli.py`). Does not block M1.
- **M1** (`vscode-extension/` v0.1.0, first Marketplace publish) — ✅
  **published 2026-08-04** as `pyobfus` v0.1.0, publisher `zhurong2020` —
  https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus.
  Scaffolding + `cli/locate.ts` (interpreter resolution, incl. a
  `PYOBFUS_PYTHON_PATH` env-var source added after a real CI failure) +
  `cli/runner.ts` (execFile + JSON parse) + diagnostics provider +
  reverse-trace command. Demoable standalone: open a file with `eval()`,
  see the squiggle; reverse a mangled trace with one command. 13/13 tests
  green in real CI (`.github/workflows/vscode-extension-ci.yml`), including
  a contract test against an actually-installed pyobfus, not a mock.
  Published via manual `.vsix` web upload, not `vsce publish` — see
  "Marketplace publishing note" above.
- **M2** (v0.2.0) — ✅ **code-complete 2026-08-04**, held for release
  (eligible 2026-08-06). Status bar (`statusBar/statusBarController.ts` +
  `status/tierStatus.ts`'s pure `deriveTier()`) showing tier + last-check
  summary, consuming M0's `pyobfus-trial status --json` /
  `pyobfus-license status --json`; a QuickPick menu (`commands/showMenu.ts`)
  gated by current tier; "Generate pyobfus.yaml" (`commands/
  generateConfig.ts`, wraps `--init --json`); "Obfuscate with pyobfus"
  (`commands/obfuscateFile.ts`, Explorer + editor context menus, wraps the
  main obfuscate command's `--json` success/error shapes, newly typed in
  `cli/types.ts` as `ObfuscateSuccessResult`/`ObfuscateErrorResult`); Pro
  trial/unlock funnel commands (`commands/proFunnel.ts`, copy manually
  synced from `pyobfus/constants.py` — see that file's `DOCS_TO_UPDATE`
  comment, which now names this TS file). A new shared
  `cli/errorReporting.ts` factors out the ENOENT-with-actionable-buttons
  handling these four new commands all need, rather than growing a third
  and fourth near-copy of what M1 already had twice (DiagnosticsProvider
  vs. unmapTrace.ts) — M1's two originals were left untouched. 12 new
  tests: 8 pure-logic (`deriveTier`, every tier-precedence case) + 4 new
  real-contract integration tests (trial/license status, `--init --json`,
  real obfuscate `--json --dry-run`), all passing locally against the
  actual installed pyobfus.
- **M3** (v0.3.0) — YAML IntelliSense: `scripts/generate-schema.py`
  introspects `ObfuscationConfig` → `schemas/pyobfus.schema.json`, CI check
  for schema drift. **Note**: `pyobfus/config_validator.py`'s
  `VALID_SCHEMA` (used by `pyobfus --validate-config`) is separately,
  already confirmed stale — missing `preset` and all v0.5.x Pro keys, so
  `--validate-config` false-warns on configs `--init` itself generates. Real
  bug, **out of scope for this extension** — flagged here so it isn't lost;
  worth its own tiny fix release. This milestone's generated schema must
  NOT be derived from that stale validator.
- **M4+** (later) — CI auto-publish on `vscode-v*.*.*` tags (prefer Entra ID
  auth over a classic PAT given the 2026-12-01 Azure DevOps PAT retirement),
  Open VSX (`ovsx`) publish alongside Marketplace, Verified Publisher badge
  (needs 6mo extension history + 6mo-old domain, not launch-blocking),
  schemastore.org submission.

## Tech stack

TypeScript, esbuild bundling, `@vscode/vsce` for packaging/publish (+
`ovsx` for Open VSX in M4), Mocha + `@vscode/test-electron` for integration
tests (needs `xvfb-run` in CI on Linux), unit tests mock
`child_process.execFile` against the JSON shapes verified live 2026-08-04.
`engines.vscode` floor and the current `ms-python.python` interpreter-API
method names should be checked against that extension's live docs at
implementation time, not hardcoded from stale memory (both move over time).

**No LSP**: explicitly weighed and rejected. LSP earns its complexity when
there's incremental, per-keystroke, in-memory analysis benefiting from a
long-lived server process and multi-client reuse. pyobfus's diagnostics come
from a discrete CLI invocation that shells out, parses a whole file/tree,
and returns a finished JSON report — no incremental state to protocol-ize.

**Interpreter/CLI discovery** (mirrors how Ruff/mypy/Pylint's official
extensions already solve this): `ms-python.python`'s exported API →
`<interpreter> -m pyobfus ...` (module invocation, matches the MCP server's
existing "importable module" reliance rather than assuming a `pyobfus`
binary landed on PATH) → fallback to bare `pyobfus` on PATH →
`pyobfus.pythonPath`/`pyobfus.cliPath` settings escape hatch → actionable
"not installed" notification with an `Install`/`Select Interpreter` prompt.

## Verified JSON contracts (live-checked 2026-08-04, not from memory)

**`pyobfus --check --json`** (`pyobfus/core/preflight.py`, wired in
`pyobfus/cli.py` ~line 2021):
```json
{
  "version": 1, "root": "...", "files_scanned": 1, "parse_errors": [],
  "severity_counts": {"high": 1, "medium": 1, "low": 0, "info": 0},
  "category_counts": {"dynamic_exec": 1, "all_export": 1},
  "frameworks": [], "suggested_preset": null, "suggested_excludes": [],
  "risks": [
    {"category": "dynamic_exec", "severity": "high", "file": "/abs/path/a.py",
     "line": 1, "col": 0, "message": "...", "suggestion": "...", "snippet": ""}
  ],
  "ai_hint": "...", "exit_code": 1
}
```
Severity levels: `high`/`medium`/`low`/`info`.

**`pyobfus --unmap --trace <path|-> --mapping <path> --json`** — already
fully supported:
```json
{
  "version": 1, "mapping": "...",
  "mapping_stats": {"modules": 1, "original_names": 2, "unique_obfuscated": 2},
  "original_trace": "...", "unmapped_trace": "...", "ai_hint": "..."
}
```

**`pyobfus --init --json`** — `{version, config_path, preset, excludes,
frameworks_detected, files_scanned, high_risk_findings, written, status,
ai_hint}`.

**`pyobfus-trial status --json`** (M0, shipped in this doc's session) —
`{"version": 1, "trial_status": {active, expires, expires_formatted,
started, days_remaining, device_id} | null}`.

**`pyobfus-license status --json`** (M0) — `{"version": 1, "device": {...},
"license_status": {key, type, expires, expired, verified_ago_days,
cache_valid, device_id?} | null, "verify_result"?: {valid, message}}`.
Exit code 1 on no-license/expired/failed-verify, matching the pre-existing
text-mode exit-code convention.

**`pyobfus.yaml` schema** — no JSON Schema file exists in the repo today.
Authoritative field list = every attribute of the `ObfuscationConfig`
dataclass (`pyobfus/config.py`, 34 fields) plus the `preset` pseudo-key (13
named presets from `ObfuscationConfig.list_presets()`).

## Critical files

- `pyobfus/core/preflight.py`, `pyobfus/cli.py` (~line 2021) — `--check
  --json` contract, source for the diagnostics provider
- `pyobfus/trial_cli.py`, `pyobfus_pro/cli.py` — M0's `--json` additions
  (done)
- `pyobfus/config.py` (`ObfuscationConfig`, `list_presets()`) — M3 schema
  source of truth
- `pyobfus/constants.py`, `pyobfus_mcp/pyobfus_mcp/tools.py` (`_pro_unlock`,
  `explain_preset`, `start_pro_trial`) — M2 funnel copy to reuse verbatim
- `.github/workflows/ci.yml`, `release.yml` — precedent for the new
  path-filtered CI job and tag-triggered publish workflow M1 will add
