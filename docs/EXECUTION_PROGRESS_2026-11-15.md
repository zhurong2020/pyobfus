# 执行进度 — 2026-11-15

目标：按维护者确认的顺序推进前三项任务，并在每个阶段留下可供新会话接续的状态。
实现、发布、Worker 部署和客户通知仍是独立 gate，本轮未获自动授权。

## 进度表

| 顺序 | 任务 | 状态 | 证据／下一步 |
|---|---|---|---|
| 1 | 推送 2026-11-15 的 3 个文档提交 | **完成** | `8a22fa0`、`b248f65`、`00f144f` 已从本地 `main` 推送到 `origin/main`；pre-push `scripts/check.sh` 全部通过。远端提示维护者权限绕过等待 2 个必需检查的规则，push 成功；无发布或部署。 |
| 2 | 11-16 周检 | **提前检查完成（截至 11-15）** | 下载、备份、KV、CI、GSC 与收件箱已核；Bing 登录成功但默认属性不是 pyobfus，未把其它站点数据误记。11-16 若继续，仅需做日期性增量复核。 |
| 3 | 清理 TODO／ROADMAP 状态漂移 | **完成** | 当前版本、执行顺序和历史路线口径已统一到 0.14.0；`scripts/check.sh` 全部通过。只改文档，未发版。 |

## 任务 1 详情

- `8a22fa0 docs: record November competitive roadmap review`
- `b248f65 docs: record local pyobfus asset cleanup`
- `00f144f docs: sync November project status entries`
- 推送范围：`cde07eb..00f144f`，目标 `origin/main`。
- push 触发的 pre-push hook 运行完整 `scripts/check.sh`：black、ruff、mypy、JSON、
  Agent guide twins、README links 与 `mkdocs --strict` 全部通过。

## 任务 2 已完成的提前检查（2026-11-15）

### 下载与可见性（数据截止 2026-11-14）

- Core：近 7 天总计 550；1 个发布日、4 个安静日，安静日中位数 52；近 30 天
  10 个发布日、11 个安静日，中位数 78。
- MCP：近 7 天总计 55、7 个安静日，中位数 6；近 30 天 4 个发布日、22 个
  安静日，中位数 10。
- runtime：近 7 天中位数 75、近 30 天 86，但受本仓 CI 安装显著主导，不作为
  用户采用指标。
- VS Code Marketplace 0.4.3：18 installs、20 updates、0 ratings；Open VSX
  0.4.3：884 downloads、0 reviews（抓取次数，不能与 Marketplace 相加）。
- GitHub Action 公开代码搜索归因仍为 0；只量可见仓库，不等于采用量。
- GitHub 14 天 traffic：210 views／155 unique；aocr.org 36/36、vuink.com 24/24
  继续按机器／异常来源谨慎处理，真实可解释来源含 Google 15/13、GitHub 11/10、
  RTD 5/2、DuckDuckGo 3/3、PyPI 3/2、Bing 2/2。
- 结论：没有异常增长或回落信号；下载继续只作异常观察，不作为发版 gate。

### 工程与备份

- 推送后 `00f144f` 的 CI、CodeQL 与 IndexNow 均已成功；此前最近定时 CI 与许可
  端点监控也成功。
- 11-15 每日快照与周快照成功；Google Drive `current/` 镜像和 cold archive 同步
  成功，云端完成标记为 2026-11-15 10:02:00。
- 11-15 KV 导出成功：7 license、0 trial、0 other；本地轮转正常。
- `check_backup.sh` 打印“最新日期 2026-11-15”后提前结束，没有展示全部章节；
  底层日志、快照和云端完成标记均明确成功。脚本的提前退出作为非阻塞维护发现，
  本轮不顺带修改。

### 已登录后台核查（2026-11-15，只读）

- Gmail：Glama 0.14.0 的 build／release 通知正常；Claude Plugin Directory 支持线程
  最新状态仍为内部团队处理中、等待更新；近期未见新的客户支持或 0.6.1 通知回复。
  未发送、删除、标记或修改邮件。
- GSC（GitHub Pages 属性）：网页索引报告上次更新为 11-09，已编入索引 1 页、
  未编入 1 页；唯一实际计数的原因为“重定向错误”1，验证未启动。“已抓取—尚未编入
  索引”一行计数为 0。
- GSC sitemap：`/sitemap.xml` 的上次读取为 11-12，状态“无法抓取”，发现网页 0。
  这是新的非阻塞排查项；本轮没有重新提交 sitemap 或请求索引。
- Bing Webmaster 已登录，但首页默认选中的是其它站点属性。页面显示的 0 点击／6 展示
  不能归因于 pyobfus；本轮未切换或修改站点配置，因此 IndexNow 的 pyobfus 后台记录
  仍待下次可靠属性选择后只读复核，且 `null` 仍不得解释成零。
- 以上为 11-15 提前快照，不冒充 11-16 的日期性结果。11-16 如继续周检，只做增量：
  确认 GSC 数据是否刷新、选择正确 Bing 属性并核 IndexNow、查看是否有新邮件。

## 任务 3 收口

- `TODO.md` 已删除当前入口中的 0.13.0／11-11 状态漂移，当前版本改为 Core 0.14.0，
  当前执行顺序改为“周检增量 → 公开参考应用及单组合验收设计 → 单一冻结格式检查 →
  key 轮换接续 → 小型渠道／真实复现”。
- `ROADMAP.md` 顶部明确为历史论证文档，并指向 11-15 调研、TODO 与 CURRENT_PLAN；
  不再把 post-0.11 进度误作当前执行入口。
- 完整 `scripts/check.sh` 通过：black、ruff、mypy、JSON、Agent guide twins、README
  链接与 `mkdocs --strict` 均通过。

## 冷启动规则

新会话先读本文，再读 [当前计划](CURRENT_PLAN_ZH.md)、[TODO](TODO.md)、
[竞品与路线复核](COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md)和
[本地资产审计](LOCAL_ASSET_AUDIT_2026-11-15.md)。继续时从首个未完成任务开始，
不得重做已完成的清理、推送或调研。
