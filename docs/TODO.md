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
- ✅ 抗 AI 分析措辞改写（`LLM_RESISTANCE_BENCHMARK.md` 引入 arXiv 2609.04220 + 新增「不得把社区版当 AI 抗性卖」红线）

## 待办（按建议顺序）

### 1. CycloneDX 版本声明对齐（一两小时）

`pyobfus/core/provenance.py` 写死 `"specVersion": "1.6"`，现行是 1.7
（ECMA-424 第 2 版）。二选一，都诚实：升到 1.7 且只填真实字段；或保持 1.6 但在
`PROVENANCE_MANIFEST.md` 写明「对齐 1.6，未使用 1.7 新增字段」。
顺带评估 1.7 的 **TLP 分发约束**对「交付给指定客户的受保护构建」是否有真实价值。
验收：`--verify-provenance-manifest` 对新旧 manifest 均通过。

### 2. 兼容性 / 验证矩阵（一天 · 零运行时风险）

一张表把 Python 版本 × 框架 preset × 操作系统 × 交付组合（PyInstaller /
Nuitka / Cython / import-hook / 模型服务）标为
**supported / tested / advisory-only**，每格指明证据来源（哪个 CI job、哪篇
cookbook、哪条用户报告，或「未验证」）。**点不到具体证据的一律降级为
advisory-only。** 纯文档，可随任意版本发布。

### 3. 稳定 reason code（两三天 · 动 JSON 契约）

给每个 excluded file、preserved symbol、disabled transform 一个稳定的 reason
code，替代现在的自由文本。涉及 `--check` / dry-run plan / build report 三处
JSON，需要版本字段管理，**排在矩阵之后**，因为矩阵会暴露到底需要哪些 code。

### 4. OpenSSF OSPS Baseline 自评（一天）

对照 [Baseline 2026-02-19](https://baseline.openssf.org/versions/2026-02-19.html)
（Level 1 / Level 2，共 40 条，覆盖访问控制、构建发布、文档、治理、法务、质量、
安全评估与漏洞处理）做一次差距清单。与已有的 OpenSSF Best Practices passing
徽章互补，不重复。产出是差距表，不是一次性全部补齐。

### 5. 对比可见度：拆分对比页 + 上架中立目录（一到两天 · 回答「怎么进对比矩阵」）

背景：在线混淆服务 `pyobfuscate.com` 针对 PyArmor / Nuitka / Cython / PyInstaller
建了**一页一对**的对比矩阵，占住了 "python obfuscator comparison" 这一类查询，
且**页面里完全没有我们**。那是他们的自有营销资产，我们进不去，也不该去要求进。
2026-08-31 的扫描已定下策略：**不追 "online" 这个词**（我们刻意本地化，这是卖点
不是短板），改为用自己的诚实对比内容去接同一批查询。可做的两件具体事：

- **把 `COMPARISON.md` 的各节拆成独立页**，一页一个对手（PyArmor / Nuitka /
  Cython / PyLocket / 浏览器端服务 / SOURCEdefender …），`COMPARISON.md` 退化成
  索引页。**拆分而非复制**——同内容两处会互相稀释。head-to-head 查询按页排名，
  这正是对手矩阵的结构优势。每页保留现有的诚实口径：不贬低对方、写清各自适用
  场景。
- **AlternativeTo 上架**（已在下方分发队列第 5 项）。那是**中立第三方**的
  「PyArmor 替代品」清单，搜这类词的人真的会落到那里，是我们能进的「对比矩阵」。

不做：在对手页面下留言/要求收录、买对比位、为排名写夸大文案。

## 分发 / 上架队列

来自 [`DISTRIBUTION_EXPANSION_RESEARCH_2026-09-07.md`](DISTRIBUTION_EXPANSION_RESEARCH_2026-09-07.md)
的执行顺序，前两项（Open VSX、GitHub Action）已完成，队列推进到第 3 项：

1. ~~Open VSX~~ ✅ 2026-09-07
2. ~~独立 GitHub Action + Marketplace~~ ✅ 2026-09-10
3. **`awesome-python`** ← 当前队头
4. `awesome-security` 或 `awesome-devsecops`（择一尝试）
5. **AlternativeTo**（同时服务上面第 6 项的对比可见度）
6. 为 stdio MCP 准备 MCPB，之后再评估 Smithery
7. Product Hunt——**等有真实用户信号再做**，不提前

另有一项新增：**`pyobfus-review` skill 尚未在任何渠道上架**（Smithery 上的是
`pyobfus-protect`）。等 skill 有实际使用反馈再考虑投递，不为上架而上架。

## 已研究、明确延后（不在队列里，但别忘了）

| 项 | 来源 | 解冻条件 |
|---|---|---|
| self-dogfooding 四条 lane 落地 | `SELF_DOGFOODING_BEST_PRACTICES.md` | 研究完成未执行；无外部压力，机会性做 |
| MCP Resources / Prompts 原语拆分 | `MCP_PRIMITIVES_DESIGN.md` | 等真实 MCP 用户反馈 |
| 放开 `mcp<2.0.0` 上限 | `MCP_SDK_2X_SPIKE.md` §5 | `mcp-sdk-2x` job 连绿数周 / 有人明确要 2.x / 1.x 停止维护，三者任一 |
| `--output-pyc` 可行性 spike | `CURRENT_PLAN_ZH.md` P3-1 | 只做 spike，不承诺产品化 |
| hosted / remote MCP endpoint | 同上 P3-2 | 明确不做（也因此拿不到 `2026-07-28` 协议） |
| `dependency_advisory` 是否拆成独立工具 | `SEO_AND_COMPETITOR_SCAN_2026-08-31.md` §1.2 | 独立赛道已拥挤，**倾向不拆**，除非出现明确差异点 |

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
