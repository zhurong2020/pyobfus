# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2025-11-12

### Security
- **[HIGH]** Added HMAC-SHA256 signature to license cache to prevent tampering
- **[HIGH]** Implemented device fingerprinting to limit license sharing across devices
- **[MEDIUM]** Reduced cache duration from 30 days to 3 days to minimize offline abuse window

### Added
- `pyobfus_pro.fingerprint` module for device identification
  - `get_device_fingerprint()` - Generate 16-character device fingerprint based on MAC, hostname, and OS
  - `get_device_name()` - Get human-readable device name
  - `get_device_info()` - Get detailed device information
- Cache schema v2 with signature and device_id fields
- Device information display in `pyobfus-license status` command
- 6 new tests for device fingerprinting and cache signing validation

### Changed
- License cache now includes HMAC-SHA256 signature (prevents direct editing)
- License cache now tied to device fingerprint (prevents cross-device use of cached license)
- Cache validity reduced from 30 days to 3 days (reduces offline abuse window)
- `pyobfus_pro.__init__` now exports `get_device_fingerprint` and `get_device_info`

### Fixed
- Legacy cache (v1) from v0.1.2-0.1.3 is still accepted for backward compatibility
- Tampered cache files are automatically detected and deleted
- Cross-device cache usage is properly rejected

### Technical Details
- Cache format upgraded from v1 to v2 with backward compatibility
- Device fingerprint based on SHA-256 hash of MAC address + hostname + OS info
- HMAC secret can be configured via `PYOBFUS_LICENSE_SECRET` environment variable
- Graceful fallback for legacy v1 cache files (will be upgraded on next verification)

### Migration Notes
- Existing users: Run `pyobfus-license status` to automatically upgrade cache to v2
- Device changes (e.g., hostname change, OS reinstall) will require license re-verification
- Cache files from v0.1.3 will work but won't be signed until next online verification

## [0.1.3] - 2025-11-11

### Fixed
- **[CRITICAL]** Added `cryptography` to required dependencies (was optional, causing `pyobfus-license` CLI to fail)
- Fixed `__version__` attribute in `pyobfus/__init__.py` (was 0.1.0, now correctly shows 0.1.3)

### Notes
- v0.1.2 had two critical issues that prevented Pro features and license management from working correctly. All users should upgrade to v0.1.3.

## [0.1.2] - 2025-11-11

### Added
- **License Verification System** (Pro Edition):
  - GitHub-based online license verification with 30-day local caching
  - License management CLI tool (`pyobfus-license`) with commands: register, status, remove, generate
  - Automatic license validation when using `--level pro`
  - Graceful fallback to cached license when offline
  - License key format: PYOB-XXXX-XXXX-XXXX-XXXX (SHA-256 based generation)
  - Support for license expiration and revocation
  - Comprehensive test suite (14 tests) with mock-based online verification testing
- Pro Edition features (Experimental):
  - AES-256 string encryption with Fernet
  - Anti-debugging checks using sys.gettrace()
  - Runtime decryption infrastructure
- Infrastructure name preservation in obfuscation
- Docstring preservation for module/function/class definitions
- Conditional dependency on `astunparse` for Python 3.8 support

### Fixed
- Infrastructure function names now properly excluded from obfuscation
- F-strings properly handled (skipped from string encryption)
- Module-level string encryption execution errors resolved
- Type checking errors in pyobfus_pro (anti_debug.py, string_aes.py) - added explicit type casts
- Pylance type checking issues (parser.py, utils.py) - improved type inference with getattr()
- Python 3.8 CI/CD test failures - added astunparse as conditional dependency

### Security
- **[CRITICAL]** Pro edition features now require valid license verification
  - Closes business model vulnerability where `--level pro` was accessible without payment
  - License verification required before enabling unlimited file/LOC limits
  - Pro features (AES-256 encryption, anti-debugging) gated behind license check
  - Community edition limits (5 files, 1000 LOC) properly enforced for unlicensed users

### Breaking Changes
- **Pro edition now requires license registration**: Users must run `pyobfus-license register YOUR-KEY` before using `--level pro`
- v0.1.1 users with `--level pro` workflows must obtain a license key (see https://github.com/zhurong2020/pyobfus for pricing)

## [0.1.1] - 2025-11-11

### Fixed
- **[CRITICAL]** Method name obfuscation now updates all call sites (Issue #4)
  - Method definitions and external calls (`instance.method()`) now properly synchronized
  - Internal self calls (`self.method()`) correctly obfuscated
  - Fixes AttributeError at runtime caused by incomplete name updates
  - Added method tracking system in analyzer

### Added
- **Configuration Presets** (Issue #5):
  - `preset_safe()`: Production-ready, preserves docstrings and public APIs
  - `preset_balanced()`: Default configuration (current behavior)
  - `preset_aggressive()`: Maximum obfuscation with minimal exclusions
- **Auto-Detection System** (Issue #5):
  - Automatic public API detection via docstrings
  - Naming convention-based detection (methods without leading underscore)
  - Reduces manual configuration by ~90%
  - Enable via `analyzer.enable_auto_detection(True)`
- **Comprehensive Test Suite** (Issue #6):
  - 25 new test cases covering real-world patterns
  - Decorator methods (@property, @staticmethod, @classmethod)
  - Private method obfuscation
  - Large file performance testing (3000+ lines, <2s completion)
  - Context managers, method chaining, lambdas
  - Test coverage: 37% → 54% (+17 percentage points)
  - Test count: 37 → 57 tests (+54%)

### Performance
- Large file obfuscation (3000+ lines): <2 seconds
- Exceeds v0.2.0 performance targets (10s limit) by 5x margin

### Known Limitations
- Class attributes accessed via `cls.attribute` not fully obfuscated (documented with xfail tests)
- Nested class access via `Outer.Inner` requires workaround (use `__dict__['Inner']`)

### Technical Details
- Enhanced analyzer with method tracking and public API detection
- Modified attribute visitor to handle method call obfuscation
- Added `_in_class` flag to distinguish methods from functions

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
