# 2026-11-06／11-07 会话收尾

冷启动：本文件 → [当前计划](CURRENT_PLAN_ZH.md) 顶部 11-06／11-07 段 → [TODO](TODO.md)（「周期性」含新增巡检）。
公开版本不变：Core **0.12.0** / MCP 0.3.17 / runtime 0.1.1 / 扩展 0.4.3 / Action v1.1.0；Glama 渠道 0.12.0（11-05）。
本轮**无发版**；main 上有未发布的 Community pre-commit 钩子，随下次发版到用户（需维护者批准）。

## 已完成（PR #188–#201，均 CI／CodeQL 通过后合并）

| 范围 | 结果 |
|---|---|
| CI | `ubuntu-latest` 切到 26.04 后无 Python 3.9，Ubuntu 3.9 格固定 `ubuntu-24.04`（#188）。维护者决定**保留 3.9 支持**；`ubuntu-24.04` 退役前需另找 3.9 runner。 |
| 观察与运营 | 11-04 巡检、Glama 渠道 0.12.0、LinkedIn 一周复盘（43 展示、无可归因访问）、Core 0.12.0 T+24h／T+72h（无客户问题）。 |
| 渠道试验评估 | aocr.org 来源判为机器流量并排除；Stack Overflow **禁止任何 LLM 起草（含改写）**，SO 回答只能维护者本人从零写；原稿转为站内 FAQ。 |
| 文档 | 新 [FAQ](guides/protect-python-code-faq.md)（#191）；Agent 文档补 0.11.1／0.12.0 并定「发版同步 Agent 文档」规则（#192、pyobfus-action #4）；两篇中文指南与报错还原指南开头（#195）。 |
| 功能（未发版） | Community pre-commit 钩子 `pyobfus-no-private-material` / `pyobfus-check-delivery`（#194，Codex 实现、Claude 两轮审核，真实 pre-commit 端到端验证）。 |
| 搜索可见度 | IndexNow 自动通知（#196，首次 202／200）；Google Search Console 两资源（落地页自动验证；文档站 HTML 文件验证，`docs/google03878b382b498ff9.html` 必须保留），文档站 sitemap 146 页读取成功；Bing 从 GSC 导入两站，sitemap 均处理成功（#199、#200）。周检与月度观测写入 TODO（#201）。 |
| 月度观测 | 11-07 搜索／AI 观测：WebSearch 5/12（10-07 为 7/12），Codex 2/12，Codebuddy hy4free 4/12、deepseek-v4-pro 3/12、kimi-k3.1-pro 2/12（1 题拒答）；多文件混淆题稳定命中，出售前保护、PyInstaller、中文报错题无一环境命中。明细私有。 |
| 备份 | 本机日备份 11-05—11-07 因用户级 systemd 管理器开机超时未运行；维护者重启 UID 1000 的用户级管理器服务后补跑，11-04 发版证据与本轮私有记录在本地快照和云端 `current/` 核对一致（#198）。 |

## 下一步（按日期）

1. **11-08**：对 `https://zhurong2020.github.io/pyobfus/`（带末尾 `/`）再请求编入索引；查看落地页 sitemap 是否已被 Google 读取。
2. **11-09 周一巡检**：进度 + 下载量 + Gmail，加 TODO「周期性」新增的 Search Console／Bing／IndexNow 检查。
3. **约 11-11**：T+7d 观察。
4. **数据有 1–2 天后**：维护者用 Chrome 插件跑只读盘点（Prompt 在 `~/projects/workspace-meta/archives/SEARCH_CONSOLE_SETUP_GUIDE_2026-11-07.md` 第 5 步），JSON 交 Claude 分析。
5. **2026-12 第一周**：月度搜索／AI 观测（方法与隔离见私有基线）。
6. **待维护者决定**：小型渠道试验（本人在 SO 作答，或 Reddit，需先核社区 AI 规则与 karma 门槛）；下次发版时机（带 pre-commit 钩子）。

## 交给其它项目

- arong.eu.org 与老博客 zhurong2020.github.io 的搜索可见度工作已交 findata：
  `findata/content/SEARCH_PRESENCE_TODO_2026-11-07.md`（findata `CLAUDE.md` 顶部有入口）。

## 本轮教训（详见 memory）

- 无头 Codex／Codebuddy 做 AI 观测必须隔离：中性目录（路径里不能有项目名）、独立 `CODEX_HOME`（只带 auth 与 config）、Codebuddy `--no-session-persistence`；`while read` 循环内的命令要 `</dev/null`；统计用整词匹配（`pyobfuscate` 会误中）。
- 不要用脚本轮询 pyobfus.readthedocs.io 判断上线：对脚本一律 Cloudflare 质询（429）。
- 「备份包含性核对」先看最新快照日期，再看配置。

## 收尾后补充（11-07 下午）

- 维护者用 Chrome 插件跑了首轮只读盘点（注册当天，多数报告处理中）；原始 JSON 存私有 workspace-meta。
  pyobfus 两站：文档站 sitemap 成功 146 页；落地页 sitemap 在 Google 仍「无法抓取」、Bing 已成功读取 2 网址。
  **11-08／11-09 用同一 Prompt 复采**（TODO「周期性」已登记，#203），届时也看 Bing IndexNow 页是否出现提交记录。
- 同一会话里顺带完成了个人站 arong.eu.org 的基础设置（站点地图提交、robots.txt 改为网站自管并放开百度与华为搜索、
  Cloudflare AI 爬虫防火墙开关核对），这些不属于 pyobfus，全部记录在
  `findata/content/SEARCH_PRESENCE_TODO_2026-11-07.md`，后续由 findata 会话接手。
- 维护者开启了 Cloudflare 账号两步验证，恢复码已存入 Vaultwarden（条目名见私有 memory）。
