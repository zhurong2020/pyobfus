# 2026-10-27 session 收尾：Core 0.10.0、Glama 与文档同步

冷启动顺序：本页 → [当前计划](CURRENT_PLAN_ZH.md) → [TODO](TODO.md) →
[分发渠道](DISTRIBUTION_CHANNELS.md)。10-26 的
[MCP 交接](SESSION_CLOSEOUT_2026-10-26.md)是 Core 发版前快照，
其中“Core 0.9.1”和“L3 未发布”不再是当前状态。

## 已完成

| 范围 | 核实结果 |
|---|---|
| Core 发版 | PR #139 合并为 `886b8c9`；合并后 CI 39 项、CodeQL、Packaging 通过；`v0.10.0` 的 OIDC 发布工作流成功。PyPI wheel/sdist 的 PEP 740、SHA-256 与 Integrity API 均核实；Python 3.10/3.15 全新安装及生成代码运行通过。GitHub Release 和 Zenodo 版本归档 `10.5281/zenodo.23687523` 已核；`CITATION.cff` 已同步。 |
| 文档巡检 | README 中英、MCP/runtime、VS Code、用户指南、支持矩阵、Agent 入口及发行记录已复核；PR #139、#140 合并。MCP `0.3.16`、runtime `0.1.1`、VS Code `0.4.3`、Action `v1.0.1` 没有随 Core 重新发布。 |
| 下载与邮件 | 10-27 18:36（北京时间）运行下载快照、查项目相关 Gmail；PyPI 数据只到 10-26，Core 30 天安静日中位数 40（11 天），近 7 天只有 2 个安静日。未见新的项目客户直接来信或 Anthropic/Stripe/Resend 通知。PR #141 已将摘要写入当前计划。 |
| Glama | 维护者同步 Repository 并将 Build steps 固定为 MCP `0.3.16` / Core `0.10.0`；后台测试 `01a17db0-eadf-78a5-b035-9f6c279cfd3d` 成功，安装 runtime `0.1.1`，服务握手 0.3.16 并列出九工具；Glama 渠道版本 `0.10.1` 已发布。PR #142 已记录。未在镜像里逐个执行九工具；Build Spec 标 Python 3.12，但 `uv pip --system` 日志显示 `/usr` Python 3.13.5。 |

当前公开发行：Core **0.10.0** / MCP **0.3.16** / runtime **0.1.1**。
`CHANGELOG.md` 的 `[Unreleased]` 没有待发 Core 功能或修复。
分发渠道编号与 PyPI 包版本独立。

## 留给下次

1. 处理 `workspace-meta` Guard 的 GitHub Actions 账单限制并核查当天云端备份
   新鲜度。10-27 新提交的 Guard 注释明确称账号近期付款失败或支出上限需提高，
   作业尚未启动；本地 `scripts/scan_credentials.sh` 通过，远端扫描仍未完成。
2. 核对 DEV 第二篇的署名、预览和是否实际发布；不要把私有草稿当成已投稿。
3. 待 PyPI 统计包含 10-27 后再观察 Core 0.10.0 发版日及后续安静日，
   不从发版尖峰推断自然增长。其余功能候选仍按 TODO 的需求与授权 gate。
4. `pyobfus-action` 本地分支 `docs/core-0.10.0-runtime-guide` 的 README
   修订已提交为 `5c6fa1c`、尚未推送；Action 仓库 `AGENTS.md` 要求推送前
   获得用户明确授权。已发布的 Action 页面不会因本地提交而改变。

## 分支与验证边界

本次核查 `~/projects/` 下 53 个 Git 仓库、54 个 worktree。唯一有未提交
内容的非 main 工作树是 `cardiac-ai-cac/.worktrees/hospital` 的
`feat/hospital-edition-v2.6.0`，有 7 个既有修改，已先告知并保持原样。
`pyobfus` main 干净，`pyobfus-action` 非 main 分支也干净；两者均无 stash。
Action 分支的“未推送提交”与“未提交改动”是不同状态。

发布前四个 Python 测试根、VS Code 测试及 `scripts/check.sh` 已通过；
发版后文档 PR #140–#142 的必需 CI/CodeQL 通过。文档后续只做状态同步，
不把历史快照改写为今天的结论。
