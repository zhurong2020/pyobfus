# TODO

排期中的任务清单。**当前计划与状态仍以
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 为准**；本文件只回答「接下来按什么
顺序做」，不记录历史。依据与实测证据见
[`FEATURE_EXPANSION_RESEARCH_2026-09-12.md`](FEATURE_EXPANSION_RESEARCH_2026-09-12.md)。

最后更新：2026-09-13。

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

## P0 · 许可系统可靠性（2026-09-13 故障后新增，排在下面所有项之前）

背景：2026-09-12 一位新客户报激活失败，查出 **Pro 联网激活对所有客户全线失效**，
最后一次成功验证停在 2026-07-08，无人察觉近两个月。根因是 Cloudflare 边缘拦
`urllib` 默认 UA，但**真正让它变成收入损失的是两件设计缺陷**：许可系统对付费
客户 **fail closed**，并且**没有任何监控**。完整档案见 memory
`pyobfus_license_edge_block_2026-09-12`。

排序依据：先做最便宜且防复发的，再做消灭整类故障的，最后才动指纹算法——因为
P0-2 到位之后指纹准不准就不再会伤到客户。

| # | 任务 | 要发版吗 | 需要维护者 |
|---|---|---|---|
| P0-1 | 发 `0.5.26`（UA 修复）+ 合成监控 | **要发版**（`pyobfus_pro/license.py` 已改） | 发版批准 |
| P0-2 | 校验 fail open + 设备滚动淘汰 | **要发版** + 部署 Worker | 部署批准 |
| P0-3 | `pyobfus-license deactivate` + 管理端重置端点 | **要发版** + 部署 Worker + 建 secret | 建 `ADMIN_TOKEN` |
| P0-4 | 设备指纹改为稳定标识 | **要发版** | 无 |

### P0-1 发 0.5.26 + 合成监控

修复已在 `e2e9d54`（未推送）。发版走既有流程，但**验收标准与平时不同**：
全新 venv 装完之后要**真的对生产端点跑一次激活**，因为这个版本修的就是这条
路径，装上了没跑通等于没验证。用户本人的序列号可用于此，取用见 memory
`reference-owner-pro-license-key`。GitHub Release 说明里必须写上 `--no-verify`,
因为升级只救新安装，已装机器看不到修复。

**合成监控是这一项真正的产出**：定时 GitHub Action 用一个**不存在的**序列号
打生产 `/api/verify`，断言拿回的是 Worker 自己的 JSON（`Invalid license key`），
而不是任何别的 403 或非 JSON 响应。零副作用：不碰客户数据、不占设备槽位、
不需要把真序列号放进 CI secrets。**这个探针如果两个月前就有，第二天就会报警。**

验收：PyPI latest = 0.5.26 且两个 provenance 端点 200；全新 venv 实跑激活成功；
监控 workflow 在 main 上真跑过一次并通过；**故意把断言指向一个会被拦的 UA，
确认它会红**（不验证告警会响的监控等于没有）。

### P0-2 校验 fail open + 设备滚动淘汰

两个改动消灭整类「付了钱用不了」故障。

**客户端 fail open**：`pyobfus/cli.py` 现在对任何 `LicenseError` 都
`sys.exit(1)`。对于一个 **active、未吊销**的许可证，联网失败或设备超限应当
**警告并继续**，而不是阻断构建。吊销才是对付滥用的手段，它随时可用且精确。
仍然 fail closed 的只有：格式非法、服务端明确说 revoked/expired。

**服务端滚动淘汰**：`cloudflare-worker/src/index.js` 的 `handleVerify` 现在在
`devices.length >= 3` 时返回 403 拒绝。改为给每条设备记 `last_seen`，超限时
**淘汰最久未用的那台**并放行新机器。这一条单独就能消灭锁死，且不依赖指纹准确。

**为什么紧急**：`pyobfus-license remove` 只删本地缓存，服务端记录永远留着，
Worker 只追加从不删除。所以每次重装/换机/升级 OS 都永久吃掉一格，客户无法回收。
**锁死不是风险，是排期中的必然。**

验收：无缓存 + 服务端不可达时 `--level pro` 仍能构建并打印警告，退出码 0；
revoked 仍然阻断；Worker 单测覆盖「第 4 台挤掉最久未用」且 `last_seen` 有更新。

### P0-3 `deactivate` + 管理端重置端点

今天为清理一位客户的设备列表，走的是「临时放开 token 写权限 → 手工改生产 KV →
调回权限」。不可重复、无日志、无审计，每一步都能写坏客户记录。**这不该是常规
运维**。

**第一层自助**：`pyobfus-license deactivate`，把当前机器从服务端列表摘掉，多数
工单从此不产生。注意现有 `remove` 只删本地缓存，名字容易被误解为解绑，文案要
一并澄清。

**第二层管理端点**：认证用专用 `ADMIN_TOKEN`（`wrangler secret put`），常量时间
比较（复用修 Stripe 签名时那个已验证的实现），**绝不复用 Cloudflare API token**，
那是基础设施凭证不是应用凭证。记录上留 `devices_reset_at` / `reset_reason`。

**还缺备份**：KV 是许可数据唯一副本，写坏无法恢复。至少把「改动前先导出」写进
步骤，更好是定期导出整个 namespace。

验收：`deactivate` 后服务端该设备消失且可用新机器注册；管理端点无 token/错
token 一律 401 且不泄露记录是否存在；审计字段落库。

### P0-4 设备指纹改为稳定标识

现在是 `sha256(MAC + 主机名 + 系统 + OS版本号)`，三个问题：

- **身份取自会变的东西**：`platform.release()` 进哈希，macOS 打小更新身份就变
  （实测 Darwin 25.4.0 → 25.5.0 指纹完全不同）。`uuid.getnode()` 拿不到网卡地址
  时 Python 返回随机数，那样每次运行都是新设备。现代系统还有 MAC 随机化。
- 客户 richard.trapp95 2026-06-10 的抱怨「it keeps thinking I'm different
  devices」正是这个，我们当时没回。

改法：首次运行生成随机 ID 持久化到 `~/.pyobfus/device_id`，之后一直用它，跨 OS
升级/venv/容器都稳定。**有人会说这个文件可以复制**——纯 Python 客户端里的一切
都可以复制，而本项目在 issue #20/#21 上已公开采取「诚实记录边界、不加固客户端」
的立场，持久化随机 ID 与该立场一致；硬件指纹反而是在假装有一层并不存在的保护。
$45 的开发者工具上，设备绑定的真实作用是阻止一个 key 传遍整个公司，不是防破解。

迁移：客户总共几个，改算法时把 devices 清空即可（需 P0-3 的端点或人工）。

验收：同机两次调用恒等；mock `platform.release()` 变化后指纹不变；
`~/.pyobfus/device_id` 缺失时能重建且不崩；测试全程绑定到 `tmp_path`。

## 待办（按建议顺序）

判断标准：**只动 `docs/` 或外部渠道 = 免发版**（改动一进 main 就在 GitHub 与文档
站生效）；**动 `pyobfus/` 或 `pyobfus_mcp/` 的代码 = 要发版才到用户手里**。

| # | 任务 | 要发版吗 | 谁来做 |
|---|---|---|---|
| 1 | CycloneDX 版本声明对齐 | **取决于选哪条**：升 1.7 改代码→要发版；保持 1.6 + 文档写明→免发版 | Claude |
| 2 | 让 `examples/` 在 CI 里真的跑 | 免发版（只动 `.github/workflows/` 与 `examples/`） | Claude |
| 2.5 | 测试 fixture 漏临时目录 | 免发版（只动测试） | Claude |
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

### 2.5 测试 fixture 漏临时目录（一两小时 · 免发版 · 跨 session 发现）

来源不是本 session：2026-09-12 另一个 session 做全工作区 `/tmp` 清理时统计到
**pyobfus 测试残留 32 项 / 212 文件**，并把它列为该次台账的「结构性建议」第 1 条
（`~/projects/home/archives/project_docs/TMP_CLEANUP_20260912.md`）。**本 session
已逐条核实属实**，是代码缺陷不是操作疏忽：

| 位置 | 症状 |
|---|---|
| `tests/test_license_embed.py:228` | `NamedTemporaryFile(delete=False, suffix=".pyobfus_test")`，零字节文件永不删除 |
| `tests/test_license_verification.py:137` | `setup_method` 里 `mkdtemp()`，`teardown_method` 只清 license 缓存、**不删目录** |
| `vscode-extension/test/suite/{obfuscateFile,validateConfig,yamlSchema}.test.ts` | 多处 `mkdtempSync` / `mkdtemp`（前缀 `pyobfus-config-test-` / `pyobfus-validate-test-` / `pyobfus-yaml-modeline-`）无清理 |
| `vscode-extension/test/suite/integration.test.ts:168` | 手拼 `os.tmpdir()` 路径，同样无清理 |

修法：Python 侧改用 pytest 的 `tmp_path`（本仓库其它测试已是这个写法），或在
`teardown_method` 里 `shutil.rmtree(..., ignore_errors=True)`；TS 侧在 `suiteTeardown`
统一 `rm -rf`。体积可忽略，值得修的原因是**每跑一次测试就留一批**，而我们一天
可能跑几十次。

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
