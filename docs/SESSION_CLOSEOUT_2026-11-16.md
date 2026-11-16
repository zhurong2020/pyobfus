# 会话收尾 — 2026-11-16

本文件是下一会话入口。状态以本文为准；详见[执行进度](EXECUTION_PROGRESS_2026-11-16.md)
与 [#241 审阅证据](UPLOAD_ARTIFACT_V7_REVIEW_2026-11-16.md)。

## 仓库与验证

- main 基线 `144b6e1`（#239 squash merge）；#240 也已在 main。
- 本轮分支 `docs/nov16-release-followup` 已推送；[草稿 PR #242](https://github.com/zhurong2020/pyobfus/pull/242)。
  `45e8d08` 收口六份文档，`4c153eb` 独立同步 CITATION 并更新状态。
  后续状态提交用 `git log --oneline -3` 核对；main 未改变。
- Core 5152 passed / 56 skipped（正常 HOME）、MCP 167、integration 371 passed /
  10 skipped、runtime 24、基准 8；完整 `scripts/check.sh` 通过，正常 hooks 通过。
  本轮无产品代码变更，无需为后续纯状态文字重复完整 pytest。
- PR 托管 CI 结果以 GitHub 检查页为准；会话末结果另保存到 git-ignored
  `docs/internal/followup_checkpoint_2026-11-16.md`，避免为记录结果反复触发 CI。
  没有维护者合并决定前不合并。

## 已完成

1. 0.15.0 发布、PyPI provenance、新环境验证、Glama 0.14.1、#239 合并均已完成，
   不重做。版本仍为 Core 0.15.0 / MCP 0.3.17 / runtime 0.1.1 / VS Code 0.4.3 /
   Action v1.1.0。
2. GSC 规范 `/pyobfus/zh-cn/` 已收录、已索引且 HTTPS 正常；sitemap 后台仍显示
   11-12 旧错误，不删除重提。Bing 已选择正确属性；IndexNow 后台未展示记录，
   GitHub notification 成功，不能写成零提交或失败。
3. #241 审阅完成：未发现阻塞兼容问题。v7.0.2 tag/SHA、Node 24 与 runner 门槛、
   默认 ZIP／hidden files／覆盖／retention／命名和消费端均已核对。Dogfood 两次和
   PDF 一次上传实际成功；独立下载三个 artifact，SHA-256、ZIP CRC、布局均通过。
   Windows Nuitka 和 Lane C 未在该 revision 执行。Windows 旧 v4.6.2 注释建议修正。
4. Zenodo record `24248676` 已可靠核实：v0.15.0 / 2026-11-15 / concept `20846053` /
   GitHub `tree/v0.15.0`。CITATION 同步候选通过官方 CFF 1.2.0 schema 校验。
5. 私有客户通知草稿已复核并修订；建议保留可复现 CI pin 但定期升级，明确当前备用 key
   的适用范围，保留冻结载荷未检查边界。正文仍待维护者审阅，未查询收件人、未发送。
   私有入口：`docs/internal/pro_customer_notice_review_2026-11-16.md`。

## 下一步（按顺序）

1. 完成文档分支托管 CI，报告 PR、准确 SHA、检查结论与工作树状态；待维护者合并。
2. #241 当前 head `72623d7`，CI、CodeQL、Dogfood 与 PDF 成功，MERGEABLE / CLEAN。
   待维护者决定是否合并；未启用 auto-merge。可顺手修正旧版本注释，再看最终 revision。
3. 维护者审阅私有客户通知正文；批准后按只读 Worker 许可记录核对、去重收件人，
   最终收件人与发送记录只存 internal。发送需明确批准最终正文和收件人范围。
4. 继续每周观察；2026-12 第一周做搜索／AI 可见性观察，约 12-04 做 Core 0.12.0
   T+30d。下载数据仅到 11-14，不能据此评估 0.15.0 发布效果。

## 保持边界

不发布新版本、不部署 Worker、不轮换 key、不修改 ruleset、不扩大 Windows 验收范围。
`ci-2026-11b` 仅客户端预信任，Worker 继续 `ci-2026-11`；计划内切换必须满足
2026-11-15 后至少 180 天（约 2027-05-14）且提前至少 60 天通知。
客户／业务细节不进公开仓库。Glama 临时托管实例提醒与渠道 release 分开判断。
