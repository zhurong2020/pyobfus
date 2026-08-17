# Changelog — pyobfus (VS Code extension)

All notable changes to this extension are documented here. Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Independent version/release cadence from the main `pyobfus` and `pyobfus-mcp` PyPI packages — see `../CHANGELOG.md` and `../pyobfus_mcp/CHANGELOG.md` for those.

## [Unreleased]

### Added

- "pyobfus: Reverse Stack Trace" now uses `--trace-marker` metadata to place
  the mapping-file picker: if the selected trace, clipboard trace, or active
  obfuscated file contains `# pyobfus:obfuscated ... mapping=...` or the
  generated `pyobfus --unmap ... --mapping ...` command, the picker opens at
  that mapping path. Without marker metadata it now defaults to the workspace
  folder instead of an arbitrary last-used location.

### Fixed

- "pyobfus: Reverse Stack Trace" now uses the shared CLI error reporter, so
  stale pyobfus installs get the same actionable "Upgrade pyobfus" / "Select
  Interpreter" choices as obfuscation and config-generation commands instead
  of a raw `--unmap` failure message.

## [0.3.0] - 2026-08-07

**M3.** Real IntelliSense (autocomplete, hover docs, inline validation) for
`pyobfus.yaml`: a declarative `contributes.yamlValidation` entry in
`package.json` associates a generated JSON Schema
(`schemas/pyobfus.schema.json`) with `pyobfus.yaml`/`.pyobfus.yaml`/
`pyobfus.yml`/`.pyobfus.yml` for anyone with the
[redhat.vscode-yaml](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
extension active — zero runtime code, no `extensionDependencies`
force-install. "Generate pyobfus.yaml" now also prepends a
`# yaml-language-server: $schema=...` modeline pointing at a stable public
URL (not a local extension-install path, which would go stale on every
extension update) as a cross-editor / no-extension-installed fallback.

The schema itself is generated from `pyobfus/config_schema.py`'s
introspection of `ObfuscationConfig`'s actual dataclass fields (new in
pyobfus core, see the main `CHANGELOG.md`), which also fixed a real core
bug found while scoping this milestone: `--validate-config` used to
false-warn on `preset` and every Pro field added since v0.5.0 because the
old hand-maintained schema had silently drifted stale. 9 new tests for the
schema generator (`tests/test_generate_vscode_schema.py`, pyobfus core) + 5
new tests here (`test/suite/yamlSchema.test.ts`).

## [0.2.1] - 2026-08-06

**Bugfix, found via hands-on testing 2026-08-06.** "Obfuscate with pyobfus"
(and, less commonly, the on-save/manual check commands) could crash with a
confusing raw Python error --
`No module named pyobfus.__main__; 'pyobfus' is a package and cannot be
directly executed` -- because `runJsonCommand` never set an explicit `cwd`
for its `python -m pyobfus ...` invocation. `-m` puts the process's cwd
first on `sys.path`, so an unset/inherited ambient cwd is a hazard: if it
(or a sibling directory) happens to be named `pyobfus` -- e.g. the
maintainer's own `~/projects/pyobfus` symlink to this checkout -- Python
resolves `import pyobfus` to that directory (a namespace package) instead
of the real pip-installed one, even against a perfectly good interpreter.

### Fixed

- `runJsonCommand` now defaults `cwd` to `os.tmpdir()` instead of leaving
  it unset, closing the hazard for every caller that doesn't have a more
  meaningful directory to supply (`checkFile`/`checkWorkspace`'s `--check`
  and `unmapTrace`'s `--unmap` code paths never touch pyobfus's own
  `pyobfus.yaml` auto-discovery, confirmed against `pyobfus/cli.py`, so this
  default is safe for them with no behavior change).
- `obfuscateFile.ts`'s "Obfuscate with pyobfus" is the one call site that
  *does* need a real project-rooted `cwd` -- pyobfus's main obfuscate
  command auto-discovers a project's `pyobfus.yaml` from cwd when
  `--config` isn't passed explicitly, and the safe `os.tmpdir()` default
  would silently skip it. New `cwdForTarget()` resolves the enclosing
  workspace folder when the target is part of one, else the target's own
  directory, matching where a user manually running
  `pyobfus <target> -o <out>` from a terminal would have `cd`-ed to.
- `reportCliError` now recognizes this same Python error text as a
  distinct case (`isStalePyobfusInstall`) and shows an actionable message
  ("pyobfus at `<path>` is too old to run as a module... Upgrade it, or
  select a different interpreter") instead of the raw traceback -- this
  also covers the separate, unrelated way the same error text can appear:
  a genuinely too-old `pyobfus` install (pre-dating `-m pyobfus`
  module-invocation support, added around the v0.4.0 AI-native CLI work),
  found live when the maintainer's own environment resolved a shared
  research venv still carrying `pyobfus==0.2.3` from December 2025.

8 new tests (2 in `cliRunner.test.ts` proving the safe cwd default, 2 real
`--dry-run --verbose` integration tests in `integration.test.ts` proving
`cwdForTarget` correctly preserves `pyobfus.yaml` auto-discovery in both
the workspace-folder and no-workspace-folder cases, 4 pure-logic tests for
`isStalePyobfusInstall`).

## [0.2.0] - 2026-08-06

**M2.** Status bar tier indicator + guided Pro funnel + generate-config +
right-click obfuscate. Full design rationale in
[`docs/VSCODE_EXTENSION_PLAN.md`](../docs/VSCODE_EXTENSION_PLAN.md).

### Added

- Status bar item: current tier (Community/Trial/Pro, from the M0
  `pyobfus-trial status --json` / `pyobfus-license status --json`
  endpoints) + last-check summary (clean / N findings). Click opens a
  QuickPick menu (Check Workspace / Generate Config / Start Trial / Unlock
  Pro — trial and unlock items hidden once already on that tier).
- "pyobfus: Generate pyobfus.yaml" command, wrapping `--init --json`.
- "Obfuscate with pyobfus" command (Explorer context menu on `.py`
  files/folders, editor context menu, and Command Palette) — runs the real
  `pyobfus <input> -o <output> --json` obfuscation with an editable
  default output path, surfaces stats on success, and offers a "Start Free
  Trial" action when a Community-tier `LimitExceededError` is hit.
- "pyobfus: Start 5-Day Pro Trial" / "pyobfus: Unlock Pro Edition"
  commands — reuse `pyobfus/constants.py`'s Stripe link / price / trial
  duration and the MCP server's funnel tone verbatim, not new copy.

### Changed

- Refactored the on-save/manual check commands to report their
  `CheckReport` back to the status bar via an `onReport` callback, so the
  status bar's summary updates the same way the Problems panel does.

## [0.1.0] - 2026-08-04

**M1, first Marketplace release.** Published as `pyobfus` (publisher
`zhurong2020`) on the VS Code Marketplace via manual `.vsix` upload
(`https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus`)
— the Azure DevOps org-creation flow required for CLI/PAT-based `vsce
publish` hit an unresolved "no subscription found" bug against valid M365
Dev Program / Azure Plan subscriptions; the Marketplace web UI's own upload
path sidesteps Azure DevOps entirely and was used instead. Published ~4
days ahead of the original 2026-08-08 release-spacing gate — accepted
because it's this package's independent first-ever release on a separate
distribution channel (VS Code Marketplace, not PyPI), so it doesn't
compete with pyobfus/pyobfus-mcp's own PyPI release cadence. Full design
rationale in [`docs/VSCODE_EXTENSION_PLAN.md`](../docs/VSCODE_EXTENSION_PLAN.md).

### Added

- Inline obfuscation-risk diagnostics: `pyobfus --check --json` findings
  surfaced via VS Code's native `DiagnosticCollection` API on every `.py`
  file save (debounced), plus manual "pyobfus: Check File" / "pyobfus:
  Check Workspace" commands.
- "pyobfus: Reverse Stack Trace" command — select or copy a mangled
  traceback, pick a `mapping.json`, get the reversed trace in a new editor
  tab.
- `pyobfus.pythonPath` / `pyobfus.checkOnSave` settings.
- Interpreter resolution via the `ms-python.python` extension's
  environments API, falling back to a bare `python3`/`python` on PATH.
