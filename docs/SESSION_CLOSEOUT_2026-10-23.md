# Session 交接：PR #112 合并，Core 0.9.0 与 MCP 0.3.15 发布

日期：2026-10-23。冷启动先读本文，再读 `CURRENT_PLAN_ZH.md` 顶部和 `TODO.md`。

## 同日后续 session：视频原创保护调研交接

维护者在发版交接之后提出视频保护讨论，并在关闭本次 session 前要求核对文档同步。本节补记后续结果；下文发版过程保留为历史快照。

- **需求范围**：自己制作、公开上传 YouTube／B 站的视频，关注搬运后的保护；当前不以自有播放器、付费课程或离线 DRM 为目标。
- **结论**：通用上传前加密不能保证公开视频正常播放且搬运副本自动失效。可行方向是来源材料、水印／内容指纹、人工审核和平台处置；同一公开水印版本不能识别具体下载者。
- **维护者决定**：将「独立的视频原创保护辅助工具」列入后续团队候选；先验证需求与平台权益，再决定原型范围。不改变下文既有任务顺序，没有开发／采购／发布授权或交付日期。
- **证据入口**：[完整调研](VIDEO_ORIGINALITY_PROTECTION_RESEARCH_2026-10-23.md) 包含需求演变、竞品版本／层级与官方来源、事实和推导的区别、测试缺口及后续验收；[当前计划](CURRENT_PLAN_ZH.md) 与 [TODO](TODO.md) 已同步回链。
- **验证**：调研登记后 `scripts/check.sh` 全部通过，`git diff --check` 通过。本次收尾追加后复跑文档检查与差异检查；未改产品代码，未运行 Python 测试套件。
- **本次本地交接状态**：仍在 `main`，四份文档为本地未提交改动（本交接、当前计划、TODO，以及新增调研文档）。本 session 未提交或推送；不要将下文发版时的「无未提交改动」误读为当前状态。下次可从上述四份文档继续，按维护者后续安排处理版本记录。

本轮仅登记未来方向，README（中英）、文档首页、CHANGELOG、CLI／配置、架构、llms 双份和技能入口没有新增已交付能力需要同步；不修改已归档的 ROADMAP，也不新增对外功能承诺。

### 最终扩展同步审计（同日，维护者要求）

- 冷启动：根目录 `CLAUDE.md` 补研究入口，并明确 10-22 状态为历史；`AGENTS.md` 的长期开发约定无须调整。
- Memory：现有 Claude 项目 `MEMORY.md` 与同日 closeout memory 已补短路由；以仓内调研为准。Codex 本地 memories 目录没有既有记录，不另建重复事实库。
- 跨项目：`workspace-meta/README.md`、`PYOBFUS_REPOSITORY_MAP.md`、`WORK_LOG_INDEX.md` 和同日 pyobfus 审计归档已同步。前两份遗留的「10-22 分支未合并／未发布」当前描述已纠正；`home/CROSS_PROJECT_INDEX.md` 补研究入口。
- 审计前 pyobfus、workspace-meta、home 均为 `main`、各一个工作树；未发现参与仓库的非 main 未提交内容。审计前仅 pyobfus 有本 session 四份文档改动，其余两仓干净。
- 本次追加后 pyobfus 为五份文档改动（另加 `CLAUDE.md`），workspace-meta 为四份，home 为一份；此外两份本地 memory。全部未提交／推送。原四份交接状态段是上一轮收口快照，当前以本节及 git 状态为准。
- 未建立独立视频仓库，也未修改 Action／法律仓库或备份。后续先读本文，再读 CURRENT_PLAN／TODO 和调研，不自动开始原型。

## 本轮做了什么

| 步骤 | 结果 |
|---|---|
| 状态核查 | 进度、下载（Core 30 天安静日中位数 35/天）、Gmail（无待回复客户）三样一起看 |
| PR #112 | 10-22 分类提交推送。首轮 hosted CI 发现两处仅测试问题：Python 3.9 只能装 Click 8.1，`CliRunner` 把 stderr 混进 stdout；Windows 子进程按 cp1252 输出 traceback。Codex 修测试（`5498330`），Claude 审核，rebase 合并 → `b01c7ad` |
| TODO 登记 | `--unmap` 读非 UTF-8 trace（文件与 stdin）抛未捕获 `UnicodeDecodeError`，未授权实现 |
| Core 0.9.0 | PR #114 → `a418d90`，tag `v0.9.0`；PyPI/PEP 740、3.10/3.15 全新安装冒烟、GitHub Release（手工建）、Zenodo `23585299`、`CITATION.cff` |
| MCP 0.3.15 | PR #116 → `887026c`，tag `mcp-v0.3.15`；PyPI/PEP 740、3.15 全新安装 stdio 握手 9 tools、MCP Registry active/isLatest、Glama 测试 `01a166ea` |
| 文档 PR | #113 / #115 / #117 / #118 和本收尾 PR，均只改文档 |

## 维护者本轮定的规则

- **发版节奏（10-23）**：不再为观察下载设静默期或月度窗口；按功能扩展与错误修订的自然进度发版，每次仍需维护者批准。全文见 `TODO.md`「节奏」。
- 公开仓库用 GitHub 托管 runner 不计 Actions 分钟额度；10 月额度用尽只影响私有仓库。

## 续接顺序

1. `--unmap` 非 UTF-8 输入（TODO，修好即可发补丁版）。
2. Pro opacity 纯转换 API 的 future prologue 缺陷（TODO，CLI 影响未验证）。
3. L3 + 应用 key provider：等维护者定范围再交 Codex。
4. DEV 第 2 篇草稿待维护者审稿；不自动投稿。
5. 每周下载只看异常；10-25 复盘照做，但不再决定发版时机。

## 发版 session 本地状态（后续状态见本文顶部）

发版 session 收尾时只剩 `main`，与远端一致，无未提交改动。发版证据在 gitignored 的 `docs/internal/release-0.9.0/`、`docs/internal/release-mcp-0.3.15/`，Codex 提示词在 `docs/internal/codex-2026-10/PR112_CI_FIX_PROMPT.md`。
