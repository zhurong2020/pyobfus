# 会话收尾 — 2026-11-16

本文件是下一会话入口。状态以本文为准；详见[执行进度](EXECUTION_PROGRESS_2026-11-16.md)
与 [#241 审阅证据](UPLOAD_ARTIFACT_V7_REVIEW_2026-11-16.md)。

## 仓库与验证

- #242 已合并为 `e5e3cc2`，CITATION 已同步；main CI `43784146594`、CodeQL
  `43784146729`、IndexNow `43784146606` 全部成功。
- #241 已合并为 `4204699`；main CI `43784675317`、CodeQL `43784675289`、
  Dogfood `43784675381`、Draft PDF `43784675293` 全部成功。WSL main 已同步该提交。
- 本轮文档按执行状态与 Agent 入口分组本地提交，准确 SHA／分支用 `git log` 和
  `git status` 核对；本次未授权新的合并、发布或部署。
- Core 5152 passed / 56 skipped（正常 HOME）、MCP 167、integration 371 passed /
  10 skipped、runtime 24、基准 8；完整 `scripts/check.sh` 通过，正常 hooks 通过。
  本轮无产品代码变更，无需为后续纯状态文字重复完整 pytest。
- PR 托管 CI 结果以 GitHub 检查页为准；会话末结果另保存到 git-ignored
  `docs/internal/followup_checkpoint_2026-11-16.md`，避免为记录结果反复触发 CI。
  两个 PR 均已获维护者授权并完成合并，不再重复请求合并。

## 已完成

1. 0.15.0 发布、PyPI provenance、新环境验证、Glama 0.14.1、#239 合并均已完成，
   不重做。版本仍为 Core 0.15.0 / MCP 0.3.17 / runtime 0.1.1 / VS Code 0.4.3 /
   Action v1.1.0。
2. GSC 规范 `/pyobfus/zh-cn/` 已收录、已索引且 HTTPS 正常；sitemap 后台仍显示
   11-12 旧错误，不删除重提。Bing 已选择正确属性；IndexNow 后台未展示记录，
   GitHub notification 成功，不能写成零提交或失败。
3. #241 已审阅并合并：未发现阻塞兼容问题。v7.0.2 tag/SHA、Node 24 与 runner 门槛、
   默认 ZIP／hidden files／覆盖／retention／命名和消费端均已核对。Dogfood 两次和
   PDF 一次上传实际成功；独立下载三个 artifact，SHA-256、ZIP CRC、布局均通过。
   Windows Nuitka 和 Lane C 未在该 revision 执行。Windows 旧 v4.6.2 注释建议修正。
4. Zenodo record `24248676` 已可靠核实：v0.15.0 / 2026-11-15 / concept `20846053` /
   GitHub `tree/v0.15.0`。CITATION 已随 #242 合入，通过官方 CFF 1.2.0 schema 校验。
5. 升级通知义务已完成，发送核验及后续支持详情仅存私有
   `docs/internal/CUSTOMER_SUPPORT_LOG.md`；不得因旧草稿状态重复发送。

## 下一步（按顺序）

1. 按常规周期观察客户反馈、CI、下载安静日、自然备份和搜索后台；通知相关支持只记私有记录。
2. 2026-12 第一周搜索／AI 可见性观察；约 12-04 做 Core 0.12.0 T+30d。
3. 未来计划内 key 轮换须另行确认最低客户端版本与切换日期，并满足下方时间边界；
   当前升级通知不替代届时的正式通知。
4. Windows workflow 旧 v4.6.2 注释留到自然维护；实际 SHA 已是 v7.0.2。
   Windows 验收与 Lane C 未因本轮升级重新执行，不扩大已验证范围。

## 保持边界

不发布新版本、不部署 Worker、不轮换 key、不修改 ruleset、不扩大 Windows 验收范围。
`ci-2026-11b` 仅客户端预信任，Worker 继续 `ci-2026-11`；计划内切换必须满足
2026-11-15 后至少 180 天（约 2027-05-14）且提前至少 60 天通知。
客户／业务细节不进公开仓库。Glama 临时托管实例提醒与渠道 release 分开判断。
