# pyobfus 当前计划

**当前状态（2026-11-16）**：Core 0.15.0 发布后收口完成；当天后续 T1–T5/T3b
已合并，产品修订仍为 **Unreleased**。本文件保留运维事实、开放决定与规则；
[路线执行台账](ROADMAP_EXECUTION_2026-11-16.md) 是唯一任务进度账，
[TODO](TODO.md) 管执行顺序，[维护者动作](MAINTAINER_ACTIONS.md) 管外部账号与等待。
[ROADMAP](ROADMAP.md) 是活跃的五类、6–12 个月路线图。
最新[会话收尾](SESSION_CLOSEOUT_2026-11-16.md)与[运维执行记录](EXECUTION_PROGRESS_2026-11-16.md)
是当天早段快照；其后的路线进度以台账为准，不能据旧交接重开已完成任务。

历史逐字节迁至 [CURRENT_PLAN_HISTORY_2026-11-16.md](CURRENT_PLAN_HISTORY_2026-11-16.md)；其中的旧版本、待办和授权不作为当前指令。

## 已发布基线与部署

| 组件 | 当前公开状态 | 证据 / 边界 |
|---|---|---|
| Core | **0.15.0**（2026-11-15） | [发布核验](CORE_0_15_0_RELEASE_2026-11-15.md)；Python 3.9–3.15；跨文件 L3 不支持 free-threaded 3.15t |
| MCP | **0.3.17**，九个工具（七 Community + 两个 tier/trial guidance） | [包元数据](../pyobfus_mcp/pyproject.toml)、[工具清单](../pyobfus_mcp/pyobfus_mcp/tool_manifest.json)；Python ≥3.10 |
| runtime / VS Code / Action | **0.1.1 / 0.4.3 / v1.1.0** | Action 移动 `v1` 指向 `3237e16`；各组件独立发布，不随 Core 自动升版 |
| Glama | 渠道 **0.14.1**；安装 Core **0.15.0** / MCP **0.3.17** | 渠道标签独立递增；构建、握手与九工具发现已核，不代表九工具逐项业务调用 |
| 许可 Worker | **`39d425d7`**（2026-11-16，#255 数据保留），回滚 **`209eb969`** | 生产签发 `ci-2026-11`；备用 `ci-2026-11b` 已由 Core 0.15.0 预分发信任，未配 Worker；每周一 03:17 UTC 清扫（设备审计记录 90 天、试用记录到期 180 天后转去重记录） |
| CITATION / Zenodo | **0.15.0**，2026-11-15，record **24248676** | [CITATION](../CITATION.cff)；concept DOI `10.5281/zenodo.20846053` |

Community 为 Apache-2.0，无文件／行数限制；Pro 为 **$45 USD 一次性**、终身更新、
最多三台设备、30 天退款、免注册五天试用（`pyobfus-trial start`）、邮件支持。
[edition 边界](EDITION_BOUNDARY_POLICY.md)不变：正确性、安全、兼容与基础本地验证／调试不收费。

## 当天路线进度与未发布边界

- **#243**：T0 运维收口；**#244**：T3 公开参考应用 PyInstaller onedir/onefile 验收及
  Windows workflow 注释修正；**#245**：T1 路线／TODO 重定基线与 T4 需求入口／门槛；
  **#246**：T2 竞品比较刷新；**#247**：T3b 目录内可执行文件检查；**#248**：T5 纯本地
  隔离试用的 Pro 阶段 C（未签发许可）；**#249**：进度台账收口。提交和验收见[台账](ROADMAP_EXECUTION_2026-11-16.md)。
- **已发布 0.15.0**：单个可执行文件的有界 PyInstaller CArchive 顶层成员检查；嵌入
  PYZ／marshalled code／未知成员明确 uninspected、warn，不得写成 clean；JSON 有
  `members_total` / `members_checked` / `unknown_members`；畸形／超限 exit 2，高风险 exit 1。
- **Unreleased / 下次自然版本**：目录扫描也检查其中顶层 PyInstaller 可执行文件，成员路径
  为 `<exe>!<member>`，聚合计数、最多 32 个 reader、共享预算；可执行成员的输出与输入
  字节相同不再误报泄漏；带 L3 build report 的冻结目录报 medium
  `delivery.l3_unverified_frozen`，保持 warn。见 [CHANGELOG Unreleased](../CHANGELOG.md#unreleased)。
- T5 的 Linux 本地试用证据不替代 Windows Pro 验收。Windows Nuitka 单格仍为
  D1–D8 pass、D9 unknown、总体 partial；不能声称干净目标机或更广平台矩阵已验证。
  参考应用与范围见 [验收记录](DELIVERY_REFERENCE_APP_ACCEPTANCE_2026-11-15.md)及
  [示例](../examples/delivery_reference/README.md)。

## 接下来与开放决定

- **T7 已完成**（#250，购买路径文案经维护者审定上线）。接下来：**隐私政策更新**（#255 Worker 数据保留
  → 部署 → 约 11-23 审定 #252 与客户通知 → 通知日合并 #252，生效日为通知后 30 天，见
  [台账](ROADMAP_EXECUTION_2026-11-16.md)）→ **T6 十二月观察**。具体队列见 [TODO 当前执行顺序](TODO.md#当前执行顺序2026-11-16-收口)。
  T8 审计本轮仅处理授权范围，不能据此声称全仓审计完成。
- 同时只推进一个产品项；无缺陷不发版，12 月中旬前不计划 Core 发版。
  资源 key provider、L3 方法／嵌套、3.15t、Nuitka 载荷解析与第二冻结格式仍按
  [需求门槛](ROADMAP.md#demand-triggers)触发；参数改名、复杂 import／H B2/B3、mapping 自动选择、
  私有下游 Y-1 与更广打包组合按 [增强路线 gate](TODO.md#增强路线复核2026-10-12--实施前-gate)另定范围。
- **F2 工作站／离线迁移**的兼容与验收仍待决定，必须保留终身授权；CI 首阶段已发布，不能重列待实现。
  **F3 AES-256-GCM** 需新格式与兼容测试，另立范围；**Pro/runtime 专利条款**仍待专业审阅。
  计划内签发 key 切换须信任版本发布满 **180 天**（最早约 **2027-05-14**），且提前
  **60 天**正式通知最低版本与日期；既有升级说明不替代该通知。
- 保留 Python 3.9：Ubuntu 3.9 当前固定 `ubuntu-24.04`，退役前另安排 runner／容器。
  CLI `--check` 默认联网、MCP 默认不查，是否改默认离线待复审；改变须发版并同步网络文档。
- `preserved.*` reason codes、Y-3 vault 覆盖等真实下游触发；DCO `LE-01.01` 等外部协作者；
  OSPS L3 SCA/SAST 阈值政策仍待定。工具型 Agent 还原实验继续暂停，不自动恢复。
- `dependency_advisory` 暂留现有检查内部，观察真实使用／独立需求并在触发竞品复核时看同类工具；
  独立包、可疑度／缓存／私有 index 等扩展须有差异与需求。delivery bundle、mapping 内置加密、
  团队许可 UX 均等重复需求；不把 mapping 与交付代码自动打包，不加任意执行验证命令。
- **Affiliate** 仅设计、未生效；实现前须确认双幂等、退款／争议、隐私与财税，
  详见 [未授权 pilot](TODO.md#affiliate-pilot未授权实现部署)。视频原创保护只授权记录，未授权实现／采购／发布。
  品牌防护商标仍待决定；不为抢 GitHub 用户名注册商标。
- VS Code／runtime 自身下次发布带入对应 README／网络行为修订；托管采用页须核对部署；
  不为文案单独发 Core/MCP。旧 Action README 事项已由 Action PR #2（`24f3328`）合并关闭；
  维护者清单中的旧分支状态核对项不再是开放义务。

## 仍生效的运维事实与周期义务

- **发布收口**：CITATION 同步与升级通知已完成，不重复通知；后续支持只进主 checkout 的
  私有 `docs/internal/CUSTOMER_SUPPORT_LOG.md`。当前源码仓为 Core 与独立 Action；
  法务目录是真实私有目录，专利证据库只读归档。OneDrive 指定旧父路径已不存在，旧 filter-repo
  备份已删除，不恢复旧删除待办；资产边界见 [资产审计](LOCAL_ASSET_AUDIT_2026-11-15.md)。
- **渠道**：Glama 更新须手动改 Build steps 并点「Build & Release」，只点「Build」不发布；
  checkout 与 PyPI 安装边界见 [渠道核验](CORE_012_CHANNEL_FOLLOWUP_2026-11-04.md)。
  Smithery 已退役，不再投递；mcp.so 与官方 MCP Registry 已收录。Claude plugin 仍被孤立仓库锁阻塞，
  等解除，不换路径绕过或重复提交；账号动作见 [维护者清单](MAINTAINER_ACTIONS.md)。
- **外部开放事项**：MCP Trust Registry 发布仍需维护者账号／token；Canopii 等上游，唯一一次 follow-up
  已做，不反复催；重扫核包边界、当前九工具与 provenance，不为总分／徽章改产品。
  AlternativeTo 待账号核验；Open VSX namespace 验证可选。mcp.so 旧比较描述待维护者核可否修改。
  MCPB、Product Hunt、skill 投递、GEO 环境补测与小型渠道试验按 [分发队列](TODO.md#分发与需求验证)，
  没有可归因安装前不新增渠道；Discussions 表单仍待维护者，等真实问题再投入。
- **搜索**：GSC 规范 `/pyobfus/zh-cn/` 已收录；sitemap 仍显示 11-12 的旧“无法读取”，
  不删除重提，周检观察刷新。Bing IndexNow 后台未显示记录但 workflow 成功，不能称零提交或失败。
  保留 `docs/google03878b382b498ff9.html` 和 IndexNow key 文件。
- **每周一**只读检查 CI／依赖、最新发布反馈、收件箱／目录锁、安静日下载、Marketplace、
  trial、GitHub 来源、Action 归因、Dogfood、KV 导出和自然备份新鲜度。KV 定期导出已建立，
  不再是未闭合缺口；后续自然备份仍需抽核新证据和私有记录包含性。整体 WSL 静态加密另定跨项目策略。
  查进度同时给下载脚本与收件箱状态；本次文档修订未重跑在线巡检。
- **T6**：12 月第一周搜索／AI 复盘，约 **12-04** Core 0.12.0 T+30d；此后逐版本观察并入周检。
  每月底复盘下载、排障、竞品和已有设计；不恢复静默期。下载尖峰不是增长，runtime 下载含本仓 CI，
  Open VSX 下载与 Marketplace 安装不相加。完整方法与停止条件见 [周期性](TODO.md#周期性)。
- **内容**：DEV 双周、中文 WP 月度；旧排期须核实际发布状态，不补造完成。
  第 7 篇先于第 5 篇，12 月第 5／3 篇及 WP 月度篇，第 6 篇顺延一月；渠道观察和停止条件见
  [内容节奏](TODO.md#内容节奏与待选题)。草稿／原始数据只放私有忽略目录，确认自然备份包含。
  多工具 benchmark／扩展 LLM 实验／论文按原 60–90 天后再议 gate，依赖真实应用数据。
- **商业运维**：下一笔自然购买只读核新发号与资料；延迟到账付款方式启用前核异步成功订阅；
  Alipay 只在真正 Enabled 后恢复文案。账号与支持细节仅私有，规则见 [维护者动作](MAINTAINER_ACTIONS.md)。

## 长期规则与能力边界

- 实施、每个 PR 合并、发版、Worker 部署和许可签发均为独立 gate，按本次维护者明确授权执行。
  文档计划本身不授权这些动作。
- 开发／测试／构建只在 WSL `~/projects/`；用仓库 `venv/`。保留 [AGENTS.md](../AGENTS.md) 的全套独立测试根、
  `scripts/check.sh`、真实 HOME 隔离、托管 MCP SDK／Python 3.15 与最终发布 21 格验证要求。
- 专利申请机制只在 Pro/runtime，永不进入 Apache-2.0 核心；法务 PII 永不入 git；
  对外只能写 **patent pending (CN 202610712171X, not yet granted)**。
  v0.5 受控公开已完成，Core 0.13.0 已发申请标识，不能重列待发布。
- Agent 可见行为变化同 PR 同步 llms 双镜像、集成模板、skills 与 AI catalog；README 文字打 tag 前更新，
  runtime 源码变动先升版先发布，Zenodo 发布后核 record；细则见 [发布 gate](TODO.md#发布兼容与信任-gate)。
- self-dogfooding 只读观察／canary／wheel，独立验证产物，不替换公开包源码；Dogfood 不自动升必需 gate。
  公开记录只写抽象工程事实，客户／付款／支持信息只私有。
- `--dry-run --json` 的 `plan` 对象自 0.5.19 提供，无 `--plan`；计划不可直接 apply。
  配置感知检查与 MCP 集成已发布，不恢复旧实施清单；静态检查不承诺运行兼容。
- 不追新 VM／编译器后端、托管 remote MCP／云混淆／商城／自动更新、anti-VM／AV bypass 或强 anti-debug 竞赛；
  其余明确延后项和反馈触发条件见 [TODO](TODO.md#已研究明确延后不做)。
