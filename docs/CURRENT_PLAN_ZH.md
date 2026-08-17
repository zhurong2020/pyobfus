# pyobfus 当前计划

更新时间：2026-08-17

这份文档是当前项目状态和后续计划的中文单一入口，面向维护者日常查看。旧的
`ROADMAP.md` 和 `POST_V0.4_TODO.md` 保留为历史归档和详细来源，但后续日常
决策优先看本文。

## 一句话定位

pyobfus 是面向 AI 辅助开发时代的 Python 代码保护工具：保留纯 Python / AST
工作流、框架兼容、反向栈追踪映射、结构化 JSON CLI、MCP/VS Code 集成，并用
可验证的供应链与工具完整性证据建立信任。

核心策略不是追 PyArmor / Nuitka 的 native / bytecode VM 赛道，而是在
“可调试、可验证、可被 AI 工具正确使用”的代码保护工作流上拉开差距。

## 当前状态

- 主包：`pyobfus 0.5.13` 已发布。
- MCP 包：`pyobfus-mcp 0.3.5` 已发布。
- VS Code 扩展：`0.3.0` 已发布到 Marketplace。
- GitHub：主分支健康，当前公开 issues/PRs 为 0。
- 近期下载：`pyobfus-mcp` 最新成功刷新为 day/week/month `2 / 67 / 598`；
  `pyobfus` 最近一次刷新触发 pypistats 429，沿用同日稍早成功快照
  `30 / 324 / 1,847`。
- 外部分发状态：
  - Glama 旧公开 API 路径
    `/api/mcp/v1/servers/io.github.zhurong2020/pyobfus-mcp` 当前返回
    `not_found`；公开页面 `/mcp/servers/zhurong2020/pyobfus` 仍可打开，页面内
    可解析到 8 个工具名。下一步不是改 pyobfus-mcp 代码，而是确认 Glama 当前
    推荐的 public API / listing 查询路径，并在 Discord `#support` 跟进旧路径
    失效或同步状态。维护者 2026-08-17 手工复核对应 Discord 频道：暂未看到
    Glama 回复，本轮跳过，等待外部反馈或下一次周期复查。
  - Claude plugin submission 已由维护者在 Console
    `/plugins/submissions` 于 2026-08-17 手工复核：`pyobfus` 仍为
    `Submitted and pending review`，日期 Aug 2；提交描述里的
    `One-call protected_project workflow` typo 仍存在，继续机会性修复，不为
    typo 单独重提。

## 已完成的关键能力

### Community / Core

- `--check` 风险扫描：eval/exec、动态属性、框架反射等。
- `--init` 自动生成 `pyobfus.yaml`。
- `--unmap` 反向映射 obfuscated stack trace。
- `--trace-marker` 在输出文件里写入可恢复提示，帮助 AI 或开发者找到 mapping。
- 全局 `--json`，适合 CLI、MCP、IDE 可靠调用。
- 框架预设：FastAPI、Django、Flask、Pydantic、Click、SQLAlchemy、ML。
- `--strip-ai-artifacts`、`--numeric-obfuscation`、`--provenance-manifest`。

### Pro

- Selective Opacity、Runtime String Vault、forensic watermarking。
- device/expiry/period license binding。
- `--seal-code`、`--scrub-traceback` / `pyobfus-unscrub`。
- import obfuscation、embedded encrypted data、runtime policy、anti-debug。

### AI / IDE / MCP

- `pyobfus-mcp` 暴露 8 个工具，返回稳定 JSON contract、`ai_hint` 和
  `next_tool`。
- MCP tool-description integrity：`pyobfus-mcp-verify`。
- VS Code 扩展已支持风险诊断、反向栈追踪、生成配置、右键 obfuscate、
  Pro trial/unlock funnel、`pyobfus.yaml` IntelliSense。
- 2026-08-14 起，VS Code 的 Reverse Stack Trace 流程开始利用 trace marker
  的 `mapping=...` 提示来定位 mapping 文件选择器。

## 竞品与最佳实践判断

### 竞品现状

- PyArmor 9.2.x 继续加深 RFT / BCC / JIT / Themida / VMC / ECC / runtime
  assert / mix-str 路线，优势是 bytecode/native/runtime 不透明交付。
- Nuitka Commercial 强调 data hiding、protected data files、encrypted output、
  traceback encryption、compiled delivery。其 traceback encryption 当前仍是对称
  加密，并称未来计划支持非对称。
- SOURCEdefender 是 `.pye` import-hook 加密产品，AES-256、TTL、PyInstaller
  bundling，偏 opaque encrypted-file delivery。

这些产品验证了“更强 runtime/data protection”有需求，但它们主线不是
AI-debuggable workflow。pyobfus 不应把 v0.6 的主目标变成模仿 native VM 或
bytecode 加密。

### 国际最佳实践

- PyPI PEP 740 / Integrity API 让 release provenance 成为公开信任面。
- PyPI 自己也明确：attestation 证明包从哪里来，不证明代码一定可信。
- PEP 770 建议 SBOM 使用 CycloneDX 或 SPDX，优先 UTF-8 JSON，包含创建时间、
  creating tool、主组件、组件关系和软件标识。
- CycloneDX CLI 已支持 validate、sign、verify、convert、diff、merge、add files。
- MCP 2026-07-28 方向是 stateless core、cacheable list results、header routing、
  auth hardening。
- MCP Authorization 仍明确区分：HTTP transport 才走 OAuth；stdio server 应从
  环境拿凭据，不应照搬 HTTP OAuth。
- MCP Registry `server.json` schema 越来越重视 repository ID、package hash、
  exact version、命令参数注入风险等 trust metadata。

## 后续优先级

### P0：外部状态继续跟进

1. Glama public API / listing 状态
   - 2026-08-17 手工复核 Discord 对应频道：暂未看到 Glama 回复。
   - 继续在 Glama Discord `#support` 等待 / 跟进，但本轮不阻塞本地工作。
   - 每次冷启动同时检查旧 API 路径和公开页面能否列出 8 个工具。
   - 找到 Glama 当前推荐 API 后，替换旧的 `tools: []` 检查口径。
   - 不为 Glama 单独改 pyobfus-mcp 代码，除非 Glama 给出可复现的本地问题。

2. Claude plugin marketplace
   - 2026-08-17 已复核：仍为 `Submitted and pending review`，日期 Aug 2。
   - 后续每轮外部状态检查只需确认是否出现 approve / reject / 补充信息。
   - 如 Anthropic 给出修改入口，再顺手修 `protected_project` typo 为
     `protect_project`。

### P1：短周期打磨

1. `P2-25` VS Code trace/config workflow polish
   - 当前 active。
   - 已完成：
     - Reverse Stack Trace 利用 `--trace-marker` 自动定位 mapping 文件。
     - Reverse Stack Trace 复用共享 CLI 错误提示；旧版 pyobfus / 解释器错误现在
       给出和 obfuscate / generate-config 一致的 Upgrade / Select Interpreter
       动作入口。
     - Obfuscate with pyobfus 识别配置 unknown-key 错误，并提供打开自动发现的
       `pyobfus.yaml` 动作入口。
   - 下一项候选：若继续 VS Code 小修，优先补 `--validate-config` JSON contract，
     再接入真正的 config validation 命令；避免在扩展里解析文本输出。
   - 原则：只做小而确定的 UX 改善，不改变 core 语义。

2. `P2-28` MCP Registry / `server.json` schema hardening
   - 本轮已完成本地处理：用官方 `2025-12-11` schema 重新验证
     `pyobfus_mcp/server.json`，并补充 GitHub repository stable ID
     `1093960892`。
   - `fileSha256` 暂不补：PyPI 有 wheel/sdist 多 artifact，填错单一 hash 比不填
     可选 hash 风险更高。
   - 已继续明确 HTTP OAuth / Server Card 对当前 stdio server 不适用。

### P2：下一项实质功能

1. `P2-26` obfuscated-output SBOM + provenance manifest
   - 在现有 `--provenance-manifest` 基础上扩展。
   - 输出 CycloneDX-compatible manifest，包含：
     - pyobfus 版本
     - git commit（如可用）
     - config hash
     - input/output file hash
     - mapping digest
     - artifact relationship metadata
   - 价值：竞品能保护代码/数据，但通常不给“被保护产物”的供应链记录。
   - 口径：这是 provenance / reproducibility / tamper-evidence，不是“证明代码可信”。

2. `P2-27` attestation verification helper / trust report
   - docs-first 或小 CLI。
   - 通过 PyPI Integrity API 或 `pypi-attestations` 验证 pyobfus / pyobfus-mcp 的
     release provenance。
   - 输出要诚实：证明发布身份和产物 digest，不证明代码没有漏洞或恶意。

3. `P2-29` compatibility checks
   - 针对真实交付组合补诊断和文档。
   - 已有 PyInstaller cookbook。
   - 后续关注 import-hook/encrypted-file ecosystem、compiled packaging、
     model-serving layout。
   - 优先 `--check` / VS Code / MCP 诊断和 cookbook，不默认新增 transform。

### P3：探索项

1. `P3-1` `--output-pyc` feasibility spike
   - 只做 spike，不承诺产品化。
   - 退出标准：
     - 是否明显提高 decompilation resistance；
     - 是否保留 mapping/unmap 和 traceback debugging；
     - 是否破坏框架反射兼容；
     - 是否影响 PyInstaller / packaging；
     - 是否只是低质量模仿 PyArmor/SOURCEdefender。

2. `P3-2` hosted/remote MCP endpoint
   - 等 Glama / Claude 外部分发稳定后再考虑。
   - 如做，只先暴露 read-only / side-effect-free tools。
   - 必须有 rate limit、audit log、无 token passthrough。
   - 不牺牲本地 stdio MCP 的可靠性。

## 明确不做

- 不把 PyArmor-style BCC/JIT/Themida/VMC 作为 v0.6 主线。
- 不把 attestation / manifest 宣传成“代码可信证明”。
- 不为当前 stdio MCP server 实现 HTTP OAuth / Server Card / hosted connector。
- 不做 anti-VM / sandbox-evasion 类能力，避免工具定位被污染。
- 不做云端 obfuscation-as-a-service，避免破坏隐私定位。
- 不做复杂企业 license server；可保留 Cloudflare Worker / recipe 级参考。

## 下次工作建议

1. 若还要继续 VS Code 小打磨，先给 core `--validate-config` 增加 JSON contract。
2. 若外部分发仍无进展，但状态已稳定，就开始 `P2-26` SBOM/provenance 设计。
