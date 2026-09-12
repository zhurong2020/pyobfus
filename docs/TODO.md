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

## 本轮已完成的去处

不在这里留历史层。2026-09-12 完成的六项（0.5.25 的三项修复、mcp 2.x 兼容与
CI job、只读 review skill、浏览器端对比小节、抗 AI 措辞改写、支持矩阵）记在
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 的「09-12 发布后续」段。

## 节奏（2026-09-12 用户定）

**过几天再动手，靠持续发版与更新吸引流量。** 下面的排序按这个前提写：**免发版的
先做**，攒够一个有意义的增量再发版，不为发版而发版。

一条要一起记住的事实，免得把噪音读成增长：本项目历史上每次发布当天下载都会尖峰，
随后 2–3 天回落到安静区间，**至今没有观测到基线抬升**（0.5.22 后三个干净日
`65 / 48 / 31` 是最近一次验证）。所以「发版吸流量」的收益要看**非发布日的基线**
是否上移，而不是看发布当天的数字。下次复查见本文件「周期性」。

## 待办（按建议顺序）

判断标准：**只动 `docs/` 或外部渠道 = 免发版**（改动一进 main 就在 GitHub 与文档
站生效）；**动 `pyobfus/` 或 `pyobfus_mcp/` 的代码 = 要发版才到用户手里**。

| # | 任务 | 要发版吗 | 谁来做 |
|---|---|---|---|
| 1 | CycloneDX 版本声明对齐 | **取决于选哪条**：升 1.7 改代码→要发版；保持 1.6 + 文档写明→免发版 | Claude |
| 2 | 让 `examples/` 在 CI 里真的跑 | 免发版（只动 `.github/workflows/` 与 `examples/`） | Claude |
| 3 | 稳定 reason code | **要发版**（改 `--check` / plan / build report 三处 JSON） | Claude |
| 4 | OpenSSF OSPS Baseline 自评 | 免发版（产出差距表；个别项可能要改仓库设置） | Claude 出表，设置项需维护者 |
| 5 | 对比可见度：拆分对比页 + 上架目录 | 免发版（拆页纯 docs；上架需对方站点提交） | 拆页 Claude；上架需维护者账号 |

### 1. CycloneDX 版本声明对齐（一两小时）

`pyobfus/core/provenance.py` 写死 `"specVersion": "1.6"`，现行是 1.7
（ECMA-424 第 2 版）。二选一，都诚实：升到 1.7 且只填真实字段；或保持 1.6 但在
`PROVENANCE_MANIFEST.md` 写明「对齐 1.6，未使用 1.7 新增字段」。
顺带评估 1.7 的 **TLP 分发约束**对「交付给指定客户的受保护构建」是否有真实价值。
验收：`--verify-provenance-manifest` 对新旧 manifest 均通过。

### 2. 让 `examples/` 在 CI 里真的跑（半天到一天 · 免发版）

`SUPPORT_MATRIX.md` 点名的最大缺口：**没有任何 `examples/` 在 CI 中执行**，它们
只在写的时候人工跑通过。分两批，别一次全上：

- **第一批（便宜，进常规 CI）**：`simple.py` / `string_encoding.py` /
  `keyword_arguments.py` / `multifile/` / `ai_debugging/`（混淆 → 执行 → 
  `--unmap` 还原）/ `import_hook/`（loader 是自包含的，不需要 SOURCEdefender）。
  纯 Python，无重依赖，秒级。
- **第二批（重，单独 job 或定时触发）**：`pyinstaller/` 与 `compiled_packaging/`
  需要装 PyInstaller / Cython / Nuitka 并真正编译，分钟级且易受上游影响。
  **建议先只跑第一批**，第二批视 CI 时长再定，或放到每周定时。

验收：第一批每个示例都**执行生成的产物并断言输出**，不是只看退出码；跑通后把
`SUPPORT_MATRIX.md` 对应格子从 advisory-only 提到 tested，并在表里写明是哪个 job。

### 3. 稳定 reason code（两三天 · 动 JSON 契约）

给每个 excluded file、preserved symbol、disabled transform 一个稳定的 reason
code，替代现在的自由文本。涉及 `--check` / dry-run plan / build report 三处
JSON，需要版本字段管理，**排在矩阵之后**，因为矩阵会暴露到底需要哪些 code（矩阵已完成，见 `SUPPORT_MATRIX.md`）。

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
3. **`awesome-python`** ← 当前队头（**需维护者账号提 PR**；文案可由 Claude 先备好）
4. `awesome-security` 或 `awesome-devsecops`（择一尝试）
5. **AlternativeTo**（**需维护者在对方站点提交**；同时服务上面第 5 项的对比可见度）
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
