# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pro Edition features (Experimental):
  - AES-256 string encryption with Fernet
  - Anti-debugging checks using sys.gettrace()
  - Runtime decryption infrastructure
- Infrastructure name preservation in obfuscation
- Docstring preservation for module/function/class definitions

### Fixed
- Infrastructure function names now properly excluded from obfuscation
- F-strings properly handled (skipped from string encryption)
- Module-level string encryption execution errors resolved
- Type checking errors in pyobfus_pro (anti_debug.py, string_aes.py) - added explicit type casts

## [0.1.0] - 2025-11-11

### Added
- Core obfuscation engine with AST-based name mangling
- Symbol table analyzer with scope analysis
- Configuration system with YAML support
- Command-line interface with click framework
- Multi-file obfuscation support
- File filtering with glob patterns
- Comment and docstring removal
- Configurable exclusion lists for names and patterns
- Example files demonstrating obfuscation
- Comprehensive test suite (32 tests, 51% coverage)
- GitHub Actions CI/CD pipeline (Ubuntu, Windows, macOS)
- Code quality tooling (black, ruff, mypy)

### Technical Details
- Architecture: AST-based transformation pipeline
- Python Support: 3.8, 3.9, 3.10, 3.11, 3.12
- Naming Scheme: Index-based (I0, I1, I2...)

### Known Limitations
- Cross-file import name mapping not yet implemented
- Recommended for single-file or self-contained modules

## [0.0.1] - 2025-11-10

### Added
- Initial project structure
- Apache 2.0 license
- Basic documentation
