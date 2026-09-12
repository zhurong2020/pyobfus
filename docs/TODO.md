# TODO

排期中的任务清单。**当前计划与状态仍以
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 为准**；本文件只回答「接下来按什么
顺序做」，不记录历史。依据与实测证据见
[`FEATURE_EXPANSION_RESEARCH_2026-09-12.md`](FEATURE_EXPANSION_RESEARCH_2026-09-12.md)。

最后更新：2026-09-12。

## 状态口径

- **实现**与**发布**是两道各自独立的 gate，都需要用户明确批准。
- 任何一项做完后，把它从本文件移除，并在 `CURRENT_PLAN_ZH.md` 记状态；
  不要在这里留「✅ 已完成」的历史层。

## 已完成（本轮，仅作交接，下次冷启动可删）

- ✅ 跨文件输出可复现 → `0.5.25`
- ✅ 包 re-export / `import` 模块绑定两个缺陷 → `0.5.25`
- ✅ mcp SDK 2.x 探路 + 兼容代码 + `mcp-sdk-2x` CI job → 已并入 main，**依赖上限
  未动**（理由见 [`MCP_SDK_2X_SPIKE.md`](MCP_SDK_2X_SPIKE.md)）
- ✅ 只读 `pyobfus-review` skill
- ✅ `COMPARISON.md` 浏览器端混淆服务独立小节

## 待办（按建议顺序）

### 1. 抗 AI 分析的措辞改写（半天 · 诚实性）

`LLM_RESISTANCE_BENCHMARK.md` 的定位从「能不能挡住 LLM」改写为「在什么任务上
挡住多少、代价是什么」，并引用 2026 年的公开实证（arXiv 2609.04220：七个 code
LLM、四语言、五种混淆手法，**直接在混淆代码上推理往往等于甚至优于先还原**，强
模型仍保持约 90% Pass@1）。`COMPARISON.md` 与 README 不得出现「AI 读不懂」这类
表述。新写的 `pyobfus-review` skill 已先行加了这条诚实边界，其余 surface 待同步。

### 2. CycloneDX 版本声明对齐（一两小时）

`pyobfus/core/provenance.py` 写死 `"specVersion": "1.6"`，现行是 1.7
（ECMA-424 第 2 版）。二选一，都诚实：升到 1.7 且只填真实字段；或保持 1.6 但在
`PROVENANCE_MANIFEST.md` 写明「对齐 1.6，未使用 1.7 新增字段」。
顺带评估 1.7 的 **TLP 分发约束**对「交付给指定客户的受保护构建」是否有真实价值。
验收：`--verify-provenance-manifest` 对新旧 manifest 均通过。

### 3. 兼容性 / 验证矩阵（一天 · 零运行时风险）

一张表把 Python 版本 × 框架 preset × 操作系统 × 交付组合（PyInstaller /
Nuitka / Cython / import-hook / 模型服务）标为
**supported / tested / advisory-only**，每格指明证据来源（哪个 CI job、哪篇
cookbook、哪条用户报告，或「未验证」）。**点不到具体证据的一律降级为
advisory-only。** 纯文档，可随任意版本发布。

### 4. 稳定 reason code（两三天 · 动 JSON 契约）

给每个 excluded file、preserved symbol、disabled transform 一个稳定的 reason
code，替代现在的自由文本。涉及 `--check` / dry-run plan / build report 三处
JSON，需要版本字段管理，**排在矩阵之后**，因为矩阵会暴露到底需要哪些 code。

### 5. OpenSSF OSPS Baseline 自评（一天）

对照 [Baseline 2026-02-19](https://baseline.openssf.org/versions/2026-02-19.html)
（Level 1 / Level 2，共 40 条，覆盖访问控制、构建发布、文档、治理、法务、质量、
安全评估与漏洞处理）做一次差距清单。与已有的 OpenSSF Best Practices passing
徽章互补，不重复。产出是差距表，不是一次性全部补齐。

## 周期性

- **下载量复查**：等数据覆盖 2026-09-12（当天发了 `0.5.24` 与 `0.5.25` 两版），
  约 09-15 后看基线有没有抬升。注意发布日与验收流量不能当自然增长。
- **归因查询**：GitHub 代码搜索 `uses: zhurong2020/pyobfus-action`，量的是
  可见性不是采纳量。
- **竞品扫描**：有触发点再做（新对手 / 生态政策变化 / 临近发布），不定期盯梢。

## 外部等待（不阻塞本地开发）

- Claude Plugin Marketplace：2026-08-02 提交，至今 `Submitted and pending
  review`。策略不变：被动等待，不为文案笔误重新提交。
- Open VSX namespace 归属验证：可选，`not verified` 是「未申请」不是「被拒」。

## 明确不做

见 `CURRENT_PLAN_ZH.md` §明确不做。本文件只补一条本轮新增的：**不实现
MCP 的 stateless / streamable-HTTP 传输**，因此也拿不到 `2026-07-28` 协议——
那属于已排除的 hosted MCP 方向，理由见 `MCP_SDK_2X_SPIKE.md` §3。
