# 2026-11-01 后续执行

维护者授权依次推进现有待办；本轮无产品发布。

## 同日追加维护（按序执行）

1. cardiac-shared：隔离测试环境对照 SimpleITK 2.5.2／2.5.7；修订旧行为假设，
   加入错误方向／原点的主动注入回归。旧版 20 项定向通过；新版 strict 全套
   1163 passed / 8 user-systemd-scope skips；消费者 69 passed / 1 optional-module skip。
   [PR #60](https://github.com/zhurong2020/cardiac-shared/pull/60) 已提交，
   远端 3.10／3.12／lint 均通过（41266199969），wheel-smoke 按预期跳过。
   PR 精简矩阵已实跑验收；独立审阅／合并仍未执行。
2. 采用入口：GitHub Pages 英文／中文首页及简版 llms 均 HTTP 200，并与源码字节一致；
   两组本地 llms 镜像也一致。Pages 仅部署简版，完整版 URL 的 404 符合配置。
   RTD 首页、llms 与公开构建 API 返回 HTTP 429、cf-mitigated: challenge；
   不能据此判断部署失败，仍待可访问环境复核。
   GitHub 远端 README 中英文、首页源码、llms 简版／完整版与本地也一致。
3. 其他私有 CI：findata 最近阻塞运行重跑成功（40083082326）；
   cardiac-manuscripts 当前 main 手动参考文献检查成功（41265887446）。
   llm-enrichment 重跑发现 openpyxl 缺失及 Python 3.10 UTC Z 时间解析差异，
   小范围修复已提交 [PR #1](https://github.com/zhurong2020/llm-enrichment/pull/1)，
   本地 676 通过、远端 3.10／3.12 均通过（41266043868）。未部署服务器或更新页面。
4. Action：审阅既有 README 分支，Ruff／mypy／YAML 本地通过，
   已提交 [PR #2](https://github.com/zhurong2020/pyobfus-action/pull/2)；
   八项 hosted real-contract 检查全通过（41265932903）。未合并、发版或移动 tag。
5. 备份：当日日备与许可导出一致，日备到云端的许可／法律资料校验通过。
   今日任务仍在复制月度快照，完整云端标记仍为昨日；内部文档定向校验
   180 秒超时后改用远端 MD5 清单完成逐文件比较，确认仍有缺失／差异，
   详情在私有 backup-docs-comparison-20261101.json。待自然日备完成后复验；
   同内容重复路径已保留，未清理云端文件。暂不声称本日日备已完整上云。
   详细日志只留私有 docs/internal，不重复启动备份或修改调度。

本轮维护文档 scripts/check.sh 与 diff-check 通过；相关仓库工作分支已推送。
两个临时 SimpleITK 环境已清理；生产环境复核仍为 2.5.2／NumPy 1.26.4。

### 同日立即复核

- RTD 首页／llms 普通请求和 Mozilla 标识请求仍为 429。检索入口能读取两天前的
  首页抓取，不能作为当前部署或 llms 字节一致性的证据；最新内容核验仍未闭合。
- 备份月快照复制进程仍存在，五秒采样有 CPU 活动，尚未进入云端同步；
  完整云端标记仍为 10-31。刷新远端 MD5 清单并复核已知差异，结果未变；
  明细保存在私有 backup-recheck-20261101.json。不终止复制或重复启动备份。
- PR 60／1／2 的当前状态均为 OPEN、非 draft、MERGEABLE；应运行检查全部成功，
  cardiac-shared wheel-smoke 按配置跳过。正式审阅结论为空；本轮未合并 PR。

## CI 与同步

- 私有 Actions 已恢复启动：workspace-meta Guard 重跑成功，Credential scan 6 秒。
  [运行记录](https://github.com/zhurong2020/workspace-meta/actions/runs/40527081904)。
- 账单 API 因当前令牌缺少 user scope 无法读取；恢复启动不等于已核实剩余额度。
- fetch 后 workspace-meta、cardiac-shared、vbca 的 main 均与 origin/main
  一致且干净，没有旧交接所称的积压提交需要推送。
- 已核对线上节流配置：Guard 每周一／PR／手动；cardiac-shared main
  只跑 3.12 和 lint；vbca 文档过滤、并发取消和超时已配置。
- 已重跑最近被额度阻塞的 cardiac-shared、vbca 运行；vbca 的 3.10／3.12
  两项通过（[运行记录](https://github.com/zhurong2020/vbca/actions/runs/40814614631)）；
  cardiac-shared 的 lint 通过，3.12 测试为 4 failed / 1164 passed / 1 skipped
  （[运行记录](https://github.com/zhurong2020/cardiac-shared/actions/runs/40814608796)）。
  四项均断言旧版 SimpleITK 负切片间距行为，与该仓 10-31 已登记的上游修复一致；
  属于依赖行为兼容待办，已在对应仓库登记，不属于账单限制或 pyobfus 产品缺陷。
- PR 精简矩阵已在修复 PR 验收；vbca 文档过滤的实际触发与 11-02 定时 Guard 仍待自然事件验收，
  不制造提交或 PR 消耗额度。
- 全仓只读扫描仍看到其他项目历史额度失败；不批量重跑历史发布／部署。

## 反馈与采用

- GitHub 当前无开放 issue/PR；最新 main CI、CodeQL 和许可端点监控成功。
- 维护者已提供 LinkedIn 帖子页与 DEV Dashboard，当前快照已补记；
  精确首日采样已错过，不回填为首日或一周数据。指标与比较见私有
  `docs/internal/content-2026-10/social-review-2026-10-29.md`。
- DEV 一周复盘保持 11-04 09:43 CST 后，LinkedIn 一周复盘保持约 11-05 晚。
- 托管 llms.txt 请求返回 HTTP 429，暂不能证明与源码同步。
- 新购买后的发号与 Customer 核验仍为事件触发待办；邮件查询未提供新付款证据，
  不能据此断言没有新购买。业务明细继续只留私有记录。
- Anthropic／Claude 相关邮件查询未见 10-29 之后新消息，目录解锁继续等待。
- 本地许可备份目录存在当日导出 `kv_backup_20261101T015249Z`；只确认导出目录，
  本轮未读取客户记录或验证云端镜像完整性。
- scripts/check.sh、git diff --check 通过；workspace-meta 本地凭据扫描
  （含最近八天新增历史）通过。本轮仅记录与定向 CI 验收，不重跑产品全量测试。

## 同日接续（协调会话，北京时间 11:00 前后）

1. **三个维护 PR 实质审阅**（Claude 审阅 + 每个 PR 一次独立的无头 Codex 只读审阅；三分支 base 均等于当前 main，无漂移）。
   - [cardiac-shared #60](https://github.com/zhurong2020/cardiac-shared/pull/60)：Codex 1 项 must-fix 成立——
     版本判断把仍受影响的 3.0.0b1 当成已修复，同时把正确的 2.3.x 当成受影响。按该仓「审阅即修复」授权改为只刻画
     2.x 稳定线（受影响 2.4.0 ≤ v < 2.5.7，3.x 预发布 skip），`b08ad53`；SimpleITK 2.5.2／2.5.6／2.5.7
     下两个几何测试文件各 20 passed，PR CI 3.10／3.12／lint 通过；其余要点（输出几何断言未放宽、注入错误
     方向／原点走真实修复分支、体素逐元素不变、verifier 仍拒绝翻转仿射）经核成立。已合并 `f4f5f50`，状态记录 `6659cb7`。
   - [llm-enrichment #1](https://github.com/zhurong2020/llm-enrichment/pull/1)：Codex 结论为批准，附 2 条小意见，均已采纳——
     只把**末尾** `Z` 换成 `+00:00`（`_utc_iso`）；补充「新快照带 Z」的回归（较旧被拒、较新或带小数秒较新放行）。
     3.12 全套 679 passed；3 个新比较在 Python 3.10 直接核对（3.10 不接受一位小数秒，测试改用 6 位）。
     旧快照拒绝逻辑不变；未部署、未更新页面。已合并 `ce20bb2`，记录 `6d0f485`。
   - [pyobfus-action #2](https://github.com/zhurong2020/pyobfus-action/pull/2)：Codex 1 项 must-fix 成立——README
     「Source, findings and mappings stay on the runner」不准确：`run_pyobfus.py` 把最多 50 行发现
     （严重度、类别、`file:line`、消息）写入 `GITHUB_STEP_SUMMARY`。修订 `bb60129`；负责人当日明确授权后推送，
     八项 hosted checks 全部通过，按该仓惯例 squash 合并为 `24f3328`（03:10 UTC）。版本区间与 install/offline
     说法与代码一致。v1 tag 仍指 `284802e`（未移动），Marketplace 未动，未发版。
2. **Read the Docs 已核实**：本机仍被 Cloudflare challenge（429），改从 arong-vps 出口各请求一次，均 HTTP 200。
   公开 builds API：最新构建 `35553414` 成功，commit `d2f0685` = 当时 origin/main，02:55 UTC 完成。
   `llms.txt`（6,041 B）与 `llms-full.txt`（15,791 B）与 `docs/` 源码逐字节一致；首页正文逐句对照
   `docs/index.md` 均在（唯一差异为行内代码渲染空格）。本机 429 是访问拦截，不是部署问题。
3. **备份已完成并复验通过**：今日日备在推进而非停滞（月／周快照 09:52:43 已记 OK，之后是保留期清理、整树 `du`、
   文件计数，再进入云端同步）；未发信号、未重启。云端同步 11:30:01 完成，标记更新为 `2026-11-01 11:30:01`，
   脚本退出码 0，日志两段云端均 OK（变更旧版进 `history/2026-11-01_111258`）。
   复验：内部文档当日日备 vs `gdrive:backups/wsl/current/` 远端 MD5 清单逐文件比较——本地 7,554 个文件全部一致，
   缺失 0、不一致 0、无哈希 0；此前的 13 个缺失与 3 个内容差异已全部消除（当时云端仍是 10-31 的日备，差异来自尚未同步）。
   云端另有 2 个本地没有的 `.pyc` 缓存文件，位于 rclone 报「重复目录、已忽略」的同一路径（Drive 同名目录），不影响备份，
   按约定不清理。许可与法律资料此前已校验一致。明细只在私有 `docs/internal/backup-docs-postsync-comparison-20261101.json`。
4. **日期项**：11-02 定时 Guard（周一 01:17 UTC = 北京 09:17）、11-04 09:43 后 DEV 一周、约 11-05 晚 LinkedIn 一周，今日均不到期，未执行。


## 状态核对与文档同步（同日后续）

- 通过 GitHub API 再核三个 PR：cardiac-shared #60、llm-enrichment #1、
  pyobfus-action #2 均为 MERGED，合并提交与「同日接续」一致；Action v1
  仍为 `284802e`。pyobfus main `d84b4a8` 与 origin/main 同步，开放 issue／PR 均为 0，
  对应 CI 与 CodeQL 成功。本次未重跑产品全量测试。
- RTD 公开 builds API 最新构建 `35553790` 成功，commit `d84b4a8`。
  arong-vps 普通请求 llms 返回 403，Mozilla 标识请求首页及两个 llms 均 200；
  `llms.txt`／`llms-full.txt` SHA-256 分别为
  `57dd77af6e3b9152360f90da4dc37bbd39e2a3f1df4449c297fcf11d1f265a7e`／
  `c91fbff0cc42b9407115f4327617dbca6073ef61f9f2631ab54f45afa82a855a`，与本地源码一致。
- 备份完成标记仍为 11-01 11:30:01，日志确认 current 与冷归档两段云端同步完成。
- 已统一 AGENTS、当前计划、TODO、交接和冷启动 prompt 的当前状态；接续前证据明确标为历史。
- 远端 Guard cron 确认为 `17 1 * * 1`，11-02 北京时间 09:17 后验收自然触发；
  11-04 09:43 后 DEV、约 11-05 晚 LinkedIn 仍未到期，不提前采样或手动触发替代。
- 刷新云端 MD5 清单后重新读取日备并逐文件核验：7,554 个普通文件全部一致，
  缺失 0、内容差异 0、无哈希 0；另有 3 个解释器符号链接，按备份脚本
  `--skip-links` 口径排除。云端仍多 2 个缓存文件，未清理。
  私有明细：`docs/internal/backup-docs-status-recheck-20261101.json`。
- 状态核对时 `scripts/check.sh` 与 `git diff --check` 通过；仅更新状态文档。
  后续按维护状态与邮件／下载观察两类提交；无产品发版，私有原始资料不进入提交。

## 邮件与下载量补核（同日）

- 邮件按项目 inbox 流程做无日期限制候选检索，并核对相关线程最后消息；
  未发现待维护者回复的客户支持请求。目录锁仍待支持方，无需补材料。
  未发送或改动邮件，未核查实时交易；私有明细见 `docs/internal/ops-2026-11-01/email-review.md`。
- 运行 `venv/bin/python scripts/download_snapshot.py --days 30`，数据截至 10-31：
  Core 30 天 3,759，安静日 8 个、中位数 53；近 7 天仅 1 个安静日（86），样本不足。
  MCP 30 天 940，安静日 20 个、中位数 13；近 7 天安静日 3 个、中位数 13。
  runtime 30 天 2,689，受本仓 CI 安装显著影响，不作为用户数。
- VS Code Marketplace 0.4.3 为 16 installs；Open VSX 792 downloads，口径不同不相加。
  GitHub 14 天 views 143／unique 105；返回来源中未见 dev.to／reddit／chatgpt.com，
  不能据此断言这些渠道完全没有流量。Action 可见代码引用仓库数 0，不等于真实采用数。
- Core 安静日中位数较 10-25 快照的 40 高，但窗口与样本均变化，尚不足认定持续自然增长。
  原始快照保存在 `docs/internal/ops-2026-11-01/download_snapshot.txt`；下次按周一节奏观察。

### 分类提交验收

- 维护状态与交接同步已提交为 `134e5df`；邮件／下载观察作为独立文档提交。
- 本次提交前使用正常 HOME、仓库 `venv/`，四个 pytest 根各自独立调用：
  Core 4,687 passed / 55 skipped（7 warnings），MCP 159 passed，
  CLI integration 368 passed / 10 skipped，runtime 24 passed。
- `scripts/check.sh`、暂存区与工作区 diff-check、提交钩子扫描通过。
  仅文档变动，无产品版本调整；私有邮件／快照／备份明细仍被 Git 忽略。
  本轮仅本地提交，远端 CI 与 RTD 的 `d84b4a8` 核验是提交前快照，未推送。
