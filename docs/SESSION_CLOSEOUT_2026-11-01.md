# 2026-11-01 会话交接

冷启动：本文件 → [本轮执行](EXECUTION_PROGRESS_2026-11-01.md) →
[当前计划](CURRENT_PLAN_ZH.md) → [TODO](TODO.md) → 各仓实际 Git／PR 状态。
日期均为北京时间。此处是会话末快照，下次必须重新读取外部状态。
复制用 [冷启动 prompt](COLD_START_PROMPT_2026-11-01.md)。

> **同日接续已完成（见[本轮执行](EXECUTION_PROGRESS_2026-11-01.md)「同日接续」节）**：接续一三个 PR 均已审阅、修订并合并（cardiac-shared #60 `f4f5f50`、llm-enrichment #1 `ce20bb2`、pyobfus-action #2 `24f3328`，后者经负责人授权；v1 未动）；接续二 RTD 最新构建 `d2f0685` 成功，llms 两个文件逐字节一致；接续三 11-01 日备 11:30 完成上云，内部文档 7,554 个文件逐一 MD5 一致。仍待：11-02 定时 Guard、11-04 DEV、约 11-05 LinkedIn。

## 已完成与边界

- Core 0.11.1 / MCP 0.3.17 / runtime 0.1.1 不变，本次无产品发版、服务器部署或 tag 移动。
- 私有 Actions 可启动：workspace-meta Guard、vbca、findata、cardiac-manuscripts
  恢复检查通过。账单 API 缺 user scope，剩余分钟数未核实，不为此扩权。
- 三个维护 PR 已提交且检查通过，均 OPEN／非 draft／MERGEABLE，正式审阅结论为空。
  已通过的测试不等于独立审阅或合并；本轮未执行合并。
- GitHub Pages 英文／中文首页与简版 llms 字节匹配，远端 README、文档首页源码、
  llms 简版／完整版与 checkout 一致。Pages 没有部署完整版 llms，不能把该 URL 的 404 当故障。
- LinkedIn／DEV 当前快照已记录，不是精确首日／一周数据；业务指标仅在私有
  `docs/internal/content-2026-10/social-review-2026-10-29.md`。
- 临时 SimpleITK 环境已删除。生产研究环境仍是 SimpleITK 2.5.2、NumPy 1.26.4。

## 接续一：三个 PR 的实质审阅

| 仓库／PR | 本地分支／提交 | 内容与已通过的验证 |
|---|---|---|
| [cardiac-shared #60](https://github.com/zhurong2020/cardiac-shared/pull/60) | `fix/simpleitk-257-test-compat` / `c57f018` | 仅测试／文档兼容 SimpleITK 2.5.7；旧版 20 定向通过，新版 strict 1163 passed / 8 user-systemd-scope skips，VBCA 69 passed / 1 TotalSegmentator skip；远端 3.10／3.12／lint 成功，wheel-smoke 按配置跳过。运行 `41266199969` |
| [llm-enrichment #1](https://github.com/zhurong2020/llm-enrichment/pull/1) | `fix/ci-runtime-dependencies` / `5643118` | CI 补 openpyxl 3.1.5；比较时间前将 UTC Z 转为 +00:00；三个时区表示的回归。本地 676 passed，远端 3.10／3.12 成功。运行 `41266043868` |
| [pyobfus-action #2](https://github.com/zhurong2020/pyobfus-action/pull/2) | `docs/core-0.10.0-runtime-guide` / `5c6fa1c` | README 对齐 runtime>=0.1.1,<1 和实际网络行为；Ruff／mypy／YAML、本机与三平台真实契约等八项 hosted checks 成功。运行 `41265932903` |

先读各仓 AGENTS.md／现行约定，再取最新 diff／checks／reviews／base 漂移。
cardiac-shared 的审阅范围与复制用 prompt 在
`docs/reviews/SIMPLEITK257_TEST_COMPAT_HANDOFF.md`，重点确认主动注入错误几何仍覆盖
真正防御路径、体素未变、输出位置和 verifier 断言未被放宽。
llm-enrichment 审查旧快照拒绝逻辑与 UTC offset 等价性；不得以运行测试为名更新线上页面。
Action 只审文档与真实契约，不移动 v1 或发 Marketplace。
按各仓既有流程收口审阅；合并／发布按届时有效授权执行，不能把本次交接当作新增授权。

## 接续二：Read the Docs 最新部署核验

- `https://pyobfus.readthedocs.io/en/latest/`、`.../llms.txt` 和公开 builds API
  本机返回 HTTP 429，响应标记 `cf-mitigated: challenge`；普通／Mozilla 请求均如此。
- 检索工具可以读取标注两天前的首页抓取，不能证明最新部署或 llms 字节匹配。
- 下一步通过正常浏览器或可用的官方部署状态核验实际构建 commit／时间；
  入口可访问后对照 `docs/index.md`、`docs/llms.txt`／`docs/llms-full.txt`。
  区分访问 challenge 与构建失败，不反复请求、不改产品代码迁就访问问题。

## 接续三：备份完成后的复验

- 许可导出与当日日备一致；当日日备到云端的许可／法律资料校验通过。
- 内部文档当日日备与云端 MD5 清单完整比较后，仍有缺失／内容差异；立即刷新远端
  清单再核已知差异，结果未变。具体清单、数量与日志只在私有 `docs/internal/backup-*20261101*`。
- 会话末完整云端标记为 `2026-10-31 09:51:25`。
  11-01 自然备份进程仍在月度快照复制阶段；`cp` 五秒采样有 CPU 活动，尚未进入云端同步。
  当时 PID 1554／26276 只作历史证据，下次按完整命令／父子关系重新识别，不能据此发信号。
- 先读备份 SoT：`cardiac-ml-research/docs/technical/SYSTEM_BACKUP_OVERVIEW_20260426.md`
  （后续日期补充优先），再看实际 `~/scripts/wsl_daily_backup.sh`／`check_backup.sh`、
  `~/scripts/logs/wsl_backup.log`、`wsl_backup_cloud_last_ok` 和进程。
- 日备根：`/mnt/c/Users/wuxia/OneDrive/Documents/wsl-backup/daily/<日期>/`；
  云端 `gdrive:backups/wsl/current/`。路径虽然带 OneDrive，该本机路径不靠 OneDrive 上传。
- 当前会话无法连接 user systemd bus；空字段不代表 timer 从未成功，需核对实际登录环境。
- 自然备份完成后再校验；若确有停滞，先取 I/O／进程证据并做最小范围诊断。
  不重复启动整套备份，不盲目终止复制，不删除重复路径／历史云副本，不公开客户数据。

## 日期／事件任务

- 11-02：自然定时 Guard 是否成功；vbca 文档过滤仍等自然触发验证，不制造空提交。
- 11-04 09:43 后：DEV 一周观察；11-05 晚左右：LinkedIn 一周观察。
- 下一笔真实购买：核验发号、激活与 Customer 资料；目录解锁继续等待支持方。
- 不因 CI 已恢复而重跑所有历史运行／旧发布／部署；不因文档修订而发新版本。

## 工作区与证据

- 主仓 `~/projects/pyobfus`，main 会话末代码／记录基线 `b439dcd`
  （交接提交在此之后）；相关三仓在上表工作分支，均已推送且干净。
- workspace-meta main 已同步；本轮恢复手册为
  `archives/CI_RESUME_AFTER_2026-11-01.md`。不覆盖其他会话的新提交。
- 日常源码只在 WSL `~/projects/` 操作；pro-dev 是只读历史仓。
- `/tmp` 测试日志与发行核查缓存均为临时证据；持久结论在本文件／执行记录／PR。
- 本轮源仓 `scripts/check.sh` 与 diff-check 通过，未重复执行无关产品全量测试。
