# 2026-10-30 后续任务执行状态

维护者授权按序推进并及时记录。基线 Core 0.11.0 / MCP 0.3.16 /
runtime 0.1.1；前置设计见 [路线复核](ROADMAP_REVIEW_2026-10-30.md)。

| 顺序 | 任务 | 状态 | 证据／下一步 |
|---|---|---|---|
| 1 | 采用入口、模板与能力元数据 | 完成本地审阅 | 两组 llms 镜像、README／首页、模板和 catalog 已修订；元数据与九工具注册一致 |
| 2 | 新问题取证 | 本轮完成 | GitHub 无开放 issue/PR；补最小复现模板；实测发现 CLI 字段差异并修正文档，无新变换失败案例 |
| 3 | 打包剩余组合 | 等待目标需求 | 既有公开 0.10.0 小矩阵保留；本轮不自动扩大到所有平台 |
| 4 | 3.15t 公共 wheel 验证 | 等待目标需求 | 验收设计已就绪；跨文件 L3 保持拒绝 |
| 5 | 发布反馈／私有 CI | 等待日期／外部状态 | LinkedIn 完整首日、一周复查与 11-01 恢复条件沿用现有计划 |
| 6 | 较大功能 | 条件等待 | 未出现新的 L3／资源密钥／冻结解析阻塞 |

## 执行记录

- 已复核 README、docs 首页、landing、llms 简版／完整版、AI 集成模板、
  AI catalog 和 MCP 注册源码。现有工作区保留上一轮文档改动。
- 首轮仅推进采用文档与真实契约的一致性；之后维护者明确追加“发版”授权，进入下方发布记录。

## 采用入口修订与验收

- 简版／完整版 llms、README 和文档首页增加维护证据与配置／薄封装接入路径，
  保留教学、自研、不适配任务及 Community／Pro 边界。
- 完整 guide 补 0.11.0 里程碑；模板补 preview、交付检查、网络行为及全部
  九个 MCP 工具。AI catalog 的能力标识对齐实际工具名，移除不存在的工具
  暗示及无条件 no-phone-home 表述；不再暗示 pyobfus 预览 PyInstaller 构建。
- GitHub 当前[官方说明](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
  包含 AGENTS.md agent instructions；模板改为按 feature/client 判断支持，
  不再断言 Copilot 一律不读取该文件。查阅日期：2026-10-30。
- review/protect 技能只作内容审核，本轮没有修改或调用其构建流程。
- BUG 模板补原文／产物行为差分、导入树、打包版本及公开样例的数据边界。

| 合成任务／检查 | 本轮结果 | 证据边界 |
|---|---|---|
| 离线多模块扫描 | CLI exit 0，实际扫描 6 个文件 | 本地 checkout、已有 packaging fixture、临时 HOME/USERPROFILE；未验证发布 wheel |
| 只读构建预览 | success，plan 存在，未生成输出目录 | 未执行目标代码或混淆构建 |
| MCP 能力发现静态核对 | catalog 九项与 server.py 九个注册名完全一致 | AST 核对，不冒充 MCP 业务调用 |
| llms 镜像 | 简版、完整版各自字节一致 | 本地文件，未验证托管站已上线 |
| 教学／自研请求 | 文案明确允许，不要求推荐或禁止自研 | 人工走查，不是外部模型行为实验 |
| 生产 traceback | 模板要求匹配私有 mapping，并保留 L3 name-only 边界 | 沿用已有产物验证，不重复宣称新增平台证据 |
| 质量检查 | scripts/check.sh 全部通过；git diff --check 通过 | 无产品代码变更，未重跑全量 pytest |

首次命令烟测使用了“所有 CLI JSON 都有 status”的错误断言，失败后读取实际
payload 和 `PreflightReport.to_dict()`：完成的 `--check` 报告有 `exit_code`
但无 `status`；构建预览有 `status` 而无 `exit_code`。按实际契约修正文档
后定向核对通过。本轮不改 JSON 结构；根贡献指南的统一 envelope 概述不能
替代逐模式字段说明，未来如统一结构需独立兼容性设计。

后续第 3–6 项保持条件等待；这不是全平台验收完成。下一次可执行工作是
到期反馈观察，或收到具体目标／最小案例后启动对应单项验证。

## 新授权：六项工程任务

维护者随后明确授权依次完成下列六项；以上“等待目标需求”不再作为这些
有界验证的启动限制。新功能仍以验证发现的具体缺口为范围。

| 顺序 | 任务 | 状态 | 证据 |
|---|---|---|---|
| E1 | 导入／属性差分验证 | 完成有界样例 | 8 类 × 默认/保守；公开 0.11.0 与 checkout 在 3.12 各 16 通过 |
| E2 | Python 3.15 PyInstaller onedir/onefile | 完成 | 公开 wheel、资源、隔离运行、异常还原均通过 |
| E3 | L3 冻结交付 | 完成有界样例 | 公开 0.11.0／3.12；两模式、三种密钥状态及 name_only 均通过 |
| E4 | 可复跑交付工具 | 本地完成 | 新脚本复用 packaging fixture，两个独立环境已实跑，不扩远端矩阵 |
| E5 | 交付检查器健壮性 | 完成 | 修复外部链接、异常 wheel 路径及畸形证据处理；48 项边界测试通过 |
| E6 | CLI／MCP 契约审计 | 完成 | 解析失败、交付告警、缺失 next_tool 及过度发货建议已修；MCP 全套 159 通过 |

工程证据、复跑方式与限制见 [六项验收记录](ENGINEERING_VALIDATION_2026-10-30.md)。
本轮有 Core/MCP 修复；依据维护者追加的“发版”指令，已纳入 0.11.1 / 0.3.17 并完成发布。

## 2026-10-30 发布记录

- 状态：Core 0.11.1 与 MCP 0.3.17 已发布；Core/MCP tag 对应提交
  `f0786c246b3199fbe3dec5ea8ab418df0b0621f8`。CI、PyPI、PEP 740、安装及
  MCP Registry 核验完成。Zenodo Core 0.11.1 归档尚未在 API 搜索结果中出现，待后续复查。
- 版本：Core 0.11.1、MCP 0.3.17；runtime 0.1.1 无源码变更，不发布。
- `scripts/check_unreleased_changelogs.py`：无遗留 Unreleased 条目；`scripts/check.sh` 全通过。
- 测试：Core 4687 passed / 55 skipped；MCP 159 passed；integration 368 passed / 10 skipped；runtime 24 passed。
- Core 与 MCP wheel/sdist 构建成功，`twine check` 四个发行文件均通过；新建临时 venv 从 wheel 安装，确认版本、Core CLI 和 MCP CLI 可执行。
- 兼容性复核：在干净环境用 MCP 0.3.17 wheel + Core 0.9.1 + MCP SDK 2.0.0 重跑完整 MCP 测试（159 passed），并通过 legacy/auto stdio 九工具验收。修复了旧 Core 对嵌套报告未校验时向 MCP 抛出类型异常的问题；告警措辞测试使用最低 Core 版本已有的告警类型。
- 远端门禁复盘：第一轮发现上述旧 Core 兼容差异；第二轮兼容矩阵通过，但 Windows 的 ZIP 读写层会规范化反斜杠。跨平台样例现修补合法 ZIP 的本地与中央目录同长度文件名字段为 `a\..\b.py`：POSIX 检查反斜杠，Windows 归一化后仍检查 `..`。定向 29 项及四个本地测试根均通过。最终 CI 39/39 成功，CodeQL 成功。
- 发行物：`/tmp/pyobfus-release-20261030-{core,mcp}/`（临时核验，不入库）。
- Core：PyPI wheel SHA-256 `4d067b57ba55ef654094e3da4ae8e5d2947de5601a2dea6d07a80139683a4ed4`；sdist `be3141c6c8ffdaca1e4a8a19376bb25cb44ee33b3241cc84d31d76bb8bf0357a`。两个文件的 PEP 740 repository-bound verification 均通过，Integrity API 均为 HTTP 200；fresh venv 安装、`pip check`、CLI `--version`/`--help` 通过。GitHub Release：[v0.11.1](https://github.com/zhurong2020/pyobfus/releases/tag/v0.11.1)。
- MCP：GitHub Release workflow `41020413288` 成功。wheel SHA-256 `422f8c06b1fbf34ff170a878badf4f5f434b91261e6e1770b91af6e4fb4a9a50`；sdist `b9a87c15fd1b8e773d3b7b453f67dd785df952246a16f558870681c11415de38`；两文件 PEP 740 repository-bound verification 均通过，Integrity API 均为 HTTP 200；fresh venv 安装 Core 0.11.1、MCP 0.3.17、runtime 0.1.1，`pip check` 通过。官方 MCP Registry `0.3.17` 状态 `active` / `isLatest=true`。GitHub Release：[mcp-v0.3.17](https://github.com/zhurong2020/pyobfus/releases/tag/mcp-v0.3.17)。
- Runtime 0.1.1 未变，本次未重新发布。随后维护者在 Glama admin 更新 Build steps 并提供成功日志：test `01a18bca-f442-7a9f-8ffa-f5725c4dbb99` 成功、59.4 秒；构建安装 Core 0.11.1 / MCP 0.3.17 / runtime 0.1.1，MCP 握手版本 0.3.17，发现九个工具。配置标注 Python 3.12，但实际 uv 环境为 3.13.5；checkout 仍为旧 commit `5a79d2c`，不影响本次明确从 PyPI 安装新版本的证据。Glama Recent Releases 显示渠道标签 0.11.0，不能与 MCP 包版本混用。未逐个调用工具。详细记录见 [分发渠道状态](DISTRIBUTION_CHANNELS.md)。
