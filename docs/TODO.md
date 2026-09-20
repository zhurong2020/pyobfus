# TODO

排期中的任务清单。**当前计划与状态仍以
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 为准**；本文件只回答「接下来按什么
顺序做」，不记录历史。依据与实测证据见
[`FEATURE_EXPANSION_RESEARCH_2026-09-12.md`](FEATURE_EXPANSION_RESEARCH_2026-09-12.md)。

最后更新：2026-09-20（对标竞品 + 国际最佳实践 + 本地已完成/未发版做了一次三透镜
重排，见 `FEATURE_EXPANSION_RESEARCH_2026-09-12.md` 之上的本轮外部核查；新增
**服务端邮箱登记 trial** 为 P1，依据见 `TRIAL_STRATEGY_DECISION_2026-09-20.md`；
把 provenance / SARIF / build-report / CycloneDX 收拢为一条「可验证性主线」抬为 P0。
Core `0.5.27` 仍是当前公开版本，运营复查见 `CURRENT_PLAN_ZH.md`）。

## 状态口径

- **实现**与**发布**是两道各自独立的 gate，都需要用户明确批准。
- 任何一项做完后，把它从本文件移除，并在 `CURRENT_PLAN_ZH.md` 记状态；
  不要在这里留「✅ 已完成」的历史层。
- **下游反馈归属（2026-09-17）**：pyobfus 是本工作区自行维护的公共 PyPI 工具。
  CAC Plus 或其他项目暴露的通用混淆缺口、最小复现和回归证据，必须同步登记在本仓库
  （公开 TODO 使用去标识描述，敏感交付背景只进入本地 internal 记录），不能只留在下游文档。
  下游是否选择混淆自己的代码由其分发边界决定；公开第三方依赖不因被打包而自动成为
  pyobfus 的处理目标。

## 本轮已完成的去处

不在这里留历史层。2026-09-12 完成的六项（0.5.25 的三项修复、mcp 2.x 兼容与
CI job、只读 review skill、浏览器端对比小节、抗 AI 措辞改写、支持矩阵）记在
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 的「09-12 发布后续」段。

2026-09-19 完成的三项（CycloneDX 1.7 对齐、`examples/` 第一批进 CI 实跑、测试
fixture 漏临时目录）记在同一文件的「09-19」段。其中只有 CycloneDX 那项改了
`pyobfus/` 代码，因此 held 在 `CHANGELOG.md` 的 `[Unreleased]`，要发版才到用户手里。

## 节奏（2026-09-12 用户定）

**过几天再动手，靠持续发版与更新吸引流量。** 下面的排序按这个前提写：**免发版的
先做**，攒够一个有意义的增量再发版，不为发版而发版。

一条要一起记住的事实，免得把噪音读成增长：本项目历史上每次发布当天下载都会尖峰，
随后 2–3 天回落到安静区间，**至今没有观测到基线抬升**（0.5.22 后三个干净日
`65 / 48 / 31` 是最近一次验证）。所以「发版吸流量」的收益要看**非发布日的基线**
是否上移，而不是看发布当天的数字。下次复查见本文件「周期性」。

## 待办（按建议顺序 · 2026-09-20 三透镜重排）

判断标准：**只动 `docs/` 或外部渠道 = 免发版**（改动一进 main 就在 GitHub 与文档
站生效）；**动 `pyobfus/`、`pyobfus_mcp/` 的代码或 Worker = 要部署 / 要发版才到
用户手里**。

**战略重估（本轮外部核查后）**：pyobfus 的护城河不是"保护强度"（PyArmor 9.2.7
已上 VMC/ECC 虚拟机档，纯 AST 追不上），而是"供应链透明与可验证性"——SARIF /
PEP 740 / build report / CycloneDX 1.7（已落 ECMA-424 2nd ed）/ OSPS Baseline /
SLSA v1.2 这一簇开放标准正是 2026 采购与 DevSecOps 在问的东西。因此把散落的
provenance 项收拢为**一条主线抬为 P0**；**明确不追** PyArmor 的保护强度，只在对比页
诚实标注差距。

| 优先级 | 任务 | 要发版吗 | 谁来做 |
|---|---|---|---|
| **P0** | 可验证性主线：CycloneDX 1.7 增量 + build report/provenance 显式对标 SLSA v1.2 与 CycloneDX citations + 稳定 reason code，凑成一个"供应链透明"版本 | 对标文档免发版；reason code + 发版要批准 | Claude 实现，发版需批准 |
| **P1** | **服务端邮箱登记 trial**（获客向，非 DRM） | Worker 要部署 + 客户端要发版 | Claude 实现，部署/发版需批准 |
| ~~P1~~ ✅ | OSPS 补齐**基本完成 2026-09-20**：4 开关（gh api 核实）+ 4 文档（f2cd713）全做完。残余 = `LE-01.01` DCO（主动延后）+ 若干 L3 | 免发版 | — |
| **P1** | 抗 AI 措辞改写（`docs/TODO.md` 遗留项，tech-deai）。~~pyarmor VMC/ECC 补记~~——核查后确认 `compare/pyarmor.md` **已诚实覆盖** 9.2.x VMC/ECC，无需改 | 免发版 | Claude |
| **P2** | 分发上架队列（awesome-python → awesome-security → AlternativeTo） | 免发版（提交需维护者账号） | Claude 备文案，提交需维护者 |

### P1 · 服务端邮箱登记 trial（尽快实现 · 获客向，非 DRM）

决策与完整设计见 [`TRIAL_STRATEGY_DECISION_2026-09-20.md`](TRIAL_STRATEGY_DECISION_2026-09-20.md)。
用户 2026-09-20 选定方案 A：**维持本地 5 天 trial、不设行数/文件数上限**（本地限制对
可读源码的 Pro 是安全戏法且伤评估者），**不改"先收费"trial**（当前无有机增长信号，加
购买摩擦反漏斗）；把 trial 挪到服务端并顺手做成获客渠道。

- **免发版**：本决策文档、TODO 登记、Worker 端点设计评审（已完成本条）。
- **要部署**：Worker 新增 `POST /api/trial/request`（email + device_id → 签名
  trial token；KV 以 email 去重；复用 `/api/verify` 同源签名工具，不 DIY 加密；
  速率限制；PII 不落明文日志）。**先于客户端部署**（硬约束，同 0.5.26 教训）。
- **要发版**：客户端 `pyobfus-trial start --email <addr>` 换 token；离线/不带
  `--email` 回退现有纯本地 5 天（不回归）。
- 验收标准见决策文档 §5.4。诚实边界：服务端登记解决**去重 + 获客**，不宣称能挡住
  能读 Pro 源码的人。

### P0 · 稳定 reason code（两三天 · 动 JSON 契约）

给每个 excluded file、preserved symbol、disabled transform 一个稳定的 reason
code，替代现在的自由文本。涉及 `--check` / dry-run plan / build report 三处
JSON，需要版本字段管理，**排在矩阵之后**，因为矩阵会暴露到底需要哪些 code（矩阵已完成，见 `SUPPORT_MATRIX.md`）。

### ✅ OSPS Baseline 补齐（2026-09-20 基本完成）

差距表 `OSPS_BASELINE_SELF_ASSESSMENT_2026-09-20.md`。**四个维护者开关 + 四份文档
均已完成**（gh api 核实：私密漏洞上报 / secret scanning + push protection /
`protect-main` ruleset / Dependabot 全 enabled；GOVERNANCE / THREAT_MODEL /
dependabot.yml / CI 最小权限见 commit f2cd713）。

**残余（不急，不列为当前主线待办）**：
- `LE-01.01` DCO sign-off — 单维护者主动延后，等有外部协作者再上。
- L3 阈值政策（SCA/SAST）、`QA-02.02` SBOM → 后者并入 **P0 可验证性主线**。
- ⚠️ `.github/dependabot.yml` **需 push 到 origin 后 Dependabot 才生效**。


### P1/P2 · 对比可见度 —— 拆页已完成，只剩上架（+ PyArmor 9.2.7 诚实性）

**已完成 2026-09-13**：`COMPARISON.md` 由 490 行的单页拆成索引页 + `docs/compare/`
下 7 个一页一对手的页面（PyArmor / Nuitka / Cython / PyLocket / Oxyry /
浏览器端 / 其它工具）。**拆分而非复制**：索引页只留跨对手的内容（速览表、特性矩阵、
三年成本、分层部署、结论），head-to-head 内容整段移走，两处不会互相稀释。逐行核对
过原文每一行都有去处，差异只有 7 行且全部有意（旧导语、两个纯结构性 H2、两处与新
导语重复的开场白、两个改名的迁移小节标题）。已接入 mkdocs 导航、README 与
`llms.txt`（孪生文件已同步）；`mkdocs build --strict` 通过——拆分过程中它抓到了 3
条因内容移入子目录而失效的相对链接。README 原有的 `#layered-deployment-strategy`
锚点仍在索引页上，未断。

**已核查确认无需改（2026-09-20）**：外部核查发现 PyArmor 最新为 **9.2.7（2026-08-14）**、
新增 VMC/ECC 虚拟机档。回查 `docs/compare/pyarmor.md` §"Bytecode Protection Is Not
Magic"**已经**诚实写明 9.2.x 的 `--vmc`/`--ecc` 函数级虚拟化是 pyobfus 结构上没有的
能力、并指用户去 PyArmor。**只是版本号写作"9.2.x"而非"9.2.7"，但 9.2.x 表述仍准确**，
且页内 9.2.4 是绑定实测的 trial-limit 实验版本、不能改。故此项**已完成，非待办**。

**仍未做（需维护者账号）**：**AlternativeTo 上架**（见下方分发队列第 5 项）。中立
第三方的「PyArmor 替代品」清单，搜这类词的人真的会落到那里。**需维护者在对方站点
提交**。

不做：在对手页面下留言/要求收录、买对比位、为排名写夸大文案。

## 待发内容（已在 main，未发版）

发版本身是独立 gate。下面内容已经合进 `main` 或进入本轮 release-candidate 提交，
但要发布才会到用户手里：

- **`pyobfus_mcp/CHANGELOG.md` 的 `[Unreleased]`**：mcp SDK 2.x 兼容。**刻意没有随
  Core 0.5.27 一起发**——这是独立 MCP 增量，不应捆绑到 Core 发布；且每发一次 MCP 都要
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

## 真实交付场景暴露的 Pro 缺口（2026-09-14 · 待排期，优先级待维护者定）

来自一个把 Pro 输出交付到第三方离线 Windows 机器的内部下游项目（torch/MONAI +
Python 3.13 嵌入版）。这是 Pro 输出第一次真正交付到别人的机器上。详细背景在本地私有的
`docs/internal/DOWNSTREAM_DEMAND_2026-09-14.md`。**不改动上面的排期顺序**，只登记。

| # | 缺口 | 证据 | 方向 |
|---|---|---|---|
| **Y-1** 🔴 | **Pro 运行时无法合法随输出分发**，影响所有使用 L3 opacity / `--scrub-traceback` / `--expire-hard` 的客户 | 2026-09-14 实验：L3 输出保留 `from pyobfus_pro import opacity, Layer` 和 `from pyobfus_pro.runtime import _l3_dispatch`，scrub 与 expire 同样注入 `pyobfus_pro` import；在没有 pyobfus_pro 的解释器上运行报 `ModuleNotFoundError`。而 `pyobfus_pro/LICENSE` §2a 禁止分发，没有运行时例外条款。标记 import 还会连带加载整个 `pyobfus_pro/__init__` | ① 独立的最小 `pyobfus-runtime` 包（运行时不需要许可证 key）；② 许可证加运行时再分发例外；③ 后处理时剥掉标记 import；④ 在 README 和 SUPPORT_MATRIX 写明交付要求 |
| Y-2 | `--expire-hard` 没有到期前提醒，不能不重新构建就延期 | `build_fusion._inject_expire_check` 在模块顶部直接抛 `LicenseExpired` | `--expire-warn-days N` 或提醒回调 |
| Y-3 | 设备绑定只认 pyobfus 自己的 `current_machine_id()` | 自带授权体系（JWT 加自有机器码）的应用，无法在不逐机器构建的前提下把 L3 密钥绑定到自己的授权上 | 运行时"密钥提供者"钩子，应用验签后提供密钥材料 |
| ~~Y-4~~ ✅ | ~~Windows 上运行混淆输出没有 CI 验证~~ **已补基础合同** | `integration` job 扩为 Ubuntu + Windows；单文件和跨文件示例均执行混淆产物并与原输出比较 | 覆盖基础 Community 交付；torch/MONAI、Python embedded、L3 runtime 等重型真实下游组合仍需 Y-1 专项验证 |
| ~~Y-6~~ ✅ | ~~name-mangling 打断运行时注解~~ **已修** | 函数签名表达式此前被跳过，或在参数局部作用域压栈后才遍历，导致同模块/导入类改名后 eager annotation 仍引用旧名 | 注解和默认值现在按 Python 语义在函数局部作用域压栈前改写；端到端测试覆盖同模块、跨模块、默认值及参数名遮蔽导入类型 |
| ~~Y-7~~ ✅ | ~~cross-file mangler 作用域 bug~~ **已修** (`069a820`) | 函数局部变量复用被重命名的模块级名字时 Load 引用被误改 → `NameError: name 'Ixx'`。`LocalNameTransformer` 现按 Python 作用域收集函数体内全部绑定名（含 lambda/推导式作用域）| 已修 + 2 回归测试 |
| ~~Y-8~~ ✅ | ~~control-flow flattening 的 `_cff_return_N` 未绑定~~ **已修** | 根因并非函数大小本身：一条路径显式 `return`、另一条路径自然落底时，统一生成的 `return _cff_return_N` 会读取未初始化变量。大型 `try/finally` 只是更容易出现这种路径组合 | 状态机启动前将共享 return slot 初始化为 Python 隐式返回值 `None`；已补最小条件分支与 `try/finally` early-return 两个回归测试 |
| ~~Y-5~~ ✅ | ~~文档漂移~~ **已修** | `pyobfus.yaml.example` 已与社区版无文件/行数限制和 Community Base64 encoding 的现状对齐 | 新增 `OPACITY_CONFIG.md`，记录 TOML 字段、匹配/优先级、CLI 只物化 encrypted 顶层函数的边界和 Y-1 交付限制 |

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

- **下载量复查**：**2026-09-19 已查**，数据覆盖至 09-18（见
  `CURRENT_PLAN_ZH.md` 09-19 条目）。结论：09-16 的 0.5.27 发布日为 `68`（低于
  历史尖峰），其后两个干净日 `18 / 32` 回落 20–40 安静区间——**09-15 的 `99`
  判定为 0.5.26 长尾，基线未抬升**，该悬置问题已关闭。下次复查照旧看非发布日
  基线是否上移；注意发布日与验收流量不能当自然增长。
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
- **Canopii [`canopii-cli#6`](https://github.com/canopii-dev/canopii-cli/issues/6)
  —— ⏰ follow-up 已到期**。2026-09-19 实测：仍 `OPEN`、**0 条回复**、最后更新
  停在 2026-09-02，距今 17 天，已越过既定的「14 天无回复只做一次简短 follow-up」。
  **这条此前只写在 `CURRENT_PLAN_ZH.md` 深处、没有进本文件**，所以到期了也没人看见——
  现在登记在此。follow-up 只发一次，不反复催。上游重扫后按四项验收（latest ≥ v0.3.10 /
  识别 8 tools / 不再把 `pyobfus_pro/`、`examples/`、VS Code/Worker 计入 MCP 包
  evidence / PEP 740 provenance 是否被识别），**不是只看总分**。
- **MCP Trust Checker 登记**：尚未执行，无外部依赖，想做随时可做。同上，此前也只在
  `CURRENT_PLAN_ZH.md` 里。

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
