# 分发扩展调研与执行顺序

更新时间：2026-09-07

## 结论

项目当前的工程基础已经足够支撑扩展分发：Core `0.5.22`、MCP `0.3.10`、VS
Code Extension `0.4.2` 均已发布，已有 PyPI、GitHub、MCP Registry、VS Code
Marketplace 和两个活跃 MCP awesome-list 入口。当前主要短板是自然用户、外部
贡献和可归因的使用数据，而不是继续增加功能数量。

本轮执行顺序确定为：

1. Open VSX（**✅ 2026-09-07 已发布上线**，见 `OPEN_VSX_PUBLISH_PLAN.md`）；
2. 独立的 GitHub Action / GitHub Marketplace 入口；
3. `awesome-python`；
4. `awesome-security` 或 `awesome-devsecops`（择一尝试）；
5. AlternativeTo；
6. 为 stdio MCP 准备 MCPB 后评估 Smithery；
7. 等有真实用户信号后，再做 Product Hunt 发布。

## free-for.dev 判断

暂不提交。`free-for.dev` 的贡献指南将项目定义为面向开发者、有免费层的 SaaS
服务，并要求使用 PR 模板；它不是普通的免费软件或 CLI 目录，还明确拒绝 AI
生成的提交：

<https://github.com/ripienaar/free-for-dev/blob/master/CONTRIBUTING.md>

当前 pyobfus 是本地 CLI、PyPI 包和 stdio MCP server，Pro 试用不构成 SaaS
免费层。为了收录而增加在线源码上传/混淆服务会引入隐私、滥用和运维风险，也会
偏离“本地处理、可验证、不上传源码”的定位。只有未来真正提供隐私边界清晰的
托管服务，才重新评估该渠道。

## 渠道评估

### Open VSX：优先级高 — ✅ 已完成（2026-09-07 发布上线）

> **结果**：`zhurong2020.pyobfus` v0.4.2 已发布，
> <https://open-vsx.org/extension/zhurong2020/pyobfus> 页面与 API 均复核 HTTP
> 200。下面是本轮调研时的原始判断，保留不改。

已有 VS Code Marketplace 扩展，发布到 Open VSX 可以覆盖 VSCodium、Eclipse
Che、Gitpod 及其他使用 Open VSX 的环境。官方发布文档支持维护者用 `ovsx`
发布，并说明平台可能执行密钥、恶意文件和名称相似度扫描：

<https://github.com/eclipse-openvsx/openvsx/wiki/Publishing-Extensions>

第一阶段只做发布前审计、打包和人工检查；需要 Eclipse 账号、Publisher
Agreement 和 token 的外部发布仍由维护者手工完成。

（后续：维护者当日即完成了外部发布，队列因此推进到第 2 项 GitHub Action。）

### GitHub Action / Marketplace：优先级高

建议建立独立的 `pyobfus-action` 仓库，而不是把 Action 元数据混入当前多包仓库。
Action 应覆盖 `--check`、SARIF、`--verify-syntax` 和 provenance，而不只是一个
简单的混淆命令。GitHub 官方要求公开仓库提供 `action.yml`/`action.yaml`，通过
Release 发布到 Marketplace：

<https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace>

### awesome-python：中高优先级

这是 Core 最匹配的著名列表。其规则优先使用 PyPI 包名和 GitHub 仓库链接，收录
判断主要参考 PyPI 下载量并保留维护者编辑判断：

<https://github.com/vinta/awesome-python/blob/master/CONTRIBUTING.md>

应以“AST-based Python source protection、framework presets、reverse stack-trace
mapping、verified build/provenance”描述，避免把 Pro 专属能力写成 Community
默认能力。

### awesome-security / awesome-devsecops：可尝试一次

pyobfus 属于源码保护和交付前安全工具，但不是传统漏洞扫描器。只有在明确匹配
Development、Runtime Application Self-Protection 或 CI/CD Security 分类时才
提交，且最多人工尝试一次，不为列表徽章修改产品行为。

参考：

- <https://github.com/sbilly/awesome-security>
- <https://github.com/tysoncung/awesome-devsecops>

### AlternativeTo：低成本尝试

AlternativeTo 允许用户提交软件，也允许将其作为其他软件的替代品。可建立
pyobfus 与 PyArmor、SOURCEdefender 等工具的诚实对比，但应标注它是 CLI/library，
而不是 native compiler 或完整打包器：

<https://alternativeto.net/faq/>

### MCP 分发：Smithery 作为后续入口

MCP Registry 已经是正式元数据入口；Smithery 还能提供分发页面和使用分析。其
官方文档支持远程 URL，也支持本地 stdio MCPB bundle：

<https://smithery.ai/docs/build/publish>

当前不为 Smithery 改造为远程服务，先研究 MCPB 打包和本地安装流程。

### 暂不投入

- OpenSourceAlternative.to：要求项目是可 self-hosted 的开源商业替代品，当前 CLI
  匹配度不足。
- SourceForge：会增加镜像制品和 provenance 管理面，当前 PyPI/GitHub 已足够。
- 批量低活跃 awesome-list：链接数量不等于目标用户。
- 在线混淆 SaaS：与当前隐私和本地可验证定位冲突。
- Product Hunt：保留为一次完整产品发布，不作为普通目录提交。

## 验收原则

每个新增渠道都要记录真实 URL、提交日期、版本、审核结果和可归因指标；不把
展示量、发布日下载峰值或目录徽章直接解释为真实采用。所有提交材料必须人工
复核，尤其是 free-for.dev 明确禁止 AI 生成贡献。
