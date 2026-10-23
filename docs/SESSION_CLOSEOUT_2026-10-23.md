# Session 交接：PR #112 合并，Core 0.9.0 与 MCP 0.3.15 发布

日期：2026-10-23。冷启动先读本文，再读 `CURRENT_PLAN_ZH.md` 顶部和 `TODO.md`。

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

## 本地状态

收尾时只剩 `main`，与远端一致，无未提交改动。发版证据在 gitignored 的 `docs/internal/release-0.9.0/`、`docs/internal/release-mcp-0.3.15/`，Codex 提示词在 `docs/internal/codex-2026-10/PR112_CI_FIX_PROMPT.md`。
