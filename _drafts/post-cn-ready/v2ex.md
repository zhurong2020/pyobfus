---
platform: V2EX `/go/python` 节点
title: "[分享创造] pyobfus 0.4 — Python 代码混淆器，不会让 Claude 看不懂崩溃日志"
status: READY v2 (tech-deai 2026-05-08 morning · Section 1 honest rewrite 2026-05-08 evening · removes "试了 PyArmor → 客户回传崩溃日志" claim that was narrative texture not fact · keeps single-line-design / Claude-can't-read concern as forward-looking reasoning)
length: ~700 字
target_post: 2026-05-10 (≥24h after 知乎)
voice: V2EX 短促 · 直接列点 · 不长 origin story · 末尾给 GitHub + PyPI
---

# [分享创造] pyobfus 0.4 — Python 代码混淆器，不会让 Claude 看不懂崩溃日志

> 利益声明：我是作者。

最近给一个要申请专利的医学项目 ship 算法模块，需要 Python 代码混淆。调研了 PyArmor，发现两件事不太对：(1) PyArmor 免费版超过约 940 行就要付费版（[5 月实测过](https://github.com/zhurong2020/pyobfus/blob/main/docs/PYARMOR_TRIAL_LIMIT_EXPERIMENT.md)），我那个项目核心模块远超过这条线。(2) 即使付费用了，工作流也对不上：我那阵子代码大半是 Claude Code 写的，崩溃日志也贴给 Claude 看的，PyArmor 把类名改成 `I0`，崩溃栈回来 Claude 就读不懂了，而 PyArmor 的保护是单向设计没法在保留保护的前提下反向。Cython 更糟（直接机器码）。

所以没付，反过来当时刚开始用 Claude Code vibe coding，想试这种方式能跑多远，就花了一个月的晚上跟 Claude Code 一起写了 pyobfus，重点解决一个 trade-off：保护 + AI 调试可以同时存在。

旧文是 [pyobfus 0.1 入门介绍](https://www.arong.eu.org/protect-your-python-code-with-pyobfus/)，这帖讲 0.4 新加的能力。

核心思路：

```
pyobfus src/ -o dist/ --save-mapping mapping.json   # 混淆，保存正反向映射
# 客户给你崩溃日志 error.log
pyobfus --unmap --trace error.log --mapping mapping.json
# 输出带原始标识符的可读栈，贴给 Claude 即可
```

`mapping.json` 自己留着（密码管理器、加密 vault 都行），不上传任何地方，不进 dist/。客户看到的还是混淆字节；你的 AI 看到的是原始名字。

附带一个 MCP 服务器（`pyobfus-mcp`），Claude Desktop / Cursor / Windsurf 可以直接把上面流程当工具调用。

技术细节：

- Apache 2.0 开源核心
- 655 个测试，Python 3.8-3.14 全过
- 框架预设：FastAPI / Django / Flask / Pydantic / Click / SQLAlchemy
- 商业版 Pro 模块（控制流平坦化、AES 字符串加密、反调试）闭源

威胁模型坦白：这是名字级混淆，不是字节码加密。社区版只能拦「路过的人随手 `tar xf`」。如果你需要拦国家级反编译，pyobfus 不是你要的。

```bash
pip install pyobfus pyobfus-mcp
```

GitHub: https://github.com/zhurong2020/pyobfus

dev.to 英文长文（更细的设计取舍）：https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm

欢迎交流威胁模型边界场景，特别是用过 PyArmor / Oxyry 然后切到 AI 编程的踩坑经历。
