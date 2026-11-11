# 2026-11-11 项目巡检与接续

Core 0.13.0 / MCP 0.3.17 / runtime 0.1.1 / 扩展 0.4.3 / Action v1.1.0 不变。本轮不发版、不部署许可服务。
Core 0.13.0 的发布、Zenodo／CITATION 和 Glama 接续已完成，不重新排入发布队列。

## 源码与托管检查

- 本地 main 从 `4983385` 快进到远端 `df58068`；新增 #218 Actions 依赖更新、#219 mypy 依赖范围调整。
- 最新 [CI](https://github.com/zhurong2020/pyobfus/actions/runs/42806534109) 成功；11-09 Packaging、Framework 与 Dogfood 均成功，11-10 22:53 UTC 许可证端点监控成功。
- 文档 PR #217 原 revision 的 CI／CodeQL 已通过。本轮补正其中“Google 处理延迟”的未经证实归因，并同步当前状态入口。
- 本地 `scripts/check.sh` 通过；各测试根独立运行：Core 5024 passed／55 skipped，MCP 167 passed，CLI integration 368 passed／10 skipped，runtime 24 passed，基准 8 passed。使用正常 HOME，未修改源码；扩展本轮无改动，未重复跑 Electron 测试。
- 11-08 历史失败日志中的解释器安装步骤返回 HTTP 504；后续定时 CI 已成功，不将环境下载失败登记为 Core 回归。

## 发布后观察与采用

下载快照采于 11-11 02:11 UTC，上游数据截至 11-10；复用 `scripts/download_snapshot.py --days 14`。

| 指标 | 本次 | 口径限制 |
|---|---:|---|
| Core 无镜像下载，7／30 天 | 1126／4361 | 包含发布、CI 和重复下载 |
| Core 安静日中位数，7／30 天 | 58／86 | 样本仅 3／9 天，排除发布日和次日仍不等于自然用户 |
| MCP 无镜像下载，7／30 天 | 94／928 | 本轮无 MCP 发布 |
| MCP 安静日中位数，7／30 天 | 10／12 | 样本 7／20 天 |
| Marketplace installs | 18 | updates 20 不算新增安装 |
| Open VSX downloads | 864 | 含重复获取，不与 installs 相加 |
| 可检索 Action 引用仓库 | 0 | 仅表示公开搜索可见性 |

Core 0.12.0 T+7d 已核查；发布窗口内另有 0.13.0，不能将滚动下载归因于单一版本。
本轮针对 11-06 后项目与支持方的邮件检索未发现新增客户支持请求；发现搜索索引通知并转入下节。
未发现报告不等于全部用户成功。支持与渠道原始材料只存私有 `docs/internal/operations-2026-11-11/`。

## 搜索可见度

本次复核已存在的 11-09 08:57 CST 只读盘点，不冒充 11-11 后台实时数据；原 JSON 在私有 workspace-meta。

- Google：文档站 sitemap 成功，发现 71 页，与收窄公开文档范围一致；落地页 sitemap 仍无法抓取。两个项目资源的索引汇总当时仍处理中。
- Bing：落地页 sitemap 成功、发现 2 页；文档站 sitemap 仍显示旧的 146 页，Site Explorer 主机范围显示 indexed 70／excluded 7／error 0。不能把该主机统计直接当成当前 sitemap 精确覆盖率。
- Bing IndexNow 字段为 `null`，表示当次未确认，不能写成零提交；AI Performance 显示零引用，数据窗口和新资源处理限制保留。最新 docs 通知日志显示无合格 URL、未发请求，workflow 成功不等于本次 API 提交成功，也不是提交故障。
- 11-09 收到落地页“重定向错误”通知，通知未提供示例 URL。11-11 公开 GET 检查：首页、中文页、sitemap 均直接 200；无末尾斜杠地址经一次 301 到首页；未复现循环。Googlebot UA 模拟请求不等于 Google 实际抓取结果。
- 域名根 robots.txt 返回 200，已列项目 sitemap；文件由个人站仓库维护，不改动本仓部署边界。

下一步必须取得 GSC 受影响 URL、上次抓取时间、抓取页／实时检查结果，再决定是否修 URL、服务器链或请求重新验证。
HTTP 200 不保证收录，见 [Google 官方说明](https://developers.google.com/crawling/docs/troubleshooting/http-status-codes)。

## 备份

11-09、11-10、11-11 日备服务日志均完成；11-11 云端镜像完成标记与日志一致。
抽核既有搜索基线与 F2 设计草稿：源文件、本地 11-11 快照、云端 `current/` 内容一致。
这不是完整恢复演练；本轮新生成材料晚于快照，须在下一次自然备份核对。
当前进程不能直接连接用户级 systemd bus，未据此判定定时器损坏，也未重启系统服务。

## 后续顺序

1. 搜索索引错误取得后台示例后继续定位；11-16 周检复看下载、邮件、CI、搜索及新证据备份包含性。
2. F2 已准备局部互操作证据（Python 3.12／3.15），尚不满足完整协议／库矩阵与迁移门槛；不擅自启用新的联网期限。
3. Pro／runtime 专利许可专业审阅包已准备；审阅前不修改生效许可。
4. 渠道规则初核与技术案例草稿已准备，账号条件和最终线程仍待核对；稿件只存私有目录，发帖另按明确授权执行，SO 仍须维护者从零撰写。
5. 12 月首周月度搜索／AI 观测，约 12-04 Core 0.12.0 T+30d；未到日期不预填完成。
6. Windows Nuitka 单组合保留需求门槛；Python 3.9 runner 替代方案在当前镜像退役前安排；插件目录锁等待支持方。

## 合并后收尾与维护核查

- 维护者批准后，#217 squash 合并为 `702d465`，本地 main 已同步，合并 tree 与已测候选一致。
- 合并后 [CI](https://github.com/zhurong2020/pyobfus/actions/runs/42947241080)、[CodeQL](https://github.com/zhurong2020/pyobfus/actions/runs/42947241045)、[Pages](https://github.com/zhurong2020/pyobfus/actions/runs/42947241207) 与 [IndexNow workflow](https://github.com/zhurong2020/pyobfus/actions/runs/42947241152) 均成功；workflow 成功仍不等于收录完成。
- 核对实际 lint 日志与全新 dev 环境，发现 mypy 2.4.1 对 `python_version=3.9` 输出“不支持”但 exit 0。维护分支恢复 `mypy>=1.19,<2.0`，并在 Dependabot 对该依赖排除 `>=2.0` 的版本更新，保留现有 Python 3.9 支持与类型目标。没有扩大一般扫描排除或改变 ruleset。
- 修复后的全新环境解析到 mypy 1.20.2，原目标诊断消失；`scripts/check.sh lint` 通过。仓库 venv 完整检查通过；四个测试根与基准再次独立运行，结果仍为 Core 5024／55 skipped、MCP 167、integration 368／10 skipped、runtime 24、benchmark 8。
- F2 的设计决策说明和新增非生产互通证据保存于私有 `docs/internal/release-next-2026-11-11/`。建议先 CI 后工作站，尚未改变授权策略、增加生产依赖或部署 Worker。
- 当前新增内容是开发检查兼容性维护，不能据此宣称新的用户保护功能已实现。Core 0.13.0 保持不变，尚无新的发版批准。

## F2 CI 首阶段候选（维护核查之后）

维护者批准“先 CI，后工作站”，实现见[草稿 #221](https://github.com/zhurong2020/pyobfus/pull/221)，依赖 #220。新增独立签发端点与 Pro 验签模块，保持旧 CI／工作站接口、缓存及设备行为；候选公钥表为空，Core 发布流程明确阻断未配置的信任表。

本地核心 5073 passed／55 skipped、MCP 167、integration 368／10 skipped、runtime 24、基准 8；Worker 单元 67（含末尾换行格式边界）。Python 3.15 与最低 cryptography 42 的针对性用例各 68 项通过。托管 [Worker CI](https://github.com/zhurong2020/pyobfus/actions/runs/42952684003) 的三格实际 workerd／Python 互通与 Worker 单元均成功。Core CI／CodeQL 在草稿改为目标 main 后另行验证，不借用 #220 的结果。

原始证据与接续保存于私有 `docs/internal/f2-ci-implementation-2026-11-11/`。没有配置生产 key、部署服务或发版；独立审阅、密钥发布／轮换计划和最终发布验收仍是后续门槛。

### 候选接续审阅

当前会话源码审阅发现，新签名端点复用的拒绝响应未统一禁止缓存，且 inactive 文本会回显存储状态。候选修订为新端点的拒绝响应添加 `Cache-Control: no-store`，并固定 inactive 错误文本；旧验证端点保持兼容。Worker 回归增加所有签名响应的缓存断言、私有状态不回显及存储／限流服务异常用例，70 项通过；Python 授权相关 68 项与完整 `scripts/check.sh` 通过。提交前各测试根独立复验：Core 5073 passed／55 skipped，MCP 167，integration 368 passed／10 skipped，runtime 24，基准 8。

密钥发布／轮换和回滚草案已补入私有接续。当前单 signer 协议切换 key 前须先分发新公钥并明确旧客户端升级窗口；仅保留服务端旧 key 不能让旧客户端自动信任新 key。此次源码审阅不代替独立外部审阅，先前托管结果也不覆盖此次修订；生产配置、合并和发布仍分别验收。

### 本次会话托管验收与接续

修订已提交并推送为 `74769cd`，其自身检查共 48 success／2 skipped；[Core CI](https://github.com/zhurong2020/pyobfus/actions/runs/42991395599)、[Worker CI](https://github.com/zhurong2020/pyobfus/actions/runs/42991395772)、[CodeQL](https://github.com/zhurong2020/pyobfus/actions/runs/42991395603)、[Packaging](https://github.com/zhurong2020/pyobfus/actions/runs/42991395576) 与 [Dogfood](https://github.com/zhurong2020/pyobfus/actions/runs/42991395594) 均成功。该结果覆盖本次代码修订，不代表后续文档提交或未来 release revision 的检查。

#220 源码审阅未见阻塞，42 success／1 skipped；维护者确认后已于 11-11 合并为 `2127c0c`，并同步进 #221。独立外部审阅与生产操作尚未执行；本次文档同步与分类提交不构成合并、部署或发版批准。完整接续见 [11-11 会话收尾](SESSION_CLOSEOUT_2026-11-11.md)。
