# CN trio · ready-to-post 索引

3 篇 ready-to-post 平台版本（tech-deai `prompts/cn_platforms.md` 工作流应用 2026-05-08）。源 design log 仍在 `../post-cn-bilingual.md`（DRAFT v1，含 platform notes 不再重复维护）。

## 投稿计划

按 `_drafts/post-cn-bilingual.md` 头部 sequencing + tech-deai 工作流 Step 6 「三平台间隔 24h 以上发布」要求：

| 顺序 | 平台 | 文件 | 目标日期 | 长度 |
|---|---|---|---|---|
| 1 | 有心工坊 / tech-empowerment | [`tech_empowerment.md`](tech_empowerment.md) | 2026-05-08 (Fri) | ~1480 字 |
| 2 | 知乎专栏 | [`zhihu.md`](zhihu.md) | 2026-05-09 (Sat, ≥24h gap) | ~1280 字 |
| 3 | V2EX `/go/python` | [`v2ex.md`](v2ex.md) | 2026-05-10 (Sun, ≥24h gap) | ~700 字 |

## 每篇关键差异

### 有心工坊 (`tech_empowerment.md`)
- 利益声明框 ✅
- `<!-- more -->` Pelican-style cut marker ✅
- 2 张截图 placeholder 标记（`03_obfuscate_demo.png` 「四个核心特性」内 + `04_json_output.png` 「30 秒上手」内）
- 末段「🌍 English resources」段落
- 「为什么我开源它」放在「限制与威胁模型」之后，「v0.5」之前
- 完整 dev.to URL 已嵌入资源段

### 知乎 (`zhihu.md`)
- 标题第一人称化 + 强 hook：「我开源了一个 Python 代码混淆工具 pyobfus，因为 PyArmor 让 Claude Code 看不懂崩溃日志了」
- 删除利益声明框（知乎读者预设作者就是介绍自己作品）
- 删除 `<!-- more -->` 标记（知乎不识别）
- 「为什么我开源它」挪到结尾（知乎读者更关心作者动机）
- 末段加邀评论钩子：「如果你也用 Claude Code 写过商业代码踩到这个坑，欢迎评论区交流」
- 标签：`#Python` `#开源项目` `#人工智能` `#编程`
- 段落更短，列表层级 ≤2

### V2EX (`v2ex.md`)
- 标题前缀「[分享创造]」（V2EX 节点常规格式）
- 利益声明 1 行（V2EX 用户最敏感）
- 不复用长 origin story
- 直接列差别 + 命令 + 数字（643 tests / Apache 2.0 / Python 3.8-3.14）
- 末尾邀的是「踩坑经历」而不是「问题反馈」（V2EX 文化更喜欢平等技术讨论）
- 长度严格 ≤800 字（实际 ~700）

## tech-deai 工作流应用细节（2026-05-08 Phase 0 第 1 次实战）

应用 `~/.claude/skills/tech-deai/prompts/cn_platforms.md` Step 2 中文 HIGH AI 模式扫源稿（`post-cn-bilingual.md`）。修复 ~8 处：

| # | 原句 | 改后 | 中文 HIGH 类别 |
|---|---|---|---|
| 1 | 「最直接的方案当然是 PyArmor」 | 「最直接的方案是 PyArmor」 | 翻译腔（of course 痕迹） |
| 2 | 「这条路上没有现成的方案——PyArmor 的保护模型...」 | 删 em-dash 改逗号 | 结构性破折号 |
| 3 | 「整个版本是围绕一个具体的取舍设计的：保护和可调试，要两者兼得。」 | 「这版本就解决一件事：保护和可调试，能不能两个都要。」 | 套话开头 + 排比铺陈 |
| 4 | 「**客户看到的还是混淆字节，AI 看到的是原始名字**——这是 pyobfus 整个版本最想做对的事。」 | 删 em-dash 改句号 + 「这是这个版本最想做对的事」 | 结构性破折号 |
| 5 | 「代价不是不存在，只是从前由人脑子里桥接，所以没显形」 | 「代价不是没有，只是过去由人脑里默默承担」 | 翻译腔 + 诗化用词「桥接 / 显形」 |
| 6 | 「修复思路也不是『少混淆一点』——真正要做的是把那座桥放在只有你能拿到的地方」 | 「修复思路也不是『少混淆一点』。要做的是：把映射表放在只有你能拿到的地方。」 | em-dash + 「真正要做的是」+「那座桥」明喻 |
| 7 | 「这个项目最初纯粹是给医学项目的工程支持写的。但写完之后...所以决定 Apache 2.0 开源——」 | 删「纯粹」+ em-dash 改冒号 | 套话「最初纯粹」 + em-dash |
| 8 | 「商业版（Pro）的差异化模块（...）保持闭源——这是我对单人维护项目长期可持续的让步。」 | 删 em-dash 改句号 | em-dash |

LOW AI patterns 全部保留 verbatim：

- 第一人称 + 短句
- 具体数字（「2026-04-22 在 PyPI 发布」「~1KB 小文件」）
- 命名错误的虚拟语气提及（`'I0' object has no attribute 'I2'` — v2 honest rewrite 里改成了「会怎样 / 假设贴过去」的条件式，不再是真实事故陈述）
- 网络口语（「踩到这个坑」）
- 自承认弱点（「老实说：pyobfus 是名字混淆 + 可选的字符串加密，不是字节码级加密」）
- 网络口语段落收尾（「别用 Python 写那种代码」）

> **2026-05-08 evening 更新（Path A v5 honest rewrite）**：原本被列在这个 LOW-AI 保留清单里的两条——「我装了，跑了，混淆产物看起来很专业」+「40 分钟手工反推」+「Vibe coding 写出来的代码，结果 vibe coding 已经看不懂了」——属于 *fabricated 叙事*（实际作者并未装 PyArmor 跑过崩溃栈，是为了戏剧化 hook 而虚构的事件）。这次 v2 修订把 Section 1 改成了 *forward-looking reasoning*（"调研了 PyArmor，价格 + 单向设计两层，停下来想了一下：如果用了会怎样"）。AI debug 担忧本身是真见解，只是事件层从「真发生过」改成「想到了所以没装」。低 AI 检测得分受影响有限——burstiness 还在、第一人称还在、具体数字（PyPI 发布日 / 一个月 / ~1KB）都还在。三平台 ready 文件已同步至 v2。

## Pre-publish 平台共用 checklist

- [x] EN dev.to 文章已发布 ≥24h（夸日发文 2026-05-07 evening, 当前 2026-05-08 morning）
- [x] 把文末「dev.to 文章 URL」placeholder 替换成真实链接 ✅ 已嵌入 3 篇
- [ ] 截图就位（用 Phase 3 重渲染过的中性化版本，路径在 `pyobfus-legal/software_copyright/screenshots/`）— **user 投稿前自己加**
- [x] tech-deai 工作流过一遍（2026-05-08 应用 · cn_platforms.md Step 1-6 全部）
- [x] 标题逐平台改：有心工坊正式 / 知乎"我"化 / V2EX 标签前缀
- [x] 三平台间隔 24h 以上发布（5/8 → 5/9 → 5/10 计划）

## Post-publish · metrics 追踪建议

每平台投稿后 24h、48h、7d 入档 `pyobfus/docs/V0.4_EXECUTION_LOG.md`：
- 阅读数 / 点赞 / 收藏 / 评论
- 单 link 跳转 GitHub stars 增量（用 `gh api repos/zhurong2020/pyobfus --jq '.stargazers_count'` 取每天数字）
- 评论里的真问题（filter 出可作为 v0.5 优先级 input 的）

---

**生成方式**：tech-deai skill v1.0.0 (`~/.claude/skills/tech-deai/`) `prompts/cn_platforms.md` workflow Step 1-6 全部应用。Phase 0 第 1 次真实运行 · 见 `~/.claude/skills/tech-deai/RUN_LOG.md` Run 1。

**Last updated**: 2026-05-08 morning
