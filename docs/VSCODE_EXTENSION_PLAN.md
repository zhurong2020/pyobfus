# VS Code extension design plan (ROADMAP P2-2)

**Status**: M0, M1, and M2 are all **published**, plus an expedited 0.2.1
bugfix patch the same day M2 shipped. **M3** (`pyobfus.yaml` IntelliSense)
is **code-complete, held for its own Marketplace release-spacing gate**
as v0.3.0 — see the dedicated M3 section below.

**0.2.1 bugfix (2026-08-06, same day as M2)**: hands-on testing of the
freshly-published 0.2.0 immediately surfaced a real crash in "Obfuscate
with pyobfus" — `runJsonCommand` never set an explicit `cwd` for
`python -m pyobfus ...`, and `-m` puts cwd first on `sys.path`, so an
ambient cwd (or sibling directory) named `pyobfus` shadows the real
pip-installed package as a namespace package, even against a perfectly
good interpreter (reproduced against the maintainer's own
`~/projects/pyobfus` symlink to this checkout). The diagnosis briefly
went sideways because the *exact same* Python error text
(`No module named pyobfus.__main__; 'pyobfus' is a package and cannot be
directly executed`) also fires for an unrelated reason — a genuinely
too-old `pyobfus` install predating `-m` module-invocation support,
which is what the maintainer's own real repro (a shared research venv
still carrying `pyobfus==0.2.3` from December 2025) actually hit — `pip
show` was needed to tell the two apart. Fixed both: `runJsonCommand` now
defaults `cwd` to `os.tmpdir()` (safe for `checkFile`/`checkWorkspace`/
`unmapTrace`, confirmed their `--check`/`--unmap` code paths never touch
`pyobfus.yaml` auto-discovery); `obfuscateFile.ts` gets a dedicated
`cwdForTarget()` since the main obfuscate command *does* auto-discover
`pyobfus.yaml` from cwd; `reportCliError` gained `isStalePyobfusInstall`
to show an actionable "upgrade or select a different interpreter"
message instead of the raw traceback when the stale-install case is
detected. 8 new tests, 32/32 total passing, real CI green. Released
same-day rather than waiting for the usual spacing gate, since it fixes
a genuine crash rather than shipping a routine feature —
https://github.com/zhurong2020/pyobfus/releases/tag/vscode-v0.2.1.

M1 published 2026-08-04 as `pyobfus` v0.1.0 on the VS Code Marketplace
(publisher `zhurong2020`) —
https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus —
via manual `.vsix` web upload, ~4 days ahead of the original 2026-08-08
gate (see "Marketplace publishing note" below for why). M1's full test
suite (13 tests, including a real contract test against actually-installed
pyobfus) passed in real CI (`.github/workflows/vscode-extension-ci.yml`)
before publish.

M0 (`--json` on `pyobfus-trial status` / `pyobfus-license status`) shipped
2026-08-06 as pyobfus **0.5.12** on its own PyPI release-spacing gate (a
pure version-bump/CHANGELOG-promotion release — the code itself had been
merged 2026-08-04).

M2 (status bar, generate-config command, right-click obfuscate, Pro
trial/unlock funnel commands) shipped 2026-08-06 as `vscode-extension`
**v0.2.0** — https://github.com/zhurong2020/pyobfus/releases/tag/vscode-v0.2.0
— on its own Marketplace release-spacing gate (2 days after M1). 24/24
tests passed locally against the real installed pyobfus
(`PYOBFUS_PYTHON_PATH=venv/bin/python3 npm test`), including 4 real-contract
tests (trial/license status, `--init --json`, real obfuscate
`--json --dry-run`) and 8 pure-logic tests for `deriveTier`. Publishing M2
also empirically confirmed the Marketplace's "update an already-listed
extension" flow for the first time — see "Marketplace publishing note"
below, and the fuller writeup in
[`docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md`](VSCODE_MARKETPLACE_PUBLISHER_SETUP.md).
The public listing page's version field flipped to `0.2.0` (confirmed via
a scripted poll of the page's JSON) and the Marketplace's own Manage tab
shows a green checkmark next to the `0.2.0` version row, meaning the
package passed automated validation, not just "uploaded."

**Recorded**: 2026-08-04, updated 2026-08-06

## Marketplace publishing note (2026-08-04, updated 2026-08-06)

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

**Updating an already-published extension (confirmed 2026-08-06, M2 v0.2.0)**:
the "New extension" entry point above is first-publish only. The control
for a *new version of an existing listing* is a "⋯" (three-dot) overflow
menu next to the extension's name on its own listing page — not the
Manage tab, and easy to miss since it's icon-only. "⋯" → "Update" → upload
the new `.vsix` (built the same PAT-free way) → an "It's live!"
confirmation page. The new version then sits in a transient "verifying
`<version>`" state on the Manage tab for a few minutes (confirmed here via
scripted polling of the public listing page's JSON) before both the public
version string and a green checkmark next to the version row (automated
validation passed) appear. Full step-by-step in
[`docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md`](VSCODE_MARKETPLACE_PUBLISHER_SETUP.md)'s
"Updating an already-listed extension" section.

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

- **M0** (pyobfus core, tiny standalone release) — ✅ **shipped 2026-08-06**
  as pyobfus **0.5.12** (code merged 2026-08-04, release itself was a pure
  version-bump/CHANGELOG-promotion once the release-spacing gate passed).
  Added `--json` to `pyobfus-trial status` and
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
- **M2** (v0.2.0) — ✅ **published 2026-08-06** —
  https://github.com/zhurong2020/pyobfus/releases/tag/vscode-v0.2.0.
  Status bar (`statusBar/statusBarController.ts` +
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
- **M3** (v0.3.0) — YAML IntelliSense. Researched and scoped 2026-08-06 —
  see the dedicated section below — the original one-line stub undersold
  both the scope (it grew to include a real core-package bugfix) and how
  small the actual VS Code-side lift turned out to be. ✅ **Published
  2026-08-07** (`vscode-v0.3.0`, GitHub Release published, real CI green,
  Marketplace listing independently confirmed serving
  `"version":"0.3.0"` after the manual "⋯" → Update upload). P2-2's full
  M0-M3 chain is now shipped end to end.
- **M4+** (later) — CI auto-publish on `vscode-v*.*.*` tags (prefer Entra ID
  auth over a classic PAT given the 2026-12-01 Azure DevOps PAT retirement),
  Open VSX (`ovsx`) publish alongside Marketplace, Verified Publisher badge
  (needs 6mo extension history + 6mo-old domain, not launch-blocking),
  schemastore.org submission.

## M3: YAML IntelliSense — design (researched 2026-08-06)

**Goal**: real autocomplete, hover documentation, and inline validation for
`pyobfus.yaml` in VS Code — not just the diagnostics-on-save M1 already
covers, but editing the config file itself.

### The mechanism (researched, not assumed — and revised once more during implementation)

VS Code has no built-in YAML language server; **`redhat.vscode-yaml`
(the YAML Language Server extension) is still the de facto standard** for
JSON-Schema-backed YAML IntelliSense as of this research pass — no newer
built-in alternative has displaced it. The initial research pass surfaced
three ways to associate a schema with a file and picked the middle one
(programmatic registration via `redhat.vscode-yaml`'s own extension API,
`registerContributor`) as primary, with the modeline comment as a
fallback and an "install redhat.vscode-yaml" prompt to handle the
not-installed case.

**That plan changed before any of it got built.** A closer look at
`redhat.vscode-yaml`'s own docs turned up a *fourth*, better option missed
on the first pass: a **purely declarative `contributes.yamlValidation`
contribution point** in `package.json` — the same shape VS Code's own
built-in JSON support already uses for `contributes.jsonValidation`. This
needs zero runtime code, has no activation-order dependency (a real,
documented failure mode of the `registerContributor` API — see
`redhat-developer/vscode-yaml` issue #261, "registerContributor is not
called when yaml file is opened at vscode start"), and is picked up
automatically by `redhat.vscode-yaml` if it's active, with no error and no
effect at all if it isn't. The whole "programmatic registration +
install-prompt" design was replaced by one static array entry:

```json
"contributes": {
  "yamlValidation": [
    { "fileMatch": ["pyobfus.yaml", "pyobfus.yml", ".pyobfus.yaml", ".pyobfus.yml"],
      "url": "./schemas/pyobfus.schema.json" }
  ]
}
```

The modeline comment stays, but demoted to what it always should have
been — a cross-editor / no-extension-installed fallback, not the thing an
install-prompt exists to make more reliable. `redhat.vscode-yaml` is
**not** an `extensionDependencies` (would force-install a ~10MB extension
on every pyobfus user, including the majority who never hand-edit
`pyobfus.yaml`) — with the declarative path, nothing forces it to be one:
absent, the association is simply inert.

The "one-time dismissible install prompt for `redhat.vscode-yaml`" idea
from the first design pass was dropped, not deferred — it existed to
paper over the programmatic-registration API's reliability gap, and that
gap doesn't apply to the declarative mechanism.

**Deliberately out of scope for M3**: submitting to schemastore.org (would
give IntelliSense to `redhat.vscode-yaml` users who don't even have our
extension installed, purely by filename match — genuinely valuable, but a
separate external governance process with a review queue we don't control;
stays on the M4+ list). Also out of scope: a hand-written custom completion
provider — unnecessary, the JSON Schema + existing language server already
covers autocomplete/hover/validation without us reimplementing that logic.

### A real bug found while scoping this, not a hypothetical

Before designing where the schema's *content* comes from, checked what
already validates `pyobfus.yaml` today: `pyobfus/config_validator.py`'s
`VALID_SCHEMA` is a hand-maintained dict, and it has drifted stale —
**missing `preset` entirely (the key `pyobfus --init` itself writes into
every config it generates) and every Pro field added since v0.5.0**
(`selective_opacity`, `scrub_traceback`, `vault`, `seal_code`,
`fingerprint`, `expire_hard`, `period_max_runs`, `opacity_config`,
`bind_device`, `bind_device_id`, `requires_os`, `requires_python_min`,
`requires_arch`, `embed_data`, `max_workers`, `license_*`,
`control_flow_flattening`, `dead_code_injection`, `import_obfuscation`,
`anti_debug`, `string_encryption`, `numeric_obfuscation`,
`strip_ai_artifacts`). Reproduced empirically:
```
$ pyobfus --validate-config test_config.yaml   # preset + 2 legit Pro keys
[WARNING] Unknown configuration key: 'obfuscation.preset'
[WARNING] Unknown configuration key: 'obfuscation.selective_opacity'
[WARNING] Unknown configuration key: 'obfuscation.scrub_traceback'
```
This is a **pyobfus core bug**, independent of the VS Code extension and
its own timeline — `--validate-config` false-warns on the exact output of
`--init`, for any user, with or without VS Code involved.

### Design: one source of truth, two consumers

Rather than hand-write a JSON Schema separately (which would just create a
*third* place this can drift, on top of the two that already disagree):

1. A new introspection helper (in `pyobfus/config.py` or a small sibling
   module) derives structured field metadata from `ObfuscationConfig`'s
   actual dataclass fields (`dataclasses.fields()` — type, default) plus
   `ObfuscationConfig.list_presets()` for the `preset` enum. No new
   runtime dependency (writing JSON Schema syntax by hand from introspected
   data doesn't need the `jsonschema` package — only *validating against* a
   schema would, and that validation happens client-side inside VS Code's
   language server, not in our Python code).
2. **Consumer A — fixes the core bug**: `config_validator.py`'s
   `VALID_SCHEMA` is computed from this helper instead of hand-maintained,
   so it cannot go stale again — there's no "regenerate and forget" step
   for this consumer since it's derived live, every call.
3. **Consumer B — the VS Code schema**: a dev-time script (same shape as
   `pyobfus-mcp-verify --generate`'s frozen-at-release-time pattern) walks
   the same introspection data and emits standard JSON Schema draft-07 at
   `vscode-extension/schemas/pyobfus.schema.json`, checked into the repo,
   regenerated + drift-checked in CI at each pyobfus release — the exact
   "shipped a new field, forgot to update the generated artifact" failure
   this whole investigation started from, closed by making the check
   automatic rather than relying on someone remembering.
   Per-field human-readable descriptions (valuable for hover tooltips, the
   actual point of "IntelliSense") aren't recoverable from
   `dataclasses.fields()` alone — Python doesn't expose inline `#` comments
   at runtime — so these need a small, explicitly-maintained
   `FIELD_DESCRIPTIONS` mapping alongside the introspection helper, not
   silently omitted.

### Implementation (code-complete 2026-08-06)

- **pyobfus core**: `pyobfus/config_schema.py` (`describe_fields()` /
  `preset_names()`) + `config_validator.py`'s `VALID_SCHEMA` now computed
  from it. 23 new tests. Shipped as its own PyPI-track item (see the main
  `CHANGELOG.md`'s `[Unreleased]` entry), independent of the extension's
  own release.
- **Schema generator**: `scripts/generate_vscode_schema.py` (repo root,
  imports `pyobfus.config_schema`, not a package runtime dependency) emits
  `vscode-extension/schemas/pyobfus.schema.json` (JSON Schema draft-07,
  `additionalProperties: false` on the `obfuscation` object — deliberate,
  a typo'd key should get a real-time red squiggle, matching
  `config_validator.py`'s existing `COMMON_TYPOS` intent). `--check` mode
  exits 1 on drift; no separate CI workflow step needed for this since
  `tests/test_generate_vscode_schema.py::test_checked_in_schema_file_is_not_stale`
  already runs the same check as a normal pytest test, across the full
  OS/Python matrix the core test job already covers. 9 tests total for the
  generator (schema validity, every dataclass field present, typo/enum/
  type rejection all verified against a real `jsonschema.Draft7Validator`,
  not just structural assertions).
- **vscode-extension**: the `contributes.yamlValidation` entry in
  `package.json` (see above) + `commands/generateConfig.ts`'s
  `addSchemaModelineIfMissing()`, which prepends the modeline to every
  freshly-written `pyobfus.yaml` before opening it (idempotent — checked
  the first line before writing). `SCHEMA_URL` is a public
  `raw.githubusercontent.com` URL, not a local extension-install path —
  a modeline gets written into a file the user may commit to their own
  repo, so it has to keep resolving after this extension updates or is
  uninstalled, or when a teammate without it opens the same file. 5 new
  tests (`test/suite/yamlSchema.test.ts`): the `yamlValidation` manifest
  entry + referenced schema file are well-formed, the modeline gets
  prepended and is idempotent, `SCHEMA_URL` is actually a public HTTPS URL.
  Confirmed the schema file is bundled into the packaged `.vsix`
  (`vsce package --no-dependencies` → `schemas/pyobfus.schema.json`,
  9.49 KB, not excluded by `.vscodeignore`).

**Released 2026-08-07** as `vscode-extension` v0.3.0 alongside `pyobfus`
0.5.13 (the core fix), a day ahead of the originally-projected 2026-08-08
gate, on explicit user request — see `CHANGELOG.md`'s `[0.3.0]` entry.
Tagged `vscode-v0.3.0`, GitHub Release published, 37/37 tests green
including real contract tests against 0.5.13, real CI (CodeQL +
VSCode Extension CI) green. Marketplace upload (the manual "⋯" → Update
flow from `docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md` — still no
CLI/PAT path) done the same day; the public listing was independently
re-checked afterward and confirms `"version":"0.3.0"`. P2-2's M0-M3
milestone chain is complete.

### Estimate vs. actual

Estimated **3-4 days** once the mechanism was researched (down from the
original stub's "1-2 weeks"); actual build, once the simpler declarative
mechanism replaced the original programmatic-registration design, came in
under that — same pattern as M0-M2, where researching the real mechanism
before writing code consistently found a smaller, more robust
implementation than the first-pass estimate assumed.

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
- `pyobfus/config.py` (`ObfuscationConfig`, `list_presets()`) +
  `pyobfus/config_schema.py` (`describe_fields()`) — M3 schema source of
  truth (done); `scripts/generate_vscode_schema.py` is the consumer that
  emits `vscode-extension/schemas/pyobfus.schema.json` from it
- `pyobfus/constants.py`, `pyobfus_mcp/pyobfus_mcp/tools.py` (`_pro_unlock`,
  `explain_preset`, `start_pro_trial`) — M2 funnel copy to reuse verbatim
- `.github/workflows/ci.yml`, `release.yml` — precedent for the new
  path-filtered CI job and tag-triggered publish workflow M1 will add
