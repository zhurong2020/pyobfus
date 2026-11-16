# TODO

**2026-11-16 路线执行台账**：[ROADMAP_EXECUTION_2026-11-16](ROADMAP_EXECUTION_2026-11-16.md)（T1–T5/T3b 已完成；当前状态以台账为准）。

**当前入口**：[路线执行台账](ROADMAP_EXECUTION_2026-11-16.md) →
[当前计划](CURRENT_PLAN_ZH.md) → [竞品与路线复核](COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md)。
最新[会话收尾](SESSION_CLOSEOUT_2026-11-16.md)和[执行进度](EXECUTION_PROGRESS_2026-11-16.md)
是当天早段运维快照，后续 T1–T5/T3b 进度以台账为准。
未来 6–12 个月的五类候选、需求门槛及停止条件见 [ROADMAP](ROADMAP.md)；
实施、发布、Worker 部署和许可签发分别需要维护者批准。

排期中的任务清单。**当前计划与状态仍以
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 为准**；本文件只回答「接下来按什么
顺序做」，不记录已完成历史。

当前版本：Core 0.15.0 / MCP 0.3.17 / runtime 0.1.1 / 扩展 0.4.3 / Action v1.1.0。
最新发布证据见 [Core 0.15.0 核验](CORE_0_15_0_RELEASE_2026-11-15.md)。

## 状态口径

- **实现**与**发布**是两道各自独立的 gate，都需要用户明确批准。
- 任何一项做完后，把它从本文件移除，并在 `CURRENT_PLAN_ZH.md` 记状态；
  路线任务的进度与证据统一记在路线执行台账，不要在这里留「✅ 已完成」的历史层。
- **下游反馈归属（2026-09-17）**：pyobfus 是本工作区自行维护的公共 PyPI 工具。
  内部下游应用或其他项目暴露的通用混淆缺口、最小复现和回归证据，必须同步登记在本仓库
  （公开 TODO 使用去标识描述，敏感交付背景只进入本地 internal 记录），不能只留在下游文档。
  下游是否选择混淆自己的代码由其分发边界决定；公开第三方依赖不因被打包而自动成为
  pyobfus 的处理目标。

## 当前执行顺序（2026-11-16 收口）

T1–T5/T3b 的完成与未发布变更见[执行台账](ROADMAP_EXECUTION_2026-11-16.md)，不再列为未来任务。

1. **T7 范围审阅**：以「自管、可验证交付」整理 Pro 购买路径；提案待维护者确认，
   不改价格／条款，落地页合并即上线，合并前维护者审最终文案。
2. **T8 文档审计**：对照当前事实清理过期入口、历史层及跨文件矛盾；本轮修订不代表审计全部关闭。
   私有事实表与审计报告在主 checkout 的 `docs/internal/doc-audit-2026-11-16/`。
3. **T6（12-01～05）**：12 月第一周搜索／AI 可见性；约 12-04 完成 Core 0.12.0 T+30d，
   此后逐版本观察并入周检，继续观察最新发布反馈。

同一时间只推进一个产品项；无缺陷不发版，12 月中旬前不计划 Core 发版。
周期巡检持续进行；不重复已完成的升级通知，后续支持仅记私有记录。

## 维护者动作清单

维护者专属动作、外部等待及其 gate 见 [MAINTAINER_ACTIONS](MAINTAINER_ACTIONS.md)。

## 发布、兼容与信任 gate

- **Python 3.9**（11-06 确认保留）：Ubuntu 3.9 固定 `ubuntu-24.04`；镜像退役前改用仍提供
  3.9 的 runner 或容器。CI 保持普通 13 格／手动定时 21 格，独立 L3 六格、MCP SDK 六格；
  必需检查 CI result + CodeQL，不改 ruleset。
- **F2／F3**：离线迁移、兼容与验收范围待确认；迁移保持终身授权有效。F2 草稿在私有
  `docs/internal/f2-signed-lease-2026-11-03/`；F3 AES-256-GCM 需要新格式与兼容测试，另立范围。
- **签发 key**：计划内切换须信任版本发布满 180 天，最早约 **2027-05-14**，且至少提前
  **60 天**正式通知最低版本与切换日期；已有升级说明不能替代该通知。工作站／离线迁移延后。
- **IP**：Pro/runtime 专有许可补运行所需专利权条款，等待专业审阅后单独跟进；不自动发版。
  法务事项在仓库外 `pyobfus-legal/IP商业化迁移_TODO.md`；公开标识始终为申请中、尚未授权，
  专利覆盖实现不得进入 Apache-2.0 核心。
- **Agent 文档同步（11-06 定）**：改变参数、退出码、JSON、授权或 MCP 工具时，打 tag 前同一 PR
  同步 `llms.txt`／`docs/llms.txt`、`llms-full.txt`／`docs/llms-full.txt`、
  `templates/ai-integration/AGENTS.md`、`skills/*/SKILL.md`、`docs/.well-known/ai-catalog.json`。
  两份镜像一致；full 只写当前行为和最低版本，历史进 CHANGELOG。
- **独立发布**：runtime 源码变动先升版本、刷新 editable 元数据并先发 runtime，运行
  `scripts/check_runtime_version.py`。MCP／插件／runtime 只在影响各自用户时发。
- 发版清单不变：README 横幅同提交、`scripts/check.sh` 全路径检查、Zenodo 核验；
  每次发版仍须维护者明确批准，不能用下载量替代发布条件。
- VS Code schema 与 README 网络行为修订等插件自己的下次发布带入 Marketplace/Open VSX；
  不改写已发 0.4.3 页面。runtime README 修订等 runtime 自身有发布理由再带入 PyPI，
  不为文档单独改 runtime 源码或版本。托管采用引导页是否同步须核对部署状态；不为文案发 Core/MCP。
- **Zenodo**：不轮换 webhook token；每次发版后验证 concept DOI 指向新 record，核对版本与日期；
  不打印带 token 的 hook 配置。

## 增强路线复核（2026-10-12 · 实施前 gate）

- 离线应用交付优先；不新增项目规模门槛；每轮先验证已有能力、修缺陷再扩面。
- 工具型 Agent 还原实验自 **10-12 暂停**，不自动恢复；现有 key-exposure 证据足以支撑决策，
  不因「抗 AI」增加 Community AST 变换。已完成项见 [TODO 历史](TODO_HISTORY_2026-11-16.md)。
- 资源 embed-data／vault 接应用 key provider、L3 方法／嵌套覆盖等待真实阻塞与 T4 门槛；
  descriptor、classmethod/staticmethod、装饰器顺序、`super()`、闭包/nonlocal、继承/override、
  异常映射与覆盖跳过原因先定义；资源契约不直接照搬 L3 provider。
- 跨文件 L3 继续拒绝 free-threaded；3.15t 必须用真实解释器，在 cryptography/cffi 导入后记录
  GIL 状态，验证 provider 并发和异常恢复；普通 3.15 通过不能替代。
- **参数改名（10-18 暂缓）**：无用户需求不实施；有触发后再确认范围，可先做 mapping 读取端。
  `CROSSFILE_PARAMETER_RENAMING_DESIGN.md` 的五步拆分与默认关闭不变。
- **H B2/B3、复杂 import 环、`__init__` 带体类／执行默认参数**：等真实最小复现再定范围，
  保持保守拒绝与提示；canary 模块属性用例等 N-1 也支持后再加。
- **mapping 自动选择**：等用户提出多版本调试需求；现有 marker id 与不匹配告警先用。
- **剩余打包组合**：macOS、Python 3.15、整包 Cython、L3 冻结组合按真实交付目标逐项选择，
  不默认全做；Windows Nuitka 已有单格 partial，不再从零列待做；干净目标机与更广矩阵不作已验证。
  复杂私有下游 Y-1 仍需专项验证，基础 Windows 合同不能替代；只登记去标识工程证据。
- **CLI `--check` 默认联网**：10-11 决定先保持，MCP 默认不查；是否默认离线可复审。
  若改须发版并记 CHANGELOG，否则维持 `NETWORK_BEHAVIOR.md` 说明。
- `preserved.*` reason codes 与 Y-3 vault 覆盖等真实下游触发；DCO `LE-01.01` 等外部协作者；
  OSPS L3 SCA/SAST 阈值政策仍待定，不能把已完成 SBOM 当成全部 L3 已完成。

## 分发与需求验证

- 小型渠道试验：选择合规线程／社区并核对账号条件；不用下载尖峰证明增长。
- GEO 补测：维护者回常住地后补 Gemini 环境与 Perplexity B1–B3，条件见私有
  `docs/internal/geo-observations/2026-10-07-baseline.md`。
- mcp.so 过时「50% cheaper than PyArmor」描述由维护者核对能否修改；Discussions 置顶 Show and tell
  表单仍待维护者发（10-11 之后）。不为冷清社区多发公告，等真实外部问题再投入。
- 多工具交付 benchmark、扩展 LLM 实验与期刊论文：10-07 定 **60–90 天后再议**，依赖真实应用数据；
  E 页并入卖前指南 FAQ，不单建。验收看可复跑、主张一致、采用可核验，不看 star 或 AI 首推率。
- **AlternativeTo**：维护者验证账号后提交；免费审核官方口径至少数月，$5 priority review 是
  单独付费 gate，默认不买。MCP Trust Registry 发布仍待维护者账号/token（见维护者清单）。
- **awesome-python #3352**：不争辩、不重开；非发布日基线明显抬升才再议；awesome-security／
  awesome-devsecops 等同条件再评估。某渠道有可归因安装前不新增渠道。
- stdio MCP 先准备 MCPB；Smithery 已退役，不再评估投递；Product Hunt 等真实用户信号。
  `pyobfus-review` skill 等实际使用反馈再考虑投递，不为上架而上架。
- **视频原创保护独立工具（10-23）**：只授权记录；先验证外部创作者需求、平台权益，再定原型。
  母版／发布记录、水印、疑似搬运比对、人工审核材料见 [调研](VIDEO_ORIGINALITY_PROTECTION_RESEARCH_2026-10-23.md)；
  不承诺副本自动失效，不改变本队列。仓库／许可／收费未定，未授权实现、采购或发布。

## Affiliate pilot（未授权实现／部署）

- [方案与验收](AFFILIATE_PROGRAM_DESIGN.md)仍为 `DRAFT — NOT IN EFFECT`，不开放、不实现，
  不能当报名页或付款承诺；必须维护者明确批准上线及最终条款／会计税务确认。
- 上线前依次补 event + Checkout Session 双幂等、paid/async fulfillment、退款／拒付回冲、
  隐私安全日志、commission 状态机和测试、KV 备份／恢复识别新记录、Privacy Policy。
- 首批只邀 **3–5 人**，**20% / 30 天 / 月结 / $50 门槛**；无 cookie、portal、Connect 或第三方 SaaS。
  只有真实活跃 affiliate 与人工工作量满足方案门槛后才升级；**三个月无可归因成交就停止**。
  不发 Core；Worker 生产部署和 Stripe 配置另需批准。

## 内容节奏与待选题

- DEV 英文每两周一篇，维护者发布，草稿经 tech-deai 并注明 AI 辅助；WP 中文每月一篇且中文首发，
  维护者跑 findata `~/projects/findata/content/publish.py`，自动推 Discord，再考虑知乎人工改写并附原文链接（09-27 只选定渠道，未开动）。
- DEV 个人资料链接 GitHub、X 简介标注 pyobfus maintainer 的旧清单项仍须核状态，
  不据 09-28～10-11 的旧排期认定完成。
- Reddit 只在有月度版本时发 showcase 更新；X 随 DEV 分享；HN 最多一次普通链接投最强事故复盘，
  维护者本人写标题与评论，先看 DEV 反响／流量与账号条件；Show HN 已用过。
  V2EX 等邀请码；Stack Overflow 按 04-22 决定在 **Q4 再评估**；微博不发 pyobfus。
- 旧排期不表示已发布：**11-02～06** 的 r/Python／WP 中文第 4 篇（1+2 合并）／知乎，
  **11-10 / 11-24** DEV 第 4、7 篇仍须核状态；不补造完成记录。
- 未发布选题：打包前混淆（PyInstaller/Nuitka cookbook，回应编译后改名无意义的误解）；
  诚实对比（含 Opy／python-minifier）；AI 还原基准（仅 5 样本）；混淆后 AI 排障（真实 mapping／
  marker／unmap／MCP／VS Code 命令，只讲自有代码，不写空泛「专为 AI 优化」）。
  第 7 篇先于第 5 篇；**12 月第 5、3 篇 + WP 月度篇，第 6 篇顺延 1 月**，
  第 6 篇的发版频率复盘须使用 10-25 数据。webhook 题材默认不写，等维护者决定。
- 草稿只放 gitignored `docs/internal/content-*/`，不进公开 `_drafts/`；自然备份检查包含性。
  发布后可选记真实 URL、日期与 +24h/+7d/+30d，原稿仍可私有。
- 每周看 GitHub 来源与每篇 DEV 作者后台阅读数；**14 天内 dev.to/reddit ≥10 独立访客**，
  或 star／安静日中位数上移算有效。**前 4 篇 DEV 每篇 <100 且从未出现 dev.to 来源**则停定期发；
  **X 满 3 条无来源就停；HN 投后 24 小时无外部评论就收掉**。
- 落地页可按需加截图／用例，但不建第二文档站，文档归 Read the Docs。

## 周期性

- **每周一只读巡检**：CI／Dependabot 大版本、最新 Core/MCP 反馈与客户调研、收件箱及目录解锁、
  下载安静日／异常、Marketplace installs、trial 登记、GitHub 来源、Action 归因、Dogfood、
  KV 备份新鲜度和自然备份包含性。所有客户、付款、支持与 trial 明细仅进私有记录。
- `scripts/download_snapshot.py` 为统一可复跑口径；发版日、次日、内容流量分开读，
  下载不作发版 gate。正常每月留一份摘要，发版／内容／异常才加检查点，不保存完整 stdout 或另建 CSV/JSON；
  runtime 逐日、Open VSX 累计和长期不变 Action 0 只在变化时写。
- **查进度固定动作（09-25 定）**：除仓库状态，同时给下载脚本结果与收件箱有无待回复；
  公开结论去标识，邮件及原始明细私有。
- **每月月底四项复盘（08-08 定）**：下载趋势、排障、竞品重扫、已有设计；决定下月自然工作与发布候选，
  不恢复静默四周／月度发版窗口。竞品细查由新对手、生态政策或临近发布触发，不无故盯梢。
- Dogfood 观察满 **4 周且无 flaky**，才另行 reviewed 决定是否升 PR gate；不自动升级。
- 下一次自然备份覆盖 **11-11** 新增巡检、接续审阅、轮换草案与回归日志及其后新增私有记录；
  整体 WSL 每日备份是否静态加密属跨项目策略，不能由本项目顺手定。
- Alipay 文案只在平台真正 Enabled 后再恢复，可向支持询问；不因等待而预写已支持。
- Action 归因用 GitHub 代码搜索 `uses: zhurong2020/pyobfus-action`，量的是可见性，不等于采用量。
- **搜索周检（11-07 起）**：GSC 两个站点资源看 sitemap、收录／未收录原因与近 28 天效果；
  Bing 分站看 Sitemaps、IndexNow 与 AI Performance。Pages／IndexNow workflow 返回码 200/202 正常，
  403/422 查 key；保留 `docs/google03878b382b498ff9.html` 和 IndexNow key 文件。
- **搜索后台跟进**：11-16 已核 GSC 规范 `/pyobfus/zh-cn/` 已收录；GSC sitemap 仍显示 11-12 旧的「无法读取」，
  不删除重提，周检复看是否自行刷新。Bing IndexNow 后台未展示记录但 workflow 成功，不能写成零提交或失败，
  继续观察后台是否补齐。详情见 [11-16 执行进度](EXECUTION_PROGRESS_2026-11-16.md)；只读浏览器步骤在
  `~/projects/workspace-meta/archives/SEARCH_CONSOLE_SETUP_GUIDE_2026-11-07.md` 第 5 步。
- **月度搜索／AI（每月第一周，下次 2026-12 第一周）**：WebSearch 12 题 + Codex（隔离
  `CODEX_HOME`、中性目录）+ Codebuddy `hy4free` / `deepseek-v4-pro` / `kimi-k3.1-pro`，
  Bing AI Performance；方法见私有 `docs/internal/geo-observations/2026-11-07-baseline.md`。
  同时复核 ChatGPT 联网 #1/#3/#8/#10 与行号还原 #4/#11，保留可比口径。

## 已研究、明确延后／不做

- MCP Resources／Prompts 拆分等真实 MCP 用户反馈；`dependency_advisory` 独立工具倾向不拆，
  除非有明确差异点；`--output-pyc` 只做 spike，不承诺产品化。
- 不实现 hosted／remote MCP 或 streamable-HTTP；stdio 协议协商由兼容 SDK 提供，不与传输混为一谈。
- 不追原生 VM/VMC/BCC、新编译器后端、云混淆／商城／自动更新／托管下载、anti-VM／AV bypass／
  强 anti-debug 竞赛；不提高 AI 自动生成 transformer 的优先级。
- 不在对手页求收录、不买对比位、不写夸大排名文案；不导入已删 `docs/_config.yml` 的旧部署项目。
- 不为抢 GitHub 用户名注册商标；**品牌防护商标仍待决定**，与抢用户名分开，先评估中国第 9 类，
  再评估美国；法律背景留历史，不据旧价格作当前承诺。
