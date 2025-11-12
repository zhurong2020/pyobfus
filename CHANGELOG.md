# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **[RESOLVED]** Keyword argument limitation (Issue #8)
  - Added `--preserve-param-names` CLI option to preserve parameter names during obfuscation
  - Function parameter names can now be preserved while still obfuscating function bodies
  - Enables keyword arguments to work correctly in obfuscated code
  - Supports all parameter types: regular args, keyword-only args, *args, **kwargs, positional-only args
  - Works with async functions and functions with default argument values

### Added
- **Parameter Preservation System** (Issue #8):
  - New `preserve_param_names` configuration option (default: False)
  - `--preserve-param-names` CLI flag for easy activation
  - Parameter name tracking in `SymbolAnalyzer` with new `parameter_names` set
  - Smart name filtering in `NameMangler` to exclude parameters from obfuscation
  - 10 comprehensive tests covering all parameter types and edge cases
- Enhanced `SymbolAnalyzer` to track all function parameter types separately
- Modified `NameMangler.transform()` to filter parameter names when flag is enabled
- Updated `visit_arg()` to skip parameter renaming when preservation is active

### Documentation
- Updated ROADMAP.md with detailed plans for addressing Issue #8 and #9
  - Issue #8 (Keyword Arguments): ✅ **COMPLETED** in v0.1.6
  - Issue #9 (Pro Features): Implementation roadmap - v0.1.6 for string encoding, v0.3.0 for control flow/dead code/opaque predicates
- Added future plan references in README.md for known limitations
- Reorganized internal documentation structure with version-specific archives

### Technical Details
- Parameter names now tracked in dedicated `parameter_names` set in analyzer
- All parameter types handled: args, kwonlyargs, posonlyargs, vararg, kwarg
- Parameter name preservation applies to both function signatures and body references
- Local variables within functions still obfuscated as expected
- Test coverage improved with 10 new tests for keyword argument scenarios

### Infrastructure
- Stripe payment system setup completed (Test Mode)
  - Product created: pyobfus Professional Edition ($45 USD)
  - Test Mode API keys obtained and configured
  - Product logo created and uploaded
  - Configuration files added (.env.stripe.example)
  - Awaiting KYC verification for Live Mode activation

## [0.1.5] - 2025-11-12

### Fixed
- **[CRITICAL]** Class attribute renaming inconsistency causing AttributeError (Issue #7)
  - Class attributes are now tracked and renamed consistently across all references
  - Fixed `ClassName.attribute` references to use renamed attribute names
  - Fixed `cls.attribute` references in classmethods to use renamed names
  - Fixed `self.__class__.attribute` references to use renamed names
  - Added comprehensive test suite with 8 tests covering all class attribute patterns

### Added
- Class attribute tracking in `SymbolAnalyzer`
  - New `class_attributes` dictionary mapping class names to their attributes
  - New `all_class_attributes` set for quick attribute lookup
- Enhanced `visit_Attribute` in `NameMangler` to handle class attributes
- 8 new tests for class attribute obfuscation patterns

### Documentation
- **[IMPORTANT]** Added clear documentation for keyword argument limitation (Issue #8)
  - Keyword arguments cannot be used with obfuscated code (parameter names are renamed)
  - Added examples and workarounds in README
  - Recommended use of positional arguments or `exclude_names` for public APIs
- Clarified Pro features status and roadmap (Issue #9)
  - Clearly marked Free Edition features as "fully implemented"
  - Clearly marked Pro features as "planned for v0.1.6+"
  - Added note that Pro config options are accepted but have no effect currently

### Technical Details
- Analyzer now tracks class-level assignments during AST traversal
- Class attributes are distinguished from instance attributes
- All attribute references (direct, cls, __class__) properly transformed
- Test coverage improved from 38% to 53%

### Migration Notes
- No breaking changes
- Existing code will benefit from automatic class attribute renaming fix
- Users relying on keyword arguments should review README limitations section

## [0.1.4] - 2025-11-12

### Security
- Enhanced license cache integrity protection with cryptographic verification
- Improved device-specific license validation mechanisms
- Optimized cache management policies for better security posture

### Added
- `pyobfus_pro.fingerprint` module for device identification
  - Device fingerprint generation
  - Device name retrieval
  - Detailed device information
- Enhanced cache format with additional security layers
- Device information display in `pyobfus-license status` command
- 6 new security-focused tests for cache validation

### Changed
- License cache now includes enhanced integrity verification
- License validation improved with device-specific checks
- Cache refresh intervals optimized for security
- `pyobfus_pro.__init__` now exports `get_device_fingerprint` and `get_device_info`

### Fixed
- Improved backward compatibility with earlier cache formats
- Better handling of cache validation failures
- Enhanced cross-device license management

### Technical Details
- Cache format upgraded with backward compatibility support
- Device identification based on hardware characteristics
- Security parameters configurable via environment variables
- Graceful handling of legacy cache formats

### Migration Notes
- Existing users: Run `pyobfus-license status` to update cache format automatically
- Seamless upgrade from v0.1.3
- No breaking changes for end users

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
