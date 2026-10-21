# pyobfus 开发约定

Modern Python Code Obfuscator - 基于 AST 的 Python 代码混淆器。

> 通用 agent 约定(build/test/lint、仓库结构、专利 gate 等)见根目录 [`AGENTS.md`](AGENTS.md)(规范源,工具无关)。本文件保留 Claude / 中文 / 专利申报相关的项目专属细节。
>
> @AGENTS.md

## ⚡ Current pending work (cold-start 必读)

**Single source of truth for current plan**: [`docs/CURRENT_PLAN_ZH.md`](docs/CURRENT_PLAN_ZH.md) — 重启 session 第一份必读

**下一步做什么**: [`docs/TODO.md`](docs/TODO.md) — 排期清单（顺序 + 验收标准 + 周期性任务），依据见 `docs/FEATURE_EXPANSION_RESEARCH_2026-09-12.md`

`docs/ROADMAP.md` 和 `docs/POST_V0.4_TODO.md` 已归档为历史执行记录和细节来源。日常优先级、外部 blocker、下次工作建议都以 `docs/CURRENT_PLAN_ZH.md` 为准。

### 2026-10-20 — Core 0.8.0 已发布：Python 3.15 支持（冷启动先读 `docs/CURRENT_PLAN_ZH.md` 顶部）

PR #108（PY315-1 惰性导入保留、PY315-2 推导式解包、3.15 新内建名保留、3.15 三平台 CI）由无头 Codex 实现、Claude 独立审核后合并并发布；PyPI/PEP 740/全新 3.15 与 3.10 安装/GitHub Release/Zenodo `23500657`/CFF 均已核。同晚维护者批准发 MCP 0.3.14（3.15 分类器 + #103 提示）：PyPI/PEP 740、全新 3.15 安装握手 0.3.14/9 tools、MCP Registry active/isLatest 均已核；runtime 0.1.1、VS Code 不发。Glama 10-21 已改装 0.3.14/0.8.0 并测试通过（9 tools）。本机跑 3.15 用工作区登记的 `~/venvs/py315_20261020`（路由见 `../workspace-meta/VENV_INDEX.md` §0，按需 `pip install -e .`），不要再建新 venv；10-20 审核用的源码编译 3.15 在 `/tmp`，已不可依赖。遗留（3.15 标准库 json/unittest 冒烟、free-threaded 未验证、black py315 告警）见 `docs/TODO.md` 10-20 段。医院应用仍暂停。

### 2026-10-18 — 历史 session 收尾

同日发布 Core 0.7.4（缺陷 N #102、H PR 4 选项 1 #103）与 0.7.5（缺陷 O #104、P #105），均 Codex 实现 + Claude 审核、全渠道核实。医院版 cand4 闸门等现场 Win7→Win10 答复；参数改名暂缓，B2/B3 等触发；DEV 第 2 篇 10-27 发。代码修改先交无头 Codex（注意 5 小时额度，沙箱 `.git` 只读时由 Claude 提交/推送）；合并与发版各需维护者明确批准。交接见 `../workspace-meta/archives/SESSION_CLOSEOUT_20261018_PYOBFUS_074_075.md`。

### 🟢 2026-10-12 — Core 0.7.0 + runtime 0.1.1 已发布；路线图复核修复随发（冷启动先读 `docs/CURRENT_PLAN_ZH.md` 顶部 10-12 段、路线图 §13、`docs/TODO.md`「增强路线复核」）

### 🟢 2026-10-11 — 限制 H 三个实现 PR 合并、默认开启；下一版 0.7.0 待 10-13 拍板（冷启动先读 `docs/CURRENT_PLAN_ZH.md` 顶部 10-11 段与 `docs/TODO.md`「下一版 Core 0.7.0」）

### 🟢 2026-10-10 — Core 0.6.1 已发布（G #66 + F 方案 A #67）

### 🟢 2026-10-08 — Core 0.6.0 已发布

- **0.6.0**（tag `v0.6.0` → `30cb13b`）：目录构建默认改函数局部变量（#57，`--no-crossfile-local-names` 可关），
  修复三个 0.5.32 既有缺陷：类体引用同名方法（#62）、单文件改函数内定义名（#63）、单文件改类体注解字段（#64，dataclass 关键字构造报错）。
  PyPI（PEP 740，publisher=release.yml）、全新安装、GitHub Release、Zenodo `23228339`、`CITATION.cff` 均已核；发布提交 CI 全绿。
  MCP 未随发（`pyobfus_mcp` 的 `[Unreleased]` 仍待定）。
- 同日收尾：参数改名设计 PR #65 已审（待维护者拍板 6 个决定）；新登记缺陷 G（目录构建 `from x import f as g` NameError）、
  F（单文件默认改参数不改关键字调用）。下一步顺序 G → F → 参数改名，见 `docs/TODO.md` P0 段。

- Claude 交叉审核三个 PR 后修复 #57 的三处问题（函数内定义的函数/类名不再改、注解作用域顺序、symtable 报错按文件降级），
  三个 PR squash 合并：Worker CI `f65be9a`、打包 lane `26337d8`、目录构建局部变量改名 `81df698`；main CI 全绿。
  报告私有 `docs/internal/geo-2026-10/CROSS_REVIEW_2026-10-08.md`。下一步与两个既有缺陷见 `docs/TODO.md` P0 段。

### 🟢 2026-10-07 — Core 0.5.32 已发布（同日 0.5.31 + 0.5.32，提前结束静默期）+ GEO 第一轮 + 目录构建改名深度 P0（历史记录，当前入口见 10-20 段）

- **10-07 第二版 `0.5.32`**：修复自 0.5.10 起目录构建里同模块装饰器/基类/元类/lambda 引用 NameError（#58），
  PyPI/PEP 740/Release/Zenodo `23212358`/CFF 已核。PR #57 审核意见：私有 `docs/internal/geo-2026-10/PR57_REVIEW.md`。
- **10-07**：维护者批准提前发 `0.5.31`（目录构建不删 docstring 属「影响用户的 bug」例外；另带 `--unmap` 位置参数与
  mapping 不匹配告警）。PyPI/PEP 740/GitHub Release/Zenodo `23210576`/CFF 全部核实。MCP 未随发。
  **P0**：目录（cross-file）构建只改模块级名字，第 1 步改函数局部变量——Codex 实现、Claude 审核，10-08 已合并（见上段）。
  GEO 方案私有原件与基线在 gitignored `docs/internal/geo-2026-10/`、`docs/internal/geo-observations/`。

- **内容引流改为定期发（2026-09-27 定）**：10-11 前只写不发，10-13 那周起 DEV 双周一篇、arong.eu.org + 知乎月度、
  微博不发 pyobfus；Show HN 已用完。**未发稿件放 gitignored 的 `docs/internal/content-*/`，不进 `_drafts/`**。
  排期与退出条件见 `docs/TODO.md`「内容节奏」。第 1、2 篇草稿已写待维护者审（第 2 篇头注释列了发稿前必须核的三条事实）。
- **AI/Agent 内容（09-28 定）**：`llms.txt`/`AGENTS.md`/MCP 这层已完整，**不另做 AI 专用页**；缺口用文章补
  （选题第 7 篇「混淆后让 AI 助手继续调试」排 11-24）。落地页已有 `SoftwareApplication` JSON-LD，改价须同步其 offers。
  每周一巡检跑 `python scripts/download_snapshot.py`（已含 GitHub 流量来源）；09-30 巡检记录在 `CURRENT_PLAN_ZH.md` 顶部。
  只留决策摘要、不存完整 stdout 或另建 CSV/JSON；10-25 复盘后改为月度留存，细则见 `docs/TODO.md`「节奏」。
- **IP 后续（09-28 登记，待拍板未执行）**：提前公布 / 专利标识 + 专有许可补专利条款（随 11 月月度版本）/ 出海建议否、
  2027-03 复核（优先权窗口 2027-05-22）。仓库侧见 `docs/TODO.md`「IP 相关」，法务侧 `~/projects/pyobfus-legal/IP商业化迁移_TODO.md`。
- **Affiliate 只完成设计，未上线**：邀请制 3–5 人、无 cookie、签名 Stripe reference、20% / 30 天
  / 月结 / $50；公开设计 `docs/AFFILIATE_PROGRAM_DESIGN.md`，条款草案明确未生效。实现前先补 Worker
  event/session 双幂等、paid/async、refund/dispute、隐私日志、测试、KV 备份、Privacy/最终条款与财税确认；
  **文档完成不等于授权实现/部署**，且不需要 Core 发版。
- **`0.5.29` 已发布并全渠道收尾**（runtime import 切换 + builder 声明 `pyobfus-runtime>=0.1,<1` 依赖
  + provenance `runtime_requirement` + Pro 导入失败提示；PyPI/PEP 740/全新装/Release/Zenodo record `22949529`
  /`CITATION.cff` 均核实）。Zenodo webhook 送达(202)但约 2.5h 才归档——延迟不是失败。
- **Core `0.5.30` 已发布**：**Y-2 `--expire-warn-days`**（到期前告警不停机）+
  **Y-3 `--bind-key-env`**（L3 密钥改由应用提供，一次构建跑任意授权机器；v1 仅 L3，配 `--vault` 报错、
  与 `--bind-device` 互斥；`docs/Y3_KEY_PROVIDER_DESIGN.md`）。真实下游 Pro 缺口 Y-1/2/3 全清零。
  用户 09-26 明确要求立即发版；本地四测试根、quality 与 Lane C 候选 wheel 全绿，远端 CI 27/27 +
  CodeQL 全绿，tag 经 OIDC/PEP 740 发布，PyPI 全新安装和 GitHub Release 已核实；Zenodo record
  `22986080` 与 `CITATION.cff` 也已同步。自本版起进入 10-25 前静默观察期。
- **self-dogfooding 四 lane 已落地为观察模式**：`dogfood/canary/` + `scripts/dogfood/run.py` +
  非阻塞 `Dogfood` workflow（**刻意不是必需检查**）；升 PR gate 是单独 reviewed 步骤。
- **Claude plugin：孤儿仓库锁已由真人支持 Rudy 于 09-28 升级到 Anthropic 内部**，等其跟进（球在对方）。维护者查
  `wuxiami@hotmail.com` / `zhurong0525@gmail.com` / `zhurong0525@icloud.com` 均无 08-02
  确认邮件；同一公开仓库根路径稳定复现锁报错。09-26 已在 Rudy 原线程附「No submissions yet」与
  repository/path lock 两张截图、三个候选邮箱及 Claude Code workspace ID，请求后端定位/释放。
  **现在等支持回复；锁没释放前别再点表单或换路径绕过**。证据与字段见
  `docs/internal/CLAUDE_PLUGIN_RESUBMISSION_2026-09-22.md`。
- 其余维护者动作不变（MCP Trust Registry publish 需 token / AlternativeTo 提交 / OneDrive 删两旧副本）；
  awesome-python PR #3352 被拒（采用量·含镜像口径）、Vercel 卸载、giscus 保留、`pyobfus-pro-dev` 归档。
- **09-25 下午 P0（用户列，当日完成）**：trial 服务端上线 5 天登记 0；KV 每日备份脚本此前不认
  `trial:*` 记录（第一条会让许可备份静默停止）→ 已按类型校验 + 自检 + 挪进日备份随 systemd 补跑，
  09-24/25 漏导已补。脚本在 `~/scripts/`（仓库外）。详见 `docs/CURRENT_PLAN_ZH.md` 09-25 下午段。
- **节奏改了（09-25 用户定 · 0.5.30 发版后生效，先测一轮；10-07 因两个用户可见 bug 例外发 0.5.31/0.5.32，静默期提前结束，
  10-25 复盘用 09-27→10-06 窗口）**：静默 4 周（10-25 前不发 Core）→ 每月一版
  → 只做有触发的事 → 每周一巡检；全文 `docs/TODO.md`「节奏」段。**查进度固定动作：进度 + 下载量
  （`python scripts/download_snapshot.py`）+ Gmail（`/pyobfus-inbox`），三样一起给**，缺一样不算查过。
- 「当前状态一句话」：Core 0.8.0（Python 3.15 支持 #108，PY315-1/2，Codex 实现 + Claude 审核）于 10-20 发布；此前 Core 0.7.5（缺陷 O 星号下标括号 #104、P sys.modules 变更方法 #105）与 0.7.4（缺陷 N #102、H PR 4 选项 1 #103）均于 10-18 发布；0.7.3 为缺陷 C/M、0.7.2 为缺陷 I；同晚 MCP 0.3.14（3.15 分类器 + #103 提示），runtime 0.1.1 不变，MCP 9 工具；发布核验见 `docs/CURRENT_PLAN_ZH.md` 顶部。下游医院应用整体暂停，等待现场后续回复；微信付款未完成买家已于 10-14 发跟进邮件、被动等待。以后 runtime 源码改动仍必须先升版本、先发 runtime。


## 历史进展（已下沉）

09-24 以前的逐次发版/排障记录（0.5.6 → 0.5.29、Glama、VS Code 插件 M0–M3、许可系统 09-13 事故、
专利申请时间线）已原样移到 [`docs/CLAUDE_MD_HISTORY.md`](docs/CLAUDE_MD_HISTORY.md)；
逐轮细节以 `docs/CURRENT_PLAN_ZH.md` 为准。本文件只放当前生效的约定。

## 反复踩过的坑（仍然生效）

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
- 与 cac-plus-ip 共享同一申请人与费减备案，跨项目索引见 `~/projects/cac-plus-ip/CLAUDE.md` + memory `ip_workflow_cross_project.md`。
- **红线**：`pyobfus-legal/` **永不入 git**（含 PII）。命名清单见 memory `pro_disclosure_finding_2026-05-09.md` + `pyobfus_patent_strategy.md`。

## 项目概述

- **定位**: Python 代码混淆器 (开源 + 商业双许可)
- **技术栈**: Python 3.9-3.15, AST, setuptools
- **PyPI 主包**: https://pypi.org/project/pyobfus/ (**latest v0.8.0，2026-10-20 发布，新增 Python 3.15 支持**；完整版本历史见 `CHANGELOG.md`)
- **VS Code 插件**: https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus (**latest v0.4.3，2026-09-10 发布**；Marketplace 与 Open VSX 两边同版本，均已 `curl` 独立复核；publisher `zhurong2020`；独立版本节奏，见 `vscode-extension/CHANGELOG.md`。**发版必须两个 registry 都发**：Marketplace 手工上传 + `ovsx publish`，runbook 见 `docs/OPEN_VSX_PUBLISH_PLAN.md`)
- **PyPI MCP 包**: https://pypi.org/project/pyobfus-mcp/ (**latest v0.3.14，2026-10-20 发布，加 3.15 分类器 + #103 未证明访问提示**；9 tools: 7 community + 2 pro_funnel · dep `pyobfus>=0.5.18` · `uvx pyobfus-mcp` 零安装；完整版本历史见 `pyobfus_mcp/CHANGELOG.md`)
- **MCP Registry**: `io.github.zhurong2020/pyobfus-mcp`（**0.3.14** 2026-10-20 发布并核实 `active` / `isLatest=true`）
- **Smithery (Skill)**: https://smithery.ai/skills/zhurong2020/pyobfus-protect (2026-06-22 上线 · 本地工具走 Skill 渠道非 MCP 渠道) · **mcp.so**: 已收录
- **Glama Listing**: https://glama.ai/mcp/servers/zhurong2020/pyobfus — 已上架；2026-10-14 维护者曾将 Build steps 固定为 `pyobfus-mcp==0.3.13 pyobfus==0.7.1`，启动/握手 0.3.13 / 9 tools 测试成功，12:33 渠道 release 0.7.1 已明确发布。10-17 Build steps 已改为 `pyobfus-mcp==0.3.13 pyobfus==0.7.3`，测试 `01a14684` 通过（Core 0.7.3、9 tools，渠道 release 0.7.5）；构建检出 `964b248`（仅文档后代，不影响所装包）。10-21 Build steps 改为 `pyobfus-mcp==0.3.14 pyobfus==0.8.0`，测试 `01a15a11` 通过（9 tools，渠道 release 0.7.7）。下次发 MCP 或 Core 同步更新包版本。详细历史与验收条件见 `docs/DISTRIBUTION_CHANNELS.md` / `docs/TODO.md`。

- **GitHub Action**: https://github.com/zhurong2020/pyobfus-action (**v1.0.1**，2026-09-10 建仓发版并上架 Marketplace：<https://github.com/marketplace/actions/pyobfus-scan-and-build>)。独立仓库**是硬性要求**——Marketplace 要求 `action.yml` 在仓库根目录且一仓一 action；另外 action 的移动 `v1` tag 会与 Core 的 `v*` 命名空间冲突并重新触发 `release.yml`。⚠️ 两个只会在上架页面才暴露的限制：**listing 名不能与已有 GitHub 用户重名**（`github.com/pyobfus` 是第三方账号，故名为 `pyobfus scan and build`；GitHub **不因不活跃释放用户名**，只受理商标投诉，此事已定论），以及 **description 上限 125 字符**（首版 151 被拒 → v1.0.1）。两条现均由该仓库 CI 断言拦截。**归因查询**（本 action 存在的理由，周期性复盘时与下载量一起看）：<https://github.com/search?q=%22zhurong2020%2Fpyobfus-action%22+path%3A.github%2Fworkflows&type=code>
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

**pre-commit 防护钩子**：`.githooks/pre-commit` 有两道**互相独立**的扫描。① PII：拦截 `诸嵘 / 陈启稚 / qizhi_chen / 身份证 / /home/wuxia/` 5 个模式，源于 2026-05-03 的 git 历史改写（见 `docs/V0.4_EXECUTION_LOG.md` Sessions 13-15）。② 凭证（2026-09-07 加）：拦截 Open VSX/PyPI/GitHub/GitLab/npm/Anthropic/OpenAI/AWS/Slack/Google token 前缀与 PEM 私钥头，命中时**只打印 `file:line` 不打印内容**。两道各有独立旁路（`PYOBFUS_ALLOW_PII=1` / `PYOBFUS_ALLOW_SECRET=1`），放行 PII 不会顺带放行密钥。详见 `.githooks/README.md`。

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
| `cac-plus-ip/` | cardiac-research.code-workspace（同 workspace 内）| **同申请人的并行 IP 工作流**。CAC Plus 医学 AI 项目的 3 件中国发明专利 + 2 件软著申请仓库。**与 pyobfus 内容无关、但工作流共享**：同一个 CCPC 账号 / 同一个 CPC 客户端 USB Key / 同一个 85% 个人申请减免资格 / 同一套 CNIPA 官方申请模板（位于 `cac-plus-ip/02_china_发明专利/_templates_CNIPA/`，pyobfus v0.5 专利申请直接复用，不重复下载）|
