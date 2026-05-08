---
platform: V2EX `/go/python` 节点
title: "[分享创造] pyobfus 0.4 — Python 代码混淆器，不会让 Claude 看不懂崩溃日志"
status: READY (tech-deai cn_platforms.md workflow applied 2026-05-08)
length: ~700 字
target_post: 2026-05-10 (≥24h after 知乎)
voice: V2EX 短促 · 直接列点 · 不长 origin story · 末尾给 GitHub + PyPI
---

# [分享创造] pyobfus 0.4 — Python 代码混淆器，不会让 Claude 看不懂崩溃日志

> 利益声明：我是作者。

最近因为给一个要申请专利的医学项目 ship 算法模块，需要 Python 代码混淆。试了 PyArmor，能用，但有个问题：客户回传的崩溃日志变成了 `'I0' object has no attribute 'I2'`，Claude Code 完全没法读。

PyArmor 的保护是单向设计，本质上没办法在不破坏保护的前提下反向出原始名字。Cython 更糟（直接机器码）。所以花了一个月写了 pyobfus，重点解决一个 trade-off：保护 + AI 调试同时存在。

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
- 643 个测试，Python 3.8-3.14 全过
- 框架预设：FastAPI / Django / Flask / Pydantic / Click / SQLAlchemy
- 商业版 Pro 模块（控制流平坦化、AES 字符串加密、反调试）闭源

威胁模型坦白：这是名字级混淆，不是字节码加密。社区版只能拦「路过的人随手 `tar xf`」。如果你需要拦国家级反编译，pyobfus 不是你要的。

```bash
pip install pyobfus pyobfus-mcp
```

GitHub: https://github.com/zhurong2020/pyobfus

dev.to 英文长文（更细的设计取舍）：https://dev.to/zhurong2020/let-claude-code-debug-your-obfuscated-python-a-guide-to-the-pyobfus-mcp-integration-3epm

欢迎交流威胁模型边界场景，特别是用过 PyArmor / Oxyry 然后切到 AI 编程的踩坑经历。
