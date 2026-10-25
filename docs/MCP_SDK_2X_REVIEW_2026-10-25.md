# MCP SDK 2.x 发布条件复审（2026-10-25）

本轮范围是复审、补齐可重复验证，不直接修改已发布包的依赖上限或发版。
生产 metadata 仍为 `mcp>=1.27.0,<2.0.0`。此前强制越过上限安装 SDK 的 CI
不能证明正常解析成功，因此新增私有候选 wheel 和干净 target 的完整验证。

## 当前证据

2026-10-25 查询 [PyPI MCP](https://pypi.org/project/mcp/2.3.0/) 与
[官方 SDK](https://github.com/modelcontextprotocol/python-sdk)：当前版本 2.3.0，
声明 Python >=3.10。该记录是当日版本快照，后续版本需重新验收。

| 验证 | Linux / Python 3.12.3 结果 |
|---|---|
| 候选 | 复制当前 MCP 0.3.15，仅将 SDK 上限改为 `<3.0.0`，构建 wheel；不修改生产源码 metadata |
| 正常依赖解析 | 新 venv 同次安装候选 wheel、公开 Core 0.9.1、SDK 2.3.0、pytest，成功；没有强装覆盖冲突 |
| 依赖一致性 | `pip check`：No broken requirements found |
| 完整 MCP 测试 | 153 passed，`-I --import-mode=importlib`，使用安装包而非源码遮蔽 |
| legacy stdio | 协商 `2025-11-25`；server version 0.3.15；9 工具全部实际调用通过 |
| auto stdio | 协商 `2026-07-28`；server version 0.3.15；9 工具全部实际调用通过 |
| 机器合同 | 每次结果均检查 status、ai_hint、next_tool 结构；unmap 实际还原；protect_project verified=true |
| 副作用边界 | 临时合成项目、独立 HOME、只读 trial 指引；未启动试用、未访问维护者许可、未请求在线依赖检查 |

原始日志保存在 gitignored `docs/internal/mcp2-review-2026-10-25/`。
候选 wheel 是测试输入，不能上传 PyPI 或作为发布包交付。

## 持续验收

维护者脚本：

```bash
venv/bin/python scripts/build_mcp_sdk2_candidate.py docs/internal/new-sdk2-candidate
# 用干净 venv 正常安装公开 Core、SDK 2.x、pytest 与 candidate/dist/*.whl。
# 以下命令中的 python 指该新环境：
python -m pip check
python -I -m pytest -c pyobfus_mcp/pyproject.toml pyobfus_mcp/tests/ --import-mode=importlib -q
python -I scripts/validate_mcp_sdk2.py
```

`mcp-sdk-2x` CI 改为 Linux/Windows × Python 3.10/3.15 四格，复用上述路径。
服务端以 `-I -m pyobfus_mcp.server` 启动，防止 checkout 遮蔽公开 Core 和候选
wheel。SDK 1.x 的 CI 保留，工具的输入/输出和 shipped manifest 不变。

| 平台 | Python 3.10 | Python 3.15 |
|---|---|---|
| Linux | PR #129 hosted passed | PR #129 hosted passed |
| Windows | PR #129 hosted passed | PR #129 hosted passed |

## 复审结论（已合并 PR #129）

现有证据支持继续双 major 兼容；此前“stdio 没有新协议收益”的历史结论已失效。
四格专项和总 CI/CodeQL 已通过，PR #129 合并为 `d28ee31`。生产上限保持原样；后续可单独准备放宽上限
与 MCP 发版，届时记录确切依赖范围和回退方案；本次不把候选解析结果冒称已升级。
不新增远程 MCP 服务或 HTTP 传输。

最终 head `3fff016`：39 检查成功 / 1 按配置跳过；[CI run 40176818313](https://github.com/zhurong2020/pyobfus/actions/runs/40176818313)。
