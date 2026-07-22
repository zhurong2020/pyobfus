# 中文发布稿

## 长文版

### 我做了一个不会让生产报错变成乱码的 Python 混淆器

代码混淆有一个经常被忽略的问题：类名和函数名变成 `I0`、`I1` 以后，
外部的人不容易直接读代码了，但开发者自己收到的生产报错也可能失去意义，
Claude Code、Cursor 之类的工具同样不知道这些名字原来是什么。

这正是我做 [pyobfus](https://github.com/zhurong2020/pyobfus) 的出发点。
它是一个基于 Python AST 的代码混淆器。Community Edition 使用 Apache-2.0，
支持 FastAPI、Django、Flask、Pydantic、Click 和 SQLAlchemy 的框架预设，
也提供稳定的 JSON CLI 与 MCP server。

最关键的是，它可以在构建时单独保存名称映射：

```bash
pip install pyobfus
pyobfus --check src/ --json
pyobfus src/ -o dist/ --save-mapping mapping.json
```

客户拿到混淆后的代码，开发者自己安全保存 `mapping.json`。收到生产环境堆栈后：

```bash
pyobfus --unmap --trace error.log --mapping mapping.json --json
```

原始名称恢复以后，既可以自己排查，也可以继续交给 AI 编程助手分析。

刚发布的 0.5.4 还补上了一个 Pro 设备绑定缺口。此前 `--bind-device` 已经
保护 Selective Opacity 的 L3 key，但 String Vault 的 key 仍可能作为常量写入
产物。现在每个 Vault 都有独立 salt，并在运行时根据绑定设备派生 key：

```bash
pyobfus src/ -o dist/ --level pro --vault --bind-device
```

这里也需要把边界说清楚：Community Edition 的目标是提高随手阅读和复制的
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
Apache-2.0。它和常见混淆工具最大的区别不是多一种变换，而是可以安全保存
`mapping.json`，收到生产堆栈后用 `--unmap` 恢复原始名称，再交给开发者或 AI
助手调试。

0.5.4 把 `--bind-device` 扩展到了每个 Pro String Vault key；正常用法是
`pyobfus src/ -o dist/ --level pro --vault --bind-device`，没有 `build` 子命令。

边界也写明了：它提高静态阅读成本，不承诺阻止控制运行进程的攻击者。当前 CI 是
Python 3.9–3.14 × 三系统，Core/MCP/端到端测试分开跑。

GitHub：<https://github.com/zhurong2020/pyobfus>
