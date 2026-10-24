# 2026-10-24 优先任务推进

维护者授权按 10-23 交接顺序推进；本轮工作保留为本地改动。开始时已有五份视频研究相关文档改动，保持其内容。

## 1. Community traceback 输入编码

`--unmap` 新增 `--trace-encoding`，默认 `utf-8-sig`，兼容 UTF-8 BOM。文件和真实管道均按指定编码严格解码；不使用机器 locale 猜测，不以替换字符损坏混淆名字。旧 Windows cp1252 日志显式指定编码。错误编码、非法字节、无法读取输入以 exit 2 和 stderr 提示结束，JSON 成功输出形状保持原样。stdin 的 CRLF 继续按原文本模式规范化。

回归覆盖文件/stdin 的 UTF-8、BOM、cp1252，非 ASCII 文件名及错误消息，未知 codec、错误字节、真实 subprocess 管道与纯文本 stdin。功能及基本本地调试属于 Community；无 Pro 门槛。

## 2. Pro opacity prologue

用提交版本的 transformer 在独立命名空间复现：模块 docstring + future import + encrypted 函数的转换文本编译失败。两处 helper 插入点遇到 docstring 停在位置 0，破坏 future import 位置及模块 `__doc__`。统一插入点跳过 docstring 和前导导入。

纯 API 回归执行加密函数，检查默认参数、future 注解语义、已有 runtime import 和模块 docstring；CLI 回归覆盖默认和 keep-docstrings 构建，加载真实产物执行。当前 CLI 两条路径均通过；没有据纯 API 缺陷宣称所有已发布 CLI 产物都受影响。此修复保留在 Pro 源目录，不改 runtime。

## 3. L3 与应用密钥范围

已收敛为 [设计 §11](CROSSFILE_OPACITY_DESIGN.md)：预检计划、Core binding 对应、Pro adapter、调试报告、staging/交付五个切片。首批约束与调试缺口可见，新目录保护能力尚未实现。

## 4. DEV 草稿审阅

保留 SARIF 主题和公开 0.8.0 固定版本证据；不因 0.9.0 发布替换已复现版本。修订「多数扫描器」的无依据泛化和「scan 不决定任何事情」的表述，明确工具错误立即失败，完成扫描才上传，最后 gate findings。

复核 GitHub shell 文档、upload-sarif v4 元数据和 Ruff 官方退出码说明。源码/文档支持 Bash shell 和报告上传契约；工具特例仍以固定版本实测为准。本地忽略目录中的草稿和发布步骤供维护者署名审阅；未上传 GitHub、未发布 DEV。

旧复现脚本依赖已消失的临时目录；本轮在新环境安装固定公开版本，脚本与证据保存于 `docs/internal/adoption-2026-10-24/`。结果与最终代码检查见本文下方验收记录。

复核来源：[GitHub shell](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell)、[upload-sarif v4 元数据](https://github.com/github/codeql-action/blob/v4/upload-sarif/action.yml)、[Ruff 退出码](https://docs.astral.sh/ruff/linter/#exit-codes)。固定版本结果：clean 0/0 results，high 1/1 result，missing 2/无报告；Bandit missing-path 0、missing-config 2；Ruff missing-path + exit-zero 0、invalid-config 2。模拟 upload-ready 和最终 gate 与 10-22 记录一致，不代表 GitHub 服务端已接收。

## 验收记录

- 环境：WSL/Linux、Python 3.12.3，仓内 `venv/`；四根测试分开运行，调用者正常 HOME。
- 最终专项：输入编码、opacity transformer、fusion CLI 共 **136 passed**，包含后补的真实 subprocess 管道和 CLI 两例。
- MCP：**153 passed**；integration：**352 passed / 10 skipped**；runtime：**24 passed**。
- 全量 Core：**4481 passed / 54 skipped**（381.77 秒）；收集早于最后四个新增用例的加入，这四例另含在最终 136 项专项中，最终源码已由专项复核。
- `scripts/check.sh`（Black/Ruff/mypy/元数据/README links/严格 MkDocs）通过；未声称已完成 Windows 或其他 Python minor 的 hosted 矩阵。
- `git diff --check` 通过。首次本地验收未含独立模型审核与 hosted 矩阵；后续审核和 PR 状态见下节。
- 代码、CHANGELOG、调试指南、当前计划和 TODO 同步；未更改版本号、提交、推送、合并、发版或外部投稿。

v1 非 ASCII 短名替换的既有限制作为独立 TODO 登记，不在本轮编码修复中扩展名字匹配规则。

## 后续：独立审核、分类提交与 PR #120

维护者同意继续推进审核和 PR。本机 Claude 以无工具、只读静态方式独立审核公开源码与合成测试材料，两轮均无阻断发现。反馈逐项处理：明确 pipe 默认编码变化；TTY 先读已解码文本，不访问 buffer；默认文本流剥离单个 BOM；已有 runtime import 测试改为实际 `pyobfus_runtime`，覆盖重用和新增 alias；文本流解码失败给出可操作的保存/管道建议。最后一项提示修订另有专项回归，不冒称独立审核者执行过测试。

审核复现的晚 runtime import 和严格 cp1252 stdout 两项既有问题分别登记 TODO，未夹入本次修复。MCP 直接调用 mapping API，不经 CLI stdin。本机订阅、无 API key；审核原始输出及逐项答复保存在本地忽略的 `docs/internal/review-2026-10-24/`。

最终本地检查：Core **4490 passed / 54 skipped**（`-n 4`，141.22 秒；收集后补了一项提示回归，含在最终专项 **142 passed**）；MCP **153 passed**、integration **352 passed / 10 skipped**、runtime **24 passed**；`scripts/check.sh`、pre-commit 个人信息/凭据扫描与 pre-push 全部通过。

分类提交：`0da7567` 编码/输入错误、`85dd41d` opacity prologue、`a0838dd` CHANGELOG。已推送分支 `fix/trace-encoding-opacity-prologue`，创建 [PR #120](https://github.com/zhurong2020/pyobfus/pull/120)。PR 只含七份代码、测试和使用说明文件；视频研究、L3 范围和本轮计划文档保留本地。GitHub 连接器返回 integration 403，改用本机已登录 `gh` 成功创建。

远端最终 head `a0838dddb90f8ea697826cf95b08921a5d11299a`：**33 项通过 / 2 项按配置跳过**；必需 `CI result`、`CodeQL` 均 SUCCESS，CI、CodeQL、Packaging、Dogfood 完成。普通 CI 的 Linux/Windows/macOS 版本矩阵通过。PR 为 OPEN / CLEAN / MERGEABLE，无冲突；未启用自动合并，尚未合并、改版本号或发布。

等待 CI 期间用真实 CLI `--name-prefix á` 构建 `calculate_total` 并运行产物，确认 v1 mapping 记录 `á0`，实际 traceback 经 unmap 后仍为短名。证据已补入 TODO，不只依赖手写 mapping 反例。

## 后续：合并 PR #120 与发布 Core 0.9.1

维护者要求推进合并与发版。合并前无头 Codex（read-only 沙箱）复核源码差异，结论 NO BLOCKERS；Claude 同步复读源码差异，未发现阻断（未知 codec 名的提示文字仍为 "cannot decode"，属措辞小项）。PR #120 rebase 合并保留三项分类提交，main CI/CodeQL 通过。发布提交 `7bbd400` 只改版本相关七份文件；本轮五份本地文档仍未提交。tag `v0.9.1` 经 release.yml 发布到 PyPI（PEP 740），全新安装与真实 cp1252 traceback 端到端核验通过，GitHub Release 已建。证据在 gitignored `docs/internal/release-0.9.1/`。

发布后：全 21 组合 CI（run `40055228574`）36/36 通过；Zenodo `23608360` 归档，`CITATION.cff` 已同步（`e6103f1`）；维护者把 Glama 改为 `pyobfus-mcp==0.3.15 pyobfus==0.9.1`，测试 `01a16bdc` 通过（握手 0.3.15、9 tools）。
