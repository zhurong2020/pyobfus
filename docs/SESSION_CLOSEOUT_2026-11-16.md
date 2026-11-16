# 会话收尾 — 2026-11-16

这是下一会话的首要入口。先读本文，再读
[本日执行记录](EXECUTION_PROGRESS_2026-11-16.md)、[当前计划](CURRENT_PLAN_ZH.md)和
[TODO](TODO.md)；不要重做已经完成的 0.15.0 发布、Glama、#239 合并或搜索后台检查。

## 当前仓库状态

- WSL 主仓 `main` 已通过 `git pull --ff-only` 快进到
  `144b6e1e1dacca57a6ec1079ab99c36003c34231`，即 #239 的 squash merge；同步前工作树
  干净。
- #239 合并后的 CI、CodeQL 与 IndexNow docs notification 均成功；同日定时 License
  Endpoint Monitor 也成功。公开版本为 Core 0.15.0／MCP 0.3.17／runtime 0.1.1／
  VS Code 0.4.3／Action v1.1.0。
- #240 的 VS Code npm minor/patch 更新已进入 `main`，但不属于 Core 0.15.0 发布内容。
- 本会话新增或修改五个公开文档，尚未提交：
  - `docs/EXECUTION_PROGRESS_2026-11-16.md`
  - `docs/CURRENT_PLAN_ZH.md`
  - `docs/TODO.md`
  - `docs/SESSION_CLOSEOUT_2026-11-15.md`
  - 本文也属于同一批 11-16 文档收口。
- 上述差异已两次通过 `git diff --check` 与完整 `scripts/check.sh`。最后一次结果为
  black 337 files unchanged、ruff 通过、mypy 121 files 无错误、JSON／Agent guide twins／
  README links／`mkdocs build --strict` 全部通过。

下一会话先运行 `git status --short`，确认只有这五个预期文档变化；审阅差异后按正常
hook 提交。建议提交信息为 `docs: record November 16 release follow-up`。未获维护者明确
授权时不要自行 push；提交或推送后再次报告 SHA 与工作树状态。

## 今日已完成

1. Core 0.15.0 的发布证据、Glama 0.14.1 接续和 #239 收尾已经进入 `main`。
2. Google Search Console 的规范地址 `/pyobfus/zh-cn/` 已收录、已编入索引且 HTTPS
   正常，因此没有重复请求索引。
3. GSC `/sitemap.xml` 仍显示 11-12 的“无法读取”旧状态；详情只有移除操作。公开侧
   sitemap、canonical 和抓取已核为正常，本次没有删除重提或修改正确配置。
4. Bing 已明确切换到 `zhurong2020.github.io/pyobfus/` 属性。IndexNow 页面仍为
   `Get Started`，但 GitHub IndexNow workflow 已成功；结论只能是“后台暂未展示记录”，
   不能写成零提交或失败。
5. TODO 的版本入口已改为 Core 0.15.0，并移除已经完成的 Windows Nuitka、CArchive 和
   Python 3.15 `.pyc` 项。

## 下一任务一：审阅 #241

#241 把 `actions/upload-artifact` 从 4.6.2 升到 7.0.2；其 CI 与 Dogfood 已成功，但这是
跨主版本升级，不得只凭绿灯合并。

审阅顺序：

1. 阅读 GitHub 官方 v7 release notes／迁移说明，核对 Dependabot 固定 SHA 确实对应
   v7.0.2。
2. 用 `rg -n "actions/upload-artifact|upload-artifact" .github scripts docs` 盘点全部
   使用点，重点核对三个被改 workflow、Windows Nuitka evidence、packaging 和任何下载端。
3. 核对 Node runtime、GitHub-hosted／self-hosted runner、GHES、hidden files、覆盖、压缩、
   retention、同名 artifact 与产物结构等兼容边界。
4. 读取 hosted logs，确认上传及后续消费步骤实际执行，而非仅 workflow 语法成功。
5. 给出“可合并／需修改／暂缓”的证据化结论。未获维护者明确授权不得 merge 或启用
   auto-merge。

## 下一任务二：Zenodo／CITATION

- 等待 Core 0.15.0 的新 Zenodo record；没有可靠结果时继续等待，不猜 record ID。
- record 出现后核对 concept DOI、version `v0.15.0`、publication date 和 GitHub tag／
  release 对应关系，再准备 `CITATION.cff` 同步。
- CITATION 更新单独经过检查、提交与托管 CI，不夹带其它产品改动。

## 下一任务三：Pro 客户升级通知

- 私有草稿在 `docs/internal/pro_customer_notice_0_15_0_DRAFT_2026-11-15.md`；先由维护者
  审阅，再按 Worker 许可记录核对收件人。
- 收件人和发送记录只进入 git-ignored `docs/internal/`；公共仓库不得写客户身份、邮箱、
  购买日期、金额、国家组合或 Stripe 对象 ID。
- 未获维护者明确批准不发送邮件。公共工程口径为：建议 CI 升级到 0.15.0、不要长期
  锁定旧版本、计划内换 key 至少提前 60 天通知，且信任新 key 的版本发布满 180 天后
  才允许切换。
- `ci-2026-11b` 仍不得配置到 Worker；Worker 继续使用 `ci-2026-11`。本任务不授权
  Worker 部署或 key 轮换。

## 周期任务

- 2026-12 第一周：月度搜索／AI 可见性观察。
- 约 2026-12-04：Core 0.12.0 T+30d 观察。
- 每周继续下载量、邮件、CI、备份和搜索后台观察；无新缺陷时不重复全量测试，也不因
  观察结果自动发版。
- 小型渠道试验与真实最小复现仍按 TODO 的触发条件推进，不用下载尖峰证明增长。

## 本交接不授权

- 不发布 Core、MCP、runtime、VS Code 或 Action 新版本。
- 不部署 Worker，不启用或轮换备用签发 key。
- 不删除重提 GSC sitemap，不把 Bing 未展示记录写成零提交或失败。
- 不猜 Zenodo record ID，不在公共仓库记录客户或业务机密。
- 不修改 GitHub ruleset。
- 不扩大 Windows Nuitka 为默认多平台矩阵；不启动资源保护、L3 方法覆盖、3.15t 或
  第二种冻结格式。
- 不合并 #241，除非审阅完成且维护者明确授权。

## 下一会话完成标准

报告文档提交 SHA、是否推送、`scripts/check.sh` 结果、#241 审阅结论、Zenodo 状态、
客户通知是否仍待审，以及最终工作树是否干净；若需要维护者决定，只提出一个具体动作。

## 接续检查点（同日第二会话）

维护者已要求依次推进并及时落盘。原五份文档已审阅，完整 `scripts/check.sh`
再次通过；提交前规定的各 pytest 根分别运行中，完成后记录结果并本地提交。
此时尚未 push、merge 或发送客户通知。

- #241 已核对官方 v6/v7 release notes、v7.0.2 tag/SHA 与 action.yml；实际变更是
  Dogfood/PDF 的 v7 → v7.0.2 和 Windows 验收的 v4.6.2 → 固定 v7.0.2。
  PR head `72623d7`，CI/CodeQL/Dogfood 均成功。Dogfood run `43765286482`
  两个上传步骤真实执行，artifact `14181908047` / `14181354974` 已存在；Lane C
  skipped；PDF 分支 push run `43765279318` 上传也成功，Windows 未执行。
  详细审阅见 [v7 审阅](UPLOAD_ARTIFACT_V7_REVIEW_2026-11-16.md)。
- Zenodo 已取得新证据：concept DOI 重定向到 record `24248676`，API 200，
  version `v0.15.0`、publication date `2026-11-15`、concept `20846053`，
  related identifier 指向 GitHub `tree/v0.15.0`。下一步单独同步 CITATION。
- 客户通知草稿已读，仍待维护者审阅；收件人未查询，未发送。

本轮提交前验证：Core 5152 passed / 56 skipped（正常 HOME），MCP 167、integration
371 passed / 10 skipped、runtime 24、基准 8；完整 `scripts/check.sh` 通过。
