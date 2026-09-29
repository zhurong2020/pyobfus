# pyobfus 开发约定

Modern Python Code Obfuscator - 基于 AST 的 Python 代码混淆器。

> 通用 agent 约定(build/test/lint、仓库结构、专利 gate 等)见根目录 [`AGENTS.md`](AGENTS.md)(规范源,工具无关)。本文件保留 Claude / 中文 / 专利申报相关的项目专属细节。
>
> @AGENTS.md

## ⚡ Current pending work (cold-start 必读)

**Single source of truth for current plan**: [`docs/CURRENT_PLAN_ZH.md`](docs/CURRENT_PLAN_ZH.md) — 重启 session 第一份必读

**下一步做什么**: [`docs/TODO.md`](docs/TODO.md) — 排期清单（顺序 + 验收标准 + 周期性任务），依据见 `docs/FEATURE_EXPANSION_RESEARCH_2026-09-12.md`

`docs/ROADMAP.md` 和 `docs/POST_V0.4_TODO.md` 已归档为历史执行记录和细节来源。日常优先级、外部 blocker、下次工作建议都以 `docs/CURRENT_PLAN_ZH.md` 为准。

### 🟢 2026-09-26/27 — Core 0.5.30 已发布 + plugin 孤儿锁待支持（最新 · 冷启动先读这段）

- **内容引流改为定期发（2026-09-27 定）**：10-11 前只写不发，10-13 那周起 DEV 双周一篇、arong.eu.org + 知乎月度、
  微博不发 pyobfus；Show HN 已用完。**未发稿件放 gitignored 的 `docs/internal/content-*/`，不进 `_drafts/`**。
  排期与退出条件见 `docs/TODO.md`「内容节奏」。第 1、2 篇草稿已写待维护者审（第 2 篇头注释列了发稿前必须核的三条事实）。
- **AI/Agent 内容（09-28 定）**：`llms.txt`/`AGENTS.md`/MCP 这层已完整，**不另做 AI 专用页**；缺口用文章补
  （选题第 7 篇「混淆后让 AI 助手继续调试」排 11-24）。落地页已有 `SoftwareApplication` JSON-LD，改价须同步其 offers。
  每周一巡检跑 `python scripts/download_snapshot.py`（已含 GitHub 流量来源）；09-28 巡检记录在 `CURRENT_PLAN_ZH.md` 顶部。
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
- **节奏改了（09-25 用户定 · 0.5.30 发版后生效，先测一轮）**：静默 4 周（10-25 前不发 Core）→ 每月一版
  → 只做有触发的事 → 每周一巡检；全文 `docs/TODO.md`「节奏」段。**查进度固定动作：进度 + 下载量
  （`python scripts/download_snapshot.py`）+ Gmail（`/pyobfus-inbox`），三样一起给**，缺一样不算查过。
- 「当前状态一句话」：`0.5.30` 是最新 Core；Core `[Unreleased]` 为空，10-25 前静默观察。逐轮细节见
  `docs/CURRENT_PLAN_ZH.md` 09-25 段 + memory `pyobfus_session_closeout_2026-09-25`。

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
- **技术栈**: Python 3.9-3.14, AST, setuptools
- **PyPI 主包**: https://pypi.org/project/pyobfus/ (**latest v0.5.30，2026-09-26/27 发布**；完整版本历史见 `CHANGELOG.md`)
- **VS Code 插件**: https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus (**latest v0.4.3，2026-09-10 发布**；Marketplace 与 Open VSX 两边同版本，均已 `curl` 独立复核；publisher `zhurong2020`；独立版本节奏，见 `vscode-extension/CHANGELOG.md`。**发版必须两个 registry 都发**：Marketplace 手工上传 + `ovsx publish`，runbook 见 `docs/OPEN_VSX_PUBLISH_PLAN.md`)
- **PyPI MCP 包**: https://pypi.org/project/pyobfus-mcp/ (**latest v0.3.12，2026-09-07 发布**；8 tools: 6 community + 2 pro_funnel · dep `pyobfus>=0.5.18` · `uvx pyobfus-mcp` 零安装；完整版本历史见 `pyobfus_mcp/CHANGELOG.md`)
- **MCP Registry**: `io.github.zhurong2020/pyobfus-mcp`（**0.3.12** 2026-09-07 发布，2026-09-10 已核实 `active` / `isLatest=true`）
- **Smithery (Skill)**: https://smithery.ai/skills/zhurong2020/pyobfus-protect (2026-06-22 上线 · 本地工具走 Skill 渠道非 MCP 渠道) · **mcp.so**: 已收录
- **Glama Listing**: https://glama.ai/mcp/servers/zhurong2020/pyobfus — 页面在线且渲染完整 8 工具，**状态：已上架且健康**（2026-09-07 核验：公开搜索 `?query=pyobfus` 返回该 server，A license / A quality / A maintenance，无 pending/unapproved 标记，详情页与徽章均 200）。2026-09-05 Frank Fiegel 邮件曾称「2026-05-03 被拒后从未批准、需重新提交」，**该说法已被公开目录证据证伪**——那封信的主题行是 5 月拒信 thread，应属照旧工单回复；**不要重新提交**（有产生重复条目 / 改动 URL 打断 README 徽章的风险）。⚠️ 方法教训：`/api/mcp/v1/...` 返回 `not_found`/`401` 曾被当作「不在目录里」的证据用了数周，401 只是**认证失败**（现对所有人要 API key），**拿不到访问权 ≠ 东西不存在**，正确探针是公开搜索页。admin「Build steps」**不会自动跟版**（停在 0.3.8、跨过 0.3.9/0.3.10，2026-09-06 由维护者手工改到 0.3.10；**已于 2026-09-07 手工改到 0.3.12**）；Glama 构建**不读仓库里的 `pyobfus_mcp/Dockerfile`**，而是用 admin Build Spec 合成一份。构建曾连续失败于其自家 BuildKit 拉 `debian:trixie-slim`（08-07 / 08-17 / 09-05 / 09-06 ×2），**2026-09-07 已确认修复**：test `01a07845-…` 详情页显式 `Status: success`/14s，8 工具握手正常。构建侧不再是阻塞项；**Glama 这条线已无待办**。历史排障见 memory `glama_introspection_dockerfile_pin_2026-06-05`、`glama_zero_tools_repro_2026-08-07`，最新证据见 `docs/DISTRIBUTION_CHANNELS.md`。
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
├── tests/             # 1352 passed + 1 skipped (2026-09-20 实测，含 reason-code 测试；+ pyobfus_mcp/tests 97 + integration_tests/ 12 + vscode-extension 53)
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

**pre-commit 防护钩子**：`.githooks/pre-commit` 有两道**互相独立**的扫描。① PII：拦截 `诸嵘 / 陈启稚 / qizhi_chen / 身份证 / /home/wuxia/` 5 个模式，源于 2026-05-03 的 git 历史改写（见 `docs/V0.4_EXECUTION_LOG.md` Sessions 13-15）。② 凭证（2026-09-07 加）：拦截 Open VSX/PyPI/GitHub/GitLab/npm/Anthropic/OpenAI/AWS/Slack/Google token 前缀与 PEM 私钥头，命中时**只打印 `file:line` 不打印内容**。两道各有独立旁路（`PYOBFUS_ALLOW_PII=1` / `PYOBFUS_ALLOW_SECRET=1`），放行 PII 不会顺带放行密钥。详见 `.githooks/README.md`。

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
- **跨版本兼容**: 确保 Python 3.9-3.14 全部通过测试
- **双许可模型**: Free (pyobfus/) 和 Pro (pyobfus_pro/) 代码分离管理

## 跨 Workspace 关联

| 关联项目 | 所在 Workspace | 关系 |
|----------|---------------|------|
| `pyobfus-legal/` | cardiac-research.code-workspace（WSL 本地同级目录 `~/projects/pyobfus-legal/` · 2026-09-21 起为真实目录，不再是 OneDrive 软链接）| pyobfus 软著 + 专利申报材料的物理仓库（**不在 git repo 内** · 含 PII，不公开）。包含 `software_copyright/` (V0.4.0 软著已 2026-05-09 提交 CCPC) 和未来的 `patent/` (v0.5 专利申请目录)。物理路径：`~/projects/pyobfus-legal/`（旧 OneDrive 副本 `/mnt/c/onedrive/msft/OneDrive - MSFT/rong/3-job/program/pyobfus-legal/` 已过期勿再编辑），工作区入口：`~/projects/pyobfus-legal/`（symlink） |
| `cac-plus-ip/` | cardiac-research.code-workspace（同 workspace 内）| **同申请人的并行 IP 工作流**。CAC Plus 医学 AI 项目的 3 件中国发明专利 + 2 件软著申请仓库。**与 pyobfus 内容无关、但工作流共享**：同一个 CCPC 账号 / 同一个 CPC 客户端 USB Key / 同一个 85% 个人申请减免资格 / 同一套 CNIPA 官方申请模板（位于 `cac-plus-ip/02_china_发明专利/_templates_CNIPA/`，pyobfus v0.5 专利申请直接复用，不重复下载）|
