# 冷启动 prompt

```text
请在 ~/projects/pyobfus 续接上一会话。
先读 AGENTS.md、docs/SESSION_CLOSEOUT_2026-11-01.md、
docs/EXECUTION_PROGRESS_2026-11-01.md 和 docs/CURRENT_PLAN_ZH.md，
再核实各仓 Git、PR、CI 与备份的实时状态，避免重复已完成工作。

依次推进：
1. 实质审阅 cardiac-shared #60、llm-enrichment #1、pyobfus-action #2。
   三者此前检查均通过、未合并；先检查最新 diff、base 漂移、checks 和 reviews，
   按各仓现行流程记录发现和必要修复。独立审阅与合并按现有授权边界执行，
   不把通过 CI 或这份交接当作新增合并／发布授权。
2. 核实 Read the Docs 最新构建与首页、llms 文件。此前本机返回 Cloudflare
   challenge 429，检索端只有两天前缓存，不能据此声称最新部署一致。
3. 核查自然备份进程、日志与云端完成标记。此前月快照还在复制，标记停在
   10-31，内部文档云端仍有差异。先读备份 SoT，完成后做 MD5 复验；
   明细在 docs/internal/backup-*20261101*。重新识别进程，不沿用旧 PID；
   不重复跑整套备份、不盲目终止复制、不删除云端历史。
4. 根据当前日期处理 11-02 定时 Guard、11-04 DEV、11-05 LinkedIn 观察；
   真实购买后的发号／Customer 核验仍由事件触发。

每完成一项及时保存证据并同步 TODO／当前计划。仅使用 WSL 工作副本，
保留其他会话改动；客户、许可和运营细节只放私有记录。
继续已授权的必要工作，遇到阻碍先做可独立推进的事项，再准确报告剩余条件。
```
