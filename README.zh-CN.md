# pyobfus：面向交付的 Python 代码混淆器

[English](https://github.com/zhurong2020/pyobfus/blob/main/README.md) ·
[产品页面](https://zhurong2020.github.io/pyobfus/) ·
[完整文档](https://pyobfus.readthedocs.io/) ·
[PyPI](https://pypi.org/project/pyobfus/)

pyobfus 是本地运行、基于 AST 的 Python 混淆器，支持 Python 3.9–3.14。
它不仅转换源码，还提供构建前检查、构建证据和生产 traceback 反向映射，让混淆后的
软件仍然可以维护，也便于 AI 编程 Agent 协助诊断。

Community 版本采用 Apache-2.0，不限制文件数和代码行数，也不需要试用。

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

框架预设包括 FastAPI、Django、Flask、Pydantic、Click、SQLAlchemy 和 ML。
完整配置、打包与验证流程请从[任务型文档首页](https://pyobfus.readthedocs.io/)进入。

## Community 与 Professional

Community 提供可靠混淆、检查、验证和调试的完整本地工作流。

Professional 针对四类商业价值收费：

- 更强保护：AES、控制流平坦化、反调试、Selective Opacity、Seal；
- 更多受保护资产：import 字符串、嵌入数据、String Vault、traceback；
- 分发控制：设备、到期、运行次数、平台和应用提供密钥；
- 责任追踪：取证水印和买方专属构建。

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

## 安全边界

混淆提高阅读和逆向成本，但不能让客户端 Python 逻辑不可恢复。密钥、凭证和授权决策
应留在环境变量、密钥管理系统或服务端。

- [威胁模型](https://pyobfus.readthedocs.io/en/latest/THREAT_MODEL/)
- [支持证据矩阵](https://pyobfus.readthedocs.io/en/latest/SUPPORT_MATRIX/)
- [竞品比较](https://pyobfus.readthedocs.io/en/latest/COMPARISON/)
- [项目架构](https://pyobfus.readthedocs.io/en/latest/PROJECT_STRUCTURE/)

问题请提交到 [Issues](https://github.com/zhurong2020/pyobfus/issues)，讨论与建议请使用
[Discussions](https://github.com/zhurong2020/pyobfus/discussions)。
