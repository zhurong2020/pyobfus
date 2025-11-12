# Release v0.1.2 - 发布检查清单

**目标版本**: v0.1.2
**发布日期**: 2025-11-11
**关键特性**: 许可证验证系统

---

## ✅ 发布前检查清单

### 1. 代码质量验证

- [x] **所有测试通过** (71 tests: 69 passed, 2 xfailed)
  ```bash
  pytest tests/ -v
  # ✅ 已验证通过
  ```

- [x] **Mypy类型检查** (19个文件，0错误)
  ```bash
  mypy pyobfus/ pyobfus_pro/ --pretty --ignore-missing-imports
  # ✅ Success: no issues found
  ```

- [x] **Ruff代码质量检查**
  ```bash
  ruff check pyobfus/ pyobfus_pro/
  # ✅ All checks passed!
  ```

- [x] **版本号已更新**
  - [x] `pyproject.toml`: version = "0.1.2"
  - [x] `CHANGELOG.md`: ## [0.1.2] - 2025-11-11

### 2. 文档完整性

- [x] CHANGELOG.md 更新完成
- [x] README.md （暂不需要更新）
- [x] LICENSE_SYSTEM_IMPLEMENTATION_SUMMARY.md
- [x] docs/internal/PYOBFUS_LICENSES_REPO_SETUP.md
- [x] docs/internal/LICENSE_VERIFICATION_SPEC.md

### 3. Git提交和标签

```bash
# 检查当前状态
git status

# 应该显示修改的文件：
# - CHANGELOG.md
# - pyproject.toml
# - pyobfus_pro/__init__.py
# - pyobfus_pro/license.py
# - pyobfus_pro/cli.py
# - pyobfus/cli.py
# - tests/test_license_verification.py
# - (其他新增文件)

# 添加所有更改
git add .

# 提交
git commit -m "feat: Add license verification system for Pro edition

- Implement GitHub-based license verification with 30-day caching
- Add pyobfus-license CLI tool (register/status/remove/generate)
- Close business model vulnerability (Pro features now require valid license)
- Add 14 comprehensive tests for license system (all passing)
- All code quality checks passing (mypy, ruff, pytest)

BREAKING CHANGE: Pro edition now requires license registration.
Users must run \`pyobfus-license register YOUR-KEY\` before using \`--level pro\`.

Fixes #N/A (internal security issue)
"

# 创建标签
git tag -a v0.1.2 -m "Release v0.1.2: License verification system

Key changes:
- License verification system for Pro edition
- Closes business model vulnerability from v0.1.1
- 14 new tests, all quality checks passing
- Breaking change: Pro requires license registration
"

# 推送到远程
git push origin main --tags
```

### 4. 构建分发包

```bash
# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info

# 构建新的分发包
python -m build

# 验证构建结果
ls -lh dist/
# 应该看到：
# - pyobfus-0.1.2-py3-none-any.whl
# - pyobfus-0.1.2.tar.gz
```

### 5. PyPI发布

```bash
# 可选：先发布到Test PyPI测试
twine upload --repository testpypi dist/pyobfus-0.1.2*

# 从Test PyPI测试安装
pip install --index-url https://test.pypi.org/simple/ pyobfus==0.1.2

# 测试pyobfus-license命令
pyobfus-license --version

# 正式发布到Production PyPI
twine upload dist/pyobfus-0.1.2*

# 输入PyPI用户名和token（或使用.pypirc）
```

### 6. Yank v0.1.1（重要！）

**方式1：使用PyPI Web界面**（推荐）

1. 访问 https://pypi.org/manage/project/pyobfus/release/0.1.1/
2. 登录PyPI账号
3. 滚动到底部，找到 "Options"
4. 点击 **"Yank this release"**
5. 在弹出框中填写原因：
   ```
   Security: Contains business model vulnerability allowing unauthorized access to Pro features. Users should upgrade to v0.1.2 or later.
   ```
6. 确认Yank

**效果**：
- ✅ v0.1.1不会被`pip install pyobfus`安装（会跳到v0.1.2）
- ✅ 已安装v0.1.1的用户仍可使用
- ✅ 明确指定版本仍可安装：`pip install pyobfus==0.1.1`
- ✅ 符合PyPI最佳实践

**方式2：使用命令行**（如果有API权限）

```bash
# 需要PyPI API token with yank权限
# 目前PyPI Web界面更可靠
```

### 7. GitHub Release

```bash
# 使用GitHub CLI创建release
gh release create v0.1.2 \
  --title "v0.1.2 - License Verification System" \
  --notes-file <(cat << 'EOF'
## 🔒 License Verification System

This release introduces a comprehensive license verification system for pyobfus Professional Edition, addressing a critical business model vulnerability found in v0.1.1.

### 🚨 Breaking Changes

**Pro edition now requires license registration**. Users must:
1. Obtain a license key (see [Pricing](https://github.com/zhurong2020/pyobfus))
2. Register: `pyobfus-license register YOUR-LICENSE-KEY`
3. Then use: `pyobfus input.py -o output.py --level pro`

### ✨ New Features

#### License Management CLI
- `pyobfus-license register` - Register your license key
- `pyobfus-license status` - Check license status
- `pyobfus-license remove` - Remove cached license

#### License Verification
- GitHub-based online verification
- 30-day local caching (offline support)
- Automatic license validation for Pro features
- Support for license expiration and revocation

#### Pro Edition Features (Experimental)
- AES-256 string encryption
- Anti-debugging checks
- Runtime decryption infrastructure

### 🔧 Fixed
- Infrastructure function names preservation
- F-string handling in encryption
- Type checking errors across modules
- Python 3.8 compatibility

### 🔐 Security
**[CRITICAL]** Closes business model vulnerability in v0.1.1:
- Pro features now properly gated behind license verification
- Community edition limits (5 files, 1000 LOC) enforced
- License verification required for unlimited access

### 📊 Technical Details
- **New tests**: 14 (license system)
- **Total tests**: 71 (69 passed, 2 xfailed)
- **Code coverage**: 52%
- **Quality checks**: All passing (mypy, ruff, pytest)

### 📚 Documentation
- [License System Implementation Summary](LICENSE_SYSTEM_IMPLEMENTATION_SUMMARY.md)
- [License Repository Setup Guide](docs/internal/PYOBFUS_LICENSES_REPO_SETUP.md)
- [License Verification Spec](docs/internal/LICENSE_VERIFICATION_SPEC.md)

### ⚠️ Important Notes

**For v0.1.1 Users**: v0.1.1 has been yanked from PyPI due to security concerns. Please upgrade:
```bash
pip install --upgrade pyobfus
```

**For Pro Users**: If you were using `--level pro` in v0.1.1, you now need a valid license. Contact us for licensing options.

### 🙏 Acknowledgments

Thank you to everyone who provided feedback on the v0.1.1 release. This update ensures a sustainable business model while maintaining excellent user experience.

---

**Full Changelog**: https://github.com/zhurong2020/pyobfus/blob/main/CHANGELOG.md
EOF
)

# 或者简化版：
gh release create v0.1.2 --generate-notes
```

### 8. 验证发布

```bash
# 等待几分钟让PyPI索引更新

# 创建新的虚拟环境测试
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# 从PyPI安装
pip install pyobfus

# 验证版本
python -c "import pyobfus; print(pyobfus.__version__)"
# 应该显示: 0.1.2

# 验证pyobfus-license命令存在
pyobfus-license --version

# 测试社区版功能
echo "x = 1" > test.py
pyobfus test.py -o test_obf.py
cat test_obf.py

# 测试Pro版需要许可证
pyobfus test.py -o test_obf.py --level pro
# 应该报错：Error: No license key found

# 清理
deactivate
rm -rf test_env test.py test_obf.py
```

---

## 📢 后续公告

### 1. GitHub Discussions公告

创建新的公告帖：

**标题**: "v0.1.2 Released - License Verification System"

**内容**:
```markdown
We're excited to announce v0.1.2, which introduces a comprehensive license verification system for pyobfus Professional Edition!

## What's New

### License Management
Pro edition now includes a complete license verification system:
- Register once, use anywhere
- 30-day offline caching
- Simple CLI: `pyobfus-license register YOUR-KEY`

### Why This Change?

v0.1.1 had a vulnerability that allowed unauthorized access to Pro features. v0.1.2 closes this gap while maintaining excellent UX:
- Community edition: Still free, 5 files/1000 LOC
- Pro edition: Now requires license, unlimited everything

### Upgrade Today

```bash
pip install --upgrade pyobfus
```

**Note**: v0.1.1 has been yanked from PyPI. All users should upgrade.

### Questions?

- Pricing: [See pricing page](https://github.com/zhurong2020/pyobfus)
- Issues: [GitHub Issues](https://github.com/zhurong2020/pyobfus/issues)
- Support: zhurong2020@users.noreply.github.com
```

### 2. README.md徽章更新（可选）

在README.md顶部添加：

```markdown
![PyPI - Version](https://img.shields.io/pypi/v/pyobfus)
![PyPI - Status](https://img.shields.io/pypi/status/pyobfus)
![License](https://img.shields.io/github/license/zhurong2020/pyobfus)
```

### 3. 社交媒体（如适用）

- Twitter/X
- Reddit (r/Python)
- Dev.to
- HackerNews (Show HN)

---

## 🔍 Post-Release监控

### 第1天

- [ ] 检查PyPI页面更新：https://pypi.org/project/pyobfus/
- [ ] 验证v0.1.1已被Yank
- [ ] 监控GitHub Issues新问题
- [ ] 检查安装统计

### 第1周

- [ ] 收集用户反馈
- [ ] 监控许可证验证错误
- [ ] 准备FAQ文档（如需要）

### 第1个月

- [ ] 评估许可证系统性能
- [ ] 规划v0.2.0功能
- [ ] 考虑支付系统集成

---

## ❓ 常见问题处理

### Q: 用户报告无法验证许可证

**检查**：
1. GitHub pyobfus-licenses仓库是否已创建并公开
2. 许可证文件格式是否正确
3. 用户网络是否可以访问GitHub

**解决**：
```bash
# 提供离线注册方法
pyobfus-license register YOUR-KEY --no-verify
```

### Q: 用户升级后Pro功能不可用

**说明**：
- v0.1.2是破坏性更新
- Pro功能现在需要许可证
- 提供购买链接和支持邮箱

### Q: 构建或发布失败

**常见原因**：
1. PyPI token过期 → 重新生成
2. 网络问题 → 重试
3. 版本号冲突 → 检查pyproject.toml

---

## 📝 总结

**发布v0.1.2需要执行的核心步骤**：

1. ✅ 运行所有测试和质量检查
2. ✅ Git commit + tag + push
3. ✅ 构建分发包：`python -m build`
4. ✅ 上传PyPI：`twine upload dist/pyobfus-0.1.2*`
5. ⚠️ **Yank v0.1.1**（重要！）
6. ✅ 创建GitHub Release
7. ✅ 验证安装和功能
8. ✅ 发布公告

**预计时间**: 30-60分钟

**下一步**: 设置支付处理，开始销售Pro版许可证

---

**创建日期**: 2025-11-11
**状态**: 准备发布
