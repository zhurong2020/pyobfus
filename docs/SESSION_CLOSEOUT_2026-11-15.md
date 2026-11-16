# 会话收尾 — 2026-11-15

本会话接续同日另一会话的调研与推进，代码改动交无头 Codex 实现、Claude 审核并独立复验。

## 已完成

| 项 | 结果 |
|---|---|
| #235 | PyInstaller CArchive 顶层交付检查；两轮审核修正 Windows 反斜杠成员名、超大非 PyInstaller 文件回归、未知类型计数、`o` 运行时选项条目误报；附带修复 `main` 自 `a240609` 起的 3.15 集成测试红灯 |
| #236 | `.pyc` 来源比对加有界纯字节 marshal 规范化（修复 Python 3.15 误报），交付数据不反序列化 |
| #237 | Windows x64／CPython 3.12／Nuitka standalone 单格托管验收：第 1 次 run 因运行脚本缺陷停在 D5，经批准修复后第 2 次 D1–D8 pass、D9 unknown、Pro L3 blocked，总体 partial |
| #238 | Core 0.15.0 发版准备；完整矩阵 47/47；tag `v0.15.0` → `3e76503`，PyPI 带 provenance，3.12／3.15 全新安装通过，GitHub Release 已建。见[发布记录](CORE_0_15_0_RELEASE_2026-11-15.md) |

## 待办（下次会话从这里开始）

1. ~~**Glama**~~：已完成。Glama 渠道 release **0.14.1**（Glama 自动递增标签，2026-11-15 23:06 北京时间发布）：维护者改 Build steps 为 `uv pip install --system --break-system-packages pyobfus-mcp==0.3.17 pyobfus==0.15.0` 并点「Build & Release」；test `01a1dfbc-345a-79cf-95ba-581e06887151` success／27.9 s，`pinnedCommit: null`（实际 checkout Glama 同步 head `cde07eb`，落后于 main；安装来自 PyPI，不影响结果），uv 装于 /usr 的 Python 3.13.5，安装 Core 0.15.0／MCP 0.3.17／runtime 0.1.1，握手 serverInfo 0.3.17、协议 2025-11-25，`tools/list` 九个工具（七 community + 两 pro_funnel）。
2. **Zenodo／CITATION**：归档后按 CLAUDE.md 发布流程第 5 步核对 record，再同步 `CITATION.cff`。
3. **Pro 客户通知（TODO 4a）**：私有草稿 `docs/internal/pro_customer_notice_0_15_0_DRAFT_2026-11-15.md` 待维护者审；审后按 Worker 许可记录核对收件人再发送。
4. ~~**本 PR（#239）合并**~~：维护者已于 2026-11-16 在 GitHub 网页端 squash
   merge 为 `144b6e1`；main CI、CodeQL 与 IndexNow docs notification 均成功。
5. ~~**11-16 周检增量**~~：规范 `/zh-cn/` 已收录、已索引且 HTTPS 正常；GSC
   sitemap 仍显示 11-12 的“无法读取”旧状态，未删除重提。Bing 已选择正确的 pyobfus
   属性，IndexNow UI 未展示记录，但 GitHub notification workflow 成功。完整结论与
   后续顺序见[11-16 执行记录](EXECUTION_PROGRESS_2026-11-16.md)。

无 Worker 部署；MCP、runtime、VS Code、Action 未发版。
