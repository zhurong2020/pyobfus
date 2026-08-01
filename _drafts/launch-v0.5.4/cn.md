# 中文发布稿

## 长文版

### pyobfus 0.5.4：给 Pro String Vault 的密钥也补上设备绑定

这是 pyobfus 系列的第三篇（前两篇：《别让你的 Python 代码"裸奔"了》
2025-12-27、《一个让 AI 还能读懂崩溃日志的 Python 代码混淆器》2026-05-21）。
`I0`/`I1` 命名混淆之后生产报错和 AI 工具都读不懂、靠 `mapping.json` +
`--unmap` 本地反解的那套方案，5 月那篇已经讲过，这里不重复，直接说
0.5.4 新补上的东西。

`--bind-device` 这个机制之前只覆盖了 Selective Opacity 的 L3 key。混淆产物
绑定到构建机器或指定设备后，密钥要在运行时重新派生才能解密，换一台机器就
解不出来。但 Pro String Vault（保护常量字符串的那层）的密钥之前不在这个机制
里，仍然作为普通常量写进产物，意味着 vault 加密的内容其实能在任意机器上解开。
这是一个已经写进文档的已知边界，不是掩盖起来的 bug，但确实是个缺口。

0.5.4 把这个缺口补上了：每个 Vault 现在都有独立 salt，密钥在运行时根据绑定
设备重新派生，跟 opacity L3 用的是同一套技术：

```bash
pyobfus src/ -o dist/ --level pro --vault --bind-device
```

Community Edition 的目标是提高随手阅读和复制的
成本，不是不可逆加密；即便使用 Pro，加密的函数或字符串在运行时仍然需要解密，
能够控制进程的攻击者仍可能通过动态分析或内存提取获得内容。本地 trial 也是便利
控制，而不是安全边界。

0.5.4 的发布 CI 包含 1,046 个通过的 Core 测试、1 个 skip、90% coverage，
覆盖 Python 3.9–3.14 和 Linux/macOS/Windows；Core、MCP、端到端测试分别运行。

下一步我不想继续凭感觉堆功能。候选方向包括 ML/model-serving preset、签名构建
来源清单、PyInstaller 集成指南，以及 MCP tool description 的完整性校验。如果你
正在交付 Python 软件，欢迎告诉我哪个才是实际阻塞，也欢迎直接提交能够复现的
框架兼容问题。

项目：<https://github.com/zhurong2020/pyobfus>

文档：<https://pyobfus.readthedocs.io/>

DOI：<https://doi.org/10.5281/zenodo.20846053>

## V2EX / 短版

发布了 pyobfus 0.5.4：一个基于 AST 的 Python 混淆器，Community Edition 是
Apache-2.0。常见混淆工具大多换个名字就完事，pyobfus 额外能安全保存
`mapping.json`，收到生产堆栈后用 `--unmap` 恢复原始名称，再交给开发者或 AI
助手调试。

0.5.4 把 `--bind-device` 扩展到了每个 Pro String Vault key；正常用法是
`pyobfus src/ -o dist/ --level pro --vault --bind-device`，没有 `build` 子命令。

它提高静态阅读成本，不承诺阻止控制运行进程的攻击者。当前 CI 是
Python 3.9–3.14 × 三系统，Core/MCP/端到端测试分开跑。

GitHub：<https://github.com/zhurong2020/pyobfus>
