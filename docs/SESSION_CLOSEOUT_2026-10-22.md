# Session 交接：采用流程、独立目录 mapping 与后续设计

日期：2026-10-22。冷启动先读本文、`CURRENT_PLAN_ZH.md` 顶部和 `TODO.md`；不要按旧静默期记录重新等待或重做已完成工作。

## 分支与提交

工作分支 `feat/adoption-debugging-workflow`，基点 `9fb1239`。本轮分类提交：

| Commit | 内容 |
|---|---|
| `f18d398` | Black 最低语法目标 py39；mypy <2，保留 Python 3.9 检查支持 |
| `267d763` | Community 独立文件目录 mapping v2、CLI/MCP 提示、回归与调试文档 |
| `29aa0eb` | 多模块 L3 + 应用 key provider 的限定设计与复核结论；未实施 |
| `956323c` | 用户流程审计、DEV 案例验证、AI 采用引导与计划同步 |

本轮提交保存在本地，尚未 push、合并或发布。版本仍是公开 Core 0.8.0 / MCP 0.3.14 / runtime 0.1.1；公开安装包不含新 mapping 能力。收尾文档另以 docs commit 保存。

## 已完成与证据

- [公开发布包用户流程](ADOPTION_WORKFLOW_AUDIT_2026-10-22.md)：隔离构建、无 builder 的目标执行、异常恢复；没有启动试用或购买。
- [mapping 验收](INDEPENDENT_DIRECTORY_MAPPING_VALIDATION.md)：Core 4467 passed / 54 skipped，MCP 153，集成 352 / 10 skipped，runtime 24；Python 3.15 专项 157。工作 wheel 的新 reader 接受旧 v1；公开旧 reader 明确拒绝 v2。都是本地验证，不代表新功能已通过 hosted 全矩阵。
- [L3 设计](CROSSFILE_OPACITY_DESIGN.md)：两路最终独立复核完成；只设计。后续实施须接受已列范围与调试限制；Pro/runtime 实现未改变。
- [DEV 验证](ADOPTION_CONTENT_VALIDATION_2026-10-22.md)：保留 SARIF 主题，使用公开 0.8.0 复现 clean / high / missing；只验证本地扫描和模拟 gate，没有 GitHub ingestion 或发稿。
- [AI / Agent 采用引导](AGENT_ADOPTION_GUIDANCE_PLAN.md)：仅列后续计划，没有修改对外 llms、技能或能力元数据。
- `scripts/check.sh` 全部通过：296 文件 Black、Ruff、113 源文件 mypy、镜像／README 链接与严格 MkDocs；`git diff --check` 通过。上述产品测试无需因纯交接文档变动重复。

审核原始记录、合成验证脚本、文章草稿及发布步骤在本地忽略目录 `docs/internal/`，没有提交到公共仓库。临时 venv 位于 /tmp，只是证据环境；长期开发使用仓内 venv，3.15 使用工作区已登记的环境。

## 续接顺序

1. 维护者审阅上述本地提交，决定后续 PR／合并／发布；不自动 push、打 tag 或发版。
2. L3 仍是未来单项实施输入；确认范围后再开工。独立发现的 Pro opacity 纯转换 API future prologue 问题已列 TODO，CLI 影响未验证，不应误说已修复。
3. DEV 草稿待维护者审稿，原拟 10-27 仅候选时间；不得自动投稿或发送邮件。
4. 保留每周下载观察与 10-25 复盘，不再以等待下载自然变化为主要任务；AI 采用引导排在本轮四阶段之后。

下载／邮件只读核查、目录锁处理和客户状态见 CURRENT_PLAN_ZH.md 10-22 记录；没有对外发送或更改邮件状态。跨项目索引和持久记忆指向本交接，不复制产品细节；医院应用仍暂停。本轮无许可证、专利或 Action 合同变化，legal、历史源和备份不做同步修改。
