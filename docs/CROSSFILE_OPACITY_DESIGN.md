# 多模块 L3 + 应用密钥：最小子集设计

状态：2026-10-22 阶段 3 设计；两路独立审核意见已逐项修订，最终复核完成，可作为限定范围的未来实施输入。本轮只交设计，未实现下列新开关，也未改变已发布产物行为。

## 1. 用户、问题和边界

目标用户是交付多模块 Python 应用、并已有自己的授权／密钥分发方式的 Pro 使用者。他们需要一致的跨模块改名，同时让部分算法函数在磁盘上以密文交付。不是为社区版新增规模限制，不建设托管授权平台，也不宣称授权运行者无法取出代码。

当前证据：Core 0.8.0 默认跨文件目录构建跳过 14 项 fusion 选项；单文件／独立文件模式已有 L3 和应用 key provider，但独立模式不保证跨文件导入改写。阶段 2 补了独立文件调试，并没有补跨文件 L3。当前没有新增客户需求调查；此设计由维护者明确批准，实施仍需另行定范围。

分层遵循 `EDITION_BOUNDARY_POLICY.md`：L3 变换、密钥装配与运行保护属于 Pro；基本名字映射、验证、跳过／失败说明及本地调试属于 Community。Core 只传递不透明的计划和结果，不包含加密实现、key provider 装配或受保护字节码。

## 2. 明确的 opt-in 与首批范围

建议增加默认关闭的 `crossfile_opacity` / `--crossfile-opacity`，只用于新能力，不改变旧选项组合的 warning／跳过语义。以下是拟议接口，不是当前可执行示例：

```bash
# APP_L3_KEY 由构建者安全提供，值不得写到命令参数、配置或报告。
pyobfus src/ -o protected/ --level pro --crossfile-opacity \
  --opacity-config opacity.toml --bind-key-env APP_L3_KEY --jobs 1 \
  --save-mapping private/mapping.json --build-report private/report.json
```

新开关开启时必须同时满足：有效 Pro 授权、跨文件目录输入、TOML opacity_config、应用密钥来源。首批只支持 TOML 选择，不支持手写 @opacity 标记；现有单文件／独立模式不受此限制。第一阶段明确要求 `--jobs 1`；自动／多 worker 不暗中改变为串行，而是给出明确配置错误。先限制并发，避免把密钥缓存、Windows spawn 和并行失败恢复一并做成项目。

新模式的功能字段穷举为 `{crossfile_opacity, opacity_config, bind_key_env, jobs=1}`；selective_opacity 手写标记路径不在首批。allowlist 预检必须覆盖 `core/fusion_options.py::FUSION_FIELDS` 的全部 14 项及依赖字段 `bind_device_id`、`expire_warn_days` 等，未允许字段须为默认值，不能只检查 fusion_enabled() 的子集。新开关下请求 seal、vault、scrub、fingerprint、device binding、到期／运行次数／平台限制、资源嵌入等其他 fusion 字段，预检报错；不静默执行部分组合。原有目录内容变换仍按原契约运作，但其加密密钥不因此受应用 provider 管理；报告须把 L3 密钥范围写清。

不开新开关时维持已有目录行为；单文件与 `--no-cross-file` 的既有 Pro 路径不变。不得直接清空 `FUSION_FIELDS` 或让全部 14 项自动进入目录管线。

## 3. 可保护对象与拒绝规则

首批只支持直接位于模块体、无装饰器的普通同步函数。作用域判定在原 AST 上进行：自己的作用域含 yield/yield-from/await、async 构造，或带 type_params，均不可选；函数体有嵌套 def/class 也不在首批。普通 lambda 和 comprehension 可包含在函数体，但必须验证编译得到的目标 co_freevars 为空，且递归 CodeType 常量均能往返；在 3.10/3.11 的独立 comprehension code object 上单独验收。generator lambda 及异步 comprehension 不在首批。

绑定必须唯一且稳定；重复 def、后续赋值／装饰器重绑定／del、同名 import、其他函数中的 global 写入，以及无法证明的动态导出／模块 __getattr__ 均不得默认视作稳定函数。普通跨模块 global 引用可用，但不支持依赖函数 __code__/__defaults__/__globals__ 严格对象等价的应用（wrapper 语义见下）。

规则根为输入目录之下：`src/pkg/a.py` 对 `pyobfus src/` 是 `pkg.a`，不是 `src.pkg.a`；__init__.py 沿用 orchestrator 的路径规则，私有计划记录实际解析根和文件键。TOML 保持 first-match 语义，只 materialize encrypted 层；其他层继续既有 Core 变换，不宣传为新的 L0/L1 保护模式。

| 请求 | 新模式结果 |
|---|---|
| encrypted TOML 匹配合格目标 | 进入显式目标集合 |
| encrypted TOML 匹配不支持的对象 | 构建失败并列原因；不以 skip 代替已请求保护 |
| 规则没有匹配任何对象 | warning；总合格目标为零则失败 |
| 任意手写 Pro 标记或用户源码引用 Pro builder | 首批拒绝，提示用 TOML／runtime API；不能留下 builder 运行依赖 |
| 用户自己的 Layer/opacity 名字 | 不按名字猜成 Pro 标记；被选函数上的任何额外装饰器按不支持处理 |

已知字面量动态 Pro builder 导入也应拒绝；不声称静态分析能识别任意字符串构造的动态加载。手写标记支持留给绑定感知设计，不复用裸名字匹配／导入删除的旧 prepass。

wrapper 不等于原函数对象：调用仍经过 functools.wraps wrapper，inspect.signature 经 __wrapped__ 可用，但 __defaults__/__kwdefaults__/__code__/__globals__ 是 wrapper 的属性，不能声称严格反射等价。递归增加 wrapper 帧，RecursionError 深度可能提前；测试比较约定的调用结果、参数行为和错误类型，不要求 traceback 帧数相同。首次调用后 __wrapped__.__code__ 明文可读。GIL 模式下并发首次调用可能重复解密；首批不承诺 free-threaded 支持或强制撤销已解密代码。

## 4. 计划与变换顺序

```mermaid
flowchart LR
  A[原文分析与跨文件绑定] --> B[Pro 选择计划：原文件与原限定名]
  B --> C[Core 既有一致改名与导入改写]
  C --> D[Pro：仅已选函数编译加密并注入 runtime]
  D --> E[逐文件语法验证、报告与私有 mapping]
```

1. 父进程和 Pro adapter 都确认新开关／许可，缺失 adapter 或无授权非零退出，不能退回普通构建。完成组合、输入、目标路径和构建密钥预检后才建 staging，不运行用户模块。
2. Pro planner 读取未经插入标记的原 AST 和 Core 只读绑定分析，按文件键、原绑定 id（含定义位置／source digest）和原限定名生成不可变选择计划。Core 不运行 opacity marker prepass，不向分析输入注入 Pro import。`pkg.py` 和 `pkg/__init__.py` 等运行时导入身份冲突在新模式预检拒绝。
3. Core 运行既有跨文件改名、局部改名、导入与模块属性改写，另外输出每文件 `{original_binding_id: final_binding_name}` 的可验证对应表。它是独立元数据，不依赖 unparse/reparse 后丢失的 AST node identity；Core 不解析 TOML 或 Pro 层语义。
4. Pro adapter 接收 `(final_source, selection_plan, binding_map)`，用显式 final-name 目标集合调用专用变换入口，绝不在短名源码上重新匹配 TOML 或按裸 decorator 名字选目标。每一目标须恰有一个顶层 FunctionDef、无额外同名模块绑定，找不到或多于一个就失败。仅 compile 不执行模块代码。
5. 加密接口直接接收运行时 key-expression 模式：内存 key bytes 用于加密，生成 AST 直接引用 provided_key 调用，任何中间源码／AST 都不得先出现 raw-key 常量再靠字符串替换移除。helper、key alias、cipher 常量、dispatch 和 runtime import 名称按最终标识符集合分配，禁止重用固定 _LAYER_KEY 等假定未占用的名字。
6. 统一插入点保留 docstring 和 future imports；stdlib 解释器 guard 在 runtime/provider 及用户初始化代码之前，其他 helper 在首次使用前，不能插到 future import 之前。文本 shebang／编码 prologue 最后恢复。`__lazy_modules__` 全模块策略首批拒绝，直到有独立 eager-helper 注入验收；显式 lazy import 必须保持用户导入副作用时序。
7. 每个加密目标在构建进程内 decrypt round-trip，验证 CodeType、final co_name、专用 co_filename、空 co_freevars、参数计数和 flags；编译最终模块确认目标只有 stub body。对输出、mapping、report、捕获日志检查 raw key、repr 形式、base64／hex 等已知表现，不允许提交；这是泄漏回归防线，不是对任意隐写的证明。key 对象 repr 脱敏且拒绝 pickle，验证子进程的 env 去掉密钥变量。
8. 仅有 L3 的文件注入一次 runtime/key 获取；未选文件不注入。Pro adapter 留在 pyobfus_pro，Core 只传递绑定元数据和不透明结果，不复制 apply_post_passes 全部机制，不通过清空 config 来绕过 allowlist。

所有输出先完成 staging 和验证再进入发布步骤；本阶段只设计这些不变量，未实施 adapter。

## 5. 应用密钥和运行初始化

复用 runtime 0.1.1 的已发布接口，不另造全局许可服务：

```python
# 由应用 bootstrap 执行，必须早于任何受保护模块的导入。
from pyobfus_runtime import set_key_provider

set_key_provider(load_authorized_application_key)  # 返回构建时使用的同一份 32 bytes
from protected_app import main
```

同一构建的受保护模块使用同一应用密钥；现有 GCM 没有绑定模块／函数的 AAD，不能宣称防跨模块换 ciphertext、抗篡改或 per-module isolation。不在首批增加每模块 KDF／新协议。密钥由构建环境的指定 env 读取一次并验证，再保留在该构建进程内存。不得进入 config 序列化、mapping、report、provenance、缓存、异常文本、命令行或输出明文常量。模块的 runtime key 调用可复用既有 provider 优先、环境变量 fallback 的契约；provider 不在运行时偷偷请求 pyobfus 许可服务。

密钥在受保护模块的全局变量和 dispatch 闭包中保持可访问；删除一个 key alias 不能被宣传为防授权运行者提取。provider 可能为每个受保护模块调用一次，不保证全进程恰好一次；应用必须返回稳定的同一把密钥。导入阶段调用 provider，函数第一次执行时再解密，这是两个不同的时间点。缺失／长度错误在导入时失败；长度正确但错误的 key 应在首次加密函数调用时清楚失败，不能降级到明文函数。首批不承诺更换 provider 会撤销已导入模块或清除已解密 code object。

`python -m protected_app` 和 console-script 的 `protected_app.cli:main` 都会先执行包 __init__，因此 bootstrap 必须在其外部。预检发现 __init__ 本身被选或会早于 provider 导入受保护子模块时，应报告初始化顺序风险。env fallback 已设置时，晚注册 provider 可能先使用 env key，必须有独立负例。Bootstrap 不得先导入受保护包来取得 provider，也不得让包 `__init__` 在注册前触发受保护子模块；文档必须展示这个顺序。父进程上的 `set_key_provider()` 不会自动出现在 spawn 子进程中：每个子进程由其应用 bootstrap／initializer 在首次导入之前注册；fork 也不作为绕过初始化验证的支持承诺。

一个 runtime import／一次 key 获取指每模块，不是每整个包一次。循环导入是否有效按原 Python 规则；新增 helper 的初始化不得访问其他用户模块，以免制造新环。动态导入只能使用现有 Core 能保守保持的模块路径；不扩张名称反射／插件发现的兼容声明。

## 6. 字节码、调试与可检查性

L3 产物依赖构建者与目标的 CPython 字节码／marshal 兼容范围；每个 L3 模块须在 runtime import／provider 调用／marshal.loads 之前执行 stdlib-only guard，比较 sys.implementation.name、importlib.util.MAGIC_NUMBER 和规范化 Py_GIL_DISABLED。任一不符就 ImportError，并只说明构建／目标解释器标识。该 tuple 进入报告；AAD 绑定留待单独 runtime 协议变更。首批按相同实现及 minor version 验收，不能继承 Community 普通源码的跨版本可移植性。不得只凭 Core 支持 3.9–3.15，就宣称一个加密 artifact 能跨这些版本运行。不同 minor／free-threaded／冻结打包留在单独矩阵。

独立审核已证实：不能简单声称“禁用行表以后用现有 v1 reader 就能恢复函数名”。当前 v1 根推断依赖可用行表；全 L3 trace 没有可投票帧，混合 trace 的绝对 caller 与相对 payload 也处于不同根。

因此新 opt-in 模式必须同时提供专用加密 code-frame 身份及 reader 扩展。建议为每次构建生成一个不含密钥的 opaque artifact id，编译每个受保护模块时使用 `<pyobfus-l3:<artifact-id>:<relative-file>>` 作为 `co_filename`；尖括号包裹既不匹配普通 .py 文件后缀，也使 linecache 不会从 sys.path 误取 stub 文件行。私有 version-1 mapping 增加可选 `encrypted_code` 表，将该完整 code 标识 关联到 source file、该模块被加密的短名／原名以及“原行号不可用”原因。新 reader 仅精确匹配该表，不做部署根投票或短路径回退；未识别的保留 code 标识 不进行推测。旧构建不写该表，原 v1 路径保持不变；旧 reader 不提供新身份验证，不能作为新模式的验收工具。

加密 code object 的行号来自加密前最终改名文本，不等于最终 stub，也不等于原文行号。首批对含 L3 模块禁用普通 statement line table，并记录原因。同一模块中未加密的普通函数仍使用普通文件名，不在 encrypted_code 表中；由于现有 v1 根推断依赖行表，这些帧首批可能既不能恢复原行号也不能恢复原函数名，保持原样。这是首批明确接受的调试限制，不能把下表的“可用名字 mapping”理解为该文件全部函数都能恢复；专用加密帧只恢复函数名，保留 code 标识 与加密代码行号，不输出伪造的原行号。JSON 使用现有 `original_line: null` / `unmapped` 位置状态，并增补 code-frame 文件归属信息和 name-only 提示，不把名字恢复冒称完整位置恢复。新格式扩展无需升级为独立文件的 v2，但实现须明确新 reader 的最低 Core 版本。

未受影响模块继续使用现有行表；runtime helper 帧不被 code 表收录。全 L3 trace、绝对未加密 caller + 专用 code 标识 payload、同包两函数和错误 artifact id 都必须用真实产物异常验收。这个 code 标识 是一致性标签，不是签名；不泄露构建机路径、不含源代码／密钥，也不证明任意提交的 traceback 真实可信。若要恢复加密函数原行号，必须另行设计 code-location 表，不能借用 stub 行表。

shareable build report 只新增模式、合格／加密／拒绝计数、原因直方图、runtime 要求、解释器 tuple、密钥来源类型／env 配置名和非秘密 build id；保留已有相对路径标签规则，不新增原函数限定名或详细选择。每文件／每原绑定的覆盖和选择计划只写入 mapping 的私有 `opacity_plan` 段，继承 mapping 的保管和交付检查，不把原有可分享 report 改成另一份名字映射。详细计划不写 stdout，密钥值不出现在任一产物。

每个真正 L3 模块携带同一非秘密 build id；delivery check 按本次 manifest/report 逐文件摘要和 L3 id 检测混合构建，不把其当签名或运行时完整性保护。随机 GCM nonce 允许不同构建字节不同，不能用跨构建字节相等验收。

## 7. 缓存、失败和无状态要求

新增模式第一阶段完全重建，拒绝 --incremental；密钥内容不能做普通落盘缓存键。

首批使用版本化的全新目标路径：output、mapping 和可选 report 不能覆盖任何既有路径，并要求同一文件系统；不承诺跨平台多路径原子覆盖旧发布。staging 是目标相邻的私有目录（POSIX 0700／Windows 当前用户受限 ACL），不放共享 /tmp。输出、私有 mapping/plan、report 使用同一 build id，staging 内不落 raw-key 中间源码。

最终先提交新的私有 metadata，最后将带完成 manifest 的全新应用目录整体 rename 到尚不存在的 output；manifest 记录本次 build id 与必要产物摘要。CLI 只有全部通过才退出成功。错误／中断不动任何旧发布路径；本次可能留下未完成 staging 或孤立的新 metadata，按本次 ownership manifest 恢复，不能把它当成功交付。目录整体提交不保留上次孤立模块。新模式不支持构建期间并发消费未完成路径。后续如需覆盖非空 output、跨文件系统 metadata 或 crash-durable 多路径事务，必须先设计恢复协议，不能以多次 os.replace 冒称单次原子事务。

所有构建、target 与负例使用测试 tmp HOME／许可路径，既不读取维护者的真实 trial/license，也不在真实 HOME 生成运行次数。目标仅安装 redistributable runtime，不需要 Core、MCP 或 Pro builder。若生成的新 runtime 行为超出 0.1.1 契约，必须先改版本、先发 runtime；不能让 Core 指向线上不存在的函数。

## 8. 实施验收矩阵

| 类别 | 必须证明 |
|---|---|
| 原绑定与跨模块调用 | 两模块同名函数、包重导出、模块属性调用、相对导入、`__all__`、普通循环导入；原文与 Community 对照；更改物理文件创建顺序不改变选择归属 |
| 调用语义 | 默认值／kw-only／注解／递归／模块全局引用／异常行为；明确拒绝 async、generator、额外 decorators、条件／重复定义、泛型和未支持闭包 |
| 初始化 | bootstrap 正确与错误顺序、`__init__` 提前导入、provider 每模块调用、动态导入、fresh spawn；无 provider、错误长度、错误 key 的不同失败阶段 |
| 注入与语法 | helper 名字冲突、future/encoding/shebang、docstring 保留、非 ASCII 路径／标识符、3.15 lazy import 副作用时序；默认 Core 及不开新开关的产物不退步 |
| 保护与调试 | 只有被选目标计为 L3；key 值不在交付物／调试资料／日志里；原包结构和可用名字 mapping；加密位置不误用 stub 行表；含源相对文件键的专用 code URI |
| 交付与失败 | 真实多模块应用在未装 builder 的 runtime-only 环境运行；装公开 runtime 0.1.1；半途失败不改旧路径；新路径提交／恢复、混合 build id 及 digest 检查；干净目录交付检查 |
| 平台与版本 | 至少 Linux/Windows 同 minor 的 3.10、3.12、3.15；其余支持矩阵按实际发布声明补齐；不以单机测试宣称全部支持 |
| 边界与回归 | 未授权不生成 Pro 保护且不假报成功；Community 四测试根、单文件／独立模式 Pro 及 CLI/MCP 合同不退步；不改 14 项总开关的旧默认行为 |

## 9. 下一步与停止条件

审核通过只意味着设计可作为实施输入。本轮不实现新开关、Pro adapter 或 runtime 扩展。实施前维护者需确认是否接受第一阶段串行、同步顶层函数、TOML-only、无手写标记、全新输出路径、相同 magic/实现/GIL 的字节码、无加密体原行表等限制；若真实需求必须方法／async／完整原行号，则重新定范围，不能把这些限制埋进实现。

公开证据入口：`FEATURE_EXPANSION_RESEARCH_2026-10-20.md`、`Y3_KEY_PROVIDER_DESIGN.md`、`OPACITY_CONFIG.md`、`EDITION_BOUNDARY_POLICY.md`。本设计只根据本仓当前代码作工程判断，不引入未复核的竞品或安全强度结论。

## 10. 独立审核修订记录

第一路独立审核复现了全 L3 与混合绝对／相对 frame 无法按现有 v1 恢复函数名的问题。§6 已将其改成必须实施的专用 code-frame 身份与 reader 扩展，不再依赖既有根投票。它属于新 opt-in 模式的基本调试验收，随能力免费提供，不新增 runtime API，也不把加密体原行表塞进首批范围。另一引擎进一步指出了选择 carrier、raw-key 中间源码、解释器 guard、prologue/linecache、拒绝语义及 report 隐私缺口。现已收窄首批为 TOML-only、显式绑定表、直接 key-expression、严格解释器 guard、独立 code namespace、counts-only shareable report + 私有 mapping 段，并补上 staging 完成与恢复不变量。


两路最终复核均认为修订后的限定设计可以作为实施输入，仍以未来实现与验收为条件。第二路最终补充的同模块普通函数调试缺口已在 §6 明示；不扩大首批实现范围，也不把其函数名恢复说成已有保证。审核原始记录留本地忽略目录。

### 必补验收反例（两路审核）

- final-source 选择不得误认用户 Layer/opacity，手写字符串／重导出 marker 在新模式必须明确拒绝；TOML-only 不复用裸名 decorator 消费。
- docstring + future、prologue + future、shebang/encoding + docstring；占用所有旧固定 helper 名字；全模块 lazy policy 拒绝。
- 输出各类 key 表现扫描；cipher 往返，不执行用户代码；编译器 magic 不匹配在 provider 之前失败。
- 全 L3 及绝对 caller + 专用 code frame、错误 build id、linecache 不显示 stub 行；旧普通 v1 trace 不退步。
- __init__ 提前导入、-m 与 console-script、晚 provider 与 env fallback、每模块多次 provider 和 fresh spawn。
- 不同 module 的共享 key／cipher swap 不被宣称为认证；混合 build id 由交付检查报告；wrapper 反射、递归与并发首次调用的限制明确。
- 任一步骤失败旧发布保持完好；全新路径的完成 manifest 和 metadata id 一致；不通过日志或异常泄漏 key。

## 11. 2026-10-24 范围收敛与实施切片

维护者要求按交接顺序推进。本项交付是将现有设计收敛为可执行清单；下列新能力仍未实现，不能使用上述拟议 CLI 命令作为现有功能。前置的纯转换 API prologue 修复独立处理，不接入新目录模式。

首批沿用 §2–§8 的完整约束：Pro opt-in、TOML-only、稳定绑定的同步顶层函数、`jobs=1`、应用密钥、全量重建、全新输出及 metadata 路径、同解释器字节码。方法、async/generator、手写 marker、其他 fusion 组合和冻结包不进入首批。加密帧只恢复名字；含 L3 模块的普通函数帧可能保持原样，这一限制必须在配置帮助和报告中可见。

| 切片 | 交付与验收 | 依赖 |
|---|---|---|
| A：预检与绑定计划 | 原 AST 的稳定目标集合、14 项 fusion 字段及依赖 allowlist、配置/路径/解释器拒绝原因；不读取真实许可状态的合成测试 | 本设计 |
| B：Core 对应表 | 原 binding id 到 final name 的显式对应；两模块同名、相对导入、重导出、循环导入及创建顺序反例；Community 默认产物不变 | A |
| C：Pro adapter | 只消费显式目标；key-expression 直接生成，无 raw-key 中间文本；compile/decrypt 往返、名字冲突、future/docstring/lazy 反例 | A、B |
| D：调试与报告 | 精确 encrypted-code 身份匹配、错误 build id、全 L3/混合 trace；私有 mapping 详细计划与可分享 counts-only 报告；明确 reader 最低版本 | B、C |
| E：发布目录与交付验证 | 私有 staging、新路径提交、完成 manifest、失败恢复及混合构建检查；runtime-only 干净安装验证 | C、D |

切片不是可绕过的验收阶段：A/B 完成不能宣传保护已经生效，C 完成不能忽略 D/E 直接交付。runtime 0.1.1 是否足够必须在 C 的接口核对后确定，若需要扩展先独立升级并发布 runtime。Linux/Windows 与 3.10/3.12/3.15 的实际结果应逐格登记；本轮 Python 3.12/Linux 的已有修复回归不能代替该矩阵。

实施时按切片准备审核材料，每一块记录支持与拒绝实例；合并、版本号和发布仍按维护者批准执行。本轮未增加开关、planner、adapter 或 runtime API。
