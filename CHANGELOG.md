# Changelog

All notable changes to pyobfus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pro Edition features (Alpha):
  - AES-256 string encryption with Fernet
  - Anti-debugging checks using sys.gettrace()
  - Runtime decryption infrastructure
- Infrastructure name preservation in obfuscation
- Docstring preservation for module/function/class definitions

### Fixed
- Infrastructure function names (_decrypt_str, _ENCRYPTION_KEY, _check_debugger) now excluded from obfuscation
- F-strings properly handled (skipped from string encryption due to AST limitations)
- Module-level string encryption no longer causes execution errors

## [0.1.0] - 2025-11-11

### Added
- Core obfuscation engine with AST-based name mangling
- Symbol table analyzer with scope analysis
- Configuration system with YAML support
- Command-line interface (CLI) with click framework
- Multi-file obfuscation support
- File filtering with glob patterns
- Comment and docstring removal
- Configurable exclusion lists for names and patterns
- Example files demonstrating obfuscation
- Comprehensive test suite (32 tests, 51% coverage)
- GitHub Actions CI/CD pipeline (Ubuntu, Windows, macOS)
- Code quality tooling (black, ruff, mypy)

### Technical Details
- **Architecture**: AST-based transformation pipeline
- **Python Support**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Naming Scheme**: Index-based (I0, I1, I2...)
- **Known Limitations**:
  - Cross-file import name mapping not implemented
  - Recommended for single-file or self-contained modules

### Community Edition Limits
- Maximum 5 files per project
- Maximum 1000 total lines of code
- Basic name obfuscation only

## [0.0.1] - 2025-11-10

### Added
- Initial project structure
- Repository created at https://github.com/zhurong2020/pyobfus
- Apache 2.0 license
- Basic README documentation

---

## Release Notes

### v0.1.0 - Phase 1 Complete

**Release Date**: 2025-11-11
**Development Time**: 1 day (4 implementation sessions)
**Status**: Community Edition functional, Pro Edition alpha

#### Highlights

✅ **Core Functionality**
- Single-file and multi-file obfuscation working
- Configuration-driven with YAML support
- 100% test pass rate (32 tests)

✅ **Quality Assurance**
- Multi-OS testing (Ubuntu, Windows, macOS)
- Python version matrix (3.8-3.12)
- Code quality verified (black, ruff, mypy)
- 51% code coverage with critical paths covered

✅ **Documentation**
- User guide in README.md
- Developer guide in CONTRIBUTING.md
- Working examples provided

#### Known Issues

⚠️ **Phase 1 Limitations**:
- Cross-file import name mapping not implemented (planned for Phase 2)
- Multi-file obfuscation works but may require manual import adjustments
- Community Edition limits not yet enforced (enforcement planned)

#### Pro Edition Status (Alpha)

🔬 **Experimental Features**:
- AES-256 string encryption (working)
- Anti-debugging checks (working)
- Requires `cryptography>=41.0` package
- Not recommended for production use yet

#### Migration Notes

This is the first release. No migration needed.

#### Contributors

- Rong Zhu (@zhurong2020) - Core development

#### Acknowledgments

- Inspired by Opy's AST-based approach
- Clean room implementation (no code copying)
- Born from cardiac-ml-research project needs

---

## Development Milestones

### Week 1-2: Core Engine (2025-11-11)
- Implemented AST parser, analyzer, transformer, generator
- Created name mangling transformer (I0, I1, I2 scheme)
- Built basic CLI with click
- Added 21 unit tests
- Commit: `dfdb779`

### Week 3-4: Configuration & Multi-file (2025-11-11)
- Implemented YAML configuration system
- Added glob pattern file filtering
- Created multi-file obfuscation pipeline
- Built example multi-file project
- Added 11 additional tests (32 total)
- Commit: `dfdb779`

### Week 5-6: Documentation & CI/CD (2025-11-11)
- Created comprehensive CONTRIBUTING.md (538 lines)
- Setup GitHub Actions CI/CD
- Configured code quality tools (black, ruff, mypy)
- Added test coverage reporting (pytest-cov)
- Verified cross-platform compatibility
- Commit: `dfdb779`

### Code Quality Improvements (2025-11-11)
- Fixed all black formatting issues
- Resolved 11 ruff linting errors
- Fixed 5 mypy type checking errors
- Updated pyproject.toml configuration
- Commit: `fe35e58`

### Pro Features Development (2025-11-11)
- Implemented AES-256 string encryption
- Added anti-debugging checks
- Fixed infrastructure name collision bugs
- Created test suite for Pro features
- Status: Alpha (working but not production-ready)

---

## Upcoming Changes

See [ROADMAP.md](ROADMAP.md) for planned features and development timeline.
