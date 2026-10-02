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

## F. 中文与示例的最小维护面 — ⏳ 等待线上验收

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
- [ ] 统一检查、线上部署和人工视觉检查入口
