# AI 时代路线图独立复核（Claude，2026-10-12）

评审对象：[增强路线图](AI_ERA_PROTECTION_ROADMAP_2026-10-12.md)（工作区未提交版本）；
任务书：[复核 Prompt](AI_ERA_ROADMAP_REVIEW_PROMPT.md)。基线提交 `2bb2cd3`（main），工作区另有
`CURRENT_PLAN_ZH.md`／`TODO.md` 两处未提交改动，本轮未动。

本文件只记录审查结论，不修改路线图或产品代码，不授权实现、发版、部署或付费模型调用。
证据标注：**[实测]** 本轮在隔离临时目录（`HOME` 指向临时目录，未触碰真实 `~/.pyobfus`）中实际运行；
**[读码]** 只读代码／文档，未运行；**[外部]** 一手外部来源，检索日 2026-10-12。

---

## 1. 结论：需重大修改（方向成立，顺序与前提要改）

「离线 Python 应用交付优先」这个方向成立，Community／Pro 分层的原则也基本符合
[版本边界政策](EDITION_BOUNDARY_POLICY.md)。但路线图建立在一个不成立的前提上：它假定已有 Pro
保护在离线应用场景中**已经能交付**，只需「检查／报告／补齐」。复核发现两处现存缺陷直接击穿这个前提：

1. **已发布的 `pyobfus-runtime` 0.1.0 不含 Y-2／Y-3 所需接口**。Core 0.5.30 生成的
   `--bind-key-env` 与 `--expire-warn-days` 产物，在只从 PyPI 安装 runtime 的干净环境里运行即失败 **[实测]**。
   路线图 §4 把 Y-1／Y-3 写作「已发布、后续 Core 已采用」。
2. **Pro build fusion（opacity／vault／key provider／水印／期限／embed-data）在默认的目录构建中不生效**，
   只能单文件或 `--no-cross-file`，而后者不写 mapping **[读码]**。离线「应用」通常是多模块目录，
   这正是路线图首选场景。

因此近期主线应先是**让现有 Pro 保护能在离线目标上真实安装运行，并如实报告未生效的部分**，
然后才是新的交付检查，Agent 实验降为低成本协议工作。候选 A 的范围应收窄到外部工具做不到的那几项；
opacity「四层补齐」应删除（实际只有 L3 有实现）；归因（候选 D）应先收窄为「如实声明 + 拒绝静默失效组合」。

---

## 2. 问题清单（按严重程度）

### 阻断

**B1. runtime 发布滞后于 builder：Y-2／Y-3 产物在 PyPI 环境中不能运行**

- 证据：PyPI `pyobfus-runtime` 只有 `0.1.0`；tag `runtime-v0.1.0` → `e04122a`，早于 Y-2 提交
  `5d74c7c` 和 Y-3 提交 `d28cbb7`（`git log runtime-v0.1.0..HEAD -- pyobfus_runtime`）。
  源码 `pyobfus_runtime/pyobfus_runtime/binding.py:100,119,328` 有 `set_key_provider`／`provided_key`／`warn_days`，
  但版本号仍是 `0.1.0`（`pyobfus_runtime/pyproject.toml:7`），所以同一个版本号对应两份不同代码。
  Core 依赖声明只有 `pyobfus-runtime>=0.1,<1`（`pyproject.toml:59`）。
- [实测] 新建 venv、从 PyPI 装 runtime 0.1.0：已安装包中 `provided_key` 出现 0 次。
  `--bind-key-env` 产物报 `ImportError: cannot import name 'provided_key'`，
  `--expire-warn-days` 产物报 `TypeError: ... 'warn_days'`。对源码 runtime 两者都正常。
- 为什么测试没发现：pytest 把 `pyobfus_runtime` 源码目录放进了路径（`pyproject.toml` pytest 配置），
  所有测试都用源码 runtime；dogfood Lane C 只测 builder，不测目标环境。
- 影响：CHANGELOG 0.5.30、`CURRENT_PLAN_ZH.md` 中「Y-1/2/3 全清零」的说法对实际用户不成立；
  维护者自有的下游（[Y-3 设计](Y3_KEY_PROVIDER_DESIGN.md) 已公开点名）若按 PyPI 安装会直接失败。
  该下游是否 vendored 源码 runtime 本轮未核实。
- 修正：发布 runtime 新版本（如 0.1.1）；builder 在使用这两个选项时声明并检查最低 runtime 版本；
  增加一项「只用已发布 wheel、不挂源码路径」的目标环境测试（见 §9 首个实践）。
  这属于「影响用户的 bug」例外，是否随 0.7.0 一起发布由维护者决定。

**B2. fusion 在默认目录构建中不生效，路线图没有提到**

- 证据：`pyobfus/cli.py:1056-1067` 在目录 + 跨文件（默认）模式下只打印一条 Note，说明 fusion 机制不应用，
  建议改用 `--no-cross-file`；该 Note 只列了 v0.5.1 的五项，没有列 `--bind-key-env`／`--expire-*`／`--embed-data`。
  `--no-cross-file` 下 `--save-mapping` 不写 mapping（`[Unreleased]` 只补了警告）。
  build report 的 `disabled_transforms` 只记了 5 项（`pyobfus/core/build_plan.py:150-156`），
  opacity_config、fingerprint、bind_key_env 等未记录。provenance 在 fusion 未执行时仍可能记 `runtime_requirement`
  （`core/provenance.py:70-91`，[读码] 推断）。
- 影响：多模块离线应用要么拿不到 Pro 保护，要么失去目录构建的正确性修复和 mapping；
  build report 不会如实说明哪些保护没生效。候选 A「覆盖报告」与候选 C「补齐交付效果」都以此为前提。
- 修正：近期先做到「如实」——Note 与 `disabled_transforms` 覆盖全部 fusion 选项，
  build report／JSON 明确列出未执行项（这是正确性与诚实验证，属 Community）；
  然后单独设计「fusion × 目录构建」是否以及如何支持（这才是真正的 Pro 交付补齐）。

### 重要

**I1. 候选 A 范围过宽，真正的增量很窄**

- 现状 [实测]：`--save-mapping out/mapping.json` 会无警告地写进输出目录；把原始明文拷进 `out/` 后
  `--check out` 报 0 条，并提示「Low risk」。build report 把多出来的 `.py` 当 obfuscated-output 计哈希，
  不看非 `.py` 文件。目前没有任何功能检查交付物里是否混入 mapping、原文、`.pyc`，也没有逐函数覆盖报告。
- 可复用：build plan 已给 mapping 标 `retain-internal`、给输出标 `ship`（`core/build_plan.py:67-115`），
  provenance 已有输入文件 SHA-256，reason codes 已预留 `preserved.*` 词表（`core/reason_codes.py:12-17`）。
- 可由外部工具覆盖的部分 [外部]：check-wheel-contents（W001 `.pyc`、W005 多余目录）、
  gitleaks／TruffleHog（凭据，含归档扫描；TruffleHog 为 AGPL，只能外部调用不宜捆绑）、
  pyinstxtractor／pyi-archive_viewer（看清冻结包内容）、diffoscope（构建差异）。
- 修正：首版只做外部工具做不到的三项——(a) 已知私有产物（mapping、原文：按 provenance 输入哈希比对）
  出现在交付目录／wheel 中；(b) 交付文件与 build report 输出哈希的对应关系；
  (c) 回读 Pro 已经写出的处理事实（见 I2），列出匹配／处理／跳过及原因。凭据与通用打包卫生交给外部工具，在文档中给出组合命令即可。
  第一版只覆盖「目录 + wheel」，不做 PyInstaller／Nuitka 冻结包解析。

**I2. opacity「四层」实际只有 L3 有实现，路线图把补齐四层当候选**

- 证据 [读码]：CLI 只对解析为 ENCRYPTED 的函数注入装饰器（`pyobfus_pro/build_fusion.py:424-476`），
  后处理只加密 L3（`pyobfus_pro/transformers/opacity.py:147,189`）。TRANSPARENT／AI_READABLE 在任何地方都没有实现，
  `LAYER_SPECS` 只是描述性数据。范围仅限顶层 `def`／`async def`；手写到方法／类上报 `OpacityBuildError`，
  而 TOML 规则匹配到方法时**静默不生效**。`injected` 计数算出后被丢弃（`build_fusion.py:447,469`）。
- 文档漂移：`docs/OPACITY_CONFIG.md:50` 称「完整四层模型可通过 Pro API 使用」，属夸大。
- 修正：删除「补齐四层」；如有需求，改为「L3 覆盖到方法」这一项单独设计。
  近期只把匹配／注入／跳过（含「规则匹配到不支持的对象」）写进 build report，供候选 A 回读。
  这个数据由 Pro 写出，Core 只读取，不需要把 Pro 解析逻辑搬进 Core。

**I3. 水印与外部密钥绑定静默互斥，恢复完全依赖明文密钥字面量**

- 证据：`--fingerprint` 实际只是把 L3 key 改成确定性派生（`build_fusion.py:89-104`）；恢复用正则读
  `_LAYER_KEY = b"..."`（`pyobfus_pro/forensic/watermark.py:68,234-300`）。所以这个「水印」同时就是随包明文交付的解密密钥。
  `--bind-device`／`--bind-key-env` 会覆盖指纹 key（`build_fusion.py:529-534`），CLI 不拒绝这些组合。
  [实测] 单独 fingerprint 时恢复 `True`；fingerprint + bind_key_env 时 `False`，字面量消失。
  没有 CLI 恢复命令，恢复测试只走 API（`tests/test_integration_all_features.py:254-284`）。
  `forensic/__init__.py:11-12` 称 vault key 也带指纹，CLI 并不如此。
- 外部 [外部]：保持语义不变的改写能把语法层代码水印的检测压到接近随机（arXiv 2507.05512，研究对象是 LLM 生成代码的水印，机制可类推）。
- 修正：候选 D 收窄为「如实声明 + CLI 拒绝或警告静默失效的组合」，只承诺「原样或轻改再分发」场景的买家匹配。
  更强的归因属于新设计，推迟到有重复需求时再做。

**I4. 现有 LLM 抗性试验的结论被攻击者权限高估**

- 证据 [读码]：攻击者零工具，只看混淆源码（`benchmarks/llm_resistance/attacker.py:76,125-131`）。
  C4／C5 没有用 `--bind-device`，`_LAYER_KEY`／`_VAULT_KEY_*` 明文在攻击者读到的产物里，
  而方法文档写的是攻击者没有 layer key（`docs/LLM_RESISTANCE_BENCHMARK.md:76`）。
  C4、C5 各自只在一个自定义样例上测过；隐藏 io 向量只有 2–7 条。
- 外部反证 [外部]：
  - Python 改名后，执行预测通常只降 0–9 点，主要伤害的是意图理解（arXiv 2510.03178，ClassEval／LiveCodeBench）；
  - 混淆代码直接给强模型时 Pass@1 约 90%（arXiv 2609.04220，C++／Go／Java／JS，不含 Python）；
  - LLM 配合确定性工具专攻字符串编码和注入的 helper（Google CASCADE，arXiv 2507.17691，JS）；
  - 运行时 hook `marshal.loads` 可绕过「静态加密、运行时解成字节码」的方案（PyArmor-Unpacker，适用 ≤ v7）。
- 修正：候选 B 必须把「带工具／可执行」列为独立攻击条件，并按密钥位置分开：
  key 在包内、key 由外部提供但攻击者是合法运行者、无 key。现有试验结论只能表述为
  「零工具、单次、静态阅读下」，不能用于营销。

**I5. 需求证据不满足政策 Q5 与路线图自己的「两个独立信号」门槛**

- 「离线应用」的唯一具体驱动是维护者自有的下游；政策 Q5 要求外部证据，路线图 §10 要求两个独立信号，路线图未说明自有下游怎么算。
  现有付费客户的使用场景未知；trial 登记仍为 0（见 `CURRENT_PLAN_ZH.md` 09-25）。
- 修正：方向已定，不重议；但对每个**新增**能力仍适用 Q5。零成本补证据的办法：问现有付费客户
  「是否离线交付、目标平台、是否多模块、授权怎么做」（发信需维护者批准）。
  修复 B1／B2 不受此门槛约束，属正确性。

**I6. YAML 配置可能绕过 `--vault` 与 `--bind-key-env` 的互斥检查**

- [读码，未运行] 互斥校验只看 CLI 参数（`cli.py:592-616`），而 `vault`、`bind_key_env` 都是 YAML 字段
  （`config_schema.py:131,140`），通过 `setattr` 应用。若成立，vault key 会作为明文字面量交付，用户却以为由外部提供。
- 修正：先补测试确认，再把校验移到合并后的配置上。这属于正确性缺陷，走质量主线。

**I7. 「离线」没有定义**

- Y-3 下游实际依赖应用自己的服务器在授权后下发密钥，也就是局域网或间歇联网，不是物理隔离。
  路线图把「无网络时的安装、授权、续期、密钥提供」混在一起。
- 修正：分三档写清——(1) 物理隔离：预置 key 或签名授权文件，到期后只能人工续期，无法远程撤销；
  (2) 局域网／站点服务器：应用自己的 key server（Y-3 provider 正适合）；(3) 间歇联网：宽限期。
  pyobfus 只提供 key 接入原语，不做授权服务器。构建器 Pro 许可与客户应用授权是两件事，文档要分开写。

**I8. 已有 `--embed-data` 被遗漏**

- `--embed-data`（0.5.10）已能 AES-GCM 加密单个文件并生成访问函数，但 key 是同一模块里的随机字面量，
  不能绑定设备或 provider（`build_fusion.py:581-583`、约 720-760 行）。
- 修正：候选 C 第 3 项「资源保护」应从「让 embed-data 与 vault 接入 key provider」开始，不要另起子系统。

### 建议

- **S1 文档漂移**（随下次文档提交一并修正）：`Y1_RUNTIME_DISTRIBUTION_DESIGN.md:3-4`、
  `Y3_KEY_PROVIDER_DESIGN.md:3-4`、`OPACITY_CONFIG.md:50,56-61`、`pyobfus_pro/forensic/__init__.py:11-12`。
  路线图只登记了其中两处。
- **S2 报告格式借鉴 PyArmor trace**：PyArmor 9.x 的 `enable_trace` 逐函数记录「转成 C／跳过 + 原因」，
  文档要求用户据此确认大部分函数已转换 [外部，厂商文档]。我们的 reason codes 已预留 `preserved.*`，直接沿用即可，不必另造 schema。
- **S3 威胁模型补一条**：合法持有 key 的运行者总能取得运行时明文（解密后的 code object），
  外部 key 只防「拿到包但拿不到 key 的人」。PyArmor 官方也承认内存保护和反调试薄弱，并以解释器不可替换为前提 [外部]。
- **S4 `.pyc`-only 是负基线**：近乎所有 CPython 3.8–3.14 `.pyc` 都能被至少一个反编译器还原成源码（arXiv 2608.12853，测的是产出源码而非等价）。
  可作为 Agent 实验的对照条件，以及交付检查中「只发 `.pyc` 不算保护」的说明依据。

---

## 3. 现状审计：路线图提到的能力

| 能力 | 状态 | 证据 |
|---|---|---|
| runtime 独立分发（Y-1） | 0.1.0 已发布；**Y-2／Y-3 接口已实现未发布**（B1） | PyPI；`binding.py:100,119,328` |
| app key provider `--bind-key-env`（Y-3） | builder 0.5.30 已发布；runtime 未发布；只覆盖 L3；CLI 拒绝与 vault／bind-device 组合，YAML 路径疑漏（I6） | `cli.py:592-616`；`build_fusion.py:163-197` |
| 到期告警 `--expire-warn-days`（Y-2） | 同上，runtime 未发布 | `build_fusion.py:645` |
| opacity CLI | `--selective-opacity` 0.5.1、`--opacity-config` 0.5.3 已发布；**只有 L3**、只限顶层函数、无报告 | I2 |
| opacity 四层 API | **纯候选**（文档夸大） | `OPACITY_CONFIG.md:50` |
| Vault | 0.5.1 发布，0.5.4 支持设备绑定；只支持顶层字符串字面量字典；无设备绑定时 key 随包 | `transformers/vault.py:1-56` |
| embed-data | 0.5.10 已发布；单文件；key 随包 | I8 |
| 水印／归因 | 0.5.1 发布原语；恢复只靠明文 key 字面量；无 CLI 恢复；与外部 key 静默互斥 | I3 |
| fusion × 目录构建 | **不支持**（B2） | `cli.py:1056-1067` |
| `--check` | 源码预检，不看交付物 | `core/preflight.py:70-83` |
| build report | 输出 `.py` 哈希、选择原因、聚合计数；无逐符号、无 fusion 计数 | `core/build_report.py:89-110` |
| 交付物泄漏检查、逐函数覆盖 | **不存在** | I1 |
| 打包 lane | Linux CPython 3.12 + Cython／Nuitka／PyInstaller，只测 Community 混淆；无 Pro／runtime；无 Windows | `integration_tests/test_packaging.py` |
| 离线安装证据 | **不存在**（无 `--no-index`、无嵌入式 Python 测试） | `scripts/dogfood/run.py:301-311` |
| LLM 抗性 harness | 隐藏测试、断网 Docker、固定模型标识已具备；零工具、单次 | I4 |

---

## 4. 外部调研要点（检索日 2026-10-12）

只列影响判断的结论，来源见 §11。

- **普通变换对 Agent 是否无效**：不是完全无效，但效果集中在「意图／摘要」，对「行为理解／功能重建」作用小
  （2510.03178，Python）。非 Python 语言上，强模型直接处理混淆代码几乎不受影响（2609.04220）。
  路线图 S5 的引用方式是对的，但还缺 Python 改名这条同语言证据。
- **同类产品的架构选择**：
  - PyArmor 9.2.x：RFT 改名 + BCC 把函数转成 C，模块级代码不转，外置运行时 key 支持期限／设备绑定。
    它 ≤ v7 有公开的运行时 dump 工具，8–9.2 有声称可用的静态解密工具（测试有限），但 BCC 的原生部分没有公开的一键工具。
  - Nuitka Commercial：编译掉字节码，常量白盒加密、数据文件嵌入、traceback 加密；`--report` 只是打包清单，不报告保护覆盖。
  - 两者都走「编译到原生」路线，原因是没有字节码可供反编译。pyobfus 的 AST 路线放弃了这一点。
    所以路线图「高价值函数交给编译层组合」的定位是对的，应在交付文档中写成推荐组合，不自建编译器。
- **覆盖报告是否已有**：没有产品在交付时给出「受保护／未受保护」报告；最接近的是 PyArmor 的 trace 日志（调试用途）。
  候选 A 的覆盖部分确属空白，但市场上没有人为此付费的证据。
- **外部密钥能防谁**：只防拿到包、拿不到 key 的人。合法运行者能取得运行时明文
  （通用混淆不可能性 Barak et al. 2001；OWASP MASWE「不要在包内硬编码密钥」；PyArmor 自述前提）。
  离线撤销：Cryptlex 官方无撤销离线激活的手段，Keygen 建议用离线时长上限和宽限期。
- **黑盒重实现**：2026 年有多起 Agent「净室重写」争议（chardet 重写后改许可等），没有同行评审研究，法律未定。
  这条路线完全绕过代码保护，路线图对此的定位正确。
- **open-core 分层**：GitLab 按买家分层（个人／经理／高管）。我们的政策与之一致：交付检查属个人开发者正确性层，key 交付与归因属组织买家层。

---

## 5. 候选逐项评审

| 候选 | 用户／触发 | 与现有的增量 | 能否用文档／外部工具解决 | 边界 | 判断 |
|---|---|---|---|---|---|
| A 交付检查 | 打包后交付前的个人／小团队 | mapping／原文混入检测、哈希对应、回读 Pro 事实 | 凭据、`.pyc`、多余目录可交外部工具 | Community | **收窄后先实验**（I1） |
| A' 覆盖报告 | 需确认保护真的生效的 Pro 用户 | build report 加 fusion／opacity 匹配跳过 | 不能 | 数据由 Pro 写出，Core 免费读取 | **立即设计**，与 B2 同做 |
| B Agent 实验 | 维护者选技术路线 | 加工具条件、密钥位置、重复次数 | 先写协议，确定性部分不需模型 | 方法公开免费 | **先做协议，延后付费运行**（§6） |
| opacity 范围 | 有专有算法写在方法里的用户 | L3 覆盖方法 | 否 | Pro | **等待需求**；删除「四层」 |
| Vault／embed-data 接 key provider | 离线交付含配置／模型密钥的用户 | 统一 key 来源 | 否 | Pro | **等 B1 修好 + 一个需求信号** |
| 资源保护（更多格式） | 模型／数据文件交付 | 超出 embed-data 单文件 | 部分交给 Nuitka 数据文件保护等编译层 | Pro | **推迟** |
| 买家归因 | 担心原样再分发的卖家 | 如实声明 + 拒绝互斥组合 | 文档为主 | Pro | **收窄**（I3） |

离线方面需要写清的四件事（不在 pyobfus 内实现授权服务器）：

- **安装**：runtime wheel 随交付物附带，用 `pip install --no-index` 安装，或 vendored 进嵌入式 Python。
- **授权**：provider 回调或环境变量。
- **续期**：重新构建或下发新 key；期限写在构建里时只能重建。
- **错误诊断**：已有 `LicenseBindingError`／`OpacityRuntimeError`，可在开发者私有 mapping 下 `--unmap`。

---

## 6. Agent 实验协议（只设计，本轮不运行）

**攻击权限分三类，分别报告，不合成单一恢复率**：

1. 静态：只读产物，无执行。
2. 可运行：带 Python、反编译器（pycdc／PyLingual 本地版）的断网容器。
   - 2a 未授权：无外部 key；
   - 2b 已授权：攻击者就是合法运行者，有 key。
3. 黑盒：只有入口签名和受限次数的输入输出查询，没有产物。

**条件**：

- C0 原文
- C-pyc 只发 `.pyc`（负基线）
- C1 Community 默认
- C4a L3，key 在包内
- C4b L3 + `--bind-key-env`，无 key
- C4c 同上但已授权
- 可选：PyArmor RFT／BCC 作为注明日期的竞品对照（需维护者决定是否购买或使用试用版）

**样例**：6 个新写的私有合成样例，至少 1 个多模块；另加 2 个公开算法，只用来测模型的「记忆」。
每个样例 ≥ 15 条隐藏向量，隐藏向量不进入工作区、上下文或工具输出。

**有效性控制**：

- C0 必须 100% 可恢复，否则说明任务或评分有问题；
- 加一个平凡 Agent 基线（如只返回常量）；
- 记录每个条件实际生效的保护（防止 no-op）；
- 固定模型标识、日期、提示、工具和产物哈希。

**度量**：隐藏测试通过率、密钥／常量提取成败、成功所需 token／时间／费用；
防御侧记录启动／运行开销、体积，以及 `--unmap` 是否仍可用。

**首轮预算（建议）**：2 个模型家族 × 6 样例 × 3 权限档中最有信息量的 4 个条件 × 3 次重复 ≈ 144 次运行。
单次设 token 和时间上限，总额由维护者定。只有静态档可以先跑 1 次 × 2 模型作探针。

**零成本先行**：C4a 在可运行档下的结论可以用一段确定性脚本得到（读字面量 → 调 runtime 解密），不需要模型。
建议先写这个脚本，它本身就说明了「key 在包内」的保护上限。

**停止规则**：

- 某变换在可运行档下对 2 个模型、各 3 次重复都无可测增益（通过率差 < 1 个样例），且有可测运行开销 → 停止扩展该变换；
- C0 不能 100% 通过 → 停下修 harness；
- 预算用尽 → 只报告「该预算内未成功」。

**研发证据与营销表述分开**：对外只能说「在 X 权限、Y 预算、Z 模型下的结果」，不使用「抗 AI」类字样。

---

## 7. 保留／收窄／推迟／替换／删除

| 路线图条目 | 处理 | 理由 |
|---|---|---|
| 离线应用优先 | **保留**，补「离线」三档定义 | I7 |
| R1 现有质量主线 | **保留并前置**，纳入 B1、B2「如实」部分、I6 | 阻断项 |
| 候选 A 交付检查 | **收窄**到三项，外部工具做组合文档 | I1 |
| 覆盖报告 | **保留**，改为 build report 回读 Pro 写出的处理事实 | I2，源码分离 |
| 候选 B Agent 实验 | **收窄**：先协议 + 确定性脚本，付费运行推迟 | I4、§6 |
| 候选 C1 opacity 四层／范围 | **删除「四层」**；方法级 L3 推迟待需求 | I2 |
| 候选 C2 Vault key provider | **推迟**到 B1 修复后，并与 embed-data 一起 | I8 |
| 候选 C3 资源保护 | **替换**为「embed-data 接入 key provider」 | I8 |
| 候选 C4 离线目标可安装可运行 | **前置为首个实践** | B1 |
| 候选 D 归因 | **收窄**为声明 + 拒绝互斥组合，扩展推迟 | I3 |
| REA 等第三方 Agent 工具 | **推迟**，不作依赖 | 热度不是证据 |
| 继续延后清单（VM、反沙箱等） | **保留** | 与外部证据一致 |

---

## 8. Community／Pro 分层（修订）

| 能力 | Community | Pro |
|---|---|---|
| 修 B1／B2、I6 等正确性缺陷，fusion 未生效的如实提示 | 是（含对 Pro 产物的诚实报告） | — |
| 交付检查三项、外部工具组合文档 | 完整 | 同一功能，可读 Pro 写出的事实 |
| 覆盖报告 | 读取与展示 | 写出 fusion／opacity 处理事实（代码留在 Pro） |
| 离线安装指南（runtime wheel、`--no-index`） | 公开文档 | — |
| Agent 实验方法、确定性脚本 | 公开 | 托管评估：无计划 |
| L3、Vault、embed-data 接 key provider、fusion × 目录构建 | — | 是 |
| 买家匹配（原样再分发） | — | 是，附局限声明 |

符合政策 Q1–Q4。Q5 对新增 Pro 能力仍需外部需求信号（I5）。
发现明文资源时的提示须列出「移到服务端／改架构／编译层／Pro」等多个选项，不能只给升级提示。

---

## 9. 近期优先事项（最多三项）与首个可验收实践

1. **P1 离线目标可运行（修 B1）**：发布带 Y-2／Y-3 接口的 runtime，builder 声明最低版本，并加目标环境测试。
2. **P2 如实报告 fusion 生效范围（B2 + I2 + I3 + I6）**：
   - Note 与 `disabled_transforms` 覆盖全部 fusion 选项；
   - Pro 把 opacity 匹配／注入／跳过写进 build report；
   - CLI 对 fingerprint + bind-* 组合给出拒绝或警告；
   - 互斥校验移到合并后的配置上。
   做完再决定是否设计「fusion × 目录构建」。
3. **P3 收窄版交付检查原型 + Agent 实验协议文档**：交付检查只做 I1 三项，用合成 fixture 验证；
   实验先写协议并完成零成本确定性脚本。

**首个可验收实践：离线目标冒烟 lane**

- 合成 fixture（多文件或单文件 + `--no-cross-file`），用 Pro 选项 L3 + `--bind-key-env` + `--expire-warn-days` + vault（绑定设备）构建；
- 把**已发布或候选 runtime wheel** 放进本地 wheelhouse，新建 venv，`pip install --no-index --find-links wheelhouse`，
  测试进程禁止网络、不挂仓库源码路径，`HOME` 指向临时目录；
- 运行产物，断言：(a) 有正确 key 时行为与原文一致；(b) 无 key／错 key 时报文档所述的错误类型；
  (c) 到期告警出现；(d) 交付目录里没有 mapping 和原文。
- **验收标准**：对 PyPI runtime 0.1.0 先红（复现 B1），对新 runtime 转绿；进入 CI（可先作为非阻断 lane）；
  Windows 与嵌入式 Python 作为第二步。

这项实践既修复真实缺陷，又是「离线应用优先」的第一份证据，也为候选 A 的 (d) 项提供 fixture。
它不涉及新付费功能，不需要模型调用。

---

## 10. 解冻／停止条件与待维护者决定

**解冻**

- 候选 C 任一项：P1 完成，且有一个外部需求信号（现有客户回复或 issue）。自有下游可以支持修复和验证，不单独支持新能力。
- fusion × 目录构建设计：P2 完成后，自有下游或任一客户确认需要多模块 Pro 保护。
- 付费 Agent 运行：协议已审，确定性脚本完成，预算已批，C0／平凡基线已在本地验证。
- 交付检查进入发布：合成 fixture 上已知遗漏全部检出、正常交付零误报，并在一个真实离线应用上试过。

**停止**

- 交付检查的误报解释不清，或主要发现都已被外部工具覆盖 → 退回为文档。
- Agent 实验停止规则见 §6。
- 两个月内现有客户中无人确认离线交付场景 → 离线方向仍保留，但只做正确性和文档，不加新的 Pro 能力。

**需要维护者决定**

1. runtime 修复版是否作为 bug 例外立即发布，以及是否与 0.7.0 同批；是否需要通知已使用 `--bind-key-env` 的用户（含自有下游）。
2. 是否给现有付费客户发一封简短的场景调研邮件（零成本补 Q5 证据）。
3. Agent 实验首轮总预算上限，以及是否允许把合成样例交给模型供应商（合成样例不含私有代码）。
4. 是否用 PyArmor 试用版或付费版作为竞品对照条件。

---

## 11. 来源、覆盖范围与未验证假设

**仓库**：文中路径与行号均基于 `2bb2cd3` 工作区。实测仅限：PyPI runtime 0.1.0 干净 venv 运行 Y-2／Y-3 产物；
mapping 写进输出目录；对含明文的输出目录跑 `--check`；fingerprint 与 bind_key_env 组合的恢复。
其余为读码。

**外部（检索日 2026-10-12；类型：研究／厂商／标准／社区／二手）**

- arXiv 2609.04220 Robustness and Trade-offs for Code LLMs on Protected Code（研究；C++／Go／Java／JS；页面标注 ISSRE 2026；编号与提交日期不一致，未解决）
- arXiv 2605.10597 CrackMeBench（研究；原生二进制）
- arXiv 2510.03178 When Names Disappear（研究；Python）
- arXiv 2507.17691 CASCADE（研究／工业；JS）；arXiv 2506.20170 JsDeObsBench（研究；JS，仅摘要）
- arXiv 2608.12853 Beyond Source（研究；PyPI `.pyc` 反编译）；PyLingual（IEEE S&P 2025）
- https://github.com/Svenskithesource/PyArmor-Unpacker （社区；≤ v7）；https://github.com/Lil-House/Pyarmor-Static-Unpack-1shot （社区；声称 8.0–9.2.x，测试有限，未独立复核）
- https://pyarmor.readthedocs.io/en/stable/how-to/protection.html 、topic/bccmode.html、topic/rftmode.html、licenses.html（厂商；9.2.x；最新版本号 9.2.6 来自 piwheels，部分页面 429）
- https://nuitka.net/doc/commercial.html 及其保护子页（厂商；价格页显示 €250／400／1000 每年，未逐项复核）
- https://github.com/jwodder/check-wheel-contents 、https://github.com/gitleaks/gitleaks 、https://github.com/trufflesecurity/trufflehog （社区）
- https://keygen.sh/docs/choosing-a-licensing-model/offline-licenses/ 、https://docs.cryptlex.com/node-locked-licenses/offline-activations （厂商）
- https://eprint.iacr.org/2001/069 （研究）；https://mas.owasp.org/MASVS/11-MASVS-RESILIENCE/ （标准，只取得部分原文）
- arXiv 2507.05512 Disappearing Ink（研究；对象是 LLM 生成代码的水印）
- arXiv 2507.02825 Agentic Benchmark Checklist；arXiv 2506.12286 SWE-Bench Illusion（研究）
- https://handbook.gitlab.com/handbook/product/tiering-guidance-for-features/ （厂商）
- https://peps.python.org/pep-0740/ （标准）

**无法访问或未验证**：

- PyArmor 部分页面（429）与 9.x 官方价格；
- PyInstaller 移除 `--key` 的官方原因；
- pyconcrete GitHub（404）；
- NIST SP 800-57、pass@k 估计器定义（来自记忆，未引用）；
- Cython 编译产物中字符串是否可读（未找到来源）；
- 未找到针对 PyArmor／pyobfus 类 Python 保护工具的 LLM Agent 同行评审研究。

**未验证假设**：

- I6 的 YAML 绕过未实测；
- 自有下游是否受 B1 影响取决于其安装方式，未核实；
- 「离线应用多为多模块」是推断，没有用户数据。

**未做的工作**：未运行任何模型评测，未运行攻击代码，未对竞品做同配置实测，未调查用户付费意愿。
本报告中的有限实测不构成普遍保证。

---

## 12. 后续处置（同日第二轮）

维护者确认按复核执行、修复随 0.7.0 同批发布，§10 的四项决定交由最佳实践处理，结果记在路线图 §13.4。

- B1：PR #94 发布 runtime 0.1.1，builder 下限改为 `>=0.1.1`。新增 `scripts/check_runtime_version.py`，在旧代码上实测能报出本问题。
  新增 `integration_tests/test_offline_target.py`，即 §9 的首个实践：对 PyPI 0.1.0 实测红，Y-2／Y-3 两项失败；对 0.1.1 绿。
- B2、I3、I6、I8 中的提示部分，以及 S1 文档漂移：均在 PR #94 中处理。fusion 与目录构建的组合支持仍待设计。
- 本轮新发现：
  - `--scrub-traceback` 把 RSA 私钥写在输出文件旁边，即交付目录里。已加警告，未改位置。
  - Dependabot 自动合并把 `click>=8.5.0`、`jsonschema>=4.26.0` 带进 main。两者都只支持 Python ≥3.10。
    原因：3.9 测试不是必需检查，bot 合并也不触发 main CI。PR #93 已修复并合并，规则集已补上 3.9／3.14。
