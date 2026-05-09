---
platform: 有心工坊 / tech-empowerment
category: 技术赋能
title: pyobfus — 一个让 AI 还能读懂崩溃日志的 Python 代码混淆器
status: READY v2 (tech-deai 2026-05-08 morning · Section 1 honest rewrite 2026-05-08 evening · removes I0/I2 incident anecdote / 40-min unmap claim that were narrative texture not fact · keeps AI-debug insight as forward-looking reasoning)
length: ~1480 字
target_post: 2026-05-08
embed_screenshots:
  - 03_obfuscate_demo.png  (一节「四个核心特性」内)
  - 04_json_output.png     (一节「30 秒上手」内)
---

> 利益声明: 我是 pyobfus 的作者。本文为个人记录，无任何赞助。

> 💡 **接上回**：5 个月前我写过一篇 [《别让你的 Python 代码"裸奔"了》](https://www.arong.eu.org/protect-your-python-code-with-pyobfus/)，介绍了 pyobfus 是什么、Python 代码为什么需要保护、最基本的用法。当时还是 0.1 版本。这 5 个月没停手，0.4.0 加了我自己最想要的一个能力：**被混淆的代码在生产报错时还能让 Claude / Cursor 看得懂**。这篇讲这个能力是怎么来的、解决了什么、怎么用。

---

## 起源：一份要申请专利的 Python 代码

我在帮一个医学影像研究项目做工程实现（基于 Python），几个核心算法模块已经在生产跑起来。这些模块要走专利申请和软件著作权登记，分发之前必须做代码保护：不是国家级反编译那种，但至少不能让一般用户 `tar xf` 一下就读到核心算法。

最直接的方案是 PyArmor。我看了一下，发现两件事不太对：（1）真正能让反编译变难的能力都在付费 Pro 层，而 PyArmor 免费版的代码量上限对我那个项目刚好不够用（[实测文档](https://github.com/zhurong2020/pyobfus/blob/main/docs/PYARMOR_TRIAL_LIMIT_EXPERIMENT.md)：PyArmor 9.2.4 trial 单文件超过约 940 行就拒绝混淆）。（2）即使付费用了，工作流也对不上：我那阵子代码大半是 Claude Code 写的，崩溃日志也是贴给 Claude 看的，一个把所有类名改成 `I0` 的混淆器一旦上线，崩溃栈回来 Claude 只能回一句 *"I have no idea what `I0` or `I2` refer to"*。我亲手装的保护反倒把我天天靠的助手挡在门外。

PyArmor 是给「人读崩溃日志」的时代设计的，保护本来就是单向，没法在不破坏保护的前提下反向出原始名字。Cython 直接机器码更糟。两者放在 2013 年都讲得通，但放到 2026 年一个晚上 vibe coding 的项目里，调试位上坐的是模型，老假设接不上了。

再加上 Claude Code 当时还很新，我正想试试 vibe coding 这种方式能跑多远。从零写一个 Python 混淆器不算大项目（AST 改写 + 名字映射 + CLI 包装，边界清楚），刚好是个练手目标。

所以我没付那笔钱，花了一个月的晚上跟 Claude Code 一起一行行写出来，围绕一个取舍：保护对外不变，但对自己留一份小到能塞进密码管理器的反向映射表。这就是 pyobfus 0.4.0，2026-04-22 在 PyPI 发布。既是一个工具，也是 vibe coding 这种工作方式的一次自我验证。

<!-- more -->

## 为什么 AI 编程时代的混淆器需要重新设计

主流的 Python 混淆工具基本都是 AI 编程兴起之前设计的：PyArmor 2013 年起步，Cython 更早，Oxyry 2017 年左右。它们都假设一个由人主导的工作流：人写代码、人混淆、人读崩溃日志。

但这套假设到 2026 年已经不成立。现在调试代码的越来越多是大模型，它需要把崩溃栈和源代码对照起来读。如果栈里的标识符全被改成 `I0`、`I2`，源代码却还是 `UserService`、`get_profile`，模型就接不上。

代价不是没有，只是过去由人脑里默默承担。现在 AI 接手调试，代价就显出来了。

修复思路也不是「少混淆一点」。要做的是：把映射表放在只有你能拿到的地方。

## pyobfus 0.4.0 的四个核心特性

这版本就解决一件事：保护和可调试，能不能两个都要。

**`pyobfus --check`** — 混淆前的风险扫描器。指向你的源代码，扫描 AST，标出会被混淆破坏的地方（`eval` / `exec` / 动态 `getattr` / 框架反射 / `__name__` 字符串比较 / `__all__` 导出）。输出 JSON 带 `ai_hint` 字段，告诉你的 AI 助手下一条命令该跑什么。

**`pyobfus --init`** — 零配置上手。识别 FastAPI / Django / Flask / Pydantic / Click / SQLAlchemy，自动生成对应的 `pyobfus.yaml`。配置文件带行内注释，给人和 AI 同时看。

**`pyobfus --save-mapping` 配 `pyobfus --unmap`** — 这是整个版本我花时间最长的功能。混淆时 `--save-mapping mapping.json` 保存正向 + 反向名字映射；生产崩溃日志回来时本地反向运行：

```bash
pyobfus --unmap --trace error.log --mapping mapping.json
```

得到的是带原始标识符的崩溃日志。贴进 Claude Code，AI 读起来跟没混淆过一样。**客户看到的还是混淆字节，AI 看到的是原始名字**。这是这个版本最想做对的事。

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

老实说：pyobfus 是名字混淆 + 可选的字符串加密，不是字节码级加密。一个有耐心、有技术、有时间的攻击者可以反推大部分内容（特别是社区版输出）。如果你的威胁模型是国家级反编译团队，请用别的工具，或者更现实地，别用 Python 写那种代码。

它给你换来的是：

- 偶然的逆向工程（把 `dist/` 里类名、API 路径、业务逻辑字符串扫一遍那种）要花更多时间
- 字符串加密（Pro 版）让简单 `strings` 扫描看不到字面密钥
- 控制流平坦化（Pro 版）让静态分析痛苦
- 生产环境的 AI 调试闭环继续可用，前提是 mapping.json 你妥善保管

最后一条是我做整个版本想换的那个 trade。其它 Python 混淆器都让你二选一：保护或者可调试。pyobfus 说你可以两个都要，前提是你自己保管好一份 1KB 不到的小文件。

## 为什么我开源它

这个项目最初是给医学项目写的。但写完发现这个问题不是医学影像独有：任何 ship 商业 Python 代码、又依赖 AI 编程做调试的开发者都会撞上。所以决定 Apache 2.0 开源，让人不用重新造一遍。

商业版（Pro）的差异化模块（控制流平坦化、AES-256 字符串加密、反调试、license 嵌入）保持闭源。这是我对单人维护项目长期可持续的让步。社区版能解决 80% 的常见需求。

## v0.5 在规划

下个版本的计划：分层保护（每个模块独立配置 AI 能看见多少）、VS Code 插件、终于可以扔掉 Python 3.8（EOL 已经到 2024-10）。如果你有具体需求场景希望优先做，欢迎到 GitHub 开 issue。

## 资源链接

- GitHub: https://github.com/zhurong2020/pyobfus
- PyPI: `pip install pyobfus pyobfus-mcp`
- AI 集成模板（CLAUDE.md / .cursorrules / AGENTS.md / windsurfrules.md / cursor-rules.mdc / copilot-instructions.md 六种格式开箱即用）：https://github.com/zhurong2020/pyobfus/tree/main/templates/ai-integration
- 完整 JSON schemas + CLI 参考（写给 AI agent 的版本）：https://github.com/zhurong2020/pyobfus/blob/main/llms-full.txt
- dev.to 英文长文（更技术细节）：https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm

🌍 **English resources** (for readers who want to dig deeper):

- Full project README: https://github.com/zhurong2020/pyobfus
- llms-full.txt (everything an AI agent needs): https://github.com/zhurong2020/pyobfus/blob/main/llms-full.txt
- MCP Registry entry: `io.github.zhurong2020/pyobfus-mcp`

如果你 ship 的代码用了 pyobfus，请保管好 mapping.json。它很小、很无聊，但它是六个月后 AI 调试闭环还能继续工作的唯一原因。
