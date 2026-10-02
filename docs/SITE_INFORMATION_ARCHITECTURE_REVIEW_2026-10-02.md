# pyobfus 网站信息架构调研与改造台账（2026-10-02）

**状态：全部完成；免发版；不得因文档完成自动发布。**

## 背景与结论

本次以 `https://pyobfuscate.com/` 的首页、工具/学习/比较入口及
`best-python-obfuscator-2026` 页面为外部参考，对照 pyobfus 的 GitHub README、
GitHub Pages 与 Read the Docs。参考站值得借鉴的是“一页回答一个意图”、稳定导航、
场景化比较和清晰 CTA，不是其大量在线小工具或 SEO 页面数量。

pyobfus 不照搬在线上传源码、大量薄内容页或宽泛安全宣传。我们的差异仍是：完整且不限
规模的 Community、本地处理、混淆后可诊断、构建可验证/可复现，以及把实测、建议和安全
边界明确分开。

## 三个入口的永久职责

| 入口 | 单一职责 | 避免 |
|---|---|---|
| GitHub README | 帮开发者快速判断、安装并找到仓库入口 | 复制完整文档站或购买页 |
| GitHub Pages | 面向产品决策：场景、优势、版本价值、试用/购买 | CLI 参数百科 |
| Read the Docs | 面向任务执行：安装、保护、检查、验证、调试、集成、参考 | 第二个销售落地页 |

版本边界以 `EDITION_BOUNDARY_POLICY.md` 为准；仓库职责以
`PROJECT_STRUCTURE.md` 为准。三个入口引用同一事实，但用各自场景表达，不复制长清单。

## 已发现问题

1. Pages 首要 CTA 是购买 Pro，不适合当前采用/试用漏斗仍小的阶段。
2. Pages 缺少 Protect / Check / Verify / Debug / Automate 的任务入口。
3. Pages Pro 内容仍是旧式 flag 列表，没有采用四类商业价值。
4. Pages 的 “nothing extra to ship” 已随独立 `pyobfus-runtime` 架构变得不准确。
5. RTD 首页是长功能清单加重复购买区，更像第二个销售页而非文档门户。
6. README 已完成 “Why pyobfus”，本轮不再重复扩写。

## 分阶段执行台账

### A. 调研与口径冻结 — ✅ 完成

- [x] 外部参考与三个自有入口审计
- [x] 冻结职责、借鉴边界及验收原则
- [x] 写入 `CURRENT_PLAN_ZH.md` / `TODO.md`

### B. GitHub Pages 适度重构 — ✅ 完成

- [x] Hero 主 CTA 改为免费安装，Pro 试用为次级入口
- [x] 增加五条任务路径，不新增薄页面
- [x] 用五项差异化优势替代重复功能表达
- [x] Pro 按保护强度/受保护资产/分发控制/责任追踪组织
- [x] 修正 runtime 交付事实，保留购买、证据与诚实边界
- [x] 本地 HTML 解析与差异检查通过

### C. Read the Docs 首页任务化 — ✅ 完成

- [x] 顶部改为 Getting started / Protect / Check / Verify / Debug / Integrate
- [x] Community/Pro 只留摘要与边界政策入口
- [x] 删除首页重复的第二套详细购买/功能清单，链接到 Pages 与 activation guide
- [x] `mkdocs build --strict` 通过

### D. 跨入口一致性验收 — ✅ 完成

- [x] 核对价格、试用、runtime、版本边界、支持版本与 CTA
- [x] `scripts/check.sh` 通过
- [x] 更新本台账、`CURRENT_PLAN_ZH.md`、`TODO.md` 和 `[Unreleased]`
- [x] 单独提交；不 push、不发版，除非维护者明确授权

## 冷启动恢复方法

先读本文件的执行台账，再运行：

```bash
git status --short --branch
git log -5 --oneline
```

从第一个未勾选项继续；不要重做已完成阶段，不要改变现有 URL，不要自行扩展为内容营销
或在线源码上传项目。

## E. README / 中文 / Agent 入口收口 — ✅ 完成

- [x] 英文 README 从 916 行百科全书收敛为项目入口，保留外部引用锚点
- [x] 详细配置、架构、限制、对比与开发内容统一链接到现有专页
- [x] 新增精简 `README.zh-CN.md` 并双向链接，不做完整镜像
- [x] 精简 root / RTD 的 `llms.txt`；Pages 部署时从同一源复制
- [x] Pages 页脚增加公开可见的 Agent 入口，不做隐藏或 UA 分流内容
- [x] GitHub About 已改指产品 Pages；Pages / RTD / CI / CodeQL / Dogfood 均在线验收通过
- [x] 本地全部检查通过；不打 tag、不发版

Agent 决策依据：`llms.txt` 仍是开放提案而非强制标准，用作简短导航而非第三份 README
（https://llmstxt.org/）；`AGENTS.md` 按开放格式只承载编码、测试与仓库约定
（https://agents.md/）；OpenAI 将搜索 `OAI-SearchBot`、训练 `GPTBot` 与用户触发的
`ChatGPT-User` 分开（https://platform.openai.com/docs/bots）。本项目在 `github.io/pyobfus/`
子路径下不能可靠控制域根 robots，因此不伪装已实现 crawler 策略；也不使用隐藏文本或
User-Agent 分流，避免不可审计内容、事实漂移和 cloaking 风险。

## F. 中文与示例的最小维护面 — ✅ 完成

原提议中的 `docs/OVERVIEW_ZH_CN.md` 与 `docs/QUICK_EXAMPLE.md` 不再创建，避免中文事实源和
示例各自变成额外副本。永久规则：

| 内容 | 唯一权威源 | 其它入口 |
|---|---|---|
| 英文产品/安装摘要与最小示例 | `README.md`（同时成为下次 PyPI long description） | RTD/Pages 只链接锚点 |
| 中文说明 | `README.zh-CN.md` | RTD 直接外链；中文 Pages 只做轻量导航壳 |
| 任务型完整文档 | RTD `docs/` 专页 | README/Pages 只链接 |
| Agent 产品指南 | root `llms.txt` | RTD twin 强制比较；Pages 部署时复制 |
| 价格与购买 | `landing/index.html` | README/RTD 只摘要并链接 |

约束：不自动按浏览器语言跳转；中英文 Pages 使用稳定 URL、显式语言切换和 `hreflang`；
翻译只覆盖稳定入口，不翻译完整手册。只有中文真实使用信号足以承担持续维护时，才建立 RTD
正式 translation project。

- [x] README 增加唯一的短 before/after 示例及稳定锚点
- [x] RTD 首页/导航链接中文 README 与 canonical example，不新增翻译页
- [x] 新增最小 `landing/zh-cn/index.html`，不复制功能百科
- [x] 英文/中文 Pages 加语言切换、canonical 与 `hreflang`
- [x] Pages workflow 校验两种语言入口、购买锚点与 Agent guide
- [x] 统一检查、Pages 线上部署及公开 URL/内容验收

线上验收：提交 `4ab32b0` 的 Pages、CI 与 CodeQL 均通过；`/zh-cn/`、英文语言入口、
canonical example 和部署后的 `llms.txt` 已从公开 URL 核对。维护者可在真实桌面/手机浏览器
做一次主观视觉复核，但它不是技术完成 gate，也不需要维护第二份内容。

维护者视觉复核后补充：中文入口不能把“轻量”误解为只展示免费版。页面现增加中文
Professional 判断区，解释四类商业价值、一次性价格和试用条件；顶部“了解 Professional”及
底部“中文查看详情”先跳到这个中文锚点，具体支付步骤仍链接英文唯一权威购买区。各 section
的标题与上方分割线间距同步加大。这是在同一 HTML 内增加导航摘要，不新建翻译文档或支付副本。

第二轮视觉复核发现上一轮间距规则被 `.wrap` 的 CSS 优先级覆盖；已将中英文页的 header、section
和 footer 改为组合选择器，使纵向 padding 真正生效，分割线不再紧贴按钮、卡片或页脚文字。
中文可见文案同时去掉未解释的 `RTD`、`mapping`、`traceback`、`provenance`、`CI` 等缩写或术语，
改用中文含义；完整英文技术文档入口明确提示可使用浏览器内置网页翻译，不建立第二套手册。

## G. 中文定位、Agent 入口与对比声明 — ✅ 完成

本节是 2026-10-02 本轮续作的冷启动检查点。恢复时从第一个未勾选项继续；不得因文档调整
自动打 tag、发布 GitHub Release 或上传 PyPI。

- [x] 判断页脚纯文本 Agent guide 是否保留链接，并优化可见标签/用途说明
- [x] 将首页价值主张补足为“AI 时代为何需要源码保护”，但避免恐惧营销和绝对安全承诺
- [x] 统一中文页 Community / Professional 的易懂命名，检查所有相关 CTA 和正文
- [x] 审计所有公开竞品对比的日期、版本、证据基线、风险与免责说明
- [x] 运行统一检查，部署并核验中英文 Pages / RTD
- [x] 评估今日文档变更是否需要发版，记录最佳发布方式；未经维护者再次确认不发版

执行决定：保留 `llms.txt` 的公开入口以便发现和人工审计，但中英文页都明确标注为“纯文本”，
避免把它伪装成普通说明页。中文 hero 使用“生成式 AI 降低理解、重构和复刻门槛”的窄主张，
同时明确混淆只是知识产权风险管理的一层，不替代服务端保密、合同或法律保护。版本名统一为
“免费社区版”与“Pro 专业版（收费）”，不再只出现未解释的 `Professional`。

对比治理：总览增加 2026-10-02 快照、动态事实、版本/层级/平台范围、商标、独立性和非保证/非
法律意见声明；PyArmor 专页以官方 9.2.7 文档、PyPI 元数据和当日公开购买页为当前基线，明确
935–940 行结果只来自 2026-05-09 的 9.2.4 实验，不能外推到 9.2.7。删除主观“痛点”、绝对
“唯一”、未经限定的“不可逆”和百分比省钱说法；其它专页统一继承总览声明，并收窄易变化的
价格、性能及能力表述。`AGENTS.md` 与 PR 模板已加入永久维护规则。

发布判断：本日主要是 README、Pages、RTD 和政策文档，正确发布通道是合并到 `main` 后由 Pages
及 RTD 连续部署；不应为了刷新 PyPI long description 单独制造包版本、tag 或 GitHub Release。
仓库相对 `v0.5.30` 确有一项用户可见代码修复（`community_edition()` 移除遗留 5 文件/1000 行
默认限制及错误提示），但不是紧急安全/兼容问题，宜继续保留在 `[Unreleased]`，随既定 10-25
复盘后的正常补丁版本一并发布。若维护者因真实受影响用户要求提前发版，应走完整 patch 流程：
版本号与 changelog → 四测试根及 release-candidate 验证 → 签名 tag → OIDC/PEP 740 PyPI 发布 →
公开安装、provenance、GitHub Release 和 Pages/RTD 复核；本轮不自行执行。

线上验收：提交 `8b0245e` 的 Pages、CodeQL 和完整 CI 均通过；中英文产品页公开 URL 已核对
新 hero、Pro 收费版命名及纯文本 Agent 标签；RTD 已核对总览的 2026-10-02 scope/disclaimer 与
PyArmor 专页的 9.2.7/9.2.4 分层基线。本轮没有 tag、GitHub Release 或 PyPI 上传。
