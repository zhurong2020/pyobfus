# TODO

排期中的任务清单。**当前计划与状态仍以
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 为准**；本文件只回答「接下来按什么
顺序做」，不记录历史。依据与实测证据见
[`FEATURE_EXPANSION_RESEARCH_2026-09-12.md`](FEATURE_EXPANSION_RESEARCH_2026-09-12.md)。

最后更新：2026-09-13（P0 许可系统可靠性四项已全部发布为 `0.5.26`；同日又做了公开门面审计，五处问题四处已修，去处均见 `CURRENT_PLAN_ZH.md`）。

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

### 5. 对比可见度 —— 拆页已完成，只剩上架

**已完成 2026-09-13**：`COMPARISON.md` 由 490 行的单页拆成索引页 + `docs/compare/`
下 7 个一页一对手的页面（PyArmor / Nuitka / Cython / PyLocket / Oxyry /
浏览器端 / 其它工具）。**拆分而非复制**：索引页只留跨对手的内容（速览表、特性矩阵、
三年成本、分层部署、结论），head-to-head 内容整段移走，两处不会互相稀释。逐行核对
过原文每一行都有去处，差异只有 7 行且全部有意（旧导语、两个纯结构性 H2、两处与新
导语重复的开场白、两个改名的迁移小节标题）。已接入 mkdocs 导航、README 与
`llms.txt`（孪生文件已同步）；`mkdocs build --strict` 通过——拆分过程中它抓到了 3
条因内容移入子目录而失效的相对链接。README 原有的 `#layered-deployment-strategy`
锚点仍在索引页上，未断。

**仍未做**：**AlternativeTo 上架**（见下方分发队列第 5 项）。那是**中立第三方**的
「PyArmor 替代品」清单，搜这类词的人真的会落到那里，是我们能进的「对比矩阵」。
**需维护者在对方站点提交**。

不做：在对手页面下留言/要求收录、买对比位、为排名写夸大文案。

## 待发内容（已在 main，未发版）

发版本身是独立 gate。下面两项已经合进 `main`，但要发布才会到用户手里：

- **Core `[Unreleased]`**：README 的 46 条相对链接改为绝对 URL（在 PyPI 上原本全部
  404），以及 `[project.urls]` 的修正（原先把一份四月的内部策略备忘录标为
  "AI Integration Guide"、把中文内部排期标为 "Current Plan"）。**项目 URL 是打包时
  固化进分发包的，所以侧边栏要等下次发版才会变**；README 链接同理。
- **`pyobfus_mcp/CHANGELOG.md` 的 `[Unreleased]`**：mcp SDK 2.x 兼容。**刻意没有随
  0.5.26 一起发**——那是 Core 的紧急修复，不该捆绑无关内容；且每发一次 MCP 都要
  手工改一次 Glama 的 Build steps。攒够增量或有人明确要 2.x 时再发。

## 本轮留下的小尾巴（都不急，按顺手程度做）

- **`docs/index.md` 的购买段仍是当年为 Jekyll 写的内联 HTML**，紫色渐变配色与新落地页
  和 logo 的品牌色对不上。Material 能正常渲染，只是不好看。想统一视觉时一起改。
- **落地页只有一页**（`landing/index.html`）。目前够用：它要回答的只有"这是什么、
  值不值 $45、怎么买"。若以后要加截图或用例页，注意别把它做成第二个文档站——
  文档归 Read the Docs，这是当初两个生成器打架的根源。
- **KV 备份未加密**。本轮刻意保持与既有备份同一口径：同一份每日备份里已有敏感度更高
  的 PHI 临床数据且是明文，只给较小的风险单独套一层加密是不一致的安全戏法。真正该
  决定的是**整个 WSL 每日备份要不要静态加密**，那是跨项目策略，不该由 pyobfus 顺手定。
- **Discussions 沉寂**：6 个主题全部维护者自建、5 个零评论、最后两条停在 2026-08-01。
  结论是**还没有社区，不是没维护**，多发公告改变不了它。不投精力，等真实外部提问再
  顺势开。

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

- **Alipay 文案复查**：Stripe 上 Alipay 自 2026-09-04 起一直是 `Pending approval`
  （Cartes Bancaires 同时挂起，更像账号级审核排队而非 Alipay 单独被卡；微信支付已
  Enabled，中国买家主路径已通）。README 与落地页现写「Alipay (支付宝) is being
  enabled」——**若到 2026-09-27 仍是 Pending，把这句删掉**，等真 Enabled 再加回来。
  我们在对外文案上守「说得准」这条线，这里不该例外。可向 Stripe 支持直接问审核在等什么。

- **下载量复查**：等数据覆盖 2026-09-12（当天发了 `0.5.24` 与 `0.5.25` 两版），
  约 09-15 后看基线有没有抬升。注意发布日与验收流量不能当自然增长。
- **归因查询**：GitHub 代码搜索 `uses: zhurong2020/pyobfus-action`，量的是
  可见性不是采纳量。
- **竞品扫描**：有触发点再做（新对手 / 生态政策变化 / 临近发布），不定期盯梢。

## 第三方授权（2026-09-13 审计 · 因一封 Vercel 邮件触发）

**判断标准不是「还在用吗」，而是「它能对 pyobfus 做什么」。** `release.yml` 由推送
`v*.*.*` 标签触发，走 OIDC 直接发布 PyPI 并生成 PEP 740 签名——**任何对本仓库有
`contents: write` 的第三方，等于对 PyPI 有以你名义发布的能力**。这不是假设某个厂商
会作恶，是授权本身就该按「能不能」而非「会不会」来给。

已处理：

- **GitHub Learning Lab — 已卸载**。它 2022-09-01 就已关停、课程仓库同年归档，
  GitHub 自己让人改用 GitHub Skills。装着一个停服四年的 App 只剩一份仍然生效的授权。
- **Google Labs Jules — 已卸载**（同样带着一个待批的权限升级请求）。
- **Vercel — 权限升级请求已拒绝**，仓库范围已由 All 收窄到 `pyobfus` 与
  `pyobfus-action` 两个。它请求的是对 administration / code / repository hooks 的
  **读写**，而它的用途是自动部署 PR 预览，我们这两个仓库都不由它部署（文档站在
  Read the Docs，落地页在 GitHub Pages Actions，pyobfus-action 是 Action 仓库）。
- **giscus — 保留**，用于旧博客的评论（基于 GitHub Discussions）。pyobfus 仓库内无
  任何引用。

仍待办：

- [ ] **确认 Vercel 是否还需要装着**。若这两个仓库都不由它部署，卸载最干净；留着也
  **不要批那个权限升级**。当前已授予的权限集无法用 `gh` 枚举（需 GitHub App 自身的
  token），只能在 <https://github.com/settings/installations> 页面看。
- [ ] **确认 giscus 的仓库范围只含博客仓库**，不含 pyobfus。同上，需页面查看。
- [ ] **不要导入 Vercel 提示的那个 "docs" 项目**。它检测到的是 `docs/_config.yml`，
  该文件已于 2026-09-13 随落地页拆分删除；导入会让同一份 `docs/` 长出第三个公开
  站点，正是刚消掉的重复内容问题。

## Zenodo webhook token —— 决定「只验证不轮换」

`repos/.../hooks` 的 Zenodo 条目 URL 里内嵌一个 Zenodo 个人访问令牌（通常带 deposit
写权限）。2026-09-13 排查 Vercel 时曾把 hook 配置整段打印到终端。

**结论：不轮换。** 该值未进仓库、未公开，GitHub 的 webhook 配置本就只有仓库管理员可读；
而轮换要在 Zenodo 关掉再打开仓库以重新生成 webhook，**concept DOI 与仓库的关联一旦
出问题，影响的是 `CITATION.cff`、README 徽章和已发出的学术引用**。用一个确定的风险换
一个很小的风险不划算。

- [ ] 改为**每次发版后验证**：concept DOI 是否指向了新 record。0.5.26 那次正常
      （record `22731176`），链路健康。

## 外部等待（不阻塞本地开发）

- Claude Plugin Marketplace：2026-08-02 提交，至今 `Submitted and pending
  review`。策略不变：被动等待，不为文案笔误重新提交。
- Open VSX namespace 归属验证：可选，`not verified` 是「未申请」不是「被拒」。

## 明确不做

见 `CURRENT_PLAN_ZH.md` §明确不做。本文件只补一条本轮新增的：**不实现
MCP 的 stateless / streamable-HTTP 传输**，因此也拿不到 `2026-07-28` 协议——
那属于已排除的 hosted MCP 方向，理由见 `MCP_SDK_2X_SPIKE.md` §3。

**不为抢 `github.com/pyobfus` 这个用户名去注册商标**（2026-09-13 调研后用户决定关闭）。
**调研结论记在这里，是为了不被重新查一遍**：

- GitHub 用户名政策明确**不受理以「看起来不活跃」为由**的释放请求，理由是并非所有
  活动都公开可见；同一页写明**有效商标投诉是唯一会被审查、可能导致释放的请求类型**。
  所以商标确实是唯一的路。
- 但商标政策的措辞是 **may** release，不是 will：无冒充意图时，GitHub 会先给对方
  澄清机会。而那个账号零活动零内容，**商标法保护的是商业活动中的混淆**，一个什么都
  没做的账号很难说混淆了谁——案子本身偏弱。投诉表单还要求填**注册号**，pending 不算。
- **最可能白花钱的是「描述性」驳回**：`pyobfus` = py + obfus(cation)，对「Python 代码
  混淆软件」几乎是在描述商品本身。它是生造缩合词（类似 Netflix = net+flicks），
  落在描述性与暗示性之间，**需要商标律师看过才能判**。
- 费用：中国 CNIPA 官费 270 元/类（网上、含 10 项）+ 代理费几百到数千，现实约
  600–1000 元，9–12 个月；美国 USPTO $350/类，且 **2019 年起中国主体强制必须请
  美国执业律师**（律师费通常 $1000–2000+），现实约 $1500–2500，12–18 个月。
  GitHub 表单接受 "federal or international" 注册号，**中国注册号是否被接受查不到
  明确说法**——走便宜那条路可能拿不到想要的结果。
- 决定性的成本收益：我们已握有仓库 `zhurong2020/pyobfus`、PyPI 的 `pyobfus`、
  VS Code publisher、MCP Registry 命名空间、Zenodo DOI。那个用户名多给的主要是更短的
  URL，而搬仓库会打断 README 徽章、Zenodo concept DOI 关联、Glama listing 地址与
  `pyobfus-action` 的 `uses:` 引用。

⚠️ **没有一并关闭的是另一件事**：为上海旎嵘科技注册商标做**品牌防护**（防别人在 PyPI
或各类市场用同名发包）本身是否值得，**本轮未做决定**，不要把它当成也被否掉了。若将来
要做，先在中国注册第 9 类（计算机软件）成本很低，拿到后再评估是否加美国。
