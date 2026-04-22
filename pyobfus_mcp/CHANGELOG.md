# Changelog — pyobfus-mcp

All notable changes to the `pyobfus-mcp` companion package are documented here. Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The main `pyobfus` package changelog lives in the repo root at [CHANGELOG.md](../CHANGELOG.md).

## [0.1.1] — 2026-04-22

### Added

- `server.json` at the package root, conforming to MCP Registry server schema 2025-12-11. Enables programmatic publication to `registry.modelcontextprotocol.io` via the `mcp-publisher` CLI.
- Ownership-verification marker (`<!-- mcp-name: io.github.zhurong2020/pyobfus-mcp -->`) at the top of `README.md`. Required by the MCP Registry to verify that the PyPI package owner controls the `io.github.zhurong2020/` namespace.

### Changed

- Nothing. Metadata-only release — no code or API changes. The tool surface, wire protocol, and behavior are identical to 0.1.0.

### Notes

The upgrade from 0.1.0 is driven purely by MCP Registry requirements: because PyPI disallows overwriting an already-published version, a patch bump is mandatory even though the change is limited to documentation and a new static config file. Future metadata-only revisions will follow the same pattern.

## [0.1.0] — 2026-04-22

### Added

- Initial public release.
- Five MCP tools exposing the pyobfus v0.4.0 AI-native capabilities:
  - `check_obfuscation_risks(path)` — pre-flight risk scan (eval/exec, dynamic attributes, framework reflection)
  - `generate_pyobfus_config(path, preset_override?, write?)` — zero-config project init with framework detection
  - `unmap_stack_trace(trace, mapping_path)` — reverse obfuscated identifiers in production tracebacks
  - `list_presets()` — enumerate community / framework / Pro presets
  - `explain_preset(name)` — describe a preset's effects
- FastMCP adapter in `server.py` with stdio transport (compatible with Claude Desktop, Claude Code, Cursor, Windsurf, Zed).
- Pure-Python tool implementations in `tools.py` — independently testable without the `mcp` SDK installed.
- Configuration snippets for Claude Desktop, Cursor, Windsurf, Zed, and `claude mcp add` in `README.md`.
- 16 tests in `tests/test_tools.py`; all pass without the MCP SDK (the SDK import is lazy in `_build_server()`).
