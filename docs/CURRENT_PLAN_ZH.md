# pyobfus 当前计划

更新时间：2026-08-20（0.5.15 发布 + Glama 第三方独立复现证据后刷新）

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

- 主包：`pyobfus 0.5.15` 已发布（2026-08-20）——`--check` 新增
  `compatibility_advisory` 类别（P2-29，import-hook/加密文件生态、编译打包、
  model-serving 三类交付组合）+ 三篇 cookbook + 两个 `examples/` 端到端复现。
  距上次发布（0.5.14，08-17）3 天，符合"1-2 天间隔、不批量"的节奏。发布前
  修复了一个已经让 main CI 红了约 19 小时的 black 格式化回归（P2-29 提交里
  `tests/test_preflight.py` 多了一个尾随空行），README"What's new"横幅这次
  与版本号/CHANGELOG 在同一提交里更新（吸取 0.5.14 那次教训）。
- MCP 包：`pyobfus-mcp 0.3.6` 已发布（2026-08-17），MCP Registry 同步发布，
  `isLatest=true` 已核实。
- VS Code 扩展：`0.4.0` 已 tag + GitHub Release 发布，**Marketplace 手工上传
  也已由用户完成**（`curl` 核实公开 listing 已返回 `"version":"0.4.0"`）。
- Glama admin「Build steps」已由用户手工改到 `pyobfus-mcp==0.3.6`，但触发的
  新构建 15 分钟后失败（`ECONNRESET`，卡在拉取 base image 这一步，是第二个
  独立复现实例，非我方问题）——详见下方 P0 小节。
- GitHub：主分支健康，当前公开 issues/PRs 为 0，CI/CodeQL 全绿。
- README/`llms.txt`/两个 `pyproject.toml`/`server.json` 的 AI 客户端定位
  文案已补 GitHub Copilot + CodeBuddy（实时搜索核实后添加，非训练记忆），
  README tagline 结尾改成"any MCP-compatible AI agent"泛称。
- ✅ **v0.5.14 那次 PyPI description 落后一个版本的问题已随 0.5.15 自然翻新**
  （新包快照带上了正确的 README 横幅），流程教训已固化进 `CLAUDE.md` 发布
  流程清单（README 横幅须在打 tag 前的同一提交里更新），0.5.15 发布时已
  实际验证生效，不再是待办。
- 近期下载（2026-08-20 发布前快照，pypistats.org）：`pyobfus` day/week/
  month `26 / 295 / 1,912`；`pyobfus-mcp` `8 / 124 / 687`。较 08-17 安静基线
  （`9/206/1,870` / `0/46/581`）周环比明显上升（pyobfus +43%，mcp +170%），
  但按历史经验（发布后 1-3 天的跳变多为 CI/依赖解析噪音），暂不当作真实
  有机增长信号——下次复查时对比是否回落。
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
   - **2026-08-17 证据**：mcp 0.3.6 发布后照惯例重新 pin Build steps，
     触发的新构建（`01a00e39-...`）15 分钟后失败，`ECONNRESET`/"aborted"，
     卡在拉取 `debian:trixie-slim` 基础镜像元数据这一步——与 08-07 那次失败
     （`context deadline exceeded`，同一卡点）是**第二个独立复现实例**，
     错误签名不同但卡点相同，指向 Glama 构建集群拉取该 base image 的网络层
     问题，与 pyobfus-mcp 包/配置无关（Build steps 已确认正确显示
     `pyobfus-mcp==0.3.6`）。
   - **2026-08-20 第三方独立复现（不是我们自己的数据点）**：user 转发
     Glama `#support` 频道全文，至少 3 位其他 maintainer（Considus/Andrei
     Lungeanu/ojkingston）报了完全相同的 `debian:trixie-slim` 构建卡点和
     错误签名，累计 5+ 个互不相关的 server 撞到同一故障；另有 maintainer
     （mellowmelomel/nolpak14/Cabal_hunter）独立报了与我们完全一致的
     "页面工具正常、公开 API 却 `tools: []`/字段陈旧"症状。两点均坐实此前
     判断——纯 Glama 平台侧构建基础设施 + 目录同步层问题，与 pyobfus-mcp
     包/配置无关，继续不需要我方改代码。Frank/Glama team 对频道内所有报告
     （含我们的两条）都尚未回复，看起来在处理积压，**用户决定不主动追发
     消息**。详见 memory `glama_zero_tools_repro_2026-08-07.md`。

2. Claude plugin marketplace
   - 2026-08-20 user 再次核实 Console 页面：仍为 `Submitted and pending
     review`，日期 Aug 2，提交描述里的 `protected_project` typo 也仍在。
   - 后续每轮外部状态检查只需确认是否出现 approve / reject / 补充信息。
   - 如 Anthropic 给出修改入口，再顺手修 `protected_project` typo 为
     `protect_project`。

### ✅ 已发布（原 P1/P2 打磨项，2026-08-17 三包发版后收口）

1. `P2-25` VS Code trace/config workflow polish — **已发布于 `vscode-extension`
   0.4.0**（tag + GitHub Release + Marketplace 手工上传均已完成，`curl` 核实
   公开 listing 已返回 `"version":"0.4.0"`）。
     - Reverse Stack Trace 利用 `--trace-marker` 自动定位 mapping 文件。
     - Reverse Stack Trace 复用共享 CLI 错误提示；旧版 pyobfus / 解释器错误现在
       给出和 obfuscate / generate-config 一致的 Upgrade / Select Interpreter
       动作入口。
     - Obfuscate with pyobfus 识别配置 unknown-key 错误，并提供打开自动发现的
       `pyobfus.yaml` 动作入口。
     - Core `pyobfus --validate-config --json`（`pyobfus` 0.5.14 已发布）已有
       稳定 JSON contract。
     - VS Code 已新增 `pyobfus: Validate pyobfus.yaml`，基于 JSON contract 显示
       validation 摘要，并把错误/警告写入 pyobfus output channel。
   - 该轮 trace/config polish 已可收束；除非实际使用发现新痛点，不继续扩大
     VS Code scope。
   - 原则：只做小而确定的 UX 改善，不改变 core 语义。

2. `P2-28` MCP Registry / `server.json` schema hardening — **已发布于
   `pyobfus-mcp` 0.3.6**（PyPI + MCP Registry，`isLatest=true` 已核实）。
   - 用官方 `2025-12-11` schema 重新验证 `pyobfus_mcp/server.json`，并补充
     GitHub repository stable ID `1093960892`。
   - `fileSha256` 暂不补：PyPI 有 wheel/sdist 多 artifact，填错单一 hash 比不填
     可选 hash 风险更高。
   - 已明确 HTTP OAuth / Server Card 对当前 stdio server 不适用。
   - 新增 `test_version_metadata.py` 回归测试，防止版本号三处（`__init__.py`/
     `pyproject.toml`/`server.json`）再次漂移。
   - ✅ Glama admin「Build steps」字段已由用户手工改成 `0.3.6`（确认无误），
     但触发的新构建随后失败（`ECONNRESET`，Glama 自家基础设施问题，非我方
     配置问题）——详见 P0 小节。

3. `P2-26` obfuscated-output SBOM + provenance manifest — **已发布于
   `pyobfus` 0.5.14**。
   - 在现有 `--provenance-manifest` 基础上扩展：manifest 保留原字段和
     integrity digest，同时新增 input SHA-256、可用时的 git commit，以及
     CycloneDX-compatible `cyclonedx` 子结构（file components + input/output/
     mapping relationships）。
   - 用户文档已补 `docs/PROVENANCE_MANIFEST.md`，README / `llms.txt` 已同步。
   - CLI 已新增 `--verify-provenance-manifest`，可校验 pyobfus manifest shape、
     CycloneDX-compatible relationships 和本地 integrity digest，并支持 JSON 输出。
   - 当前先不扩独立 `--sbom` 入口；只有当用户或外部工具明确需要 standalone
     CycloneDX 文件时，再单独开后续项。
   - 价值：竞品能保护代码/数据，但通常不给"被保护产物"的供应链记录。
   - 口径：这是 provenance / reproducibility / tamper-evidence，不是"证明代码可信"。

4. `P2-27` attestation verification helper / trust report — **docs-first 已发布**
   （新增 `docs/RELEASE_PROVENANCE_VERIFICATION.md`）。
   - 2026-08-17 三包发版后已重新核实：PyPI JSON API 最新版本
     `pyobfus 0.5.14`、`pyobfus-mcp 0.3.6`；四个最新 wheel/sdist 的 PyPI
     Integrity API provenance endpoint 均返回真实 `HTTP 200`（非文本平移）。
   - 文档给出 `pypi-attestations verify pypi` 的完整验证口径；当前不手写
     sigstore / DSSE 校验逻辑。
   - 输出要诚实：证明发布身份和产物 digest，不证明代码没有漏洞或恶意。

### ✅ P1：`P2-29` compatibility checks — 已发布于 `pyobfus` 0.5.15（2026-08-20）

针对真实交付组合补诊断与文档，**未新增任何 transform**（遵守"明确不做"）。

- **`--check` 新增 `compatibility_advisory` 类别**（`pyobfus/core/preflight.py`，
  severity `low`/`info`，不改动 `exit_code` 语义，不阻塞 CI）。自动流入 VS Code
  红线（`diagnosticsProvider.ts` 消费 `Risk` contract，`low→Information`/
  `info→Hint`）与 MCP `check_obfuscation_risks` 工具（包裹 `PreflightChecker`）——
  **VS Code / MCP 无需改代码**。
  - import-hook / 加密文件生态：`import sourcedefender`、`.pye` 字面量、
    `sys.meta_path` 赋值/变更、`importlib.abc` 子类。
  - 编译打包：`import nuitka` / `import Cython` / `.pyx` 字面量。
  - model-serving：检测到 `ml` preset 时追加一条 `info` 级建议，指向保留
    mapping 做反向栈追踪。
- **三篇 cookbook**（`docs/`）：`IMPORT_HOOK_COOKBOOK.md`、
  `COMPILED_PACKAGING_COOKBOOK.md`、`MODEL_SERVING_COOKBOOK.md`，沿用
  `PYINSTALLER_COOKBOOK.md` 的 compose-not-compete 格式。
- **两个端到端复现示例**（`examples/`，参考性、不进 pytest）：
  `examples/import_hook/`（标准库自定义 import hook，无需付费依赖即可跑通）、
  `examples/compiled_packaging/`（Cython，免费）。
- 回归测试：`tests/test_preflight.py` 新增 9 条 `compatibility_advisory` 用例。
- 后续机会（未并入本轮）：`--check` 接入已配置 `--config` / `exclude_patterns`
  以减少真实组合的误报，属独立行为改动，留作单独小项。

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

1. `pyobfus 0.5.15` 已发布并核实 PyPI latest；main CI 已从 P2-29 提交带来
   的 black 格式化回归中修复转绿。本轮无遗留的本地机械任务。
2. `P2-29` compatibility checks 已发布收口。后续若有真实用户反馈新的交付
   组合（如 PyInstaller 之外的 bundler、其他 import-hook 产品），再机会性
   扩检测信号或补 cookbook，仍遵守"优先诊断 + 文档、不新增 transform"。
3. Glama：2026-08-20 已有多位第三方 maintainer 独立复现我们报告过的两个
   症状（构建卡 `debian:trixie-slim`、页面正常但公开 API `tools: []`），
   进一步确认是 Glama 平台侧问题。继续被动等 `#support` 回复，不主动追发
   消息、不改代码。下次冷启动检查：① 两条帖子有没有回复；② `curl` 复查
   `tools` 字段；③ Recent Tests 有没有新构建尝试。
4. Claude plugin marketplace：仍 `Submitted and pending review`（Aug 2），
   只需确认是否出现 approve/reject/补充信息。
5. 下载量：0.5.15 发布后建议按"周期性发布后复盘节奏"再等几天采一次快照，
   对比 08-20 发布前的读数（`pyobfus` 26/295/1,912；`pyobfus-mcp`
   8/124/687）是否回落，判断是否为真实趋势而非发布噪音。
