# Development Roadmap

This document outlines the planned technical features and improvements for pyobfus.

**Target Users**: Individual developers and small teams
**Positioning**: Free open-source alternative to commercial tools (PyArmor, Oxyry)

---

## Current Status

✅ **v0.1.5 Released** (November 2025)
- **Fixed critical class attribute renaming bug** (Issue #7)
- **Documented keyword argument limitation** (Issue #8)
- **Clarified Pro features status** (Issue #9)
- Test suite with **87 tests, 53% coverage**
- Class attribute tracking and consistent renaming
- Enhanced documentation with clear limitations and feature roadmap

✅ **v0.1.1 Released** (November 2025)
- Core obfuscation engine with AST-based name mangling
- Multi-file support with configuration system
- **Fixed critical method obfuscation bug** (Issue #4 - P0)
- **Configuration presets** (safe/balanced/aggressive) - partial completion of v0.2.0 P0#3
- **Auto-detection of public APIs** (reduces manual config by ~90%)
- Test suite with **57 tests, 54% coverage** (+25 tests, +3% coverage vs v0.1.0)
- Large file performance: 3000+ lines in <2 seconds
- CI/CD pipeline for Python 3.8-3.12 across multiple OS
- Published to PyPI
- GitHub Pages documentation live

✅ **v0.1.0 Released** (November 2025)
- Core obfuscation engine with AST-based name mangling
- Multi-file support with configuration system
- Test suite with 32 tests, 51% coverage
- CI/CD pipeline for Python 3.8-3.12 across multiple OS
- Published to PyPI
- GitHub Pages documentation live

📚 **Competitive Analysis**: See [docs/internal/FEATURE_COMPARISON_ROADMAP.md](docs/internal/FEATURE_COMPARISON_ROADMAP.md) for detailed comparison with PyArmor, Oxyry, and other tools.

---

## Version Roadmap

### v0.2.0 - Core Functionality & Initial Pro Features (6-8 weeks)

**Goal**: Fix critical issues, ensure reliable multi-file support, implement basic Pro features

#### P0 - Must Have

**1. Cross-file Import Mapping** ⭐⭐⭐⭐⭐
- **Issue**: Multi-file projects currently fail due to import mapping problems
- **Impact**: Critical - blocks most real-world usage
- **Features**:
  - Global symbol table management
  - Two-phase processing (scan → obfuscate)
  - Import statement rewriting (`from utils import func` → `from I3 import I0`)
  - `__all__` list updates
  - Support for relative/absolute imports
- **Effort**: 2-3 weeks
- **Success**: Django/Flask projects work correctly

**2. Performance Optimization** ⭐⭐⭐⭐
- **Issue**: Large projects (1000+ files) process slowly
- **Target**: > 1000 lines/second, < 500MB memory
- **Features**:
  - Parallel file processing (multiprocessing)
  - AST traversal optimization
  - Progress reporting
  - Performance profiling tools
- **Effort**: 1-2 weeks
- **Success**: 5-10x speed improvement

**3. Configuration Enhancement** ⭐⭐⭐⭐ *(Partially completed in v0.1.1)*
- **Issue**: Configuration requires manual setup, no validation
- **Features**:
  - ✅ **Preset levels**: `preset_safe()`, `preset_balanced()`, `preset_aggressive()` (v0.1.1)
  - ✅ **Auto-detection of public APIs** via docstrings and naming conventions (v0.1.1)
  - 🔲 Project templates: `pyobfus --init-config django/flask/library` (pending)
  - 🔲 Config validation: `pyobfus --validate-config` (pending)
  - 🔲 Auto-discovery of config files (pending)
- **Effort**: 1 week (50% complete)
- **Success**: 4+ templates, 100% accurate validation

**4. Keyword Argument Support** ⭐⭐⭐ *(Addresses Issue #8)*
- **Issue**: Obfuscated functions cannot be called with keyword arguments
- **Impact**: Breaking change for public APIs, library code
- **Features**:
  - Option 1: `--preserve-param-names` flag to preserve all parameter names
  - Option 2: Extend `preserve_patterns` to include parameter names
  - Option 3: Decorator-based control (`@preserve_signature`)
  - Detection and warning for keyword-only arguments
- **Effort**: 1-2 weeks
- **Success**: Public APIs can use keyword arguments, backward compatible

**5. String Encoding (Basic)** ⭐⭐⭐ *(Partial implementation of Issue #9)*
- **Issue**: Pro feature `string_encode` currently has no effect
- **Impact**: Users expect Pro config to work
- **Features**:
  - Base64 encoding for string literals
  - Optional XOR encryption with configurable key
  - Runtime decryption infrastructure
  - License check for Pro features
- **Effort**: 1-2 weeks
- **Success**: String literals are encoded, configurable algorithms

**Release Criteria**:
- ✅ All multi-file import patterns work
- ✅ Performance > 1000 LOC/sec
- ✅ Test coverage > 70%
- ✅ Zero critical bugs

---

### v0.3.0 - Enhanced Protection (6-8 weeks)

**Goal**: Increase obfuscation strength, complete Pro features (Issue #9)

#### P1 - Should Have

**6. Control Flow Obfuscation** ⭐⭐⭐ *(Completes Issue #9 - Pro feature)*
- **Purpose**: Make code harder to analyze manually
- **Issue**: Pro feature `control_flow` currently has no effect
- **Features**:
  - If/else flattening
  - False branch injection
  - Loop transformation
  - While-loop conversion for simple if statements
- **Tradeoff**: 10-30% performance overhead
- **Effort**: 2-3 weeks
- **Success**: 100% correctness, < 30% slowdown

**7. Dead Code Injection** ⭐⭐⭐ *(Completes Issue #9 - Pro feature)*
- **Purpose**: Increase code complexity, hinder manual analysis
- **Issue**: Pro feature `dead_code` currently has no effect
- **Features**:
  - Insert unreachable code blocks
  - Realistic-looking but non-functional code
  - Configurable complexity level
- **Effort**: 1-2 weeks
- **Success**: Code runs correctly, analysis time increased

**8. Opaque Predicates** ⭐⭐⭐ *(Completes Issue #9 - Pro feature)*
- **Purpose**: Obscure control flow with always-true/false conditions
- **Issue**: Pro feature `opaque_predicates` currently has no effect
- **Features**:
  - Mathematical invariants (e.g., x*x >= 0)
  - Complex boolean expressions
  - Hard to detect statically
- **Effort**: 1-2 weeks
- **Success**: Predicates are opaque, no false positives

**9. String Encryption Enhancement** ⭐⭐⭐
- **Purpose**: Protect sensitive strings (API keys, passwords)
- **Features**:
  - Auto-detect sensitive patterns
  - Multiple algorithms (AES-256, Fernet, XOR)
  - Runtime decryption caching
- **Effort**: 1-2 weeks
- **Success**: 3+ algorithms, > 90% auto-detection accuracy

**10. License Management (Lightweight)** ⭐⭐⭐
- **Purpose**: Support commercial distribution
- **Features**:
  - Expiration date: `--expire 2026-12-31`
  - Hardware binding: `--bind-machine`
  - Usage limits: `--max-runs 100`
- **Note**: Basic implementation, not deep protection
- **Effort**: 2-3 weeks
- **Success**: 3 license types working

**Release Criteria**:
- ✅ Medium-level protection strength
- ✅ License features documented
- ✅ Performance impact < 30%

---

### v0.4.0 - Ecosystem (8-10 weeks)

**Goal**: Improve user experience, build community

#### P2 - Nice to Have

**11. Junk Code Injection** ⭐⭐
- Insert harmless but realistic-looking code
- Increase manual analysis difficulty
- Effort: 1 week

**12. VSCode Extension** ⭐⭐
- Right-click obfuscation
- Config file intellisense
- Effort: 2-3 weeks

**13. Incremental Obfuscation** ⭐⭐
- Only process changed files
- Result caching
- Effort: 1-2 weeks

**14. Code Compression** ⭐⭐
- Minify whitespace
- Reduce file size
- Effort: 1 week

---

## What We Won't Do

To maintain focus on core users (individual developers/small teams):

❌ **Deep Bytecode Encryption** - Too complex to maintain
❌ **Compile to C/Machine Code** - Cython already does this well
❌ **Enterprise License Server** - Not our target market
❌ **Compete with PyArmor Pro** - Different price/feature tier

---

## Ongoing Improvements

Throughout all versions:

**Code Quality**:
- Increase test coverage from 51% → 80%+
- Add integration tests for real-world frameworks (Django, Flask)
- Performance benchmarking framework

**Documentation**:
- API reference documentation
- Advanced usage guides (multi-file, Django/Flask integration)
- Architecture documentation for contributors

**Compatibility**:
- Support newer Python versions (3.13+ when released)
- Handle modern Python syntax features (match/case, walrus operator, etc.)
- Improve error messages and debugging

---

## Success Metrics

### v0.2.0 Targets
- GitHub Stars: 100+
- PyPI Downloads: 1K+/month
- Community contributors: 2+

### v0.3.0 Targets
- GitHub Stars: 500+
- PyPI Downloads: 5K+/month
- Community contributors: 5+

### v0.4.0 Targets
- GitHub Stars: 1K+
- PyPI Downloads: 10K+/month
- Active ecosystem (plugins, extensions)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Feature requests can be submitted via GitHub issues with the `enhancement` tag.

For detailed competitive analysis and feature comparison, see [docs/internal/FEATURE_COMPARISON_ROADMAP.md](docs/internal/FEATURE_COMPARISON_ROADMAP.md).

---

## Recent Issues Addressed

### v0.1.6 (November 12, 2025)

**Issue #8 - Keyword Argument Limitation**: ✅ **RESOLVED**
- Added `--preserve-param-names` CLI option to preserve parameter names during obfuscation
- Function parameter names can now be preserved while still obfuscating function bodies
- Supports all parameter types: regular args, keyword-only args, *args, **kwargs, positional-only args
- 10 comprehensive tests covering all parameter types and edge cases
- Documentation updated with usage examples and recommendations

**Issue #9 - Pro Features Not Implemented**: ⏳ **PARTIAL IMPLEMENTATION**
- ✅ String Encoding (Base64) - **COMPLETED** (Community Edition)
  - Base64 encoding for all string literals
  - Automatic decoder function injection
  - F-string expression preservation
  - Unicode string support (UTF-8)
  - 15 comprehensive tests covering all string types
  - Example file demonstrating feature
- 🔲 String Encryption (AES-256) - Planned for future Pro release
- 🔲 Control Flow Obfuscation - Planned for v0.3.0
- 🔲 Dead Code Injection - Planned for v0.3.0
- 🔲 Opaque Predicates - Planned for v0.3.0

### v0.1.5 (November 12, 2025)

**Issue #7 - Class Attribute Renaming (CRITICAL)**: ✅ **FIXED**
- Class attributes now consistently renamed across all references
- Added comprehensive test coverage

---

**Last Updated**: November 12, 2025
**Next Review**: After v0.2.0 release
