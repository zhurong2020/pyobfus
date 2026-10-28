# DEV 第二篇：可复现案例与采用观察

日期：2026-10-22。状态：已准备、未投稿。保留原主题 **Stop writing `|| true` before your SARIF upload**，不改成未发布功能宣传；对不采用 pyobfus 的读者，退出码、报告新鲜度和先上传后 gate 的通用模式仍有用。稿件与发布清单存于本地忽略目录 `docs/internal/content-2026-10/`，由维护者最终审阅。

2026-10-28 后续：维护者已将标题改为无反引号形式，并在
[DEV 发布](https://dev.to/zhurong2020/stop-writing-true-before-your-sarif-upload-16ih)。
正式正文使用公开 Core 0.10.0；七个案例在隔离环境重跑，证据保存于
`docs/internal/adoption-2026-10-28/`。本页以下 0.8.0 结果是 10-22
的历史验证，不冒充正式正文版本；发布记录见 `CURRENT_PLAN_ZH.md`。
同日维护者补上[封面](assets/dev-sarif-workflow-cover.png)，
并在 [X 分享](https://x.com/zhurong0525/status/2115269885244944746)；
素材归档与后续观察见[10-28 会话收尾](SESSION_CLOSEOUT_2026-10-28.md)。

## 实测范围

Python 3.12 / Linux；隔离 HOME；构建环境使用公开 PyPI **pyobfus 0.8.0**，不是本轮工作树 wheel。每次使用新报告目录。另建环境安装 Ruff 0.17.1 和 `bandit[sarif]==1.9.4`。没有扫描用户源码，没有启动 Pro 试用。

| 合成案例 | scanner 退出码 | Bash scan 步骤 | 可继续上传 | 模拟最终 gate |
|---|---|---|---|---|
| `def total(value): return value + 2` | 0 | 0 | 是，SARIF 0 results | 0 |
| `result = eval("1 + 2")` | 1 | 0 | 是，SARIF 1 result | 1 |
| 不存在的 `missing.py` | 2 | 2 | 否，无报告 | 2 |

使用 `bash --noprofile --norc -eo pipefail` 执行：在 scanner 调用前临时 `set +e`，读出 `$?` 后恢复 `set -e`；仅接受 0/1，非空报告成功后才写上传路径到 GITHUB_OUTPUT；最后按 findings 状态 gate。新建临时目录失败也须立即失败，不放到 `set +e` 范围内。这里只验证本地上传前条件及模拟 gate，**没有执行 GitHub 上传、权限或服务端接收**。

复现输入无需下载工程：在新临时目录建 venv，安装 `pyobfus==0.8.0`；创建上表 clean.py / high.py，分别执行 `python -m pyobfus --check <file> --offline --sarif <fresh-dir>/results.sarif --json`。missing.py 不创建。完整可复制命令已放进草稿。

补充复测：Bandit 1.9.4 对缺失路径退出 0、写 0 results 的 SARIF，缺失 `-c` 配置退出 2；Ruff 0.17.1 缺失路径配 `--exit-zero` 退出 0（E902），无效 TOML 配置退出 2。因此非空 SARIF 和退出码都不能证明扫描过源文件；有扫描文件数时还应校验覆盖范围。

## 草稿修订

- 固定公开 0.8.0，加入三类真实输入、预期结果与复现命令。
- 通用 Bash 示例输出动态报告路径，避免复用旧文件。
- 区分 composite action 自身不上传与整个上传工作流的权限要求。
- 将 AI 辅助与本地验证范围写实，不声称维护者已亲自运行或本轮已验证 GitHub ingestion。
- 不引入下一版本 mapping / Pro 设计宣传，不自动发布。原拟 10-27 时间仅供维护者选择。

[GitHub shell 说明](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell)、[upload-sarif 源码](https://github.com/github/codeql-action/blob/v4/src/upload-lib.ts)及 [Ruff 退出码](https://docs.astral.sh/ruff/linter/#exit-codes)于本日复核；工具特例以上述固定版本实测为准。

## 采用观察

发布后记录文章 URL、日期和使用版本。约三天及次周巡检分别看 DEV 浏览／反应／具体问题、GitHub dev.to 来源、Action 引用及真实使用反馈；下载按发布日／次日／安静日拆分，不把总下载数当新增客户，也不把文章后波动当因果证据。不添加追踪标识或改遥测。
