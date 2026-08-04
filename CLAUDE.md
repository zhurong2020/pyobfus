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

**✅ README/MCP/ROADMAP 陈旧内容审计 + 修复，两轮 session 都做完了（2026-08-02）**：第一轮 5 项机械修复（ROADMAP.md 同步、MCP 元数据补 `ml` preset、Codex 补进全仓库、README 清理老版本号、plugin 目录问题 WebSearch 查清）。第二轮：**pyobfus-mcp 0.3.2 已发布**（PyPI + MCP Registry 均确认 isLatest，`mcp-publisher` 已跑）；plugin marketplace 提交流程查清 + 本地 `claude plugin validate` 已通过（实际提交需 user 自己登录网页操作，Claude Code 做不到）；Pro Edition 定位已讨论，user 认可方向。

**✅ Plugin marketplace 提交已完成（2026-08-02）**：Console 表单提交成功，显示"Plugin submitted for review"——状态是**待 Anthropic 审核**，不是已上线；`Link to plugin` 字段一度报 `must not contain spaces or control characters`（复制粘贴带入隐藏字符，手动重新输入后解决）。后续查审核结果看 `github.com/anthropics/claude-plugins-community`（审核通过后隔夜同步）或 Console 里的"View submissions"。

**⏳ Glama 后台 Dockerfile 版本号更新——尝试过，被 Glama 自己的 UI bug 卡住，user 改天再试**：user 能进后台管理页（`.../admin`，能看到 Profile/Analytics/Repository/Dockerfile 四个 tab），但点 Dockerfile tab 不跳转、又弹回 Profile 页，F12 有报错但没抓到具体错误文本。不是 user 操作问题，像是 Glama 前端路由 bug 或临时故障。**下次重试时先截报错原文**——这是唯一缺的信息，抓到就能真正定位，不然就是重试运气。详见 `docs/DOC_SYNC_AUDIT_2026-08-02.md` 第 3 节。

**✅ 已回填（2026-08-02 验证，原「下次 session 直接执行清单」①②两项其实早已完成）**：`docs/DOC_SYNC_AUDIT_2026-08-02.md`「Session 2 punch list」①② 两项实测 `README.md` 均已完成——① 锚点链接已是 `#-pro-edition`（README.md:21，非损坏的旧版 `#-pro-edition-available-now`）② Pro Edition 常驻提示行已在 README.md 第 21 行（`> **🔒 Pro Edition available** — 6 patent-targeted...`）。**仍待**：③ Glama 后台 Dockerfile 版本号手动更新（目标应是当前最新 **0.3.3**）。**2026-08-03 复查**：Dockerfile tab 不跳转的 UI bug 看起来自愈了（能正常打开、看到 Configuration 表单），但 user 反映"还是有问题"（具体报错未截取），且决定性的 **Build steps** 字段实际内容（是否还写死旧版本号）当场没能确认——**user 决定过几天再看**，下次重试先截 Build steps 字段的实际 JSON 内容 + 任何报错原文。**极小尾巴仍待**：plugin marketplace 提交描述里有个笔误"protected_project"应为"protect_project"，不影响功能，Anthropic 若跟进补充信息时顺手改。

**✅ 2026-08-04 UI bug 确认自愈 + Build steps 字段内容已拿到**：user 贴出完整 admin Dockerfile 页面，Profile/Analytics/Repository/Dockerfile 四个 tab 均正常可点，Configuration 表单完整显示，之前的路由 bug 不再复现（不需要再截 F12 报错）。**Build steps 字段实测写死 `["uv pip install --system --break-system-packages pyobfus-mcp==0.3.1"]`**——落后当前 PyPI latest 两个版本（0.3.1，应为 0.3.3），与此前记录一致：之前每次改到 0.3.2 的尝试都被那个路由 UI bug 卡住、从未真正提交成功，所以字段停留在最早的 0.3.1 原值，不是"改过又被覆盖"。Pinned commit SHA 显示 `b216665`、旁注"Current head commit: b216665 (sync)"，即该字段只是跟随 repo HEAD 自动同步、与 mcp 包版本号无关，**不用动**。改法：把 Build steps 数组里的 `pyobfus-mcp==0.3.1` 手动改成 `pyobfus-mcp==0.3.3`，保存后右侧 Dockerfile 预览里的 `RUN (uv pip install ...)` 那行应同步刷新为 0.3.3；Recent Tests 面板通常会因配置变更自动跑一次新测试，可用来确认。

**✅ 已确认保存生效（2026-08-04 同日）**：user 保存后贴出的页面截图核实——Build steps 字段与 Dockerfile 预览里的 `RUN` 行均已是 `pyobfus-mcp==0.3.3`；Recent Tests 新增一条 "Make Release"（`019fcb2e-4fbc-726b-b1f3-0064598f2e75`，2026-08-04 13:10），证明这次真的触发了重新构建，不是像 0.3.2 那次"改了没存住"。**Glama 版本同步任务本轮彻底收尾**，不用再问。

完整时间线 + 修复细节见 `docs/POST_V0.4_TODO.md` 顶部 handoff note + § item 7-8。

### ✅ 2026-08-02 又一轮 — pyobfus 0.5.7 + pyobfus-mcp 0.3.3 已发布

**pyobfus 0.5.7**：`--import-obfuscation`（Pro，P2-4，运行时 import 重写为 `importlib`/`__import__` + 自动开 AES 字符串加密）+ P2-22 诚实字节码对比内容（`docs/COMPARISON.md` 扩写 + README FAQ 指向）。tag `v0.5.7` 经 OIDC + PEP 740 attestations 发 PyPI（`pip download` 已核实可拉到），GitHub Release 已建（notes-only，同 v0.5.3/v0.5.4 惯例，无附件）。

**pyobfus-mcp 0.3.3**：纯内容修复（同 0.3.2 那类，非 tool 签名变化）——`recommend_tier`/`start_pro_trial` 硬编码的 Pro 机制清单此前只列 v0.5.0-0.5.4 那 4 项（Selective Opacity/watermarking/Vault/@seal_code），漏了 0.5.7 的 `--import-obfuscation`，同 `ml` preset 在 0.3.2 之前漏同步的同一类漂移。73 测试全绿，tag `mcp-v0.3.3` 发 PyPI + `mcp-publisher publish` 发 MCP Registry（两边都核实 isLatest），GitHub Release 附 wheel+sdist（同 mcp-v0.3.0 惯例）。

**🔁 新记录的后续任务（user 2026-08-02 要求，每次 cold-start 切换进本项目都例行做）**：
1. 查 pyobfus + pyobfus-mcp 的 PyPI 下载量（`pypistats recent pyobfus pyobfus-mcp` 或 `https://pypistats.org/api/packages/<pkg>/recent`）。
2. 核对「上次记录以来的修订」是否已同步进所有相关文档——不只 README/ROADMAP/POST_V0.4_TODO，**本文件自己的 cold-start 区块也是易漂移对象**（见下方一处已验证的活例子）。
3. 文档修复按主题拆开分别 commit，不要合并成一个大 commit（本 session `b9b5150`/`f6a70f1` 各自单一主题一个 commit 是范例）。

**📊 下载量基线（2026-08-02 首次记录，任务①的起点）**：pypistats.org `recent` 端点——**pyobfus** last_day 88 / last_week 210 / last_month 1016；**pyobfus-mcp** last_day 0 / last_week 12 / last_month 176。⚠️ pypistats 数据源（PyPI BigQuery 公开数据集）有 ~1-2 天延迟，上面的 `last_day` 实际反映的是 08-01 甚至更早，**不是**当天刚发的 0.5.7/mcp-0.3.3 的下载数。

**📊 第二次快照（2026-08-03）**：**pyobfus** last_day 232 / last_week 421 / last_month 1232；**pyobfus-mcp** last_day 178 / last_week 186 / last_month 348。pyobfus-mcp 从 0→178/天的跳变很显眼，但仍在 0.5.7/mcp-0.3.3（08-02 发布）的 1-2 天 BigQuery 延迟窗口内，大概率是发布流程本身（CI 校验/镜像同步/依赖解析）产生的下载，**不代表自然用户增长确认**——下次快照（08-04 之后）若仍维持高位才能算真实信号，不要提前当作发布反馈来解读。

**📊 第三次快照（2026-08-04）**：**pyobfus** last_day 38 / last_week 428 / last_month 1246；**pyobfus-mcp** last_day 10 / last_week 194 / last_month 346。**mcp 的 last_day 178→10 回落，证实了 08-03 那次跳变确实是发布当天的 CI/镜像同步噪声，不是真实用户增长**。周/月累计仍在小幅爬升（pyobfus 421→428 / 1232→1246；mcp 186→194，但月环比 348→346 微降），量级仍很小，暂无法判断是否为真实趋势，继续按例行任务隔天采点观察。

**已回填（2026-08-02，同一天）**：上面提到的活例子已经处理——本节原「下次 session 直接执行清单」①②两项已改标为 ✅ 已回填（见下方），user 当场要求就手，没有拖到下次 session。

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
- ✅ **pyobfus-mcp 0.3.2 已发布（2026-08-02）**：纯文档/元数据修复,补 `ml` preset + `codex` client,tag `mcp-v0.3.2` 发 PyPI + Registry(0.3.2 isLatest)。Glama 后台 Dockerfile 版本号手动改到 0.3.2 已尝试但被 Glama 自己的 UI bug 卡住(见上,已改天再试)。
- ✅ **AI-agent 可发现性 Wave A（2026-06-22）**：Smithery 经 **Skill 渠道** `zhurong2020/pyobfus-protect`（Smithery MCP 发布是远程网关、本地工具走不通,Skill 才对）+ mcp.so + `uvx` 零安装 + server.json 99 字描述(commit `826c576`/`49f4df3`)。报告:`docs/AGENTIC_DISCOVERABILITY_2026-06-22.md`。
- ❌ **JOSS 投稿被拒(2026-06-24)**:v0.5.1 投 JOSS(issue `openjournals/joss-reviews#10788`)被总编 desk-reject,理由=**scope/significance 非质量**("private-dev-then-public" + 无第三方复用)。→ 改走免费路径:✅ **Zenodo DOI `10.5281/zenodo.20846053`(concept)已拿到**,已接进 CITATION.cff + README 徽章 + `## Citation` + 两个 pyproject + RTD + ORCID + arong.eu.org/academic。完整记录+渠道对比见 `docs/JOSS_REJECTION_20260624.md`。
- ✅ **P2-18 内部证据完成（2026-08-01）**：5 样本 × Codex+Claude 全跑完，`price_rules` 拿到第一个干净跨模型 C4 数据点，决定不加第三个模型家族。评审版报告 `docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md`；过程中顺带修了 3 个既有 plumbing bug（语料库 no-op 稀释统计、`--json-schema` 不认 `$schema` meta key、docker 打分沙箱 temp dir 权限导致此前从未真实跑通），细节见 `docs/POST_V0.4_TODO.md` § P2-18。
- ✅ **pyobfus 0.5.5 已发布（2026-08-02，PR #26 + #27）**：`--preset ml`（P2-19，社区版模型服务 preset）+ `--provenance-manifest`（P2-17，本地 JSON 构建溯源清单，非加密签名）。Review 顺带发现 issue #25 并诚实标注在 CHANGELOG/docstring 里，不是掩盖。
- ✅ **pyobfus 0.5.6 已发布（2026-08-02）**：issue #25 修复（见上）+ CodeQL 高危告警清零（见上）。
- ✅ **README/MCP/ROADMAP 陈旧内容审计 + 修复（2026-08-02）**：见上，5 commits 全绿。
- ✅ **pyobfus 0.5.7 已发布（2026-08-02）**：`--import-obfuscation`（Pro，P2-4）+ P2-22 诚实对比内容。tag `v0.5.7` 经 OIDC + PEP 740 发 PyPI，GitHub Release 已建。
- ✅ **pyobfus-mcp 0.3.3 已发布（2026-08-02）**：`recommend_tier`/`start_pro_trial` 补 `--import-obfuscation` 到硬编码 Pro 机制清单（同 0.3.2 那类内容漂移修复）。tag `mcp-v0.3.3` 发 PyPI + Registry（isLatest），GitHub Release 附 wheel+sdist。
- ⏭️ **更后续**（完整清单见 `docs/POST_V0.4_TODO.md` 顶部「Current prioritized TODO」）:P2-13/P2-22 这类零代码内容型候选（PyInstaller cookbook / PyArmor 对比页）。Launch wave 已收工转被动监测(+7d/+30d checkpoint,不主动推)。IP 商业化迁移(个人→旎嵘科技)排在更后面。

**Cold-start session 第一句话应问 user**：「plugin marketplace 提交描述里那个"protected_project"笔误（应为 protect_project）要不要顺手改掉？另外查一下 plugin marketplace 审核结果出了没有。」（Glama Build-steps 已于 2026-08-04 确认改到 0.3.3 并保存生效，不用再问）

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
