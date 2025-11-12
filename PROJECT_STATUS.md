# pyobfus Project Status Snapshot

**Generated**: 2025-11-12
**Current Version**: v0.1.4
**Next Version**: v0.2.0 (in planning)

---

## 📦 Current Release

### v0.1.4 (Live on PyPI)
- **PyPI**: https://pypi.org/project/pyobfus/0.1.4/
- **GitHub Release**: https://github.com/zhurong2020/pyobfus/releases/tag/v0.1.4
- **Release Date**: 2025-11-12
- **Status**: ✅ All systems operational

### What's in v0.1.4 (Security Release)
- **Security**: HMAC-SHA256 cache signing (prevents tampering)
- **Security**: Device fingerprinting (limits license sharing)
- **Security**: 3-day cache TTL (reduced from 30 days)
- **Features**: Device information display in `pyobfus-license status`
- **Tests**: 79 tests passing (2 xfailed), 6 new security tests
- **Compatibility**: Backward compatible with v0.1.3 caches

### Previous Vulnerabilities (FIXED in v0.1.4)
1. ~~Cache tampering~~ → ✅ HMAC signatures detect modifications
2. ~~Offline bypass~~ → ✅ 3-day TTL limits offline abuse
3. ~~No device binding~~ → ✅ Device fingerprinting ties cache to hardware

---

## 🔐 License System Status

### Architecture
- **Type**: GitHub-based (public repository)
- **Repository**: https://github.com/zhurong2020/pyobfus-licenses
- **Cache Format**: v2 (HMAC-signed, device-bound)
- **Cache Location**: `~/.pyobfus/license.json`
- **Cache Duration**: 3 days

### Security Features (v0.1.4)
- ✅ HMAC-SHA256 cache signing
- ✅ Device fingerprinting (MAC + hostname + OS)
- ✅ Tamper detection (auto-delete corrupted cache)
- ✅ Cross-device protection
- ✅ Backward compatible with v1 caches

### CLI Commands
```bash
pyobfus-license register YOUR-KEY    # Register license
pyobfus-license status                # Check status + device info
pyobfus-license status --verify       # Force online verification
pyobfus-license remove                # Remove cached license
```

---

## 📊 Project Metrics

### Code
- **Total Lines**: ~3,500 (pyobfus + pyobfus_pro)
- **Test Coverage**: 52%
- **Tests**: 79 total (77 pass, 2 xfail)
- **Languages**: Python 3.8-3.12

### Quality
- ✅ Black formatted
- ✅ Ruff checked (all errors fixed)
- ✅ Mypy verified (all type errors fixed)
- ✅ GitHub Actions CI passing

### Modules
```
pyobfus/
├── core/           # AST parsing, analysis, generation
├── transformers/   # Name mangling
├── plugins/        # Plugin system (skeleton)
└── cli.py          # Main CLI

pyobfus_pro/
├── license.py      # License verification (v2)
├── fingerprint.py  # Device fingerprinting (NEW in v0.1.4)
├── cli.py          # pyobfus-license tool
├── string_aes.py   # AES-256 encryption
└── anti_debug.py   # Anti-debugging checks
```

### Recent Changes (v0.1.4)
- ➕ Added `pyobfus_pro/fingerprint.py` (80 lines)
- ➕ Added `tests/test_fingerprint.py` (42 lines)
- ✏️ Modified `pyobfus_pro/license.py` (+100 lines)
- ✏️ Modified 8 other files
- 📝 Updated all documentation

---

## 🗂️ Important Files

### Configuration
- `pyproject.toml` - Package metadata, version 0.1.4
- `.gitignore` - Excludes docs/internal/
- `.github/workflows/ci.yml` - CI/CD pipeline

### Documentation
- `README.md` - Main documentation
- `CHANGELOG.md` - Version history (v0.1.4 added)
- `ROADMAP.md` - Long-term vision
- `LICENSE` - Apache 2.0
- `docs/internal/` - Business docs (excludes archived v0.1.4 plans)
- `docs/internal/LICENSE_VERIFICATION_SPEC.md` - Updated with v2 format

### Tests
- `tests/test_license_verification.py` - 20 license tests (6 new)
- `tests/test_fingerprint.py` - 4 device fingerprint tests (NEW)
- `tests/test_issue_*.py` - Issue-specific tests
- `tests/test_core/` - Core functionality tests

### Archive
- `docs/internal/archive/v0.1.4/` - Planning documents (completed)
  - `QUICK_START_v0.1.4.md`
  - `V0.1.4_IMPLEMENTATION_PLAN.md`
  - `LICENSE_SECURITY_ANALYSIS.md`

---

## 🌐 External Links

### GitHub
- **Repo**: https://github.com/zhurong2020/pyobfus
- **Issues**: https://github.com/zhurong2020/pyobfus/issues
- **Actions**: https://github.com/zhurong2020/pyobfus/actions
- **Latest Release**: https://github.com/zhurong2020/pyobfus/releases/tag/v0.1.4

### PyPI
- **Package**: https://pypi.org/project/pyobfus/
- **Latest**: https://pypi.org/project/pyobfus/0.1.4/
- **Stats**: https://pypistats.org/packages/pyobfus

### License Repository
- **Repo**: https://github.com/zhurong2020/pyobfus-licenses
- **Format**: Monthly JSON files (e.g., `licenses/2025/11.json`)

---

## 🔄 Git Status

```bash
# Current state
Branch: main
Latest commit: 29be115 feat: Release v0.1.4 - License security enhancements
Tags: v0.1.0, v0.1.2, v0.1.3, v0.1.4

# Release branch
release/v0.1.4: merged to main

# Working directory
Clean (no uncommitted changes)
```

---

## 🎯 Next Steps (v0.2.0)

### Planned Features
1. **Cython Compilation** - Compile pyobfus_pro to .pyd/.so
2. **License Server** - REST API for license management
3. **Usage Analytics** - Track device count per license
4. **Automated Revocation** - Suspend abusive licenses

### Timeline
- **Start**: TBD
- **Completion**: TBD
- **Release**: TBD

### References
- `docs/internal/FUTURE_FEATURES_ROADMAP.md`

---

## 📞 Contact

- **Author**: Rong Zhu
- **Email**: zhurong2020@users.noreply.github.com
- **GitHub**: @zhurong2020

---

## 🚀 Quick Commands

```bash
# Install latest version
pip install --upgrade pyobfus

# Install development version
pip install -e .

# Run all tests
pytest tests/ -v

# Run security tests
pytest tests/test_fingerprint.py tests/test_license_verification.py::TestCacheSigning -v

# Format code
black pyobfus/ pyobfus_pro/ tests/

# Check code quality
ruff check pyobfus/ pyobfus_pro/ tests/
mypy pyobfus/ pyobfus_pro/ --ignore-missing-imports

# Build package
python -m build

# Upload to PyPI
twine upload --disable-progress-bar dist/pyobfus-0.1.4*

# Create GitHub Release
gh release create v0.1.4 --title "v0.1.4 - License Security Fixes" dist/pyobfus-0.1.4*
```

---

## 📈 Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| v0.1.4 | 2025-11-12 | 🔒 Security: HMAC signing, device fingerprinting, 3-day cache |
| v0.1.3 | 2025-11-11 | 🐛 Fix: Critical dependency issues |
| v0.1.2 | 2025-11-11 | ✨ Feature: License verification system, Pro features |
| v0.1.0 | 2025-11-XX | 🎉 Initial release |

---

**This snapshot**: Current as of v0.1.4 release
**Next update**: After v0.2.0 planning begins
