# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] - 2026-06-18

**Build-fusion release.** The v0.5 Pro mechanisms are now wired into the main
`pyobfus` CLI as opt-in flags, composing correctly with Core name-mangling and
string-encoding (the interleave validated by the 2026-06-18 design probe: vault
runs as a PRE-pass; opacity and seal as POST-passes over the final mangled
bytecode).

### Added — Pro build flags (single-file / `--no-cross-file`, like existing Pro features)

- **`--selective-opacity`** (P2-1) — AES-256-GCM-encrypt functions marked
  `@opacity(Layer.ENCRYPTED)`; lazy `__code__` materialization at runtime.
- **`--seal-code`** (P2-9) — bytecode integrity seal for `@seal_code` functions,
  hashed against the final obfuscated bytecode (ciphertext for L3 functions).
- **`--vault`** (P2-11) — rewrite `vault_secrets({...})` into an encrypted
  runtime `Vault` (secrets never appear as plaintext in the output).
- **`--scrub-traceback`** (P2-10) — install a production traceback-encrypting
  excepthook; the RSA private key is written to a `<output>.scrub.key.pem`
  sidecar for reversing error IDs with `pyobfus-unscrub`.
- **`--fingerprint <buyer-id>`** (P2-7) — derive a per-buyer deterministic L3
  key for forensic watermarking / piracy traceback.
- **`--expire-hard <ISO-date>`** (P2-8 subset) — inject a module-top expiry
  check that refuses to import past the date.

Note: like the existing Pro AST features (CFF, string-AES, …), these run in
single-file / `--no-cross-file` mode, not cross-file directory mode.

### Deferred to 0.5.2

- `--bind-device` (runtime device-key substitution) and `--period` (run-count
  counter file) — the P2-8 device/period subset needs careful runtime-key AST
  rewriting.
- `--opacity-config` TOML pattern rules — needs name-map coupling so config
  patterns match pre-mangle qualnames; the decorator channel ships now.

### Changed

- README long-description refreshed (the 0.5.0 PyPI page kept the pre-3.8-drop
  text; this release surfaces the corrected Python ≥3.9 / 1016-test copy).

### Testing

- Test suite **1016 → 1024** (+8 end-to-end build-fusion CLI tests). Zero regressions.

## [0.5.0] - 2026-06-18

**Patent milestone release.** The six v0.5 Pro mechanisms that were held back
under an active Chinese invention-patent application (CN 202610712171X, priority
date 2026-05-22) are now public: the application passed preliminary examination
(初步审查合格) on 2026-06-17, securing the priority date, so disclosure no longer
risks the filing.

### Added — Pro Edition mechanisms (patent-targeted)

These ship as the `pyobfus_pro` API, the `pyobfus-unscrub` developer CLI, and
standalone build passes. Fusing them into a single `pyobfus build --flag`
combined run (alongside Core name-mangling) needs additional Core
parameterization and lands in **0.5.1**.

- **Selective Opacity (P2-1)** — per-symbol protection layers (transparent /
  ai-readable / obfuscated / encrypted); L3 functions are AES-256-GCM encrypted
  with lazy `__code__` materialization. `pyobfus_pro.opacity` + `transformers.opacity`.
- **Forensic watermarking (P2-7)** — per-buyer deterministic key derivation
  (`forensic_seed` / `WatermarkRNG` / `derive_layer_key`) for piracy traceback.
- **License binding combo (P2-8)** — device / expiry / run-count binding woven
  into the AES-GCM decryption path (`pyobfus_pro.license_binding`); the license
  gate is the GCM tag check itself, with no separate patchable check.
- **`@seal_code` integrity decorator (P2-9)** — build-time bytecode hash baked
  in; runtime detection of in-memory patching, with layer-aware sealing for L3.
- **`--scrub-traceback` (P2-10)** — production traceback encryption (hybrid
  RSA-2048-OAEP + AES-256-GCM); developer reverses error IDs with the new
  **`pyobfus-unscrub`** CLI.
- **Runtime String Vault (P2-11)** — encrypted KV namespace for runtime secrets
  with lazy per-entry decryption and schema-without-key queries.

### Changed

- **BREAKING: dropped Python 3.8** (EOL 2024-10). `requires-python` is now
  `>=3.9`, removing the recurring `astunparse` CI flakes documented in
  `docs/PYTHON38_COMPATIBILITY.md`.
- Development Status classifier promoted **Beta → Production/Stable**.
- `cryptography>=42.0`; added `tomli` backport for Python < 3.11 (opacity-config
  TOML parser).

### Testing

- Test suite **727 → 1016** (+290 Pro-mechanism tests, 1 skip). Zero regressions.

## [0.4.1] - 2026-06-11

### Added — Core Features

- **Numeric / constant obfuscation (`--numeric-obfuscation`)** — Community-tier AST transformer that replaces integer and float literals with value-preserving opaque expressions, so the original constants no longer appear in shipped source (ROADMAP P2-5). Integers become random XOR / add / sub identities (exact in Python's arbitrary-precision arithmetic, any sign); floats become `float.fromhex(...)` calls (bit-exact round-trip, unlike a naive `a + b` split). Booleans, `None`, strings, bytes, and complex literals are left untouched, as are numeric literals inside `match`/`case` patterns (which must stay literal). Runs after name mangling and string encoding so the emitted `float` builtin reference is never renamed and the hex strings are not re-encoded. 37 new tests covering int/float round-trip exactness, skip rules, and match-case preservation.
- **AI artifact stripping (`--strip-ai-artifacts`)** — Community-tier AST transformer that removes AI-generation *provenance markers* (e.g. `Generated by Claude`, `Co-Authored-By: Claude`, `🤖 Generated with Claude Code`) so code authored with an AI assistant doesn't ship with "this was AI-generated" fingerprints (ROADMAP P2-3). Deliberately conservative for near-zero false positives: only **docstrings** (module/function/class) and **attribution dunders** (`__author__`, `__copyright__`, `__credits__`, `__maintainer__`) whose text matches an unambiguous attribution marker are removed; arbitrary string literals (program data) and conversational AI-tell phrasing are left untouched. Regular comments need no handling — the AST round-trip already drops them. Emptied function/class bodies are backfilled with `pass`. 27 new tests.
- **`python -m pyobfus` module entry point** — Added `pyobfus/__main__.py` so the CLI is invocable as a module via the current interpreter, not only through the `pyobfus` console script on `PATH`. Makes subprocess invocation reliable for tooling (used by the pyobfus-mcp `protect_project` orchestration tool).
- **`--trace-marker` auto-unmap convention** — Opt-in flag (requires `--save-mapping`) that prepends a stable `# pyobfus:obfuscated id=<id> mapping=<file>` header — plus the exact `--unmap` command — to each obfuscated file. An AI agent that lands in an obfuscated file from a traceback immediately knows the artifact is pyobfus output and how to reverse the names. The mapping file gains a deterministic `marker_id` (stable across runs with the same name map) that cross-references the header. Shebang and PEP 263 encoding cookies are preserved; stamping is idempotent. The `--json` obfuscate output gains a `trace_marker_id` field. Comment-only — does not affect execution. 7 new tests.

### Testing

- Test suite **655 → 727** (+37 numeric obfuscation, +27 AI artifact stripping, +7 trace marker, +1 misc). Zero regressions.

## [0.4.0] - 2026-04-22

**AI-native release.** Ten features shipped in one day around a single theme: making pyobfus the Python obfuscator that AI coding agents (Claude Code, Cursor, Windsurf, Zed) can actually use. Reshape v0.4 goals toward adoption + AI-native integration (see `docs/ROADMAP.md`, `docs/AI_INTEGRATION_STRATEGY.md`, `docs/V0.4_EXECUTION_LOG.md`).

### Added — P0 Core Features

- **`pyobfus --check` pre-flight risk scanner** — Detects `eval`/`exec`/`compile`, dynamic `getattr`/`setattr` with non-literal names, `__import__` / `importlib.import_module`, `vars`/`locals`/`globals`/`dir`/`inspect.*`, `.__name__`/`.__qualname__`/`.__class__` string references, `__all__` exports, and `__main__` entry-point guards. Auto-detects imports of FastAPI, Django, Flask, Pydantic, Click, SQLAlchemy and suggests a matching preset. Exit codes: `0` safe / `1` high-risk / `2` parse errors.
- **`pyobfus --unmap` reverse mapping** — Reverses obfuscated identifiers in a production stack trace using a `mapping.json`. Identifier-boundary-aware (no false replacements inside longer names). Solves the "I can't debug obfuscated code with my AI assistant" dead end.
- **`pyobfus --save-mapping PATH`** — Writes a versioned JSON mapping during obfuscation (both single-file and cross-file modes). Format v1 includes pyobfus version, scan root, mode, per-module forward map, and a precomputed reverse index.
- **Framework-aware presets** — `--preset fastapi | django | flask | pydantic | click | sqlalchemy`. All community-tier (free), built on `preset_safe`, with `preserve_param_names=True` and framework-specific `exclude_names` + `exclude_patterns` bundled in.
- **AI-friendly global `--json`** — Every CLI mode (obfuscate, `--check`, `--init`, `--unmap`) emits a stable JSON schema with `version`, `status`, `ai_hint`, and `exit_code` fields. Errors follow `{error_type, message, suggestion, ai_hint, exit_code}`. `ai_hint` contains the single next command for an AI agent to run.
- **`pyobfus --init`** — Zero-config onboarding. Scans project → detects framework → writes `pyobfus.yaml` with the matching preset, auto-assembled `exclude_patterns`, and explanatory comments aimed at both humans and AI assistants.
- **`preset:` YAML key support** — `ObfuscationConfig.from_file()` now accepts a top-level `preset:` that's applied first; other fields override individual settings. `exclude_patterns` and `exclude_names` merge additively. Unknown keys raise a clear `ValueError`.

### Added — P1 AI Ecosystem

- **`pyobfus-mcp` (new sibling package)** — Model Context Protocol server exposing five tools (`check_obfuscation_risks`, `generate_pyobfus_config`, `unmap_stack_trace`, `list_presets`, `explain_preset`) to Claude Desktop, Claude Code, Cursor, Windsurf, Zed, and any MCP-capable agent. See `pyobfus_mcp/README.md`.
- **`llms.txt` + `llms-full.txt`** (llmstxt.org standard) — Concise project overview + full JSON schema reference at the repo root and docs site.
- **AI integration templates** — `templates/ai-integration/` contains drop-in rule files for Claude Code (`CLAUDE.md`), Cursor (`cursor-rules.mdc`, `.cursorrules`), Windsurf, GitHub Copilot, and a generic `AGENTS.md`.
- **`--incremental` flag** — Project-level skip-if-unchanged cache at `<output>/.pyobfus-cache/manifest.json`. Unchanged rebuilds become O(scan) instead of O(transform).

### Changed

- **Package description + keywords** — PyPI description rewritten for keyword density; adds `python-obfuscator`, `py-obfuscator`, `pyobfuscator`, all 6 framework names, `mcp`, `claude-code`, `cursor`, `llm-tools`, `ai-native`. README headline now reads **"pyobfus — the Python obfuscator"** with a pronunciation line to build AI training-corpus association.
- **Development Status classifier** — `3 - Alpha` → `4 - Beta` (consistent with 655 tests / 91% coverage).
- **GitHub repo topics** — 12 new topics including `python-obfuscator`, `mcp-server`, `claude-code`, `cursor`, `pyarmor-alternative`.

### Testing

- Test suite grew **561 → 655** (+94 tests in main package). New test files: `test_preflight.py`, `test_mapping.py`, `test_unmap_cli.py`, `test_framework_presets.py`, `test_json_cli.py`, `test_init_config.py`, `test_incremental.py`. Plus 16 tests in `pyobfus_mcp/tests/test_tools.py`.
- Coverage **90% → 91%**.
- Zero regressions.

### Documentation

- New: `docs/AI_INTEGRATION_STRATEGY.md`, `docs/V0.4_EXECUTION_LOG.md`.
- Updated: `docs/ROADMAP.md` fully reshaped around P0/P1 priorities with effort estimates.
- Updated: `README.md` AI-native features section, `CHANGELOG.md` (this entry).

## [0.3.3] - 2026-03-24

### Added
- **Parallel File Processing**: New `-j/--jobs` CLI option for multi-process obfuscation
  - `-j 0` (default): auto-detect CPU cores
  - `-j 1`: sequential processing
  - `-j N`: use N worker processes
  - Phase 1 (scan) remains sequential; Phase 2 (transform) runs in parallel
  - Real-time progress display with percentage
- **`max_workers`** config option in `ObfuscationConfig` for programmatic control

### Changed
- **Test Coverage**: 56% -> 90% (410 -> 561 tests)
  - Comprehensive CLI tests (single file, directory, cross-file, Pro features, presets)
  - Pro feature path tests using mock (control flow, dead code, string encryption, anti-debug, license embedding)
  - Trial CLI tests (start, status, features commands)
  - Extended analyzer, transformer, plugin, and exception tests

## [0.3.2] - 2025-12-27

### Added
- **Python 3.14 Support**: Full support for Python 3.14 (latest stable release)
  - CI testing on Python 3.8-3.14 across all platforms
  - Updated documentation and SEO keywords
- **Statistics Summary**: New `--stats` CLI flag to display obfuscation statistics
  - Files processed, names obfuscated, strings encoded/encrypted
  - Pro feature counts (control flow, dead code, anti-debug)
- **PyPI Badges**: Version and download count badges in README
- **Dual Licensing Documentation**: Synced Open Core license model across all docs

### Changed
- **Version Management**: Refactored to Single Source of Truth pattern
  - `pyproject.toml` is now the only place version is defined
  - `pyobfus.__version__` reads from package metadata via `importlib.metadata`
  - Removed hardcoded versions from README.md, ROADMAP.md, and other docs
- Improved documentation consistency for Apache 2.0 (core) + Proprietary (Pro) licensing

## [0.3.1] - 2025-12-25

### Fixed
- Fixed mypy type errors in control flow, dead code, and license embedding modules
- Synced `__version__` across all modules

## [0.3.0] - 2025-12-25

### Added
- **License Embedding** (Pro): Embed restrictions directly into obfuscated code
  - `--expire YYYY-MM-DD`: Set expiration date
  - `--bind-machine`: Bind to specific machine
  - `--max-runs N`: Limit executions

- **Configuration Presets**: Simplified setup with pre-built presets
  - `--preset trial/commercial/library/maximum`
  - `--list-presets`: View all presets

- **Control Flow Flattening** (Pro): Transform control flow into state machines
  - Supports if/else, for loops, while loops
  - CLI: `--control-flow`

- **Dead Code Injection** (Pro): Inject unreachable code
  - Four strategies: After Return, False Branches, Opaque Predicates, Decoy Functions
  - CLI: `--dead-code`

### Example
```bash
# Create a 30-day trial version
pyobfus src/ -o dist/ --preset trial

# Commercial distribution with machine binding
pyobfus src/ -o dist/ --preset commercial

# Custom restrictions
pyobfus src/ -o dist/ --expire 2025-12-31 --bind-machine
```

## [0.2.4] - 2025-12-22

### Added
- **5-Day Pro Trial**: Try Pro features FREE without registration
  - `pyobfus-trial start` - Start trial
  - `pyobfus-trial status` - Check status
  - Works seamlessly with main CLI

## [0.2.3] - 2025-12-11

### Fixed
- **[P0] Python 3.6-3.11 Compatibility**: F-string quote handling now works on ALL Python versions

### Added
- `--upgrade` CLI command: Display Pro features and purchase info
- FAQ section in README
- Comparison documentation (`docs/COMPARISON.md`)

## [0.2.2] - 2025-12-11

### Fixed
- **[P0] F-String Quote Bug**: Fixed syntax errors with dictionary subscripts in f-strings

## [0.2.1] - 2025-12-10

### Added
- **Configuration Templates**: `pyobfus --init-config django/flask/library/general`
- **Configuration Validation**: `pyobfus --validate-config`
- **Auto-Discovery**: Automatically find `pyobfus.yaml` without `-c` flag

## [0.2.0] - 2025-11-19

### Added
- **Cross-File Obfuscation**: Consistent name obfuscation across multiple files
  - Automatic import statement rewriting
  - `__all__` list updates
  - Global symbol table with collision detection

- **CLI Enhancements**:
  - `--cross-file/--no-cross-file` flag (default: enabled)
  - `--dry-run` for preview without writing

### Fixed
- **[CRITICAL]** Local name references now updated after export renaming

### Breaking Changes
- Cross-file mode now default (use `--no-cross-file` for legacy behavior)

## [0.1.6] - 2025-11-12

### Added
- **String Encoding (Base64)**: Community Edition feature
- **Pro Features** (require license):
  - AES-256 String Encryption
  - Anti-Debugging Checks
- **Parameter Preservation**: `--preserve-param-names` for keyword argument support
- Self-service purchase flow with Stripe

### Fixed
- **[CRITICAL]** StringEncoder F-string bug (Issue #10)

## [0.1.5] - 2025-11-12

### Fixed
- **[CRITICAL]** Class attribute renaming inconsistency (Issue #7)

### Added
- Class attribute tracking and consistent renaming

## [0.1.4] - 2025-11-12

### Added
- Device fingerprint for license validation
- Enhanced cache security

## [0.1.3] - 2025-11-11

### Fixed
- Added `cryptography` to required dependencies
- Fixed `__version__` attribute

## [0.1.2] - 2025-11-11

### Added
- **License Verification System** for Pro Edition
- Pro Edition features: AES-256 encryption, Anti-debugging

### Breaking Changes
- Pro edition now requires license registration

## [0.1.1] - 2025-11-11

### Fixed
- **[CRITICAL]** Method name obfuscation now updates all call sites (Issue #4)

### Added
- Configuration presets: `preset_safe()`, `preset_balanced()`, `preset_aggressive()`
- Auto-detection of public APIs

## [0.1.0] - 2025-11-11

### Added
- Core obfuscation engine with AST-based name mangling
- Multi-file obfuscation support
- YAML configuration system
- Command-line interface
- Python 3.8-3.12 support

## [0.0.1] - 2025-11-10

### Added
- Initial project structure
