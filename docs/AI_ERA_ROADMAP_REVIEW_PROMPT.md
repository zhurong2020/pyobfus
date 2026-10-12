# AI 时代路线图独立复核 Prompt

维护者可将下方文本直接交给有仓库访问与联网能力的 Claude Code。
如果在普通聊天中复核，应同时提供所列仓库文档和相关代码；未取得内容的部分须标为无法核实。
本任务仅调研／复核，可保存审查文档，不授权产品实现、发布、部署、付费模型运行或对外通信。

```text
请对 pyobfus 的增强路线图做一次独立、批判性的复核调研。
你是交叉审查者，不是为 Codex 的建议背书。可以否定、收窄、重排或提出更合适的方案。

工作区：~/projects/pyobfus，遵守 AGENTS.md，使用 WSL 和仓库 venv/。
先读取 git status 和当前提交，保留现有未提交修改，不自动 pull、合并、提交或推送。
若文档在当前工作区尚未提交，应直接读取工作区版本，不只读 GitHub。

已确定的维护者方向：
1. 下一阶段优先服务离线 Python 应用交付，商业 wheel／SDK 产品场景后置。
2. Community 必须保留完整基本混淆、本地检查、验证与调试，不设文件／行数收费门槛。
3. Pro 的商业价值是增强保护、更多受保护资产、运行／分发控制与买家归因。
4. Codex 建议用 Community 交付物检查／覆盖报告、Agent 重建实验、Pro 选择性保护和密钥交付补齐原路线。
5. 方向已经认可，但新增能力实施前必须完成本次独立复核，再由维护者确认范围。
   不改变当前 0.7.0 发布范围／节奏，不把这次复核当作功能实施授权。

必读入口（再按引用和代码扩展）：
- AGENTS.md
- docs/AI_ERA_PROTECTION_ROADMAP_2026-10-12.md（本次评审对象）
- docs/CURRENT_PLAN_ZH.md、docs/TODO.md、CHANGELOG.md
- docs/EDITION_BOUNDARY_POLICY.md、docs/PROJECT_STRUCTURE.md、docs/THREAT_MODEL.md
- docs/ROADMAP.md（已归档，仅追溯，不执行其历史规则）
- docs/LLM_RESISTANCE_BENCHMARK.md、docs/LLM_RESISTANCE_PILOT_RESULTS_2026-08-01.md
- benchmarks/llm_resistance/README.md 与 harness、attacker、conditions、executor、tests
- docs/OPACITY_CONFIG.md、docs/Y3_KEY_PROVIDER_DESIGN.md、docs/Y1_RUNTIME_DISTRIBUTION_DESIGN.md
- docs/VERIFIABLE_BUILD_REPORT.md、docs/COMPILED_PACKAGING_COOKBOOK.md
- docs/SELF_DOGFOODING_BEST_PRACTICES.md、docs/COMPARISON.md
- 对应 core/check/report、Pro build_fusion/opacity/vault/forensic 与 runtime 代码、测试和 CI

请完成以下工作：

A. 先审计现状
逐项判断路线图中描述的能力：已发布、已实现未发布、API 有但 CLI 不完整、纯候选。
以代码／测试／CHANGELOG／当前计划交叉核对，不照抄历史设计状态。
重点检查 runtime 独立分发、key provider 的 Vault 边界、opacity 四层 CLI 语义、
watermark 与外部 key binding 的组合，以及现有 report 能证明什么。
报告路径／行号或提交证据；没有复现实测时不要称已验证。

B. 独立外部调研
联网查找截至你实际检索日的一手资料，范围不限于公众号文章和 Codex 所列来源。
覆盖 AI 工具辅助逆向／黑盒重实现、相关评测研究、Python 保护与编译产品、
离线应用交付／密钥生命周期、可信构建与供应链、open-core 分层实践。
至少比较两种直接或相邻 Python 保护产品及一种可组合的外部工具方案。
不强求最新产品价格；若价格／版本／平台影响建议，务必核查并记录条件。
每条关键外部结论给一手链接、检索日期、版本／平台／许可档位（适用时），
区分厂商声明、研究范围和你自己的复现实验。无法访问的来源明确登记，不凭记忆补齐。
主动寻找反证：普通变换是否对 Agent 无效？外部密钥能抵御哪些权限？
运行时捕获或黑盒查询是否使原论证失效？类似产品为何选择不同架构？
不要把二进制／Android／其他语言结果直接外推到 Python，不把星数当需求或强度证据。

C. 评审每个候选
对交付物检查、覆盖报告、Agent benchmark、opacity 范围、Vault key provider、
资源保护和买家归因，分别回答：
- 用户／买家／具体触发场景是什么？需求证据与关键未知是什么？
- 与既有功能的增量在哪里？能否只用文档、fixture 或外部集成解决？
- 首版最小范围、技术依赖、支持目标、维护成本和验证方法是什么？
- 免费／Pro／混合的合理边界是什么？是否违反现有政策？
- 应立即设计、先实验、等待需求，还是放弃？什么证据会改变判断？
离线场景须讨论没有网络时的安装、授权、续期、密钥提供和错误诊断，
不能承诺即时远程撤销或运行时绝对保密，不能混淆构建器许可与客户应用许可。

D. 严审 Agent 实验设计
区分静态、可运行（未授权／已授权）、黑盒三种攻击权限，
检查原文对照、no-op、公开算法记忆、隐藏测试隔离、预算与重复次数。
提出成本可控的首轮矩阵和停止规则，分离研发证据与营销表述。
评测应衡量功能与提取结果、攻击成本及防御运行开销，不只看源码相似度。
本轮不要调用付费模型、上传私有源码或运行攻击生成代码；只提出协议与预算。
若建议复现实验，只使用维护的合成 fixture、隔离临时目录，绝不触碰真实 ~/.pyobfus。

输出要求：
1. 结论先行：通过／有条件通过／需重大修改／不建议推进，给出具体原因。
2. 按严重程度列问题（阻断、重要、建议）；每项附证据、影响和可操作修正。
3. 给“保留／收窄／推迟／替换／删除”对照表，不只堆新增功能。
4. 给 Community／Pro 分层表、最多三个近期优先事项及首个可验收实践。
5. 给明确解冻／停止条件和需要维护者决定的问题；已确认方向不反复询问。
6. 列来源与未验证假设，说明调研／实验覆盖范围，禁止把有限试验写成普遍保证。

将去标识的审查结果保存到：
docs/AI_ERA_PROTECTION_ROADMAP_REVIEW_CLAUDE_YYYY-MM-DD.md
（替换为实际日期，若已有同名文件先读并追加明确的新一轮记录）。
敏感下游／客户证据只进入 docs/internal/，公开报告不得含 PII、密钥、许可值或私有代码。
只写审查报告，不直接改路线图或产品代码，不提交／推送；由维护者与 Codex 讨论后再修订。
写文档后运行 scripts/check.sh 和 git diff --check；若环境或网络阻塞，记录未完成检查。
最终给我中文审查摘要、报告路径，以及你认为最值得先做的一项实践。
```
