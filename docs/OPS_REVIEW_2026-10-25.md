# 2026-10-25 复盘与 10-26 巡检准备

查询时间：2026-10-25 08:01 UTC 起。下载数据覆盖至 10-24。
本轮由 Codex 独立处理；原始输出和草稿保存在 gitignored
`docs/internal/ops-2026-10-25/` 与 `docs/internal/content-2026-10/`。

## 采用情况

使用仓内 `scripts/download_snapshot.py --days 30`，排除镜像、发版日与次日：

| 指标 | 本次结果 | 解读 |
|---|---|---|
| Core 最近 30 天 | 3169 下载，10 个安静日，中位数 40/天 | 尚不能将总量增长归因于自然采用 |
| Core 最近 7 天 | 956 下载，只有 1 个安静日，值为 30 | 样本不足，不作为增长证据 |
| MCP 最近 30 天 | 653 下载，24 个安静日，中位数 8/天 | 继续观察用户反馈 |
| MCP 最近 7 天 | 256 下载，3 个安静日，中位数 3/天 | 不按短窗口调整产品方向 |
| runtime 最近 30 天 | 1868 下载 | 本仓 CI 会安装 runtime，不能当用户数 |
| VS Code Marketplace | 0.4.3，15 installs | 不与更新次数或 Open VSX 下载相加 |
| Open VSX | 0.4.3，762 downloads | 下载请求数，不是独立安装数 |
| Action 归因 | 0 个可见引用仓库 | 只反映公开代码可见性 |
| GitHub 最近 14 天 | 107 views / 56 unique | 来源列表未出现 dev.to 或 reddit |

GitHub 来源为 github.com 8/7、Google 5/5、pypi.org 5/3、Bing 3/2、RTD 2/2、
Pages 1/1（views/unique）。DEV 第 1 篇公开 API 返回 0 reactions、0 comments；
阅读数不在公开 API 中，需作者后台查看，不能推断为 0 阅读。

结论：继续按实际修复/功能进度安排发布，不恢复静默期或固定月度窗口。
内容方向尚缺有效来源信号；按原计划准备第二篇，发后再测，暂不增加投稿渠道。
本次没有新的外部客户需求证据，不据下载尖峰扩大功能范围。

公开入口：[PyPI 统计](https://pypistats.org/packages/pyobfus)、
[Marketplace](https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus)、
[Open VSX](https://open-vsx.org/extension/zhurong2020/pyobfus)、
[DEV 第一篇](https://dev.to/zhurong2020/cloudflare-blocked-urllibs-default-user-agent-and-it-took-me-two-months-to-notice-3k8e)。

## 服务、渠道与反馈

- PyPI 实时查询：Core 0.9.1、MCP 0.3.15、runtime 0.1.1；没有本轮新发版。
- 官方 MCP Registry：0.3.15、active、isLatest=true，与公开 MCP 包一致。
- 许可端点用仓内探针走真实客户端路径：服务端对不存在的探针 key 返回预期自身
  404，健康；没有读取客户 key 或触发真实激活。
- 10-22 之后的产品邮件增量检索，排除 GitHub/Glama 自动通知后无新增匹配。
  未发现新的客户报障、支持回信或目录解锁通知；不发送跟催。
- Glama 10-24 21:32 UTC 构建成功通知对应 test
  `01a16fd2-181a-7208-aab8-d84753dfec0e`，21:35 的平台 release label 为 0.9.2。
  这是平台标签，不是 PyPI Core/MCP 发版；邮件本身不能证明镜像的安装 pin 或握手
  版本已改变，未据此修改产品版本、触发构建或发布。

## 备份核查

只读执行现有备份检查：本机日备份目录为 10-25；pyobfus 许可快照 6 条、trial 0，
备份副本计数一致。最新许可导出日志为 10-24 23:02 UTC，即北京时间 10-25 07:02；
不能只因 UTC 日期不同就判定当天未备份。

云端 current 可读，39491 files / 1.85 GB；最后完整镜像成功标记仍是北京时间
10-24 09:19，history 最新目录同日。**本次没有证明 10-25 的云端镜像已成功**。
当前执行环境连接不到 systemd user bus，因此不能确认 timer/service 实时状态。
未改备份脚本、调度或云端文件；10-26 巡检应优先在正常 WSL 登录会话核实当天
镜像完成记录。完整状态属于跨项目运维，不将本机日备成功冒称云端全绿。

## DEV 第二篇准备

公开固定版本 Core 0.8.0、Ruff 0.17.1、Bandit SARIF 1.9.4 在新环境复跑七例：

| 案例 | 扫描退出码 | 扫描步骤/报告 |
|---|---|---|
| pyobfus clean | 0 | 步骤 0，报告 0 findings，可进入上传 |
| pyobfus high | 1 | 步骤 0，报告 1 finding，最终 gate 1 |
| pyobfus missing | 2 | 步骤 2，无报告，不上传 |
| Bandit missing path | 0 | 空 SARIF；不能据此声称扫描了源码 |
| Bandit missing config | 2 | 工具错误 |
| Ruff missing path + exit-zero | 0 | E902 诊断 |
| Ruff invalid config | 2 | 工具错误 |

再次核对 [GitHub shell](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell)、
[upload-sarif v4](https://github.com/github/codeql-action/blob/v4/upload-sarif/action.yml)、
[Ruff 退出码](https://docs.astral.sh/ruff/linter/#exit-codes)。
未实测 GitHub 服务端 SARIF ingestion，不将本地 upload-ready 模拟称为上传验收。

草稿保留 `published: false`，固定版本不替换为未发布代码；收窄退出码泛化表述，
保留 AI 辅助说明。发布步骤已改为维护者审阅、预览和亲自发布，不依赖其他 AI 代理
或第三方检测器。候选日期仍为 10-27 21:00 北京时间；未投稿、未创建外部草稿、
未发 X，也未将未公开正文提交第三方。

## 10-26 的增量巡检入口

1. 在正常 WSL 登录会话核实 systemd 和当天云端镜像；检查此处的日期而非只看文件数。
2. 看新客户来信、真实购买和 CI；只有出现新购买才核验付款/发号/投递，不重放事件。
3. 更新下载与来源快照，分开发版日、次日和内容投放；不因总量尖峰认定增长。
4. 维护者可补 DEV 作者后台阅读数；10-27 发布前完成最后署名和预览确认。

本次已完成能在 10-25 执行的复盘与准备，不声称完成未来日期的增量状态检查。
