---
target_platforms:
  - 有心工坊 / tech-empowerment (primary, professional 科普 tone)
  - 知乎专栏 (adapted, more colloquial)
  - V2EX `/go/python` (adapted, even shorter, more casual)
status: DRAFT v1 (2026-05-05) — SUPERSEDED by ready-to-post versions in `post-cn-ready/` (2026-05-08)
ready_versions: post-cn-ready/{tech_empowerment,zhihu,v2ex}.md (tech-deai cn_platforms.md workflow applied · 8 HIGH-AI fixes · LOW-AI preserved)
ready_index: post-cn-ready/README.md (per-platform differences + posting schedule + rewrite log)
target_post_window: 2026-05-08 to 2026-05-22 (within 48h after dev.to article lands)
sequencing: post AFTER dev.to article goes live (CN traffic needs the EN canonical first for backlink credibility)
length_target: 1,400-1,600 字（有心工坊）· 1,200-1,400（知乎）· 600-800（V2EX）
---

> ⚠️ **This file is now the design log, not the post source.** Posting versions live at `post-cn-ready/` (tech_empowerment / zhihu / v2ex / README). Do not edit this draft for content fixes — edit the corresponding `post-cn-ready/*.md` instead. This file retains the original design notes + per-platform adaptation guidelines that informed the ready versions.

---

# CN platform notes (apply when adapting)

## 有心工坊 / tech-empowerment

- Category: **技术赋能**
- Voice: 专业、数据驱动、科普 tone（参考心脏组 CLAUDE.md 风格）
- Structure: opening hook → `<!-- more -->` → main content → 🌍 English resources
- Embed 2 张截图（Phase 3 重渲染版）：`03_obfuscate_demo.png` 在「四个核心特性」一节内；`04_json_output.png` 在「30 秒上手」一节
- Footer 一定带英文资源段，方便读者深挖
- 不写 AI 协助声明（有心工坊读者不在意；写了反而让叙述生硬）

## 知乎专栏

- 较 colloquial / 第一人称视角强
- 段落更短，技术细节减半（知乎读者多为通才不一定都写 Python）
- 标题更"我"化：「我开源了一个 Python 代码混淆工具 pyobfus」
- 末尾鼓励 issue / star，知乎用户对 GitHub 流量响应好
- 可以稍带"使用 AI 编程开发的工具"叙事钩子（vibe coding 在知乎是热词）

## V2EX `/go/python`

- 短促，~600-800 字
- 直接说"刚发了 v0.4，这是和 PyArmor 的差别"，list 化
- 不要长 origin story；V2EX 用户对故事化文字反感
- 末尾给 GitHub + PyPI 链接即可

---

# 主体草稿（有心工坊 / 知乎适用）

> 利益声明: 我是 pyobfus 的作者。本文为个人记录，无任何赞助。

---

## 起源：一份要申请专利的代码

pyobfus 这个工具是从一个具体需求里长出来的。

我在帮一个医学影像研究项目做工程实现，几个核心算法模块已经能在生产环境跑起来。问题是这些模块马上要走专利申请和软件著作权登记，分发出去之前必须做某种程度的代码保护——不是国家级反编译那种保护，但至少不能让任何路过的人 `tar xf` 一下就能读到核心算法。

最直接的方案当然是 PyArmor。我去翻了文档，看了功能矩阵，找到了价格页。能真正给反编译者添堵的那些东西——字节码加密、控制流平坦化、反调试——都在付费 Pro 层。这是合理的商业模式，没问题。但让我停下来想了一下：我要付的授权费，是为一个适合我工作流的工具，还是为一个适合「**别人**」工作流的工具？

我的工作流有它自己的形状。那一阵子写代码大半时间是 Claude Code，vibe coding 的方式：我描述需求，模型给出实现，我看着调整。生产报错时第一个动作也是把崩溃栈贴给 Claude。那么一个会把所有类名换成 `I0`、所有方法名换成 `I2` 的混淆器，落到这种工作流里会怎样？崩溃日志贴过去，Claude 只能回一句 *"I have no idea what `I0` or `I2` refer to"*——我亲手装的保护，把我天天用的助手挡在门外，反过来对真正的攻击者一点用都没有（他们有的是时间慢慢反推）。

PyArmor 是给「由人读崩溃日志」的工作流设计的。Cython 编进机器码，离 LLM 可读更远。两者放在 2013 年、2017 年都讲得通。但放到一个晚上 vibe coding 的项目里，调试位上坐的是模型——这套老假设接不上。

这是个真实的 trade-off，但好像没人讨论。所以与其付钱买一个我之后还要对抗的工具，不如自己写一个小的。一个月晚上，跟 Claude Code 一起一行行码出来，围绕一个取舍：保护对外不变，但对自己留一份小到能塞进密码管理器的反向映射表。这就是 pyobfus 0.4.0，2026-04-22 在 PyPI 发布。

<!-- more -->

## 为什么 AI 编程时代的混淆器需要重新设计

现在主流的 Python 混淆工具基本都是 AI 编程兴起之前设计的：PyArmor 2013 年起步，Cython 更早，Oxyry 2017 年左右。它们都假设一个由人主导的工作流——人写代码、人混淆、人读崩溃日志。

但这套假设到了 2026 年已经不成立。现在调试代码的越来越多是大模型，它需要把崩溃栈和源代码对照起来读。如果栈里的标识符全被改成 `I0`、`I2`，源代码却还是 `UserService`、`get_profile`，模型就接不上。

代价不是不存在，只是从前由人脑子里桥接，所以没显形。现在 AI 介入了，代价就显形了。

修复思路也不是"少混淆一点"——真正要做的是把那座桥放在只有你能拿到的地方。

## pyobfus 0.4.0 的四个核心特性

整个版本是围绕一个具体的取舍设计的：保护和可调试，要两者兼得。

**`pyobfus --check`** — 混淆前的风险扫描器。指向你的源代码，扫描 AST，标出会被混淆破坏的地方（`eval` / `exec` / 动态 `getattr` / 框架反射 / `__name__` 字符串比较 / `__all__` 导出）。输出 JSON 带 `ai_hint` 字段，告诉你的 AI 助手下一条命令该跑什么。

**`pyobfus --init`** — 零配置上手。识别 FastAPI / Django / Flask / Pydantic / Click / SQLAlchemy，自动生成对应的 `pyobfus.yaml`。配置文件带行内注释，给人和 AI 同时看。

**`pyobfus --save-mapping` 配 `pyobfus --unmap`** — 这是整个版本我花时间最长的功能。混淆时 `--save-mapping mapping.json` 保存正向 + 反向名字映射；生产崩溃日志回来时本地反向运行：

```bash
pyobfus --unmap --trace error.log --mapping mapping.json
```

得到的是带原始标识符的崩溃日志。贴进 Claude Code，AI 读起来跟没混淆过一样。**客户看到的还是混淆字节，AI 看到的是原始名字**——这是 pyobfus 整个版本最想做对的事。

**`pyobfus-mcp`** — 配套的 MCP（Model Context Protocol）服务器。装好后 Claude Desktop / Claude Code / Cursor / Windsurf / Zed 可以把上面三件事当工具调用，无需手敲 shell。已经登记到官方 MCP Registry（`io.github.zhurong2020/pyobfus-mcp`）。

[此处放截图：03_obfuscate_demo.png — 混淆前后并排对比]

## 30 秒上手

```bash
pip install pyobfus pyobfus-mcp
```

Claude Desktop 配置（macOS 路径 `~/Library/Application Support/Claude/claude_desktop_config.json`）加：

```json
{
  "mcpServers": {
    "pyobfus": {
      "command": "pyobfus-mcp"
    }
  }
}
```

重启 Claude Desktop，然后输入：

> *"扫描一下我项目里的 src/ 目录是否适合混淆，如果是 FastAPI 项目就帮我生成 pyobfus.yaml"*

Claude 会自动调用 `check_obfuscation_risks(path="src/")` → 读 JSON → 看到 `suggested_preset: fastapi` → 调用 `generate_pyobfus_config(path="src/", preset_override="fastapi")` → 把生成的配置交给你审。完全无需手敲 shell。

[此处放截图：04_json_output.png — pyobfus --check --json 结构化输出]

## 限制与威胁模型

老实说：pyobfus 是名字混淆 + 可选的字符串加密，不是字节码级加密。一个有耐心、有技术、有时间的攻击者可以反推大部分内容（特别是社区版输出）。如果你的威胁模型是国家级反编译团队，请用别的工具（或者更现实地，别用 Python 写那种代码）。

它给你换来的是：

- 偶然的逆向工程（把 `dist/` 里类名、API 路径、业务逻辑字符串扫一遍那种）要花更多时间
- 字符串加密（Pro 版）让简单 `strings` 扫描看不到字面密钥
- 控制流平坦化（Pro 版）让静态分析痛苦
- 生产环境的 AI 调试闭环继续可用——前提是 mapping.json 你妥善保管

最后一条是我做整个版本想换的那个 trade。其它 Python 混淆器都让你二选一：保护或者可调试。pyobfus 说你可以两个都要，前提是你自己保管好一份 1KB 不到的小文件。

## 为什么我开源它

这个项目最初纯粹是给医学项目的工程支持写的。但写完之后发现这个问题不是医学影像独有——任何要 ship 商业 Python 代码、又依赖 AI 编程做调试的开发者都会撞上。所以决定 Apache 2.0 开源，让需要的人不用重新造一遍。

商业版（Pro）的差异化模块（控制流平坦化、AES-256 字符串加密、反调试、license 嵌入）保持闭源——这是我对单人维护项目长期可持续的让步。社区版能解决 80% 的常见需求。

## v0.5 在规划

下个版本的计划：分层保护（每个模块独立配置 AI 能看见多少）、VS Code 插件、终于可以扔掉 Python 3.8（EOL 已经到 2024-10）。如果你有具体需求场景希望优先做，欢迎到 GitHub 开 issue。

## 资源链接

- GitHub: https://github.com/zhurong2020/pyobfus
- PyPI: `pip install pyobfus pyobfus-mcp`
- AI 集成模板（CLAUDE.md / .cursorrules / AGENTS.md / windsurfrules.md / cursor-rules.mdc / copilot-instructions.md 六种格式开箱即用）：https://github.com/zhurong2020/pyobfus/tree/main/templates/ai-integration
- 完整 JSON schemas + CLI 参考（写给 AI agent 的版本）：https://github.com/zhurong2020/pyobfus/blob/main/llms-full.txt
- dev.to 英文长文（更技术细节）：[填入 dev.to 文章 URL，发文当天更新]

🌍 **English resources** (for readers who want to dig deeper):
- Full project README: https://github.com/zhurong2020/pyobfus
- llms-full.txt (everything an AI agent needs): https://github.com/zhurong2020/pyobfus/blob/main/llms-full.txt
- MCP Registry entry: `io.github.zhurong2020/pyobfus-mcp`

如果你 ship 的代码用了 pyobfus，请保管好 mapping.json。它很小、很无聊，但它是六个月后 AI 调试闭环还能继续工作的唯一原因。

---

# 知乎版本调整指引

将上面主体草稿做以下修改即可适配知乎：

1. 标题改为：「我开源了一个 Python 代码混淆工具 pyobfus，因为 PyArmor 让 Claude Code 看不懂崩溃日志了」
2. 删除「免责声明」框（知乎读者预设作者就是介绍自己作品）
3. 把「<!-- more -->」标记删掉（知乎不识别）
4. 减少 Markdown 列表层级——知乎渲染器对深层 list 不友好
5. 把「为什么我开源它」一节挪到结尾，因为知乎读者更关心"作者动机"这条钩子
6. 末段加一句：「如果你也用 Claude Code 写过商业代码踩到这个坑，欢迎评论区交流」
7. 标签：`#Python` `#开源项目` `#人工智能` `#编程`

# V2EX 版本（独立短稿）

V2EX `/go/python` 适用，不超过 800 字。不复用上面的长稿。

---

**标题**: 「[分享创造]」 pyobfus 0.4 — Python 代码混淆器，不会让 Claude 看不懂崩溃日志

**正文**:

> 利益声明：我是作者。

最近因为给一个要申请专利的医学项目 ship 算法模块，需要 Python 代码混淆。调研了 PyArmor — 真正能让反编译变难的功能（字节码加密 / 控制流平坦化 / 反调试）在付费 Pro 层，价格不是问题但停下来想了一下：现在我大半代码是 Claude Code 写的，崩溃日志也是贴给 Claude 看的。如果用 PyArmor 把类名全换成 `I0`、方法名换成 `I2`，崩溃栈一回来 Claude 就读不懂了。这事 PyArmor 不可能在它当前的架构下修，因为它的保护本来就是单向设计。Cython 更糟（直接机器码）。

所以没付，自己花一个月跟 Claude Code 一起写了 pyobfus，重点解决一个 trade-off：保护 + AI 调试可同时存在。

核心思路：

```
pyobfus src/ -o dist/ --save-mapping mapping.json   # 混淆，保存正反向映射
# 客户给你崩溃日志 error.log
pyobfus --unmap --trace error.log --mapping mapping.json
# 输出带原始标识符的可读栈，贴给 Claude 即可
```

`mapping.json` 你自己留着（密码管理器/加密 vault 都行），不上传任何地方，不进 dist/。客户看到的还是混淆字节；你的 AI 看到的是原始名字。

附带一个 MCP 服务器（`pyobfus-mcp`），Claude Desktop / Cursor / Windsurf 可以直接把上面流程当工具调用。

技术细节：
- Apache 2.0 开源核心
- 655 个测试，Python 3.8-3.14 全过
- 框架预设：FastAPI / Django / Flask / Pydantic / Click / SQLAlchemy
- 商业版 Pro 模块（控制流平坦化 / AES 字符串加密 / 反调试）闭源

威胁模型坦白：这是名字级混淆，不是字节码加密。社区版只能拦"路过的人随手 `tar xf`"。如果你需要拦国家级反编译，pyobfus 不是你要的。

```bash
pip install pyobfus pyobfus-mcp
```

GitHub: https://github.com/zhurong2020/pyobfus

欢迎交流威胁模型边界场景，特别是用过 PyArmor / Oxyry 然后切到 AI 编程的踩坑经历。

---

# Pre-publish 检查（CN 三平台共用）

- [ ] EN dev.to 文章已发布 ≥48h（让 CN 读者点 EN 链接时是有效的）
- [ ] 把上面文末「dev.to 文章 URL」placeholder 替换成真实链接
- [ ] 截图就位（用 Phase 3 重渲染过的中性化版本，路径在 `pyobfus-legal/software_copyright/screenshots/`）
- [ ] WriteHuman 或类似工具过一遍（CN 检测器虽然不如 GPTZero，但有心工坊读者对 AI 文风敏感）
- [ ] 标题逐平台改：有心工坊正式 / 知乎"我"化 / V2EX 标签前缀
- [ ] 三平台间隔 24h 以上发布（避免被识别为同步铺贴）

# v0.5 之后

如果反响不错，第二篇 CN 文章可以写「我用 Claude Code 一个月写了 pyobfus 的复盘」——纯 AI vibe-coding 视角，技术细节让位给开发流程。这是知乎专栏特别吃的题材。
