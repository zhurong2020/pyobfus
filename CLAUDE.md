# pyobfus 开发约定

Modern Python Code Obfuscator - 基于 AST 的 Python 代码混淆器。

> 通用 agent 约定(build/test/lint、仓库结构、专利 gate 等)见根目录 [`AGENTS.md`](AGENTS.md)(规范源,工具无关)。本文件保留 Claude / 中文 / 专利申报相关的项目专属细节。
>
> @AGENTS.md

## ⚡ Current pending work (cold-start 必读)

**Single source of truth for current plan**: [`docs/CURRENT_PLAN_ZH.md`](docs/CURRENT_PLAN_ZH.md) — 重启 session 第一份必读

`docs/ROADMAP.md` 和 `docs/POST_V0.4_TODO.md` 已归档为历史执行记录和细节来源。日常优先级、外部 blocker、下次工作建议都以 `docs/CURRENT_PLAN_ZH.md` 为准。

### ⏳ 2026-08-30 — 客户 paid-invoice PDF 已升级 Stripe 工程处理

- **`pyobfus 0.5.19` 已发布（2026-08-30，用户明确批准）**：把此前 held 的两个
  独立 commit 组成 Core 小版本——`3758482` 的 `--dry-run --json` versioned
  `plan` 对象（effective config / 选中与排除文件及原因 / artifacts 交付角色，
  只给 cwd-relative label，`apply_supported=false`）与 `1a1b18c` 的 opt-in
  `--verify-syntax`（构建后内存 `compile()`，不 import / 不执行 / 不写
  `__pycache__`，JSON 只声明 `syntax_valid`）。tag `v0.5.19` 经 OIDC + PEP 740
  发到 PyPI，wheel/sdist 两个 Integrity provenance endpoint 均 HTTP 200，全新
  venv `pip install pyobfus==0.5.19` 已核实带上两个新 flag，GitHub Release 已建，
  Release / CI 全矩阵 / CodeQL 均绿。发布收尾提交为
  `docs: record pyobfus 0.5.19 release`。MCP 与 VS Code 扩展本轮
  `[Unreleased]` 均为空，未动。
- **docs cleanup 已做（2026-08-31，commits `4482eb7`/`f1c3e4a`/`ac6a572`/`e3ed135`）**：
  ① `llms.txt` ↔ `docs/llms.txt` 双向 drift 完整对账，`cmp` 已 byte-identical、
  指针全 resolve、`mkdocs build` 核实 `docs/llms.txt` 发布到站点根；顺带刷新
  `llms-full.txt`（MCP 工具表 5→8 个、按 shipped `tool_manifest.json` 校对签名，
  Versioning 段补到 0.5.19，示例 header `v0.5.6`→`v0.5.19`，Links
  `Roadmap`→`Current plan`）。`llms-full.txt` 无 `docs/` 孪生（llmstxt.org 规范
  只要求 `/docs/llms.txt`）。② mkdocs Home 页 `docs/index.md` 补 headline 反向
  映射/`--check`/0.5.19 flags + 补全 Pro build-fusion 行 + 过期 `--expire`
  示例日期；`CONFIG_AWARE_CHECK_DESIGN.md` 时态修正 + `PROVENANCE_MANIFEST.md`
  样例 JSON 版本 0.5.13→0.5.19。其余（`AGENTS.md`/`pyobfus_mcp/README.md` 8
  工具表/`SKILL.md`/`templates/`/`_drafts/` 0.4.0 营销稿/归档 docs）核实无需改。
- **当日小版本发布已完成**：用户明确批准后，`pyobfus 0.5.18` 与
  `pyobfus-mcp 0.3.9` 已按 Core→MCP 顺序通过 OIDC 发布；两个 GitHub
  Releases、四个 PyPI provenance endpoint、MCP Registry
  `active` / `isLatest=true` 和公开 PyPI 全新安装均已核实。配置感知
  `--check` 是本轮唯一功能，dry-run plan 与 syntax-only verification 继续
  保持为后续独立节奏项，每次正式发布仍须用户单独批准。发布标签都指向
  `99a6b84`；发布收尾文档提交为 `0cf24be`，已 push，CI/CodeQL/Pages 全绿。

- 08-24 发布后的首轮完整数据已复查：发布日下载为 Core 137 / MCP 99，
  08-25 随即回落为 27 / 8；GitHub issue、PR、Discussion 均无新增，维持
  “发布/自动化噪音，尚无有机增长”判断。证据已追加到
  [`docs/EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md`](docs/EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md)。
- 一位真实 Pro 客户确认使用进展良好，并要求为既有 Payment Link 购买开票。
  客户已回复收票主体（公司实体）；开具发票时撞上 Stripe 的 guest-customer /
  付款应用不匹配问题（Payment Link 一次性购买记在 guest customer 名下，
  无法把既有付款应用到 regular Customer 的发票），已于 2026-08-27 联系
  Stripe Support 等待回复。不把单次开票需求提前解释为团队许可或企业功能
  需求。（2026-08-30 追加：既有付款现已成功关联，Dashboard 与 receipt 均为
  已付/US$0.00 remaining；但按 Support 指示从实时 Dashboard 新下载的 invoice
  PDF，在付款关联 84+ 小时后仍错误显示全额应付，已排除误开旧文件和其所称的
  24 小时 CDN 延迟。新 PDF 与实时状态截图已附回原线程，请 Billing/Invoicing
  工程团队重生成。不得开贷项通知单、退款、解除付款或重扣。客户确认未收到
  Stripe 的错误自动邮件，且已获告知无需付款或操作；冷启动无需再发例行进度
  更新。）当前状态、hold 清单与后续
  步骤以 `docs/CURRENT_PLAN_ZH.md` 为准；具体客户/支付信息只留在 Git 忽略
  的 `docs/internal/` 运营记录，绝不进入公开提交。
- 下一轮功能方向已完成代码审计与官方资料调研，见
  [`docs/FEATURE_EXPANSION_RESEARCH_2026-08-26.md`](docs/FEATURE_EXPANSION_RESEARCH_2026-08-26.md)。
  配置感知 `--check`（0.5.18）、`--dry-run --json` versioned plan 与
  `--verify-syntax`（均 0.5.19，见本节首条）都已发布。暂不做任意
  `--verify-command`、zip/tar delivery bundle、mapping 内建加密或团队 license
  后端。
- **🆕 已排入 TODO（2026-08-31，用户意向"过几天发一个小版本或与其它功能合并"）：
  长尾词 / AI 搜索优化 rollout** —— 竞品扫描 + 15 个 surface 的关键词计划见
  [`docs/SEO_AND_COMPETITOR_SCAN_2026-08-31.md`](docs/SEO_AND_COMPETITOR_SCAN_2026-08-31.md)，
  执行拆分与 gate 见 `docs/CURRENT_PLAN_ZH.md` "下次工作建议" #11 + "恢复
  工作清单" #7。Wave B（纯 docs）可先做；Wave C（keywords/README/`server.json`）
  进发版 commit；Wave A（GitHub 仓库 description/topics/homepageUrl）交用户
  在 GitHub 设置里操作，Claude 只出文案。除此之外下一功能方向仍须用户 gate。
- 本 session 全部产出已 push（0.5.19 发布 `beae06d`→`e99339b`→`452ba29`→`f91e78d`，
  docs cleanup `4482eb7`→`f1c3e4a`→`ac6a572`→`e3ed135`），tag `v0.5.19` 在 origin，
  工作区干净。逐轮明细以 `docs/CURRENT_PLAN_ZH.md` +
  `~/projects/WORK_LOG_INDEX.md` 顶行为准（每轮追加，是活的 tip 来源）。此前
  session 的 Stripe 交接、配置感知实现、HOME 隔离测试、发票工程升级状态也均已
  push。冷启动后先读 `docs/CURRENT_PLAN_ZH.md`，等待 Stripe Billing/Invoicing
  工程团队提供正确 paid invoice PDF；除非用户明确 gate，不启动下一项功能实现
  或发布。外部手工项仍是 Canopii claim/rescan、Claude plugin pending 观察，并在
  1–2 周后复查下载；若 9 月 1–7 日仍无 advisory 反馈，再考虑 GitHub Discussion
  投票。

### ✅ 2026-08-24 — 0.5.17 / MCP 0.3.8 发布与外部渠道收尾

- `pyobfus 0.5.17`、`pyobfus-mcp 0.3.8` 已通过 OIDC 发布；PyPI PEP 740
  provenance、GitHub Releases、MCP Registry `active` / `isLatest=true` 均已
  核实。VS Code 扩展保持 0.4.1。
- 本轮发布 `dependency_advisory`：CLI 默认联网、`--offline` 可关闭；MCP 的
  `verify_dependencies_online` 默认 false，只有显式 opt-in 才访问 PyPI。
- Glama 21:09 测试成功（12.1s），实际安装 Core 0.5.17 + MCP 0.3.8，实时
  `ListToolsRequest` 返回完整 8 工具。公开 API 的 `tools: []` 已坐实为 Glama
  目录同步问题；不再改本地代码或重复排查容器运行时。
- Claude plugin 仍为 Aug 2 `Submitted and pending review`。MCP Skills 扫描为
  6.06 / established / no safety findings，因低采用和单作者未达 Verified。
  Canopii 的 39/F 来自扫描 sibling Pro runtime 的 `marshal.loads` 语法命中，
  MCP 输入无可达路径；先 claim + 请求按 0.3.8 重扫，仍命中再报上游误报。
- 冷启动的完整数字、证据边界与 2-3 天后复查清单见
  [`docs/EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md`](docs/EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md)。
  当前开发/产品优先级仍只看 `docs/CURRENT_PLAN_ZH.md`。

### ✅ 2026-08-21 — 周期性复查（下载量 + Glama + Claude plugin），全部无变化

按"周期性发布后复盘节奏"做的轻量复查（非完整竞品扫描；2026-08-20 刚做过
完整版）：
- **下载量**：pypistats 快照与 08-20 基线**完全一致**（`pyobfus`
  26/295/1,912；`pyobfus-mcp` 8/124/687）——发布后的跳变未再放大，维持
  "发布噪音而非有机增长"判断，无新动作。
- **Glama**：旧 API 路径 `/api/mcp/v1/servers/io.github.zhurong2020/
  pyobfus-mcp` 仍 `not_found`；公开页面正常、仍列出 8 个工具，但版本元数据
  陈旧（停在 v0.5.13，当前 0.5.15）——维持"Glama 侧目录同步陈旧"判断。
  Discord `#support` 回复与 Recent Tests 需 user 登录查，本轮未变。
- **Claude plugin marketplace**：Console 登录墙无法程序化核实；user 08-20
  已查仍 `Submitted and pending review`（Aug 2），维持"机会性修 typo、被动
  等待"策略。
- 文档同步：`docs/DISTRIBUTION_CHANNELS.md`（版本号 0.5.14→0.5.15、
  Marketplace 上传状态、Glama/plugin 复查结果、GitHub Releases 行）与
  `docs/CURRENT_PLAN_ZH.md`（更新时间、下载复查、P0 小节、下次工作建议 3/5）
  均已同步。**下一步唯一动作仍是 P2-30~33 三包按"1-2 天间隔"各自独立发版**
  （0.5.15 是 08-20，08-21 间隔已够，cold-start 后即可执行）。

### ✅ 2026-08-20 — pyobfus 0.5.15 发布 + main CI 修复 + Glama 第三方独立复现证据

**发现并修复了一次未察觉的 main CI 红灯**：P2-29 的 `0ec2179` 提交（08-19
20:04 推送）在 `tests/test_preflight.py` 结尾多带了一个空行，触发
`black --check` 失败，`Lint and Type Check` job 已经红了约 19 小时无人
注意（此前几次发布只查了 Release/CodeQL，没查完整 CI 矩阵，跟 08-06 那次
P2-15 反调试测试连红 3 次是同一类"发布检查清单漏了完整 CI 矩阵"的疏漏）。
已本地复现、`black` 修好、验证仓库全部 161 个文件重新通过 `black --check`
且该文件 35 测试仍全过，commit `895a56b` 推送后 CI 转绿。

**顺势发布 `pyobfus` 0.5.15**：CHANGELOG `[Unreleased]` 段此前一直是空的
（P2-29 三个提交漏写），先补录（commit `6b0b613`），距上次发布（0.5.14，
08-17）3 天符合"1-2 天间隔"节奏，随后正式发版——版本号提升 + CHANGELOG
`[0.5.15]`成节 + README"What's new"横幅**这次在打 tag 前的同一提交里更新**
（吸取 0.5.14 那次教训，此次已验证 PyPI 新包快照带上了正确文案）。三个
测试根（1169+90+7 全过）+ black/ruff/mypy 全绿后打 tag `v0.5.15`，OIDC
发布 workflow `success`，PyPI JSON API 核实 `latest=0.5.15`。内容：`--check`
新增 `compatibility_advisory` 类别（P2-29）+ 三篇 cookbook + 两个
`examples/` 复现。

**Glama：第三方独立复现坐实此前两个猜测**（user 转发 `#support` 频道
08-08~08-18 全文，非我方自己的数据点）——至少 3 位其他 maintainer
（Considus/Andrei Lungeanu/ojkingston）报了与我们完全相同的
`debian:trixie-slim` 构建卡点错误签名，累计 5+ 个互不相关 server 撞到同一
故障；另有 maintainer（mellowmelomel 等）独立报了与 pyobfus-mcp 完全一致
的"页面工具正常、公开 API 却 `tools: []`/字段陈旧"症状。两点均确认是纯
Glama 平台侧问题，不需要我方改代码。Frank/Glama team 对频道内所有报告都
尚未回复，**用户决定不主动追发消息**。详见 memory
`glama_zero_tools_repro_2026-08-07.md`。

**下载量**（0.5.15 发布前快照，pypistats）：`pyobfus` day/week/month
26/295/1,912；`pyobfus-mcp` 8/124/687——较 08-17 安静基线周环比明显上升
（pyobfus +43%，mcp +170%），按历史经验暂不当真实信号，下次复查看是否回落。

Claude plugin marketplace：user 08-20 再核实仍 `Submitted and pending
review`（Aug 2），无变化。

**同日续（P2-30~33 落地 + 一个真实安全漏洞的发现/修复/部署）**：竞品扫描后
提出的四项候选（`docs/ROADMAP.md`「Planning refresh from 2026-08-20」）全部
动手实现——`docs/COMPARISON.md` 加 PyLocket 诚实对比；**真实**装 Cisco
`mcp-scanner` 扫真实发布的 `pyobfus-mcp` 0.3.6（8/8 SAFE、0 findings）；
**真实**下载 free-threaded Python 3.14.7 验证 Pro 运行时组件（核心测试
1169/1169 + 混淆/执行/崩溃/加密/解密全链路冒烟测试全过）；VS Code 信任信号
文案补 Nx Console 2026 事件+CodeQL-clean+SHA-pinned CI。四项均 held 在
`[Unreleased]`，未发布（下次按"1-2 天间隔"节奏判断）。

🔴 **过程中意外发现并已修复部署一个真实、可被利用的安全漏洞**：排查一位付费
客户活跃度时，在 `cloudflare-worker/src/index.js` 发现 Stripe webhook
从未校验签名（"TODO: Verify Stripe signature"从未实现）——任何人知道公开
URL 就能伪造请求白拿永久 Pro license，完全绕过付款。已复用仓库里 
`content_webhook.js` 已验证的 HMAC-SHA256 校验函数修复（commit `b49fdb2`，
5 场景功能测试全过：合法签名/篡改 body/错误 secret/**缺签名请求头**[即
原漏洞利用方式]/10 分钟前重放，全部按预期通过），**并已用 `npx wrangler
deploy` 部署到生产、现场重放原攻击确认 `HTTP 400 Invalid signature`**。
KV 里仅 4 条 license 记录全部对得上号（3 真实客户+1 自测数据），无证据
显示漏洞被实际利用过。`STRIPE_WEBHOOK_SECRET` 早在 2025-11-12 就已配置为
Cloudflare secret，纯代码修复，未新增任何密钥。

README 顺带两处修正：加了"Watch this repo → Releases"的 CTA（此前 0
watcher）；Pro Support 段落"any issues→email"改窄为"license/账号问题
留邮件，其他导去 GitHub"。

**跨项目动作**：① Gmail MCP（`claude.ai Gmail` 连接器）本 session 首次接入，
是账号级能力非 pyobfus 专属，已记入全局 `~/.claude/CLAUDE.md`；② 用 Gmail
搜索顺手查到 cardiac-manuscripts AIC-01(CAC Plus) 论文的拒稿信，动手更新
追踪文档前先去核对，发现该项目自己的 `STATUS.md` 已经领先于其"权威"
`PAPERS_MASTER_INVENTORY.md`——已同步该文件五处并单独 commit+push 到
cardiac-manuscripts 仓库（不影响 pyobfus 仓库本身）。

完整过程见 memory `pyobfus_p2_30_33_scan_followups_2026-08-20.md` +
`reference_pyobfus_pro_customer_outreach.md`（含安全漏洞完整时间线）+
`credentials_workflow.md`（Vaultwarden 凭证记录同步）+ 跨项目
`~/projects/WORK_LOG_INDEX.md` 顶行。

### ✅ 2026-08-17 — 三包发布完成 + session 收尾（pyobfus 0.5.14 / pyobfus-mcp 0.3.6 / vscode-extension 0.4.0）

**发布流程**：早前 session 积累的 17 个本地提交先推送到 `origin/main`（P-1），推送后 CI 首次真正跑这批改动，抓到一个真 mypy 回归（`_handle_verify_provenance_manifest` 的 `result` 被推断成 `Dict[str, object]`）并当场修复（commit `e883c0a`）。随后判断距上次发布（08-07）已 10 天、早过"1-2 天"间隔窗口，三包依次发版：
1. `pyobfus` **0.5.14**（provenance manifest CycloneDX 增强 + `--verify-provenance-manifest` + `--validate-config --json`）—— tag `v0.5.14`，OIDC+PEP740 workflow 绿，PyPI 核实 latest。
2. `pyobfus-mcp` **0.3.6**（`server.json` repository ID + 官方 `2025-12-11` schema 校验 + 新增版本同步回归测试）—— tag `mcp-v0.3.6`，PyPI 核实 latest；MCP Registry 也重新发布（`mcp-publisher login github` 缓存 token 已过期，走了一次新的 device-code 授权，用户在浏览器完成，`isLatest=true` 已核实）。
3. `vscode-extension` **0.4.0**（trace-marker mapping picker + `Validate pyobfus.yaml` 命令）—— 本地 51/51 测试绿（含对刚发布的 0.5.14 的真实合约测试），打出 `pyobfus-0.4.0.vsix`，tag `vscode-v0.4.0`，GitHub Release 已建并附 vsix。**Marketplace 手工上传已由用户完成**，`curl` 独立核实公开 listing 已返回 `"version":"0.4.0"`。

**✅ Glama Build steps 已由用户手工改到 `pyobfus-mcp==0.3.6`**——但触发的新构建（`01a00e39-...`）15 分钟后**失败**（`ECONNRESET`/"aborted"，卡在拉取 `debian:trixie-slim` 基础镜像元数据这一步），与 08-07 那次失败是第二个独立复现实例，同一卡点、不同错误签名，非我方包/配置问题（Build steps 本身已核实正确）。**用户决定继续观察，暂不追加 Discord 消息、暂不手动重试**。详见 memory `glama_zero_tools_repro_2026-08-07.md` 的 08-17 追加小节。

**两处发布流程教训，已固化进下方「发布流程」清单，避免重犯**：
1. **README"What's new"横幅必须在打 tag 前的同一提交里更新**——0.5.14 的 tag 只包含 `pyproject.toml`/`CHANGELOG.md`，横幅更新拖到 tag 之后的 docs-sync 提交里才做，导致 PyPI 包（不可变）永久错过这次快照，页面 description 卡在"v0.5.13"字样。用户决定不为此单独发版，等下次自然发布带上。
2. **PyPI 版本徽标（shields.io badge）是动态生成的，不需要、也不该被当作发布清单项**——用户同时问徽标是否也滞后，`curl` 直接探 shields.io 源头 + GitHub camo 代理确认两层当时已经是最新版本，纯粹是缓存/浏览器问题，跟①不是同一类 bug。

**AI 客户端清单扩充**：用户问 README"designed for X/Y/Z"是否该加国内主流工具，实时搜索核实（非训练记忆）后确认 GitHub Copilot（42% 市占率，仓库本就有 `copilot-instructions.md` 模板却漏提）和 CodeBuddy（腾讯云，中国首个支持 MCP 的编程助手）均属实有据，已加进 README/llms.txt/mcp README/两个 pyproject.toml description/server.json target_clients 共 6 个文件，README tagline 结尾改成"any MCP-compatible AI agent"泛称防止以后再漂移。

**外部状态（session 内多次复查，均未变化）**：Glama 旧 public API 路径 `not_found`，Discord `#support` 暂无回复；Claude plugin marketplace 仍 `Submitted and pending review`（Aug 2）。两条继续被动等待，不阻塞本地工作。

**下次 cold-start 顺序**：
1. 先读 `docs/CURRENT_PLAN_ZH.md`。
2. Glama：检查 `01a00e39-...` 之后 admin 面板 Recent Tests 有没有新构建尝试；Discord `#support` 有没有回复；`curl` 复查公开 API 的 `tools` 字段。
3. Claude plugin：只需确认 Console 状态是否变化。
4. P2-29 compatibility checks 已于本轮收口（见 `docs/CURRENT_PLAN_ZH.md` P1 小节）：`--check` 新增 `compatibility_advisory` 类别（import-hook/加密文件生态、编译打包、model-serving 三类真实交付组合），并补三篇 cookbook + 两个 `examples/` 端到端复现 + 回归测试；VS Code 红线与 MCP `check_obfuscation_risks` 经既有 `Risk` contract 自动继承这些建议，无需改那两处代码。后续若有新交付组合反馈，机会性扩检测信号或补 cookbook。

### ✅ 2026-08-02 — pyobfus 0.5.6 已发布，issue #25 已关闭，CodeQL 已清零

**pyobfus 0.5.6 已发布**（issue #25 修复 + benchmark 沙箱权限加固，commit `4f53c2e`/`8ec8abc`，tag `v0.5.6` 经 OIDC 发 PyPI，核实 latest=0.5.6）。mcp 仍 0.3.1（本次未涉及 tool surface 变化）。

**issue #25**（`preserve_param_names`/`remove_docstrings`/`remove_comments` 被 CLI 默认值静默覆盖，且波及全部 7 个 framework preset 的 docstring 保留承诺）：`pyobfus/cli.py` 3 个 flag 改成 tri-state（`default=None`），"Override config with CLI options" 代码块只在用户显式传参时才覆盖 preset/config 选择。三个测试根全绿（1074+73+7）+ black/ruff/mypy 全过，8 个新回归测试。**已关闭**（issue 评论总结 + 引用 commit）。

**同 session 顺带清零 2 条 open CodeQL 告警**（High/CWE-732 `py/overly-permissive-file`，`benchmarks/llm_resistance/scorer.py` 的 Docker 打分沙箱 temp dir chmod）：目录权限 `0o755`→`0o711`（仅 traverse 不可 list，driver 只按已知硬编码路径开 3 个文件、从不 list 目录），真实 Docker 沙箱验证通过，下次扫描自动 fixed。逐文件 `0o644` 是功能性必需（容器跑不受信任 LLM 输出，用与 host 无关的 UID `65534:65534` 防御纵深，与文件属主无共同 group，跨 UID 读内容只能靠 world-read bit）——已用 `gh api` 记录 `won't fix` 理由正式 dismiss，非静默放置。

完整时间线 + 修复细节见 `docs/POST_V0.4_TODO.md` 顶部 handoff note + § item 7。

**✅ README/MCP/ROADMAP 陈旧内容审计 + 修复，两轮 session 都做完了（2026-08-02）**：第一轮 5 项机械修复（ROADMAP.md 同步、MCP 元数据补 `ml` preset、Codex 补进全仓库、README 清理老版本号、plugin 目录问题 WebSearch 查清）。第二轮：**pyobfus-mcp 0.3.2 已发布**（PyPI + MCP Registry 均确认 isLatest，`mcp-publisher` 已跑）；plugin marketplace 提交流程查清 + 本地 `claude plugin validate` 已通过（实际提交需 user 自己登录网页操作，Claude Code 做不到）；Pro Edition 定位已讨论，user 认可方向。

**✅ Plugin marketplace 提交已完成（2026-08-02）**：Console 表单提交成功，显示"Plugin submitted for review"——状态是**待 Anthropic 审核**，不是已上线；`Link to plugin` 字段一度报 `must not contain spaces or control characters`（复制粘贴带入隐藏字符，手动重新输入后解决）。后续查审核结果看 `github.com/anthropics/claude-plugins-community`（审核通过后隔夜同步）或 Console 里的"View submissions"。

**✅ 2026-08-04 找到确切查询入口 + 状态确认**：权威地址是 **`https://platform.claude.com/plugins/submissions`**（Claude Console → Plugin submissions，需登录 user 自己的 Console 账号 `Rong / Shanghai Nirong Technology Co., Ltd.`）。页面显示 pyobfus 状态仍是 **"Submitted and pending review"**（提交于 2 天前，与 08-02 提交时间吻合，尚无 approve/reject 结论）。顺带核实了那个"protected_project"笔误确实还留在已提交的描述文案里（"One-call protected_project workflow..."一句）——继续维持"机会性修复"处置，不主动改，除非 Anthropic 跟进要求补充信息。公开旁证渠道（`claude-plugins-community` 仓库 `.claude-plugin/marketplace.json`，2298 个插件里搜 `pyobfus`）2026-08-04 同步核实：尚未出现，与 Console 状态一致。

**✅ 2026-08-09 再次手动确认 Claude plugin submission 状态**：user 打开 `https://platform.claude.com/plugins/submissions`，页面仍显示 `Plugin submissions` → `pyobfus` → **"Submitted and pending review"**，日期 **Aug 2**，没有 approve/reject/补充信息。提交描述仍显示 `"One-call protected_project workflow"` 这个 typo（正确工具名是 `protect_project`），继续维持既定处置：不为 typo 单独重提，除非 Anthropic 要求修改或给出编辑/重提路径。

**同轮外部复查（2026-08-09）**：公开 `claude-plugins-community` marketplace 仍无 `pyobfus`/`protect_project` 命中；GitHub open issue/PR 仍为空；最近 `main` CI + CodeQL（commit `911ce27`）均为 success；Glama public API 仍返回 `tools: []`，所以 Glama Discord `#support` 报告仍是当前外部 blocker。pypistats 快照：pyobfus 日/周/月 **34 / 1,093 / 1,871**；pyobfus-mcp **9 / 462 / 601**，day 继续从 08-06 发布批次噪音里回落。

**✅ 2026-08-09 post-release review 已完成并写入 `docs/ROADMAP.md`**：按用户定下的四项节奏复查了下载趋势、GitHub/CI/外部分发状态、PyArmor/Nuitka/VS Code Marketplace/PyPI 竞品现状，并回头审视已发布设计。结论：暂不抢开大功能；Glama public API 和 Claude plugin review 是外部 blocker；下一步优先等/跟 Glama `#support`、记录 Marketplace 安装信号，再考虑小范围 `--output-pyc` feasibility 或 VS Code trace/config workflow polish。顺手修了 review 发现的文档漂移：`docs/VSCODE_EXTENSION_PLAN.md` 顶部已从“M3 held”改为“v0.3.0 published”，`docs/COMPARISON.md` 的 Nuitka traceback 链接已更新到当前官方路径。

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
- ⏭️ **更后续**：旧的 P2-13/P2-22 等历史候选已经被 2026-08-14 规划刷新吸收；当前完整优先级看 `docs/CURRENT_PLAN_ZH.md`。Launch wave 已收工转被动监测(+7d/+30d checkpoint,不主动推)。IP 商业化迁移(个人→旎嵘科技)排在更后面。

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

**✅ 2026-08-09 — Glama Discord 频道纠正并已补发到正确位置**：user 发现 08-08 两条 Glama bug report 实际发在 **Model Context Protocol** Discord server 的 `#general`，不是 Glama 自己的 Discord；那里是协议/生态讨论频道，不是 Glama 支持入口。user 随后进入单独的 **Glama** Discord server，并把精简版报告发到 `#support`（更合适：该频道已有 Docker base-image timeout、admin UI、public API stale 等同类问题）。报告内容点名 server `zhurong2020/pyobfus`、public API 仍 `tools: []`、build `019fe034-7da2-73ef-8b02-b279c9ae4b68` 成功且 Glama 自己的 `initialize -> ListToolsRequest` 拿到 8 tools，结论是 successful introspection 未传播到 public directory API。下次 cold-start 优先查 **Glama Discord `#support`** 有没有 Frank/Glama team 回复，同时继续 `curl https://glama.ai/api/mcp/v1/servers/zhurong2020/pyobfus` 复查；MCP Discord 那两条不用删除，视为错频道的旁路备份。

**📅 周期性发布后复盘节奏（user 2026-08-08 定下的标准做法）**：不要只在发布当天查一次下载量就算完——每积累约 3-5 个版本发布后（或跨度 1-2 周，取决于实际发布节奏；不是每次 session 都做，太频繁会把发布日噪音当趋势），做一轮**四件事一起做**：① 下载量趋势（pypistats/pepy，看 week/month 别只看 day）② 排查可能出现的新问题（GitHub issues/PR、CI、Glama/plugin marketplace 等外部平台状态）③ 重新对比同类产品（PyArmor/Nuitka/VS Code marketplace 等，重新搜索确认现状，别复用上次扫描结论）④ **复盘并完善"原来的设计"本身，不只是找下一个新功能**——回头看已实现机制是否有可改进点，这条最容易被"下一个功能是什么"的默认思维忽略掉。结果记入 `docs/ROADMAP.md` 带日期小节。完整 rationale 见 memory `feedback_periodic_release_review_cadence`。

**Cold-start 资料定位**（按读取优先级）：

| 优先级 | 文件 | 用途 |
|---|---|---|
| 1 | `~/projects/pyobfus-legal/patent/SESSION_LOG_20260617.md`（最新）+ `SESSION_LOG_20260611.md` | 最新时间线 + 初审合格 + next action（off-repo · 完整 narrative）|
| 2 | `~/.claude/projects/-mnt-c-onedrive-msft-OneDrive---MSFT-rong-3-job-program-pyobfus/memory/patent_correction_notice_2026-06-01.md` | 初审合格结论 + 补正根因/历史 + 受理/费用状态 |
| 3 | `~/projects/pyobfus-legal/patent/08_提交记录/` | 五份官方通知书正本（受理 / 收费减缴 / 电子回执 / 补正 / **初步审查合格**）|
| 4 | `docs/CURRENT_PLAN_ZH.md` + archived `docs/V0.5_RELEASE_PLAN.md` / `docs/POST_V0.4_TODO.md` § P1 | 当前计划 + v0.5/patent 历史状态块 |

**跨项目联动**：cac-plus-ip 与本 pyobfus 共享同一个人申请人 + 同一 2026 年度费减备案；`~/projects/cac-plus-ip/CLAUDE.md` 含完整跨项目索引。详见 memory `ip_workflow_cross_project.md`。

**Path C 红线（gate 解除后的残留约束）**：① `pyobfus-legal/` **永不入 git**（含 PII，永久有效）；② v0.5 Pro 机制的公开发布**走 Phase 5 受控合并**（一次性、刻意公开），合并前公开 commit 仍不得泄露未发布机制——但 gate 本身（"补正办结前不得公开 v0.5 机制"）**已于 2026-06-17 解除**。完整命名清单见 memory `pro_disclosure_finding_2026-05-09.md` + `pyobfus_patent_strategy.md`。

## 项目概述

- **定位**: Python 代码混淆器 (开源 + 商业双许可)
- **技术栈**: Python 3.9-3.14, AST, setuptools
- **PyPI 主包**: https://pypi.org/project/pyobfus/ (**latest v0.5.19，2026-08-30 发布**；完整版本历史见 `CHANGELOG.md`)
- **VS Code 插件**: https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus (**latest v0.4.1，2026-08-22 发布**（tag+GitHub Release+Marketplace 手工上传均已完成，`curl` 核实公开 listing 已返回 `"version":"0.4.1"`）；publisher `zhurong2020`；独立版本节奏，见 `vscode-extension/CHANGELOG.md`)
- **PyPI MCP 包**: https://pypi.org/project/pyobfus-mcp/ (**latest v0.3.9，2026-08-28 发布**；8 tools: 6 community + 2 pro_funnel · dep `pyobfus>=0.5.18` · `uvx pyobfus-mcp` 零安装；完整版本历史见 `pyobfus_mcp/CHANGELOG.md`)
- **MCP Registry**: `io.github.zhurong2020/pyobfus-mcp` (active, isLatest=true · **0.3.9**，2026-08-28 发布，`registry.modelcontextprotocol.io` 直查核实)
- **Smithery (Skill)**: https://smithery.ai/skills/zhurong2020/pyobfus-protect (2026-06-22 上线 · 本地工具走 Skill 渠道非 MCP 渠道) · **mcp.so**: 已收录
- **Glama Listing**: https://glama.ai/mcp/servers/zhurong2020/pyobfus (Quality A) — admin Build steps 已自动更新到 `pyobfus-mcp==0.3.8`；2026-08-24 测试 `01a033e4-3336-7e7b-9792-0d7e056d2dba` success（12.1s），实时枚举完整 8 工具。公开 API 仍 `tools: []`，属于 Glama 目录同步漂移，非包、Docker 或 MCP introspection 故障。后续只查公开 API/Discord 回复；历史排障见 memory `glama_introspection_dockerfile_pin_2026-06-05`、`glama_zero_tools_repro_2026-08-07`，最新证据见 `docs/EXTERNAL_CHANNEL_SNAPSHOT_2026-08-24.md`。
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
├── tests/             # 1208 passed + 1 skipped (0.5.19 发布前验证)
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
3. **同一提交里顺手更新 `README.md` 的"What's new in vX.Y.Z"横幅**（打 tag
   之前）——PyPI 包一旦发布不可变，README 快照就是发布那一刻的 `main`；
   若这句更新拖到打 tag 之后的单独 docs-sync 提交里，就会正好被已发布的
   包错过，PyPI 页面 description 从此永久落后一个版本，只能等下次自然
   发版才带上（2026-08-17 v0.5.14 实际踩过这个坑，处置见
   `docs/CURRENT_PLAN_ZH.md` 当前状态块）。
4. `python -m build && twine upload dist/*`（或走 `git tag vX.Y.Z && git push --tags`
   触发 `.github/workflows/release.yml` 的 OIDC 自动发布，是当前实际使用的路径）

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
| `pyobfus-legal/` | cardiac-research.code-workspace（symlink to OneDrive 同级目录）| pyobfus 软著 + 专利申报材料的物理仓库（**不在 git repo 内** · 含 PII，不公开）。包含 `software_copyright/` (V0.4.0 软著已 2026-05-09 提交 CCPC) 和未来的 `patent/` (v0.5 专利申请目录)。物理路径：`/mnt/c/onedrive/msft/OneDrive - MSFT/rong/3-job/program/pyobfus-legal/`，工作区入口：`~/projects/pyobfus-legal/`（symlink） |
| `cac-plus-ip/` | cardiac-research.code-workspace（同 workspace 内）| **同申请人的并行 IP 工作流**。CAC Plus 医学 AI 项目的 3 件中国发明专利 + 2 件软著申请仓库。**与 pyobfus 内容无关、但工作流共享**：同一个 CCPC 账号 / 同一个 CPC 客户端 USB Key / 同一个 85% 个人申请减免资格 / 同一套 CNIPA 官方申请模板（位于 `cac-plus-ip/02_china_发明专利/_templates_CNIPA/`，pyobfus v0.5 专利申请直接复用，不重复下载）|
