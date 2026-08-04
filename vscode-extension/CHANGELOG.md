# Changelog — pyobfus (VS Code extension)

All notable changes to this extension are documented here. Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Independent version/release cadence from the main `pyobfus` and `pyobfus-mcp` PyPI packages — see `../CHANGELOG.md` and `../pyobfus_mcp/CHANGELOG.md` for those.

## [Unreleased]

**M1 (first release, not yet published).** Full design rationale in
[`docs/VSCODE_EXTENSION_PLAN.md`](../docs/VSCODE_EXTENSION_PLAN.md).

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
