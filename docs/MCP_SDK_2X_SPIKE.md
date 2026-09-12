# mcp SDK 2.x 迁移探路（2026-09-12）

Status: 探路完成，**兼容代码与 `mcp-sdk-2x` CI job 已于 2026-09-12 合并进
`main`**（分支 `spike/mcp-sdk-2x` 保留作历史）。合并后该 job 在 main 上首次真实
运行并通过——`ci.yml` 只在 `main`/`develop` push 与 PR 上触发，所以探路阶段它
从未在云端跑过。**依赖上限仍为 `mcp<2.0.0`，未发版**，两者都需要用户单独批准。

触发点：`FEATURE_EXPANSION_RESEARCH_2026-09-12.md` §3.2 实测到
`pyobfus-mcp` 在 `mcp 2.x` 下根本起不来（`FastMCP` 已更名 `MCPServer`），
而 MCP 规范 `2026-07-28` 已 GA。本文件回答两个问题：**移植要改多少**，
以及**不移植到底损失什么**。

---

## 1. 结论

| 问题 | 答案 |
|---|---|
| 移植成本 | **小**。适配层三处改动，8 个工具的注册代码一行未改 |
| 1.x / 2.x 能否同一份代码 | **能**。97 个 MCP 测试在两个 major 下全过 |
| 行为是否有差异 | **实测无差异**：8 工具、`meta`、`status`/`ai_hint`/`next_tool` 契约、serverInfo 版本全部一致 |
| 升级能否拿到 `2026-07-28` 协议 | **不能**——见 §3，这是本轮最重要的发现，它推翻了「生态时限」这个立项理由 |
| 建议 | 合并兼容代码 + 新增真跑 2.x 的 CI；**本轮仍保留 `mcp<2.0.0` 上限**，等 2.x 线跑一段时间再放开 |

---

## 2. 移植实际改了什么

适配层 `pyobfus_mcp/server.py` 三处：

1. `_load_server_class()`：优先 `from mcp.server.mcpserver import MCPServer`
   （2.x），`ImportError` 时回落 `from mcp.server.fastmcp import FastMCP`（1.x）。
2. `_construct_server()`：先试 `server_class(name=..., version=...)`。**2.x 把
   `version=` 变成了一等构造参数**，于是 1.x 时代那个戳私有
   `app._mcp_server.version` 的补丁在 2.x 上自动退役；`TypeError` 时才回落到
   老路径。
3. `main()` 不变——两个 major 的 `run()` 都默认 stdio。

8 个 `@app.tool(name=, description=, meta=)` **一行未改**：2.x 的
`MCPServer.tool()` 签名仍然接受 `meta=`（还多了 `title` / `annotations` /
`icons` / `structured_output`，我们没用）。

另外两处是 1.x 内部形状的假设，已改成两边都认：

- `tool_manifest.compute_live_manifest()`：`Tool.inputSchema`（1.x）↔
  `Tool.input_schema`（2.x）。**schema 的 JSON 本身两边逐字相同**，所以
  shipped manifest 的 digest 校验在 2.x 下照样通过——这条是实测，不是推断。
- `test_build_server_advertises_this_packages_version`：1.x 走
  `app._mcp_server`，2.x 走公开的 `app.version`（内层对象也从 `_mcp_server`
  更名为 `_lowlevel_server`）。测试改为「哪个 seam 存在就查哪个」，断言落在
  「客户端实际收到的版本」上。

## 3. 🔴 升级**不会**让 stdio server 用上 `2026-07-28` 协议

立项时的假设是「我们停在 1.x 线 → 最高只能协商到 `2025-11-25` → 正在落后」。
实测把它推翻了一半：**2.x 的 stdio 服务器同样只协商到 `2025-11-25`**。

同一份 handshake 脚本（自己收发 JSON-RPC，不用 SDK 客户端，因为要看「宿主
看到什么」）：

| SDK | 客户端请求 | 协商结果 | serverInfo | 工具数 | 契约字段 |
|---|---|---|---|---|---|
| 1.27.0 | `2025-11-25` | `2025-11-25` | `pyobfus 0.3.12` | 8 | `status`/`ai_hint`/`next_tool` |
| 2.2.0 | `2026-07-28` | **`2025-11-25`** | `pyobfus 0.3.12` | 8 | 同上 |
| 2.2.0 | `2025-11-25` | `2025-11-25` | `pyobfus 0.3.12` | 8 | 同上 |

原因在 SDK 自己的版本表里：

```
HANDSHAKE_PROTOCOL_VERSIONS = ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25')
MODERN_PROTOCOL_VERSIONS    = ('2026-07-28',)
LATEST_HANDSHAKE_VERSION    = 2025-11-25
```

`2026-07-28` 属于 **modern（stateless）**那一档，不走 `initialize` 握手，而是
靠每请求的 `io.modelcontextprotocol/protocolVersion` 信封 + 探测协商，代码里
所有相关分支都在 **client 侧与 streamable-http** 上。给 2.x 的 stdio 连接发一条
带该信封的 `tools/list`，服务器明确拒绝：

```
-32600 this connection serves the handshake protocol era;
       requests carrying the 2026-07-28 envelope are not accepted on it
```

**所以：升到 2.x 对一个本地 stdio server 不带来任何协议层收益。** 想要
`2026-07-28`，要做的是换传输（streamable HTTP / 远程），而那正是
`CURRENT_PLAN_ZH.md` 里明确「不做」的 hosted MCP 方向。

这条把 2.x 迁移从「生态时限」重新定性为**依赖卫生**：该做，但不急，且不应
用「协议落后」当理由对外宣传。

## 4. 验收证据

- `pyobfus_mcp/tests/` **97 passed** 在 `mcp 1.27.0` 与 `mcp 2.2.0` 下各跑一遍。
- 真实 stdio 握手在两个 major 下逐项一致（见 §3 表）。
- shipped tool-manifest digest 在 2.x 下校验通过 → 两边生成的 JSON schema 相同。
- 两个 major 的 `requires-python` 都是 `>=3.10`，与 `pyobfus-mcp` 现有下限一致，
  **放开上限不会影响任何 Python 版本支持**。

## 5. 为什么本轮仍不放开 `mcp<2.0.0`

- 2.x 线很新（2.0.1 / 2.1.0 / 2.2.0 都在约三周内发布）。上限一旦放开，
  `uvx pyobfus-mcp` 的用户会**自动**拿到 2.x，我们没有真实宿主侧的使用数据。
- 升级目前**没有可讲的用户收益**（§3），所以承担新线的回归风险不划算。
- 代价也已经记清楚：**上限存在期间，想主动装 2.x 的用户会遇到 pip 依赖冲突**。
  如果有人真的来要，这就是放开的信号。

配套动作是新 CI job `mcp-sdk-2x`：装完包之后**故意越过上限**装 `mcp>=2,<3`，
建服务器、断言 8 个工具、跑完整 MCP 测试套件。它是阻塞的，与既有
`mcp-sdk-latest` 同一思路（那个 job 也是为了抓 SDK 漂移而存在）。顺带修正了
既有 job 的名字：它叫 "latest mcp SDK"，但因为本包的上限，resolver 永远给它
1.x，**从来没测过 2.x**，名字有误导性，现已改为 "mcp SDK 1.x"。

放开上限的建议条件（满足任一即可重新评估）：

1. `mcp-sdk-2x` 这个 job 连续绿若干周；
2. 有用户或宿主明确要求 2.x；
3. 1.x 线进入维护终止或停止接收修复。

## 6. 不在本轮范围

- 不实现 stateless / streamable-HTTP 传输（那是 hosted MCP 方向，已明确不做）。
- 不实现 MCP Apps（沙箱 iframe UI）、extensions framework、CIMD 授权。
- 不改 8 个工具的响应契约。
