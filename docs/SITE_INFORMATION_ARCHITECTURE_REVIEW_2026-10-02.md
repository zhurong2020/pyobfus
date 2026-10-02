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
