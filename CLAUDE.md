# pyobfus 开发约定

Modern Python Code Obfuscator - 基于 AST 的 Python 代码混淆器。

> 通用 agent 约定(build/test/lint、仓库结构、专利 gate 等)见根目录 [`AGENTS.md`](AGENTS.md)(规范源,工具无关)。本文件保留 Claude / 中文 / 专利申报相关的项目专属细节。
>
> @AGENTS.md

## ⚡ Current pending work (cold-start 必读)

**Single source of truth for forward TODO**: [`docs/POST_V0.4_TODO.md`](docs/POST_V0.4_TODO.md) — 重启 session 第一份必读

该文档顶部是活的「Current prioritized TODO」（随每次发布/里程碑刷新日期），下方是冻结的历史执行记录——**只读顶部，别被下面的历史小节带偏**。

### ✅ 2026-08-02 — pyobfus 0.5.6 已发布，issue #25 已关闭，CodeQL 已清零

**pyobfus 0.5.6 已发布**（issue #25 修复 + benchmark 沙箱权限加固，commit `4f53c2e`/`8ec8abc`，tag `v0.5.6` 经 OIDC 发 PyPI，核实 latest=0.5.6）。mcp 仍 0.3.1（本次未涉及 tool surface 变化）。

**issue #25**（`preserve_param_names`/`remove_docstrings`/`remove_comments` 被 CLI 默认值静默覆盖，且波及全部 7 个 framework preset 的 docstring 保留承诺）：`pyobfus/cli.py` 3 个 flag 改成 tri-state（`default=None`），"Override config with CLI options" 代码块只在用户显式传参时才覆盖 preset/config 选择。三个测试根全绿（1074+73+7）+ black/ruff/mypy 全过，8 个新回归测试。**已关闭**（issue 评论总结 + 引用 commit）。

**同 session 顺带清零 2 条 open CodeQL 告警**（High/CWE-732 `py/overly-permissive-file`，`benchmarks/llm_resistance/scorer.py` 的 Docker 打分沙箱 temp dir chmod）：目录权限 `0o755`→`0o711`（仅 traverse 不可 list，driver 只按已知硬编码路径开 3 个文件、从不 list 目录），真实 Docker 沙箱验证通过，下次扫描自动 fixed。逐文件 `0o644` 是功能性必需（容器跑不受信任 LLM 输出，用与 host 无关的 UID `65534:65534` 防御纵深，与文件属主无共同 group，跨 UID 读内容只能靠 world-read bit）——已用 `gh api` 记录 `won't fix` 理由正式 dismiss，非静默放置。

完整时间线 + 修复细节见 `docs/POST_V0.4_TODO.md` 顶部 handoff note + § item 7。

**🔍 README/MCP/ROADMAP 陈旧内容审计已做完（2026-08-02，未修）**：user 看完 0.5.6 后的 README 提了 11 个问题（Codex 未提及、PyPI 徽标误报缓存问题、MCP 元数据没跟上 `ml` preset、Claude Code plugin marketplace 是否需要外部注册、`v0.1.6+` 老版本号是否该清理、"New in v0.5.0" 标题已过时 6 个版本、**最锐利的发现**——`docs/ROADMAP.md` 仍把已发布的 P2-17/P2-19 标成进行中）。完整发现 + 建议修复顺序在 `docs/DOC_SYNC_AUDIT_2026-08-02.md`（专门写成冷启动可直接照做，不用重新调研）+ `docs/POST_V0.4_TODO.md` § item 8。

- ✅ 已提交并受理（申请号 `202610712171X` · 申请日/优先权日 2026-05-22 · 17 项权利要求）
- ✅ 费用全部缴清（共 1610 元 · 2026-05-22 一次缴清 · 含申请费类 1235 与实审费 375 · 官方审查信息查询「费足」核实）
- ✅ **段号补正答复**（2026-06-11 提交）→ **初步审查合格通知书**（发文 2026-06-17 · 发文序号 2026061200904340 · 审查员 陈立英），据专利法第 34 条进入「申请日满 18 个月（≈2027-11）即行公布」轨道
- ✅ **补正硬期限彻底关闭**；下一硬期限仅剩实审请求（申请日起 3 年 ≈2029-05-22，实审费 375 已缴）
- ✅ **v0.5.0 已发布**：6 项专利机制（P2-1/7/8/9/10/11）已并入公开 `pyobfus_pro/`，1016 测试 / 砍 3.8 / Beta→Production/Stable，tag `v0.5.0` 经 OIDC Trusted Publishing 发到 PyPI。机制经 `pyobfus_pro` API + `pyobfus-unscrub` CLI + standalone passes 可用
- ✅ **0.5.1 已发布（2026-06-22）**：`pyobfus build --flag` 融合 6 机制,tag `v0.5.1` 经 OIDC + PEP 740 attestations 发 PyPI(run `27938471463`)。
- ✅ **0.5.2 已发布（2026-06-22，PR #18）**：修 0.5.1 build-fusion 两个 Py3.9/3.10 bug——① `--seal-code` 在 3.9/3.10 误报 `IntegrityError`(seal 哈希用 marshal 默认版本≥3,受字符串 interning 影响 → 钉到 marshal version 2);② `--vault` 在 3.9 抛 `zip() takes no keyword arguments`(`zip(strict=)` 是 3.10+ 才有 → 改普通 zip)。1025 测试,tag `v0.5.2` 经 OIDC + PEP 740 发 PyPI(release run `27963690396`,CI 全矩阵含 3.9/3.10 绿)。回归守卫 `tests/test_seal_runtime.py::TestMarshalVersionStability`。
- ✅ **0.5.3 已发布（2026-07-07）**：补齐 0.5.1 顺延的三个 build-fusion flag——`--period`(运行计数守卫,commit `dfe1dbd`)、`--opacity-config`(pre-mangle qualname 解析 + 注入 `@opacity` 装饰器,绕开 name-map,`34dcbc5`)、`--bind-device`/`--bind-device-id`(设备锁定 L3,重写 `_LAYER_KEY` 为运行时派生,`62646b6`)。1033 测试,tag `v0.5.3` 经 OIDC + PEP 740 发 PyPI。
- ✅ **0.5.4 已发布（2026-07-19，PR #19）**：`--bind-device` 扩展到 vault key(`_VAULT_KEY_*`)设备绑定,与 opacity L3 用同一套运行时派生技术。首批外部 issue #20/#21(trial 绕过报告)按「诚实记录边界、不加固客户端」处置并关闭。
- ✅ **issue #22 mypy gate 已关闭（2026-07-22，PR #23）**：Core/Pro/MCP 共 72 个源文件 mypy 零错误,CI 全矩阵绿后合并。
- ✅ **pyobfus-mcp 0.3.1 已发布（2026-06-22）**：pro-funnel 文案点名 v0.5 机制 · dep `>=0.5.1` · tag `mcp-v0.3.1` 发 PyPI + `mcp-publisher` 发 MCP Registry(0.3.1 isLatest)。
- ✅ **AI-agent 可发现性 Wave A（2026-06-22）**：Smithery 经 **Skill 渠道** `zhurong2020/pyobfus-protect`（Smithery MCP 发布是远程网关、本地工具走不通,Skill 才对）+ mcp.so + `uvx` 零安装 + server.json 99 字描述(commit `826c576`/`49f4df3`)。报告:`docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`。
- ❌ **JOSS 投稿被拒(2026-06-24)**:v0.5.1 投 JOSS(issue `openjournals/joss-reviews#10788`)被总编 desk-reject,理由=**scope/significance 非质量**("private-dev-then-public" + 无第三方复用)。→ 改走免费路径:✅ **Zenodo DOI `10.5281/zenodo.20846053`(concept)已拿到**,已接进 CITATION.cff + README 徽章 + `## Citation` + 两个 pyproject + RTD + ORCID + arong.eu.org/academic。完整记录+渠道对比见 `docs/JOSS_REJECTION_20260624.md`。
- ✅ **P2-18 内部证据完成（2026-08-01）**：5 样本 × Codex+Claude 全跑完，`price_rules` 拿到第一个干净跨模型 C4 数据点，决定不加第三个模型家族。评审版报告 `docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md`；过程中顺带修了 3 个既有 plumbing bug（语料库 no-op 稀释统计、`--json-schema` 不认 `$schema` meta key、docker 打分沙箱 temp dir 权限导致此前从未真实跑通），细节见 `docs/POST_V0.4_TODO.md` § P2-18。
- ✅ **pyobfus 0.5.5 已发布（2026-08-02，PR #26 + #27）**：`--preset ml`（P2-19，社区版模型服务 preset）+ `--provenance-manifest`（P2-17，本地 JSON 构建溯源清单，非加密签名）。Review 顺带发现 issue #25 并诚实标注在 CHANGELOG/docstring 里，不是掩盖。
- ✅ **pyobfus 0.5.6 已发布（2026-08-02）**：issue #25 修复（见上）+ CodeQL 高危告警清零（见上）。
- ⏭️ **更后续**（完整清单见 `docs/POST_V0.4_TODO.md` 顶部「Current prioritized TODO」）:P2-13/P2-22 这类零代码内容型候选（PyInstaller cookbook / PyArmor 对比页）。Launch wave 已收工转被动监测(+7d/+30d checkpoint,不主动推)。IP 商业化迁移(个人→旎嵘科技)排在更后面。

**Cold-start session 第一句话应问 user**：「README/MCP/ROADMAP 陈旧内容审计已经做完，`docs/DOC_SYNC_AUDIT_2026-08-02.md` 里有完整发现和建议修复顺序（最优先：ROADMAP.md 把已发布功能标成进行中）。现在开始按那份计划修吗？」

**Cold-start 资料定位**（按读取优先级）：

| 优先级 | 文件 | 用途 |
|---|---|---|
| 1 | `~/projects/pyobfus-legal/patent/SESSION_LOG_20260617.md`（最新）+ `SESSION_LOG_20260611.md` | 最新时间线 + 初审合格 + next action（off-repo · 完整 narrative）|
| 2 | `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/patent_correction_notice_2026-06-01.md` | 初审合格结论 + 补正根因/历史 + 受理/费用状态 |
| 3 | `~/projects/pyobfus-legal/patent/08_提交记录/` | 五份官方通知书正本（受理 / 收费减缴 / 电子回执 / 补正 / **初步审查合格**）|
| 4 | `docs/V0.5_RELEASE_PLAN.md` + `https://github.com/zhurong2020/pyobfus/blob/main/docs/POST_V0.4_TODO.md` § P1 | v0.5 发布 checklist + 公开版状态块 |

**跨项目联动**：cac-plus-ip 与本 pyobfus 共享同一个人申请人 + 同一 2026 年度费减备案；`~/projects/cac-plus-ip/CLAUDE.md` 含完整跨项目索引。详见 memory `ip_workflow_cross_project.md`。

**Path C 红线（gate 解除后的残留约束）**：① `pyobfus-legal/` **永不入 git**（含 PII，永久有效）；② v0.5 Pro 机制的公开发布**走 Phase 5 受控合并**（一次性、刻意公开），合并前公开 commit 仍不得泄露未发布机制——但 gate 本身（"补正办结前不得公开 v0.5 机制"）**已于 2026-06-17 解除**。完整命名清单见 memory `pro_disclosure_finding_2026-05-09.md` + `pyobfus_patent_strategy.md`。

## 项目概述

- **定位**: Python 代码混淆器 (开源 + 商业双许可)
- **技术栈**: Python 3.9-3.14, AST, setuptools
- **PyPI 主包**: https://pypi.org/project/pyobfus/ (**v0.5.3，2026-07-07 发布** — 补齐 `--period`/`--opacity-config`/`--bind-device` 三个 build-fusion flag · 1033 测试 · 0.5.2 修 Py3.9/3.10 · 0.5.1 把 6 机制接进 `pyobfus build` flags · 0.5.0(06-18)首次公开机制 + 砍 3.8)
- **PyPI MCP 包**: https://pypi.org/project/pyobfus-mcp/ (**v0.3.1，2026-06-22 发布** — 8 tools: 6 community + 2 pro_funnel(`recommend_tier`/`start_pro_trial` · 文案点名 v0.5 机制) · dep `pyobfus>=0.5.1` · `uvx pyobfus-mcp` 零安装)
- **MCP Registry**: `io.github.zhurong2020/pyobfus-mcp` (active, isLatest=true · **0.3.1**)
- **Smithery (Skill)**: https://smithery.ai/skills/zhurong2020/pyobfus-protect (2026-06-22 上线 · 本地工具走 Skill 渠道非 MCP 渠道) · **mcp.so**: 已收录
- **Glama Listing**: https://glama.ai/mcp/servers/zhurong2020/pyobfus (Quality A) — Glama 容器 build 自 **admin Dockerfile→Configuration「Build steps」字段**(web-UI)，**不读 repo 的 `pyobfus_mcp/Dockerfile`**，且**不自动跟 PyPI 最新**：每次发 mcp 新版都要手动把该字段的 `pyobfus-mcp==<ver>` bump 一次，否则 listing 静默供旧工具面——**发布必做步骤**，已进 `docs/V0.5_RELEASE_PLAN.md` Phase 5.6。最近 2026-07-07 从 0.2.0→0.3.1(test `019f3b5a` 返回全 8 工具)；公开 API re-index 滞后 ≤1 天。「Recent Releases」的版本号(如 0.5.4)是 Glama 自增计数、与实装版本无关，忽略。教训 memory `glama_container_build_source` · 历史 `docs/POST_V0.4_TODO.md`
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
├── tests/             # 1033 测试用例 (90% coverage · 0.5.3 发布版)
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

**ℹ️ Python 3.8 已于 0.5.0 移除**（EOL 2024-10，floor 升到 3.9）：当年 `astunparse` 在 3.8 上的 CLI 集成测试 flaky 问题随之消失，`@requires_py39` 装饰器现为 no-op（可逐步清理）。`docs/PYTHON38_COMPATIBILITY.md` 仅作历史记录保留。

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
- **跨版本兼容**: 确保 Python 3.9-3.14 全部通过测试
- **双许可模型**: Free (pyobfus/) 和 Pro (pyobfus_pro/) 代码分离管理

## 跨 Workspace 关联

| 关联项目 | 所在 Workspace | 关系 |
|----------|---------------|------|
| `pyobfus-legal/` | cardiac-research.code-workspace（symlink to OneDrive 同级目录）| pyobfus 软著 + 专利申报材料的物理仓库（**不在 git repo 内** · 含 PII，不公开）。包含 `software_copyright/` (V0.4.0 软著已 2026-05-09 提交 CCPC) 和未来的 `patent/` (v0.5 专利申请目录)。物理路径：`/mnt/c/onedrive/msft/OneDrive - MSFT/rong/3-job/program/pyobfus-legal/`，工作区入口：`~/projects/pyobfus-legal/`（symlink） |
| `cac-plus-ip/` | cardiac-research.code-workspace（同 workspace 内）| **同申请人的并行 IP 工作流**。CAC Plus 医学 AI 项目的 3 件中国发明专利 + 2 件软著申请仓库。**与 pyobfus 内容无关、但工作流共享**：同一个 CCPC 账号 / 同一个 CPC 客户端 USB Key / 同一个 85% 个人申请减免资格 / 同一套 CNIPA 官方申请模板（位于 `cac-plus-ip/02_china_发明专利/_templates_CNIPA/`，pyobfus v0.5 专利申请直接复用，不重复下载）|
