# 路线执行跟踪 — 2026-11-16 起

状态：**维护者 2026-11-16 批准按顺序推进 T0–T4**；实现交无头 Codex，Claude 审核、
独立复跑检查并提交。每个 PR 的合并、任何发版、Worker 部署和许可签发仍是各自独立
的 gate，须维护者逐次明确批准。本文件是本轮唯一进度台账：每项完成后在此更新状态与
证据链接，再从 [TODO](TODO.md) 移除。

依据：[11-15 竞品与路线复核](COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md)。该复核的
0–4 周 P0（公开交付参考应用、Windows Nuitka 单格验收、一个冻结格式的
`--check-delivery`）与“下一次自然 Core 发版”已在 11-15 完成（Core 0.15.0）；
Nuitka 验收结果为 partial（D9 unknown、Pro 阶段 C blocked），见
[参考应用验收](DELIVERY_REFERENCE_APP_ACCEPTANCE_2026-11-15.md)。

## 规则

- 同一时间只推进一个产品项；每项写明用户／证据、验收和停止条件。
- 无缺陷不发版；12 月中旬前不计划 Core 发版。
- 需求门槛项（资源 key provider、L3 方法／嵌套、3.15t、Nuitka 载荷解析、第二种冻结
  格式）在 T4 定义的触发条件满足前不排期。
- 客户、付款与支持细节只进私有 `docs/internal/`。

## 任务台账

| ID | 任务 | 窗口 | 状态 | 验收 / 停止条件 | 证据 |
|---|---|---|---|---|---|
| T0 | 11-16 周检；推送 11-16 收尾文档 | 11-16 | ✅ 完成 | 只记录，不改功能 | 见下方 T0 记录；#243 已合并 `062579f` |
| T1 | ROADMAP 重定基线（五类 6–12 个月表，历史原样归档）；TODO 清除已完成层，维护者清单拆分 | 11-16 | ✅ 完成 | 链接全部可解析；版本正确；ROADMAP／TODO 行数明显下降；历史原样保存 | [#245](https://github.com/zhurong2020/pyobfus/pull/245) 已合并 `8969a05`：ROADMAP 734→约 140 行、TODO 702→191 行；历史逐字节保存（已 `cmp` 核对） |
| T2 | 刷新 `COMPARISON.md` 快照（按 11-15 核对的版本／价格，补 PyLocket） | 11-16 | ✅ 完成 | 每条有官方链接与核对日期；对外发布前重查；不发版 | [#246](https://github.com/zhurong2020/pyobfus/pull/246) 已合并 `6a0aeef`：版本与价格 11-16 在线复核；PyLocket 许可失效表述按定价页与计费条款并列 |
| T3 | 参考应用 PyInstaller onedir/onefile + Core 0.15.0 CArchive 交付检查；修 Windows workflow 旧 v4.6.2 注释 | 11-23～29 | ✅ 完成 | 顶层成员实际被检查；PYZ 明确 uninspected；不得出现假 clean；发现缺陷才改产品代码 | [#244](https://github.com/zhurong2020/pyobfus/pull/244) 已合并 `4c00a7c`，CI 42 项通过（packaging lane 用 PyInstaller 6.22.3）：onefile 29/21/8 → warn；三种植入均 fail／exit 1；traceback 4 帧全还原；本地复跑 9 passed／3 skipped |
| T3b | 目录扫描对 onedir 内的冻结可执行文件执行 CArchive 检查（T3 发现） | 11-16 | ✅ 完成（未发版） | 目录扫描与单文件路径给出相同的逐文件检查结果；沿用现有边界；unknown 仍为 unknown；不执行载荷 | [#247](https://github.com/zhurong2020/pyobfus/pull/247) 已合并 `397584b`：参考应用 onedir 目录检查 inspected=1；另修可执行成员「输出与输入一致不算泄漏」误报；Windows CRLF 测试问题已修 |
| T4 | 需求入口：交付受阻／冻结格式 issue 模板、参考应用反馈入口、3 个指标与 P1/P2 触发门槛 | 11-16 | ✅ 完成 | 门槛写入 ROADMAP 表 | [#245](https://github.com/zhurong2020/pyobfus/pull/245) 已合并：issue 模板、`delivery-blocker` 标签已建、门槛与 90 天停止规则 |
| T5 | Pro 阶段 C：补 L3 冻结交付验证（改用纯本地试用，未签发许可） | 11-16 | ✅ 完成（未发版） | 不碰真实密钥；隔离 HOME；缺失／错误密钥失败关闭 | [#248](https://github.com/zhurong2020/pyobfus/pull/248) 已合并 `39503ac`：onefile／onedir 通过；发现并修复冻结目录误报 `l3_build_mismatch` → medium `l3_unverified_frozen`；packaging lane 改为普通安装 runtime |
| T6 | 12 月第一周搜索／AI 可见性；约 12-04 Core 0.12.0 T+30d（之后逐版本观察并入周检） | 12-01～05 | ⏳ 定时 | — | — |
| T7 | 以“自管、可验证交付”整理 Pro 购买路径 | 11-16 | ✅ 完成 | 每条主张有可复现证据；不改价格／条款；落地页合并即上线，合并前维护者审最终文案 | [#250](https://github.com/zhurong2020/pyobfus/pull/250) 已合并 `b250c1e`：维护者审定文案（更积极、四类能力全站统一、入口句精简）；中英文落地页线上已核 |
| T8 | pyobfus 及相关项目文档审计（多个版本后的一致性复核） | 11-16 | ✅ 完成（#252 待通知后合并） | 见下方 T8 方案 | 约 96 条发现；修复：#251 隐私、#253 用户文档、#254 内部入口、Action #5、workspace-meta `0346b80`；法律草稿 #252 与 Worker 数据保留 #255 见下方隐私政策更新安排 |

## 隐私政策更新安排（2026-11-16 维护者决定）

审计发现隐私政策／条款与实际行为有出入，维护者决定按隐私最佳实践处理（透明告知、最小化、
存储期限、如实披露服务商）。因当天已向客户发过升级通知，不在同日再发第二封。顺序如下，
每一步都需维护者单独批准：

1. ✅ 2026-11-16：[#255](https://github.com/zhurong2020/pyobfus/pull/255) 合并 `4fcb4bb` 并经维护者批准部署为
   Worker **`39d425d7`**（回滚 `209eb969`，部署前 KV 全量导出已做）。定时清扫已登记（周一 03:17 UTC，
   首次 11-23）。线上验证：端点监控健康；自有许可签名 CI 准入成功且产物可运行；伪造许可被拒且无产物；
   自有记录结构完好，90 天内的审计记录按规则保留。
2. 约 11-23 周检前后：维护者审定 [#252](https://github.com/zhurong2020/pyobfus/pull/252) 定稿与客户通知稿
   （私有）；原拟确认统一 30 天删除承诺，11-25 已决定不新增该保证，改按适用法律处理。
   生效日期仍定为通知日后 30 天；既有承诺能否变更不得仅凭通知期推定。
3. 通知当天发出通知并合并 #252（填入正式生效日期，去掉草稿标记）。

### 2026-11-25 接续验收

- Worker 生产只读快照与部署前及清扫前备份比较，许可与设备槽位一致，CI 遥测符合最小化。
  无到期审计记录残留；实际超期删除与 trial 转换缺线上样本，只由离线回归覆盖。
- 首次 Cron 的确切执行时间待 Cloudflare Scheduled Event／日志证明，不能仅凭快照关闭该项。
- 每日 KV 导出网络超时已修复专用代理配置并完成无交互代理环境导出；导出器补 trial 去重记录兼容。
  下一次定时运行及自然备份包含性仍待观察。私有材料在 `docs/internal/retention-acceptance-2026-11-25/`。
- #252 与通知本地审定稿已补实际部署日；维护者确认避免额外自愿承诺，删除请求改按适用法律处理，
  同步修订固定响应／泄露通知时限、第三方与保护效果边界。通知日期及最终公开文稿仍待审定；未发送、未合并。
  详见 [11-25 收尾](SESSION_CLOSEOUT_2026-11-25.md)。

### 2026-11-25 文稿复核交接

- 11-25 晚独立复核已完成（Claude），本地三份稿已修正事实与透明度问题；结论 `docs/internal/retention-acceptance-2026-11-25/CLAUDE_REVIEW_2026-11-25.md`。
  后续为维护者决定 → 定通知日 → 同步 #252 → 发信与合并。
- 维护者要求保存原则、调研与修订证据，供另一 LLM 独立复核。长期规范为
  [对外承诺起草原则](PUBLIC_COMMITMENTS_POLICY.md)；完整私有交接入口为
  `docs/internal/retention-acceptance-2026-11-25/LLM_REVIEW_HANDOFF.md`。
- 已区分公开法律原文、远端 #252 旧稿、本地修订及修订前副本，附差异、版本与哈希。
  原则已确定，文稿仍待独立复核与最终审定；未发信、未更新远端 PR、未合并或发布。

## T8 文档审计方案（2026-11-16 排期）

维护者在连续多个版本（0.12.0–0.15.0 及未发版改动）后要求审计 pyobfus 与所有相关项目的文档。
沿用 [08-02](DOC_SYNC_AUDIT_2026-08-02.md) 与 [10-02 跨仓](CROSS_REPO_DOC_SYNC_AUDIT_2026-10-02.md)
审计的方法，先出报告再分仓修复；T7 合并后开始，避免与其文案改动冲突。

1. **事实基线**（Claude）：一页当前事实表——各包版本、Glama 渠道、Worker 版本、
   `--check-delivery` 当前与未发版行为、版别边界、支持矩阵、关键日期。所有审计以此对照。
2. **只读审计**（无头 Codex，按范围拆分并行，只写报告不改文件）：
   (a) 面向用户：README／README.zh-CN、文档站导航页与指南、`llms*.txt`、skills、
   集成模板、`ai-catalog.json`、落地页中英文；(b) 子包：`pyobfus_mcp`、`pyobfus_runtime`、
   `vscode-extension` 的 README／CHANGELOG；(c) 内部入口：CLAUDE.md／AGENTS.md「Where to look
   next」堆积、CURRENT_PLAN_ZH（2662 行）、TODO／ROADMAP、SESSION_CLOSEOUT 与 COLD_START 系列；
   (d) `pyobfus-action` 仓；(e) 工作区索引：`workspace-meta` 中涉及 pyobfus 的 6 份文件。
   每条发现写明文件:行、与事实表的差异、建议动作（改／删／折叠／保留）。
3. **复核与分级**（Claude）：抽查每份报告，按「事实错误／过期版本与死链／结构臃肿／可延后」
   分级；CLAUDE.md、AGENTS.md 与工作区索引按工作区「指令＋指针，不装历史」规则瘦身，
   历史原样归档。
4. **修复**：每个仓单独 PR（Codex 实现、Claude 审核）；外部渠道（Marketplace、Open VSX、
   Glama、mcp.so、PyPI 页面）只出差异清单，由维护者手动处理或随下次发版带出。
5. **不送外部模型**：`pyobfus-legal`（含个人信息，非 git）只由 Claude 只读核对版本／
   日期引用；`pyobfus-pro-dev`（专利证据库，已归档只读）不在修复范围；私有 memory 由
   Claude 自行整理。

验收：事实表中每项在所有公开入口一致；`scripts/check.sh` 与各仓 CI 通过；新增链接全部可解析；
CLAUDE.md／AGENTS.md 体积明显下降且无悬空指针；外部渠道差异清单交维护者。

## T3 新发现（2026-11-16）

对 onedir 输出**目录**做 `--check-delivery` 时，目录扫描不解析其中 bootloader 的 CArchive
（`found=1, inspected=0`，如实报 warn，不是假 clean）；直接检查该可执行文件则会解析。已登记为
ROADMAP Delivery 表的 Community 候选；**11-16 维护者批准实施**（任务 T3b，见下）。

## T0 记录（2026-11-16）

- CI：main 最近 CI／CodeQL／Dogfood／Draft PDF／IndexNow 全部成功；11-15 `a240609`
  的 3.15 集成红灯已由 #235 修复。License Endpoint Monitor 近 5 次成功。无开放 issue／PR。
- 下载（`scripts/download_snapshot.py`，数据至 11-15）：Core 近 7 天 803、安静日中位数 52；
  30 天 4318、安静日中位数 78；MCP 近 7 天安静日中位数 7。11-15 发版日 304 为尖峰，不计增长。
  Marketplace installs 18，Open VSX 886，Action 归因 0。
- 邮件：未发现等待回复的客户来信；Glama 通知为渠道 0.14.1 构建／发布与临时托管实例到期
  提醒（与渠道 release 分开判断）。通知后续只记私有支持日志。

## T8 钩子兼容后续（2026-11-17）

- 分支 `fix/hooks-bash32`：四处 `mapfile` 改为保留空白和反斜线的读取循环；
  macOS 钩子测试明确使用 `/bin/bash`，Windows 仍跳过 POSIX shim。
- 已补空索引／干净内容回归，并修正测试 shim 对空索引的模拟；专项 43 passed。
- 验证：`scripts/check.sh` 通过；真实 GNU bash 3.2.57 与系统 bash 的专项测试均
  43 passed（临时构建于 `/tmp`，未修改系统 bash）。
- 独立测试根：Core 5200 passed / 56 skipped；MCP 167 passed；CLI 集成
  378 passed / 10 skipped；runtime 与基准测试通过。全部使用正常 HOME。
- 状态：[PR #258](https://github.com/zhurong2020/pyobfus/pull/258) 托管 CI 42 项全部通过，
  11-19 维护者批准后 squash 合并为 `a125825`。未发版、未部署。

## 周检记录（2026-11-19）

- 下载（`scripts/download_snapshot.py --days 14`，数据至 11-18）：Core 近 7 天 784、
  安静日中位数 46；30 天 4180、安静日中位数 59。11-15 发版日 304、次日 218 为尖峰，不计增长。
  MCP 近 7 天 65、中位数 4；runtime 数量主要来自本仓 CI，不作采用指标。
  Marketplace installs 19，Open VSX 894，Action 归因 0；GitHub 14 天访问 263／独立 160。
- 邮件（11-16 起）：未发现等待回复的客户来信。Glama 通知为 pyobfus-mcp 渠道 0.15.0
  构建成功／发布与临时托管实例到期；其余为已处理 PR 的 CI 通知。通知后续只记私有支持日志。
- 需求触发：无 `delivery-blocker` issue、无交付受阻支持请求，ROADMAP 需求门控项均未触发。
- 产品网站（维护者 11-19 按最佳实践决定）：不在 arong-vps／openclaw 自建；继续 GitHub Pages
  ＋ ReadTheDocs ＋ Cloudflare Worker。T6 后再判断是否启用独立域名（Cloudflare 指向现有 Pages，
  旧地址 301），条件与验收见 ROADMAP「Distribution」表。
