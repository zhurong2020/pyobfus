# Python 3.15 支持计划与下次会话交接

**优先级：P0，维护者于 2026-10-20 明确确认。** 利用 Python 3.15 发布窗口，尽快完成兼容支持；优先于 MCP SDK 升级、mapping 扩展、目录 fusion、参数改名及其他新增功能。

**执行状态：支持分支已实现，正在完成验收与 draft PR 交接。** 本轮仅实现与 PR，不合并、不改版本号、不打 tag、不发布；合并及发布由 Claude 独立审核后执行。见 [2026-10-20 验证记录](PYTHON315_VALIDATION.md)。医院应用继续暂停。

## 1. 当前事实与入口

- 已发布版本：Core 0.7.5 / MCP 0.3.13 / runtime 0.1.1。
- 已发布 Core 0.7.5 的支持范围为 **Python 3.9–3.14**；支持分支增加 **3.15**，具体 CI head 与验收结论写入实施 PR。
- 10-20 已用原生 Linux x86_64 CPython 3.15.0，对 checkout 和 PyPI Core 0.7.5 wheel 复现两项缺口；原文与产物均用独立 Python 子进程比较。
- 最小输入、解释器／wheel 哈希、结果与限制见 [10-20 调研 §5](FEATURE_EXPANSION_RESEARCH_2026-10-20.md)。小型证据和探针位于本地忽略目录 `docs/internal/research-2026-10-20/`。临时解释器路径只作复跑便利，不作为其他机器的环境前提。
- 工作规则以 [AGENTS.md](https://github.com/zhurong2020/pyobfus/blob/main/AGENTS.md) 为准；实际进度写回 [当前计划](CURRENT_PLAN_ZH.md)，待办写回 [TODO](TODO.md)。

## 2. 实施范围与建议顺序

1. **先复现，再定位两项已知缺口。** 用本轮 PyPI 0.7.5 wheel 作旧版基线，对修订 checkout 做行为差分；补与构建解释器绑定的回归，避免仅在旧 AST 上模拟字段。
2. **审计 3.15 相关 AST 与作用域路径。** 覆盖惰性导入、推导式解包、节点构造器、名称保留、源码生成、symtable 对应；检查 Core 与 Pro 共用路径。
3. **验证现有工作流与 runtime 边界。** 单文件、默认跨文件目录、独立文件目录、报告／mapping／unmap、CLI／MCP 及现有 Pro 支持模式。按已支持能力验收，不在此轮扩展目录 fusion 或方法加密。
4. **接入持续 CI，完成真实目标验证。** 保留 3.9–3.14，增加 3.15；依赖安装、测试、打包与干净目标运行都要有证据。
5. **最后更新支持声明和发布材料。** 检查通过后再扩大分类器、支持矩阵、README 等承诺；独立审核和版本决定完成后，按发布清单发版并验证发布包。

本任务属于 Community 正确性／兼容性，不改变版本分层、不提高现有最低 Python 版本，不引入原生保护器或新收费能力。

## 3. 两项已知缺口

| 编号 | 原文与失败 | 初始定位 | 验收 |
|---|---|---|---|
| PY315-1 | `lazy from calculator import Calculator`：原文输出 `START → LOADED → True`；构建成功但产物为 `LOADED → START → True` | `ImportRewriter` 重建 `ImportFrom` 丢失 `is_lazy`；不能只补字段而忽略其他重建、作用域或导入分析路径 | 导入副作用和失败时机一致；普通／惰性、别名／相对／多名字导入、串行／并行均有代表性样例 |
| PY315-2 | `values = {**row for row in rows}`：原文可运行；构建报 `NoneType ... _fields` | 根因尚未完成定位；发布 ASDL 的 `DictComp.value` 可空 | 字典解包构建与行为一致；同时验证列表、集合、生成器及异步适用形态、绑定与嵌套作用域 |

更多发现先登记最小复现和影响范围，不把新语法问题直接概括成所有 3.15 程序不可用，也不把旧版本通过当作新语法通过。

## 4. 支持声明前的验收清单

- [x] PY315-1／PY315-2 在 0.7.5 基线失败、修订版通过；原生 3.15 回归持续执行。
- [x] 普通源码与 3.15 新语法分别验收；语法合法但无法安全处理的情况必须明确报告，不得静默改变语义。
- [x] 审计 AST 必需字段、惰性标记、`DictComp.value=None`、新增内建名、默认编码及源码生成行为；有代表性的反向对照。
- [ ] Core 3.15 在 Linux、Windows、macOS 持续 CI 通过；原有 3.9–3.14 矩阵保持通过。任何未验证平台须明确收窄声明，不可把 Linux 冒烟扩大为三平台支持。
- [x] 按 AGENTS.md 将 `tests/`、`pyobfus_mcp/tests/`、`integration_tests/`、`pyobfus_runtime/tests/` **分开运行**；确认 3.15 对四测试根的影响。测试使用各自 tmp_path，保持调用者正常 HOME 下隔离。
- [x] 完整 `scripts/check.sh` 通过；必要时核对格式／类型工具对 3.15 的兼容，但不借机无关升级依赖。
- [x] 新解释器构建的普通源码在仍承诺的旧目标版本上解析／运行；3.15 专属语法明确保留目标下限，不要求把语言新特性自动降级。
- [x] Core、runtime 候选 wheel 在全新 3.15 环境安装、`pip check` 与代表性运行通过；检查 runtime 及 cryptography 等实际依赖的目标可用性。
- [x] Pro 验证仅使用合成样例与隔离许可状态；分别核对源码变换与 L3 bytecode/marshal 的构建／目标版本约束，不承诺加密字节码跨 Python minor 可移植。
- [x] MCP／VS Code／Action 的 Python 解析、基础合同与必要集成检查无退步；MCP 2.x 上限调整仍是独立任务，不捆绑进 3.15 支持。
- [ ] 独立审核通过；支持矩阵的每项结论能指向测试、CI 或带日期的记录。

四测试根通过和多平台证据是支持声明的组成部分，不用单个最小修复替代整体验收；无需为未触及的重型框架或冻结包宣称全面支持。

本轮证据：`docs/internal/codex-2026-10/py315-evidence/`（本地忽略）。
最小失败：`main-regressions.log`、`main-traceback.txt`、`published075-regressions.log`；
修复：`regressions.log`、`315-extra-regressions.log`；AST：`ast-delta.json`、`ast-source-audit.txt`；
反向兼容：`portable315-to310.json`；完整检查：`check.log`；安装与 runtime：
`core-clean-install.log`、`core-clean-canary.log`、`runtime-clean-tests.log`、`mcp-clean-install.log`。
标准库与 H/I 对照见验证记录及 PR；`tests-315-tests-final.log` 是修复后完整 Core 结果，
`regressions-final.log` 追加验证最终 50 项原生回归；四根均独立运行。
VS Code：`vscode-tests315-final.log`（53 项，原生 3.15 CLI）；Action：`action315-smoke.json`
（本地 driver check/build 合同，不能替代其 hosted composite 三平台验收）。
未验证项不得由本地 Linux 冒烟替代。

## 5. 同步与发布顺序

达到上述门槛后，同步以下面向用户的事实；本次规划同步不提前修改它们的版本范围：

- Core／MCP／runtime 适用的 `pyproject.toml` 分类器，以及格式／类型目标配置；保留既有最低版本，按各包实际证据更新。
- `AGENTS.md`、`CLAUDE.md`、`SUPPORT_MATRIX.md`、README 中英文、文档首页；核对生成的配置 schema／VS Code 描述／工具清单中是否存在 Python 版本枚举。
- Core 与受影响包的 `[Unreleased]`、发布说明、构建兼容性及 runtime 限制；版本号由实际范围决定，本计划不预设 0.7.6 或其他版本。
- 原先 [10-12 路线图](AI_ERA_PROTECTION_ROADMAP_2026-10-12.md) 和 [10-20 调研](FEATURE_EXPANSION_RESEARCH_2026-10-20.md) 保留研究历史，更新实施结果指针；TODO 移除已完成项，当前计划记录完成证据。

发布仍需维护者另行确认。若 runtime 源码变动，先升版本、先发 runtime，再发依赖它的 Core；MCP／扩展／Action 不因 Core 支持新解释器而自动发版。发布前完整检查与审核，发布后做 PyPI 产物、PEP 740、全新环境安装、GitHub Release、Zenodo/CFF 核对，沿用现有 runbook。

## 6. 后续 session 的启动提示

> 先读 AGENTS.md、CURRENT_PLAN_ZH.md 顶部和 PYTHON315_SUPPORT_PLAN.md。维护者已将 Python 3.15 兼容性列为 P0；本次 session 的具体实现与发布范围以维护者当次指示为准。先复现 PY315-1／PY315-2，再审计并完成 3.15 验收，保持 3.9–3.14 正确性。不要恢复医院应用工作，不捆绑 MCP 2.x、参数改名或目录 fusion。完成后同步支持声明和证据，合并与发版按各自 gate 执行。
