# TODO

排期中的任务清单。**当前计划与状态仍以
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 为准**；本文件只回答「接下来按什么
顺序做」，不记录历史。依据与实测证据见
[`FEATURE_EXPANSION_RESEARCH_2026-09-12.md`](FEATURE_EXPANSION_RESEARCH_2026-09-12.md)。

最后更新：2026-10-15。Core 0.7.3（缺陷 C #100、M #101）/ MCP 0.3.13 已发布（0.7.2 为缺陷 I），runtime 0.1.1 保持不变；Core/MCP Unreleased 均为空。发布前完整 CI 与本地四测试根通过，PyPI 发布包和 PEP 740 已独立验证，Registry 与 Zenodo/CFF 已同步。私有历史库 CI 已定性，Glama 502 已恢复；Glama 安装/握手/9 工具测试、渠道记录与源码 pin（`22ecd62`）均已完成。

## 状态口径

- **实现**与**发布**是两道各自独立的 gate，都需要用户明确批准。
- 任何一项做完后，把它从本文件移除，并在 `CURRENT_PLAN_ZH.md` 记状态；
  不要在这里留「✅ 已完成」的历史层。
- **下游反馈归属（2026-09-17）**：pyobfus 是本工作区自行维护的公共 PyPI 工具。
  CAC Plus 或其他项目暴露的通用混淆缺口、最小复现和回归证据，必须同步登记在本仓库
  （公开 TODO 使用去标识描述，敏感交付背景只进入本地 internal 记录），不能只留在下游文档。
  下游是否选择混淆自己的代码由其分发边界决定；公开第三方依赖不因被打包而自动成为
  pyobfus 的处理目标。

## 后续任务顺序（2026-10-17 更新）

缺陷 I 随 Core 0.7.2 发布（PR #99），缺陷 C/M 随 0.7.3 发布（PR #100/#101），D 由 0.7.2 修好；Glama 源码 pin 已收尾，10-17 Build steps 已改装 Core 0.7.3 并测试通过。

| 顺序 | 待办 | 验收 / 下一步 |
|---|---|---|
| 1 | **私有下游候选 Windows 闸门（维护者）** | **10-18 维护者定：暂停，等现场答复能否从 Windows 7 升级到 Windows 10**（不能升级则先做下游向下兼容改造，闸门随之重排）。10-15 已用 0.7.3 重建候选 `2.6.2-20261015-e7e96fb`（`build/release-v2.6.2-cand4`，取代 0.7.2 的 cand3）：SHA256、名字检查 59/63（4 处星号转发：3 处外部 wheel，`nifti_loader` 为项目内转发但被转发模块导出不可静态确定→保守保留）、交付检查 0 发现。剩：发布机授权续签 → 装机评分、M2 升级、生命周期、向导目视。 |
| 2 | **10-19 周一巡检** | 下载安静日（0.7.2 发布日与次日不计）、客户反馈/调研回答、微信付款跟进线程（`/pyobfus-inbox`）、Stripe Alipay 审批状态、CI、许可证监控、KV 备份、Anthropic 插件解锁消息；仅留决策摘要。 |
| 3 | **10-25 复盘** | 区分发布/次日/内容流量，综合下载、trial、客户回答和 DEV 来源，决定下轮优先级与发布节奏；评估一周两笔微信付款未完成是否需要更多动作（Alipay、弃单提醒需 Stripe restricted key）。 |

10-18 维护者批准两项代码任务（14:05 后交 Codex、Claude 审，顺序：缺陷 N → H PR 4 选项 1；发版另批）；参数改名暂缓；Pro 扩展等真实需求信号，详见各条目。本次没有授权额外部署或客户邮件发送。

## 发布后观察与下次发版

- 每周一巡检继续观察 Core 0.7.3 / MCP 0.3.13 反馈、下载安静日、客户调研回答、CI 与备份。无新缺陷时不重复全量测试、不主动增加功能。
- **10-25 复盘**照原计划；发布日、次日与内容投放流量分开记录，据客户回答调整后续优先级。
- 下次发布按实际新增改动与维护者授权确定，不恢复此前 10-15 的等待通知状态。
- runtime 源码若有改动必须先升版本、先发 runtime（`scripts/check_runtime_version.py`）；改版本号后先刷新 editable 元数据，再按发布清单验证。
- VS Code schema 随插件下次发版，不因本次 Core/MCP 发布自动发插件。

## 增强路线复核（2026-10-12 · 实施前 gate）

复核已完成（[报告](AI_ERA_PROTECTION_ROADMAP_REVIEW_CLAUDE_2026-10-12.md)），维护者确认按修订执行；修订后的范围与顺序见路线图 §13。

- 随 0.7.0 已发布：PR #93、#94。
- [x] 离线交付指南：`docs/guides/ship-python-offline.md`（已上导航；staging 命令实跑过）。
- [x] Agent 实验协议（`docs/LLM_RESISTANCE_BENCHMARK.md`「Round 2 protocol」）+ 确定性脚本 `benchmarks/llm_resistance/key_exposure.py`（进 CI）。
- [x] 静态探针（10-12，只用订阅，48 次调用）：C0 6/6、**C1 社区版 6/6 被还原**、C4/C4b 0/6（两模型一致）→ 不为「抗 AI」新增社区 AST 变换。见 `docs/LLM_RESISTANCE_STATIC_PROBE_2026-10-12.md`。
- 可运行档（带工具的 Agent 还原）：**暂停**（10-12）。已完成两个订阅 CLI 的沙箱实测：Codex 用户配置开着 `network_access = true`，需 `--ignore-user-config` 并排除 `/tmp` 才断网、禁止工作区外写入；Claude Code 用 `--settings` 开 sandbox 后联网被拒、工作区外只读。后续实现在会话中被安全分类器拦下，未继续。路线图需要的结论已由不用模型的 `key_exposure.py` 给出（密钥在包内可直接解密；应用提供密钥时运行者可见字节码），暂停不影响决策。
- [x] 覆盖报告第一步 PR #95 已随 Core 0.7.1 发布（opacity 规则命中方法/嵌套函数时警告，build report 记计数）。
- [x] 交付检查 `--check-delivery`（PR #96，社区版，Core 0.7.1 已发布）：mapping／私钥／原文混入为 high（exit 1），构建报告外的 .py、Pro 选项被跳过为 medium；7 个真实 wheel 与 2.8 万文件 site-packages 零误报。MCP 工具 `check_delivery` 已随 MCP 0.3.13 发布（工具数 9）。后续候选：`.pyc` 是否由原文编译的判定、PyInstaller/Nuitka 冻结包解析（等需求）。
- 待需求信号：「fusion × 目录构建」设计（多模块离线应用拿到 Pro 保护的前提）、embed-data／vault 接 key provider、L3 覆盖方法。
- 已认可方向不变：离线应用交付优先；不新增项目规模门槛；路线图每轮先检验现有功能、修缺陷，再扩展。

## 维护者动作清单（2026-09-22 收尾 · Claude 做不了、只等你）

按顺手程度排，每项的细节都在本文件后面对应小节或所指文件里，这里只是一处能勾掉的总表。


- [ ] **Claude plugin — 已由真人支持升级到内部，等待后端解除锁**（2026-09-28 更新）：Console 重提被拒
      「Another submission already holds this repository and path」，但两个工作区 submissions 页都 `No submissions yet`。
      2026-08-02 旧提交没消失，而是留了个自己撤不掉的**孤儿仓库锁**。**别再反复点提交表单**（同一个锁挡）；
      走 contact the directory team 请求释放锁,说明:表单报错原文 + 两工作区皆空 + 旧提交约 2026-08-02 +
      账号 `zhurong0525@gmail.com`。**2026-09-24 升级邮件已发**(`support@anthropic.com`);**2026-09-25 Fin AI
      自动回信称只懂 Claude Code worktree 锁、需真人释放提交锁并主动提出转人工,维护者已回「yes」转人工**。
      09-25 真人支持 Rudy 回信要求核对原提交账号；维护者已查三个常用邮箱均无确认邮件，随后以同一仓库根路径
      复现锁报错，并于 09-26 在原线程附上「No submissions yet」与 repository/path lock 两张截图，提供
      Claude Code workspace ID，请求后端定位/释放。**09-28 Rudy 回信「已升级内部，有消息再跟进」——球在对方，不必再催；锁没释放前别再点表单或换路径绕过**。**10-14 Tiffany 确认：原提交归属当前账号，无需补材料或寻找别的账号；目录团队解除锁后，使用 `claude.ai/directory/manage` developer portal 重提，Console 表单已停用。继续等待，不换仓库/路径重提。**。字段/描述与证据见
      `docs/internal/CLAUDE_PLUGIN_RESUBMISSION_2026-09-22.md`。
- [x] **通知 Pro 客户升级到 0.6.1**（10-10 维护者定：发；草稿私有 `docs/internal/content-2026-10/pro_customer_notice_0.6.1.md`，10-10 已按线上许可证记录建 5 封 Gmail 草稿（每人一封、排除维护者自用许可证；未激活的那位多一句协助激活），维护者 10-10 12:35 已逐封发出（Gmail「已发送」核实 5 封、草稿箱清空）；有回信按 `/pyobfus-inbox` 跟进；取代原「是否通知升级到 0.5.32」，0.6.1 已含该修复）。原登记（2026-10-07）：0.5.10–0.5.31 的目录构建遇到同模块
      装饰器/基类/lambda 会 import 时 NameError。两位 10 月新客户如用过目录构建可能受影响；需要的话由 Claude 起草、
      维护者审后发送，AI 代理不直接发信。
- [ ] **MCP Trust Registry publish**：在其站点注册拿 API token 后
      `MCPTRUSTCHECKER_TOKEN=… npx --yes mcptrustchecker@1.14.0 publish pyobfus-mcp --registry pypi --online --category developer-tools`
      （wheel 已扫 A · 94/100，09-23 已用 CLI help 核对参数；不要把 token 写进 shell history、仓库或聊天）。
- [ ] **下一笔真实 Pro 购买后核验新发号流程**（2026-10-05 登记，事件触发，由 AI 代理做）。Worker 10-05 起
      只对已付款发号、序列号由 session 派生，这条路径未用真付款跑过。下次 Stripe 有成功付款时：只读 KV 确认
      新记录的 `stripe_session_id` 与付款一致、key 格式 `PYOB-XXXX-XXXX-XXXX-XXXX`、只有一条；Stripe
      Workbench → Event destinations 该次投递为 200；问买家或看 Gmail 确认许可邮件送达。任何一项不符先停下排查，
      不要在 Dashboard 手工重放事件（Stripe 本身会按退避自动重投）。
- [ ] **10-11 会话遗留的维护者小事**（2026-10-11 收尾登记）：
      ① ChatGPT 账号个性化：AI 回答基线测试时关闭了，测完可按需恢复（恢复后自己看到的推荐不可信，复测前再关）；
      ② Anthropic 目录支持（Tiffany 10-11 来信「仍在处理」）：可选致谢回信，草稿在 10-11 会话，未发；插件提交的是仓库+manifest 路径，
      会按最新 GitHub 代码安装，**无需更新提交内容**；
      ③ `--check` 仍默认联网（CLI，MCP 默认关）——10-11 定「等 Codex 这波完成后再审」，现可决定是否改默认离线；
      ⑤ 约 10-14 看 DEV 第 1 篇反响与 GitHub 流量来源，再决定是否投 HN（Show HN 已用过，只能普通投稿）。
- [ ] **0.6.1 通知的回信**（10-10 发出 5 封，身份记在私有 memory）：随每周一巡检看 Gmail。10-11 KV 实读：
      09-12 报障客户已于 10-05 联网激活成功（原「未激活」跟进结案）；另有一位 8 月客户至今从未联网激活、
      一位 6 月客户当前无设备记录，二人均未来信——回信若报激活问题按 `LICENSE_ACTIVATION_GUIDE.md` 排障，
      不再主动追发第二封。
- [ ] **Payment Link 开票设置**（2026-10-05 登记，维护者 + API，不急）。链接 `plink_1SSnVd1BxxEBSJisxqFMUKeA`
      由 API 创建，Dashboard 不能编辑。开 `customer_creation=always`（免费，根治访客结账没有 Customer、事后
      开票对不上）或 `invoice_creation`（每笔自动发票，可能另收 Invoicing 费，开前看说明）只能走 API；需先在
      Dashboard 建只含 Payment Links 写权限的 restricted key 并存进 Vaultwarden。开票需求 10 个月 1 次，
      等下一次真有人要发票时再做也可以。
- [ ] **开启任何延迟到账付款方式前的检查**（规则，长期有效）：Worker 与 webhook 订阅已支持
      `checkout.session.async_payment_succeeded`，但开 ACH / SEPA / 银行转账等之前先确认 endpoint 仍订阅该事件，
      开后的第一笔按上面「核验新发号流程」走一遍。Stripe 付款方式是账户级配置，会按它动态展示。
- [ ] **维护者手动删除 OneDrive 两个旧副本**：`…/3-job/program/` 下 `pyobfus-action/` 与
      `pyobfus-backup-pre-filter-repo-20260503-2231/`，都带 `MOVED_TO_WSL_20260921.md`、WSL 均有副本
      （`~/projects/` 同名目录）。09-22 只删了 pyobfus 与 pyobfus-legal 两个批过的；这两个不在清单里，未动。
      **09-23 已完成删除前核验**：排除 `.git`、`.mypy_cache`、`.ruff_cache` 与迁移标记后，
      对两组执行 checksum `rsync -rcni --delete` 均为零输出。维护者已决定自行删除，AI
      代理不执行该云同步删除；删完只需回报以便勾掉。此后 Core/MCP/runtime/Action 的本地
      开发、测试、构建与发版准备全部只在 `~/projects/` 的 WSL 工作副本进行，
      OneDrive 仅作迁移残留或备份，不在其中编辑或执行。

## 本轮已完成的去处

不在这里留历史层。2026-09-12 完成的六项（0.5.25 的三项修复、mcp 2.x 兼容与
CI job、只读 review skill、浏览器端对比小节、抗 AI 措辞改写、支持矩阵）记在
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 的「09-12 发布后续」段。

2026-09-19 完成的三项（CycloneDX 1.7 对齐、`examples/` 第一批进 CI 实跑、测试
fixture 漏临时目录）记在同一文件的「09-19」段。其中只有 CycloneDX 那项改了
`pyobfus/` 代码，因此 held 在 `CHANGELOG.md` 的 `[Unreleased]`，要发版才到用户手里。

## 节奏（2026-09-25 用户定 · 0.5.30 发版后生效，先当一次测试）

**背景**：09-12 定的「靠持续发版与更新吸流量」跑了三周：9 月 10 次 Core 发版、最长间隔
4 天；发布日 120–225、非发布日中位数 31、地板 16–32 始终没动。发版只买到当天尖峰。
而且间隔从没超过 4 天，「非发布日基线」这个核心指标从来没有过干净的观测窗口，
awesome-python 要的 adoption trajectory 也因此拿不出来。09-25 用户同意改为下面这套，
0.5.30 发出后开始，10-25 复盘。

**2026-10-07 状态**：静默期按例外提前结束——0.5.31（目录构建不删 docstring）与 0.5.32（目录构建
装饰器/基类/lambda NameError，0.5.10 起）均属「影响用户的 bug」，维护者当日批准。唯一干净的观测窗口是
09-27→10-06（近 7 天安静日中位数 40），10-25 复盘按此给初步结论；10-07 发版尖峰与 10-13 起的内容投放分开记录。
之后照常：每月第一周一版、只做有触发的事、每周一巡检。

**发版**
1. `0.5.30`（Y-2 + Y-3）已于 09-26/27 发布，是这一波功能驱动发版的收尾。
2. 之后**静默 4 周，10-25 前不发 Core**。例外只有三种：影响用户的 bug、安全修复、
   付费客户或真实下游明确要的东西。目的是拿到第一份干净的基线读数，按周看安静日。
3. 静默期后**每月一个小版本**，落在每月第一周，装那个月 `[Unreleased]` 攒下的东西；
   攒不满就跳过那个月，补丁版只为 bug。
4. MCP / VS Code / runtime 各自只在有影响该渠道用户的改动时才发。MCP 2.x 兼容继续攒。
5. 发版清单不变：README 横幅同提交、全路径 lint、Zenodo 核验（`CLAUDE.md`「发布流程」）。

**开发**
1. **只做有触发的事**：下游真实需求、用户 issue、安全通告、依赖大版本、竞品变化动摇了
   文档里的某个断言。「已研究、明确延后」表的解冻条件就是标准。
2. **每周一固定巡检，不写代码**：`python scripts/download_snapshot.py`（三个 PyPI 包安静日
   中位数 + Marketplace installs + Open VSX + Action 归因）、trial 登记数（`check_backup.sh`
   3b 节）、客户来信（`/pyobfus-inbox`）、plugin 解锁邮件、Stripe Alipay、CI 与 Dependabot
   大版本、Dogfood workflow 结果、KV 备份新鲜度。结果在 `CURRENT_PLAN_ZH.md` 记一行决策摘要；
   不保存完整 stdout，也不另建 CSV/JSON 快照。静默期保留 Core/MCP 安静日中位数、Marketplace
   installs、trial、GitHub 流量/来源与结论；runtime 逐日数、Open VSX 累计抓取数和长期不变的
   Action `0` 只在异常或变化时写。10-25 复盘后改为每月留一份摘要，发版、内容投放或异常峰值
   才增加临时检查点。`scripts/download_snapshot.py` 继续作为统一、可复跑的统计口径。
3. **每月月底四件事复盘**（下载趋势 / 问题排查 / 竞品重扫 / 已有设计复盘，08-08 定），
   结论决定下月第一周发不发版、发什么。
4. dogfood 观察满 4 周且无 flaky 失败，再决定是否升 PR gate。
5. 静默期腾出的时间优先给只有维护者能做的渠道动作（AlternativeTo / MCP Trust Registry /
   plugin 重提）；某个渠道出现可归因安装之前不再新增渠道。
6. Y-3 vault 覆盖、`preserved.*` reason codes 等「后续」项，等下游真的碰到再做。

**测试判定（10-25 复盘看三样）**：4 周安静日中位数是否明显高于 9 月的 31；trial 登记是否
从 0 起步；客户来信 / issue 是否出现。三样都没动，说明节奏不是变量，下一步该换的是渠道
或产品定位，不是再把发版调快。

**查进度的固定动作（2026-09-25 用户定）**：每次用户让查看项目进度，除仓库状态外**一并**给出
(a) 下载量：`scripts/download_snapshot.py` 的输出，发布日与安静日分开读；(b) Gmail：按
`/pyobfus-inbox` 的查法报有没有相关邮件、谁在等回复。

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
| **P1 · gate** | **Affiliate 邀请制 pilot**：方案与未生效条款草案已完成；当前不开放、不实现。若维护者明确批准上线，必须依次完成 Stripe event + Checkout Session 双幂等、paid/async fulfillment、退款/拒付回冲、隐私安全日志、commission 状态机与测试、KV 备份/恢复识别新记录、Privacy Policy + 最终条款 + 会计税务确认；只先邀 3–5 人，20% / 30 天 / 月结 / $50 门槛，无 cookie。验收与停止条件见 `AFFILIATE_PROGRAM_DESIGN.md` | **不发 Core**；需 Worker 部署和 Stripe 配置 | AI 实现 + 维护者批准/财税确认 |
| ~~P0~~ ✅ | 可验证性主线**完成**：对标文档 `SUPPLY_CHAIN_ASSURANCE.md` + 稳定 reason code（`reason_codes.py` v1，plan/report 发射，`REASON_CODES.md`）+ CycloneDX 1.7，全部**随 0.5.28 发布** | — | — |
| ~~P1~~ ✅ | OSPS 补齐**基本完成 2026-09-20**：4 开关（gh api 核实）+ 4 文档（f2cd713）全做完。残余 = `LE-01.01` DCO（主动延后）+ 若干 L3 | 免发版 | — |
| ~~P1~~ ✅ | 抗 AI 措辞改写**完成 2026-09-22**（tech-deai）：README / `landing/index.html` / `docs/index.md` 散文里的 em-dash 全部清零（README 48 处）、20 条 bold-colon 功能列表改成带动词的句子；命令、路径、版本号、链接、What's new 横幅与 UI 标签（如 `Unlock Pro`）原样。H2 骨架未动（doc-hub 型 README，锚点被外部引用）。~~pyarmor VMC/ECC 补记~~——已确认无需改 | 免发版（README 到 PyPI 要等下次发版） | — |
| ~~P0~~ ✅ | **KV 每日备份适配 trial 记录 + 补跑机制**（用户 2026-09-25 列为 P0，当日完成）：`~/scripts/pyobfus_kv_export.sh` 此前只认 license 记录，第一条 `trial:*` 登记会让整轮导出拒绝落盘、许可备份静默停止（上线 5 天 KV 尚无 trial 记录，未实际发生）。已改为按 key 类型校验（`PYOB-*` 查 license_key / `trial:*` 查 email_hash+v / 未知类型只查可解析并 WARN）+ `:`→`__` Windows 安全文件名 + `--selftest` 14 项；调度从 crontab 01:30 挪进 `wsl_daily_backup.sh` 开头（systemd `Persistent` 开机补跑，cron 不补跑致 09-24/25 漏导，已补、与 09-22 逐字节一致）；`check_backup.sh` 加 KV 一节。脚本都在 `~/scripts/`（仓库外，随日备份进 OneDrive），仓内只记状态 | 免发版（仓库外脚本） | — |
| **P2** | 分发上架队列：awesome-python PR #3352 **2026-09-24 被拒**（理由=采用量，对方留了「adoption grows」再议的门；不争辩、不重开）；awesome-security / awesome-devsecops 门槛同为下载量，**跳过**；队列下一项 **AlternativeTo**（需维护者账号） | 免发版 | 维护者 |

### P0 · 目录构建的改名深度（2026-10-07 发现 · 第 1 步与缺陷 A/B/E 已随 0.6.0 发布，10-08；缺陷 G、F 已随 0.6.1 发布，10-10）

**现状**：目录（cross-file）构建改模块级名字和函数局部变量并同步 import；参数、方法名、属性保留原名。单文件模式改得更深
（含方法与参数），但保留函数内定义的函数/类名和类体注解字段名。0.6.0 的内容与审核记录见 `CURRENT_PLAN_ZH.md` 10-08 段。

**分工（10-07 维护者定）**：Codex 实现，Claude 审核，维护者批准合并；发版另需批准。

- [x] **既有缺陷 G · 目录构建的别名导入（优先，0.5.28 已存在——10-13 下游构建实证，早于原记的 0.5.32；影响用户）**：`from pkg import scale as action` 或
      `from pkg.core import scale as action` 后调用 `action(...)` 即 NameError（局部改名开关无关）。参数改名设计审核中发现；
      应先于参数改名的解析器工作修复。**10-10 已合并 PR #66（`b56afe2`），随 0.6.1 发布**（保留显式本地别名，仅同步被导入符号名）；审核记录私有 `docs/internal/geo-2026-10/PR66_REVIEW_2026-10-10.md`。
- [x] **既有缺陷 I · 函数内别名覆盖模块级导入**（10-10 审 #66 发现）：模块级 `from pkg.core import helper` + 函数内
      `from pkg.core import scale as helper` → NameError（扁平 `import_mappings` 被函数内导入覆盖）。**10-14 合并 PR #99（`2cabc06`），随 0.7.2 发布**：
      导入引用按 Python 词法作用域解析（定义时表达式、闭包、global/nonlocal、类体、推导式、PEP 695、except/match 绑定名），无法识别的编译器作用域按模块保守回退并提示。
      四轮：Codex 实现 → Claude 审出 3 个退步并修（Codex 429）→ 独立审核 F1–F4 由 Codex 修 → Codex 合并 main、修 Windows 换行断言。142 个对抗样例在 3.12/3.13/3.14 无一比 main 差。
      已知仍存（与 main 相同）：限制 H 拒绝时 `--check` 提示、星号导入、`globals()['x']` 字符串查找。
- [x] **既有缺陷 F · 单文件模式默认改参数但不改关键字调用（优先，0.5.32 已存在）**：同文件 `scale(1, factor=3)` 即 TypeError；
      含 `/`、`*args`、`**kwargs` 的签名还会静默绑错（关键字落进 `**kwargs`、参数取默认值）。无预设、safe、balanced、aggressive
      在 0.5.32 / 0.6.0 都是 `preserve_param_names=False`（框架预设与 library 为 True）。**10-10 已合并 PR #67（`ed8cceb`），随 0.6.1 发布**；审核记录私有 `docs/internal/geo-2026-10/PR67_REVIEW_2026-10-10.md`：
      按 10-10 已合并设计 PR #65 的维护者决定实现默认保留参数名；显式 false 照旧生效但警告，`--init` 模板改为 true，
      `--check` 加 medium 语法候选风险提示，目录 cross-file 参数保留行为不变。证据私有 `docs/internal/geo-2026-10/param-default-evidence/`。
- [x] **既有限制 H · 通过模块对象访问属性**（10-08 交叉审核发现，0.5.32 已存在）：目录构建里 `from pkg import core` 后
      `core.LIMIT`（或 `import pkg.core as engine; engine.scale()`）时属性名没跟着改 → AttributeError。
      **10-11 全部完成，随 Core 0.7.0 于 10-12 发布**：提示与文档 #80 → 设计 #82（方案 A，维护者按 Claude 建议拍板）→ 实现 #83（from/别名，opt-in）
      → #84（dotted、相对导入、包 re-export、escape 提示）→ **#85 默认开启**（`3759000`；补「无法证明」提示，
      保证产物里未改写且目标被改名的访问都有提示；导入前有 `sys.path`/`logging` 等语句时函数体访问也能改写；
      `globals()`/`setattr(sys.modules[__name__], …)`/`exec` 等动态改写本模块命名空间时整体拒绝）。
      退路 `--no-crossfile-module-attributes` 与 main 旧默认产物逐字节一致。发版说明须写「升级后完整重新构建、重新生成 mapping」。
      私有验证：动机项目副本 127 处 `config.X` 全部改写、`--check` 无剩余提示。审核与提示词私有 `docs/internal/codex-2026-10/H_IMPL_PR*`。
      后续（不阻塞）：canary 在 N-1 也支持后可加模块属性用例；`__init__` 含带体类/执行默认参数、导入循环等仍拒绝并提示。
- [ ] **H PR 4 · 10-18 维护者定选项 1（批准实现，14:05 后交 Codex、Claude 审；发版另批）**：10-18 实测 0.7.3 自混淆构建无告警、运行即 AttributeError，三个独立阻断：
      B1 `module_attributes.py` 对任何 `x.modules[k] = v` 写入（不论是否 `sys`）把全项目标为不安全（`core/mapping.py` 一处即关掉 61 个模块）；
      B2 包 `__init__` 的 try/外部导入；B3 再导出子模块回导包内 `__version__` 的导入环。本 PR 只做：修 B1 误判、`--check` 写明拒绝原因、构建时提示未证明安全的属性访问数。
      选项 1 PR #103 待审，B2/B3 未做（等用户触发）。范围备忘与 Codex 提示词私有 `docs/internal/codex-2026-10/SCOPE_H4_PARAMS_2026-10-18.md`。原登记：包 `__init__` 里 `try: __version__ = version(...)` 会阻止整个包的子模块属性改写（pyobfus 自身可复现）；评估仅绑定与子模块名无关的语句能否安全放宽。需单独确认范围，不阻塞已发布版本。
- [x] **既有缺陷 C · 运行时注入的模块级名字** — **10-15 合并 PR #100（`bde110c`），随 0.7.3 发布**。
      Community correctness fix: automatically preserve static `enum.global_enum` members in single-file and directory builds;
      preserve module export spellings when module-level `__getattr__` prevents H proofs, and conservatively preserve non-static enum modules with a planning warning.
      Artifact regressions cover references, `__all__`, imports, module attributes, dynamic enums, exclude_names and standard-library `calendar` / `re`.
- [ ] **缺陷 N · 在 CPython 3.12.0–3.12.8 上构建，兼容 3.9 的 f-string 被改成同引号复用，产物在 3.9–3.11 上 SyntaxError**（10-18 复现，Community 正确性）：
      根因是这些补丁版的 `ast.unparse` 选引号不避开内层引号（3.12.9 / 3.13 已修；Ubuntu 24.04 自带 3.12.3，CI 用最新补丁版所以测不到）。
      最小复现 `python3.12 -c "import ast;print(ast.unparse(ast.parse('''f\"{f'{x}'}\"''')))"` → `f'{f'{x}'}'`。
      `generator.py` 的 `_fix_fstring_quotes` 只修 `['k']` 下标；`--verify-syntax` 只用构建解释器 compile，均兜不住。运行语义不变，只是语法层。
      建议：子类化 unparser，在 <3.12.9 时用 3.13 的引号选择；源码未用 PEP 701 专属写法时断言产物也不用（tokenize 检测）；测试与补丁版本无关；3.13+ 产物逐字节不变。10-18 维护者批准实现（含 `--check` 提示），14:05 后交 Codex、Claude 审；发版另批。
- [ ] **候选 · 3.12 嵌套 f-string 的 `--check` 提示**（低优先级，10-11 登记；可随缺陷 N 一起做：源码用了 PEP 701 专属写法时提示产物需 ≥3.12）：3.12 起允许 f-string 内复用同种引号/嵌套，
      产物在 3.9–3.11 上无法解析；目录/单文件构建若面向旧解释器分发，`--check` 可提示目标版本不兼容。先确认 `--verify-syntax`
      与 `target_python` 现有行为再定是否需要。
- [x] **新缺陷 M · 项目内星号转发后再从转发模块导入**（10-14 Claude 用 PyPI 0.7.2 复现）：`pkg/shim.py` 写 `from pkg.core import *`，`app.py` 写 `from pkg.shim import helper` → 产物 ImportError（开/关局部改名一样）。兼容转发模块常见；外部模块的星号导入不受影响（私有下游 4 处均转发外部 wheel 或显式列名）。**10-15 已合并 PR #101（`b6c06b2`），随 0.7.3 发布**。
- [x] **既有缺陷 D · `global` 重新绑定导入名** — fixed by 0.7.2 (PR #99).
      PR #100 adds artifact regressions for assignment and re-import after `global helper`, printing before and after rebinding,
      with local renaming and name verification both enabled and disabled.
- [ ] **第 2 步：参数改名 — 10-18 维护者定暂缓**（无实现、无用户需求；可能受益参数 pyobfus 自身约 18%、下游约 3%；有触发再议，届时可先做 mapping 读取端）：设计文档 `docs/CROSSFILE_PARAMETER_RENAMING_DESIGN.md`（PR #65，Codex 起草、Claude 审核通过）。
      分 5 个 PR：F 的方案 A → mapping 读取端与分析（观察模式）→ 同文件私有函数 → 跨文件 → 扩展；默认关闭。
      文末 6 个问题已于 10-10 由维护者拍板（PR #65）；后续实现范围仍需确认。Claude 的建议在私有 `docs/internal/geo-2026-10/PR65_REVIEW_2026-10-08.md`。
- 规则：本条属于「真实转换问题」，优先于下面所有推广项（GEO 计划 §16）。

### GEO / 外部采用（2026-10-07 登记 · 全部免发版）

依据是一份外部调研方案（私有输入，存 `docs/internal/geo-2026-10/`，不进公开仓库）。10-07 已完成的项（主张纠错、
JOSS 页改为引用页、两张任务页、Pages sitemap、FastAPI 真实应用 lane、Nuitka/Cython 实测、案例表单与政策页、
搜索基线）记在 `CURRENT_PLAN_ZH.md` 10-07 段。剩下：

- [ ] **README / RTD / Pages 首屏措辞检查**（2026-10-11 AI 基线发现，免发版；README 部分随下次发版到 PyPI）：
      ChatGPT 联网时把竞品 README 的原句直接当推荐理由（如「原生支持多模块项目」），而 pyobfus 在 12 个通用问题里
      一次也没进候选。检查三处首屏是否用直白句子写明：支持多文件项目、跨文件改写 import、输出仍是普通 `.py`、
      可用私有 mapping 还原 traceback；不夸大、不加竞品断言。改后在 11 月观测里对照。
- [ ] **Gemini 环境补跑 + Perplexity 补 B1–B3**（维护者回常住地后）：方法与条件见私有基线
      `docs/internal/geo-observations/2026-10-07-baseline.md` 末尾总结。
- [ ] **Search Console**（维护者账号）：验证 `https://zhurong2020.github.io/pyobfus/`（URL-prefix）并提交
      `/pyobfus/sitemap.xml`；RTD 的 sitemap 对脚本返回 Cloudflare 质询，在 GSC 里看抓取状态。域名根 `robots.txt`
      属个人站仓库，没有改。
- [ ] **mcp.so 列表文案过时**（「50% cheaper than PyArmor」）：维护者在 mcp.so 看能否更新描述。
- [ ] **Discussions 置顶一条**指向新的 Show and tell 表单（公开发帖，10-11 之后由维护者发）。
- 60–90 天后再定（P2）：多工具交付 benchmark、扩展 LLM 实验与期刊论文（都依赖上面的真实应用数据）；
  E 页（AI 写的应用交付）已并入卖前指南的 FAQ，不单独建页。

验收口径：完成标准是「用户能按页面跑通、公开主张与测试一致、外部采用可核验」，**不以 star 数或 AI 首推率
作为工程验收**。月度复查 12 个问题（下次 11 月第一周），与 `download_snapshot.py` 一起看。

### 2026-10-11 AI 回答基线衍生的改进（逐条对照仓库现状核实，只列确认的缺口）

依据：12 个通用问题 × Perplexity / ChatGPT 联网 / ChatGPT 不联网 + 3 个品牌问题的回答（明细在私有基线文件）。
已排除、无需做的：参数名默认保留与目录模式改名范围的文档（0.6.1 已同步）；卖前保护指南已覆盖授权、API key、
AI 代码、源码不上传（问题在**没被检索到**，不是缺内容）。

**代码（Community，要发版才到用户；按「只做有触发的事」排进 11 月第一周月度版本评估）**

- [ ] **P2 · `--no-cross-file` 目录构建支持 mapping**（需按文件区分名字表，`--unmap` 需按帧所在文件解析）。
      当前各文件独立改名会产生同名冲突；`--save-mapping` 在该模式下不写 mapping，并在 stderr 与 JSON 中警告。
- [ ] P2 · 多版本 mapping 按 trace marker id 自动选取（如 `--unmap --mapping-dir`）。触发弱（回答建议「每次构建一个 Build ID」，
      我们已有 `--trace-marker` 的 id 注释 + 0.5.31 的不匹配告警），等有用户提出再做。

**测试证据（免发版，CI）**

- [ ] P2 · 打包 lane 后续：Nuitka onefile、整包 Cython、Windows runner（多模块 + Nuitka standalone 已于 10-11 加入，见 `CURRENT_PLAN_ZH.md`）。
      只在有用户问到或成本可接受时做；Windows 打包 runner 每次约多 5–10 分钟。

**文档（免发版）**

- [ ] **CLI `--check` 是否改为默认离线：10-11 维护者定先保持默认联网；密钥检查已于 10-11 合并（PR #74），可随时复审**（2026-10-11 写联网行为页时登记）：CLI 默认查 PyPI、MCP 默认不查，
      两处不一致。改为默认离线是行为变更，要发版并在 CHANGELOG 写明；不改则维持 `docs/NETWORK_BEHAVIOR.md` 现有说明。
- [ ] P2 · 中文任务页「卖给客户前如何保护 Python 源码」。证据：中文 Q9/Q11/Q12 三个环境全空白，而 Perplexity Q10 引用了
      `README.zh-CN.md`（有中文内容就会被用）。与「中文最小维护面」政策冲突，**待维护者定**；如做，只做 Pages `/zh-cn/` 一页。

**内容选题证据（补到下方选题池第 3、4 篇，不新增题目）**：第 3 篇可直接回应「Nuitka 编译后改名就没意义」这一误解（B3 原话 +
cookbook 实测表）；第 4 篇需覆盖 ChatGPT 实际推荐的 Opy / python-minifier 等，配合上面的开源混淆器比较页。

**复测**：11 月第一周观测时，重点看 ChatGPT 联网 #1、#3、#8、#10（首屏措辞 PR #70 生效后）与 #4、#11（行号还原上线后）。

### P1 gate · Affiliate pilot（方案完成，未授权实现/部署）

- 方案源：[`AFFILIATE_PROGRAM_DESIGN.md`](AFFILIATE_PROGRAM_DESIGN.md)；条款草案明确
  `DRAFT — NOT IN EFFECT`，不能当报名页或付款承诺。
- Worker 10-05 已上线 paid/async 分流与按 Checkout Session 派生的许可号。Affiliate 上线前仍需补齐
  event/session 双幂等、refund/dispute 回冲和佣金状态机，避免重复处理与重复佣金。
- v1 不放 cookie、不建 portal、不上 Stripe Connect/第三方 SaaS；只有真实活跃 affiliate 和人工
  工作量达到设计文档门槛后才升级。三个月无可归因成交就停止，不继续自动化。
- 这项不需要 Core 发版；实现与部署按维护者授权推进，Worker 生产部署仍须单独批准。

### ✅ 可验证性主线（2026-09-20 完成，随 0.5.28 发布）

- 对标文档 `SUPPLY_CHAIN_ASSURANCE.md`（SLSA v1.2 / CycloneDX 1.7 / PEP 740）。
- 稳定 reason code：`pyobfus/core/reason_codes.py`（v1）+ plan/report 发射
  `selected.included`/`excluded.pattern`/`disabled_transforms` + `reason_codes_version`；
  契约 `docs/REASON_CODES.md`。`preserved.*` 为**保留词汇未发射**（analyzer 在收集期
  剪枝、事后无法重建 per-symbol 原因，是刻意的 follow-up）。
- CycloneDX 1.7 声明对齐。


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

## 待发内容

- Core/MCP 当前没有未发布 changelog 内容。
- VS Code schema 已同步 `preserve_param_names` 默认值，随插件自己的后续版本发布。

## IP 相关（2026-09-28 登记 · 待维护者拍板，未执行）

专利申请 CN 202610712171X 与软著的法务事项（是否提前公布、是否出海、商标、转公司）在仓库外的
`pyobfus-legal/IP商业化迁移_TODO.md` 跟踪，**不在公开仓库展开**。这里只登记要改本仓库的部分：

- [ ] **专利标识**：README 与 `landing/index.html` 加申请阶段标识。措辞必须是「专利申请，尚未授权」+
      申请号（英文 "Patent pending (CN 202610712171X, not yet granted)"），**不能写成已授权**。
- [ ] **专有许可补专利条款**：`pyobfus_pro/LICENSE`、`pyobfus_runtime/LICENSE` 现对专利只字未提；补
      「仅授予按本许可运行所需的专利权利，不授予其他专利许可」。措辞发版前请专业人士过目。
- [ ] **发版检查清单加一条**：专利覆盖机制的实现不得进入 Apache-2.0 核心（Apache-2.0 §3 会把核心代码
      涉及的专利权免费授出）。09-28 核查：核心只做 CLI 转发，实现都在 `pyobfus_pro/` 与 `pyobfus-runtime`，
      边界当前守住。
- 节奏：三项可以先写好放进 `[Unreleased]`，**随 11 月第一周月度版本发**，不单独打破 10-25 前静默期。

## 内容节奏（2026-09-27 用户定 · 只写不发到 10-11，10-13 那周起发）

**依据**：09-13→09-26 的 GitHub 流量来源是 github.com 32 / pypi.org 19 / Bing 15 /
Google 14 / DuckDuckGo 9 / chatgpt.com 9，14 天 301 次浏览（169 独立访客）。dev.to、X、
微博、Reddit、HN **一次都没出现**。7–8 月的发布波次（dev.to 两篇阅读 52/42、Show HN 1 分
零外部评论、r/Python showcase）是一次性的，已结束。所以方向改成**能被搜索与 AI 问答
收录的问题型工程文章**，按固定节奏发，每篇都有真实素材、可归因。

**为什么 10-11 前不发**：10-25 前是 Core 静默观察期，目的是拿到第一份不受发版干扰的
下载基线；前两周连内容也不发，保住这份读数。

**渠道分工**

| 渠道 | 角色 | 频率 | 谁发 |
|---|---|---|---|
| DEV（英文） | 主力，工程故事 | 每两周一篇 | 维护者（Claude 起草 + tech-deai + 文末 AI 辅助说明） |
| arong.eu.org（中文） | 中文首发（WordPress 首发原则），自动推 Discord | 每月一篇，跟月度版本 | 维护者跑 findata `publish.py` |
| **知乎**（中文开发者渠道，**2026-09-27 选定，先记录不开动**） | 把 WP 月度文人工粘贴并改写成知乎体，注明原文链接 | 跟 WP 月度文 | 维护者 |
| Reddit r/Python | 当月 showcase 帖里发一条更新 | 有月度版本的月份 | 维护者 |
| X | 每篇 DEV 顺手一条链接帖 | 跟 DEV | 维护者 |
| HN | 最多一次，只投最强的事故复盘，普通链接帖 | 一次 | 维护者本人写标题与全部评论 |
| 微博 | **不发 pyobfus**（受众是投资与医学读者） | — | — |

V2EX 仍卡在账号激活（要邀请码）；Stack Overflow 按 2026-04-22 的决定到 Q4 再评估。

**选题池**（真实素材，按搜索意图排；Stripe webhook 那段默认不写，待维护者定）

1. Cloudflare 拦 `Python-urllib` UA（403 / error code 1010），全体付费客户两个月激活不了
   —— **10-11 已发布 DEV，下一步观察来源与反响**，放在 gitignored 的 `docs/internal/content-2026-10/01-urllib-user-agent-postmortem.md`
   （`published: false`；维护者 09-27 定：发稿前不进公开仓库）
2. SARIF 上传前别再 `|| true`（带出 `pyobfus-action`）—— **草稿已写 09-28**，
   `docs/internal/content-2026-10/02-sarif-or-true.md`（`published: false`，待维护者审）
3. PyInstaller / Nuitka 打包前先混淆（已有 cookbook）
4. 2026 年 PyArmor 替代品的诚实对比（`docs/compare/` 已有搜索流量）
5. Claude / Codex 能不能还原混淆过的 Python（08-01 基准，写明只有 5 个样本）
6. 一个月 10 次发版、下载基线没动（**等 10-25 复盘数据**）
7. **混淆之后，怎么让 AI 助手还能帮你查生产环境报错**（09-28 加，和第 5 篇配对：第 5 篇讲 AI 能不能还原，
   这篇讲 AI 怎么在混淆后继续帮你调试）。对应 08-31 调研里的「可调试性」搜索意图，是 pyobfus 在 AI 方面真正的
   差异点，此前选题池没有。真实素材：`--save-mapping` + `--trace-marker`（文件头告诉落到混淆文件里的 Agent
   该怎么反解）+ `--unmap --json`、MCP 工具 `unmap_stack_trace`、VS Code「Reverse Stack Trace」命令。
   写法：问题型标题，全程用真实命令和输出演示；只写 pyobfus 自己的反向映射，不写成还原他人代码的教程；
   不写「专为 AI 优化」之类空话。AI 渠道的效果看 `download_snapshot.py` 流量来源里的 chatgpt.com 一项。

**排期**

| 时间 | 事项 |
|---|---|
| 09-28 → 10-11 | 只写不发：维护者审第 1 篇、Claude 起草第 2 篇；DEV 个人资料链 GitHub；X 简介加一句 pyobfus maintainer |
| 10-13 那周（周二/三美东上午） | **10-11 已提前发**：DEV 第 1 篇 <https://dev.to/zhurong2020/cloudflare-blocked-urllibs-default-user-agent-and-it-took-me-two-months-to-notice-3k8e>（05:58 UTC；标签已由维护者改回 `cloudflare`；描述取正文首段）+ X 一条（10-11 已发）；1–3 天后（10-14 前后）看反响，决定是否由维护者本人投一次 HN |
| 10-25 | 节奏复盘，同时看第 1 篇的来源数据 |
| 10-27 那周 | DEV 发第 2 篇 + X |
| 11-02 → 11-06 | 月度版本（`[Unreleased]` 非空才发）+ r/Python showcase + WP 中文第 4 篇（1+2 合并）+ 知乎（若届时开动） |
| 11-10 / 11-24 | DEV 第 4、7 篇（第 7 篇 09-28 加入，接在第 5 篇之前先讲「可调试」） |
| 12 月 | 第 5、3 篇 + 12 月 WP 月度篇；第 6 篇顺延到 1 月 |

**草稿存放规则（09-27 定）**

- 未发布的文章一律放 `docs/internal/content-*/`（已 gitignore），**不进 `_drafts/`**：本仓库公开，
  草稿一进 `main`，随下一次 push 就公开了。
- `docs/internal/` **已在** `~/scripts/wsl_daily_backup.sh` 第 9 条里（09-21 加，`pyobfus_local_only/docs_internal/`，
  09-27 日志 OK 845K）。⚠️ 但 09-27 核查发现该脚本的落点 `C:\Users\wuxia\OneDrive\Documents\wsl-backup`
  已不是任何 OneDrive 账号的同步目录（个人账号现同步 `C:\onedrive\wuxiami\OneDrive`），Google Drive 上也只有
  `backups/arong-vps/`：**此前 WSL 每日备份只有本机 C 盘一份**。同日已修：日备份末尾 rclone 镜像到
  `gdrive:backups/wsl/`（详见全局 memory `reference_wsl_local_backup`），`check_backup.sh` 第 5 节可查。
- 发布后可选把定稿连同真实 URL、发布日期、+24h/+7d/+30d 数据写回公开记录（参照
  `_drafts/launch-v0.5.4/README.md` 的 Publication record 写法），草稿原文仍可留在 internal。

**度量与退出**

- 每周一巡检加一项：GitHub 流量来源（`gh api repos/zhurong2020/pyobfus/traffic/popular/referrers`）
  + 每篇 DEV 阅读数。来源与 14 天浏览量已并进 `scripts/download_snapshot.py`（09-28，免发版），巡检跑一条命令即可。
- 算有效：发文后 14 天内来源里出现 dev.to / reddit ≥ 10 独立访客，或 star、安静日中位数上移。
- 退出：前 4 篇 DEV 每篇阅读都不到 100 且来源里从未出现 dev.to → 停止定期发，改成有好故事
  才写；X 满 3 条没有来源 → 停；HN 投后 24 小时零外部评论 → HN 这条线收掉。

## 本轮留下的小尾巴（都不急，按顺手程度做）
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
3. ~~`awesome-python`~~ ❌ **2026-09-24 被拒（未合并）**：09-23 提交
   [`vinta/awesome-python#3352`](https://github.com/vinta/awesome-python/pull/3352)（严格一行、按
   challenger 报并披露维护者身份），次日由维护者 JinyangWang27 关闭，原话
   「A Challenger slot needs adoption-trajectory evidence, and pyobfus is at ~6k downloads/month versus ~313k for pyarmor. Happy to revisit as adoption grows.」
   对方的约 6k 是含镜像口径（pypistats 近 30 天 with_mirrors 6538 / without_mirrors 2172），与
   我们自报的约 2k 不矛盾。结论与预判一致：拒的是采用量不是质量。按既定规则**不争辩、不重开**；
   **重提条件**=非发布日下载基线明显抬升后再议，届时引用这条评论。
4. ~~`awesome-security` 或 `awesome-devsecops`~~ **跳过**：admission 门槛同样是下载量，现在投大概率
   同一结果；等第 3 项的重提条件满足后再一并评估
5. **AlternativeTo**（**需维护者验证邮箱后在对方站点提交**；字段草稿已记入
   `DISTRIBUTION_CHANNELS.md`。免费队列官方口径至少数月，$5 priority review 是可选付费 gate，
   默认不买；同时服务上面第 5 项的对比可见度）
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
| ~~Y-2~~ ✅ | ~~`--expire-hard` 没有到期前提醒~~ **已实现 2026-09-24，随 Core 0.5.30 发布** | runtime `expire_check` 加向后兼容 `warn_days`，窗口内发 `LicenseExpiryWarning`（`UserWarning` 子类，宿主可经 `warnings`/`logging.captureWarnings` 接管）| `--expire-warn-days N`（须配 `--expire-hard`）；16 测试含端到端「warns but still loads」 |
| ~~Y-3~~ ✅ | ~~设备绑定只认 pyobfus 自己的 `current_machine_id()`~~ **v1 已于 2026-09-25 实现，随 Core 0.5.30 发布** | `--bind-key-env NAME`：L3 密钥改由应用提供（`pyobfus_runtime.set_key_provider` 回调 或 base64 env 回退），一次构建跑任意授权机器；v1 只覆盖 L3，配 `--vault` 报错、与 `--bind-device` 互斥。契约 `docs/Y3_KEY_PROVIDER_DESIGN.md` | 19 测试（10 运行时 + 9 构建/校验/端到端含正确/错误 key/provider 通道）；vault 覆盖为后续 |
| ~~Y-4~~ ✅ | ~~Windows 上运行混淆输出没有 CI 验证~~ **已补基础合同** | `integration` job 扩为 Ubuntu + Windows；单文件和跨文件示例均执行混淆产物并与原输出比较 | 覆盖基础 Community 交付；torch/MONAI、Python embedded、L3 runtime 等重型真实下游组合仍需 Y-1 专项验证 |
| ~~Y-6~~ ✅ | ~~name-mangling 打断运行时注解~~ **已修** | 函数签名表达式此前被跳过，或在参数局部作用域压栈后才遍历，导致同模块/导入类改名后 eager annotation 仍引用旧名 | 注解和默认值现在按 Python 语义在函数局部作用域压栈前改写；端到端测试覆盖同模块、跨模块、默认值及参数名遮蔽导入类型 |
| ~~Y-7~~ ✅ | ~~cross-file mangler 作用域 bug~~ **已修** (`069a820`) | 函数局部变量复用被重命名的模块级名字时 Load 引用被误改 → `NameError: name 'Ixx'`。`LocalNameTransformer` 现按 Python 作用域收集函数体内全部绑定名（含 lambda/推导式作用域）| 已修 + 2 回归测试 |
| ~~Y-8~~ ✅ | ~~control-flow flattening 的 `_cff_return_N` 未绑定~~ **已修** | 根因并非函数大小本身：一条路径显式 `return`、另一条路径自然落底时，统一生成的 `return _cff_return_N` 会读取未初始化变量。大型 `try/finally` 只是更容易出现这种路径组合 | 状态机启动前将共享 return slot 初始化为 Python 隐式返回值 `None`；已补最小条件分支与 `try/finally` early-return 两个回归测试 |
| ~~Y-5~~ ✅ | ~~文档漂移~~ **已修** | `pyobfus.yaml.example` 已与社区版无文件/行数限制和 Community Base64 encoding 的现状对齐 | 新增 `OPACITY_CONFIG.md`，记录 TOML 字段、匹配/优先级、CLI 只物化 encrypted 顶层函数的边界和 Y-1 交付限制 |

## 已研究、明确延后（不在队列里，但别忘了）

| 项 | 来源 | 解冻条件 |
|---|---|---|
| ~~self-dogfooding 四条 lane 落地~~ ✅ 2026-09-25 | `SELF_DOGFOODING_BEST_PRACTICES.md` | 已落地为观察模式：`scripts/dogfood/run.py` + `dogfood/canary/` + 非阻塞 `Dogfood` workflow（不是必需检查）。Phase A3 升为 PR gate 仍是单独 reviewed 步骤 |
| MCP Resources / Prompts 原语拆分 | `MCP_PRIMITIVES_DESIGN.md` | 等真实 MCP 用户反馈 |
| 放开 `mcp<2.0.0` 上限 | `MCP_SDK_2X_SPIKE.md` §5 | `mcp-sdk-2x` job 连绿数周 / 有人明确要 2.x / 1.x 停止维护，三者任一 |
| `--output-pyc` 可行性 spike | `CURRENT_PLAN_ZH.md` P3-1 | 只做 spike，不承诺产品化 |
| hosted / remote MCP endpoint | 同上 P3-2 | 明确不做（也因此拿不到 `2026-07-28` 协议） |
| `dependency_advisory` 是否拆成独立工具 | `SEO_AND_COMPETITOR_SCAN_2026-08-31.md` §1.2 | 独立赛道已拥挤，**倾向不拆**，除非出现明确差异点 |

## 周期性

- **Alipay 文案**：Stripe 上 Alipay 自 2026-09-04 起 `Pending approval`，2026-09-22 维护者
  核实仍是。README / 落地页 / `docs/index.md` 里「Alipay (支付宝) is being enabled」一句
  **已于 09-22 删除**（没等到 09-27 期限，因为它本来就说不准）。微信支付已 Enabled，
  中国买家主路径未受影响。**等 Stripe 真 Enabled 再加回来**；可向 Stripe 支持直接问审核在等什么。

- **下载量复查**：**2026-09-23 已查**，数据覆盖至 09-22：Core 09-20（0.5.28 发布日）`120`、
  09-21/09-22 `18 / 21`；MCP `6 / 6 / 9`。发布日尖峰后连续两日回到安静区间，
  **基线未抬升**。此前 2026-09-19
  那次覆盖至 09-18（见 `CURRENT_PLAN_ZH.md` 09-19 条目）。结论：09-16 的 0.5.27 发布日为 `68`（低于
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

已收口（2026-09-24，维护者在 <https://github.com/settings/installations> 操作）：

- [x] **Vercel — 已卸载**。它不部署 pyobfus 的任何面（文档在 RTD、落地页在 Pages、
  `pyobfus-action` 是 Action 仓），对本仓库只有 `contents: write` 风险没有用途，直接卸载。
- [x] **giscus — 已核实干净，保留**。权限仅 Read metadata + Read/write discussions（**无 code/
  contents 写权限**，碰不到 `release.yml`/PyPI）；Repository access 为 Only select，精确 1 个
  `zhurong2020/workshop`（博客仓），不含 pyobfus / pyobfus-action。
- 备忘（Vercel 已卸载后此项变为 moot，保留提醒）：**不要导入那个 "docs" 项目**——它认的是已删的
  `docs/_config.yml`，导入会多长一个重复文档站。

## Zenodo webhook token —— 决定「只验证不轮换」

`repos/.../hooks` 的 Zenodo 条目 URL 里内嵌一个 Zenodo 个人访问令牌（通常带 deposit
写权限）。2026-09-13 排查 Vercel 时曾把 hook 配置整段打印到终端。

**结论：不轮换。** 该值未进仓库、未公开，GitHub 的 webhook 配置本就只有仓库管理员可读；
而轮换要在 Zenodo 关掉再打开仓库以重新生成 webhook，**concept DOI 与仓库的关联一旦
出问题，影响的是 `CITATION.cff`、README 徽章和已发出的学术引用**。用一个确定的风险换
一个很小的风险不划算。

- **每次发版后验证** concept DOI 是否指向新 record。0.5.28 已于 2026-09-23 验证：
  `10.5281/zenodo.20846053` 跳转 record `22858892`，API 返回 version `v0.5.28`、
  publication date `2026-09-20`，链路健康；下次发版后重复。

## 外部等待（不阻塞本地开发）

- **Claude Plugin Marketplace —— 等待支持团队解除提交锁**。09-28 已升级内部；10-11 Tiffany 回信仍在处理、无需补充材料；10-14 再确认旧提交就在当前账号下、只能由目录团队释放，释放后改到 <https://claude.ai/directory/manage> 用付费账号重提（Console 表单已停用）。截至 10-17 无新消息。此前“需要重提”的记录已被后端锁事实取代；不反复提交或换路径绕过。维护者清单与私有 `docs/internal/CLAUDE_PLUGIN_RESUBMISSION_2026-09-22.md` 保留原始证据。
- Open VSX namespace 归属验证：可选，`not verified` 是「未申请」不是「被拒」。
- **Canopii [`canopii-cli#6`](https://github.com/canopii-dev/canopii-cli/issues/6)
  —— 单次 follow-up 已发，等待上游**。2026-09-23 确认 issue 仍 `OPEN`、0 条上游回复后，
  已按约定发出唯一一次简短 follow-up（明确当前版本 0.3.12 与四项验收）；**不再反复催**。
  上游重扫后按四项验收（latest ≥ v0.3.10 /
  识别 8 tools / 不再把 `pyobfus_pro/`、`examples/`、VS Code/Worker 计入 MCP 包
  evidence / PEP 740 provenance 是否被识别），**不是只看总分**。
- **MCP Trust Checker**：**2026-09-22 已实扫**——`npx mcptrustchecker@1.14 scan` 对已发布 wheel
  `pyobfus_mcp-0.3.12`：**Trust grade A · 94/100 · 0 威胁发现**；唯一一条是能力观察
  `MTC-SRC-002`（`tools.py` 里的 shell/command execution，即调用 pyobfus CLI，设计内，
  信息性不扣信任分）。stdio 实跑扫描被其沙箱拒（`Connection closed`），覆盖面为源码级。
  **登记（publish 到其公开 MCP Trust Registry）需要该站 API token，得维护者注册后跑
  `MCPTRUSTCHECKER_TOKEN=… npx --yes mcptrustchecker@1.14.0 publish pyobfus-mcp --registry pypi --online --category developer-tools`**；
  09-23 已用该固定版本的 CLI help 核对 package、registry、online、category 与 token 参数。
  不为徽章改产品逻辑，也不要把 token 写进 shell history、仓库或聊天。结果记在
  `DISTRIBUTION_CHANNELS.md`。

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
