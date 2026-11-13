# pyobfus 开发约定

Modern Python Code Obfuscator - 基于 AST 的 Python 代码混淆器。

> 通用 agent 约定(build/test/lint、仓库结构、专利 gate 等)见根目录 [`AGENTS.md`](AGENTS.md)(规范源,工具无关)。本文件保留 Claude / 中文 / 专利申报相关的项目专属细节。
>
> @AGENTS.md

## ⚡ Current pending work (cold-start 必读)

**2026-11-12 #221 审阅完成、Worker 限流上线**：独立审阅仅一项低危（CI 未实际限流），#227 修复并部署 Worker `209eb969`（回滚 `13aaa4a8`），线上验证通过；#226 修正文档站 canonical。见 [当前计划](docs/CURRENT_PLAN_ZH.md)。

**2026-11-12 发布收尾完成**：CITATION 已同步 Zenodo `24140234`（#224）；Glama 渠道 0.13.1 装 Core 0.14.0（test `01a1cd2b`；11-13 03:56 维护者再次手工 Build & Release，渠道 0.14.0，test `01a1d155` 同样装 Core 0.14.0／MCP 0.3.17）；签发私钥已在 Vaultwarden 并复核。GSC 重定向错误示例为无斜杠 `/zh-cn`，单次 301 到 `/zh-cn/`（200），无需改代码。剩 #221 独立外部审阅、11-16 周检。见 [当前计划](docs/CURRENT_PLAN_ZH.md)。

**2026-11-11 夜 Core 0.14.0 已发布**（签名 CI 构建准入）：核验见 [发布记录](docs/CORE_0_14_0_RELEASE_2026-11-11.md)。#221 squash 为 `96e6340`、tag `v0.14.0`，PyPI 0.14.0 带 attestation，全新安装与线上签名准入通过。待：Zenodo 归档后同步 CITATION、Glama Build steps（手工）、#221 独立外部审阅（发版后补）。

**2026-11-11 晚 生产 key 与 Worker 上线**：#220 已合并；生产 key `ci-2026-11` 已生成，公钥入 `pyobfus_pro/ci_lease.py`，Worker 版本 `13aaa4a8` 已部署并线上配对通过（回滚 `d8588738`）。私钥已入 Vaultwarden（11-12 复核）；#221 合并与发版待批准。详见 [当前计划](docs/CURRENT_PLAN_ZH.md)。

**2026-11-11 本次会话收尾**：先读 [会话收尾](docs/SESSION_CLOSEOUT_2026-11-11.md)。`74769cd` 签名拒绝响应修订已推送，托管 48 success／2 skipped，本地全量与 Worker 70 项通过。#220 源码审阅无阻塞，待明确合并决定；#221 仍待独立外部审阅、公钥／轮换方案及最终发布验收。未合并、配置生产 key、部署或发版。私有接续见 `docs/internal/f2-ci-implementation-2026-11-11/NEXT_SESSION.md`，下方为此前阶段快照。

**2026-11-11 F2 CI 首阶段候选**：维护者已批准“先 CI，后工作站”。草稿 #221／分支 `feat/ci-signed-lease-v1`，父依赖为未合并 #220，PR 目标 main 以运行现有 Core CI／CodeQL；Worker 三格互通已通过，其余候选检查与独立审阅待核。私有接续 `docs/internal/f2-ci-implementation-2026-11-11/PROGRESS.md`。工作站／离线不迁移；生产信任表为空且发布流程有阻断，未配置 key、未部署、未发版。不得重用 #217 的合并批准。

**2026-11-11 接续**：见 [本轮巡检](docs/OPERATIONS_REVIEW_2026-11-11.md) → [当前计划](docs/CURRENT_PLAN_ZH.md) → [TODO](docs/TODO.md)。本地已同步 `df58068`；T+7d、下载／邮件、11-09 搜索盘点与备份抽核已做。优先取得 GSC“重定向错误”示例 URL；下次周检 11-16，T+30d 约 12-04。F2 先确认兼容与离线迁移；许可条款先专业审阅。下方 11-07 段为历史交接。

**2026-11-07 晚 Core 0.13.0 已发布**（Community pre-commit 钩子 + 专利申请标识）：核验见 [发布记录](docs/CORE_0_13_0_RELEASE_2026-11-07.md)。Zenodo record `24031969` 已归档、`CITATION.cff` 已同步，Glama 已更新并通过检测；本版发布收尾完成。MCP／runtime／扩展／Action 不变。

**2026-11-07 最终交接**：先读 [会话收尾](docs/SESSION_CLOSEOUT_2026-11-07.md) → [当前计划](docs/CURRENT_PLAN_ZH.md) → [TODO](docs/TODO.md)「周期性」。
该段记录 11-07 上午状态；晚间 Core 0.13.0 已发布 Community pre-commit 钩子（#194）。已做：CI 3.9 runner、FAQ／中文指南、Agent 文档同步规则、
IndexNow、Search Console／Bing 登记（文档站验证文件 `docs/google03878b382b498ff9.html` 必须保留）、T+24h／T+72h、备份故障修复与核对。
下一步：11-08 再请求编入索引、11-09 周检（含搜索引擎检查）、约 11-11 T+7d、维护者跑只读盘点、12 月首周月度观测。
arong.eu.org 与老博客已交 findata。

**单一事实来源**：[`docs/CURRENT_PLAN_ZH.md`](docs/CURRENT_PLAN_ZH.md)（当前计划）与 [`docs/TODO.md`](docs/TODO.md)（排期、验收、周期性任务）。
`docs/ROADMAP.md`、`docs/POST_V0.4_TODO.md` 为归档。11-04 及更早的交接段落已移至私有 `docs/internal/CLAUDE_MD_HISTORY_2026-11-07.md`。

### 仍生效的约定（从历次交接提炼，2026-11-07）

- **工作方式**：代码修改默认交无头 Codex 实现、Claude 审核（注意 Codex 5 小时额度；沙箱 `.git` 只读时由 Claude 提交／推送）。
  所有 PR（含纯文档）的合并均遵循维护者在每次会话中的明确指示，无常设自动合并授权；发版另需明确批准。
- **发版节奏（10-23 定）**：不为观察下载设静默期，按功能与修复的自然进度规划发版，每次发版仍须批准（`docs/TODO.md`「节奏」）。
- **查进度固定动作**：进度 + 下载量（`python scripts/download_snapshot.py`）+ Gmail（`/pyobfus-inbox`），三样一起给。
- **内容与稿件**：未发稿件放 gitignored 的 `docs/internal/content-*/`，不进公开目录；排期见 `docs/TODO.md`「内容节奏」。
  `llms.txt`／`AGENTS.md`／MCP 已覆盖 Agent 需求，不另做 AI 专用页；落地页 JSON-LD 的 offers 须随改价同步。
- **runtime**：`pyobfus_runtime` 源码有改动必须先升版本、先发 runtime（`scripts/check_runtime_version.py`）。
- **本机 Python 3.15**：常规检查使用 `~/venvs/py315_20261020`；已发布 wheel 的全新安装验证可按 `../workspace-meta/VENV_INDEX.md` 使用一次性环境。
- **Affiliate**：只有设计（`docs/AFFILIATE_PROGRAM_DESIGN.md`），条款未生效；实现前须补幂等、退款／争议、隐私与财税确认，文档完成不等于授权实现。
- **Claude 插件市场**：仓库锁已升级到 Anthropic 内部，等支持回复；锁未释放前不要重提表单或换路径（证据见私有 `docs/internal/CLAUDE_PLUGIN_RESUBMISSION_2026-09-22.md`）。
- **IP**：专利标识与专有许可专利条款待随版本发布，见 `docs/TODO.md`「IP 相关」；法务侧在仓库外 `pyobfus-legal/`。
- **self-dogfooding**：四条 lane 为观察模式，`Dogfood` workflow 刻意不是必需检查。
- **公开记录**：客户、付款、下游部署与支持过程只写进私有记录，公开文档写抽象工程事实（`AGENTS.md`「Public vs private records」）。



## 历史进展（已下沉）

09-24 以前的逐次发版/排障记录（0.5.6 → 0.5.29、Glama、VS Code 插件 M0–M3、许可系统 09-13 事故、
专利申请时间线）已原样移到 [`docs/CLAUDE_MD_HISTORY.md`](docs/CLAUDE_MD_HISTORY.md)；
逐轮细节以 `docs/CURRENT_PLAN_ZH.md` 为准。本文件只放当前生效的约定。

## 反复踩过的坑（仍然生效）

- **AI 安全分类器误判（dual-use）**：本仓是正规的开源 + 商用混淆器（专利 `202610712171X`），源码里本就含 `obfuscate`/`encrypt`/`anti_debug`/`license`/`string_enc` 等词；对自己源码的只读检索或编辑有时会被模型 `[cyber]` 误判并中断当轮（回退到弱模型）。**这不是错误也不是违规**：重跑同一条命令通常即过，或用 `/config` 换回强模型重试，并用 `/feedback` 反馈。减少误判的习惯与反馈模板见 [`docs/DUAL_USE_CONTEXT_AND_SAFETY_FLAGS.md`](docs/DUAL_USE_CONTEXT_AND_SAFETY_FLAGS.md)：优先用 Grep/Read 工具而非长管道 shell、单条命令别堆砌多个安全敏感词、在描述里写清是「保护自有源码」的良性意图。

- **注册表传播延迟不是发布失败**：PyPI JSON 已显示新版后 pip 仍可能短时间 `No matching distribution`；
  Open VSX 上传后约 160 s 版本端点才不 404；Zenodo webhook 202 后约 2.5 h 才归档。等，别重试。
- **本地 editable 元数据会过期**：核验「输出里的版本号」前先 `pip install -e .`，否则 marker/report 写旧版本。
- **`[project.urls]` 与 README 文字修复要发版才到 PyPI**（打包时固化）；README 顶部 shields.io 徽标是动态的，不用改。
- **许可系统顺序硬约束：先部署 Worker，再发客户端**（`pyobfus-license deactivate` 等新路由）。
  已装客户机器 Pro 激活仍需 `pyobfus-license register <KEY> --no-verify`（0.5.26 修复只救新安装）。
- **发布后查完整 CI 矩阵**，不只 Release/CodeQL workflow。
- **CI 任务绿 ≠ 测试通过（10-21）**：旧 Windows 步骤用 PowerShell 连跑两条 pytest，只看末条退出码，3.9/3.14 及 0.8.0 发版 run 的核心失败都显示绿；已改 bash（PR #109）。必需检查现为 `CI result` + `CodeQL`；普通推送 13 个核心组合，全 21 组合只在每日定时/手动跑——要全矩阵就 `gh workflow run ci.yml --ref <分支>`。详见 `docs/TODO.md`「CI 提速」。
- **Stripe / 许可 Worker（10-05）**：Worker 只对 `payment_status=paid` 发号、序列号由 HMAC(webhook secret, session id) 派生——
  **别 Roll webhook signing secret**（验签全挂、派生也会变）；Payment Link 是 API 创建，Dashboard 不能编辑；
  Dashboard 首页「Blocked」先点开看时间线再判断是否流失客户。详见 `docs/TODO.md` 维护者清单。
- **拿不到访问权 ≠ 东西不存在**：API 返回 401/`not_found` 不能当「未收录」证据，用公开搜索页核实。
- 发版是独立 gate，须用户明确批准；当前节奏见上文「节奏」一条与 `docs/TODO.md`。

## 专利 / IP（当前状态）

- 发明专利 `202610712171X`（申请日 2026-05-22）已**初审合格**（2026-06-17），费用缴清；约 2027-11 公布，
  下一硬期限 = 实审请求 ≈2029-05-22（实审费已缴）。v0.5 机制已于 v0.5.0 公开发布。
- 冷启动资料：`~/projects/pyobfus-legal/patent/SESSION_LOG_20260617.md`（最新时间线）· 官方通知书正本
  `~/projects/pyobfus-legal/patent/08_提交记录/` · memory `patent_correction_notice_2026-06-01.md`。
- 与本地私有仓库 `~/projects/cac-plus-ip/` 共享同一申请人、费减备案与 CNIPA 申请模板；跨项目索引见该仓 `CLAUDE.md` 与 memory `ip_workflow_cross_project.md`。
- **红线**：`pyobfus-legal/` **永不入 git**（含 PII）。命名清单见 memory `pro_disclosure_finding_2026-05-09.md` + `pyobfus_patent_strategy.md`。

## 项目概述

- **定位**: Python 代码混淆器 (开源 + 商业双许可)
- **技术栈**: Python 3.9-3.15, AST, setuptools
- **PyPI 主包**: https://pypi.org/project/pyobfus/ (**latest v0.14.0，2026-11-11 发布**；完整版本历史见 `CHANGELOG.md`）
- **Smithery**: 已下线——Smithery 并入 Arcade 后技能目录取消，2026-11-07 核实原技能页 404；`smithery.yaml` 已删除。**mcp.so**: 已收录
- **Glama Listing**: https://glama.ai/mcp/servers/zhurong2020/pyobfus — 渠道 release **0.14.0**（11-13 03:57 北京时间，维护者手工 Build & Release；release 说明取自 GitHub Release，后台已开 Auto-Release；test `01a1d155-5ae8-767a-816e-dc0d2966670a`；此前 0.13.1／test `01a1cd2b`），Build steps 为 `pyobfus-mcp==0.3.17 pyobfus==0.14.0`；发 Core 或 MCP 后须手工改：Admin → Dockerfile → Build steps，点「Build & Release」（另一按钮「Build」只测试不发布）。checkout 与 Python 实装边界见 `docs/CORE_012_CHANNEL_FOLLOWUP_2026-11-04.md`。

- **GitHub Action**: https://github.com/zhurong2020/pyobfus-action (**v1.1.0**，2026-11-04 发布，移动 `v1` 同指 `3237e16`，Marketplace 最新版本已核：<https://github.com/marketplace/actions/pyobfus-scan-and-build>)。独立仓库**是硬性要求**——Marketplace 要求 `action.yml` 在仓库根目录且一仓一 action；另外 action 的移动 `v1` tag 会与 Core 的 `v*` 命名空间冲突并重新触发 `release.yml`。⚠️ 两个只会在上架页面才暴露的限制：**listing 名不能与已有 GitHub 用户重名**（`github.com/pyobfus` 是第三方账号，故名为 `pyobfus scan and build`；GitHub **不因不活跃释放用户名**，只受理商标投诉，此事已定论），以及 **description 上限 125 字符**（首版 151 被拒 → v1.0.1）。两条现均由该仓库 CI 断言拦截。**归因查询**（本 action 存在的理由，周期性复盘时与下载量一起看）：<https://github.com/search?q=%22zhurong2020%2Fpyobfus-action%22+path%3A.github%2Fworkflows&type=code>
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
├── tests/             # Core 测试；各测试根须按 AGENTS.md 分开运行，最新验收见 CURRENT_PLAN_ZH.md
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

# 一次性激活仓库内钩子（每个 clone 各自做一次）：pre-commit 拦 PII/凭证，pre-push 跑 scripts/check.sh
git config core.hooksPath .githooks
```

**pre-commit 防护钩子**：`.githooks/pre-commit` 有三道**互相独立**的扫描。① PII：拦截 `诸嵘 / 陈启稚 / qizhi_chen / 身份证 / /home/wuxia/` 5 个模式，源于 2026-05-03 的 git 历史改写（见 `docs/V0.4_EXECUTION_LOG.md` Sessions 13-15）。② 凭证（2026-09-07 加）：拦截 Open VSX/PyPI/GitHub/GitLab/npm/Anthropic/OpenAI/AWS/Slack/Google token 前缀与 PEM 私钥头，命中时**只打印 `file:line` 不打印内容**。③ 客户/经营数据（2026-10-29 加，只查新增行）：Stripe 对象 ID 与白名单外的邮箱，`commit-msg` 钩子对提交信息做同样检查。三道各有独立旁路（`PYOBFUS_ALLOW_PII=1` / `PYOBFUS_ALLOW_SECRET=1` / `PYOBFUS_ALLOW_CUSTOMER_DATA=1`），放行 PII 不会顺带放行密钥。详见 `.githooks/README.md`。

### 测试

```bash
pytest tests/ -v
pytest tests/ -v --cov=pyobfus --cov-report=html
pytest tests/ -n auto --no-cov     # 并行（pytest-xdist 在 dev extra 里），约快 3 倍
pytest integration_tests/ -v
```

**ℹ️ Python 3.8 已于 0.5.0 移除**（EOL 2024-10，floor 升到 3.9）：当年 `astunparse` 在 3.8 上的 CLI 集成测试 flaky 问题随之消失，`@requires_py39` 装饰器现为 no-op（可逐步清理）。`docs/PYTHON38_COMPATIBILITY.md` 仅作历史记录保留。

### 代码规范

- 格式 / lint / 类型 / 文档站：一律跑 `scripts/check.sh`（与 CI 同一份路径清单，pre-push 钩子也跑它）。
  **不要手打 `black pyobfus/` 之类的缩短命令**——CI 查 10 个路径，09-20 就因只有 CI 查的 `tests/` 文件连红 9 次推送。

### 发布流程

1. 更新 `pyproject.toml` 版本号
2. 更新 `CHANGELOG.md`
3. **同一提交里顺手更新 `README.md` 的"What's new in vX.Y.Z"横幅**（打 tag
   之前）——PyPI 包一旦发布不可变，README 快照就是发布那一刻的 `main`；
   若这句更新拖到打 tag 之后的单独 docs-sync 提交里，就会正好被已发布的
   包错过，PyPI 页面 description 从此永久落后一个版本，只能等下次自然
   发版才带上（2026-08-17 v0.5.14 实际踩过这个坑，处置见
   `docs/CURRENT_PLAN_ZH.md` 当前状态块）。
3a. **Agent 文档同步**：改变 Agent 可见行为（参数、退出码、JSON、授权、MCP 工具）的版本，同一提交里更新 `llms.txt`/`llms-full.txt`（及 `docs/` 镜像）、`templates/ai-integration/AGENTS.md`、`skills/*/SKILL.md`、`ai-catalog.json`（清单见 `docs/TODO.md`「每次发版的 Agent 文档同步」；0.11.1/0.12.0 曾漏，11-06 补）。
3b. **IP 边界**：专利申请覆盖的机制只能实现在 `pyobfus_pro/` 或 `pyobfus-runtime`，不得进入 Apache-2.0 核心（Apache-2.0 §3 会把核心代码涉及的专利权免费授出）；核心只做 CLI 转发。对外标识只能写「专利申请中，尚未授权」。
4. `python -m build && twine upload dist/*`（或走 `git tag vX.Y.Z && git push --tags`
   触发 `.github/workflows/release.yml` 的 OIDC 自动发布，是当前实际使用的路径）
5. **发布后**更新 `CITATION.cff` 的 `version` / `date-released`：Zenodo 的 GitHub
   集成会**自动归档每个 GitHub Release**，concept DOI 随即指向新归档，cff 落后就
   与实际归档对不上。先查证再改，别照抄版本号：
   `curl -sL -H "Accept: application/json" https://doi.org/10.5281/zenodo.20846053`
   看重定向到哪个 record，再拉 `https://zenodo.org/api/records/<id>` 读
   `metadata.version`，同时把注释里的 version DOI 换成该 record 的 DOI。
   （0.5.24 与 0.5.25 各漏过一次，均为事后补。）

**⚠️ 区分两类内容，别把动态徽标误判成需要手动更新的静态文案**（2026-08-17
教训）：README 顶部 `[![PyPI version](https://img.shields.io/pypi/v/pyobfus.svg)]`
这一行徽标是**动态生成**的，shields.io 每次都会实时查 PyPI 最新版本号，
**从来不需要手动改这行 markdown**——它显示旧版本号只可能是缓存滞后（shields.io
自身 + GitHub camo 代理两层 `max-age=10800`（3 小时）缓存，或用户浏览器自己
缓存了图片），耐心等或强制刷新页面（Ctrl+Shift+R）即可，**不是**上面第 3
步说的那种"打包时固化、发布后不可变"的问题，不要为此改代码或重新发版。
真正需要在打 tag 前更新的只有 README 里**文字内容**（"What's new in
vX.Y.Z"横幅），跟徽标是两回事。

## 注意事项

- **公开仓库**: 不要提交 Pro 许可密钥或 Stripe Webhook Secret
- **跨版本兼容**: 确保 Python 3.9-3.15 全部通过测试
- **双许可模型**: Free (pyobfus/) 和 Pro (pyobfus_pro/) 代码分离管理

## 跨 Workspace 关联

| 关联项目 | 所在 Workspace | 关系 |
|----------|---------------|------|
| `pyobfus-legal/` | cardiac-research.code-workspace（WSL 本地同级目录 `~/projects/pyobfus-legal/` · 2026-09-21 起为真实目录，不再是 OneDrive 软链接）| pyobfus 软著 + 专利申报材料的物理仓库（**不在 git repo 内** · 含 PII，不公开）。包含 `software_copyright/` (V0.4.0 软著已 2026-05-09 提交 CCPC) 和未来的 `patent/` (v0.5 专利申请目录)。物理路径：`~/projects/pyobfus-legal/`（旧 OneDrive 副本 `/mnt/c/onedrive/msft/OneDrive - MSFT/rong/3-job/program/pyobfus-legal/` 已过期勿再编辑），工作区入口：`~/projects/pyobfus-legal/`（symlink） |
| `pyobfus-pro-dev/` | 本地 `~/projects/pyobfus-pro-dev`；GitHub `zhurong2020/pyobfus-pro-dev`（**private + archived，只读，推送 403**） | **专利 `202610712171X` 的发明/实现时间线证据库，不是开发源**。v0.5 Pro 机制 2026-05-09 起在此开发（早于 05-22 申请日），06-17 初审合格后 squash 合入公开仓库，逐提交历史只在这里；`pyobfus-legal/patent/01_权利要求书/disclosure_v1.md` 依据其 `PATENT_NOTES.md`（28 条）与集成测试撰写，第 12 节引用它。**用途**：实审请求（≈2029-05）、审查答复、无效/维权时证明实现时间与方式。**规则**：保留远端归档、不删不公开；不在其中开发/发版/拷回公开仓库；跨仓同步时跳过它。2026-10-14 远端已包含两个历史标记/`.gitignore` 提交，仍为 archived；10-11 已删本地 `venv-3.10/`。可选加固：`git bundle` 离线备份放 `pyobfus-legal/patent/`（未做）。 |
| `cac-plus-ip/` | 本地私有仓库（同 workspace） | 同申请人的并行 IP 工作流，与 pyobfus 内容无关；可复用其 CNIPA 申请模板，项目材料保持分离。 |
