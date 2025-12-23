# Development Roadmap

This document outlines the planned technical features and improvements for pyobfus.

**Target Users**: Individual developers and small teams
**Positioning**: Free open-source alternative to commercial tools (PyArmor, Oxyry)

---

## Current Status

✅ **v0.2.4 Released** (December 2025)
- **Trial System**: New `pyobfus-trial` command for testing Pro features
- **HTTP Error Handling Fix**: Fixed exception handling in license verification
- **Test Improvements**: Fixed test mocks for HTTP error simulation
- **Constants Refactoring**: Centralized URLs in `pyobfus/constants.py`
- **Test Suite**: 366 tests, 69% coverage

✅ **v0.2.3 Released** (December 2025)
- **[P0 Bug Fix] Python 3.6-3.11 Compatibility**: Fixed f-string quotes to work on ALL Python versions
- **Always Normalize**: Quote handling now runs unconditionally (not just when compile fails)
- **`--upgrade` CLI Command**: Show Pro edition features and purchase information
- **FAQ Section**: AI-optimized FAQ in README with comparison tables
- **Comparison Page**: New `docs/COMPARISON.md` with detailed tool comparisons
- **Test Suite**: 350 tests, 69% coverage

✅ **v0.2.2 Released** (December 2025)
- **[P0 Bug Fix] F-String Quote Handling**: Fixed syntax errors when obfuscating f-strings with dictionary subscript access
- **Defensive Code Generation**: Added `_fix_fstring_quotes()` to detect and fix quote conflicts automatically
- **New Test Suite**: Added `tests/test_generator.py` with 19 comprehensive tests

✅ **v0.2.1 Released** (December 2025)
- **Configuration Templates**: `pyobfus --init-config django/flask/library/general`
- **Configuration Validation**: `pyobfus --validate-config pyobfus.yaml` with typo detection
- **Auto-Discovery**: Automatically find config files without `-c` flag
- **Documentation**: Clarified `exclude_names` behavior with `string_encoding`
- **Test Suite**: 330+ tests, 69% coverage

✅ **v0.2.0 Released** (November 2025)
- **Cross-File Obfuscation**: Consistent name obfuscation across multiple files
- **Import Rewriting**: Automatic `from module import name` updates
- **Two-Phase Pipeline**: Scan → Transform architecture
- **Test Suite**: 302 tests, 69% coverage

✅ **v0.1.6 Released** (November 2025)
- **Pro Features Production Ready**: AES-256 encryption and anti-debugging fully tested
- **Self-Service Purchase Flow**: Automated Stripe payment with instant license delivery
- **Legal Compliance**: Terms of Service, Refund Policy, Privacy Policy (GDPR compliant)
- **Integration Testing Framework**: Test on real-world projects without PyPI upload
- **String Encoding (Base64)**: Community edition feature with comprehensive testing
- **Test suite**: 112 tests (15 xfailed, 1 xpassed), 59% coverage
- **Pro Edition Support**: License management system with 3-device limit

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

**3. Configuration Enhancement** ⭐⭐⭐⭐ *(Completed in v0.2.1)*
- **Issue**: Configuration requires manual setup, no validation
- **Features**:
  - ✅ **Preset levels**: `preset_safe()`, `preset_balanced()`, `preset_aggressive()` (v0.1.1)
  - ✅ **Auto-detection of public APIs** via docstrings and naming conventions (v0.1.1)
  - ✅ **Project templates**: `pyobfus --init-config django/flask/library/general` (v0.2.1)
  - ✅ **Config validation**: `pyobfus --validate-config` with typo detection (v0.2.1)
  - ✅ **Auto-discovery of config files**: pyobfus.yaml, .pyobfus.yaml, pyproject.toml (v0.2.1)
- **Effort**: 1 week (100% complete)
- **Success**: 4 templates, schema validation, typo detection

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

## Operations & Support Automation

### Phase 1: Professional Email System (Planned - Week 1)

**Goal**: Replace personal Gmail with professional branded email addresses

**Features**:
- ✅ **Cloudflare Email Routing Setup**
  - Create professional email aliases (@pyobfus.dev)
  - `support@pyobfus.dev` - Customer support
  - `sales@pyobfus.dev` - Sales inquiries
  - `license@pyobfus.dev` - License issues
  - `refund@pyobfus.dev` - Refund requests
  - Catch-all forwarding to operational email

- **Benefits**:
  - Professional brand image
  - Clear functional separation
  - Easy to scale with team growth
  - Zero cost (Cloudflare free tier)

- **Effort**: 1 hour setup + documentation update
- **Status**: Planned, ready to implement

### Phase 2: Email Auto-Responder (Planned - Week 2-3)

**Goal**: Automatic acknowledgment and basic support

**Features**:
- **Cloudflare Worker Email Handler**
  - Automatic reply with expected response time
  - Include relevant documentation links
  - Different templates per email type
  - Forward to human for complex issues

- **Auto-Reply Templates**:
  - License support → activation guide + status check instructions
  - Sales inquiry → product information + purchase link
  - Refund request → confirmation + process timeline
  - General support → FAQ links + 24-hour response promise

- **Effort**: 4-6 hours development + testing
- **Status**: Planned, design phase

### Phase 3: Smart Email Processing (Planned - Future)

**Goal**: Intelligent automation and self-service

**Features**:
- **License Status Auto-Query**
  - Extract license key from email content
  - Query Cloudflare KV for status
  - Send detailed status report automatically
  - 90% of license inquiries resolved without human intervention

- **Refund Request Tracking**
  - Auto-log refund requests to D1 database
  - Send confirmation email immediately
  - Create internal task for manual processing
  - Track SLA compliance (2 business days)

- **FAQ Auto-Matching**
  - Parse email content for common questions
  - Match against knowledge base
  - Send relevant articles automatically
  - Reduce support workload by 50%

- **Effort**: 1-2 weeks development
- **Cost**: $5-10/month (D1 + R2 storage)
- **Status**: Future consideration

### Phase 4: Complete Support System (Optional - Long-term)

**Goal**: Enterprise-grade customer support

**Features**:
- Full ticketing system with web interface
- SLA tracking and reporting
- Team collaboration tools
- Customer satisfaction surveys
- Analytics and insights dashboard

- **Effort**: 2-3 weeks development
- **Cost**: $10-20/month
- **Status**: Optional, based on growth

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

**Operations**:
- Professional email system with Cloudflare Email Routing
- Automated customer support responses
- License inquiry self-service automation
- Refund request tracking and management

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

**Last Updated**: December 23, 2025
**Next Review**: After v0.3.0 release
