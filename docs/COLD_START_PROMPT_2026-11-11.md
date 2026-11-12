# 2026-11-11 冷启动提示

复制以下内容开始下一次会话：

```text
切换到 ~/projects/pyobfus，先读 AGENTS.md、docs/SESSION_CLOSEOUT_2026-11-11.md（顶部"夜间最终状态"）、docs/CORE_0_14_0_RELEASE_2026-11-11.md、docs/CURRENT_PLAN_ZH.md 和 docs/TODO.md。

先检查 git status 与 origin 差异。公开版本：Core 0.14.0（签名 CI 构建准入，11-11 发布）、MCP 0.3.17、runtime 0.1.1、扩展 0.4.3、Action v1.1.0。生产签发 key ci-2026-11 与 Worker 13aaa4a8 已上线；私钥在私有凭证库，勿随意轮换（换 key 先发带新公钥的客户端并约定升级窗口），不接受 unsigned fallback／环境公钥覆盖。

待办：确认 96e6340 的 main CI 结果；Zenodo 归档后同步 CITATION.cff；提醒维护者更新 Glama Build steps；询问是否补 #221 独立外部审阅；GSC 示例、11-16 周检（含下载量与收件箱）、专业许可审阅、12 月观测。合并、部署与发版均需维护者当次明确批准。跨项目审计见 ~/projects/workspace-meta/archives/SESSION_FINAL_SYNC_20261111_PYOBFUS.md。
```
