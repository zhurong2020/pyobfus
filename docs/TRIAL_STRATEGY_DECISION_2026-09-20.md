# Trial 策略调研与决策（2026-09-20）

Status: **决策已定（方案 A）**。服务端邮箱登记 trial 列入 **P1，尽快实现**，但
实现与发版仍各自需要用户明确批准（沿用既有 gate）。本文件是决策记录 + 实现设计。

触发点：用户提出当前 Pro trial 是否"太大方"，是否该设行数/文件数上限、加登记与
防护，或改为"先收费"的 trial。

---

## 1. 当前 trial 的真实机制（对代码，非记忆）

`pyobfus/trial.py`：

- **5 天、零注册、零付费**，期间是**完整 Pro**，**无行数上限、无文件数上限**。
  （free/community 版本身也无 size 限制，此前已实测确认。）
- 状态存 `~/.pyobfus/trial.json`，**未签名明文 JSON**。
- "设备 ID" = `hostname + MAC` 的 SHA-256 前 16 位，作用是**防止 trial 记录被误
  拷到别的机器**（scoping），**不是防篡改**。
- 服务端（Cloudflare Worker + KV）**没有任何 trial 通道**：只有 license
  `/api/verify`、`/api/deactivate`、Stripe webhook、设备重置。trial 100% 客户端。
- 代码自述："convenience control, not a security boundary"；"deliberate bypass
  is expected and accepted"；真正加固需要**不把 Pro 以可读源码放进公开 wheel**
  ——分发模型改动，非改此文件。见 issue #20/#21。

## 2. 用户担忧的滥用点 —— 逐条评估

| 担忧 | 现状 | 评估 |
|---|---|---|
| 用一次 trial 就不买 | 完全可行 | 混淆是**每次发版都要重跑的构建步骤**；只发一次的脚本作者能"用完即走"，持续分发产品的厂商（真正客户）必须反复重跑 → 自然约束 |
| 换信息多次 trial | 删 `trial.json` 或改 hostname/MAC 即重置，门槛≈0 | 成立，但见 §3 |
| trial 登记 + 防护 | 无服务端登记 | 目前无 per-identity 去重 |
| 行数/文件数上限 | 无 | 见 §3——本地加是安全戏法 |

## 3. 关键判断：本地限制是安全戏法

`pyobfus_pro/` 自 2025-11 起以**可读源码**在公开 wheel 里。任何本地限制（LOC 上限、
文件数上限、本地登记检查）用户都能读到并一行改掉 / 删 json。结果：

- **挡不住真心白嫖的人**（读得到代码）；
- **却劝退诚实评估者**——真买家想在自己真实（通常很大）的代码库上试，行数上限
  第一个卡住的就是他。

能改变经济账的杠杆只有两个，都是结构性的：
1. **服务端签发 trial**（复用现成 Worker + KV）——把 trial 门移到用户改不了的地方。
2. **不再以可读源码分发 Pro**——更大的分发模型改动。

## 4. 决策（方案 A，用户 2026-09-20 拍板）

- **维持本地 5 天 trial，不设行数/文件数上限。** 与"Pro 反正是可读源码"的现实自洽，
  且不伤评估漏斗。
- **不改"先收费 / 先要卡"的 trial。** 当前无有机增长信号、仅个位数客户，加购买
  摩擦是反漏斗的；留到出现真实 trial 滥用证据或漏斗顶端显著变大时再议。
- **把 trial 当获客而非 DRM**：新增**可选的"留邮箱换 trial"**，由 Worker/KV 服务端
  签发并登记 trial key。收益：(a) 邮箱层的 per-identity trial 去重（挡住"换信息
  多刷"的低成本滥用）；(b) outreach 名单；(c)"trial 到期→折扣召回"钩子。复用已上线
  的 Worker 基建，投入产出比最高。**列入 P1，尽快实现。**

> 核心结论一句话：问题不在"trial 太大方"，在"trial 不在服务端、既没登记也没获客"。
> 修法不是收紧额度，是把 trial 挪到服务端并顺手变成获客渠道。

## 5. 实现设计（P1 · 待实现/发版批准）

**设计原则**：新增服务端 trial 是**可选增益**，不破坏现有零摩擦本地 trial——
无网络 / 不留邮箱者仍可 `pyobfus-trial start` 拿本地 5 天。服务端 trial 是"想要
被记住、想收到召回、愿意留邮箱"的用户的升级路径，也是唯一能做 per-identity 去重的
位置。它是防"低成本多刷"与获客，**不宣称**能挡住能读源码的人（诚实边界，同现有
trust boundary 注释）。

### 5.1 服务端（Cloudflare Worker + KV）—— 要部署

- 新端点 `POST /api/trial/request`：入参 `{email, device_id}`。
  - KV 以 email 为键登记：已发过 trial 的 email → 返回既有到期时间，不重复延长
    （per-identity 去重）。
  - 首次 → 生成受签名的 trial token（含 email 哈希、device_id、issued/expires），
    写 KV，返回 token。
  - 复用 `/api/verify` 已验证过的 HMAC/签名工具，与 Stripe webhook 签名校验同源，
    不 DIY 加密（Tier 2 基线：well-vetted crypto only）。
- 速率限制 + 邮箱形状校验，防脚本批量刷。
- **红线**：不写任何 PII 明文到日志；email 只存哈希用于去重（可选保留明文用于
  召回时必须走与 license 同级的保护，且进 KV 每日备份口径）。

### 5.2 客户端（`pyobfus/trial.py` + `trial_cli.py`）—— 要发版

- `pyobfus-trial start --email <addr>`：打服务端换 token，本地存 `trial.json`
  增加 `token` 字段；离线 / 不带 `--email` 时**回退到现有纯本地 5 天**（不回归）。
- token 存在时，`is_trial_active()` 以 token 的 expires 为准；仍是 convenience
  control（本地可篡改），服务端登记只解决去重与获客，不改变 trust boundary 措辞。
- 新增/更新 trust boundary docstring，诚实说明服务端登记的作用边界。

### 5.3 免发版 vs 要发版拆分

- **免发版**：本决策文档、TODO 登记、Worker 端点设计评审。
- **要部署**：Worker 新端点（先于客户端部署，顺序是硬约束——同 0.5.26 教训：
  客户端先于服务端发布会打到不存在的路由）。
- **要发版**：客户端 `--email` 支持（Core 小版本）。

### 5.4 验收标准（实现时据此）

- 服务端：同一 email 二次 `request` 不延长 trial（去重生效）；无 email 的本地
  `start` 仍拿满 5 天（不回归）；端点对缺签名 / 伪造 token 返回 4xx；速率限制生效。
- 客户端：离线 `pyobfus-trial start` 与今日行为逐字一致；带 `--email` 成功换 token
  并本地生效；三个测试根 + 扩展根全绿；不读写开发者真实 `~/.pyobfus`。
- 部署顺序：Worker 端点先上线并 `curl` 实测，再发客户端。

## 6. 明确不做

- 本地 LOC / 文件数上限（安全戏法）。
- "先收费 / 先要卡"的 trial（反漏斗，当前规模不做）。
- 声称服务端 trial 能挡住能读 Pro 源码的人（诚实边界）。

## 7. 上线后状态（2026-09-25 核查）

- Worker `/api/trial/request` 在线（空请求返回 400 校验提示）；客户端 `pyobfus-trial start --email`
  自 0.5.28（2026-09-20）起可用。
- KV 里 trial 登记数 **0**：上线 5 天，全部 5 个 key 仍是许可记录。与下载基线未抬升一致，
  是流量问题不是功能问题。
- §5.1 红线的「进 KV 每日备份口径」当时**没有真正落地**：`~/scripts/pyobfus_kv_export.sh`
  只认 license 记录，第一条 trial 记录会让整轮导出拒绝落盘、许可备份静默停止。2026-09-25
  已修（按 key 类型校验 + Windows 安全文件名 + `--selftest`），并把调度挪进日备份以随
  systemd `Persistent` 补跑。记录里的明文 email 沿用 license 记录的 PII 口径，随日备份进
  OneDrive；恢复命令见 `~/.pyobfus-backups/README.md`。
