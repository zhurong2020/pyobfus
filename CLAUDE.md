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

**✅ 2026-08-04 找到确切查询入口 + 状态确认**：权威地址是 **`https://platform.claude.com/plugins/submissions`**（Claude Console → Plugin submissions，需登录 user 自己的 Console 账号 `Rong / Shanghai Nirong Technology Co., Ltd.`）。页面显示 pyobfus 状态仍是 **"Submitted and pending review"**（提交于 2 天前，与 08-02 提交时间吻合，尚无 approve/reject 结论）。顺带核实了那个"protected_project"笔误确实还留在已提交的描述文案里（"One-call protected_project workflow..."一句）——继续维持"机会性修复"处置，不主动改，除非 Anthropic 跟进要求补充信息。公开旁证渠道（`claude-plugins-community` 仓库 `.claude-plugin/marketplace.json`，2298 个插件里搜 `pyobfus`）2026-08-04 同步核实：尚未出现，与 Console 状态一致。

**✅ Glama Dockerfile Build-steps 版本号已同步至 0.3.5（2026-08-06）**：user 贴出的 admin Configuration 页面核实 Build steps 数组与 Dockerfile 预览的 `RUN` 行均为 `pyobfus-mcp==0.3.5`，Recent Tests 新增一条 "Make Release"（`019fd4f7-f687-7f25-ab75-73bbc774acf9`，2026-08-06 10:47）。此前 2026-08-02~08-04 那轮"点 Dockerfile tab 不跳转"的路由 UI bug 已确认自愈，不再复现。**公开 API 目前仍返回 0 tools**——这是已知的 re-index 滞后模式（历史上最长 ≤1 天自行追上，2026-06-08 那次即是先例），不是新问题，不用现在采取行动，隔天复查一次即可。「Recent Releases」面板显示的 0.5.9/0.5.8/0.5.7 是 Glama 自增计数器、与实际安装的 mcp 版本号无关，忽略。完整历史时间线见 `docs/POST_V0.4_TODO.md` 顶部 handoff note + § item 7-8。

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

### ✅ 2026-08-04 又一轮 — Tier 1 六项全部发布 + 采用「间隔发布」节奏

**Tier 1 六项一次性做完并发布**（同一 session）：v0.5.8(P2-13 PyInstaller cookbook)→v0.5.9(P2-16 `--requires-os/-python-min/-arch`)→mcp-v0.3.4(P2-12 PII 检测)→v0.5.10(P2-14 `--embed-data`)→v0.5.11(P2-15 原生反调试)→mcp-v0.3.5(P2-21 工具描述完整性)。事前先核对代码现状（而非直接照单实现），发现 P2-6 其实早已发布（checkbox 没勾）、P2-12/P2-15 是部分实现——省下不少工作量，3 周预估压缩到一个 session。MCP Registry 补发布(mcp-0.3.4+0.3.5 → isLatest=0.3.5)走了 GitHub device-code 登录（教训：`mcp-publisher login github` **每次调用都生成新的一次性设备码**，别把旧码和新码搞混，只信最后一次实际在跑的那个进程输出的码）。

**🔁 用户明确要求：往后发布改成"间隔 1-2 天"节奏，不再合并批量发布**（今天这批 6 个是特例，已做完不用回滚）。机制沿用本项目自己 `docs/POST_V0.4_TODO.md` 一直在用的"等 N 天、下次冷启动查日期"套路，不建额外调度基础设施（`CronCreate` 只在单个对话 session 内有效，跨天不可靠，已排除）。**实操**：功能正常实现+测试+提交到 main，CHANGELOG 改动写在 `[Unreleased]` 段（不提前建版本号小节），version/tag/PyPI 发布留到 gate 日期到了再做。当前生效的 gate 见下方 P2-2 VSCode 插件条目。

**⭐ 下一优先方向：P2-2 VSCode 插件**——用户要求先查同类产品/竞品功能/网上热点趋势再设计，不要凭空写。已完成真实调研（非训练记忆）：竞品(PyArmor/Nuitka/Sourcedefender)都没有 VSCode 插件；查到一个真实的信任风险——2025-04 一个真叫"Python Obfuscator for VSCode"的恶意插件（XMRig 挖矿木马，30万+安装量才被下架），"python obfuscator"这个类目在 Marketplace 名声已被污染，pyobfus 的 listing 要明确亮出 OpenSSF/PEP740/provenance/tool-integrity 这些真实信任基建，不能只暗示；查到 2026 年 VSCode 插件最大的采纳驱动是"内联诊断"(Error Lens 模式)，且 Error Lens 本身不生成诊断、只是把已有的原生 `DiagnosticCollection` API 结果重新渲染——`pyobfus --check --json` 已经有现成的 line/col/severity 数据，接入原生 Diagnostics API 零核心代码改动，比"右键混淆"这种任何竞品都能抄的功能差异化强得多。完整方案（含分期里程碑、技术选型、已验证的 CLI JSON 契约）见 `docs/VSCODE_EXTENSION_PLAN.md`。

- ✅ **M0 已发布（2026-08-06，pyobfus 0.5.12）**：`pyobfus-trial status --json` + `pyobfus-license status --json`（同 `--check`/`--unmap --json` 的既有模式），是 VSCode 插件读取 trial/license 状态的前置依赖（避免像 MCP server 那样绕开 CLI 直接 shell 进 Python 内部函数）。12 个新测试，三个测试根全绿。纯版本号+CHANGELOG 提升发布（代码本身 2026-08-04 已合并），tag `v0.5.12` 经 OIDC+PEP740 发布，PyPI 核实 latest。
- ✅ **M1（vscode-extension/ 脚手架 + 诊断 + 反解 stack trace）已发布（2026-08-04）**：`pyobfus` v0.1.0 在 VS Code Marketplace 上线（publisher `zhurong2020`）—— https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus ，比原定 2026-08-08 的 gate 提前约 4 天，用户明确拍板"现在就发"（独立包的首次发布、走的是 Marketplace 而非 PyPI 渠道，不占用 pyobfus/pyobfus-mcp 自己的发布节奏名额，所以不违背 spacing gate 的本意）。新建独立包 `vscode-extension/`（TypeScript + esbuild + `@vscode/vsce`），头号功能 `pyobfus --check --json` → 原生 `DiagnosticCollection` API（诊断/`diagnosticsProvider.ts`），另有 `pyobfus: Reverse Stack Trace` 命令包 `--unmap --json`。本地验证：`npm ci`/lint/typecheck/esbuild/`vsce package` 全过，打出真实可装的 32KB `.vsix`。真正的电子测试（`@vscode/test-electron`，需要 xvfb，本机无 GUI 跑不了）靠新建的 `.github/workflows/vscode-extension-ci.yml` 在真实 CI 里验证——**过程中连续揪出 3 个真 bug**：① fixture 脚本用 `.js` 时 `tsc` 不编译进 `out/`（改成 `.ts`）；② Electron Extension Host 子进程解析 `python3` 不一定命中 `actions/setup-python` 配置的解释器（加 `PYOBFUS_PYTHON_PATH` 环境变量兜底，也是通用可复用的设计，不只是 CI workaround）；③ 反解出①②之后测试仍然"优雅跳过"掩盖了第三个真因——`.py` fixture 同理不会被 `tsc` 拷进 `out/`（加专门的 copy 脚本）。全部 13 个测试（含对真实 pyobfus CLI 的 contract test）现在在 CI 里真正跑通，非 skip。**Marketplace publisher 注册踩坑**：Azure DevOps 组织创建报"找不到订阅"（两个有效订阅、Owner role、Azure Plan，M365 Dev Program E5 沙箱租户），换目录重新登录/强制重新认证都没解决,是个未解已知 bug，非"过期 token"那类已知可修场景。绕过方案：Marketplace 网页 `manage/publishers/<publisher>` → "New extension" → "Visual Studio Code" 手工上传本地打的 `.vsix`——走网页会话自己的认证，完全不碰 Azure DevOps/PAT。M4（CI 自动发布 `vscode-v*.*.*` tag）因此暂时没有可行的自动化路径，先手工发布。**完整注册步骤 + 排查过程逐条记录**（两个 email 各自试过什么、两个订阅的详细信息、两次修复尝试分别是什么/为何都没解决、手工上传每一步）见新建的 `docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md`——下次发版（M2 起）或重试 Azure DevOps 组织创建时直接照着走，不用重新摸索。
- ✅ **M2（状态栏 + trial/pro 引导 + 右键混淆 + generate-config）已发布（2026-08-06，vscode-extension v0.2.0）**：状态栏（`statusBar/statusBarController.ts` + 纯函数 `status/tierStatus.ts::deriveTier()`）显示当前 tier（Community/Trial/Pro，读 M0 的两个 `--json` 端点）+ 最近一次 check 结果，点击弹出按 tier 过滤的 QuickPick 菜单；`pyobfus: Generate pyobfus.yaml`（包 `--init --json`）；`Obfuscate with pyobfus`（Explorer/编辑器右键菜单，跑真实混淆 `--json`，新增 `ObfuscateSuccessResult`/`ObfuscateErrorResult` 类型）；Start Trial/Unlock Pro 引导命令（文案手动同步自 `pyobfus/constants.py`，该文件 `DOCS_TO_UPDATE` 注释已加上这个 TS 文件的指针）。新增共享 `cli/errorReporting.ts`——M1 已经有两份手写的 ENOENT-带按钮 错误处理（`DiagnosticsProvider`/`unmapTrace.ts`），M2 四个新命令都要同款体验，再复制两份就是真重复了，M1 那两份原样不动。24 个测试全绿（本机 `PYOBFUS_PYTHON_PATH=venv/bin/python3 npm test`，WSLg 提供显示不需要 xvfb）。**发布经过**：Marketplace 管理页三个 tab（Acquisition/Rating & Reviews/Manage）都不是更新入口——真正的按钮是扩展名称旁一个图标化的「⋯」菜单 → 「Update」→ 上传 `.vsix` → 页面显示「It's live!」→ 有几分钟的「verifying `<version>`」过渡态，之后公开 listing 页面版本号才真正翻新（用 curl 轮询 `marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus` 的 `"version"` 字段确认，约 4 分钟）。已完整记录进 `docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md`「Updating an already-listed extension」一节。顺带修了插件自己 `CHANGELOG.md` 的一个历史遗留问题：M1 发布时从没真正拆出 `[0.1.0]` 版本号标题，M1/M2 内容一直混在同一个 `[Unreleased]` 下——这次拆成 `[Unreleased]`(空)/`[0.2.0]`/`[0.1.0]` 三段。tag `vscode-v0.2.0` + GitHub Release 已建。
- 🐛 **已修：`vscode-v0.1.0` tag 误触发 PyPI 发布 workflow（2026-08-04）**：push `vscode-v0.1.0` 后收到 GitHub "Release workflow run failed" 邮件——`release.yml` 的 `v*.*.*` glob 只检查"以 v 开头 + 后面某处有两个点"，没检查"v 后面紧跟数字"，`vscode-v0.1.0` 意外命中，触发了「Build + publish pyobfus」job，拿当时未变的 `pyproject.toml`（仍是 0.5.11）尝试重新上传 PyPI，被 PyPI 用 `400 Bad Request: File already exists` 正确拒绝——**未造成实际损坏**（核实 PyPI 0.5.11 的 wheel/sdist 哈希未变），纯粹是 CI 分钟数浪费 + 一封误报邮件。已修（commit `96eeda7`）：`release.yml` 的 `tags:` 触发器加 `'!vscode-v*.*.*'` 排除项，往后任何 `vscode-v*` tag 都不会再碰这条 workflow。
- 🐛 **意外发现并修复：P2-15 反调试测试套件让 main 分支 CI 连续 3 次跑红（0.5.11 发布前后）**，这次才第一次注意到（之前几次发布只查了 Release/CodeQL workflow，没查完整的 CI 矩阵）。根因：4 个新测试直接调用真实 `_check_debugger()` 却没 mock `sys.gettrace`——本地开发全程用 `pytest --no-cov` 跑得很快没暴露，但 CI 跑的是 `pytest --cov=pyobfus`，coverage.py 自己会装一个 trace 函数，导致 `sys.gettrace()` 在 CI 下必然非 None，提前触发了 `_check_debugger` 最早那行 pre-existing 的 gettrace 检查——"必须不退出"的测试因此真的失败，"必须退出"的测试则表面通过但其实是蒙对的（掩盖了 TracerPid/IsDebuggerPresent 逻辑本身是否正确）。已修（commit `f153374`，加 `mock.patch("sys.gettrace", return_value=None)`），本地用 `--cov` 复现+验证后确认 CI 转绿。**教训**：功能代码本身没问题（真遇到调试器或 coverage 插桩都应该正确拒绝运行，这是设计意图内的行为），纯粹是测试没考虑到"测试环境本身也会让 gettrace 非 None"这个特殊场景。

**✅ 2026-08-06：M0（pyobfus 0.5.12）+ M2（vscode-extension v0.2.0）均已发布，P2-2 四个里程碑（M0/M1/M2/M3）全部 code-complete，只差 M3 发布。** VS Code Marketplace「更新已有 listing」的真实流程已现场探明并写入 `docs/VSCODE_MARKETPLACE_PUBLISHER_SETUP.md`：扩展名称旁「⋯」菜单 → Update（不是 Manage tab、也不是「New extension」按钮）。

- 🐛 **同日 M2 发布后，user 亲手实测右键混淆命令，揪出并修复一个真崩溃 bug，已加急发 vscode-extension 0.2.1（不等 2 天 gate）**：`runJsonCommand` 从未传 `cwd`，`-m pyobfus` 把进程 cwd 放在 `sys.path` 最前——若 cwd（或其兄弟目录）恰好叫 `pyobfus`（例如 maintainer 自己 `~/projects/pyobfus` 指回本仓库的符号链接），Python 会把它当 namespace package 抢先命中，报 "'pyobfus' is a package and cannot be directly executed"，即使目标解释器本身完全正常。诊断途中一度被**同一段报错文字的另一个不相关根因**带偏：user 实测那个文件解析到的解释器（`vbca/wsl_venv`，cardiac 研究共用 venv）里装的是 2025-12 的古董版本 `pyobfus==0.2.3`，那时候压根没有 `__main__.py`——两种根因文字完全相同，靠 `pip show` 交叉核实才分清。修复：`runJsonCommand` 默认 `cwd=os.tmpdir()`（对 check/workspace-check/反解 trace 安全，已核实它们的 `--check`/`--unmap` 分支不碰 `pyobfus.yaml` 自动发现）；`obfuscateFile.ts` 单独用 `cwdForTarget()`（工作区根目录优先，否则退回目标自身目录）因为混淆主命令确实会从 cwd 自动发现 `pyobfus.yaml`；`reportCliError` 新增 `isStalePyobfusInstall` 识别，命中老版本时给"升级或换解释器"按钮而非原始 traceback。8 个新测试（含两个用真实 `--dry-run --verbose` 输出核实 auto-discovery 确实按 cwd 生效，不是只测路径字符串），32/32 全绿，真实 CI 也全过。tag `vscode-v0.2.1` + GitHub Release 已建，公开 listing 已核实显示 0.2.1。完整诊断经过见 memory `pyobfus_vscode_cwd_bug_fix_2026-08-06.md`。

- 🔬 **同日又一轮：2026-08-06 竞品扫描 + P2-23/24 + M3 全部 scope+实现完成**（PyArmor/Nuitka/VS Code Marketplace/LLM 反混淆研究/MCP Server Card 标准重新核实，无新竞争威胁）。**P2-23**（Nuitka Commercial 的 traceback 加密官方文档写明只有对称加密，比我们现有的 RSA+AES 混合 `--scrub-traceback` 弱，已加进 `docs/COMPARISON.md`，内容型改动待发布）。**P2-24** 动手写代码前先查了 SEP-2127 规范原文，发现原计划整个方向错了——`.well-known` Server Card 明确只适用于 HTTP 远程服务器，stdio 本地服务器（pyobfus-mcp 就是）该走的是我们已经在用的 `server.json`+Registry，无需新代码，当场纠正。**M3（`pyobfus.yaml` IntelliSense）scope 完当天就实现完成**：调研中意外发现真核心 bug——`config_validator.py` 的 `VALID_SCHEMA` 手工维护已漂移，缺 `preset` 和所有 v0.5.x Pro 字段，`--validate-config` 假警告，已用新 `pyobfus/config_schema.py::describe_fields()`（现查现算不会再漂移）修好（23 测试）；`scripts/generate_vscode_schema.py`（发布期脚本非运行时依赖）产出真实 JSON Schema draft-07（9 测试，真用 `jsonschema.Draft7Validator` 验证）。**实现过程中又推翻了自己一半设计**：原计划用 `redhat.vscode-yaml` 的 `registerContributor` 运行时 API + 装机提示兜底，写代码前再查一遍文档才发现有更简单更稳的纯声明式机制——`package.json` 加 `contributes.yamlValidation` 字段即可，零运行时代码，且原计划那条路本身有个官方记录在案的激活时序 bug（issue #261）；装机提示整个砍掉不需要了（5 测试）。**37 个新测试全绿，真实 CI 全过**（23-job OS/Python 矩阵 + headless xvfb 插件测试 + CodeQL）。P2-23/M3 均已 commit，按 gate 待 2026-08-08 与 M0/M2 一起发布（M3 发布为 vscode-extension v0.3.0）。完整经过见 `docs/VSCODE_EXTENSION_PLAN.md` M3 小节 + `docs/ROADMAP.md`「2026-08-06 竞品扫描」小节。

**✅ 2026-08-07 — 发布 dry-run 已跑完，08-08 到点直接执行，不必重新验证**：三个测试根 + black/ruff/mypy + `python -m build`/`twine check` 全部本地重跑一遍，全绿（core 1154 passed/1 skipped、mcp 89 passed、integration 7 passed），构建产物在临时 `dist_dryrun/` 验证后已删除，`git status` 未受影响。**结论：08-08（或之后任何一次 cold-start）到点时，跳过重新跑测试，直接执行机械步骤**——`pyproject.toml` 版本号提升 + `CHANGELOG.md` `[Unreleased]` 提升成版本号小节 + tag + push + 核实 PyPI（pyobfus 核心），然后 `vscode-extension/package.json`→0.3.0 同样流程发 Marketplace。这一步是为了避免"等一天再发布"额外产生一次冷启动重新验证的开销——验证成本已经在 08-07 这次付过，08-08 那次 cold-start 不需要再花 token 重新跑三个测试根。同日也顺手刷新一次 PyPI 下载量快照（pypistats 断续限流，两个包最终都拿到：pyobfus 日181/周1017/月1746，mcp 日48/周442/月593，见 memory `pypi_download_tracking.md`——较 08-04 大幅跳升，**大概率又是 08-06 那批发布的 CI/依赖解析噪音**，不当作有机增长信号，等 08-09 之后再看是否回落判断真假），Glama admin 面板已让 user 亲自截图核实：Build steps 仍正确停在 `pyobfus-mcp==0.3.5`（无需重新 pin），"Recent Releases" 面板显示的 0.5.8/0.5.9/0.5.10 再次确认是 Glama 自己的计数器、与实装版本无关，忽略。

**✅ 2026-08-07（同日）—— 没等到 08-08，用户明确要求现在就发，gate 提前一天清空**：08-06 距 0.5.12 只隔 1 天，仍在"1-2 天"间隔规则内。`pyobfus` **0.5.13**（`config_schema.py` 的 `--validate-config` 修复 + P2-23 内容）已 tag，OIDC+PEP740 发布 workflow 全绿，PyPI JSON API 核实 latest=0.5.13。`vscode-extension` **0.3.0**（M3）本地真实构建+测试（lint/typecheck/pretest 全过，37/37 测试含对 0.5.13 的真实合约测试），打包出 `pyobfus-0.3.0.vsix`，tag `vscode-v0.3.0`，GitHub Release 已建，真实 CI 全绿（CodeQL + VSCode Extension CI + 主 OS/Python 矩阵）。`pyobfus-mcp` 本轮未动（`[Unreleased]` 是空的），**无需 Glama 重新 pin**。**Marketplace「⋯→Update→上传 .vsix」这一步 user 已亲手完成**，`curl` 独立核实公开 listing 已返回 `"version":"0.3.0"`——**P2-2 全部四个里程碑（M0/M1/M2/M3）端到端发布完毕**。README/ROADMAP/POST_V0.4_TODO/VSCODE_EXTENSION_PLAN 均已同步。

**✅ 2026-08-08 — Glama 复查条件满足，Discord 消息已由 user 发出**：cold-start 三项常规检查全跑了一遍——① `curl` 复查 Glama 公开 API，`tools` 仍是 `[]`（距 08-06 10:47 最后一次成功 rebuild 已超 48 小时，超过历史"≤1 天自愈"窗口），达到 08-07 定下的"明天仍是 0 才正式发"条件，把写好的消息原文（未改时间措辞）呈现给 user，**user 已贴进 Glama Discord General 频道**（显示用户名 `zzann`，同日下午发出）；@punkpeye 尚未回复，下次 cold-start 查一下有没有回音，同时继续照旧 `curl` 复查——如果哪天自愈了直接记录，不必等回复。② plugin marketplace：直接 `curl`+`grep` 公开 `claude-plugins-community/marketplace.json` 全文（不用 WebFetch 摘要，避免大文件被小模型截断误判"未找到"），仍未出现 `pyobfus` 条目，与"pending review"状态一致；Console 私有提交页仍需 user 自己登录查。③ PyPI 下载快照：pyobfus 日145/周1147/月1871，mcp 日13/周453/月606——较 08-07 两包 day 都明显回落（pyobfus 181→145、mcp 48→13），week/month 仍缓慢爬升，**进一步坐实 08-06 那批发布的 day-1 跳变是 CI/依赖解析噪音，不是有机信号**，已记入 memory `pypi_download_tracking.md`。**结论：三个测试根+CHANGELOG 均无 `[Unreleased]` 待发内容，main 分支干净、CI 全绿、0 open issue/PR，本轮没有本地可发布的机械任务**；下一步方向（P2-20 RTD 重定向尾巴 / P3 长线实验项 / 新一轮竞品扫描挑新功能）留给 user 拍板，不要在没有信号的情况下自行开一个新大方向。

**🔑 同日追加：user 转发 Glama 08-07 官方 build-failure 邮件，找到实锤根因线索**——08-07 17:30 上海时间 Glama 确实自动触发过一次 rebuild（build id `019fdb8f-8498-70fb-ab64-a340239f9970`），但因**他们自家构建集群拉取 `debian:trixie-slim` 基础镜像超时**（`context deadline exceeded`，发生在 Dockerfile 第一层，跟 pyobfus-mcp 包/我们的配置完全无关）失败——这推翻了"08-06 后无新 rebuild、纯玄学等自愈"的旧猜测，也是比"indexing lag"更有说服力的证据。已写好待发的 Discord 追加消息（纯文本）+ 建议 user 检查 admin 面板 08-07 17:30 后有没有更多尝试、或手动重新保存 Build steps 触发重试，全文见 memory `glama_zero_tools_repro_2026-08-07.md`（尚未执行，等 user 决定）。

**🎯 同日再追加：user 点了「Build & Release」，问题范围被精确定位——不再是构建/内省失败，是 Release→公开 API 的同步环节坏了**。新构建（`019fe034-...`，08-08 15:09）**成功**（1m17s），Instance logs 显示 Glama 自己在构建时做的真实 `initialize`→`ListToolsRequest` handshake **完整拿到全部 8 个工具**（与本地复现逐字一致），页面显示"Release Created"（`0.5.11`，其自增计数器）。**但构建+Release 完成后立刻复查公开 API，`tools` 依然是 `[]`**。这是迄今最强证据：Glama 自己的 introspection 已经证明拿到了正确数据，只是没同步进公开目录。已把待发 Discord 消息更新为更精确的 v2 版本（引用这次成功构建的 log 作证据），旧的 v1（针对 08-07 失败构建）已存档但被取代。同时 user 查了 Console plugin-submissions 页面：pyobfus 状态仍是 "Submitted and pending review"（6 天前提交，跟 08-02 提交日期一致，无新进展）。**v2 消息已由 user 用 Reply（带 `@punkpeye` mention）挂在原始报告下发出**（Discord 时间戳 "zzann — 3:18 PM"），@punkpeye 尚未回复。下次 cold-start 查两条消息下面有没有回音，同时继续照旧 `curl` 复查公开 API。全文 memory `glama_zero_tools_repro_2026-08-07.md`。

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
- **PyPI 主包**: https://pypi.org/project/pyobfus/ (**latest v0.5.13，2026-08-07 发布**；完整版本历史见 `CHANGELOG.md`)
- **VS Code 插件**: https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus (**latest v0.3.0，2026-08-07 发布**；publisher `zhurong2020`；独立版本节奏，见 `vscode-extension/CHANGELOG.md`)
- **PyPI MCP 包**: https://pypi.org/project/pyobfus-mcp/ (**latest v0.3.5，2026-08-04 发布**；8 tools: 6 community + 2 pro_funnel · dep `pyobfus>=0.5.1` · `uvx pyobfus-mcp` 零安装；完整版本历史见 `pyobfus_mcp/CHANGELOG.md`)
- **MCP Registry**: `io.github.zhurong2020/pyobfus-mcp` (active, isLatest=true · **0.3.1**)
- **Smithery (Skill)**: https://smithery.ai/skills/zhurong2020/pyobfus-protect (2026-06-22 上线 · 本地工具走 Skill 渠道非 MCP 渠道) · **mcp.so**: 已收录
- **Glama Listing**: https://glama.ai/mcp/servers/zhurong2020/pyobfus (Quality A) — Glama 容器 build 自 **admin Dockerfile→Configuration「Build steps」字段**(web-UI)，**不读 repo 的 `pyobfus_mcp/Dockerfile`**，且**不自动跟 PyPI 最新**：每次发 mcp 新版都要手动把该字段的 `pyobfus-mcp==<ver>` bump 一次，否则 listing 静默供旧工具面——**发布必做步骤**，已进 `docs/V0.5_RELEASE_PLAN.md` Phase 5.6。最近 2026-08-06 从 0.3.3→0.3.5(test `019fd4f7`)。「Recent Releases」的版本号(如 0.5.4)是 Glama 自增计数、与实装版本无关，忽略。**⚠️ 公开 API 工具数 2026-08-07 复查仍是 0**（超过此前"≤1 天自愈"的历史窗口）——**本地已完整复现 Glama 的构建管道并排除我方问题**：`pip install pyobfus-mcp==0.3.5` 干净装 + 直接 stdio 握手 → 8/8 工具返回正常；再套一层 Glama 自家的 `mcp-proxy@6.4.3`（与 Dockerfile 里 `CMD ["mcp-proxy","--","pyobfus-mcp"]` 完全一致）暴露成 streamable-HTTP，同样走 `initialize`→`tools/list` 全流程 → 8/8 工具+完整 schema 正常返回。**结论：pyobfus-mcp 包本身和 mcp-proxy 桥接都健康，0 tools 是 Glama 自家 indexing/公开 API 管道的问题，不是我方代码或配置问题**——下一步该做的是带着这份复现证据去 Glama Discord 报告，而不是继续被动等自愈。教训 memory `glama_introspection_dockerfile_pin_2026-06-05` + `glama_zero_tools_repro_2026-08-07` · 历史 `docs/POST_V0.4_TODO.md`
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
