# 独立文件目录 mapping 验收与审核

日期：2026-10-22。状态：已实现，本地验证通过；分支 `feat/adoption-debugging-workflow`，按维护者授权分类提交到工作分支，尚未合并／发布。公开 0.8.0 尚不含此能力。

## 已验证

| 路径 | 结果 |
|---|---|
| Python 3.12 Core 全量 | 4467 passed，54 skipped |
| MCP 独立测试根 | 153 passed |
| CLI 集成独立测试根 | 352 passed，10 skipped |
| runtime 独立测试根 | 24 passed |
| Python 3.15 专项 | 157 passed（含末次 names-only 幂等回归） |
| Black/Ruff/mypy/README links/严格文档构建 | 最终统一脚本全部通过（296 文件格式检查、113 源文件类型检查及严格文档构建） |
| 新 wheel／新目标与旧 reader | 工作树 wheel 在隔离环境安装；无 builder/runtime 的目标执行两个不同原函数但同短名的脚本；新 reader 分别恢复，接受旧 v1；公开 0.8.0 reader 对 v2 明确退出 2 |

复跑入口：`scripts/check.sh`、四个 pytest 根（按 AGENTS.md 分开调用）；专项 `tests/test_independent_mapping.py`、`tests/test_independent_mapping_cli.py`、`tests/core/test_line_map.py`、`tests/test_source_prologue.py`；MCP 合同回归在其独立根。wheel 的版本号没有提升，属于未发布工作产物，不能把安装结果说成已发布版本行为。

## 多引擎审核实际改变了什么

| 反例／问题 | 修订与证据 |
|---|---|
| 原文加空行，AST 产物相同，原始行号不同 | marker 纳入原文与 marker 插入前产物的摘要；空行变化回归 |
| 多文件共用短名，旧全局表 first-wins | v2 逐文件候选表，不 backfill 全局表；旧 v1 writer 不变，旧 reader 拒绝 v2 |
| 部署目录名与嵌套包重名 | 保留全部后缀候选，联合路径／名字推根；单帧歧义拒绝，`<module>` 调用帧也参加排除 |
| 外部同名函数压过本应用路径 | 所有匹配路径参与一致性检查，不按帧数投票；无名字证据的单一外部路径不恢复 |
| 失败／排除／残留嵌套文件借用短路径映射 | `unmapped_files` 保留负身份，参与根候选但不恢复；只给本次成功文件盖章；JSON 警告覆盖不完整 |
| 异常组、异常链、缩进异常消息串用上下文 | 支持树前缀帧头；不改写源码片段、异常文本或无帧日志 |
| Unicode 及 NFKC 短名 | Greek、Kelvin 与组合音标前缀的真实 CLI 运行／异常回归；不改 v1 行为 |
| 缺失行表／损坏可选行表 | 保留文件身份与名字；`resolved_file` 明确名字可归属而行表不可用 |
| 再次 unmap 导致名字二次变换 | 有原行位置、generated 及 names-only 都使用可识别注记；原始名等于另一短名的回归 |
| 不同换行拆分导致迭代器不同步 | 同一次物理行解析贯穿推断和呈现；控制字符反例不崩溃 |
| 增量缓存不补新 mapping | 请求独立目录 mapping 时强制重建；覆盖先无 mapping、损坏旧 mapping 和原文改变 |
| 合法 POSIX 文件名不能放进可移植键 | 保留成功产物，标记路径不可映射并警告；不在写完代码后把整个构建变成异常 |

Claude 通过本机现有 CLI 独立审阅公开源码／设计；另一路独立代码审核提供了实测反例。原始输入、输出和运行日志保留本地忽略目录。不是所有建议均直接采纳：例如“单文件缓存 override”位于既有 directory-only guard 内，实际未改变单文件路径；“盖 marker 前必须把全部产物留内存”也可由现有的先收集／保存、后盖章顺序解决。

## 实际限制

版本 2 只在可唯一归属的帧上恢复名字及可用原语句位置。没有 marker 就不能证明使用了正确构建的 mapping；marker 也不是认证。严格路径一致性可能因外部 `__init__.py` 等同名路径而拒绝整段 trace。未知、越界、歧义及未成功映射的文件保持原样。未验证所有 OS／Python 组合，不把本地证据当成 hosted CI 全矩阵结果；没有修改仓库保护规则或发布渠道。
