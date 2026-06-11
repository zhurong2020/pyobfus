# pyobfus 开发约定

Modern Python Code Obfuscator - 基于 AST 的 Python 代码混淆器。

> 通用 agent 约定(build/test/lint、仓库结构、专利 gate 等)见根目录 [`AGENTS.md`](AGENTS.md)(规范源,工具无关)。本文件保留 Claude / 中文 / 专利申报相关的项目专属细节。
>
> @AGENTS.md

## ⚡ Current pending work (cold-start 必读)

**Single source of truth for forward TODO**: [`docs/POST_V0.4_TODO.md`](docs/POST_V0.4_TODO.md) — 重启 session 第一份必读

Snapshot 2026-05-07 (v0.4 distribution leg 完整闭环之后)。包含 30-second resume cheat sheet · 4 个 self-actionable P0 item（CI smoke test + PEP 740 attestation + server.json _meta + dev.to voice pass）· v0.5 work（含 3 个 2026-05 research 发现的新机会：PEP 750 t-string handler · FastMCP 3.0 升级 · `--target claude-skill` preset）· passive waiting items · do-not-do list · 3 周建议节奏。

### 🔥 2026-06-05 active state — pyobfus v0.5 中国发明专利申请（补正阶段）

**当前最高优先级活动**：发明专利已**提交并缴费、受理通知书已下发**，现处于初审**形式补正**阶段，需在期限内答复补正通知书。

- ✅ 已提交并受理（申请号 `202610712171X` · 申请日/优先权日 2026-05-22 · 17 项权利要求）
- ✅ 费用全部缴清（共 1610 元 · 2026-05-22 一次缴清 · 含申请费类 1235 与实审费 375 · 官方审查信息查询「费足」核实 · 7-22 缴费期限与 2029 实审费期限均关闭）
- 🔴 **当前唯一硬期限 = 答复补正通知书**（发文 2026-06-01 · 说明书段号需系统自带 · **~2026-08-01 前答复，逾期申请视为撤回**）
- 📋 流程：先电话审查员问清提交方式 → 重提合规说明书/补正书 → 补正办结、申请状态干净 → **方可解锁 Path C Phase 5（v0.5 公开 release）**

**Cold-start session 第一句话应问 user**：「补正答复办妥了吗？（说明书段号那件）」

**Cold-start 资料定位**（按读取优先级）：

| 优先级 | 文件 | 用途 |
|---|---|---|
| 1 | `~/projects/pyobfus-legal/patent/SESSION_LOG_20260605.md` | 最新时间线 + 补正硬期限 + 费用全清 + next action（off-repo · 含完整 narrative）|
| 2 | `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/patent_correction_notice_2026-06-01.md` | 补正硬期限 + 根因 + 受理/费用状态 |
| 3 | `~/projects/pyobfus-legal/patent/08_提交记录/` | 四份官方通知书正本（受理 / 收费减缴 / 电子回执 / 补正）|
| 4 | `https://github.com/zhurong2020/pyobfus/blob/main/docs/POST_V0.4_TODO.md` § P1 | 公开版状态块 |

**跨项目联动**：cac-plus-ip 与本 pyobfus 共享同一个人申请人 + 同一 2026 年度费减备案；`~/projects/cac-plus-ip/CLAUDE.md` 含完整跨项目索引。详见 memory `ip_workflow_cross_project.md`。

**Path C 红线**（**持续生效至 v0.5 公开发布，即补正办结后**；注意：申请号虽已到手，但 v0.5 mechanism 的公开限制不解除，直到正式 release）：pyobfus-legal/ 永不入 git；pyobfus-pro-dev v0.5 mechanism 永不 push 公开 repo；公开 commits 中不出现 v0.5 patent-gated 内部符号（命名清单与具体禁忌见 memory `pro_disclosure_finding_2026-05-09.md` + `pyobfus_patent_strategy.md`）。

## 项目概述

- **定位**: Python 代码混淆器 (开源 + 商业双许可)
- **技术栈**: Python 3.8-3.14, AST, setuptools
- **PyPI 主包**: https://pypi.org/project/pyobfus/ (v0.4.0，2026-04-22 发布)
- **PyPI MCP 包**: https://pypi.org/project/pyobfus-mcp/ (v0.2.0，2026-05-08 发布 — 7 tools: 5 community + 2 pro_funnel `recommend_tier`/`start_pro_trial` · FastMCP 1.27 + security hardening. 0.1.2 曾修 `FastMCP.__init__()` `version=` kwarg drift)
- **MCP Registry**: `io.github.zhurong2020/pyobfus-mcp` (active, isLatest=true · 0.2.0)
- **Glama Listing**: https://glama.ai/mcp/servers/zhurong2020/pyobfus (Quality A · 全 A) — **2026-06-08 tool-count 真根因已修**：Glama 容器 build 自 **admin Dockerfile→Configuration「Build steps」字段**(web-UI 专属设置)，**不读 repo 自带 `pyobfus_mcp/Dockerfile`**；该字段独立 pin 在 `0.1.2` 一直卡住(06-05 改 repo Dockerfile pin 0.1.1→0.2.0 方向错、无效)。改 Build steps `0.1.2`→`0.2.0` 保存后 test `019ea6c5` 18:27 CST 跑绿、introspection 返回全部 7 工具。剩公开 API/列表/Inspector 被动 re-index(≤1 天)。教训见 memory `glama_container_build_source.md`
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
├── tests/             # 719 测试用例 (91% coverage · 0.4.0 发布版 655)
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
| `pyobfus-legal/` | cardiac-research.code-workspace（symlink to OneDrive 同级目录）| pyobfus 软著 + 专利申报材料的物理仓库（**不在 git repo 内** · 含 PII，不公开）。包含 `software_copyright/` (V0.4.0 软著已 2026-05-09 提交 CCPC) 和未来的 `patent/` (v0.5 专利申请目录)。物理路径：`/mnt/c/onedrive/msft/OneDrive - MSFT/rong/3-job/program/pyobfus-legal/`，工作区入口：`~/projects/pyobfus-legal/`（symlink） |
| `cac-plus-ip/` | cardiac-research.code-workspace（同 workspace 内）| **同申请人的并行 IP 工作流**。CAC Plus 医学 AI 项目的 3 件中国发明专利 + 2 件软著申请仓库。**与 pyobfus 内容无关、但工作流共享**：同一个 CCPC 账号 / 同一个 CPC 客户端 USB Key / 同一个 85% 个人申请减免资格 / 同一套 CNIPA 官方申请模板（位于 `cac-plus-ip/02_china_发明专利/_templates_CNIPA/`，pyobfus v0.5 专利申请直接复用，不重复下载）|
