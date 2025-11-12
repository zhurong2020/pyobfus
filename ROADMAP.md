# Development Roadmap

This document outlines the planned technical features and improvements for pyobfus.

**Target Users**: Individual developers and small teams
**Positioning**: Free open-source alternative to commercial tools (PyArmor, Oxyry)

---

## Current Status

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

### v0.2.0 - Core Functionality (6-8 weeks)

**Goal**: Fix critical issues, ensure reliable multi-file support

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

**Release Criteria**:
- ✅ All multi-file import patterns work
- ✅ Performance > 1000 LOC/sec
- ✅ Test coverage > 70%
- ✅ Zero critical bugs

---

### v0.3.0 - Enhanced Protection (6-8 weeks)

**Goal**: Increase obfuscation strength, align with PyArmor Basic features

#### P1 - Should Have

**4. Control Flow Obfuscation** ⭐⭐⭐
- **Purpose**: Make code harder to analyze manually
- **Features**:
  - If/else flattening
  - False branch injection
  - Loop transformation
- **Tradeoff**: 10-30% performance overhead
- **Effort**: 2-3 weeks
- **Success**: 100% correctness, < 30% slowdown

**5. String Encryption Enhancement** ⭐⭐⭐
- **Purpose**: Protect sensitive strings (API keys, passwords)
- **Features**:
  - Auto-detect sensitive patterns
  - Multiple algorithms (AES-256, Fernet, XOR)
  - Runtime decryption caching
- **Effort**: 1-2 weeks
- **Success**: 3+ algorithms, > 90% auto-detection accuracy

**6. License Management (Lightweight)** ⭐⭐⭐
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

**7. Junk Code Injection** ⭐⭐
- Insert harmless but realistic-looking code
- Increase manual analysis difficulty
- Effort: 1 week

**8. VSCode Extension** ⭐⭐
- Right-click obfuscation
- Config file intellisense
- Effort: 2-3 weeks

**9. Incremental Obfuscation** ⭐⭐
- Only process changed files
- Result caching
- Effort: 1-2 weeks

**10. Code Compression** ⭐⭐
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

**Last Updated**: November 11, 2025
**Next Review**: After v0.2.0 release
