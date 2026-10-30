# 六项工程验收（2026-10-30）

状态：六项工程范围已实施，完整质量检查进行中。Core/MCP 修复尚未发布；
打包实验使用公开 Core 0.11.0 / runtime 0.1.1，不依赖本轮新修复。
用户、买方与问题：交付 Python 软件的开发者需要可靠转换、可执行成品和
诚实的机器接口。本轮直接证据是合成复现与现有交付样例，不是新客户调研。
按 [版本边界政策](EDITION_BOUNDARY_POLICY.md)，检查器与 MCP 正确性修复
属于 Community；L3 仍为 Pro，仅补验证，不移动源码或改变收费边界。

## E1：导入与属性差分

维护用例：`integration_tests/test_import_semantic_corpus.py`。包含相对别名、
包再导出、包版本循环、try 初始化、函数内导入遮蔽、星号转发、模块
`__getattr__`、跨模块异常八类；各自运行默认与保守模式。

Python 3.12.3 下公开 0.11.0 与 checkout 各 16 项通过，公开 0.11.0 在
Python 3.15.0 另有 16 项通过。这里“通过”包含
默认模式无法证明时的已知诊断，不表示默认模式所有产物都与原文等价；
默认失败限于循环、try 初始化、模块 getattr 三个已知类；不允许其他样例
仅凭告警就通过。保守模式要求本组样例的输出、退出码与异常类型保持一致，异常名字可还原。
不把八个样例推广为任意循环导入或任意动态访问支持。

```bash
venv/bin/pytest integration_tests/test_import_semantic_corpus.py --no-cov
# 可用独立公开 wheel 环境的解释器替换，测试子进程从临时目录调用该安装。
PYOBFUS_VALIDATION_PYTHON=/path/to/public-env/bin/python \
  venv/bin/pytest integration_tests/test_import_semantic_corpus.py --no-cov
```

## E2／E3：公开 wheel 的冻结交付

Linux x86_64 / WSL；PyInstaller 6.22.3、hooks-contrib 2026.9。
独立 venv 正常安装公开 Core 0.11.0、runtime 0.1.1；L3 依赖
cryptography 50.0.2 / cffi 2.1.1。所有试用状态写入全新的实验 HOME，
无 email、无真实许可证读取、无线上注册。应用密钥随机生成，仅经环境
传入构建与目标运行，不写进源码、命令或证据 JSON。

| 组合 | 结果 | 业务／异常验收 |
|---|---|---|
| Python 3.15.0 Community onedir | 通过 | 正常报价与资源读取、跨模块错误和 mapping |
| Python 3.15.0 Community onefile | 通过 | 同上，包含临时解包目录中的 traceback |
| Python 3.12.3 L3 onedir | 通过 | 正确 key 正常运行；缺失 LicenseBindingError；错误 OpacityRuntimeError |
| Python 3.12.3 L3 onefile | 通过 | 同上；加密 quote_order 帧还原为 name_only |

构建后隐藏原文与混淆树；目标 cwd 为空目录，环境仅保留基本 PATH、临时
HOME/USERPROFILE 和本次应用 key。检查自产 PyInstaller 归档没有 builder
模块或 mapping 名称；目标运行不调用 builder。外壳检查仍明确返回
`frozen_uninspected`，没有把运行成功或归档列表当成内部保密性证明。
原始 key 与 base64 形式未出现在可执行文件字节中；这不证明运行时不可提取。

Community 14 个步骤累计约 11.93 秒，L3 19 个步骤约 15.79 秒（不含环境安装，
本机单次观察，非性能承诺）。临时详细证据：
`/tmp/pyobfus-delivery-315-community/result.json`、
`/tmp/pyobfus-delivery-312-l3/result.json`；持久结论以本记录为准。
不代表 Windows/macOS、3.15 L3 冻结交付、free-threaded 或复杂插件已验收。

## E4：复跑入口

`scripts/validate_packaged_delivery.py` 复用既有多模块夹具，增加小型资源变体；
在指定的新目录内完成原文→混淆→onedir/onefile→隔离运行→异常还原→
交付告警检查。失败也写 `result.json`；各步日志与 mapping 留在 private
子目录。工作目录已存在即拒绝，避免覆盖旧证据。

```bash
# 在 WSL checkout 运行；选择已安装 pyobfus 和 PyInstaller 的目标解释器。
/path/to/public-env/bin/python scripts/validate_packaged_delivery.py \
  --work-dir /tmp/new-community-delivery
/path/to/public-env/bin/python scripts/validate_packaged_delivery.py \
  --work-dir /tmp/new-l3-delivery --l3
```

脚本不自动安装依赖，不修改 CI，不发版。当前实测为 Linux；Windows 命令
路径虽作兼容处理，尚未据此声明验证通过。原有 packaging lane 保持不变。

## E5：交付检查器边界与修复

修复前最小复现：外部文件符号链接被读取并返回 ok；wheel 中 `../outside.py`
返回 ok；证据 `{ "outputs": [] }` 导致 AttributeError，MCP 无结构化错误。

本地修复（尚未发布）：

- 拒绝外部／目录／循环链接和特殊文件；允许指向交付树内普通文件的链接。
- wheel 拒绝绝对、穿越、Windows drive/backslash、重复路径及符号链接成员。
  不解包、不执行成员。
- 目录与 wheel 限制 100,000 条目、单项 256 MiB、累计 1 GiB；证据 JSON
  限制 20 MiB，字节码邻接源码重读限制为 1 MiB 加一个检测字节。
- 校验消费的 report/manifest 字段形状，损坏或超限中止，CLI exit 2、MCP
  InvalidInput。不会把部分扫描标作 ok；原有 high exit 1、warn exit 0 保留。

定向 44 项通过，包含降低测试阈值模拟压缩成员超限、累计量／数量超限、
路径、链接、FIFO、坏归档、坏 report 与截断字节码。阈值约束本地静态
输入的读取量，不是针对并发恶意改写目录的操作系统沙箱，也不保证耗时上限。

## E6：机器接口审计与修复

CLI 完成扫描报告保留原契约：有 `exit_code` / `ai_hint`，没有 `status`；
构建预览有 `status` 而不要求 `exit_code`。没有统一重写或升级 CLI 格式。
VS Code 的 `CheckReport` 使用扫描 exit_code，runner 允许解析非零 JSON；
本轮无需修改扩展。九个 MCP 工具名与 catalog 已静态核对一致。

新增回归核对 CLI/MCP clean/high/parse-error 三类结果，及路径缺失、坏交付
证据、交付告警、禁用工具和限流响应。本地 MCP 修复：

- parse error 从 warnings 改为 error，不再建议下一步保护构建。
- delivery warn 要求审查未检查内容，不再声称没有已知问题。
- 普通错误、工具禁用和限流响应补已有文档约定的 `next_tool`，tool 为 null；
  为新增字段，不移除已有字段，调用方不得自动重试或绕过禁用策略。
- protect 成功不再把 compile/import 验证描述为 safe/ready to ship；要求应用
  行为和交付检查，跳过验证时明确说明。

MCP 全套 159 项通过。完整 Core／integration／runtime 与质量检查结果在
[执行表](EXECUTION_PROGRESS_2026-10-30.md)收口后记录。

## 提交前审阅（2026-10-30）

复核完整代码差异、新增文件、Unreleased changelog、TODO 状态和测试日志；
没有发现新增秘密、临时构建产物或阻断问题。最终检查：Core 4,683 passed /
55 skipped；MCP 159 passed；integration 368 passed / 10 skipped；runtime
24 passed；3.15 边界 48 passed；`scripts/check.sh` 与 `git diff --check`
通过。Core 输出含 7 条既有 Click isolated_filesystem 弃用警告；所有测试退出成功。

当前审阅结论：工作区变更可进入提交流程；未创建 commit、推送分支或发布。
