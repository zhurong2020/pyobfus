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
| T7 | 以“自管、可验证交付”整理 Pro 购买路径 | 11-16 起 | 📝 范围提案待维护者确认 | 每条主张有可复现证据；不改价格／条款；落地页合并即上线，合并前维护者审最终文案 | 提案在私有 `docs/internal/codex-2026-11-16/` |

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
