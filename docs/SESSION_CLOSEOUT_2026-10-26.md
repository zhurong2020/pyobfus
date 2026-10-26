# 2026-10-26 session 收尾：MCP SDK 2.x 生产支持

冷启动顺序：本页 → [当前计划](CURRENT_PLAN_ZH.md) → [TODO](TODO.md)。
10-25 的 [交接](SESSION_CLOSEOUT_2026-10-25.md) 是发版前快照，其中
“MCP 0.3.15 为最新”和“生产 SDK 上限未改”已被本页取代。

## 已完成

| 范围 | 结果 |
|---|---|
| 生产依赖与 CI | PR #134 → main `18b346b`；MCP SDK 范围为 `mcp>=1.27.0,<3.0.0`，兼容矩阵覆盖 1.27.0、2.0.0 与最新 2.x |
| MCP 发版 | PR #135 → main `04985d4`；`mcp-v0.3.16` 已通过 Trusted Publishing 发布 PyPI wheel/sdist；Core 0.9.1、runtime 0.1.1 不变 |
| 发布验证 | PyPI 两个产物 PEP 740 证明均验证通过；Python 3.10/3.15 全新安装解析 SDK 2.3.0，`pip check`、153 项测试及 legacy/auto 模式各九工具真实调用通过 |
| 分发 | [GitHub Release](https://github.com/zhurong2020/pyobfus/releases/tag/mcp-v0.3.16) 已创建；官方 MCP Registry 0.3.16 为 `active`、`isLatest=true` |
| Glama | 维护者提供后台测试 `01a17790-1545-7aef-8966-dcbb65b5c39b`：Build steps 固定 MCP 0.3.16 / Core 0.9.1，构建 `success`，握手 0.3.16，九工具列出；PR #137 → main `9d71b64` 已记录并关闭 Glama 待办 |

Glama 测试证明镜像安装、服务启动和工具发现，不代表九个工具已在
Glama 镜像里逐个调用。构建规范写 Python 3.12，日志中 uv 安装到
`/usr` Python 3.13.5；仓库检出 `7cf8302`、`pinnedCommit: null`，
服务本身来自固定版本的 PyPI 包。细节见
[MCP 发布验证](MCP_SDK_2X_RELEASE_PREP_2026-10-26.md)和
[分发渠道](DISTRIBUTION_CHANNELS.md)。

## 当前边界和下一步

公开版本为 Core **0.9.1** / MCP **0.3.16** / runtime **0.1.1**。
多模块 L3 A–E 已合并但仍是未发布预览；MCP 0.3.16 的 SDK 2.x
支持不等于 Core L3 已发版。继续按 [TODO](TODO.md) 的当前顺序处理
Core 下一次发布决定、备份巡检和 DEV 私有草稿预览；不要重复 Glama
0.3.16 构建或把历史快照当成当前待办。

本轮发布和 Glama 文档收尾 PR #136 / #137 已合并。文档同步工作
按发布状态、冷启动交接分类提交；文档改动不触发新的包发布。
