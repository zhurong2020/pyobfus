# 维护者动作清单

从 TODO.md（源提交 `764ead1`）拆出的未完成动作；不批准发布、部署、签发或对外发信。
公开文件只保留工程动作；账号、支持与业务背景见私有记录。

## 外部账号与只读核验

- [ ] Claude plugin：等待目录解除锁，解除后用付费账号在 <https://claude.ai/directory/manage> 重提；不反复提交、不换仓库／路径绕过、不必更新仓库+manifest 提交内容。支持详情见私有 `docs/internal/CLAUDE_PLUGIN_RESUBMISSION_2026-09-22.md`；可选致谢草稿仍待维护者决定。
- [ ] **MCP Trust Registry publish**：在其站点注册拿 API token 后
      `MCPTRUSTCHECKER_TOKEN=… npx --yes mcptrustchecker@1.14.0 publish pyobfus-mcp --registry pypi --online --category developer-tools`
      （wheel 已扫 A · 94/100，09-23 已用 CLI help 核对参数；不要把 token 写进 shell history、仓库或聊天）。

- [ ] 基线测试结束后可按需恢复个性化设置；复测前关闭，避免把个性化推荐当中性结果。
- [ ] **原 10-11 清单的其余开放动作**：
      ③ `--check` 仍默认联网（CLI，MCP 默认关）——10-11 定「等 Codex 这波完成后再审」，现可决定是否改默认离线；
      ⑤ 约 10-14 看 DEV 第 1 篇反响与 GitHub 流量来源，再决定是否投 HN（Show HN 已用过，只能普通投稿）。

- [ ] **0.6.1 通知的回信**：随每周一巡检看 Gmail；回信若报激活问题按 `LICENSE_ACTIVATION_GUIDE.md`
      排障，不主动追发第二封。各客户激活状态只在私有记录。

- [ ] **下一次自然购买核验**：下一笔真实购买时按「核验新发号流程」复核发号与 Customer 资料。
      过程与原因见私有 `docs/internal/billing/`。
- 后续核验应只读比对许可记录与 Checkout Session；不符先排查，不在 Dashboard 手工重放事件。

- [ ] **开启任何延迟到账付款方式前的检查**（规则，长期有效）：Worker 与 webhook 订阅已支持
      `checkout.session.async_payment_succeeded`，但开 ACH / SEPA / 银行转账等之前先确认 endpoint 仍订阅该事件，
      开后的第一笔按上面「核验新发号流程」走一遍。Stripe 付款方式是账户级配置，会按它动态展示。
- [ ] **维护者手动删除 OneDrive 两个旧副本**：`…/3-job/program/` 下 `pyobfus-action/` 与
      `pyobfus-backup-pre-filter-repo-20260503-2231/`，都带 `MOVED_TO_WSL_20260921.md`、WSL 均有副本
      （`~/projects/` 同名目录）。09-22 只删了 pyobfus 与 pyobfus-legal 两个批过的；这两个不在清单里，未动。
      **09-23 已完成删除前核验**：排除 `.git`、`.mypy_cache`、`.ruff_cache` 与迁移标记后，
      对两组执行 checksum `rsync -rcni --delete` 均为零输出。维护者已决定自行删除，AI
      代理不执行该云同步删除；删完只需回报以便勾掉。此后 Core/MCP/runtime/Action 的本地
      开发、测试、构建与发版准备全部只在 `~/projects/` 的 WSL 工作副本进行，
      OneDrive 仅作迁移残留或备份，不在其中编辑或执行。

## 外部等待与其他维护者决定

- Open VSX namespace 归属验证：可选，`not verified` 是「未申请」不是「被拒」。
- **Canopii [`canopii-cli#6`](https://github.com/canopii-dev/canopii-cli/issues/6)
  —— 单次 follow-up 已发，等待上游**。2026-09-23 确认 issue 仍 `OPEN`、0 条上游回复后，
  已按约定发出唯一一次简短 follow-up（明确当前版本 0.3.12 与四项验收）；**不再反复催**。
  上游重扫后按四项验收（latest ≥ v0.3.10 /
  识别 8 tools / 不再把 `pyobfus_pro/`、`examples/`、VS Code/Worker 计入 MCP 包
  evidence / PEP 740 provenance 是否被识别），**不是只看总分**。

上述版本与 8 tools 为原 09-23 验收口径，不是当前工具数；新版本重扫仍须核对实际包边界与 provenance，不能只看总分。

- MCP Trust Registry 发布后将结果记入 `DISTRIBUTION_CHANNELS.md`；不为徽章改产品逻辑。
- Action 旧 README 分支 `docs/core-0.10.0-runtime-guide`（`5c6fa1c`）的推送／合并是否仍有遗留先只读核对；该仓库推送须用户明确授权。
- 品牌防护商标仍待决定，先评估中国第 9 类，再评估美国；法务与身份材料仅留仓库外私有记录。
