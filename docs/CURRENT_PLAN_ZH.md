# pyobfus 当前计划

更新时间：2026-09-02（`pyobfus` 0.5.20 与 `pyobfus-mcp` 0.3.10 已发布；
`vscode-extension` 最新仍为 0.4.1。既有付款
现已成功关联，Dashboard 显示 Paid / US$0.00 remaining，且 Stripe 生成的收据
正确。2026-09-01 Stripe Support 最终确认：`send invoice` 流程的 invoice PDF
按设计永久保留原始应付金额和付款条款，付款关联后无法重生成零余额或 `Paid`
样式；单独的 Invoice Receipt 才是该流程的正式付款证明。维护者已在原客户线程
说明并纠正先前会补发 corrected paid-invoice PDF 的预期，附上正确 Stripe
Invoice Receipt，重申无需付款或操作；未发送仍显示应付的 invoice PDF。
该客户开票支持事项已完成，不得再开贷项通知单、退款、解除付款或重新扣款。
客户回访改为被动等待客户邮件，不主动追发；长尾词/AI 搜索优化
Wave A/B/C 均已于 2026-09-01 完成。Wave C 经用户明确批准作为独立
SEO 小版本发布：Core 0.5.20 / MCP 0.3.10 已在 PyPI、GitHub Release 与
MCP Registry 全渠道核实；Registry 0.3.10 为 `active` / `isLatest=true`。
0.5.18 正式发布已获用户明确批准
并完成。结构化 dry-run plan 与 syntax-only 构建后验证随后作为两个独立 commit
实现，经用户明确批准于 2026-08-30 组成 `pyobfus 0.5.19` 发布：tag `v0.5.19`
经 OIDC workflow 发到 PyPI，wheel/sdist 两个 Integrity provenance endpoint 均
HTTP 200，全新虚拟环境 `pip install pyobfus==0.5.19` 已核实带上两个新 flag，
GitHub Release 已建，Release / CI 全矩阵 / CodeQL 均绿。后续正式发布仍须单独
取得用户同意）

这份文档是当前项目状态和后续计划的中文单一入口，面向维护者日常查看。旧的
`ROADMAP.md` 和 `POST_V0.4_TODO.md` 保留为历史归档和详细来源，但后续日常
决策优先看本文。

## 一句话定位

pyobfus 是面向 AI 辅助开发时代的 Python 代码保护工具：保留纯 Python / AST
工作流、框架兼容、反向栈追踪映射、结构化 JSON CLI、MCP/VS Code 集成，并用
可验证的供应链与工具完整性证据建立信任。

核心策略不是追 PyArmor / Nuitka 的 native / bytecode VM 赛道，而是在
“可调试、可验证、可被 AI 工具正确使用”的代码保护工作流上拉开差距。

## 当前状态

- **2026-09-01 SEO 小版本发布**：`pyobfus 0.5.20` 与
  `pyobfus-mcp 0.3.10` 已通过 OIDC 发布，四个 wheel/sdist Integrity
  provenance endpoints 均 HTTP 200，全新环境同时安装两个 wheel 并
  核实版本/manifest，GitHub Releases 已建。本次只改 README/FAQ、
  PyPI keywords 与 MCP Registry description，运行时和 schemas 不变。
  2026-09-02 Registry 端点恢复后已成功发布 0.3.10，公共 version endpoint
  独立核实为 `active` / `isLatest=true`，新版 intent description 已生效。

- **2026-08-28 发布完成**：`pyobfus 0.5.18` 与 `pyobfus-mcp 0.3.9` 已通过
  tag 触发的 OIDC workflow 发布到 PyPI，并分别创建 GitHub Release；四个
  wheel/sdist Integrity provenance endpoint 均返回 HTTP 200。MCP Registry
  0.3.9 已公开核实为 `active` / `isLatest=true`，全新虚拟环境从公开 PyPI
  安装 `pyobfus-mcp==0.3.9` 会解析到 Core 0.5.18，manifest 校验通过。

- **2026-08-24 发布完成**：`pyobfus 0.5.17` 与 `pyobfus-mcp 0.3.8` 已通过
  tag 触发的 OIDC workflow 发布到 PyPI，两个 wheel 的 Integrity provenance
  endpoint 均返回 HTTP 200；GitHub Releases 已创建。MCP Registry 0.3.8 已
  发布并公开核实为 `active` / `isLatest=true`。VS Code 扩展 `[Unreleased]`
  为空，本轮保持 0.4.1 不动。

- **2026-08-30 发布完成**：`pyobfus 0.5.19` 已通过 tag `v0.5.19` 触发的
  OIDC workflow 发布到 PyPI——`--dry-run --json` 新增 versioned `plan` 对象
  （effective config / 选中与排除文件及原因 / artifacts 交付角色，只给
  cwd-relative label，`apply_supported=false`），以及 opt-in `--verify-syntax`
  构建后内存 `compile()` 验证（不 import、不执行、不写 `__pycache__`，JSON 只
  声明 `syntax_valid`）。两个 wheel/sdist Integrity provenance endpoint 均
  HTTP 200；MCP 与 VS Code 扩展本轮无改动（`[Unreleased]` 均为空）。
- **2026-08-31 docs cleanup**（commits `4482eb7`/`f1c3e4a`/`ac6a572`/`e3ed135`）：
  ① `llms.txt` ↔ `docs/llms.txt` 两份孪生文件此前双向漂移（~5 commit），已完整
  对账为 byte-identical（`cmp` 干净、指针全 resolve、`mkdocs build` 核实
  `docs/llms.txt` 发布到站点根）；顺带刷新 `llms-full.txt`（MCP 工具表 5→8 个按
  shipped `tool_manifest.json` 校对、Versioning 段补到 0.5.19、示例 header→
  `v0.5.19`、Links `Roadmap`→`Current plan`）。`llms-full.txt` 无 `docs/` 孪生
  （llmstxt.org 规范只要求 `/docs/llms.txt`），非缺失。② mkdocs Home 页
  `docs/index.md` 补 headline 反向映射 / `--check` / 0.5.19 flags + 补全 Pro
  build-fusion 行 + 修过期 `--expire` 示例日期；`CONFIG_AWARE_CHECK_DESIGN.md`
  Rollout 段时态修正；`PROVENANCE_MANIFEST.md` 样例 JSON `pyobfus_version`
  0.5.13→0.5.19。其余候选（`AGENTS.md` / `pyobfus_mcp/README.md` 8 工具表 /
  `skills/pyobfus-protect/SKILL.md` / `templates/ai-integration/` / `_drafts/`
  0.4.0 营销稿 / 归档 docs）逐个核实无需改。
- 主包：当前 `pyobfus 0.5.20`（2026-09-01）；最新运行时能力仍来自 0.5.19
  的结构化 dry-run plan 与 syntax-only 构建后验证，以及 0.5.18 的配置感知
  `--check`。0.5.20 只更新发现元数据和 README/FAQ，不改变运行时。
- MCP 包：当前 `pyobfus-mcp 0.3.10`（2026-09-01，Registry 于 09-02 补发布）；
  最新工具能力仍来自 0.3.9 的默认开启 `use_project_config`，依赖下限为
  `pyobfus>=0.5.18`。0.3.10 只更新发现元数据，工具行为和 schemas 不变。
- VS Code 扩展：`0.4.1` 已 tag + GitHub Release 发布（P2-33，"Why trust this
  extension" 小节强化 Nx Console 事件对比 + CodeQL/CI 签名信号），**Marketplace
  手工上传也已由用户完成**——微软 "[Succeeded]" 确认邮件已收到，公开 listing
  `curl` 核实已返回 `"version":"0.4.1"`。
- 🆕 **新增 `scripts/check_unreleased_changelogs.py`**：本轮发布前发现
  `pyobfus-mcp`/`vscode-extension` 两份 CHANGELOG 的 `[Unreleased]` 内容已经
  held 了几天没人想起来一起发——写了个脚本扫描仓库内三份 CHANGELOG 的
  `[Unreleased]` 段落，已接入本地专用的 `docs/internal/PYPI_RELEASE_GUIDE.md`
  发布前检查清单，避免同类遗漏再犯。
- Glama admin「Build steps」已于 2026-08-24 自动更新到
  `pyobfus-mcp==0.3.8`；21:09 的新测试已确认 success（12.1s），安装日志为
  MCP 0.3.8 + Core 0.5.17，实时 `ListToolsRequest` 返回完整 8 工具及新增
  `verify_dependencies_online` schema。新公开 API 仍返回 `tools: []`，现已由
  成功实例日志反证为纯 Glama 目录同步问题，非我方包或配置问题。
- GitHub：主分支健康，当前公开 issues/PRs 为 0，CI/CodeQL 全绿。
- README/`llms.txt`/两个 `pyproject.toml`/`server.json` 的 AI 客户端定位
  文案已补 GitHub Copilot + CodeBuddy（实时搜索核实后添加，非训练记忆），
  README tagline 结尾改成"any MCP-compatible AI agent"泛称。
- ✅ **v0.5.14 那次 PyPI description 落后一个版本的问题已随 0.5.15 自然翻新**
  （新包快照带上了正确的 README 横幅），流程教训已固化进 `CLAUDE.md` 发布
  流程清单（README 横幅须在打 tag 前的同一提交里更新），0.5.15 发布时已
  实际验证生效，不再是待办。
- 近期下载（2026-08-20 发布前快照，pypistats.org）：`pyobfus` day/week/
  month `26 / 295 / 1,912`；`pyobfus-mcp` `8 / 124 / 687`。较 08-17 安静基线
  （`9/206/1,870` / `0/46/581`）周环比明显上升（pyobfus +43%，mcp +170%），
  但按历史经验（发布后 1-3 天的跳变多为 CI/依赖解析噪音），暂不当作真实
  有机增长信号——下次复查时对比是否回落。
- **2026-08-21 周期性复查**：下载量快照与 08-20 基线**完全一致**（pyobfus
  `26/295/1,912`、mcp `8/124/687`），发布后的跳变未再放大，维持"发布噪音
  而非有机增长"判断，无需调整任何动作；Glama 与 Claude plugin 状态复查亦无
  变化（详见 P0 小节与 `docs/DISTRIBUTION_CHANNELS.md`）。
- **2026-08-24 下载量复查（pypistats.org，数据截止 08-23，不含当天新发布）**：
  `pyobfus` day/week/month `27 / 502 / 2,059`，相对 08-20/21 基线周 +70%、
  月 +7.7%；`pyobfus-mcp` `11 / 242 / 772`，周 +95%、月 +12.4%。但 overall
  日序列显示增量高度集中于发布日：主包 08-17/20/22 分别 `124/119/151`，
  MCP 08-17/22 分别 `95/110`，到 08-23 已回落为 `27/11`。因此只记录为
  “周/月累计上升”，不升级为自然用户增长信号；pypistats 会排除已知镜像，
  但仍包含 CI/CD 下载。下一次最早在数据覆盖 08-24 发布后 2-3 天时复查，
  且仍以非发布日基线是否抬升为判断标准。
- **2026-08-26 首次 post-release 复查（数据截止 08-25）**：08-24 发布日
  `pyobfus` / `pyobfus-mcp` 分别为 `137 / 99`，08-25 随即回落为 `27 / 8`；
  最新 day/week/month 为 `27/512/2,178` 与 `8/245/874`。GitHub 仍为
  6 stars、2 forks、0 open issue/PR，Discussions 无新评论；08-24 clone
  `268/31 unique`，08-25 回落为 `10/6 unique`。维持“发布/自动化噪音，尚无
  有机增长或 dependency_advisory 独立需求信号”判断。完整证据见
  `docs/EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md` 的 08-26 复查小节。
- **2026-08-26 首个真实 Pro 客户售后信号（匿名记录）**：客户主动确认当前
  使用“going well”，随后提出已完成购买的企业开票需求。已回复并请求确认
  个人/公司收票主体、法定实体名称、账单地址、税号及 PO/reference；不提前
  把一次开票需求解释为团队许可或企业功能需求。PII、支付编号与具体开票
  资料只保存在 Git 忽略的本地运营记录，不进入公开仓库。
- **2026-08-27 客户已回复开票资料**：收票主体为一家公司法律实体（某地区
  子公司，与邮件签名里的美国母公司不同），需按客户书面确认的实体名/地址
  开具，可选放一个联系人姓名；未提供单独税号，也未要求 PO 号。字面开票
  信息只在邮件线程 + Git 忽略的 `docs/internal/CUSTOMER_SUPPORT_LOG.md`
  + `docs/internal/STRIPE_POST_PURCHASE_INVOICE_RUNBOOK.md`，不进公开仓库。
  **2026-09-01 已完成**：Stripe 最终确认 Invoice Receipt 是该流程的付款证明，
  已向客户说明并交付正确 receipt，未发送仍显示应付的 invoice PDF。现按下方
  “恢复工作清单”推进。客户回访仅等待客户自行来信，不主动追发；若收到回复，
  再把实际使用功能及工作流需求作为排序证据，不推销预设功能。
- **2026-08-27 发票遇 Stripe 侧 blocker，已联系 Support**：原始 Payment
  Link 付款挂在 Stripe guest customer 下，发票建在 regular Customer 下，
  Stripe「应用付款」报 400 customer 不匹配；作废重建两次无效。按 runbook
  的 guest-customer 分支，已于 2026-08-27 通过认证 Dashboard 联系 Stripe
  Support（诉求：把既有付款关联到发票、产出正确的已付发票 PDF、不二次
  收款、抬头保持公司实体）。中途在 Dashboard AI 助手指引下用了「mark as
  paid」，结果不一致：列表显示已付但 PDF 仍显示应付金额 + 未来到期日。
  **等待 Support 回复期间**：不把发票/PDF 发给客户、不再作废重建、不再
  「mark as paid」、不退款重扣。**2026-08-27：Stripe 自动开票通知邮件已发
  到客户（显示应付金额 + ~30 天到期日）——不是新扣款；已同日手动给客户
  回信（改编 runbook 进度更新模板，reply 到客户 08-27 邮件线程）：自动邮件
  不是新扣款、购买已付清、正在把发票关联到既有付款、与 Stripe support
  处理中、几个工作日内补正确的 US$0.00 PDF（抬头保持公司实体），未含任何
  Stripe 标识符/PII。因此冷启动无需再发例行进度更新，除非 Support 往返
  拖很久。** 字面开票信息与 Stripe 标识符只在邮件线程 +
  `docs/internal/CUSTOMER_SUPPORT_LOG.md`（Git 忽略），不进公开仓库。
- **2026-08-28 付款关联已成功，但 invoice PDF 仍未同步**：Dashboard 已显示
  Paid、全额支付、余额为 US$0.00；同一账单通过「发送账单收据」产生的 receipt
  PDF 也正确显示原购买日与全额已付，但无痕窗口中新下载的 invoice PDF 仍显示
  全额应付和未来到期日。未照 Support 的早期通用建议开全额贷项通知单，因为
  有效销售在付款后做贷记会错误表达退款/客户余额/外部贷记。已将互相矛盾的
  两份 PDF 附在 Support 原线程，请 Billing/Invoicing 技术团队刷新；附件仅存
  Git 忽略的内部归档。当前 hold：不向客户发送错误 invoice，不退款、不贷记、
  不解除付款、不重新扣款；正确 receipt 只在交付紧急时作为临时证明，不能
  默默替代客户要求的 paid invoice。
- **2026-08-30 Dashboard 新下载仍错误，已要求工程升级处理**：Stripe Support
  将矛盾归因于最长 24 小时的 CDN 缓存，并要求从实时 Dashboard 下载；实际
  严格照做后，新生成文件在付款成功关联 84+ 小时后仍显示全额应付和未来到期
  日。文件时间与 digest 均证明不是误开旧本地文件；同时保存的 Dashboard
  截图明确显示 Paid、全额付款已应用、余额 US$0.00。已在原 Support 线程附上
  新 PDF 与截图，请 Billing/Invoicing 工程团队重生成/失效错误 PDF asset，
  hold 清单不变。客户确认未收到 Stripe 的错误自动邮件；已回复其购买全额付清、
  无需付款或操作，待正确公司抬头 paid invoice 就绪后再发送，未向其发送错误
  PDF 或 Stripe 内部细节。字面标识符与附件仍只在 Git 忽略的内部归档和邮件中。
- **2026-08-24 发布后反馈全量审计**：GitHub 当前 0 open issue、0 open PR；
  Discussions 共 6 条，最新项目公告仍为 08-01 且 0 评论，尚无人提到
  `dependency_advisory` 或要求脱离混淆单独使用。仓库已有 6 stars / 2 forks；
  过去 14 天 GitHub Traffic 为 155 views / 65 unique visitors、1,480 clones /
  158 unique cloners。克隆量同样由 08-17/20/22 发布日尖峰主导，但 08-23
  仍有 10 个 unique clones，是比“仅下载量”稍强、但仍不足以证明留存的弱
  兴趣信号。来源包括 GitHub、Google、Bing、PyPI、ChatGPT；Stripe/Jira 各
  只有 1 个来源访问，不能解释为购买或企业采用。VS Code Marketplace API：
  0.4.1、3 installs、124 downloads，无可识别的真实评分/评论信号。最新 main
  CI、CodeQL、Pages 及两个 release workflow 全绿。
- 同类工具扫描确认不能把 `dependency_advisory` 当成空白赛道：Python/PyPI
  已有名为 `slopcheck` 的独立工具，另有 `slopscan`；npm 侧同名 slopcheck
  已扩展到 markdown/agent rule 文件、unpublished/security-hold 检测。近期研究
  也在做已注册包的年龄、发布次数、作者/仓库等概率式风险判断。当前 pyobfus
  的“只证伪不存在的声明依赖”定位仍诚实，但若将来独立，差异化不能只停留
  在 PyPI 404 检查，应优先考虑 AI-agent JSON/SARIF 工作流和注册后可疑度证据。
- **2026-08-22 追加（非发布，held 在 `[Unreleased]`）**：一次竞品/MCP 安全
  调研顺带产出两处已核实的诚实文档更新——`docs/COMPARISON.md` 补 PyArmor
  VMC（可逆 VM 字节码）/ECC（不可逆 C 编译）函数体虚拟化模式的技术细节，
  先查证官方 features 文档才落笔（最初 WebSearch 摘要在两份官方 GitHub
  changelog 里都对不上号，坐实"不能直接采信搜索摘要"）；`docs/MCP_SECURITY_SCAN.md`
  新增 SSRF 自查小节，grep 全部 `pyobfus_mcp` 源码确认零出站 HTTP/URL-fetch
  代码路径，SSRF 类风险（OWASP 数据：7000+ 公开 MCP server 中 36.7% 中招）
  对当前工具面不适用。顺带用 PyPI JSON API 核实 PyArmor 最新版仍是 9.2.6
  （2026-07-27，非搜索摘要含糊提到的"9.2.7"）；`docs/ROADMAP.md` 里旧的
  "9.2.6（June 2026）"月份有误，但那是已归档的历史扫描快照，按惯例不回溯
  改写。两个 commit（`1616e5a`/`462213f`）已推送，等下次自然发布节奏带上。
- **2026-08-22 又追加（同日新增，非发布，held 在 `[Unreleased]`）：
  `--check` 新增 `dependency_advisory` 类别**——源自
  `~/projects/NEXT_TOOL_OPPORTUNITY_SCAN.md` 机会扫描的 A1 候选（Python
  vibe-coding 安全检查/hallucinated-dependency 检测），user 拍板"先做成
  pyobfus 内部 advisory 做低成本验证"。检测 `requirements*.txt`/
  `pyproject.toml` 声明的依赖是否在公开 PyPI 上真实存在，命中"不存在"时
  给出 MEDIUM 级 risk（含 slopsquatting 说明 + 自定义 index 场景下调低置信度
  的 caveat）。**CLI 默认联网**（`pyobfus --check` 会真的发 PyPI 请求，
  `--offline` 关掉）；**MCP 侧 `check_obfuscation_risks` 默认离线**
  （新增 `verify_dependencies_online` 参数需显式传 `true` 才联网）——两者
  刻意不同默认值，是为了不让 pyobfus-mcp 已经建立的"零出站网络"安全姿态
  被静默打破。这也是仓库第一次出现出站网络调用，**上面那条"SSRF 自查……
  零出站 HTTP 代码路径"的结论已随之更新**（`docs/MCP_SECURITY_SCAN.md` 已
  同步修订，不是删除旧结论而是记录"新增一条、为什么它不构成 SSRF 模式"）。
  新模块 `pyobfus/core/dependency_advisory.py` + 新 cookbook
  `docs/DEPENDENCY_ADVISORY_COOKBOOK.md`（含诚实的能力边界：只能证伪"名字
  不存在"，抓不到"已被抢注"的更危险场景）。21+6 个新测试，三个测试根
  +black/ruff/mypy（含 CI 实际用的 `mypy pyobfus/ pyobfus_pro/
  pyobfus_mcp/pyobfus_mcp/` 联合调用）全绿。**用户已明确要求这次先只提交
  到 main、不升版本号，等用户后续通知再发布**——不要在没有新指示的情况下
  自行打 tag/发布。发布前用户还要求：持续关注真实使用情况（GitHub
  issue/反馈）、可能主动征求用户意见、并观察同类竞品动态，作为后续
  "留在 pyobfus 内部" vs "拆成独立包/品牌"决策的依据，详见机会扫描文档
  与 memory `project_next_tool_opportunity_scan_2026-08-22.md`。
- **2026-08-22 又一轮（同日，两个独立 commit `8d0fc0c`/`c864bdf`）：AI-agent
  面向的 Pro 引导审计 + 一个真实存在的文档自相矛盾被发现并修正**。用户想
  给 AI agent 补"如实"的 Pro 引导（安全完整性/一次性付费/大项目不受限
  三点），动手前先审计全项目现有的 AI 面向提示（`ai_hint`/`pro_value`/
  `recommend_tier`/`llms.txt`/`SKILL.md` 等）——发现 README 自相矛盾：
  一处脚注说"Community Edition 无文件/行数限制"，另一处 FAQ 对比表却说
  "Free tier: Clear limits (5 files/1000 LOC)"。**实测验证**：
  `community_edition()` 的 5 文件/1000 行上限只在 legacy `--no-cross-file`
  路径和单文件模式生效，cross-file 模式（**当前默认**）和**所有具名
  preset**（含 `safe`/`balanced`/`aggressive`）从未接入这个检查——真实
  多文件项目今天在 Free 版上默认就是无限制的，测试套件也只用
  `--no-cross-file` 测过这条限制，从未覆盖默认路径，因此从未被发现。
  **用户拍板"改文档不改代码"**（不为此引入对现有 Free 用户的破坏性行为
  变更）——commit `8d0fc0c` 修正 README/`trial_cli.py`/`recommend_tier`/
  `config_schema.py`(+ 重新生成 vscode schema) 五处失真表述，改成更强的
  诚实卖点："pyobfus 无论 Free/Pro 都没有项目规模限制，对比 PyArmor 试用版
  实测约 935-940 行/文件封顶"。`docs/COMPARISON.md` 本身这块内容**一直是对的**
  （已有完整实测方法论），只是 README 和 CLI 文案漂移掉了。commit `c864bdf`
  在 `llms.txt`+`SKILL.md` 新增"何时该提 Pro"小节（只在扫描真给出
  `pro_value`/`pro_action` 信号时才提，给精确数字不给模糊形容词，绝不拿
  项目规模当理由）+ `_pro_unlock()` 新增 `pricing_model: "one_time"` 字段。
  三个测试根+black/ruff/mypy 全绿，两个 commit 已推送，CI（含
  VSCode Extension CI，因改了 schema 文件触发）全绿。
- 外部分发状态：
  - Glama 旧公开 API 路径
    `/api/mcp/v1/servers/io.github.zhurong2020/pyobfus-mcp` 当前返回
    `not_found`；公开页面 `/mcp/servers/zhurong2020/pyobfus` 仍可打开，页面内
    可解析到 8 个工具名。下一步不是改 pyobfus-mcp 代码，而是确认 Glama 当前
    推荐的 public API / listing 查询路径，并在 Discord `#support` 跟进旧路径
    失效或同步状态。维护者 2026-08-17 手工复核对应 Discord 频道：暂未看到
    Glama 回复，本轮跳过，等待外部反馈或下一次周期复查。
  - Claude plugin submission 已由维护者在 Console
    `/plugins/submissions` 于 2026-08-17 手工复核：`pyobfus` 仍为
    `Submitted and pending review`，日期 Aug 2；提交描述里的
    `One-call protected_project workflow` typo 仍存在，继续机会性修复，不为
    typo 单独重提。

## 已完成的关键能力

### Community / Core

- `--check` 风险扫描：eval/exec、动态属性、框架反射等。
- `--init` 自动生成 `pyobfus.yaml`。
- `--unmap` 反向映射 obfuscated stack trace。
- `--trace-marker` 在输出文件里写入可恢复提示，帮助 AI 或开发者找到 mapping。
- 全局 `--json`，适合 CLI、MCP、IDE 可靠调用。
- 框架预设：FastAPI、Django、Flask、Pydantic、Click、SQLAlchemy、ML。
- `--strip-ai-artifacts`、`--numeric-obfuscation`、`--provenance-manifest`。

### Pro

- Selective Opacity、Runtime String Vault、forensic watermarking。
- device/expiry/period license binding。
- `--seal-code`、`--scrub-traceback` / `pyobfus-unscrub`。
- import obfuscation、embedded encrypted data、runtime policy、anti-debug。

### AI / IDE / MCP

- `pyobfus-mcp` 暴露 8 个工具，返回稳定 JSON contract、`ai_hint` 和
  `next_tool`。
- MCP tool-description integrity：`pyobfus-mcp-verify`。
- VS Code 扩展已支持风险诊断、反向栈追踪、生成配置、右键 obfuscate、
  Pro trial/unlock funnel、`pyobfus.yaml` IntelliSense。
- 2026-08-14 起，VS Code 的 Reverse Stack Trace 流程开始利用 trace marker
  的 `mapping=...` 提示来定位 mapping 文件选择器。

## 竞品与最佳实践判断

### 竞品现状

- PyArmor 9.2.x 继续加深 RFT / BCC / JIT / Themida / VMC / ECC / runtime
  assert / mix-str 路线，优势是 bytecode/native/runtime 不透明交付。
- Nuitka Commercial 强调 data hiding、protected data files、encrypted output、
  traceback encryption、compiled delivery。其 traceback encryption 当前仍是对称
  加密，并称未来计划支持非对称。
- SOURCEdefender 是 `.pye` import-hook 加密产品，AES-256、TTL、PyInstaller
  bundling，偏 opaque encrypted-file delivery。

这些产品验证了“更强 runtime/data protection”有需求，但它们主线不是
AI-debuggable workflow。pyobfus 不应把 v0.6 的主目标变成模仿 native VM 或
bytecode 加密。

### 🆕 2026-08-20 竞品 + 生态扫描（实时搜索核实，非训练记忆）

完整版见 `docs/ROADMAP.md`「Planning refresh from 2026-08-20」小节，中文摘要：

- **PyLocket——一个此前未扫描过的新对手**，定位比 SOURCEdefender 更"完整平台"：
  逐函数字节码加密（非整文件）+ 设备绑定密钥（激活时下发、从不内嵌进产物）
  + anti-debug/anti-VM/内存保护 + 内置 licensing/delivery/checkout 全套商业化
  基础设施。仅支持 **Python 3.12-3.14**（比 pyobfus 的 3.9-3.14 窄），定价
  是订阅 + $4/激活许可（与 pyobfus $45 一次性完全不同形态）。**关键发现**：
  它的官方文档/营销材料完全没有提到调试支持、traceback 处理或 AI 辅助工作流
  ——在 pyobfus 主打的"可调试保护"这条赛道上，PyLocket 并不构成竞争，它拼的
  是防篡改强度和商业化完整度。**不追它的逐函数加密架构**（仍属于此前反复
  排除的 native/opaque-runtime 主线），但值得诚实加进 `COMPARISON.md`。
- **MCP 安全扫描生态已经成熟**：Cisco `mcp-scanner`、Invariant `MCP-Scan`
  等可信品牌工具出现，且研究反复确认"目前没有被广泛采纳的公开 MCP server
  认证/审查标准"——这是给 `pyobfus-mcp` 加一个新信任信号的低成本机会（跑
  Cisco 的扫描器、结果干净就公开引用，同 OpenSSF badge 的逻辑）。
- **PEP 740 attestation 采用率仍然很低**（360 个最热门 PyPI 包里只有约 5%
  已上传 attestation）——pyobfus 已经做了，且比生态平均水平领先很多，值得
  在定位文案里继续强调，不是"已经普及、不再是差异化"的东西。
- **VS Code Marketplace 恶意插件浪潮在加剧**（GlassWorm/WhiteCobra 蠕虫式
  campaign、Open VSX 08 月下架 77 个"evil-twin"插件、Nx Console 带
  Verified-Publisher 徽章却在 05 月被植入凭证窃取器影响 220 万安装量）——
  **"Verified Publisher" 徽章现在被行业公认为不可靠信号**，反向验证了
  pyobfus 一直坚持的策略（不靠徽章，靠 OpenSSF/PEP740/CodeQL-clean/
  Apache-2.0 可审计这类结构性可验证信号），值得把这些信号在 Marketplace
  listing 文案本身里做得更显眼，不能只放在 README 里点进去才看到。
- **Python 3.14 free-threading（PEP 779）已从实验特性转正**——pyobfus 声称
  支持 3.9-3.14，但 Pro 运行时组件（Runtime String Vault、license binding、
  anti-debug）目前没有针对 free-threaded build（`python3.14t`）做过验证，
  是一个此前没被标记过的真实兼容性缺口（不是假设性的）。
- decompiler 生态对现代 Python（3.8+）依然不成熟——重新确认（不是新发现）
  P3-1 `--output-pyc` spike 不需要因此提高优先级。

### 国际最佳实践

- PyPI PEP 740 / Integrity API 让 release provenance 成为公开信任面。
- PyPI 自己也明确：attestation 证明包从哪里来，不证明代码一定可信。
- PEP 770 建议 SBOM 使用 CycloneDX 或 SPDX，优先 UTF-8 JSON，包含创建时间、
  creating tool、主组件、组件关系和软件标识。
- CycloneDX CLI 已支持 validate、sign、verify、convert、diff、merge、add files。
- MCP 2026-07-28 方向是 stateless core、cacheable list results、header routing、
  auth hardening。
- MCP Authorization 仍明确区分：HTTP transport 才走 OAuth；stdio server 应从
  环境拿凭据，不应照搬 HTTP OAuth。
- MCP Registry `server.json` schema 越来越重视 repository ID、package hash、
  exact version、命令参数注入风险等 trust metadata。

## 后续优先级

### P0：外部状态继续跟进

1. Glama public API / listing 状态
   - 2026-08-17 手工复核 Discord 对应频道：暂未看到 Glama 回复。
   - 继续在 Glama Discord `#support` 等待 / 跟进，但本轮不阻塞本地工作。
   - 每次冷启动同时检查旧 API 路径和公开页面能否列出 8 个工具。
   - 找到 Glama 当前推荐 API 后，替换旧的 `tools: []` 检查口径。
   - 不为 Glama 单独改 pyobfus-mcp 代码，除非 Glama 给出可复现的本地问题。
   - **2026-08-17 证据**：mcp 0.3.6 发布后照惯例重新 pin Build steps，
     触发的新构建（`01a00e39-...`）15 分钟后失败，`ECONNRESET`/"aborted"，
     卡在拉取 `debian:trixie-slim` 基础镜像元数据这一步——与 08-07 那次失败
     （`context deadline exceeded`，同一卡点）是**第二个独立复现实例**，
     错误签名不同但卡点相同，指向 Glama 构建集群拉取该 base image 的网络层
     问题，与 pyobfus-mcp 包/配置无关（Build steps 已确认正确显示
     `pyobfus-mcp==0.3.6`）。
   - **2026-08-20 第三方独立复现（不是我们自己的数据点）**：user 转发
     Glama `#support` 频道全文，至少 3 位其他 maintainer（Considus/Andrei
     Lungeanu/ojkingston）报了完全相同的 `debian:trixie-slim` 构建卡点和
     错误签名，累计 5+ 个互不相关的 server 撞到同一故障；另有 maintainer
     （mellowmelomel/nolpak14/Cabal_hunter）独立报了与我们完全一致的
     "页面工具正常、公开 API 却 `tools: []`/字段陈旧"症状。两点均坐实此前
     判断——纯 Glama 平台侧构建基础设施 + 目录同步层问题，与 pyobfus-mcp
     包/配置无关，继续不需要我方改代码。Frank/Glama team 对频道内所有报告
     （含我们的两条）都尚未回复，看起来在处理积压，**用户决定不主动追发
     消息**。详见 memory `glama_zero_tools_repro_2026-08-07.md`。
   - **2026-08-21 复查**：旧 API 路径仍 `not_found`；公开页面正常且列出
     全部 8 个工具，但页面版本元数据仍停在 v0.5.13（当前 0.5.15）——维持
     "Glama 侧目录同步陈旧"判断。Discord `#support` 与 Recent Tests 两项
     需 user 登录后手工查，本轮未变化。

2. Claude plugin marketplace
   - 2026-08-20 user 再次核实 Console 页面：仍为 `Submitted and pending
     review`，日期 Aug 2，提交描述里的 `protected_project` typo 也仍在。
   - 2026-08-21：Console 登录墙，程序化无法核实，维持 user 手工复查。
   - 后续每轮外部状态检查只需确认是否出现 approve / reject / 补充信息。
   - 如 Anthropic 给出修改入口，再顺手修 `protected_project` typo 为
     `protect_project`。

### ✅ 已发布（原 P1/P2 打磨项，2026-08-17 三包发版后收口）

1. `P2-25` VS Code trace/config workflow polish — **已发布于 `vscode-extension`
   0.4.0**（tag + GitHub Release + Marketplace 手工上传均已完成，`curl` 核实
   公开 listing 已返回 `"version":"0.4.0"`）。
     - Reverse Stack Trace 利用 `--trace-marker` 自动定位 mapping 文件。
     - Reverse Stack Trace 复用共享 CLI 错误提示；旧版 pyobfus / 解释器错误现在
       给出和 obfuscate / generate-config 一致的 Upgrade / Select Interpreter
       动作入口。
     - Obfuscate with pyobfus 识别配置 unknown-key 错误，并提供打开自动发现的
       `pyobfus.yaml` 动作入口。
     - Core `pyobfus --validate-config --json`（`pyobfus` 0.5.14 已发布）已有
       稳定 JSON contract。
     - VS Code 已新增 `pyobfus: Validate pyobfus.yaml`，基于 JSON contract 显示
       validation 摘要，并把错误/警告写入 pyobfus output channel。
   - 该轮 trace/config polish 已可收束；除非实际使用发现新痛点，不继续扩大
     VS Code scope。
   - 原则：只做小而确定的 UX 改善，不改变 core 语义。

2. `P2-28` MCP Registry / `server.json` schema hardening — **已发布于
   `pyobfus-mcp` 0.3.6**（PyPI + MCP Registry，`isLatest=true` 已核实）。
   - 用官方 `2025-12-11` schema 重新验证 `pyobfus_mcp/server.json`，并补充
     GitHub repository stable ID `1093960892`。
   - `fileSha256` 暂不补：PyPI 有 wheel/sdist 多 artifact，填错单一 hash 比不填
     可选 hash 风险更高。
   - 已明确 HTTP OAuth / Server Card 对当前 stdio server 不适用。
   - 新增 `test_version_metadata.py` 回归测试，防止版本号三处（`__init__.py`/
     `pyproject.toml`/`server.json`）再次漂移。
   - ✅ Glama admin「Build steps」字段已由用户手工改成 `0.3.6`（确认无误），
     但触发的新构建随后失败（`ECONNRESET`，Glama 自家基础设施问题，非我方
     配置问题）——详见 P0 小节。

3. `P2-26` obfuscated-output SBOM + provenance manifest — **已发布于
   `pyobfus` 0.5.14**。
   - 在现有 `--provenance-manifest` 基础上扩展：manifest 保留原字段和
     integrity digest，同时新增 input SHA-256、可用时的 git commit，以及
     CycloneDX-compatible `cyclonedx` 子结构（file components + input/output/
     mapping relationships）。
   - 用户文档已补 `docs/PROVENANCE_MANIFEST.md`，README / `llms.txt` 已同步。
   - CLI 已新增 `--verify-provenance-manifest`，可校验 pyobfus manifest shape、
     CycloneDX-compatible relationships 和本地 integrity digest，并支持 JSON 输出。
   - 当前先不扩独立 `--sbom` 入口；只有当用户或外部工具明确需要 standalone
     CycloneDX 文件时，再单独开后续项。
   - 价值：竞品能保护代码/数据，但通常不给"被保护产物"的供应链记录。
   - 口径：这是 provenance / reproducibility / tamper-evidence，不是"证明代码可信"。

4. `P2-27` attestation verification helper / trust report — **docs-first 已发布**
   （新增 `docs/RELEASE_PROVENANCE_VERIFICATION.md`）。
   - 2026-08-17 三包发版后已重新核实：PyPI JSON API 最新版本
     `pyobfus 0.5.14`、`pyobfus-mcp 0.3.6`；四个最新 wheel/sdist 的 PyPI
     Integrity API provenance endpoint 均返回真实 `HTTP 200`（非文本平移）。
   - 文档给出 `pypi-attestations verify pypi` 的完整验证口径；当前不手写
     sigstore / DSSE 校验逻辑。
   - 输出要诚实：证明发布身份和产物 digest，不证明代码没有漏洞或恶意。

### ✅ P1：`P2-29` compatibility checks — 已发布于 `pyobfus` 0.5.15（2026-08-20）

针对真实交付组合补诊断与文档，**未新增任何 transform**（遵守"明确不做"）。

- **`--check` 新增 `compatibility_advisory` 类别**（`pyobfus/core/preflight.py`，
  severity `low`/`info`，不改动 `exit_code` 语义，不阻塞 CI）。自动流入 VS Code
  红线（`diagnosticsProvider.ts` 消费 `Risk` contract，`low→Information`/
  `info→Hint`）与 MCP `check_obfuscation_risks` 工具（包裹 `PreflightChecker`）——
  **VS Code / MCP 无需改代码**。
  - import-hook / 加密文件生态：`import sourcedefender`、`.pye` 字面量、
    `sys.meta_path` 赋值/变更、`importlib.abc` 子类。
  - 编译打包：`import nuitka` / `import Cython` / `.pyx` 字面量。
  - model-serving：检测到 `ml` preset 时追加一条 `info` 级建议，指向保留
    mapping 做反向栈追踪。
- **三篇 cookbook**（`docs/`）：`IMPORT_HOOK_COOKBOOK.md`、
  `COMPILED_PACKAGING_COOKBOOK.md`、`MODEL_SERVING_COOKBOOK.md`，沿用
  `PYINSTALLER_COOKBOOK.md` 的 compose-not-compete 格式。
- **两个端到端复现示例**（`examples/`，参考性、不进 pytest）：
  `examples/import_hook/`（标准库自定义 import hook，无需付费依赖即可跑通）、
  `examples/compiled_packaging/`（Cython，免费）。
- 回归测试：`tests/test_preflight.py` 新增 9 条 `compatibility_advisory` 用例。
- 后续机会（未并入本轮）：`--check` 接入已配置 `--config` / `exclude_patterns`
  以减少真实组合的误报，属独立行为改动，留作单独小项。

### ✅ 2026-08-20 扫描新增，2026-08-22 三包发布收口

用户要求"依次完成上述所有功能，但等几天再发布"——四项实现+验证+提交到 main
后 held 了两天（沿用本项目一贯的"功能先合并、发布单独 gate"节奏），
2026-08-22 统一切版本号发布（`pyobfus` 0.5.16 / `pyobfus-mcp` 0.3.7 /
`vscode-extension` 0.4.1，各自独立 tag + PyPI/MCP Registry/Marketplace 全渠道
核实）。发布前用新写的 `scripts/check_unreleased_changelogs.py` 核对，
确认三份 CHANGELOG 均已清空 `[Unreleased]`。

1. ✅ `P2-30` **已发布于 `pyobfus` 0.5.16**。`docs/COMPARISON.md` 加了
   `### pyobfus vs PyLocket` 完整小节——诚实列出它的真实优势（逐函数字节码
   加密+设备绑定密钥，防篡改强度确实比 pyobfus AST+Pro vault 强），同时点出
   三个真实差距（Python 版本覆盖更窄、订阅+按许可计费 vs 一次性 $45、完全
   没提调试/AI 工作流支持）。
2. ✅ `P2-31` **已发布于 `pyobfus-mcp` 0.3.7**（PyPI + MCP Registry，
   `isLatest=true` 已核实）。实际跑了 Cisco `cisco-ai-mcp-scanner`（PyPI 真实
   工具，非模拟）扫真实发布的 `pyobfus-mcp` 0.3.6（干净 venv 装的 PyPI 包，
   非本地开发版）——**8/8 工具 SAFE，0 findings**（YARA + 依赖漏洞审计两个
   离线 analyzer，不需要 API key）。过程中撞到扫描器自己的一个 CLI bug
   （`vulnerable-package` 子命令参数解析冲突），改用直接 `pip-audit --strict`
   交叉验证同样干净。新建 `docs/MCP_SECURITY_SCAN.md`（完整可复现步骤 + 诚实
   的适用范围声明：只测了离线 analyzer，`api`/`llm`/`behavioral`/`virustotal`
   需要付费 key 没测），`pyobfus_mcp/README.md` 加了摘要小节引用。
3. ✅ `P2-32` **已发布于 `pyobfus` 0.5.16**。下载了 python-build-standalone
   的 free-threaded Python 3.14.7 独立构建（不需要 sudo/apt），核实
   `sys._is_gil_enabled()` 确实是 `False`，然后：① 完整核心测试套件 1169
   passed/1 skipped 全过（含所有 Pro 运行时测试文件：Vault/license
   binding/scrub/seal）；② 真实端到端冒烟测试（不只是单测）——用
   `--seal-code --scrub-traceback` 混淆一个样例文件，在 `python3.14t` 下执行
   保护产物，正常路径输出正确且 GIL 确认仍是禁用状态；异常路径触发真实
   KeyError，确认 RSA+AES 加密 hook 正确触发，再用 `pyobfus-unscrub` 完整
   解密回原始 traceback——free-threading 下全链路走通。新建
   `docs/PYTHON314_FREETHREADING.md`，诚实声明适用范围（验证的是单进程使用
   场景，没有专门做并发多线程访问 Pro 运行时状态的压力测试，因为这不是
   pyobfus 的正常使用模式）。
4. ✅ `P2-33` **已发布于 `vscode-extension` 0.4.1**（Marketplace 手工上传已
   完成，微软确认邮件已收到，公开 listing 核实为 `"version":"0.4.1"`）。
   调研发现原计划部分过时——`package.json` description 和 README "Why trust
   this extension" 小节其实早在之前的 session 里就已经把 OpenSSF/PEP740
   放得很显眼了，不是"只塞在 README 里点进去才看到"。真正补的是这次扫描里
   发现的新证据：**Nx Console 事件**（220 万安装量、带 Marketplace 自己的
   "Verified Publisher"徽章，2026 年 5 月还是被植入了凭证窃取器）——比原有
   的 2025 年 4 月"Python Obfuscator for VSCode"案例更有说服力，直接证明
   徽章不可靠。另外补了两条此前没写但真实可核实的信号：零个 open CodeQL
   alert（链接到 Security tab）+ CI/CD 全部第三方 Action SHA-pinned
   （`gh api` + `grep` 实测核实后才写）。

### 下一轮功能候选（首选项已随 0.5.18 / 0.3.9 发布）

2026-08-26 已完成本轮本地代码审计与官方资料调研，完整证据和取舍见
`docs/FEATURE_EXPANSION_RESEARCH_2026-08-26.md`。2026-08-27 已把首选候选
（配置感知 `--check`）落成**可直接实现的设计** `docs/CONFIG_AWARE_CHECK_DESIGN.md`
（含 `--check`/MCP 共用的 `core/config_resolve.py` helper、`PreflightReport` 增量字段、JSON
契约全文、测试清单、rollout）。调研+设计解决了技术依据，但不等于用户验证；
用户已于 2026-08-28 打开实现 gate，并接受下方三个推荐决策；首选项已进入
代码与测试，并在用户明确批准后完成 0.5.18 / 0.3.9 全渠道发布。2026-09-01
Stripe 已给出最终文档结论，Invoice Receipt 已交付客户，发票事项结案。

**发布 gate（用户 2026-08-28 再确认）**：实现完成不等于允许发布。正式改
版本号、打 tag 或触发 PyPI/MCP/Marketplace 发布前必须再次取得用户明确同意。
多个功能不捆成一次大版本：本轮只准备配置感知 `--check`；dry-run plan 与
syntax-only verification 留作后续独立节奏项，结合下载回落情况，通常至少间隔
1–2 天逐项评估和发布。

**测试隔离已修复（2026-08-28）**：trial、Pro license cache、license-embed
run counter 测试不再读写开发者真实 `~/.pyobfus` / HOME，而是逐测试绑定
pytest `tmp_path`。在 Codex 的只读 HOME 沙箱中直接运行标准
`venv/bin/pytest tests/` 已通过（1201 passed, 1 skipped），不再需要临时覆盖
`HOME=/tmp/...`；生产默认状态路径未改变。

**今日发布验证（2026-08-28）**：Core 0.5.18 / MCP 0.3.9 的版本元数据、
CHANGELOG、README highlight、MCP `server.json` 与依赖下限（`pyobfus>=0.5.18`）
已同步。Core 1201 passed / 1 skipped、MCP 93 passed、端到端 7 passed，Black、
Ruff、联合 mypy、tool manifest 均通过；两包 wheel/sdist 在 `/tmp` 隔离构建，
四个制品 `twine check` 全通过，并在全新 venv 中按 Core→MCP 顺序安装后核实
`pyobfus --version == 0.5.18` 与 MCP manifest digest。首次主分支 CI 因尚未发布的
Core 依赖下限导致 MCP latest-SDK smoke 从 PyPI 解析失败；提交 `99a6b84` 改为
同时安装本地 Core 候选后，全矩阵复跑通过。随后按 Core→MCP 顺序发布，四个
provenance endpoint、两个 GitHub Release、MCP Registry `active` / `isLatest`
以及公开 PyPI 全新安装均已核实。CI 另提示旧版 `setup-python` 将由 GitHub
强制切到 Node 24；后续应在独立维护提交中核实并更新固定 SHA，不阻塞本次发布。

**已确认的 3 个设计决策**（详见设计文档 §Open questions）：
1. `--check PATH` 的配置发现根：跟 build 一样用工作目录（推荐）vs 相对 `PATH`。
2. `mitigated_by` 是否允许改写 `--check --json` 里的 `severity` 字符串
   （永不动 `high`、永不影响 `exit_code`），还是只加注解、保留原 severity。
3. 首版降级范围是否够（只 `exclude_names ↔ dynamic_attr` 字面量 +
   `safe` preset 的 `__all__`），其余降级留后续。

1. **配置感知的 `--check`（当前首选代码候选；设计已完成）**
   - 已有依据：P2-29 收口时已经明确记录 `--check` 接入 `--config` /
     `exclude_patterns` 可降低真实组合误报；CLI/MCP/VS Code 共用现有 Risk
     contract，增量路径清楚。
   - 调研结论：复用真实 build 的 config discovery/override；excluded file 的
     finding 从主风险数移出但单列 `excluded_findings`，不静默丢失；只有配置
     确实缓解风险时才注释/降级，dependency declaration 保持项目级扫描。
   - 设计要点（`docs/CONFIG_AWARE_CHECK_DESIGN.md`）：新增 `--no-config`
     回退开关；`--check` 开始认已有的 `--config`/`--preset`；新增
     `core/config_resolve.py::resolve_effective_config`，先供 `--check`/MCP
     共用并镜像 build 优先级；build 重构留到 dry-run plan 独立增量，避免本轮
     顺带改变成熟的 build/Pro license 路径；
     `PreflightReport` 增 `files_excluded` + `excluded_risks`，`to_dict()`
     增 `effective_config`/`files_excluded`/`excluded_findings`，`Risk` 增
     可选 `mitigated_by`——`severity_counts`/`exit_code`/`risks[]` 形状对
     现有消费方不变；预计单个 `pyobfus` minor（0.5.18），MCP 侧
     `use_project_config` 可同波或后续 `pyobfus-mcp` 版本。

2. **结构化保护计划 `--dry-run --json` plan 对象**
   - ✅ **2026-08-30 已随 `pyobfus 0.5.19` 发布**：沿用现有
     `--dry-run --json`，新增 versioned `plan` 对象；commit `3758482`。
     JSON 列 effective config 摘要/哈希、选中与排除文件及原因、planned
     artifacts，并用 `ship` / `retain-internal` / `optional` 标明交付角色。
     所有路径只给 cwd-relative label 或 basename，不输出源码 literal、密钥、
     device fingerprint 或绝对 home path；`apply_supported=false`，不能把 plan
     保存后直接 apply。非 dry-run JSON contract 不新增 `plan`。
   - 调研结论：有 Terraform plan/JSON、Nuitka compilation report 等成熟工作流
     证据，但无需新增命令；优先给现有 `--dry-run --json` 增加 versioned `plan`
     对象，列 effective config 摘要、选中/排除文件与原因、planned artifacts。
   - 安全边界：不输出 literal/vault/key/device fingerprint/绝对 home path；首版
     plan 不可保存后直接 apply，避免引入第二套状态管理。

3. **受控的构建后验证**
   - ✅ **2026-08-30 已随 `pyobfus 0.5.19` 发布**：新增显式
     `--verify-syntax`；commit `1a1b18c`。构建写出后逐个读取生成的 `.py` 并在
     内存调用 `compile(..., "exec", dont_inherit=True)`，不 import、不执行、
     不生成 `__pycache__`。JSON 只报告 `mode=syntax-only`、`syntax_valid`、
     `files_checked` 与相对错误位置；失败返回结构化 error 并明确禁止交付。
     `--dry-run` 与 `--verify-syntax` 互斥，避免声称验证尚未生成的产物。
   - 调研结论：拒绝任意 `--verify-command` 和默认 import（会执行用户代码）；
     只做 syntax-only spike，优先内存 `compile(..., "exec")`，不在输出目录留下
     `__pycache__`。JSON 只能声明 `syntax_valid`，不能宣传 runtime verified。
   - MCP 不接受任意命令；隔离 import verifier 仅在将来有明确需求时再研究。

4. **标准 delivery bundle**
   - 调研结论：当前不做 zip/tar bundle；自动把 mapping 与交付代码打包是安全
     foot-gun。改为在 plan/provenance 中将 artifact 标为 `ship`、
     `retain-internal`、`optional`，保持 mapping 默认在 output 外。
   - 只有反复出现“需要单一交付包”企业反馈时才重新评估 archive。

5. **mapping 安全增强**
   - 调研结论：先做 mapping-inside-output warning + 安全存储文档；需要真实性
     的团队可用 Sigstore/cosign 对覆盖 mapping digest 的 provenance 签名。
   - 内置加密暂缓：它会引入密码/密钥输入、CI secret、恢复/轮换和 encrypted
     unmap UX；没有具体存储威胁模型前不实现。

6. **轻量团队/许可证管理 UX**
   - 调研结论：近期只补 vendor/billing FAQ、三设备/CI/缓存删除与服务端撤销的
     边界说明；现有 `status --json` 已覆盖本机信息。
   - 自助 list/deactivate 需要 Worker machine-resource model、客户鉴权和隐私/
     并发处理，等重复 activation 支持请求再 spike；不做 portal/SSO/复杂 server。

7. **`dependency_advisory` 第二阶段**
   - 已有专项机会/竞品扫描与毕业标准；候选仍是注册后可疑度、SARIF/CI、缓存/
     并发、私有 index allowlist。继续以真实反馈触发，不立即拆包。

8. **兼容性矩阵自动化**
   - 已有 P2-29 advisory、三篇 cookbook、PyInstaller/compiled/import-hook
     示例与 Python 3.14t 实测基础；“统一 compatibility report 命令”尚未做
     独立用户价值调研。
   - 调研结论：不新增 `compatibility-report` 命令；把 detected signals、配置缓解
     和 cookbook 链接合入 config-aware `--check`/dry-run plan。静态扫描永远不
     输出“已兼容”结论；只有复现过的支持案例或实测组合才扩规则。

### P3：探索项

1. `P3-1` `--output-pyc` feasibility spike
   - 只做 spike，不承诺产品化。
   - 退出标准：
     - 是否明显提高 decompilation resistance；
     - 是否保留 mapping/unmap 和 traceback debugging；
     - 是否破坏框架反射兼容；
     - 是否影响 PyInstaller / packaging；
     - 是否只是低质量模仿 PyArmor/SOURCEdefender。

2. `P3-2` hosted/remote MCP endpoint
   - 等 Glama / Claude 外部分发稳定后再考虑。
   - 如做，只先暴露 read-only / side-effect-free tools。
   - 必须有 rate limit、audit log、无 token passthrough。
   - 不牺牲本地 stdio MCP 的可靠性。

## 明确不做

- 不把 PyArmor-style BCC/JIT/Themida/VMC 作为 v0.6 主线。
- 不把 attestation / manifest 宣传成“代码可信证明”。
- 不为当前 stdio MCP server 实现 HTTP OAuth / Server Card / hosted connector。
- 不做 anti-VM / sandbox-evasion 类能力，避免工具定位被污染。
- 不做云端 obfuscation-as-a-service，避免破坏隐私定位。
- 不做复杂企业 license server；可保留 Cloudflare Worker / recipe 级参考。
- 不追 PyLocket 的逐函数字节码加密+设备绑定密钥架构（仍属 native/opaque
  runtime 主线，非 AI-debuggable 定位）；不建它那种 licensing/checkout/
  delivery 商业化平台（是完全不同的产品类别）。

## 下次工作建议

### ✅ 外部状态复查已收口（2026-09-02）

- MCP Registry 0.3.10 已在端点恢复后成功发布，公共 version endpoint 核实
  `active` / `isLatest=true`；无需重打 tag、重发 PyPI 或改代码。
- docs commit `289752a` 的 CI run `33521916080` 已 success；其 CodeQL / Pages
  以及最新收尾 commit `4b7bf9a` 的 CI / CodeQL / Pages 也全部 success。
- 本轮 Core 0.5.20 / MCP 0.3.10 发版已完成全渠道验证，无剩余发布事项。

1. `dependency_advisory` 已随 `pyobfus 0.5.17` / `pyobfus-mcp 0.3.8` 发布并
   完成 PyPI、PEP 740 provenance、GitHub Release、MCP Registry 全渠道核实。
   下一步按下方毕业标准收集真实使用反馈；`vscode-extension` 本轮无待发布
   内容，保持 0.4.1。
2. `P2-29` compatibility checks（0.5.15）与本轮 `P2-30`~`P2-33`（本轮发布）
   均已收口。后续若有真实用户反馈新的交付组合（如 PyInstaller 之外的
   bundler、其他 import-hook 产品），再机会性扩检测信号或补 cookbook，
   仍遵守"优先诊断 + 文档、不新增 transform"。
3. Glama：2026-08-20 已有多位第三方 maintainer 独立复现我们报告过的两个
   症状（构建卡 `debian:trixie-slim`、页面正常但公开 API `tools: []`），
   进一步确认是 Glama 平台侧问题。继续被动等 `#support` 回复，不主动追发
   消息、不改代码。✅ **2026-08-21 已复查**：旧 API 路径仍 `not_found`、
   公开页面 8 工具可列出但版本元数据陈旧（v0.5.13，且 08-22 发现它把核心包
   `pyobfus` 的 Release 标签和 `pyobfus-mcp` 自己的版本号搞混，见
   `docs/DISTRIBUTION_CHANNELS.md` Glama 小节）。`pyobfus-mcp==0.3.8` Build
   steps 已更新，新测试 success 且实时列出 8 工具，无需再手工 re-pin。下次
   只需检查：① 公开 API 的 `tools: []` 是否恢复；② Discord 是否回复。
4. Claude plugin marketplace：用户于 2026-08-24 再次手工确认仍为
   `Submitted and pending review`（Aug 2），只需等待 approve/reject/补充信息。
5. 下载量：✅ 2026-08-26 已完成第一次 post-release 复查。08-24 发布日为
   `137/99`，08-25 回落为 `27/8`；最新 rolling day/week/month 为
   `27/512/2,178`、`8/245/874`。非发布日基线没有明显抬升，维持“发布/CI
   噪音，未证明有机增长”判断。此后恢复每 3-5 个版本或 1-2 周的周期。
6. 竞品/生态扫描节奏：本项目历史扫描是"版本发布前后触发一次"，不是固定
   周期盯梢（05-09→06-22→07-07→08-06→08-14→08-20，间隔 1-6 周不等）。
   2026-08-22 又做了一轮（见下方"2026-08-22 扫描"小节），产出的行动项已
   held 到 main，等下次自然发布节点再切版本号——不要因为"该扫了"本身去扫，
   要有具体触发点（新对手/生态政策变化）或临近下次发布。
   **2026-08-31 又做了一轮 + 长尾词/AI 搜索优化规划**（用户请求触发）：完整
   结论、竞品表、15 个 surface 的关键词计划与 Wave A/B/C 优先级见
   [`docs/SEO_AND_COMPETITOR_SCAN_2026-08-31.md`](SEO_AND_COMPETITOR_SCAN_2026-08-31.md)。
   要点：PyArmor 9.2.7 / Nuitka Commercial 无实质变化；两个新 AST 系
   entrant（`davidteather/python-obfuscator` MIT v0.1.0 很薄但撞通用名、
   CodeEnigma ~58★ 定位最像但走加密字节码 loader、无反向映射/AI/MCP）；
   在线混淆站是 comparison 关键词的真实 SERP 对手；slopsquatting 检测赛道
   已拥挤（喂给 #8 的 graduation 判断）。执行等用户 gate。
7. **新增（2026-08-22，源自 `~/projects/NEXT_TOOL_OPPORTUNITY_SCAN.md`
   机会扫描）：pyobfus-mcp 去申请 MCP 信任目录徽章**——扫描时发现 MCP
   信任评分赛道已有至少 4 个独立竞品（MCP Skills 的 Verified badge、
   Canopii Trust Index、MCP Trust Checker、企业级 MintMCP+SOC2），结论
   是"不做新产品，去申请徽章"这个低成本分发动作。下次 cold-start 做：
   ① 去 MCP Skills（mcpskills.io）用 pyobfus-mcp 的 repo/PyPI 包地址跑一次
   trust score，若 composite score ≥7.0 门槛达标就申领 Verified badge；
   ② 去 Canopii Trust Index（index.canopii.dev）和 MCP Trust Checker
   （mcptrustchecker.com）确认 pyobfus-mcp 是否已被收录/评分，未收录则
   提交登记。三个都是只读扫描 + 表单登记，不涉及代码改动，不占用现有
   "1-2 天间隔"发布节奏。做完后把结果（score/badge 状态）记回
   `docs/DISTRIBUTION_CHANNELS.md` 的 Glama 小节旁边。
8. **新增（2026-08-22）：`dependency_advisory` 发布后的"毕业标准"跟踪
   计划**——user 明确要求"先内部做、但一定要关注后续使用情况，可能还需要
   主动征求用户意见，并且观察网上同类竞品的情况"，同时表态自己倾向认为
   最终独立包更好。发布（等用户通知）之后按下面三条持续跟踪，作为"留在
   pyobfus 内部" vs "拆成独立包/品牌"的判断依据：
   - **使用信号**（pyobfus 无遥测，只能看间接信号）：GitHub issue/
     Discussion 里是否有人主动提到这个检查、是否有人问"能不能脱离混淆
     单独用"、`--check`/`check_obfuscation_risks` 相关的 Star/下载增量
     是否在发布窗口后出现异常。每次例行下载量复查（见上面第 5 条）时顺手
     瞄一眼 GitHub 通知，不用单独起一个监测任务。
   - **主动征求意见**：下次发布这个功能时，release notes / README 里
     明确写"这是一个实验性功能，欢迎反馈"并给出 GitHub issue 模板入口，
     而不是悄悄上线指望自然被发现——用户已经说了"可能还需要主动征求"，
     不要假设沉默=没需求。
   - **竞品动态**：`slopcheck` 及其他 hallucinated-dependency /
     slopsquatting 检测工具的成熟度目前仅初步核实过（见机会扫描文档），
     下次触发竞品扫描（第 6 条节奏）时顺带查一次这个细分类目是否有新
     进入者或明显做得更好的对手，而不是假设格局不变。
   - 判断"何时拆独立包"没有固定时间表，出现下面任一信号就该主动向 user
     提出讨论，而不是等 user 先问：① 有人明确提出"不要混淆功能，只要这个
     检查"；② 竞品格局出现值得抢位的空窗（例如 slopcheck 明显不活跃/
     体验差）；③ 使用信号显著高于 pyobfus 其它 advisory 类别（说明买家
   画像可能不同，见本次讨论第 2 条判断依据）。
9. **2026-08-24 审计后的执行顺序**：
   - 本轮外部渠道、下载/反馈基线、MCP Skills 与 Canopii 证据已冻结到
     `docs/EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md`；几天后复查应以该文档
     为对照，不凭印象比较 rolling 数字。
   - ✅ 08-26 已完成首次复查：08-25 PyPI 下载回落为 `27/8`，GitHub clone
     回落为 `10/6 unique`；issue/PR/Discussion 无新增，README/CHANGELOG 各仅
     3 unique views。尚无有机增长或 advisory 独立需求信号。
   - Claude plugin 仍 pending；Glama 21:09 测试已成功，二者本轮核实完成。
   - MCP Skills 已实跑：6.06 / established / 14 signals / no safety findings，
     但因 `SINGLE_AUTHOR_LOW_ADOPTION` + `low_legit` disqualifier 未达 Verified。
     不花钱买 full report、不为评分刷指标，等真实采用/外部贡献后复评。下一步
     转向 Canopii / MCP Trust Checker 的评分与收录流程。
   - Canopii 当前只扫描到 MCP v0.3.7，显示 39/F；唯一 high evidence 是
     sibling Pro runtime 的 `marshal.loads`，且位于认证 AES-GCM 解密之后，
     MCP tool 输入无可达路径。按误报处理：先 claim + 请求 v0.3.8 rescan；
     若仍命中，再向 Canopii CLI 提交带数据流和 monorepo subfolder 证据的
     upstream issue。当前不嵌 F badge、不为扫描器改产品逻辑。
   - 若 1-2 周仍无主动反馈，开一条简短 GitHub Discussion 投票，明确问：
     “留在 pyobfus --check / 独立 Python 包 / 暂无需求”，不能把无 Issue
     等同于无需求。
   - 在出现毕业信号前，不立刻拆包。若进入独立包 spike，第一批候选不是更多
     registry，而是：注册后可疑度（包年龄/发布历史/源码链接）、SARIF/CI
     可阻断模式、缓存/并发/私有 index allowlist；保持现有 advisory 默认
     非阻断和诚实能力边界。
10. **2026-08-27 客户跟进与下一轮功能 gate**：客户已回复开票主体（公司
    实体，见 `docs/internal/CUSTOMER_SUPPORT_LOG.md` 2026-08-27 条）。
    ✅ **2026-09-01 已完成**：Stripe Support 最终确认 `send invoice` 的 invoice
    PDF 不会因后续付款而改成零余额或 `Paid`，Invoice Receipt 才是正式付款
    证明。已在客户原线程解释并纠正先前预期，附上正确 receipt；错误 invoice
    PDF 未发送。不得贷记、退款、解除付款或重扣。客户回访改为被动等待客户
    邮件，不主动追发；若收到实际使用功能或大项目/CI/CD/团队工作流反馈，作为上方 P2 候选
    排序证据。`--plan` 已随 0.5.19 发布；delivery bundle、mapping 加密、团队
    license UX 仍需真实重复需求才做。
11. **✅ 长尾词 / AI 搜索优化 rollout（2026-09-01 完成）**：
    完整规划 = [`docs/SEO_AND_COMPETITOR_SCAN_2026-08-31.md`](SEO_AND_COMPETITOR_SCAN_2026-08-31.md)
    §2（15 个 surface + 目标意图短语 + Wave A/B/C + 红线）。用户意向：**过几天
    就这些内容发一个小版本（或与其它功能合并发布）**。执行拆分：
    - **Wave A**（维护者操作，非代码，无需发版，可立即做）：改 GitHub 仓库
      description（去掉 "Enterprise-grade / 50% lower cost" 定位漂移）、补
      `homepageUrl` = RTD、加约 7 个 topics；可由维护者在 GitHub 设置页或
      通过认证 API 完成。
      ✅ **2026-09-01 已通过 GitHub API 完成**：description 已改为 AST + reverse
      mapping + pre-shipping / AI-debuggable intent；homepage 指向 RTD；topics
      13→19，新增计划中的发现词并移除易误导的 `python-obfuscator-online`。
      可选 S14 置顶 FAQ Discussion 暂不创建，等待真实讨论触发。
    - **Wave B**（纯 docs，无发版 gate，可随时并入一轮 `docs:` commit）：
      `ai-catalog.json` `representativeQueries` 4→~10；`llms.txt` 三孪生加
      精简 `## FAQ` + `## Compared to`（改后 `cmp` 必须 byte-identical +
      `mkdocs build` 复核 + 保持精简）；`mkdocs.yml` `site_description` 扩写；
      `docs/index.md` 引言段重写；`COMPARISON.md` 补 CodeEnigma /
      `python-obfuscator` / SOURCEdefender / 在线工具行；`CITATION.cff`
      keywords（**不碰 version/date-released**）。
      ✅ **2026-09-01 已完成**：AI catalog 扩到 10 个代表性任务问句；两份
      `llms.txt` 增 FAQ + Compared to 且 byte-identical，`llms-full.txt` 增选型
      问答；扩写 RTD meta description 与首页引言；comparison 补 CodeEnigma、
      `python-obfuscator`、SOURCEdefender、在线工具；CFF 只增关键词，未动归档
      version/date。JSON/CFF 解析、`cmp`、`git diff --check`、MkDocs strict build
      均通过（仅既有链接/nav warnings）。S15 JSON-LD 暂不做。
    - **Wave C**（并入下次发版的同一 commit，PyPI 需版本号才刷新）：
      `server.json` description 改意图短语（走 `pyobfus-mcp` 版本）；两个
      `pyproject.toml` 的 keywords 补 `reverse-mapping`/`unmap`/`deobfuscation`/
      `provenance`/`slopsquatting`/`obfuscate-before-shipping` 簇；README FAQ
      加 3 条 + 引言段确保含 "obfuscate before shipping" / "debug obfuscated
      stack traces"（**必须在打 tag 前的同一 commit**）。
      ✅ **已经用户明确批准作为独立 SEO 版本发布**：Core
      0.5.20 / MCP 0.3.10 的 PyPI、PEP 740、GitHub Releases 与 MCP Registry
      均已核实；Registry 0.3.10 为 `active` / `isLatest=true`。
    - 红线：同一短语不跨 >2 surface、不堆砌；发版前复核 "50% lower cost"
      对 PyArmor 现价是否仍成立（`COMPARISON.md` 仍写 $89）。
    - 附带的 `dependency_advisory` #8 判断：slopsquatting 检测赛道已拥挤
      （见 scan §1.2），倾向**保留在 `--check` 内部不拆包**，待用户确认。

## 恢复工作清单（发票交付后按序执行）

> 2026-09-01 cold-start：Stripe 已确认 invoice PDF 的表现是 `send invoice`
> 流程设计，正确付款证明为 Invoice Receipt；客户说明与 receipt 均已发送，
> 支持事项完成，本清单立即生效。仍不要贷记/退款/解除付款/重扣；正式发版继续
> 等待用户单独确认。

1. **前置检查**：`git status` 干净、`origin/main` 已同步；三个测试根
   （`tests/`、`pyobfus_mcp/tests/`、`integration_tests/`）+ `black`/`ruff`/
   CI 用的联合 `mypy pyobfus/ pyobfus_pro/ pyobfus_mcp/pyobfus_mcp/` 全绿。
2. **确认 3 个设计决策**（见上方“下一轮功能候选”小节，或直接问用户）——
   发现根、`mitigated_by` 是否改 severity、首版降级范围。定了才动手。
3. **实现配置感知 `--check`**，严格按 `docs/CONFIG_AWARE_CHECK_DESIGN.md`：
   - 新建 `pyobfus/core/config_resolve.py`（`resolve_effective_config` +
     `ConfigProvenance`），本轮供 `--check`/MCP 共用；build 路径重构延后到
     dry-run plan 独立增量，届时必须保持同 config 对象和 Pro license gate。
   - `pyobfus/cli.py`：`_handle_check` 加 `config_path`/`preset`/`no_config`/
     `level` 参数；dispatch 处转发已解析值；新增 `--no-config` flag；
     `format_report_text` 加 “Effective config” + “Excluded files” 两行。
   - `pyobfus/core/preflight.py`：`PreflightChecker` 加 `preserve_names`/
     `report_excluded`；`_check_directory` 分桶 included/excluded；
     `PreflightReport` 加 `files_excluded`/`excluded_risks`，`to_dict()`
     加 `effective_config`/`files_excluded`/`excluded_findings`；`Risk` 加
     可选 `mitigated_by`；`_finalize` 实现两条降级规则 + 依赖 advisory
     保持项目级（加注释说明）。
   - 测试：按设计文档 §Tests 清单补 `tests/test_preflight.py`、
     `tests/test_json_cli.py`、`pyobfus_mcp/tests/`、config_resolve 单测；
     守住 “`PreflightChecker()` 无参 → `to_dict()` 与改动前逐字节一致”。
   - 文档：`docs/DEPENDENCY_ADVISORY_COOKBOOK.md` 补注释；README `--check`
     示例块 + `docs/llms.txt` 加 “`--check` 与你的配置” 小节。
4. **MCP 侧**（可同波或后续 `pyobfus-mcp` 版本）：`check_obfuscation_risks`
   加 `use_project_config: bool = True`，payload 增 `effective_config`/
   `excluded_findings`；更新 `pyobfus_mcp/CHANGELOG.md` + tool-manifest
   描述；VS Code 无需改。
5. **发布**：0.5.18 / MCP 0.3.9 已在用户最终批准后完成 tag、PyPI、GitHub
   Release、PEP 740 provenance、MCP Registry 与公开安装验证。后续版本继续在
   发布前运行 `scripts/check_unreleased_changelogs.py`，固定先 Core、后 MCP，
   并逐次取得用户明确批准。
6. **候选 2/3**（`--dry-run --json` plan 对象、syntax-only 验证 spike）：
   ✅ 已于 2026-08-30 按两个独立 commit 实现，经用户明确批准组成
   `pyobfus 0.5.19` 发布（tag `v0.5.19`，OIDC + PEP 740，PyPI/GitHub Release/
   全矩阵 CI/CodeQL 均绿，全新 venv 安装核实带两个新 flag）。发布前质量门为
   Core 1208 passed/1 skipped、MCP 93 passed、端到端 7 passed，Black/Ruff/
   联合 mypy 全绿。MCP 与 VS Code 扩展本轮 `[Unreleased]` 均为空，未动。
7. **长尾词 / AI 搜索优化 rollout**（见上方"下次工作建议" #11 + scan doc §2）：
   ✅ Wave A/B/C 均完成；Core 0.5.20 / MCP 0.3.10 已完成 PyPI、PEP 740、
   GitHub Releases 与 MCP Registry 全渠道核实，无剩余发布事项。
