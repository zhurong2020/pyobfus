---
platform: 知乎专栏
category: Python / 开源 / AI
title: 我用 Claude Code 写了一个 Python 代码混淆工具 pyobfus，因为不想付钱买一个之后还得对抗它的工具
tags: [Python, 开源项目, 人工智能, 编程]
status: READY v2 (tech-deai 2026-05-08 morning · Section 1 honest rewrite 2026-05-08 evening · removes I0/I2 incident anecdote / 40-min unmap claim that were narrative texture not fact · keeps AI-debug insight as forward-looking reasoning)
length: ~1280 字
target_post: 2026-05-09 (≥24h after 有心工坊 to avoid simultaneous-multi-platform pattern)
voice: 较 colloquial · 第一人称强 · 段落短 · 「我」化叙述 · 末段邀评论
---

# 我用 Claude Code 写了一个 Python 代码混淆工具 pyobfus，因为不想付钱买一个之后还得对抗它的工具

故事得从一份要申请专利的代码说起。

我在帮一个医学影像研究项目做工程实现。核心算法模块跑通了，正准备走专利申请和软件著作权登记。意思是分发出去之前要做代码保护——不是国家级反编译那种，但至少不能让任何路过的人 `tar xf` 一下就读到核心。

> 💡 5 个月前我写过一篇入门介绍 [《别让你的 Python 代码"裸奔"了》](https://www.arong.eu.org/protect-your-python-code-with-pyobfus/)（pyobfus 0.1 时代），讲了 pyobfus 是什么、为什么需要、怎么用。这篇接上回，讲 0.4.0 加了一个我自己最想要的能力：**被混淆的代码在生产报错时还能让 Claude / Cursor 看得懂**。

第一反应是 PyArmor。翻了文档、看了功能矩阵、点开价格页。真正能让反编译变难的功能（字节码加密、控制流平坦化、反调试）都在付费 Pro 层。这是合理的商业模式。但让我停下来想了一下：现在要花的这笔钱，到底是买一个真适合我工作流的工具，还是买一个对别人合适、对我会别扭的工具？

我那阵子的开发节奏是这样的。写代码大半时间是 Claude Code，vibe coding 那种节奏。生产报错第一个动作就是把栈贴给 Claude。一个把类名全改成 `I0`、方法名全改成 `I2` 的混淆器，落到这种工作流里会怎样？日志贴过去，Claude 只能回一句 *"I have no idea what `I0` or `I2` refer to"*。**我亲手装的保护把我天天靠的助手挡在了门外**。对真正的攻击者还一点用都没有（他们有的是时间慢慢反推）。

PyArmor 是给「由人读日志」的时代设计的，Cython 直接机器码就更远。两者放在 2013 年、2017 年都说得过去。但调试位上坐着模型的项目里，这套老假设就接不上了。

还有两个推力让我从「调研」滑到「自己写」。

一个是 PyArmor 免费版的代码量上限。官方 license 表里这条叫 Big Script 模式，免费层用不了。今天我专门起了干净 venv 实测（PyArmor 9.2.4 trial）：单文件 935 行通过、**940 行就 `ERROR out of license`**（看行数不看字节，900 行 67KB 仍然过）。我那个医学影像项目的核心模块远超过这条线，意味着「将来要不要付费」直接变成「现在就得付费」。

另一个是 Claude Code 当时还很新，我刚开始 vibe coding，好奇这种方式能跑多远。从零写一个 Python 混淆器不算大项目（AST 改写 + 名字映射 + CLI 包装，边界清楚），刚好拿来试。Claude Code 写得出来 → 后面更难的项目就敢做；写不出来 → 至少摸到工具边界。**结果是写得出来**，所以 pyobfus 既是一个工具，也是我对 vibe coding 这种工作方式的一次自我验证。

这是个真实的 trade-off，但好像没人讨论。所以我没付钱，反过来花了一个月的晚上，跟 Claude Code 一起把工具写出来。围绕一个取舍：保护对外不变，但对自己留一份小到能塞进密码管理器的反向映射表。pyobfus 0.4.0，2026-04-22 在 PyPI 发布。

## 为什么 AI 编程时代的混淆器需要重新设计

主流 Python 混淆工具基本都是 AI 编程兴起之前设计的。PyArmor 2013 年起步，Cython 更早。它们假设一个由人主导的工作流：人写代码、人混淆、人读崩溃日志。

但这假设到 2026 年已经不成立。现在调试代码的越来越多是大模型。它需要把崩溃栈和源代码对照起来读。栈里全被改成 `I0`、`I2`，源代码却还是 `UserService`、`get_profile`，模型就接不上。

代价不是没有，只是过去由人脑里默默承担。AI 接手调试后代价就显出来了。

修复思路也不是「少混淆一点」。要做的是：把映射表放在只有你能拿到的地方。

## 四个核心特性

这版本就解决一件事：保护和可调试能不能两个都要。

**`pyobfus --check`** — 混淆前的风险扫描器。扫源代码 AST，标出会被混淆破坏的地方（`eval`、`exec`、动态 `getattr`、框架反射、`__name__` 字符串比较、`__all__` 导出）。输出 JSON 带 `ai_hint` 字段，告诉你的 AI 助手下一条命令该跑什么。

**`pyobfus --init`** — 零配置上手。识别 FastAPI / Django / Flask / Pydantic / Click / SQLAlchemy，自动生成对应的 `pyobfus.yaml`。配置文件带行内注释。

**`pyobfus --save-mapping` 配 `--unmap`** — 这是我花时间最长的功能。混淆时保存正反向名字映射，生产崩溃日志回来后本地跑：

```bash
pyobfus --unmap --trace error.log --mapping mapping.json
```

得到带原始标识符的崩溃日志。贴进 Claude Code，AI 读起来跟没混淆过一样。客户看到的还是混淆字节，AI 看到的是原始名字。

**`pyobfus-mcp`** — 配套的 MCP 服务器。Claude Desktop / Cursor / Windsurf / Zed 可以把上面三件事当工具调用，无需手敲 shell。已经登记到官方 MCP Registry（`io.github.zhurong2020/pyobfus-mcp`）。

## 30 秒上手

```bash
pip install pyobfus pyobfus-mcp
```

Claude Desktop 配置加一段：

```json
{
  "mcpServers": {
    "pyobfus": { "command": "pyobfus-mcp" }
  }
}
```

重启 Claude Desktop 后输入：

> *"扫描一下我项目里的 src/ 目录是否适合混淆，如果是 FastAPI 项目就帮我生成 pyobfus.yaml"*

Claude 自动调 `check_obfuscation_risks` → 读 JSON → 看到 `suggested_preset: fastapi` → 调 `generate_pyobfus_config` → 把生成的配置交给你审。完全无需手敲。

## 限制与威胁模型

老实说：pyobfus 是名字混淆 + 可选字符串加密，不是字节码级加密。一个有耐心、有技术、有时间的攻击者可以反推大部分内容（特别是社区版输出）。如果你的威胁模型是国家级反编译团队，请用别的工具。或者更现实地，别用 Python 写那种代码。

它给你换来的是：

- 偶然的逆向工程（把 `dist/` 里类名、API 路径、业务逻辑字符串扫一遍那种）要花更多时间
- 字符串加密（Pro 版）让简单 `strings` 扫描看不到字面密钥
- 控制流平坦化（Pro 版）让静态分析痛苦
- 生产环境的 AI 调试闭环继续可用，前提是 mapping.json 你妥善保管

最后一条是我做整个版本想换的那个 trade。其它 Python 混淆器都让你二选一。pyobfus 说你可以两个都要，前提是你自己保管好一份 1KB 不到的小文件。

## v0.5 在规划

下个版本的计划：分层保护（每个模块独立配置 AI 能看见多少）、VS Code 插件、终于可以扔掉 Python 3.8。如果你有具体需求场景希望优先做，欢迎到 GitHub 开 issue。

## 为什么我开源它

这个项目最初是给医学项目写的。但写完发现这个问题不是医学影像独有：任何 ship 商业 Python 代码、又依赖 AI 编程做调试的开发者都会撞上。所以决定 Apache 2.0 开源，让人不用重新造一遍。

商业版（Pro）的差异化模块（控制流平坦化、AES-256 字符串加密、反调试、license 嵌入）保持闭源。这是我对单人维护项目长期可持续的让步。社区版能解决 80% 的常见需求。

## 资源链接

- GitHub: https://github.com/zhurong2020/pyobfus（欢迎 star / issue）
- PyPI: `pip install pyobfus pyobfus-mcp`
- dev.to 英文长文（更技术细节）：https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm
- AI 集成模板六种格式：https://github.com/zhurong2020/pyobfus/tree/main/templates/ai-integration

如果你 ship 的代码用了 pyobfus，请保管好 mapping.json。它很小、很无聊，但它是六个月后 AI 调试闭环还能继续工作的唯一原因。

如果你也用 Claude Code 写过商业代码踩到这个坑，欢迎评论区交流。
