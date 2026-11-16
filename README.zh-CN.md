# pyobfus：面向交付的 Python 代码混淆器

[English](https://github.com/zhurong2020/pyobfus/blob/main/README.md) ·
[中文产品入口](https://zhurong2020.github.io/pyobfus/zh-cn/) ·
[完整文档](https://pyobfus.readthedocs.io/) ·
[PyPI](https://pypi.org/project/pyobfus/)

pyobfus 是本地运行、基于 AST 的 Python 混淆器，支持 Python 3.9–3.15。
它把多文件项目和包作为整体混淆：跨模块统一改名并同步改写 import，输出仍是不依赖
pyobfus 的普通 `.py` 文件。它不仅转换源码，还提供构建前检查、构建证据和生产 traceback 反向映射，让混淆后的
软件仍然可以维护，也便于 AI 编程 Agent 协助诊断。

Community 版本采用 Apache-2.0，不限制文件数和代码行数，也不需要试用。Professional 版本的部分机制已提交专利申请（CN 202610712171X，尚未授权）。

> **v0.15.0 新增**：`--check-delivery` 现在检查 PyInstaller 可执行文件的顶层成员，内嵌字节码仍明确标为未检查。Python 3.15 运行时 `.pyc` 不再被误报为来源未知。CI 客户端预先信任备用签发公钥，为未来计划中的轮换做准备。

> 历史版本更新见[变更日志](https://github.com/zhurong2020/pyobfus/blob/main/CHANGELOG.md)。

## 主要优势

- **不是限规模演示版**：免费版可以处理真实多文件项目。
- **混淆后仍可诊断**：mapping 由开发者私有保存，可恢复生产 traceback 中的名称。
- **构建过程可验证**：支持风险扫描、dry-run、语法验证、provenance、可复现输出和构建报告。
- **本地、跨平台**：源码不需上传，Community 输出普通 Python 文件。
- **诚实的安全边界**：明确区分实测、建议和威慑能力，不把客户端混淆宣传为不可逆加密。

## 快速开始

```bash
pip install pyobfus

pyobfus --check src/
pyobfus src/ -o dist/ --dry-run --json
pyobfus src/ -o dist/ --save-mapping mapping.json --verify-syntax

# 收到生产错误日志后恢复原始标识符
pyobfus --unmap --trace error.log --mapping mapping.json
```

0.7.1 起提供可选的 `--verify-names` 静态全局名字检查，会明确提示未覆盖的模块；用法与限制见[名字验证说明](https://pyobfus.readthedocs.io/en/latest/NAME_VERIFICATION/)。

框架预设包括 FastAPI、Django、Flask、Pydantic、Click、SQLAlchemy 和 ML。
完整配置、打包与验证流程请从[任务型文档首页](https://pyobfus.readthedocs.io/)进入。
最小输入/输出示例只在英文 README 维护，见
[Minimal example](https://github.com/zhurong2020/pyobfus#minimal-example)，避免多份示例漂移。

## Community 与 Professional

Community 提供可靠混淆、检查、验证和调试的完整本地工作流。

Professional 为商业交付增加四类能力：

- **保护强度：** AES 加密（包括使用应用自管密钥的 L3 / Selective Opacity）、控制流平坦化、死代码注入、反调试和封印（sealing）。
- **受保护资产：** import 字符串、嵌入数据、Runtime String Vault 和受保护的错误堆栈。
- **分发控制：** 按设备、期限、运行次数、平台或应用提供的密钥控制运行。
- **责任追踪：** 取证水印和买方专属构建。

长期划分原则见
[Community / Pro 边界政策](https://github.com/zhurong2020/pyobfus/blob/main/docs/EDITION_BOUNDARY_POLICY.md)。

Professional 为 **45 美元一次性购买**，不是订阅。可以先使用无需注册、无需信用卡的
五天试用：

```bash
pyobfus-trial start
```

购买方式、微信支付和退款说明见
[产品页面](https://zhurong2020.github.io/pyobfus/#purchase-professional-edition)，
购买后参阅[激活指南](https://pyobfus.readthedocs.io/en/latest/LICENSE_ACTIVATION_GUIDE/)。

## AI Agent、编辑器与 CI

- `uvx pyobfus-mcp` 启动 MCP server，无需 API key，不上传源码；
- `pyobfus-review` / `pyobfus-protect` Skills 分开只读审查与生成构建；
- VS Code / Open VSX 扩展提供风险诊断与 traceback 反解；
- `zhurong2020/pyobfus-action@v1` 支持 GitHub Actions 和 SARIF；
- CLI 提供稳定 JSON、reason code 和 `ai_hint`。

Agent 入口见公开、可由人审查的
[`llms.txt`](https://github.com/zhurong2020/pyobfus/blob/main/llms.txt)；
开发 Agent 的仓库约定见
[`AGENTS.md`](https://github.com/zhurong2020/pyobfus/blob/main/AGENTS.md)。项目不会根据
User-Agent 返回隐藏指令或不同事实。

## 中文指南

- [卖给客户前如何保护 Python 源码](https://pyobfus.readthedocs.io/en/latest/zh/protect-python-before-selling/)
- [Python 混淆后客户报错，怎样定位原来的函数](https://pyobfus.readthedocs.io/en/latest/zh/debug-obfuscated-python/)
- [各保护方案能还原出什么（英文 FAQ）](https://pyobfus.readthedocs.io/en/latest/guides/protect-python-code-faq/)

## 安全边界

混淆提高阅读和逆向成本，但不能让客户端 Python 逻辑不可恢复。密钥、凭证和授权决策
应留在环境变量、密钥管理系统或服务端。

- [威胁模型](https://pyobfus.readthedocs.io/en/latest/THREAT_MODEL/)
- [支持证据矩阵](https://pyobfus.readthedocs.io/en/latest/SUPPORT_MATRIX/)
- [竞品比较](https://pyobfus.readthedocs.io/en/latest/COMPARISON/)
- [项目架构](https://pyobfus.readthedocs.io/en/latest/PROJECT_STRUCTURE/)

问题请提交到 [Issues](https://github.com/zhurong2020/pyobfus/issues)，讨论与建议请使用
[Discussions](https://github.com/zhurong2020/pyobfus/discussions)。
