# Changelog — pyobfus (VS Code extension)

All notable changes to this extension are documented here. Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Independent version/release cadence from the main `pyobfus` and `pyobfus-mcp` PyPI packages — see `../CHANGELOG.md` and `../pyobfus_mcp/CHANGELOG.md` for those.

## [Unreleased]

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
