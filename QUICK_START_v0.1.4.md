# Quick Start: v0.1.4 Implementation

**READ THIS FIRST when starting next session**

---

## 📍 Current Status

### ✅ Completed (v0.1.3)
- Released to PyPI: https://pypi.org/project/pyobfus/0.1.3/
- All tests passing (69 passed, 2 xfailed)
- All CI checks passing

### 🎯 Next Task: v0.1.4 Security Fixes

**Priority**: CRITICAL (P0)
**Goal**: Fix 3 license bypass vulnerabilities
**Time**: 1 week

---

## 🚀 Start Commands

```bash
# 1. Navigate to project
cd "c:\onedrive\msft\OneDrive - MSFT\rong\3-job\program\pyobfus"

# 2. Check current status
git status
git log --oneline -5

# 3. Read detailed implementation plan
cat docs/internal/V0.1.4_IMPLEMENTATION_PLAN.md

# 4. Create branch
git checkout -b release/v0.1.4

# 5. Start with Step 1 (Device Fingerprinting)
```

---

## 📋 3 Features to Implement

### Feature #1: Device Fingerprinting
**File**: Create `pyobfus_pro/fingerprint.py`
**Code**: See implementation plan Step 1
**Test**: Create `tests/test_fingerprint.py`

### Feature #2: HMAC Cache Signing
**File**: Modify `pyobfus_pro/license.py`
**Changes**:
- Add `LICENSE_SECRET` constant
- Update `cache_license()` - add HMAC signature
- Update `load_cached_license()` - verify signature
**Cache format**: v1 → v2 (add "sig", "device_id")

### Feature #3: Shorten Cache TTL
**File**: `pyobfus_pro/license.py`
**Change**: `CACHE_DURATION = timedelta(days=3)`  # was 30

---

## 📝 Checklist

```markdown
- [ ] Step 1: Create fingerprint.py (30 min)
- [ ] Step 2: Modify license.py - add signing (60 min)
- [ ] Step 3: Update __init__.py exports (5 min)
- [ ] Step 4: Update CLI to show device info (20 min)
- [ ] Step 5: Add/update tests (40 min)
- [ ] Step 6: Update version numbers (5 min)
- [ ] Step 7: Update CHANGELOG.md (10 min)
- [ ] Step 8: Run all tests (10 min)
- [ ] Step 9: Code quality checks (10 min)
- [ ] Step 10: Commit and push (10 min)
- [ ] Step 11: Build and release to PyPI (20 min)
- [ ] Step 12: Create GitHub Release (10 min)
```

**Total Time**: ~4 hours

---

## 🔑 Key Files

### To Create
```
pyobfus_pro/fingerprint.py      # NEW
tests/test_fingerprint.py       # NEW
docs/MIGRATION_v0.1.4.md        # NEW
```

### To Modify
```
pyobfus_pro/license.py          # Add HMAC signing
pyobfus_pro/__init__.py         # Export fingerprint
pyobfus_pro/cli.py              # Show device info
pyproject.toml                  # Version 0.1.4
pyobfus/__init__.py             # Version 0.1.4
CHANGELOG.md                    # Add v0.1.4 section
tests/test_license_verification.py  # Add signing tests
```

---

## 🧪 Testing Commands

```bash
# Unit tests
pytest tests/ -v

# Code quality
black pyobfus/ pyobfus_pro/ tests/
ruff check pyobfus/ pyobfus_pro/ tests/
mypy pyobfus/ pyobfus_pro/ --ignore-missing-imports

# Integration test
rm ~/.pyobfus/license.json
pyobfus-license register PYOB-TEST-1234-5678-90AB
pyobfus-license status
```

---

## 📚 Reference Documents

All in `docs/internal/`:

1. **V0.1.4_IMPLEMENTATION_PLAN.md** - Detailed step-by-step guide
2. **LICENSE_SECURITY_ANALYSIS.md** - Security analysis and vulnerabilities
3. **FUTURE_FEATURES_ROADMAP.md** - Long-term roadmap

---

## 🎯 Success Criteria

v0.1.4 is complete when:
- ✅ Cache files have HMAC signature
- ✅ Tampered cache is rejected
- ✅ Device fingerprint works correctly
- ✅ All 75+ tests pass
- ✅ Published to PyPI
- ✅ GitHub Release created

---

## 💡 If You Get Stuck

1. Read detailed plan: `docs/internal/V0.1.4_IMPLEMENTATION_PLAN.md`
2. Check existing code: `pyobfus_pro/license.py` (current implementation)
3. Review tests: `tests/test_license_verification.py` (patterns to follow)
4. Search issues: https://github.com/zhurong2020/pyobfus/issues

---

**Created**: 2025-11-11
**For Session**: Next conversation
**Estimated Time**: 4 hours
**Priority**: P0 - CRITICAL
