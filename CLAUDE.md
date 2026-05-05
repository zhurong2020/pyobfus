# pyobfus 开发约定

Modern Python Code Obfuscator - 基于 AST 的 Python 代码混淆器。

## 项目概述

- **定位**: Python 代码混淆器 (开源 + 商业双许可)
- **技术栈**: Python 3.8-3.14, AST, setuptools
- **PyPI**: https://pypi.org/project/pyobfus/ (v0.4.0，2026-04-22 发布)
- **GitHub**: https://github.com/zhurong2020/pyobfus (public)
- **文档**: https://pyobfus.readthedocs.io
- **许可**: Apache 2.0 (Core) + Proprietary (Pro)

## 架构

```
pyobfus/
├── pyobfus/           # 核心包 (Free Edition)
│   ├── obfuscator.py  # 主混淆器
│   ├── analyzer.py    # 符号表分析
│   ├── transformers/   # AST 变换器
│   └── cross_file/    # 跨文件混淆
├── pyobfus_pro/       # Pro Edition (商业许可)
├── tests/             # 560+ 测试用例 (90% coverage)
├── examples/          # 示例代码
├── docs/              # 项目文档
└── cloudflare-worker/ # 许可验证 Worker
```

## 开发约定

### 本地开发

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# 一次性激活仓库内的 PII 防护 pre-commit 钩子（每个 clone 各自做一次）
git config core.hooksPath .githooks
```

**PII 防护 pre-commit 钩子**：`.githooks/pre-commit` 拦截 `诸嵘 / 陈启稚 / qizhi_chen / 身份证 / /home/wuxia/` 5 个模式进入暂存区。源于 2026-05-03 的 git 历史改写（见 `docs/V0.4_EXECUTION_LOG.md` Sessions 13-15）。详见 `.githooks/README.md`。

### 测试

```bash
pytest tests/ -v
pytest tests/ -v --cov=pyobfus --cov-report=html
pytest integration_tests/ -v
```

**⚠️ Python 3.8 注意**：`astunparse` 库在某些 AST 输入上的输出不稳定，会导致 Pro 特性的 CLI 集成测试在 macOS ARM64 / Windows runner 上 flaky。**添加新的 Pro 特性 CLI 集成测试（`CliRunner().invoke + --<pro-flag>`）前务必阅读 [`docs/PYTHON38_COMPATIBILITY.md`](docs/PYTHON38_COMPATIBILITY.md)**，并对新测试套用 `@requires_py39` 装饰器（参考 `tests/test_cli_pro_paths.py::TestProFeatureExecution`）。纯 AST transformer 单元测试不受影响。

### 代码规范

- 格式化: `black pyobfus/`
- 类型检查: `mypy pyobfus/`
- Lint: `ruff check pyobfus/`

### 发布流程

1. 更新 `pyproject.toml` 版本号
2. 更新 `CHANGELOG.md`
3. `python -m build && twine upload dist/*`

## 注意事项

- **公开仓库**: 不要提交 Pro 许可密钥或 Stripe Webhook Secret
- **跨版本兼容**: 确保 Python 3.8-3.14 全部通过测试
- **双许可模型**: Free (pyobfus/) 和 Pro (pyobfus_pro/) 代码分离管理

## 跨 Workspace 关联

| 关联项目 | 所在 Workspace | 关系 |
|----------|---------------|------|
| 无直接关联 | - | 独立工具项目 |
