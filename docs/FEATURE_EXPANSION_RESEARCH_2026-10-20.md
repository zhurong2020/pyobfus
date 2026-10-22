# pyobfus 功能路线复核（2026-10-20）

**10-22 后续登记（不改变下文历史调研快照）**：维护者要求将「AI / Agent 发现项目后如何优先评估直接采用」纳入后续扩展。见 [采用引导计划](AGENT_ADOPTION_GUIDANCE_PLAN.md)：利用已有 llms、README／首页、集成模板和能力元数据，链接持续维护与真实验证证据；当前仅记录，不实施对外文案。四阶段本地工作已完成：独立目录 mapping 已实现并验证，L3 仅完成设计复核，DEV 案例已准备，均未合并／发布；验收和后续边界见 [推进计划](ADOPTION_WORKFLOW_PLAN_2026-10-22.md)。

状态：调研完成；维护者同日确认 **Python 3.15 兼容为 P0**，其余候选仍为建议。本轮只同步文档，后续独立 session 再实施、审核和发布，尚未开始产品实现。医院应用暂停，等待现场后续反馈；不以其安装验收推动本轮 pyobfus 功能排期。

后续实施：同日 Python 3.15 支持分支已进入 PR #108 待审；本文保留调研时的版本与复现快照，当前实现、验收与限制见 [验证记录](PYTHON315_VALIDATION.md) 和 [支持计划](PYTHON315_SUPPORT_PLAN.md)。本轮不合并、不发布。

本轮基线：Core 0.7.5、MCP 0.3.13、runtime 0.1.1；本地代码 `7e2cc5c`，远端 `e167182` 只多两个依赖更新提交。继承 [10-12 路线图](AI_ERA_PROTECTION_ROADMAP_2026-10-12.md) 的威胁模型和 [版本边界政策](EDITION_BOUNDARY_POLICY.md)。Python 3.15 的首要优先级已获维护者确认，实施范围以 [支持计划](PYTHON315_SUPPORT_PLAN.md) 为准；下面其他排序仍为建议。

## 1. 结论与建议顺序

**先处理已复现的两项 Python 3.15 兼容性缺口、复审 MCP 2.x 的发布条件，再设计多模块 Pro 保护。** 本轮原生 stdio 实测已推翻旧的协议限制结论。细节见 §5。不恢复以增加 AST 变换为目的的功能堆叠。

| 顺序 | 工作 | 理由 | 最小结果 / 分层 |
|---|---|---|---|
| **P0（已确认）** | **Python 3.15 兼容修复与支持验收** | 10-09 已正式发布；AST、导入、推导式语法直接触及变换器。现有 CI 只到 3.14 | 先修两项缺口，完成原生差分、四测试根、多平台 CI、干净安装及支持声明；Community |
| 2 | MCP SDK 2.x 本地协议与依赖复审 | 2.3.0 已有通过的真实 CI；官方当前文档明确支持 stdio 新协议，旧探路结论不能继续泛化 | 新旧协议各完成发现、9 工具列表、只读工具调用；Python 下限与干净解析验证；Community |
| 3 | `--no-cross-file` 目录模式 mapping | 官方绕过目录 fusion 限制的路径仍失去基本反向调试，已有明确代码证据 | 按文件记录名字表，按 traceback 帧定位，旧 mapping 继续可读；Community |
| 4 | fusion × 目录构建的单项设计 | 仍是最直接的 Pro 交付缺口，现有 14 项 fusion 字段都在默认目录模式跳过 | 先定义 L3 顶层函数 + 应用 key provider 的多模块子集；Pro 执行、Community 报告 |
| 5 | 资源 key provider / L3 方法覆盖 | 均有产品价值，但没有本轮新增的独立客户需求 | 分开立项，按资源或对象的明确需求择一；Pro |

第 3、4 项存在取舍：若下一位真实用户明确需要默认跨文件构建中的 L3，可先做第 4 项设计；若继续使用独立文件模式，应先补第 3 项。不是要求先做两个并行大项目。

## 2. 证据口径与限制

- 外部事实只使用官方文档、发布元数据、带版本源代码和原论文；搜索摘要只用作发现入口。
- 竞品是 **2026-10-20** 的文档／元数据快照，未购买商业层或做同配置强度测试。适用 [比较范围与免责声明](COMPARISON.md)。未复核价格，不更新价格表。
- 本仓观察区分代码已存在、测试已覆盖、干净发布包安装、真实线路协议与生产宿主验证；单项通过不能替代其他层。
- 无本轮新增的付费需求或采用量调查。此前的下载和 trial 摘要是上下文，不能把下载当用户数、把竞品功能当本产品需求。
- 不调用付费模型 API，不恢复此前暂停的可运行逆向 Agent 实验，不修改公开包源码去做自混淆。

## 3. 外部变化与本仓风险

### 3.1 Python 3.15：新增了实际的兼容性触发点

[官方发布页](https://www.python.org/downloads/release/python-3150/) 标注 2026-10-09 正式发布；[What's New](https://docs.python.org/3.15/whatsnew/3.15.html) 列出惰性导入、推导式解包、新内建类型和默认 UTF-8 等变化。本仓 `pyproject.toml` 为 `>=3.9`，但分类器、支持矩阵和 CI 都只声明／验证到 3.14；可安装不等于通过兼容验证。

应重点检查：

| 接口变化 | 本仓关联位置 | 要证明什么 |
|---|---|---|
| `Import` / `ImportFrom` 新增可选 `is_lazy` | `transformers/import_rewriter.py` 重建 `ImportFrom`；`scoped_imports.py` 再 unparse/parse | 保留惰性标记和导入副作用时序，不能把 lazy 改成 eager |
| 推导式解包；`DictComp.value` 可空 | AST visitor、作用域对应、名称验证、生成器 | 列表／集合／字典／异步形态不崩溃、不误改绑定 |
| AST 必需字段／未知关键字收紧 | Core、Pro 中所有人工构造节点 | 所有构建路径遵守新构造器要求 |
| 新内建名与 UTF-8 默认 | 名字保留、源码编码、CLI JSON、Windows 文本 | 名字不被误改；用户指定编码和非 ASCII 行为不回退 |
| 新解释器上的 bytecode / marshal | L3 构建器、独立 runtime | 构建解释器与目标解释器契约明确，不能把 Community 源码可移植性套给加密字节码 |

依据：[CPython v3.15.0 ASDL](https://raw.githubusercontent.com/python/cpython/v3.15.0/Parser/Python.asdl)、[AST 构造器说明](https://docs.python.org/3.15/library/ast.html#ast.AST)、[PEP 810](https://peps.python.org/pep-0810/)、[PEP 798](https://peps.python.org/pep-0798/)。在线 AST 页面没有完整显示新导入字段，本轮以发布 tag 的 ASDL 交叉核对，避免仅凭说明页推断节点形状。

现有版本处理“普通源码”的新解释器运行，与处理“3.15 新语法”，必须分别验收。3.15 上生成的普通源码还需在现有最低支持版本解析／运行，防止再次出现 f-string、星号下标一类语法被动升级。未过门槛前不扩大支持声明。

### 3.2 MCP：旧结论需要复测，不能直接放开依赖上限

PyPI 元数据：`mcp==2.3.0`，上传于 10-02，声明 Python `>=3.10`。本仓仍为 `mcp>=1.27,<2`，但 [10-19 的真实 CI](https://github.com/zhurong2020/pyobfus/actions/runs/39226803664/job/117974954288) 已明确安装 **2.3.0** 并跑过 **152 项 MCP 测试**。这证明适配层可工作，不证明新协议已经在线路上通过。

[SDK 当前协议文档](https://py.sdk.modelcontextprotocol.io/protocol-versions/) 明确说明现代发现适用于 stdio；[v2 发布说明](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0) 也说明同时兼容新旧客户端。因而 [09-12 探路](MCP_SDK_2X_SPIKE.md) 的“本地 stdio 没有新协议收益”不能作为当前结论。历史实测保留，先复现差异，不臆断当时的测试环境或原因。

还存在版本证据差异：当前 SDK 首页写 Python 3.11+，而 2.3.0 的发行元数据写 `>=3.10`。应针对精确 wheel 在 3.10 验证，不能根据滚动文档悄悄提高 pyobfus-mcp 的下限。[SDK 首页](https://py.sdk.modelcontextprotocol.io/)、[2.3.0 发布说明](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0)。

建议最小复审：

1. 固定 1.x 与 2.3.0，分别验证旧 `initialize` 与现代发现，实际调用只读工具，核对 `status` / `ai_hint` / `next_tool`。
2. 保留工具清单摘要及 serverInfo 版本测试；覆盖 Windows stdio 启停和取消、错误路径。
3. 新建干净环境正常解析依赖并 `pip check`；当前 CI 故意越过上限安装，不是正常解析证明。
4. 复核宿主实际使用的协议。升级 SDK 不表示每个宿主都会自动选择新协议。
5. 证据通过后再决定 `<3` 等上限和发布 MCP 版本；本轮不改依赖，也不扩远程 MCP 服务。

### 3.3 竞品：价值在交付范围与覆盖透明度

| 对象与精确范围 | 本轮确认 | 对 pyobfus 的启示 |
|---|---|---|
| PyArmor 9.2.7 官方文档／PyPI；高级模式依具体许可与平台 | native runtime、多种函数保护模式及外部 runtime key 工作流已文档化；平台表列到 Python 3.15。未独立实测 | 承认其原生保护与部署工作流；不因其有 VM 而立项自建 VM |
| Nuitka 4.3.1 公共发布；Commercial 文档独立核查 | 4.3 系列把 3.15 标为实验支持；商业数据嵌入、常量保护、可恢复 traceback 是独立产品能力 | 维持“支持／实验／未验证”分级；优先组合编译与调试验证 |
| PyLocket：PyPI 1.1.20；滚动官方 FAQ／平台文档不视为锁版测试 | 覆盖摘要明确列出例外；原生 runtime、授权和多格式分发；承认授权运行者可见运行值。页面列 Python 3.12–3.14 | 借鉴可解释覆盖报告和运行边界；不复制整套云端销售／授权平台 |
| CodeEnigma：PyPI 1.2.0；仓库 README 限架构观察，未做发布包实测 | 加密字节码、Cython loader、自包含本地流程；1.2.0 元数据为 Python `>=3.10,<3.14` | “AES + loader”本身不足以构成差异化；pyobfus 应补多模块交付和私下调试闭环 |

来源：[PyArmor 9.2.7 文档](https://pyarmor.readthedocs.io/en/stable/)、[平台表](https://pyarmor.readthedocs.io/en/stable/reference/environments.html)、[外部 key 教程](https://pyarmor.readthedocs.io/en/stable/tutorial/obfuscation.html#using-outer-file-to-store-runtime-key)、[Nuitka 变更记录](https://nuitka.net/changelog/Changelog)、[Commercial 资源保护](https://nuitka.net/doc/commercial/protect-data-files.html)、[traceback 加密](https://nuitka.net/doc/commercial/traceback-encryption.html)、[PyLocket FAQ](https://docs.pylocket.com/faq/)、[PyLocket 元数据](https://pypi.org/pypi/pylocket/1.1.20/json)、[CodeEnigma README](https://github.com/KrishnanSG/codeenigma)、[CodeEnigma 元数据](https://pypi.org/pypi/codeenigma/1.2.0/json)。这不是保护强度排名，也不据文档缺少某个词断言竞品没有某功能。

### 3.4 研究：没有支持继续堆 AST“抗 AI”变换的新证据

- [BinDeObfBench，2026-04-09](https://arxiv.org/abs/2604.08083)：二进制伪代码反混淆评测，强调推理能力与任务适配；不能换算为 Python 产物恢复率。
- [Protected Code 论文](https://arxiv.org/abs/2609.04220)：C++／Go／Java／JavaScript 的执行型翻译与补全研究，支持以行为测试衡量效果；没有实测 pyobfus/Python。页面编号与提交日期不一致，沿用原路线图的限制，不据编号推导新近性。
- [人类理解研究，2026-03-08](https://arxiv.org/abs/2603.07668)：Python／JavaScript 输出预测任务，不同改名强度的效果不单调；这既不是生产破解测试，也不能证明某配置对人或模型一定更强。
- 本仓 [10-12 静态探针](LLM_RESISTANCE_STATIC_PROBE_2026-10-12.md) 仍是更直接的自有证据：两个模型对 Community 六样例均恢复成功；L3 的静态结果不能说明授权运行时安全。

结论是研究推断：现阶段投入多模块保护的实际覆盖、密钥不随包交付及运行／调试正确性，比再添加未经验证的 AST 变换更合理。没有找到足以宣称“pyobfus 抗最新 AI”或“任何保护都无用”的证据。

## 4. 功能缺口应怎样收窄

### 4.1 Community：独立文件目录模式的 mapping

`cli.py::_report_fusion_options` 仍明确提示 `--no-cross-file` 模式不写 `--save-mapping`。这是现有工作流缺口，不是竞品驱动的新花样。

最低验收：两个模块将不同函数改成同一个混淆名时，各自 traceback 都能按文件恢复；绝对／相对路径、多帧、未知帧和错误 Build ID 有明确结果；旧版 mapping 仍可读取。嵌套同名作用域若不能唯一定位，必须保留歧义而不是猜一个名字。单个全局反向字典不能解决该问题。

归 Community：正常调试与本地验证不可收费。实现不应借机做远程 mapping 托管、账号系统或自动上传。

### 4.2 Pro：目录 fusion 先设计一个可交付子集

本轮代码再次确认 `core/fusion_options.py` 的 **14 个字段**在默认跨文件目录构建中跳过；字符串加密等其他 Pro 变换不在这 14 项之内，不能称“目录模式没有 Pro”。既有警告／报告已实现，不重开“补提示”项目。

建议第一阶段只论证：**保持包结构的多模块 L3 顶层函数 + 应用提供密钥 + 完整 mapping/report**。不把 fusion 理解成强行合并所有文件；不一次支持全部 14 个选项。

设计须回答：跨模块引用与原始限定名匹配、运行时注入次数、`__init__` 与循环导入、动态导入／插件、async 与闭包边界、多进程初始化、加载顺序、错误／缺失密钥、无授权状态写入、traceback 反向定位，以及单文件模式输出契约。方法／嵌套函数继续明确跳过，除非另行设计。

门槛：维护的多模块合成应用、现有与全新目标环境、名字／语法／行为差分、错误 key 失败、无需 builder 的 runtime 安装、报告与真实输出一致。不得把“字符串不可见”作为强度验收；授权运行者的可观察性仍须如实说明。

### 4.3 其他候选与解冻条件

| 候选 | 本轮判断 | 解冻依据 |
|---|---|---|
| H 的 B2/B3（复杂 init、循环导入） | 不因自混淆再扩范围 | 真实项目最小复现；Community 正确性处理 |
| 参数改名 | 保持维护者的暂缓决定 | 用户确实要覆盖的私有调用面，并证明关键字调用／反射安全 |
| Vault／embed-data 外部 key | Pro 候选 | 明确资源类型、读取接口、key 生命周期、离线交付需要 |
| L3 方法／嵌套函数 | Pro 候选 | 真实覆盖缺口；先处理绑定、闭包和继承语义 |
| PyInstaller／Nuitka onefile、Windows 打包矩阵 | 可做小型组合验证，非独立打包器 | 新用户问题或现有 fixture 暴露失败 |
| `.pyc` 泄漏／冻结包检查 | 保持候选，不自动纳入交付检查 | 可说明来源和低误报的样本集 |
| 指纹／买家归因扩展 | 后置 | 先验证现有组合的可恢复性与误归因边界 |
| 企业 KMS、远程服务、原生 VM、云端销售平台 | 不立项 | 重复付费需求和维护资源，不能靠竞品存在替代 |

## 5. 本轮验证与尚未回答的问题

### 5.1 原生 Python 3.15：两个缺口已在发布 wheel 复现

解释器：Linux x86_64 CPython 3.15.0，来自 [python-build-standalone 20261013](https://github.com/astral-sh/python-build-standalone/releases/tag/20261013)，下载后核验 GitHub 资产摘要：`e02a368dd5dc76ffe0599e5109ad6c1ee84e597910758b0e006bab25372a8921`。

先对当前 checkout 跑五个合成样例，再直接解压 PyPI **0.7.5 wheel**（SHA256 `a06f2db3138aab3ec1c9e7beb735210aa9ac3bd5cdb6be96ffd4096b8aee7bd7`）复测两个失败样例和一个对照。通过 `__file__` 核实第二轮确实导入发布 wheel，原文和产物都由独立的原生 3.15 子进程运行。构建使用 `CrossFileOrchestrator(ObfuscationConfig.community_edition()).obfuscate(src, out)`。

| 样例 | checkout | 发布 wheel 0.7.5 | 结果解释 |
|---|---|---|---|
| 普通 `from ... import ...` | 行为相同 | 行为相同 | 有效对照 |
| `lazy from ... import ...` | 构建成功、行为不同 | 构建成功、行为不同 | PY315-1：导入副作用提前 |
| 普通 `lazy import ...` | 行为相同 | 未重跑 | 不扩大失败结论至全部 lazy 导入 |
| 列表推导式解包 | 行为相同 | 未重跑 | 不扩大失败结论至全部 PEP 798 |
| 字典推导式解包 | 构建失败 | 构建失败 | PY315-2：`'NoneType' object has no attribute '_fields'` |

PY315-1 最小输入：

```python
# calculator.py
print("LOADED")
class Calculator:
    pass
```

```python
# app.py
lazy from calculator import Calculator
print("START")
print(Calculator() is not None)
```

原文输出 `START → LOADED → True`，产物变为 `LOADED → START → True`。原生 AST 探针同时确认 `ImportFrom._fields` 含 `is_lazy`，重写前为 `1`、重写后为 `None`。这不只是格式变化，可能影响初始化／注册时机。

PY315-2 最小输入：

```python
rows = [{"a": 1}, {"b": 2}]
values = {**row for row in rows}
print(values)
```

原文输出 `{'a': 1, 'b': 2}`；构建失败。尚未完成异常栈根因定位，不能据报错认定仅改某个 visitor 即解决。

限制：这是 Community、Linux x86_64 的小样本，不是全平台 3.15 支持认证，也不是已支持的 3.9–3.14 回归。第二轮直接读取发布 wheel，但复用了现有纯 Python 依赖路径，不冒充干净 pip 安装。脚本入口已加 multiprocessing 的 `__main__` 守卫；早期无守卫探针出现的启动错误已排除，未登记为产品缺陷。所有探针 HOME／USERPROFILE 都指向临时目录。

### 5.2 MCP：本地 stdio 已真实协商到新协议

临时独立环境安装 SDK **2.3.0**，不改变仓库 venv 的依赖。对当前 MCP 0.3.13 服务启动真实子进程：

| SDK / 客户端模式 | 实际协议 | serverInfo | 工具数 | 只读调用 |
|---|---|---|---|---|
| 2.3.0 / legacy | `2025-11-25` | `pyobfus / 0.3.13` | 9 | `list_presets` 成功 |
| 2.3.0 / auto | `2026-07-28` | `pyobfus / 0.3.13` | 9 | `list_presets` 成功 |

另用原始 JSON-RPC 向现有 1.x 和临时 2.3.0 发送相同 legacy 请求，核对文本 JSON 与 `structuredContent` 的封装形状，不能把 SDK 的 `result` 包装误判为丢失业务字段。未启用远程服务，未发送用户源码、未调用修改项目或启动 trial 的工具。

这足以撤销“本地 stdio 必须换 HTTP 才有新协议”的当前限制性判断。仍未完成 Windows 原生宿主、Python 3.10、全工具线路合同、干净正常依赖解析等验收，**不因此直接放开上限或宣称所有宿主已经兼容**。09-12 具体环境为何给出不同结果，仍未复原。

小型证据与探针脚本保存在本地忽略目录 `docs/internal/research-2026-10-20/`，公开报告仅记录可复现合成输入和结论，不提交下载的解释器／依赖环境。

维护者已确认下一首要任务为 Python 3.15 兼容修复与支持验收，留待后续独立 session 实施，见 [支持计划](PYTHON315_SUPPORT_PLAN.md)。MCP 发布条件复审与新 Pro 设计仍属后续候选，保留各自的范围决定、独立审核、合并与发布步骤。
