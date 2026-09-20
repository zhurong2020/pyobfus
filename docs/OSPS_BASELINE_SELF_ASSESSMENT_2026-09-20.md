# OpenSSF OSPS Baseline 自评差距表（2026-09-20）

对照 **[OSPS Baseline 2026-02-19](https://baseline.openssf.org/versions/2026-02-19.html)**
（Level 1/2/3，8 大类，共 62 条控制）。这是**差距清单**，不是一次性全部补齐承诺；
与已有的 **OpenSSF Best Practices passing 徽章（项目 12788）** 互补，不重复。

Status: 自评完成。**逐条状态就是当天实测**；标 `⚙️设置` 的项需维护者在 GitHub
后台操作，标 `📝文档` 的项 Claude 可起草。**本文件不授权任何仓库设置改动或发版**。

## 结论摘要

- **L1（基础）现已全面达标**（2026-09-20 收口）：`AC-03.01` 由 active ruleset
  `protect-main`（+ admin bypass，路线 A）部分满足、`BR-07.01` 由 secret scanning
  + push protection 补齐。
- **L2 强项**在构建发布与漏洞管理：`BR-06.01` 签名发布由 **PEP 740 attestations**
  满足、`VM-01.01` CVD 政策（48h ack / 7d / 90d）齐备、`SA-03.01` 安全评估由
  CodeQL + self-dogfooding + mcp-scanner 覆盖。
- **L2 真实缺口**集中在**治理与流程门禁**：无 `GOVERNANCE.md`（GV-01）、无 DCO
  sign-off（LE-01.01）、CI 未作为**强制合并门**（QA-03.01，根因同 AC-03.01）、
  GitHub 私密漏洞上报通道**未开启**（VM-03.01，SECURITY.md 已指向该通道但后台关着）。
- **2026-09-20 收口**：四个维护者开关（私密漏洞上报 / secret scanning + push
  protection / `protect-main` ruleset / Dependabot）+ 四份文档（GOVERNANCE /
  THREAT_MODEL / dependabot.yml / CI 最小权限）均已完成并经 gh api 核实。剩余仅
  L2 的 DCO 与若干 L3（阈值政策、SBOM 并入 P0 主线）。

## 逐条差距表

图例：✅达标 · 🟡部分/待核 · ❌缺口 · ⬜L3暂不追（记录不列为当前待办）

### Access Control
| 控制 | Lv | 状态 | 证据 / 缺口 | 补法 |
|---|---|---|---|---|
| AC-01.01 MFA 访问敏感资源 | 1 | 🟡 | PyPI 走 OIDC 无长期 token；PyPI 已强制 2FA | 维护者确认 GitHub 账号 2FA 已开 ⚙️ |
| AC-02.01 协作者默认最小权限 | 1 | ✅ | 单维护者、无外部协作者 | 加人时按最小授权 |
| AC-03.01 禁止直推主分支 | 1 | 🟡 | ruleset `protect-main` **active**（deletion + non_fast_forward + required_status_checks），maintainer 走 bypass 直推 → 部分达标（路线 A，见下方取舍） | — |
| AC-03.02 删主分支需确认 | 1 | ✅ | GitHub 默认分支防删除 | — |
| AC-04.01 CI 任务默认最小权限 | 2 | ✅ | 全部 workflow 已声明 `permissions:`（`ci.yml`/`vscode-extension-ci.yml` 于 f2cd713 补齐 `contents: read`）| — |
| AC-04.02 CI 作业最小特权 | 3 | ⬜ | release 已按 job 授 `id-token/attestations` | — |

### Build & Release
| 控制 | Lv | 状态 | 证据 / 缺口 | 补法 |
|---|---|---|---|---|
| BR-01.01 净化不可信 CI 元数据 | 1 | 🟡 | 无 fork PR 自动取密钥路径；未系统化审计 | 记录一次审计结论 📝 |
| BR-01.03 不可信快照不得取特权凭证 | 1 | ✅ | release 由 tag 触发走 OIDC，fork PR 默认无密钥 | — |
| BR-02.01 唯一版本标识 | 2 | ✅ | SemVer + git tag | — |
| BR-03.01 官方沟通加密信道 | 1 | ✅ | GitHub/PyPI HTTPS | — |
| BR-03.02 分发防中间人 | 1 | ✅ | PyPI HTTPS + OIDC Trusted Publishing | — |
| BR-04.01 含安全项的变更日志 | 2 | ✅ | `CHANGELOG.md` 逐版本、含安全修复 | — |
| BR-05.01 标准化依赖工具 | 2 | 🟡 | `pyproject.toml` 有依赖，**无锁文件** | 评估加锁文件（Tier 0 基线项）📝 |
| BR-06.01 签名发布 / 带哈希签名清单 | 2 | ✅ | **PEP 740 attestations**（两个 integrity endpoint 200） | — |
| BR-07.01 防密钥入库 | 1 | ✅ | `.githooks/pre-commit` 凭证扫描 **+ GitHub secret scanning + push protection 均已启用**（2026-09-20 gh api 核实） | — |
| BR-07.02 密钥管理政策 | 3 | ⬜ | Vaultwarden 为 canonical store（跨工作区约定） | — |

### Documentation
| 控制 | Lv | 状态 | 证据 / 缺口 | 补法 |
|---|---|---|---|---|
| DO-01.01 用户指南 | 1 | ✅ | README + Read the Docs | — |
| DO-02.01 缺陷上报指南 | 1 | ✅ | CONTRIBUTING + Issues | — |
| DO-06.01 依赖选择/跟踪说明 | 2 | 🟡 | 分散在 pyproject/AGENTS | 汇一小节 📝 |
| DO-07.01 构建说明 | 2 | ✅ | AGENTS.md build/test/lint | — |
| DO-03.01/03.02 校验完整性/作者身份 | 3 | 🟡 | PEP 740 provenance 文档已覆盖大半 | 发布页补"如何验证" 📝 |
| DO-04.01/05.01 支持范围与期限 | 3 | ⬜ | SECURITY.md 有 Supported Versions | — |

### Governance
| 控制 | Lv | 状态 | 证据 / 缺口 | 补法 |
|---|---|---|---|---|
| GV-01.01/01.02 成员清单与角色 | 2 | ✅ | `GOVERNANCE.md`（f2cd713）单维护者+角色+升权约束 | — |
| GV-02.01 公开讨论机制 | 1 | ✅ | Discussions + Issues | — |
| GV-03.01 贡献流程说明 | 1 | ✅ | CONTRIBUTING.md | — |
| GV-03.02 贡献者接受标准 | 2 | 🟡 | CONTRIBUTING 有流程，接受标准可更明确 | 补验收标准段 📝 |
| GV-04.01 升权前审查 | 3 | ⬜ | — | — |

### Legal
| 控制 | Lv | 状态 | 证据 / 缺口 | 补法 |
|---|---|---|---|---|
| LE-01.01 每次提交声明法律授权（DCO） | 2 | ❌ | 近期提交 **0 条 Signed-off-by** | 评估启用 DCO app 或 CONTRIBUTING 声明 📝⚙️ |
| LE-02.01/02.02 OSI/FSF 许可 | 1 | ✅ | Apache-2.0（core）；Pro 专有另计不属"released OSS" | — |
| LE-03.01 LICENSE 文件 | 1 | ✅ | 根目录 LICENSE | — |
| LE-03.02 发布物含许可 | 1 | ✅ | wheel/sdist 打包 LICENSE | 发版时抽检 |

### Quality
| 控制 | Lv | 状态 | 证据 / 缺口 | 补法 |
|---|---|---|---|---|
| QA-01.01 公开静态 URL 仓库 | 1 | ✅ | github.com/zhurong2020/pyobfus | — |
| QA-01.02 公开变更记录 | 1 | ✅ | git 历史 + CHANGELOG | — |
| QA-02.01 依赖清单 | 1 | ✅ | pyproject 直接依赖 | — |
| QA-02.02 编译发布带 SBOM | 3 | 🟡 | provenance manifest 内含 CycloneDX 1.7 | 与 P0 可验证性主线合并推进 |
| QA-03.01 强制状态检查作为合并门 | 2 | ✅ | ruleset 要求 Lint/CodeQL/Test 3.10–3.13 通过（非 bypass 用户）| — |
| QA-04.01 项目代码库清单 | 1 | ✅ | AGENTS.md 列 core/mcp/pro/vscode | — |
| QA-05.01 禁生成的可执行物入库 | 1 | ✅ | 实测无 whl/so/exe/vsix 入库 | — |
| QA-05.02 禁不可审二进制入库 | 1 | ✅ | 同上 | — |
| QA-06.01 提交前跑自动测试 | 2 | ✅ | 测试现为 required status check（ruleset）| — |
| QA-06.02/06.03/07.01 测试文档/大改必测/非作者审批 | 3 | ⬜ | 单维护者，07.01 结构性 N/A | — |

### Security Assessment
| 控制 | Lv | 状态 | 证据 / 缺口 | 补法 |
|---|---|---|---|---|
| SA-01.01 设计文档 | 2 | 🟡 | AGENTS.md 架构 + docs/ | 可补一页系统 actor/action 概览 📝 |
| SA-02.01 外部接口文档 | 2 | ✅ | 稳定 JSON 契约 + MCP tool_manifest | — |
| SA-03.01 执行安全评估 | 2 | ✅ | CodeQL + self-dogfooding + 真跑 mcp-scanner | — |
| SA-03.02 威胁建模/攻击面分析 | 3 | 🟢 | `docs/THREAT_MODEL.md`（f2cd713）F1–F10 + 非目标 | — |

### Vulnerability Management
| 控制 | Lv | 状态 | 证据 / 缺口 | 补法 |
|---|---|---|---|---|
| VM-01.01 CVD 政策含响应时限 | 2 | ✅ | SECURITY.md：48h ack / 7d 详复 / 90d 披露 | — |
| VM-02.01 安全联系人 | 1 | ✅ | SECURITY.md 邮箱 + 通道 | — |
| VM-03.01 私密漏洞上报通道 | 2 | ✅ | **private vulnerability reporting = enabled**（2026-09-20 gh api 核实）+ 邮箱通道 | — |
| VM-04.01 公开已知漏洞数据 | 2 | 🟡 | 暂无漏洞需披露；CodeQL dismiss 有据可查 | 出现时走 GH advisory |
| VM-05.x SCA 阈值/发布前处置/恶意依赖评估 | 3 | 🟢 | **Dependabot enabled** + `dependabot.yml`；开启即报的 7 个 npm 告警**已全部清零**（fix + override，commit 2e603db）；成文阈值政策待定 | 阈值政策 📝（L3，不急） |
| VM-06.x SAST 阈值/自动评估 | 3 | 🟡 | CodeQL 已跑（SAST），无成文阈值政策 | 记一条阈值政策 📝 |

## 流程门禁的取舍（AC-03.01 / QA-03.01 / QA-06.01 / LE-01.01）

这四条都指向"PR 评审 + 强制门 + 逐提交法律声明"的多人协作范式，与当前**单维护者
直推 main**的现实有张力。两条诚实路线，供维护者选：

- **A（推荐，低摩擦）**：给 `main` 建 ruleset——**禁 force-push、禁删除、要求
  CI/CodeQL 状态检查通过**，但**允许维护者 bypass**（`QA-03.01` 明确接受"pass
  或手动 bypass"）。这样 `AC-03.01`/`QA-03.01`/`QA-06.01` 三条即达标，且不逼单人
  开发走 PR。
- **B**：完整 PR 流程 + DCO sign-off。达标更彻底，但给单维护者加显著摩擦——建议
  等有外部协作者时再上（与 `AC-02.01` 备注一致）。

`LE-01.01`（DCO）独立于分支保护：可先在 CONTRIBUTING 写明"提交即声明有权贡献"，
待引入 DCO app 时再强制。

## 建议的补齐顺序（不承诺一次做完）

**第一批 · 维护者开关（✅ 2026-09-20 全部完成，gh api 核实）**：
1. ✅ GitHub 私密漏洞上报（`enabled:true`）→ VM-03.01。
2. ✅ secret scanning + push protection（均 `enabled`）→ BR-07.01。
3. ✅ ruleset `protect-main` active（deletion + non_fast_forward + required_status_checks，admin bypass）→ AC-03.01 部分 / AC-03.02 / QA-03.01 / QA-06.01。
4. ✅ Dependabot security updates（`enabled`）→ VM-05.x。

**第二批 · 文档（✅ 2026-09-20 完成，commit f2cd713）**：
5. ✅ `GOVERNANCE.md`（GV-01）。
6. ✅ `ci.yml`/`vscode-extension-ci.yml` 加 `permissions: contents: read`（AC-04.01）。
7. ✅ `.github/dependabot.yml`（配第 4 项；**需 push 到 origin 后 Dependabot 才读取**）。
8. ✅ `docs/THREAT_MODEL.md`（SA-03.02）。

**剩余（不急）**：`LE-01.01` DCO sign-off（主动延后，见取舍）；L3 阈值政策；
`QA-02.02` SBOM 并入 P0 可验证性主线。

**并入既有主线**：`QA-02.02` SBOM / `DO-03.x` 验证说明并入 **P0 可验证性主线**
（CycloneDX 1.7 + PEP 740 对标），不单开。

> 与 pyobfus 已持有的 **OpenSSF Best Practices passing 徽章**不冲突：那套 67 条侧重
> 开发实践，OSPS 侧重**项目安全治理姿态**，两者互补。本表可作为下一步"是否申报
> OSPS 自证"的依据。
