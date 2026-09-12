# 功能扩展与国际最佳实践调研（2026-09-12）

Status: 调研完成；**本文件不授权任何实现或发布**。实现与发版仍各自需要用户
明确批准，沿用既有 gate。

触发点：`Core 0.5.24`（unified verifiable build report）发布当日，用户要求
规划「设计文档里应当优先实现哪一项」并复核国际最佳实践与对标现状。

本轮与 [`FEATURE_EXPANSION_RESEARCH_2026-09-02.md`](FEATURE_EXPANSION_RESEARCH_2026-09-02.md)
的关系：那一轮的三项 P1 已全部发布（SARIF → 0.5.21、PEP 768 advisory →
0.5.22、build report → 0.5.24），其 P2/hold 清单继续有效；本轮在此之上补充
**实测证据**与 2026-09 的外部事实复核，并给出新的优先级。

---

## 1. 建议顺序（结论先行）

| # | 候选 | 包 | 依据强度 | 类型 |
|---|---|---|---|---|
| 1 | 跨文件模式输出可复现（确定性命名顺序） | Core | **本轮实测** | ✅ 已随 0.5.25 发布 |
| 2 | `mcp` SDK 2.x 迁移 spike + 真实 2.x CI | MCP | **本轮实测** | 生态时限 |
| 3 | CycloneDX 版本声明对齐（1.6 → 1.7 或如实降级说明） | Core | 外部标准复核 | 小修 |
| 4 | 兼容性/验证矩阵（supported / tested / advisory-only） | 文档 | 存量 P2 | 零运行时风险 |
| 5 | 稳定 reason code（excluded / preserved / disabled） | Core | 存量 P2 | schema 变更 |
| 6 | 只读 review Skill + `.github/skills/` 落位 | 分发 | 存量 P1 + 外部复核 | 生态入口 |
| 7 | OSPS Baseline 自评 | 工程基线 | 外部新标准 | 可验证credential |
| 8 | 文档诚实性更新（LLM 论文、在线混淆站类别、PyArmor 版本纠正） | 文档 | 本轮复核 | 随手可做 |

**第 1 项是唯一「补完刚发布功能」的候选**：0.5.24 刚把输出 SHA-256 作为交付
证据写进报告，但当时跨文件模式重跑同一输入会得到不同哈希，第三方拿到报告无法
自行重建复核。

**✅ 第 1 项已于 2026-09-12 同日实现并随 `0.5.25` 发布**（用户批复「继续」后
实现、批「发版」后发布）：export 登记与文件发现改为排序迭代，6 个新回归测试用两个不同
`PYTHONHASHSEED` 子进程比对每一个生成字节、mapping 内容与报告里的摘要；四个
测试根全绿（core 1301 / MCP 97 / integration 7），black/ruff/mypy 干净。
**未改版本号、未 tag、未发布**——发版仍需用户单独批准。实测细节见 §3.1。

---

## 2. 存量盘点：设计文档里已设计、尚未实现的项

| 项 | 来源文档 | 现状 |
|---|---|---|
| 只读 preflight review Skill / template | `FEATURE_EXPANSION_RESEARCH_2026-09-02.md` P1 #2 | 未实现 |
| MCP 官方 conformance evidence | 同上 P2 #4 | 未实现（本轮有新证据，见 §3.2） |
| 持续验证矩阵 supported/tested/advisory-only | 同上 §Nuitka 借鉴 #2 | 未实现 |
| 稳定 reason code + 可审查框架 profile + fixture | 同上 §Nuitka 借鉴 #3 | 未实现 |
| self-dogfooding 四条 lane 的落地 | `SELF_DOGFOODING_BEST_PRACTICES.md` | 研究完成，未执行 |
| MCP Resources / Prompts 原语拆分 | `MCP_PRIMITIVES_DESIGN.md` | research only，gate 在真实 MCP 用户反馈 |
| `--output-pyc` 可行性 spike | `CURRENT_PLAN_ZH.md` P3-1 | 未启动（仅 spike，不承诺产品化） |
| hosted / remote MCP endpoint | 同上 P3-2 | 明确等外部分发稳定后再议 |
| 分发队列（awesome-python 等 5 项） | `DISTRIBUTION_EXPANSION_RESEARCH_2026-09-07.md` | 非功能项，队列推进到第 3 项 |

已发布、不再是待办：配置感知 `--check`(0.5.18)、dry-run plan 与
`--verify-syntax`(0.5.19)、SARIF(0.5.21)、remote-debug advisory(0.5.22)、
build marker(0.5.23)、build report(0.5.24)、GitHub Action(独立仓库 v1.0.1)。

---

## 3. 本轮实测证据（不是推断）

### 3.1 跨文件模式输出不可复现

同一份输入、同一份配置、同一台机器，连跑三次目录模式：

```
默认（哈希随机化开启）：
  run1 app=4d83569230d54ae4   util=68180722746f6123
  run2 app=4d83569230d54ae4   util=68180722746f6123
  run3 app=7cd173fce12b0882   util=68180722746f6123
PYTHONHASHSEED=0：
  run1 app=7cd173fce12b0882   util=68180722746f6123
  run2 app=7cd173fce12b0882   util=68180722746f6123
  run3 app=7cd173fce12b0882   util=68180722746f6123
```

对照结论：**单文件模式三次运行稳定**；目录/跨文件模式随进程哈希种子变化。
`ObfuscatorAnalyzer.obfuscatable_names` 是 `Set[str]`
（`pyobfus/core/analyzer.py`），分配混淆名时按集合迭代顺序取用，顺序随
`PYTHONHASHSEED` 变化 → 同一符号在不同进程拿到不同的新名字。

不是加密随机性问题：`secrets` 仅用于 `transformers/numeric_obfuscator.py`
（`--numeric-obfuscation`，默认关闭），本次对照未启用。

影响面：
- **0.5.24 build report 的 `outputs[].sha256` 第三方无法复核**——重建必然不同；
- provenance manifest 的输入/输出哈希同理；
- 缓存与增量构建的命中判断被削弱（同配置重建产出不同字节）。

**实际修法（已落地，held 在 `[Unreleased]`）**：根因比 §3.1 最初写的更靠上游
一层——真正决定顺序的是 `core/orchestrator.py` phase1 里
`for export_name in exports:`（`exports` 是 `ExportDetector.get_exports()`
返回的集合），以及 `utils.filter_python_files` 直接返回 `rglob` 顺序（随文件
系统与机器变化）。两处都改为排序后迭代；**没有引入 `--seed`、没有动加密材料**。诚实边界要写清楚：可复现的是
**命名与结构选择**；`--numeric-obfuscation` 与 AES 字符串加密（每次新 nonce/
IV）**按设计不可复现，也不应该可复现**——这一点必须在文档和报告里明说，不能
宣传成「整包可复现」。

国际对照：`SOURCE_DATE_EPOCH` 与可复现构建在 2026 已是常规实践，但 PyPI 上
12,180 个流行发行版的实测逐字节一致率仍然很低——**所以「我们可复现」是一个
有区分度但必须限定范围的主张**，不能笼统宣称。

### 3.2 `mcp` SDK 2.x 下服务器无法启动

全新 venv 装 PyPI 上的 `pyobfus-mcp==0.3.12`，解析到 `mcp 1.30.0`；强制装
`mcp==2.2.0` 后构建服务器：

```
No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was
renamed to MCPServer (from mcp.server.mcpserver import MCPServer) ...
```

协议版本对照（同一台机器实测）：

| SDK | `LATEST_PROTOCOL_VERSION` | 构建 `_build_server()` |
|---|---|---|
| `mcp 1.30.0` | `2025-11-25` | OK |
| `mcp 2.2.0` | `2026-07-28` | 失败（FastMCP → MCPServer） |

当前 `pyobfus_mcp/pyproject.toml` 的 `mcp>=1.27.0,<2.0.0` 上限**正在生效并
保护用户**（今天装到的是 1.30.0，一切正常）。但两点值得注意：

1. CI 的 `mcp-sdk-latest` job 装的是 `'mcp>=1.20'`，会被本包的 `<2.0.0` 上限
   拉回 1.x——**它今天并没有在测 2.x**，名字容易让人误以为在测。
2. MCP 规范 `2026-07-28` 已 GA（stateless core、extensions framework、
   MCP Apps、授权收紧、DCR 弃用），Tier 1 SDK 已跟进。我们停在 1.x 线意味着
   最高只能协商到 `2025-11-25`。

建议不是「立刻迁移」，而是**先做 spike 拿事实**：在分支上把
`FastMCP` → `MCPServer`、`@app.tool(meta=...)` 等 API 逐个对齐，确认 8 个工具
的稳定响应契约（`status` / `ai_hint` / `next_tool`）能否原样保住；同时新增一个
**真的**装 2.x 的 CI job（允许先标记为 informational）。这项 spike 同时就是
存量 P2「MCP conformance evidence」的实际内容，一石二鸟。

### 3.3 provenance 声明的 CycloneDX 版本

`pyobfus/core/provenance.py` 写死 `"specVersion": "1.6"`。CycloneDX 1.7 已于
2025-10 发布并在同年 12 月成为 ECMA-424 第 2 版。1.7 里与本项目直接相关的
三处新增：**verifiable provenance 的 citations**、**专利/专利族元数据**、
**以 TLP 标记表达的分发约束**——最后一项与「把受保护构建交付给特定客户」的
场景天然契合。

处置有两种，都诚实，二选一即可：升到 1.7 并只填真实字段；或保持 1.6 但在
文档里写明「对齐的是 1.6，未使用 1.7 新增字段」。**不可接受的是继续默认
读者以为我们跟着最新版。**

### 3.3b ✅ 实现候选 1 时发现的既有缺陷：包 re-export 三方不一致（已修）

**不是可复现性改动引入的**（在未改动的树上复现过）。发现当日记录、用户拍板
「先修这个」后**已修复并 held 在 `[Unreleased]`**，与可复现性改动是各自独立的
commit。修法与验收见本节末尾。

最小复现（两个文件）：

```python
# lib/__init__.py
from lib.math_utils import add
__all__ = ["add"]

# lib/math_utils.py
def add(a, b):
    return a + b
```

`pyobfus src -o out` 之后：

```python
# out/lib/__init__.py
from lib.math_utils import I1
__all__ = ['I0']          # I0 不存在
# out/lib/math_utils.py
def I1(a, b): ...
```

`import lib` 后 `lib.__all__` 里的名字一个都不存在 → `from lib import *`
失败，任何依赖 `__all__` 的消费方也失败。更大的 fixture 上还观察到第三种
不一致：调用方 `main.py` 的 `from pkg import run_pipeline` **导入语句没有被
改写**，而同一文件里的调用点被改写成了 `I0`，于是同一个符号在三处拿到三个
不同身份（调用方视角 `I0`、定义处 `I6`、`__all__` 里 `I2`）。

根因方向（未深查）：模块 `pkg` 把从 `pkg.core` 导入的名字也登记成了自己的
export 并分配了**新**的混淆名，而 import 改写走的是 `pkg.core` 的映射，
`__all__` 更新走的是 `pkg` 自己的映射，两套名字对不上。

影响面不小：`__init__.py` 做 re-export 是最常见的包结构之一。
`--cross-file`、`--no-cross-file`、`--preset safe` 三种组合都复现。

**✅ 已随 `0.5.25` 发布（2026-09-12）**。三个症状同一个根因，实际改了三处
（外加同族的「`import json` 模块绑定被改名」，见本节末）：

1. `ExportDetector` 新增 `imported_from`，记下每个名字是不是 import 来的、
   来自哪个模块（含相对层级与 `as` 之前的原名）。
2. `orchestrator.phase1_scan` 改为**两趟**：第一趟只给**本模块定义的**导出取新
   名；第二趟把 re-export 解析到定义处的名字，并**循环到不再有新解析**，从而支持
   链式（`pkg` → `pkg.api` → `pkg.core`）。**源在项目之外的（如
   `from json import dumps`）刻意不登记**——那属于我们不改写的第三方包，改名只会
   把它来的那条 import 弄坏。
3. `GlobalSymbolTable` 新增 `register_reexport`（**不**在 reverse mapping 里
   占用该混淆名，定义方保持所有权，因此复用不是 `register_export` 会拒绝的冲突）
   与 `register_module_alias`（让 `pkg` 解析到 `pkg.__init__` 的导出表，消费方
   那一侧的症状由此消失）。

验收：9 个新回归测试 `tests/test_reexport_consistency.py`，覆盖绝对/相对/链式/
第三方 re-export + 消费方端到端 + 符号表三条单测；**它们在未修复的树上 9 个全
失败**，修复后全过。四个测试根：core 1310 / MCP 97 / integration 7。多包样例
混淆后实跑结果与混淆前逐字相同（`18.0`）。

### 3.4 竞品版本事实纠正（我们自己的记载错了）

PyPI 的 upload_time 是不可变事实：

| 版本 | 上传时间 |
|---|---|
| PyArmor 9.2.5 | 2026-06-01 |
| PyArmor 9.2.6 | **2026-07-27** |
| PyArmor 9.2.7 | **2026-08-29** |

因此 2026-08-31 那轮扫描写「PyArmor 9.2.7」是**对的**；2026-09-02 在
`CURRENT_PLAN_ZH.md` 和 `FEATURE_EXPANSION_RESEARCH_2026-09-02.md` 里
「更正」为「仍是 9.2.6（2026-07-23）」**才是错的**，且日期也不对。这正是本
项目自己那条教训的又一个实例：**更正别人（包括更正自己）之前先取证**。

---

## 4. 国际最佳实践与对标现状（2026-09-12 复核）

### 4.1 供应链证据链

- **SLSA v1.2**（2025-11 通过）：Build track L0–L3 之外新增 Source track；
  provenance 以 in-toto attestation + DSSE 封装，记录 builder 身份、构建指令、
  参数、环境与依赖摘要。GitHub Artifact Attestations 与 npm trusted publishing
  已默认发这类证据。我们已有 PEP 740 attestations（发布物层面），
  但 `--provenance-manifest` / `--build-report` 是**本地自述事实**，不是
  attestation。**继续按现在这样诚实区分**，不要把两者混称。
- **SBOM 格式**：CycloneDX 1.7（ECMA-424 2nd ed）与 SPDX 3.0.1 是当前参考集，
  工具侧普遍期待机器可读 JSON、签名制品与 VEX。见 §3.3。
- **可复现构建**：`SOURCE_DATE_EPOCH` 已是常规做法，但 Python wheel 生态的
  逐字节一致率仍低。见 §3.1。

### 4.2 AI / agent 生态

- **MCP 规范 `2026-07-28` GA**：stateless 核心、多轮请求、header 路由、可缓存
  list 结果、扩展框架（reverse-DNS ID）、MCP Apps（沙箱 iframe UI）、授权
  收紧（CIMD 取代 DCR）。见 §3.2。
- **Agent Skills 已跨厂商收敛**：`SKILL.md` 遵循 agentskills.io 规范，
  GitHub Copilot 于 2026-04 在 agent mode 支持，仓库级技能放 `.github/skills/`，
  并有 `gh skill`（2026-04-16 公测）做 search/install/pin/publish。
  我们现有的 `skills/pyobfus-protect/SKILL.md` 已是同一格式，但**没有放在
  `.github/skills/`**，Copilot/Cursor/Codex 在本仓库内不会自动拾取。
  存量 P1「只读 review skill」正好可以顺着这个约定一起落位：一个 mutating
  skill（现有）+ 一个只读 review skill（新，只跑 `--check` 与读 dry-run plan）。

### 4.3 混淆与 LLM 的关系（影响我们的措辞，不影响功能）

2026 年的研究结论对「混淆能挡住 AI」这类说法不利，也正好支持我们一贯的
克制表述：

- *Robustness and Trade-offs for Code LLMs on Protected Code*（arXiv 2609.04220）：
  七个 code LLM、四种语言、五种混淆手法；**直接在混淆代码上推理往往等于甚至
  优于先还原再推理**，GPT-4.1 与 Qwen3-Coder-30B 在混淆翻译任务上仍保持约
  90% Pass@1；模型能力是主因，混淆手法是次因。
- *Acoda: Adversarial Code Obfuscation for Defending against LLM-based Analysis*
  （arXiv 2606.11755）与 Recon 2026 的 agentic 逆向议题，说明「对抗 LLM 分析」
  正在成为独立研究方向。

对我们的意义：`LLM_RESISTANCE_BENCHMARK.md` 的定位应当从「能不能挡住」改写为
「**在什么任务上、挡住多少、代价是什么**」，并引用上述工作；`COMPARISON.md`
不得出现「AI 读不懂」这类表述。这是文档工作，不是功能工作。

### 4.4 对标产品现状

| 产品 | 最新版 | 本轮观察 |
|---|---|---|
| PyArmor | **9.2.7**（2026-08-29） | 新增 `ProcessPoolExecutor` 生成支持、**只读混淆模块**（明文脚本可读可调用、不可写改）；修 `--enable-rft` 在 Win/Py3.13 的崩溃 |
| Nuitka | **4.2.1**（2026-09-05；4.2 为 2026-08） | 主线仍是 C 编译规模化与 3.14 正式支持、VS2026 支持；仍不改我们「不追 compiler/installer」的判断 |
| SOURCEdefender | 16.0.66（2026-08-18） | 持续维护，加密 `.pye` 路线不变 |
| python-minifier | 3.3.0（2026-09-04） | 不同赛道（压缩非保护），我们的 Skill 已正确把它排除在外 |
| pyobfuscate.com | 在线服务 | **已建立 comparison SEO 矩阵**（PyArmor / Nuitka / Cython / PyInstaller 六组对比页），自我定位「free, web-based, no runtime」；**页面完全没有提到 pyobfus** |

对 pyobfuscate.com 的处置：不投入对抗式 SEO。但 `COMPARISON.md` 目前只比
本地工具，**缺「在线混淆服务」这一类**——而那正是我们有硬差异的地方：源码是否
离开本机。补一段事实性的类别对比即可，不贬低对方。

---

## 5. 前四项的范围、验收与风险

### 候选 1 · 跨文件输出可复现（建议下一个功能版本）

- **范围**：命名分配顺序确定化；`--build-report` / provenance 文档写明可复现
  与不可复现的边界；不新增 flag，不改加密材料。
- **验收**：同输入在**不同 `PYTHONHASHSEED` 下**连续构建，输出逐字节一致
  （回归测试直接跑两个子进程比对，不靠人工观察）；`--numeric-obfuscation`
  与字符串加密**仍**不可复现且有测试说明其为预期；1295 核心测试不回归。
- **风险**：命名顺序变化会改变现有用户重建后的产物字节（但他们本来每次就不
  一样，不构成回归）；mapping 文件格式不变。

### 候选 2 · MCP SDK 2.x spike

- **范围**：分支上完成 API 迁移评估，产出一份「能否在保住 8 工具契约的前提下
  支持 2.x」的结论文档；新增真正安装 2.x 的 CI job；**本轮不改上限、不发版**。
- **验收**：2.x 下 `_build_server()` 成功、8 工具 `ListTools` 一致、
  `status`/`ai_hint`/`next_tool` 契约逐字段不变；若做不到，写明卡点后维持 1.x。
- **风险**：SDK 2.x 是 stateless 重构，`meta=` 等我们依赖的 API 可能语义变化；
  贸然放开上限会伤到现有用户——**上限必须等 spike 结论出来再动**。

### 候选 3 · CycloneDX 声明对齐

- **范围**：二选一（升 1.7 只填真实字段 / 保持 1.6 并注明）；顺带评估 TLP
  分发约束是否对「交付给客户的受保护构建」有真实价值。
- **验收**：`--verify-provenance-manifest` 对新旧 manifest 均通过；不为了字段
  好看而填写无法证实的内容。

### 候选 4 · 兼容性/验证矩阵

- **范围**：一张表把 Python 版本 × 框架 preset × 操作系统 × 交付组合
  （PyInstaller/Nuitka/Cython/import-hook/模型服务）标注为
  supported / tested / advisory-only，并指明每格的证据来源（CI job、cookbook、
  用户报告、未验证）。
- **验收**：每个 "tested" 都能点到具体 CI job 或测试；不能点到的一律降级为
  advisory-only。零运行时改动，可随任意版本发布。

---

## 6. 继续不做 / 继续 hold

沿用 `CURRENT_PLAN_ZH.md` §明确不做，本轮无变化：不做 BCC/JIT/VMC 字节码虚拟机
路线、不把 manifest/attestation 宣传成「代码可信证明」、不为当前 stdio server
做 HTTP OAuth / hosted connector、不做 anti-VM / 沙箱规避、不做云端混淆服务、
不做复杂企业 license server、不追 PyLocket 式逐函数字节码加密 + 设备绑定架构。

继续 hold（等真实失败案例或重复用户需求）：import/runtime verifier 扩展、
delivery bundle、mapping 内建加密、新 transform、MCP Resources/Prompts 拆分、
`--output-pyc`、hosted MCP。

**MCP Apps（2026-07-28 规范新增的沙箱 iframe UI）明确不追**：我们的价值在本地、
可验证、不上传源码；给混淆器加一个宿主内的 UI 面板不解决任何已知用户问题。

---

## 参考来源（2026-09-12 复核）

- PyArmor 9.2.7 变更：<https://pyarmor.readthedocs.io/> ·
  <https://github.com/dashingsoft/pyarmor/releases>
- Nuitka 4.2：<https://nuitka.net/posts/nuitka-release-42.html> ·
  <https://nuitka.net/changelog/>
- SLSA v1.2 规范：<https://slsa.dev/spec/v1.2/> ·
  分发 provenance：<https://slsa.dev/spec/v1.0/distributing-provenance>
- CycloneDX 1.7 新特性：<https://fossa.com/blog/whats-new-cyclone-dx-1-7/> ·
  <https://safeguard.sh/resources/blog/cyclonedx-1-7-new-features-review>
- 可复现构建 / `SOURCE_DATE_EPOCH`：<https://reproducible-builds.org/specs/source-date-epoch/> ·
  <https://reproducible-builds.org/reports/2026-07/>
- MCP `2026-07-28` 规范：<https://modelcontextprotocol.io/specification/2026-07-28> ·
  <https://blog.modelcontextprotocol.io/posts/2026-07-28/>
- OSPS Baseline：<https://baseline.openssf.org/versions/2026-02-19.html>
- Agent Skills 约定：<https://github.com/github/awesome-copilot/blob/main/docs/README.skills.md> ·
  <https://learn.microsoft.com/en-us/visualstudio/ide/copilot-agent-skills?view=visualstudio>
- LLM 与受保护代码：<https://arxiv.org/abs/2609.04220> ·
  <https://arxiv.org/pdf/2606.11755> · <https://cfp.recon.cx/recon-2026/talk/A99GW9/>
- 在线混淆服务对比矩阵：<https://pyobfuscate.com/compare>
