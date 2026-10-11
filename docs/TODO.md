# TODO

排期中的任务清单。**当前计划与状态仍以
[`CURRENT_PLAN_ZH.md`](CURRENT_PLAN_ZH.md) 为准**；本文件只回答「接下来按什么
顺序做」，不记录历史。依据与实测证据见
[`FEATURE_EXPANSION_RESEARCH_2026-09-12.md`](FEATURE_EXPANSION_RESEARCH_2026-09-12.md)。

最后更新：2026-10-11（AI 回答基线完成并衍生改进清单（见「2026-10-11 AI 回答基线衍生的改进」）；首屏多文件措辞 PR #70 已合并；周巡检：09-12 报障客户已激活、原跟进项结案；Glama 两次构建失败经 admin 日志确认是其 Docker 构建服务 502，结案。上一轮 2026-10-10：维护者批准 PR #65 的 6 个决定并合并；Codex 无头实现、Claude 审核合并 G（#66）与 F 方案 A（#67），**发布 Core `0.6.1`**（PyPI/PEP 740/全新安装/Release/Zenodo `23273782`/CFF 已核）；新登记缺陷 I；Discussions #11/#13/#24 加过时说明、#11 改试用命令与措辞，新公告 #68 已发；Pro 客户 0.6.1 通知 5 封已由维护者发出。上一轮 2026-10-08：参数改名设计 PR #65 审核；新登记缺陷 F、G。同日发布 Core `0.6.0`：目录构建改函数局部变量 + 三个 0.5.32 既有缺陷修复，PyPI/PEP 740/Release/Zenodo `23228339` 已核。此前同日：Claude 交叉审核 #57/#59/#60，修复 #57 三处问题后三个 PR 全部 squash 合并：main `f65be9a`/`26337d8`/`81df698`，未发版；P0 第 1 步完成，新登记两个既有转换缺陷与四条非阻断跟进，见「P0 · 目录构建的改名深度」。上一轮 2026-10-07 晚：同日发 0.5.31 与 0.5.32，静默期按「影响用户的 bug」例外提前结束，10-25 复盘照做；PR #57 审核意见已给 Codex；新增维护者动作：是否通知 Pro 客户升级。此前同日：GEO 计划第一轮完成，剩余项见「GEO / 外部采用」；新增 P0「目录构建的改名深度」。上一轮 2026-10-05：Stripe/许可线：两笔新购核对、结账页文案与激活说明更新、Worker 只对已付款发号并部署、webhook 加 async 订阅；新增维护者清单 5 项见下。上一轮 2026-09-30：下载数据留存收口：只保留决策摘要，10-25 复盘后改为月度留存；所有暂不发版的后续改进继续按本文件的触发条件与节奏跟踪。上一轮 09-28：新增「IP 相关」段：专利标识、专有许可专利条款、发版清单 Apache 边界检查，待拍板；选题池加第 7 篇「混淆后让 AI 助手继续帮你调试」并排进 11-24；落地页加 JSON-LD 结构化数据；周一巡检：plugin 锁由 Rudy 09-28 升级到 Anthropic 内部、等其跟进；GitHub 流量来源已并进 `download_snapshot.py`；第 2 篇草稿已写。上一轮 09-27：新增「内容节奏」段：只写不发到 10-11、10-13 那周起 DEV 双周一篇，知乎选定为中文开发者渠道先记录，第 1 篇草稿已写；Show HN 最终结果补记；上一轮 09-26：Claude plugin 孤儿锁已按 Rudy 要求补齐账号核查、workspace ID 与两张截图并在原线程回复，现等后端处理；上一轮 09-25：trial 现状核查 + KV 备份 P0 当日完成；09-24：awesome-python PR #3352 当日被维护者关闭，理由是采用量，见「分发 / 上架队列」；
`pyobfus-runtime` 0.1.0 已通过 OIDC/PEP 740 发布并完成 PyPI 验收；
删除已完全合入 `main` 的本地及远端 `spike/mcp-sdk-2x` 空壳分支；
修正本文件把已随 0.5.28 发布的邮箱 trial 误列为待实现、仍称 0.5.27 为当前版本的状态漂移。
上一轮 2026-09-22：迁移到 WSL 后的核查与收尾，抗 AI 措辞改写完成、Alipay 句已删、
awesome-python PR #3352 已提交（09-24 被拒）、Claude plugin 需重提、MCP Trust Checker 已实扫；详见
`CURRENT_PLAN_ZH.md` 09-22 段。上一轮 2026-09-20：对标竞品 + 国际最佳实践 + 本地已完成/未发版做了一次三透镜
重排，见 `FEATURE_EXPANSION_RESEARCH_2026-09-12.md` 之上的本轮外部核查；新增
**服务端邮箱登记 trial** 为 P1（现已完成并随 0.5.28 发布），依据见
`TRIAL_STRATEGY_DECISION_2026-09-20.md`；
把 provenance / SARIF / build-report / CycloneDX 收拢为一条「可验证性主线」抬为 P0。
Core `0.5.30` 是当前公开版本，已进入 10-25 前静默观察期；运营复查见 `CURRENT_PLAN_ZH.md`）。

## 状态口径

- **实现**与**发布**是两道各自独立的 gate，都需要用户明确批准。
- 任何一项做完后，把它从本文件移除，并在 `CURRENT_PLAN_ZH.md` 记状态；
  不要在这里留「✅ 已完成」的历史层。
- **下游反馈归属（2026-09-17）**：pyobfus 是本工作区自行维护的公共 PyPI 工具。
  CAC Plus 或其他项目暴露的通用混淆缺口、最小复现和回归证据，必须同步登记在本仓库
  （公开 TODO 使用去标识描述，敏感交付背景只进入本地 internal 记录），不能只留在下游文档。
  下游是否选择混淆自己的代码由其分发边界决定；公开第三方依赖不因被打包而自动成为
  pyobfus 的处理目标。

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
      Claude Code workspace ID，请求后端定位/释放。**09-28 Rudy 回信「已升级内部，有消息再跟进」——球在对方，不必再催；锁没释放前别再点表单或换路径绕过**。**10-11 支持 Tiffany 主动回信：团队仍在处理、有进展会再联系（无需我方提供新材料）**。字段/描述与证据见
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
- [ ] **Glama 构建服务 502，10-19 周一巡检时重试一次**（2026-10-11 登记，维护者）：10-08、10-10、10-11 三次测试都在
      毫秒级失败、无构建日志，错误为 Glama 自家 docker-modem 调构建后端得到 nginx `502 Bad Gateway`，与我们的包无关
      （本地实测 `pyobfus-mcp 0.3.12` + Core 0.6.1 正常；公开页、徽章正常）。维护者定先等。10-19 在 Dockerfile 页点一次
      测试：成功即勾掉；仍 502 再给 `support@glama.ai` 发一次报告（附三个 test ID，草稿见 10-11 会话），不要反复点，
      也**不要重新提交条目**。下次发 MCP 前此项必须先通过，否则 Build steps 改版本后无法验证。
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

- [x] **既有缺陷 G · 目录构建的别名导入（优先，0.5.32 已存在，影响用户）**：`from pkg import scale as action` 或
      `from pkg.core import scale as action` 后调用 `action(...)` 即 NameError（局部改名开关无关）。参数改名设计审核中发现；
      应先于参数改名的解析器工作修复。**10-10 已合并 PR #66（`b56afe2`），随 0.6.1 发布**（保留显式本地别名，仅同步被导入符号名）；审核记录私有 `docs/internal/geo-2026-10/PR66_REVIEW_2026-10-10.md`。
- [ ] **既有缺陷 I · 关闭局部改名时函数内别名覆盖模块级导入**（10-10 审 #66 发现，main 与 0.6.0 同样失败，低优先级）：
      模块级 `from pkg.core import helper` + 函数内 `from pkg.core import scale as helper`，加 `--no-crossfile-local-names`
      时模块级的 `helper(...)` NameError。根因：ImportedNameTransformer 的 `import_mappings` 按模块扁平存放，函数内导入覆盖模块级条目。
      默认（开启局部改名）正确。
- [x] **既有缺陷 F · 单文件模式默认改参数但不改关键字调用（优先，0.5.32 已存在）**：同文件 `scale(1, factor=3)` 即 TypeError；
      含 `/`、`*args`、`**kwargs` 的签名还会静默绑错（关键字落进 `**kwargs`、参数取默认值）。无预设、safe、balanced、aggressive
      在 0.5.32 / 0.6.0 都是 `preserve_param_names=False`（框架预设与 library 为 True）。**10-10 已合并 PR #67（`ed8cceb`），随 0.6.1 发布**；审核记录私有 `docs/internal/geo-2026-10/PR67_REVIEW_2026-10-10.md`：
      按 10-10 已合并设计 PR #65 的维护者决定实现默认保留参数名；显式 false 照旧生效但警告，`--init` 模板改为 true，
      `--check` 加 medium 语法候选风险提示，目录 cross-file 参数保留行为不变。证据私有 `docs/internal/geo-2026-10/param-default-evidence/`。
- [ ] **既有限制 H · 通过模块对象访问属性**（10-08 交叉审核发现，0.5.32 已存在）：目录构建里 `from pkg import core` 后
      `core.LIMIT`（或 `import pkg.core as engine; engine.scale()`）时属性名没跟着改 → AttributeError。至少在支持矩阵
      「What gets renamed」写明并在 `--check` 提示；是否改写 `模块.属性` 另议（可与缺陷 G 的导入解析一起看）。
- [ ] **既有缺陷 C · 运行时注入的模块级名字**（#62 审核中发现，0.5.32 已存在）：`enum.global_enum` 这类装饰器在运行时
      把成员注入模块命名空间，引用与 `__all__` 被改名，但注入的定义改不了 → NameError（标准库 `calendar.py` 默认构建即如此）。
      当前绕法：把这些名字加入 `exclude_names`。先在 `--check` 里检测 `global_enum` 并给出提示，同时在支持矩阵写明；
      是否自动保留另议。
- [ ] **既有缺陷 D · `global` 重新绑定导入名**（#62 审核中发现，0.5.32 已存在，低优先级）：模块级 `from pkg.util import helper`，
      函数里 `global helper; helper = ...`；关闭局部改名时产物仍调用原导入（默认开启时正确）。
- [ ] **MCP `unmap_stack_trace` 的 mapping 不匹配提示**在 `pyobfus_mcp/CHANGELOG.md` 的 `[Unreleased]` 中。
      与 #57 的 mapping 格式调整一起评估后再发 MCP；每次发 MCP 都要手工更新 Glama 的 Build steps。
- [ ] **第 2 步：参数改名**：设计文档 `docs/CROSSFILE_PARAMETER_RENAMING_DESIGN.md`（PR #65，Codex 起草、Claude 审核通过）。
      分 5 个 PR：F 的方案 A → mapping 读取端与分析（观察模式）→ 同文件私有函数 → 跨文件 → 扩展；默认关闭。
      文末 6 个问题待维护者拍板；Claude 的建议在私有 `docs/internal/geo-2026-10/PR65_REVIEW_2026-10-08.md`。
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

发版本身是独立 gate。

- **Core `[Unreleased]` 为空**：`0.6.1` 已于 2026-10-10 发布（缺陷 G 别名导入 + F 默认保留参数名）；`0.6.0` 于 10-08 发布。
- **`pyobfus_mcp/CHANGELOG.md` 的 `[Unreleased]`**：mcp SDK 2.x 兼容、mapping 不匹配提示、关键字调用 advisory（10-10 维护者定：暂不发）。VS Code 插件 schema 已随 #67 同步 `preserve_param_names` 默认值，也暂不发插件。刻意不随 Core
  发，攒够增量或有人明确要 2.x 时再发（每发一次 MCP 要手工改 Glama Build steps）。


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
   —— **10-11 已逐条核实事实并修订，待维护者通读后发 DEV（目标 10-13/14）**，放在 gitignored 的 `docs/internal/content-2026-10/01-urllib-user-agent-postmortem.md`
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
| 10-13 那周（周二/三美东上午） | **10-11 已提前发**：DEV 第 1 篇 <https://dev.to/zhurong2020/cloudflare-blocked-urllibs-default-user-agent-and-it-took-me-two-months-to-notice-3k8e>（05:58 UTC；标签误选 `cloudflarechallenge`，已请维护者改回 `cloudflare`；描述取正文首段）+ X 一条；1–3 天后（10-14 前后）看反响，决定是否由维护者本人投一次 HN |
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

- **Claude Plugin Marketplace —— 需重新提交（维护者动作）**。2026-09-22 维护者看到 Console
  「Plugin submissions · No submissions yet」，08-02 的记录已消失；同日核实公开目录
  `claude-plugins-community/.claude-plugin/marketplace.json`（2,320 条）无 `pyobfus` → 从未被批准。
  官方文档现写明流程是 **Console 表单 <https://platform.claude.com/plugins/submit>** → 内部管线
  （跑 `claude plugin validate` + 安全扫描）→ 每夜同步目录；旧记录大概率随管线重建作废，
  「被动等待」已无对象。本地 `validate` 通过、从本仓库以 marketplace 方式实装成功（2 skills）。
  表单文案见 `docs/internal/CLAUDE_PLUGIN_RESUBMISSION_2026-09-22.md`（已修 `protected_project` 笔误）。
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
