# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.4] - 2025-12-22

### Added
- **5-Day Pro Trial** (`pyobfus-trial`): Try Pro features FREE without registration or credit card
  - `pyobfus-trial start` - Start a 5-day trial
  - `pyobfus-trial status` - Check trial status
  - `pyobfus-trial features` - View available Pro features
  - Device-bound trial (one trial per machine)
  - Seamless integration with main CLI (`pyobfus --level pro` works during trial)

- **Trial-Aware CLI**: Main CLI now checks trial status and shows appropriate messages
  - Shows trial expiration warnings
  - Suggests trial start when using `--level pro` without license
  - Updated `--upgrade` command to show trial options

- **New Tests**: Added 16 unit tests for trial management system

### Improved
- **Pro Feature Hints**: Updated hints to mention free trial option
- **Error Messages**: All Pro-related errors now suggest starting a trial

## [0.2.3] - 2025-12-11

### Fixed
- **[P0] Python 3.6-3.11 Compatibility**: Fixed f-string quote handling to work on ALL Python versions
  - Problem: v0.2.2 fix only activated when `compile()` failed, but Python 3.12+ (PEP 701) allows same quotes
  - This meant code generated on Python 3.12+ would fail on Python 3.10 and earlier
  - Solution: ALWAYS normalize f-string quotes for backward compatibility
  - Example: `f'Value: {d['key']}'` → `f'Value: {d["key"]}'` (works on Python 3.6+)

### Added
- **`--upgrade` CLI Command**: New command to display Pro edition features and purchase information
  - Shows feature list, pricing ($45), and purchase link
  - Detects if Pro is already active and shows appropriate status
  - Run `pyobfus --upgrade` to see upgrade options

- **FAQ Section in README**: Added comprehensive FAQ optimized for AI search (GEO/AEO)
  - 10 common questions with detailed answers
  - Comparison tables (pyobfus vs PyArmor, Cython, Nuitka)
  - Troubleshooting guidance

- **Comparison Documentation**: New `docs/COMPARISON.md` with detailed tool comparisons
  - Feature matrices for obfuscation techniques
  - Pricing comparison (3-year TCO)
  - Migration guides from PyArmor and Oxyry

- **Python 3.6+ Compatibility Tests**: Added 3 new tests verifying backward compatibility

### Internal
- **Community Outreach Templates**: Added `docs/internal/COMMUNITY_OUTREACH.md` with Reddit, HN, Awesome Python templates
- **Payment Flow Testing Guide**: Added `docs/internal/PAYMENT_FLOW_TESTING.md` with comprehensive testing checklist

## [0.2.2] - 2025-12-11

### Fixed
- **[P0] F-String Quote Handling Bug**: Fixed syntax errors when obfuscating f-strings containing dictionary subscript access
  - Problem: F-strings like `f'Value: {data['key']}'` could generate invalid code with quote conflicts
  - Solution: Added `_fix_fstring_quotes()` in CodeGenerator that detects and fixes quote conflicts
  - Handles single-quoted f-strings with single-quoted subscripts: `f'..{d['k']}..'` → `f'..{d["k"]}..'`
  - Handles double-quoted f-strings with double-quoted subscripts: `f"..{d["k"]}.."` → `f"..{d['k']}..'`
  - Defensive approach: Only activates when generated code has syntax errors
  - Supports multiple subscripts, nested access, and complex expressions

### Added
- **New Test Suite**: Added `tests/test_generator.py` with 19 comprehensive tests for f-string quote handling
  - Unit tests for quote fix functions
  - Integration tests with full obfuscation pipeline
  - Edge case coverage (nested dicts, multiple subscripts, mixed content)

## [0.2.1] - 2025-12-10

### Added
- **Configuration Templates** (`--init-config`): Generate pre-configured YAML templates for common project types
  - `pyobfus --init-config django` - Django projects with migrations, admin, models exclusions
  - `pyobfus --init-config flask` - Flask projects with blueprints, extensions support
  - `pyobfus --init-config library` - Python libraries with public API preservation
  - `pyobfus --init-config general` - General purpose configuration

- **Configuration Validation** (`--validate-config`): Validate configuration files before use
  - Syntax validation for YAML format
  - Schema validation for configuration options
  - Typo detection with suggestions (e.g., `exclude_pattern` -> `exclude_patterns`)
  - Pro feature warnings when using community level

- **Auto-Discovery of Config Files**: Automatically find configuration without `-c` flag
  - Searches for: `pyobfus.yaml`, `pyobfus.yml`, `.pyobfus.yaml`, `.pyobfus.yml`
  - Supports `pyproject.toml` with `[tool.pyobfus]` section

- **Documentation**: Added `exclude_names Behavior` section in README explaining the relationship between `exclude_names` and `string_encoding`

- **Tests**: Added 28 new unit tests for configuration features and exclude_names behavior

### Clarified
- **exclude_names behavior**: `exclude_names` only affects name obfuscation, not string encoding. Variables in `exclude_names` will have their names preserved, but string values are still Base64 encoded.

## [0.2.0] - 2025-11-19

### Added
- **Cross-File Obfuscation System** - Major architecture upgrade enabling consistent name obfuscation across multiple files:
  - **GlobalSymbolTable**: Centralized symbol tracking with collision detection and validation
  - **ExportDetector**: Automatic detection of exported names (functions, classes, variables) and `__all__` lists
  - **CrossFileOrchestrator**: Two-phase obfuscation pipeline coordinator
    - Phase 1: Project-wide scanning and symbol table construction
    - Phase 2: Coordinated transformation with import rewriting
  - **ImportRewriter**: Rewrites import statements with obfuscated names (`from calc import Calculator` → `from calc import I0`)
  - **AllListUpdater**: Updates `__all__` lists with obfuscated names
  - **ExportedNameTransformer**: Renames exported definitions in their source files
  - **ImportedNameTransformer**: Updates references to imported names
  - **LocalNameTransformer**: Updates references to locally-defined exported names (NEW)

- **Enhanced CLI Integration**:
  - `--cross-file/--no-cross-file` flag: Enable/disable cross-file obfuscation (default: enabled)
  - `--dry-run` flag: Preview obfuscation results without writing files
  - Phase-based progress indicators (Phase 1: Scan, Phase 2: Transform)
  - Statistics display: files discovered, modules, exports
  - Validation warnings for unresolved imports (non-blocking)
  - Legacy single-file mode preserved for backward compatibility

### Fixed
- **[CRITICAL]** Local name references not updated after export renaming
  - Problem: After renaming `run_demo` → `I2`, local calls like `run_demo()` in `if __name__ == '__main__'` remained unchanged
  - Solution: New `LocalNameTransformer` with proper scope tracking
  - Correctly handles parameter scoping (doesn't rename function parameters)
  - Correctly handles local variable shadowing
  - Obfuscated code now executes correctly without NameError

### Technical Details
- **Architecture**: Two-phase obfuscation pipeline (Scan → Transform)
- **Import Resolution**: Handles relative imports, aliased imports, and `__all__` lists
- **Name Mapping**: Global deduplication ensures unique obfuscated names across entire project
- **Scope Handling**: LocalNameTransformer uses scope stack to avoid renaming shadowed names
- **Test Coverage**: 300 tests passing (100%), coverage improved from 16% → 69%
- **New Modules**: 8 new core modules (1,200+ lines of code)
  - `pyobfus/core/global_table.py` (240 lines)
  - `pyobfus/core/export_detector.py` (295 lines)
  - `pyobfus/core/orchestrator.py` (415 lines)
  - `pyobfus/transformers/import_rewriter.py` (279 lines)
  - `pyobfus/transformers/all_list_updater.py` (287 lines)
  - `pyobfus/transformers/exported_name_transformer.py` (363 lines)
  - `pyobfus/transformers/imported_name_transformer.py` (336 lines)
  - `pyobfus/transformers/local_name_transformer.py` (298 lines)

### Testing
- **Test Suite**: 300 tests passing, 1 xfailed, 1 xpassed
- **Coverage**: 69% (up from 16%)
- **New Test Files**:
  - `tests/core/test_global_table.py`: 24 tests
  - `tests/core/test_export_detector.py`: 31 tests
  - `tests/core/test_orchestrator.py`: 29 tests
  - `tests/transformers/test_import_rewriter.py`: 26 tests
  - `tests/transformers/test_all_list_updater.py`: 14 tests
  - `tests/transformers/test_exported_name_transformer.py`: 20 tests
  - `tests/transformers/test_local_name_transformer.py`: 19 tests
- **Integration Testing**: Successfully tested on `examples/multifile` project
- **Execution Verification**: Obfuscated code runs without errors

### Performance
- Multi-file obfuscation: 4 files processed in <1 second
- Phase 1 scan: Instantaneous for small projects (<100ms)
- Phase 2 transform: Linear scaling with file count

### Breaking Changes
- **Cross-file mode now default**: Use `--no-cross-file` to revert to legacy behavior
- **Import statements modified**: Obfuscated imports may break external tools that parse import statements
- **Name collision detection**: Builds may fail if duplicate exported names detected (by design)

### Migration Guide
- **From v0.1.x**: Existing single-file workflows work unchanged
- **Multi-file projects**: Automatic upgrade, no configuration needed
- **Legacy mode**: Add `--no-cross-file` flag to maintain v0.1.x behavior
- **Dry-run testing**: Use `--dry-run` to preview changes before applying

### Known Limitations Resolved
- ✅ Cross-file import name mapping (Issue from v0.1.0) - **FIXED**
- ✅ Local function calls after renaming - **FIXED**

### Example Usage
```bash
# Cross-file obfuscation (default)
pyobfus src/ -o dist/ --verbose

# Dry-run preview
pyobfus src/ -o dist/ --dry-run

# Legacy single-file mode
pyobfus src/ -o dist/ --no-cross-file
```

## [0.1.6] - 2025-11-12

### Added
- **Self-Service Purchase Flow**:
  - Permanent Stripe Payment Link for instant purchases
  - "Buy Now" buttons integrated in documentation
  - Automated license delivery via Resend email service
  - No manual email requests required
  - Purchase link: https://buy.stripe.com/00w4gr8ta9F78Fj8oI9k400

- **Legal & Compliance Documents**:
  - Terms of Service & EULA with comprehensive license terms
  - Refund Policy with 30-day money-back guarantee
  - Privacy Policy with GDPR compliance
  - All policies linked from purchase documentation

- **Pro Feature Promotion**:
  - Non-intrusive Pro feature hints in CLI
  - Shows upgrade information after successful Community edition obfuscation
  - Direct purchase link in CLI output

### Changed
- **Purchase Process**: Simplified from 5 steps to 3 steps
- **GitHub Pages**: Fixed configuration to use /docs directory
- **Documentation**: Updated README.md and docs/index.md with direct purchase links

### Added
- **Pro Features - Complete Test Suite**:
  - 28 comprehensive unit tests for Pro features (AES-256 + Anti-debugging)
  - `tests/test_string_aes.py`: 14 tests for AES-256 string encryption
  - `tests/test_anti_debug.py`: 14 tests for anti-debugging injection
  - `scripts/test_pro_features.py`: Integration testing tool for Pro features
  - Integration testing: 10/10 real-world files pass (100% success rate)
  - Test coverage improved to 59%

- **Pro Feature: AES-256 String Encryption** (Fully Tested):
  - Enterprise-grade string encryption using AES-256-CBC with HMAC authentication
  - Per-file unique encryption key generation
  - Runtime decryption function injection
  - F-string preservation (skips encryption to maintain AST structure)
  - Docstring preservation support
  - Unicode/UTF-8 string support
  - Comprehensive testing on real-world code (616 strings encrypted, ~75KB)

- **Pro Feature: Anti-Debugging Checks** (Fully Tested):
  - Automatic debugger detection using sys.gettrace()
  - Injection into function entry points
  - Smart filtering (skips small functions and infrastructure functions)
  - Async function support
  - Comprehensive testing (35 functions injected in real-world code)

### Added
- **String Encoding (Base64)** - Community Edition feature (Issue #9):
  - Base64 encoding for all string literals in obfuscated code
  - Automatic decoder function injection at module level
  - F-string expression preservation (only static parts encoded)
  - Docstring preservation when `remove_docstrings = False`
  - Unicode string support (UTF-8 encoding/decoding)
  - Statistics reporting (encoded strings, skipped f-strings)
  - New `StringEncoder` transformer in `pyobfus/transformers/string_encoder.py`
  - 15 comprehensive tests covering all string types and edge cases
  - Example demonstration file: `examples/string_encoding.py`

- **Integration Testing Framework** (2025-11-12):
  - Complete framework for testing pyobfus on external projects without PyPI upload
  - New `integration_tests/` directory with pytest test suite
  - Convenient CLI script `scripts/test_ml_research.py` for quick testing
  - Jupyter notebook for interactive testing and debugging
  - Comprehensive documentation: `docs/INTEGRATION_TESTING.md` and `integration_tests/README.md`
  - Successfully tested on 20/20 real-world files from cardiac-ml-research project
  - Immediate bug discovery: Found and fixed Issue #10 in first test run

### Fixed
- **[CRITICAL]** StringEncoder F-string bug causing code generation failure (Issue #10)
  - F-strings with function calls inside were causing `ValueError: Unexpected node inside JoinedStr`
  - Fixed by properly skipping f-string node traversal to preserve AST structure
  - Success rate improved from 50% to 100% on real-world testing (10/10 → 20/20 files)
  - Added comprehensive f-string tests to prevent regression

- **Type Annotation Issues** - Fixed 19 Pylance type checking errors (2025-11-12):
  - Fixed `reportAttributeAccessIssue` in test_issue_8.py (17 errors)
    - Added isinstance() assertions for AST node type narrowing
    - Added None checks for optional AST attributes (vararg, kwarg)
  - Fixed `reportArgumentType` in test_ml_research.py (2 errors)
    - Changed `Path = None` to `Path | None = None` for optional parameters

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
- **Type Annotation Best Practices** added to CONTRIBUTING.md (2025-11-12):
  - Guidelines for optional parameters (`Type | None` instead of `Type = None`)
  - AST node type assertions with isinstance()
  - Optional attribute None checks
  - Common Pylance error resolutions table with solutions

- **Project Structure Cleanup** (2025-11-12):
  - Removed redundant `.local-testing/` directory (50KB+ of personal testing notes)
  - Replaced by formal `integration_tests/` framework with official documentation
  - Archived completed implementation guides to `docs/internal/archive/v0.1.6/`
    - Issue #8 implementation guide (feature completed)
    - Session summaries (2025-11-12, Parts 1 & 2)
  - Established clear documentation lifecycle: Active → In-Progress → Archive
  - Created `PROJECT_CLEANUP_PLAN.md` with cleanup strategy and future guidelines

- Updated docs/ROADMAP.md with detailed plans for addressing Issue #8 and #9
  - Issue #8 (Keyword Arguments): ✅ **COMPLETED** in v0.1.6
  - Issue #9 (Pro Features): Implementation roadmap - v0.1.6 for string encoding, v0.3.0 for control flow/dead code/opaque predicates
- Added future plan references in README.md for known limitations
- Reorganized internal documentation structure with version-specific archives
- Updated PROJECT_STATUS.md with code quality improvements and project structure cleanup

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
