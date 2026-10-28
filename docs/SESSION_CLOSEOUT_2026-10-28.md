# 2026-10-28 session 收尾：DEV、封面、安全告警与 CI 成本

冷启动顺序：本页 → [当前计划](CURRENT_PLAN_ZH.md) → [TODO](TODO.md) →
[分发渠道](DISTRIBUTION_CHANNELS.md)。[10-27 收尾](SESSION_CLOSEOUT_2026-10-27.md)
是 Core 发版后的历史快照，其中 DEV 尚未发布、备份未核实等待办已由本页更新。

## 已完成并核实

| 范围 | 结果 |
|---|---|
| DEV 第二篇 | 维护者于 10-28 09:43:42 北京时间发布 [SARIF 文章](https://dev.to/zhurong2020/stop-writing-true-before-your-sarif-upload-16ih)，标题无反引号，使用公开 Core 0.10.0 复现，标签为 `githubactions/security/python/devops`，AI disclosure 为 `some_ai`。本地定稿与公开元数据保存在忽略目录 `docs/internal/content-2026-10/`；没有实测 GitHub 服务端 SARIF ingestion。 |
| 分享与封面 | 维护者发布 [X 原帖](https://x.com/zhurong0525/status/2115269885244944746)，10:53:51 北京时间给 DEV 文章补[流程示意封面](assets/dev-sarif-workflow-cover.png)。公开 DEV API 返回自定义 `cover_image` 和 `social_image`；1000 × 420 预览目视完整。已采用原图 2000 × 840 存入公开仓库；另一张 AI 候选图和四张 PyPI 对照截图存入 `docs/internal/content-2026-10/02-cover-candidates/`。维护者随后手工删除 Downloads／Desktop 临时副本，归档文件仍在。 |
| VS Code 开发依赖 | [PR #147](https://github.com/zhurong2020/pyobfus/pull/147) 修复 Dependabot #43、#39：`@azure/msal-node` 7.1.2、`serialize-javascript` 7.1.4，并将同链条 `qs` 更新到 6.17.0。本地 `npm audit` 为 0 个漏洞，扩展 53 项测试及 VSIX 打包通过；GitHub 两告警均显示 fixed，当前无开放 Dependabot 告警。MSAL override 跨上游 `@azure/identity` 声明的主版本范围；上游更新后须移除并复核。 |
| CI 分类 | 封面 PNG 原先被保守分类器视为代码，启动完整 Python 多系统矩阵。[PR #150](https://github.com/zhurong2020/pyobfus/pull/150) 仅豁免 `docs/assets/dev-*.png` 与文档组合；普通图片、社交预览图、代码和未知路径仍触发完整测试。分类器 36 项测试通过；合并后实际路径输入返回 `code=false`，社交预览图返回 `code=true`。修订本身是代码改动，因此 PR 与主分支各完整验证一次。 |
| 文档与 CI | [PR #145–#150](https://github.com/zhurong2020/pyobfus/pulls?q=is%3Apr+is%3Amerged) 依次记录文章、Publishing Tips、X、封面及安全／CI 修订。最新 `main` `b82ded8` 的 CI 与 CodeQL 均成功；工作树在收尾前干净。正式封面、发布清单、计划和分发渠道均有当前入口。 |
| 归档备份 | 原日备份完成于 09:05:35，早于图片归档。12:05–12:06 将 `docs/internal/content-2026-10/` 补入当日本地快照及 `gdrive:backups/wsl/current/pyobfus_local_only/docs_internal/content-2026-10/`；`rclone check --checksum --one-way` 显示 19 个文件匹配、0 差异。这是该文章归档的定向补备，并非整套日备份重跑。 |

公开版本仍为 Core **0.10.0**、MCP **0.3.16**、runtime **0.1.1**。
本轮没有发布新包、插件或 Action，也没有改动付费客户状态。

## 边界与下次顺序

1. **10-29 09:43 北京时间后**：查看 DEV 后台 24 小时阅读数、反应和具体评论；分别标注发布、补封面和 X 分享的时间，不从单次波动推断因果。
2. **11-01 后**：确认 GitHub 账号账单限制自然解除；先审 `workspace-meta` private Guard 的 push/PR 重复触发、超时和测试成本，再只运行必要的远端扫描并同步待推送的本地文档提交。此前不推送、不重跑 Guard。该仓库在本轮收尾前已有两笔本地提交未推送；本次跨仓索引更新若产生新提交也继续留在本地。
3. **11-04 09:43 北京时间后**：复盘文章一周后台数据、GitHub 来源与 PyPI 安静日。Core 10-27 发版日的 208 次非镜像下载早于文章，不能归因于内容。
4. **日常巡检**：只在真实缺陷／需求和相应授权下安排发版。`pyobfus-action` 的既有本地文档分支 `docs/core-0.10.0-runtime-guide`（`5c6fa1c`）仍未推送；其仓库指南要求推送前由维护者明确授权，本轮未处理。

本次没有触发 private 仓库的 GitHub Actions。完整候选图 SHA-256 与归档说明见本地忽略文件
`docs/internal/content-2026-10/02-cover-candidates/README.md`；平台图片 URL 与编辑时间见
`docs/internal/content-2026-10/02-published-metadata.json`。

## 关会话前最后审计

2026-10-28 再查 54 个 Git worktree：唯一非 main 未提交内容在
`cardiac-ai-cac/.worktrees/hospital` 的 `feat/hospital-edition-v2.6.0`，
共 7 个此前已存在的医院版修改；已先告知维护者，本会话未触碰。
`pyobfus-action` 的非 main 文档分支工作树干净，提交仍未推送。

项目的 `AGENTS.md` 和 `CLAUDE.md` 已指向本交接；用户版根 README
仍准确写明 Core 0.10.0，无会话状态需要加入。`workspace-meta` 的 README、
`WORKSPACE_CLAUDE.md`、`WORK_LOG_INDEX.md` 与 `PYOBFUS_REPOSITORY_MAP.md`
已同步交接路由；该 private 仓库本地 main 比远端多 4 笔文档提交，账单限制
解除前不推送。Claude 项目与工作区 memory 索引、Codex 10-28 memory
均已写入新入口；旧 memory 保留为带日期的历史记录。
两处 Claude memory 目录随后定向补入当日快照和 Google Drive 当前镜像：
项目 memory 110 个文件、工作区 memory 194 个文件，`rclone check --checksum`
均为 0 差异。Codex 的 10-28 memory 文件在本机 `~/.codex/memories/`，
其权威内容另见本仓已提交的本交接。
