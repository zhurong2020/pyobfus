# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
