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
- 许可状态导出成功，本地轮转正常。（私有记录：`docs/internal/archive/PUBLIC_DOCS_PRIVACY_MOVE_2026-11-16.md#m01`。）
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

## 后续顺序推进（同日）

1. **GSC 公开侧诊断完成**：11-15 以 Googlebot UA 复核首页与 `/zh-cn/` 为 200，
   `/zh-cn` 仅一次 301 到带斜杠地址；`/sitemap.xml` 返回 200、`application/xml`，
   只列两个正确 canonical URL；根 `robots.txt` 也列出项目 sitemap。项目侧未发现循环、
   多跳、阻止抓取或错误 URL，不为迎合历史 GSC 状态修改正确配置。后续只观察 Google
   重新处理，并以 `/zh-cn/` 的实时检查为准。
2. **公开交付参考应用验收合同完成**：范围、Community／Pro 边界、目录隔离、正常／
   负例、证据、停止条件和实施顺序见
   [参考应用验收合同](DELIVERY_REFERENCE_APP_ACCEPTANCE_2026-11-15.md)。应用实现与 Windows
   Nuitka 实跑尚未开始，不预填通过。
3. **公开参考应用第一阶段完成**：新增 `examples/delivery_reference/`，包含自包含多模块
   storefront、包资源、固定 allowlist 动态插件、稳定业务异常、Community 配置和不含
   key 的应用 key-provider 示例；`integration_tests/test_examples.py` 新增原文与 Community
   保护目录契约测试。定向测试 5 项通过，完整 `scripts/check.sh` 通过。Pro L3、冻结交付
   与 Windows Nuitka 仍未执行。
4. **Community 证据补全**：参考应用测试现同时验证保护后异常、私有 mapping 的 JSON
   unmap 结果及带 build report／provenance 的 `--check-delivery`。一次测试设计偏差曾把
   原始 `data/__init__.py` 复制进保护树，交付检查正确报告 medium；改为只复制文档约定的
   `label.txt` 后状态为 ok。该过程证明检查没有把未记录 Python 文件误报为 clean。
5. **Windows Nuitka 环境门槛 blocked**：本机原生 Windows 仅有 CPython 3.11，未发现
   CPython 3.12、Nuitka、`cl.exe` 或 Visual Studio 2022 工具链。没有自动安装、没有改用
   3.11 冒充目标组合；Windows x64／CPython 3.12／Nuitka standalone 继续保持未执行。

## 冷启动规则

新会话先读本文，再读 [当前计划](CURRENT_PLAN_ZH.md)、[TODO](TODO.md)、
[竞品与路线复核](COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md)和
[本地资产审计](LOCAL_ASSET_AUDIT_2026-11-15.md)。继续时从首个未完成任务开始，
不得重做已完成的清理、推送或调研。
