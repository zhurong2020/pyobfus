# 2026-11-03 项目检查与运营补核

本次未发布产品、部署服务、发送邮件或修改运行依赖。首次检查完成工程健康验收；
随后按维护者追问补核下载、Gmail、测试缓存原因与待办同步。不能把首次检查称为完整运营巡检。

## 工程状态

检查对象 main `b972b5e` 与远端一致，检查前工作区干净；开放 issue／PR 均为 0。
[最新 CI](https://github.com/zhurong2020/pyobfus/actions/runs/41543674921) 39 个 job 均成功，
[CodeQL](https://github.com/zhurong2020/pyobfus/actions/runs/41543674929) 成功。
最近扩展 CI、Dogfood 和许可端点监控也成功。

本地 WSL、仓库 `venv/`、Python 3.12.3、正常 HOME 下分别运行：

| 检查 | 结果 |
|---|---|
| `scripts/check.sh` | black、ruff、mypy、README 链接与严格文档构建通过 |
| `venv/bin/pytest tests/ -q` | 4977 passed / 55 skipped / 7 warnings；覆盖率 92% |
| `venv/bin/pytest pyobfus_mcp/tests/ -q` | 167 passed |
| `venv/bin/pytest integration_tests/ -q` | 368 passed / 10 skipped |
| `venv/bin/pytest pyobfus_runtime/tests/ -q` | 24 passed |
| 两个 `benchmarks/llm_resistance` CI 测试文件 | 8 passed |
| 扩展 lint、typecheck、pretest | 通过 |
| 扩展完整测试，显式指定仓库 Python | 53 passed，退出码 0 |

跨 Python／OS 与 MCP SDK 组合以 hosted CI 为证据，本机没有重复建立全部矩阵环境。
本地日志留在私有 `docs/internal/ops-2026-11-03/`。

## VS Code 下载原因与依赖告警

`.vscode-test.mjs` 未固定 `version`，工具默认跟随最新 stable。
原缓存为 1.141.0（10-07）和 1.143.1（10-27），本次下载的是 1.144.1；
三者均在 `vscode-extension/.vscode-test/`，合计约 3 GiB。
这是多个版本的测试 host 缓存，不是三个 Python 开发环境；根目录有 `venv/`、没有 `.venv/`。
CI 与本次本地测试均显式提供 `PYOBFUS_PYTHON_PATH`，未发现测试解释器指向遗漏。
保留最新 stable 验证，不为避免下载固定旧版，也未清理旧缓存。
依据：[官方测试说明](https://code.visualstudio.com/api/working-with-extensions/testing-extension)。

Dependabot #45 仍 open：扩展开发工具依赖 minimatch，
[上游公告](https://github.com/isaacs/minimatch/security/advisories/GHSA-g3hv-75wg-m249)
描述不可信 glob pattern 在 `optimizationLevel >= 2` 时可能放大 CPU／内存开销，修复版本 11.0.1。
本地依赖树含 3.1.5、9.0.9、10.2.6；GitHub／npm 的数据库范围为 `<11.0.1`，
上游描述具体指 10.2.6，不能声称所有旧主版本都已实际复现。
完整 npm audit 为 16 个 moderate 依赖条目，源于同一公告传播；`--omit=dev` 为 0。
不属于 Python Core/runtime 运行依赖。npm 报 `fixAvailable: false`，需单独兼容修复，
不使用未经验证的跨主版本全局 override。建议发布前优先处理，不自动阻塞 Core 0.12.0；
以上为首次核查快照；后续授权修复与验收见下节，远端告警关闭以合并后的扫描为准。

### 同日授权修复

维护者明确要求修复已发现问题、同步文档，为 11-04 发布做准备。
扩展改用 ESLint 10.14.0，移除旧版 ESLint 带入的 minimatch 3；TypeScript ESLint
现有 8.72.1 支持 ESLint 10，保留现有 lint 规则。Node 开发基线明确为 22.13 以上的 Node 22。

对 minimatch `>=9 <11.0.1` 使用 `^11.0.1` 的有界 override，锁定结果为 11.0.4。
复查 audit 另发现 glob 的
[取消后仍继续遍历漏洞](https://github.com/advisories/GHSA-3g3m-2fjr-6pw4)
（`GHSA-3g3m-2fjr-6pw4`），对 `>=9 <14.0.2` 使用 `^14.0.2`，锁定结果为 14.0.3。
这两项 override 只覆盖使用现代导出接口的依赖范围，不把旧 minimatch 3 强行替换为 11。
此前所有旧 minimatch 节点及 glob 10／13 节点均已从 lockfile 移除。

干净 `npm ci` 与完整 `npm audit` 均为零漏洞；lint、typecheck、扩展普通测试 53 项、
带 coverage 的 53 项测试均通过，覆盖了 c8／test-exclude 所在工具链。
`vsce package --no-dependencies` 成功生成 9 文件 VSIX；开发依赖没有进入产物。
扩展 CHANGELOG、开发说明、AGENTS、当前计划与 TODO 已同步。
这是安全维护，按 edition-boundary 的免费安全修复规则处理，没有增加能力、改变版别或收费边界。

Core／MCP／runtime 源码和版本未改；扩展版本仍为 0.4.3，不为开发依赖单独发布扩展。
Core 0.12.0 的版本号／横幅／CHANGELOG promotion 与 tag 留到 11-04 发布步骤。
本地完整检查与四个 Python 测试根在提交前另行复验，hosted CI 以本次修复 PR 为准。

## 下载与反馈

11-03 00:30 UTC 运行 `scripts/download_snapshot.py --days 30`，上游数据截至 11-01。

| 指标 | 本次 | 11-01 快照 |
|---|---:|---:|
| Core 30 天下载（无镜像） | 3862 | 3759 |
| Core 30 天安静日中位数／天数 | 56 / 8 | 53 / 8 |
| MCP 30 天下载（无镜像） | 923 | 940 |
| MCP 30 天安静日中位数／天数 | 12 / 20 | 13 / 20 |
| Marketplace installs | 16 | 16 |
| Open VSX downloads | 812 | 792 |
| GitHub 14 天 views／unique | 139 / 102 | 143 / 105 |

Core 最近 7 天 1088，只有两个安静日（86、169），不能据此认定持续自然增长。
窗口是滚动的，合计差值不等于新增用户；runtime 30 天 2795，仍受本仓 CI 安装影响。
Open VSX 含重复下载／爬虫，不与 Marketplace 相加。
Action 可见引用仓库数为 0，不等于真实采用数为 0。
来源返回项未见 DEV／LinkedIn，不能据此断言无内容流量。

Gmail 无日期限制候选检索及关键线程末条复核未发现新增待回复客户支持请求；
支持方等待、通知线程和其他账户事项的明细仅记于私有
`docs/internal/ops-2026-11-03/email-review.md`。未发信、改标签或归档；未核实实时交易或银行到账。

## 运维与后续

- [11-02 Guard](https://github.com/zhurong2020/workspace-meta/actions/runs/41407722228)
  的事件为 `schedule`、结果 success；实际开始为 07:39 UTC，晚于 cron 计划，非手动替代。
- 今日备份完成标记为 11-03 02:54:22；日志记录日备与冷归档上云成功，
  当日日备目录与对应本地凌晨许可导出存在。本轮只核新鲜度及成功日志，
  没有重做全量远端哈希比对或恢复演练；新生成的本次巡检文件等待下一轮自然备份。
- Core 0.12.0 尚未发布，MCP 0.3.17／runtime 0.1.1 不变；发布仍需维护者批准。
- 11-04 09:43 CST 后 DEV 一周复盘、约 11-05 晚 LinkedIn 一周复盘尚未到期。
  周度平台摘要不替代单篇帖子的一周验收。
- vbca 文档过滤继续等待自然事件，本轮未补验该跨仓事项；目录解锁继续等待支持方。
- 已同步当前计划、TODO 与 AGENTS 冷启动入口；历史 11-01 记录保持原日期语境。
