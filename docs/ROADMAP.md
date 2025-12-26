# Development Roadmap

This document outlines the planned technical features and improvements for pyobfus.

**Target Users**: Individual developers and small teams
**Positioning**: Free open-source alternative to commercial tools (PyArmor, Oxyry)

---

## Current Status

✅ **v0.3.1 Released** (December 2025)
- **Bug Fixes**: Fixed mypy type errors and Python 3.8 compatibility
- **Version Sync**: All version numbers now consistent across the codebase

✅ **v0.3.0 Released** (December 2025)
- **Control Flow Flattening**: Transform code structure into state machines (Pro)
- **Dead Code Injection**: Inject unreachable code blocks to increase complexity (Pro)
- **License Embedding**: Embed license restrictions directly into obfuscated code (Pro)
  - `--expire YYYY-MM-DD` - Expiration date enforcement
  - `--bind-machine` - Hardware binding with machine fingerprint
  - `--max-runs N` - Runtime execution limits
- **Configuration Presets**: One-command setup for different use cases (Pro)
  - `--preset trial` - 30-day trial with all Pro features
  - `--preset commercial` - Machine binding for commercial distribution
  - `--preset library` - Preserve docstrings for library development
  - `--preset maximum` - All protections enabled
  - `--list-presets` - Show all available presets
- **Test Suite**: 451 tests, 70%+ coverage

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

### v0.3.0 - Control Flow Protection ✅ RELEASED

**Goal**: Implement Control Flow Flattening - the #1 missing feature vs PyArmor

**Status**: ✅ **RELEASED** - v0.3.0 released on December 25, 2025

#### P0 - Must Have (v0.3.0 Core) ✅

**6. Control Flow Flattening** ⭐⭐⭐⭐⭐ ✅ **COMPLETED**
- **Purpose**: Transform code structure to prevent manual analysis
- **Status**: Fully implemented with state machine transformation
- **Features**:
  - ✅ State machine transformation for if/else
  - ✅ Loop flattening (for/while → state machine)
  - ✅ Nested structure support
  - ✅ Switch-case style dispatch
- **CLI**: `pyobfus input.py -o output.py --control-flow`
- **Performance**: ~15% overhead (within acceptable range)
- **Tests**: 25+ unit tests covering all scenarios

**Example Transformation**:
```python
# Before
if x > 0:
    result = x * 2
else:
    result = x / 2
return result

# After (flattened)
_state = 0
while _state != -1:
    if _state == 0:
        _state = 1 if x > 0 else 2
    elif _state == 1:
        result = x * 2
        _state = 3
    elif _state == 2:
        result = x / 2
        _state = 3
    elif _state == 3:
        _state = -1
return result
```

#### P1 - Should Have (v0.3.0 Bonus) ✅

**7. Dead Code Injection** ⭐⭐⭐ ✅ **COMPLETED**
- **Purpose**: Increase code complexity, hinder manual analysis
- **Features**:
  - ✅ Insert unreachable code blocks with opaque predicates
  - ✅ Realistic-looking but non-functional code
  - ✅ Configurable complexity level (3 levels)
- **CLI**: `pyobfus input.py -o output.py --dead-code`
- **Tests**: 15+ unit tests

**8. Opaque Predicates** ⭐⭐⭐ *(Included in Dead Code Injection)*
- Integrated into dead code injection feature
- Uses mathematical invariants for always-false predicates

#### P2 - v0.3.0 Implemented ✅

**9. License Embedding** ⭐⭐⭐ ✅ **COMPLETED**
- **Purpose**: Support commercial distribution of obfuscated code
- **Features**:
  - ✅ Expiration date: `--expire 2026-12-31`
  - ✅ Hardware binding: `--bind-machine`
  - ✅ Usage limits: `--max-runs 100`
- **Implementation**: AST-based injection of license checks
- **Tests**: 24 unit tests

**10. Configuration Presets** ⭐⭐⭐ ✅ **COMPLETED**
- **Purpose**: One-command setup for different use cases
- **Presets**:
  - ✅ `trial` - 30-day trial with all Pro features
  - ✅ `commercial` - Machine binding for commercial distribution
  - ✅ `library` - Preserve docstrings for library development
  - ✅ `maximum` - All protections enabled
- **CLI**: `pyobfus input.py -o output.py --preset commercial`
- **Tests**: 17 unit tests

**Release Criteria**: ✅ ALL MET
- ✅ Control Flow Flattening fully working
- ✅ All existing tests pass (451 tests)
- ✅ Performance impact < 30%
- ✅ Test coverage > 70%

---

### v0.4.0 - Ecosystem (8-10 weeks)

**Goal**: Improve user experience, build community

#### P1 - Should Have

**11. Enhanced Key Obfuscation** ⭐⭐⭐⭐
- **Purpose**: Make encryption key extraction more difficult
- **Background**: Current AES string encryption embeds key directly in code, which can be easily extracted
- **Features**:
  - Key splitting across multiple variables
  - Decoy/fake keys to confuse analysis
  - Key derivation from code structure (e.g., hash of AST)
  - Dynamic key reconstruction at runtime
  - Obfuscated decryption function names
- **Note**: This is a hardening measure, not a security guarantee (see README security notes)
- **Effort**: 1-2 weeks
- **Success**: Significantly increases effort required to extract encryption key

#### P2 - Nice to Have

**12. Junk Code Injection** ⭐⭐
- Insert harmless but realistic-looking code
- Increase manual analysis difficulty
- Effort: 1 week

**13. VSCode Extension** ⭐⭐
- Right-click obfuscation
- Config file intellisense
- Effort: 2-3 weeks

**14. Incremental Obfuscation** ⭐⭐
- Only process changed files
- Result caching
- Effort: 1-2 weeks

**15. Code Compression** ⭐⭐
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

**Marketing & Content**:
- See [MARKETING_PLAN.md](MARKETING_PLAN.md) for detailed content strategy
- X/Twitter presence and engagement
- Reddit r/Python community participation
- Dev.to tutorials and articles
- Track metrics: GitHub stars, PyPI downloads, Pro license sales

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

**Issue #9 - Pro Features Not Implemented**: ✅ **FULLY IMPLEMENTED** (v0.3.0)
- ✅ String Encoding (Base64) - **COMPLETED** (Community Edition)
  - Base64 encoding for all string literals
  - Automatic decoder function injection
  - F-string expression preservation
  - Unicode string support (UTF-8)
  - 15 comprehensive tests covering all string types
- ✅ String Encryption (AES-256) - **COMPLETED** (Pro Edition)
- ✅ Control Flow Flattening - **COMPLETED** (v0.3.0, Pro Edition)
- ✅ Dead Code Injection - **COMPLETED** (v0.3.0, Pro Edition)
- ✅ Opaque Predicates - **COMPLETED** (integrated into Dead Code Injection)
- ✅ License Embedding - **COMPLETED** (v0.3.0, Pro Edition)
- ✅ Configuration Presets - **COMPLETED** (v0.3.0, Pro Edition)

### v0.1.5 (November 12, 2025)

**Issue #7 - Class Attribute Renaming (CRITICAL)**: ✅ **FIXED**
- Class attributes now consistently renamed across all references
- Added comprehensive test coverage

---

**Last Updated**: December 25, 2025
**Next Review**: Before v0.4.0 planning
