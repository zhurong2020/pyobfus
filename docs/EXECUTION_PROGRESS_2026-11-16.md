# 执行进度 — 2026-11-16

本记录收口 Core 0.15.0 发布后的公开渠道与仓库状态。涉及客户、收件人与私有草稿的
细节继续只留在 `docs/internal/`，本文不记录个人或业务机密信息。
下一会话直接从[本日收尾](SESSION_CLOSEOUT_2026-11-16.md)接续。

## 首轮仓库与托管检查（历史快照）

- 维护者在 GitHub 网页端将 #239 squash merge 到 `main`，合并提交为
  `144b6e1e1dacca57a6ec1079ab99c36003c34231`。本地 WSL 主仓已通过
  `git pull --ff-only origin main` 快进到该提交，工作树在同步前后均无本地改动。
- #239 合并后的托管结果全部成功：CI run `43780329567`、CodeQL run
  `43780329541`、IndexNow docs notification run `43780329549`。同日定时
  License Endpoint Monitor run `43769788605` 也成功。
- #240（VS Code npm minor/patch 依赖更新）已经进入 `main`；本次同步包含其
  `package.json`／`package-lock.json` 变化，不把它误记为 0.15.0 发布内容。
- #241（`actions/upload-artifact` 4.6.2 → 7.0.2）仍为独立待审 PR。其 CI 与
  Dogfood 已成功，但跨主版本升级仍须核对官方迁移说明、固定 SHA、runner／GHES
  边界和三个 workflow 使用点；不得仅凭绿灯直接合并。

## 搜索后台增量

- Google Search Console 的规范地址
  `https://zhurong2020.github.io/pyobfus/zh-cn/` 显示“网址已收录到 Google”，
  网页已编入索引且 HTTPS 正常，因此未重复请求索引。
- GSC 的 `/sitemap.xml` 仍显示上次读取 2026-11-12、状态“无法读取”、发现网页 0。
  详情页只提供移除操作，没有重新读取入口；公开侧 sitemap、canonical 与抓取结果此前
  已核为正常，本次没有删除重提，也没有为迎合旧状态修改正确配置。
- Bing Webmaster 已明确切换到 `zhurong2020.github.io/pyobfus/` 属性。该属性的
  IndexNow 页面仍显示 `Get Started`，没有可归因的提交记录；但 GitHub 的 IndexNow
  workflow run `43780329549` 已成功。因此不得把后台未展示解释为零提交或提交失败，
  后续只观察后台是否补齐记录。

## 首轮发布后接续（已由下文收口）

- Core 0.15.0、GitHub Release、PyPI provenance、全新 3.12／3.15 安装和 Glama
  0.14.1 安装 Core 0.15.0 的证据已随 #239 进入 `main`，见
  [发布记录](CORE_0_15_0_RELEASE_2026-11-15.md)与
  [11-15 收尾](SESSION_CLOSEOUT_2026-11-15.md)。
- Zenodo 0.15.0 新 record 尚未得到可靠证据；继续等待归档，不猜测 record ID，出现后
  再同步 `CITATION.cff`。
- Pro 客户升级通知现已到期，但发送仍是独立外部动作：维护者先审私有草稿，再按 Worker
  许可记录核对收件人；公开仓库只记工程义务，不写客户信息。备用 key `ci-2026-11b`
  仍不得配置到 Worker。

## 首轮下一顺序（历史快照）

1. 在 WSL 主仓运行完整 `scripts/check.sh`，确认本次文档增量。
2. 独立审阅 #241，给出可合并、需修改或暂缓的证据化结论；未获授权不合并。
3. 等待 Zenodo 0.15.0 record，出现后按发布流程同步 `CITATION.cff`。
4. 维护者审阅并决定是否发送 Pro 客户升级通知；发送记录只留私有目录。
5. 继续按既定周期执行 12 月第一周搜索／AI 观察与约 12-04 的 Core 0.12.0 T+30d
   观察，不因无新缺陷重复发版。

## 同日接续：独立复核检查点

- 完整 `scripts/check.sh` 再次通过；提交前各 pytest 根分别运行，Core 已完成。
  MCP 167、integration 371 passed / 10 skipped、runtime 24、基准 8 已通过。
- #241 审阅未发现阻塞兼容问题，完整证据见
  [upload-artifact v7 审阅](UPLOAD_ARTIFACT_V7_REVIEW_2026-11-16.md)。Dogfood 与
  PDF 的三个 artifact 已独立下载，SHA-256、ZIP CRC 与目录布局均核实；Windows
  与 Lane C 未在该 revision 实跑。Windows 的旧 v4.6.2 注释为非阻塞修正建议。
- Zenodo concept DOI 已重定向到 [24248676](https://zenodo.org/records/24248676)，
  API 确认 v0.15.0 / 2026-11-15 / concept 20846053 / GitHub tree/v0.15.0。
  CITATION 将单独提交同步。
- 私有客户通知草稿已复核，建议定期更新固定版本、明确当前备用 key 的范围和冻结
  载荷仍可能未检查；仍待维护者审阅，未查询收件人、未发送。
- 下载数据截至 11-14：Core 近 7 天 550、安静日中位数 52（4 天），30 天 4112、
  安静日中位数 78（11 天）；MCP 近 7 天 55、中位数 6。尚未覆盖 0.15.0 发布日。
  本轮邮件检索未发现新增客户支持请求；目录解除锁仍等待上游，详情只留私有记录。

本轮提交前验证：Core 5152 passed / 56 skipped（正常 HOME），MCP 167、integration
371 passed / 10 skipped、runtime 24、基准 8；完整 `scripts/check.sh` 通过。

## 提交与最终接续

- `45e8d08`：六份公开文档收口，包含原五份交接增量和 #241 审阅证据；正常 hooks 通过。
- CITATION 独立同步提交：version 0.15.0、date-released 2026-11-15、version DOI
  10.5281/zenodo.24248676；concept DOI 不变。官方 CFF 1.2.0 JSON schema
  (`citation-file-format` 的 1.2.0 tag) 校验通过，并与本轮独立取得的 Zenodo API 比对。
- 本轮分支 `docs/nov16-release-followup` 已推送，CITATION 提交 `4c153eb`；
  [草稿 PR #242](https://github.com/zhurong2020/pyobfus/pull/242) 已建立，待托管 CI，未合并。
  检查完成后精确状态保存到 git-ignored `docs/internal/followup_checkpoint_2026-11-16.md`。
- 客户通知正文已完成私有复核，待维护者审阅；未查询收件人、未发送，未部署 Worker。

## 最终收口：合并与接续

- #242 已获维护者批准 squash merge 为 `e5e3cc20e3fe68997588e7f44279b18250606c12`；
  main CI `43784146594`、CodeQL `43784146729`、IndexNow `43784146606` 全部成功。
  CITATION 的 v0.15.0／2026-11-15／Zenodo `24248676` 已进入 main。
- #241 随后获准 squash merge 为 `4204699cc89b7c81ad53787a4120a1a9eddf271b`；
  main CI `43784675317`、CodeQL `43784675289`、Dogfood `43784675381`、
  Draft PDF `43784675293` 全部成功。WSL 主仓已快进同步，原工作树干净。
- 升级通知义务已完成，发送核验与后续支持记录只存私有
  `docs/internal/CUSTOMER_SUPPORT_LOG.md`；公开文档不包含客户或收件信息。
- TODO 已移除本次完成的文档合入、通知和 #241 合并项，保留周期观察、正式轮换通知
  规则和自然维护注释。没有新发版、Worker 部署或 key 轮换。
- 本轮仅更新文档，沿用同日已通过的各测试根结果；分类提交前分别运行完整
  `scripts/check.sh` 与 diff 检查。确切提交状态保存在私有检查点，避免记录引发循环提交。
