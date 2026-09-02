# 外部渠道与用户信号快照（2026-08-24）

这份文档冻结 2026-08-24 发版后的外部观察结果，供数日后复查时作基线。
它不是实时状态页；最新状态仍以 `CURRENT_PLAN_ZH.md` 和
`DISTRIBUTION_CHANNELS.md` 为准。

## 发布与分发基线

- `pyobfus 0.5.17`、`pyobfus-mcp 0.3.8` 已发布；PyPI OIDC/PEP 740
  provenance、GitHub Releases 和 MCP Registry `active` / `isLatest=true`
  均已核实。
- Claude Plugin Marketplace：维护者手工查看后仍为
  `Submitted and pending review`，提交日期 Aug 2。暂不因描述中的
  `protected_project` typo 重提，等待 approve/reject/补充信息入口。
- Glama：测试 `01a033e4-3336-7e7b-9792-0d7e056d2dba` 于 21:09 成功，
  耗时 12.1s。构建实际安装 `pyobfus-mcp==0.3.8` 与 `pyobfus==0.5.17`，
  `ListToolsRequest` 返回完整 8 个工具，并包含新增的
  `verify_dependencies_online` 参数。
- Glama 公开 API 仍返回 `tools: []`。成功实例已经证明服务启动和工具枚举
  正常，因此这是 Glama 目录/API 同步问题，不是本项目运行时或 Docker 配置
  问题。Build Spec 的 `pinnedCommit: null` 与 clone 日志 checkout
  `e44e687` 也互相矛盾，但不影响从 PyPI 安装的运行时版本。

## 下载量与用户反馈基线

数据来自 pypistats，统计截止 2026-08-23，因此尚不包含 08-24 本轮发布后的
完整数据日：

| 包 | day | week | month |
|---|---:|---:|---:|
| `pyobfus` | 27 | 502 | 2,059 |
| `pyobfus-mcp` | 11 | 242 | 772 |

周/月增长主要由发布日尖峰解释；08-23 已回落到 `27 / 11`。pypistats 会排除
已知镜像，但仍包含 CI/CD 下载，因此当前不能认定为有机用户增长。

同期公开反馈信号：

- GitHub：6 stars、2 forks、0 open issues、0 open PRs；6 条 Discussions，
  没有关于 `dependency_advisory` 的新外部评论。
- GitHub 14-day Traffic：155 views / 65 unique visitors；1,480 clones /
  158 unique cloners。发布自动化主导 clone 峰值，08-23 的 10 unique clones
  只记作弱兴趣信号，不等同于留存或生产采用。
- VS Code Marketplace：0.4.1、3 installs、124 downloads；暂无可识别的真实
  rating/review 信号。

## MCP Skills 扫描

- 官方免费 API 扫描 `zhurong2020/pyobfus`：composite **6.06**，tier
  `established`，14 signals，`verified=false`。
- 正向结果：`no safety findings`，且扫描器识别到了仓库中的 AI skill。
- 未达 Verified 的主要标记：`SINGLE_AUTHOR_LOW_ADOPTION` 和 `low_legit`。
- 决策：不购买 $2 full report，不通过修改代码/文档刷分；等真实采用、star、
  外部贡献者等信号改善后再扫描。

## Canopii Trust Index：39/F 的处理结论

Canopii 当前展示的是 `pyobfus-mcp v0.3.7`，分数 39/100、Grade F、81%
confidence；唯一导致封顶的 high failure 为 “No unsafe deserialization”。
页面证据定位到：

```text
pyobfus_pro/runtime/opacity.py:147
marshal.loads(plaintext)
```

本地代码语义核对结论：

- 这段逻辑属于同一 monorepo 中的 Pro Selective Opacity runtime，不属于
  `pyobfus_mcp/` 的 MCP 服务实现；MCP tool 参数不存在到该 bytes/key/plaintext
  的调用路径。
- `plaintext` 来自 `AESGCM.decrypt(...)`；密文或认证标签被篡改、或密钥错误时
  会先触发 `InvalidTag`。这里的认证成立于生成 artifact 的现有信任模型内，
  不能夸大为面对可同时改写源码、密钥和 artifact 的攻击者仍不可伪造；但这类
  攻击者本来就可直接替换 Python 代码，因此它不是新增的 MCP 远程输入风险。
- Canopii 的公开 Semgrep 规则 `deserialize-py-unsafe` 对所有
  `marshal.loads(...)` 直接命中，没有 taint/source 或前置认证数据流分析；同时
  扫描了整个仓库，而 MCP Registry 的 `server.json` 明确把包目录指向
  `pyobfus_mcp`。因此当前 F 更准确地说是“monorepo scope + 语法规则”的误报，
  不是已确认的 pyobfus-mcp 可利用漏洞。

处理策略：

1. 优先在 Canopii 用 GitHub claim maintainer 身份，并请求按最新 v0.3.8 重扫。
2. 若分数不变，向 `canopii-dev/canopii-cli` 提交误报 issue：附上证据行、
   AES-GCM 认证前置条件、MCP 无可达路径，以及 Registry subfolder 元数据。
3. 在上游确认支持的 suppression 机制前，不加入 `nosemgrep` 注释；不删除该
   Pro 功能、不改成 JSON，也不为评分改变安全边界。
4. 当前不把 39/F badge 嵌入 README，避免向用户传播未经澄清的结论。

参考：

- Canopii 规则：<https://github.com/canopii-dev/canopii-cli/blob/main/rules/insecure-impl.yml>
- Canopii CLI / issue 入口：<https://github.com/canopii-dev/canopii-cli>
- 评分方法：<https://index.canopii.dev/methodology>

## 数日后的复查清单

建议在 pypistats 已覆盖至少 2-3 个 08-24 后完整数据日时做第一次复查：

1. 对比两个 PyPI 包的非发布日 day 基线，而不是只看 rolling week/month。
2. 查看 GitHub issue、PR、Discussion、stars/forks 和 unique visitors/cloners；
   特别搜索是否有人提到 `dependency_advisory` 或“希望独立使用”。
3. 查看 Claude Plugin Marketplace 是否 approve/reject/要求补充信息。
4. 查看 Glama 公开 API 的 `tools: []` 是否恢复，以及 Discord `#support` 是否
   有回复；无需重复验证已经成功的容器运行时。
5. 查看 MCP Skills 是否仍为 6.06；没有真实采用/贡献变化时不必频繁重扫。
6. 完成 Canopii claim/v0.3.8 rescan 后记录版本、分数和 evidence 是否变化；
   若仍命中同一行，再决定是否正式提交上游 issue。
7. 一至两周仍无 `dependency_advisory` 主动反馈时，再开简短 GitHub Discussion
   投票；不要把“没有 issue”直接解释为“没有需求”。

## 2026-08-26 首次发布后复查

pypistats 已覆盖 08-24 发布日和 08-25 第一个完整非发布日：

| 包 | 08-24 | 08-25 | 最新 day/week/month |
|---|---:|---:|---:|
| `pyobfus` | 137 | 27 | 27 / 512 / 2,178 |
| `pyobfus-mcp` | 99 | 8 | 8 / 245 / 874 |

08-24 的尖峰与发布时点一致；08-25 立即回落到与发布前安静日相近的水平。
rolling week/month 虽继续上升，但仍主要由 08-17、08-20、08-22、08-24 的
发布/自动化流量解释，暂不能认定自然用户基线抬升。

GitHub 同期复查结果：

- 仍为 6 stars、2 forks、0 open issues、0 open PRs；Discussions 仍为 6 条，
  最新项目公告没有新评论，也没有人提到 `dependency_advisory` 或要求独立使用。
- 14-day Traffic 更新为 176 views / 72 unique visitors、1,751 clones /
  182 unique cloners。08-24 发布日为 268 clones / 31 unique，08-25 回落到
  10 / 6；与 PyPI 一致，发布自动化仍是主要解释。
- 热门路径以仓库首页为主；README、CHANGELOG 各只有 3 unique views，尚无
  足够证据把访问归因到新 advisory。referrer 仍以 GitHub、Google、PyPI、
  Bing 为主，ChatGPT 只有 2 unique。
- 最新 main CI、CodeQL、Pages 仍全部成功。

外部渠道：Glama 公开页面仍可解析到完整 8 个工具；其旧公开 API 本轮返回
HTTP 401，进一步说明该 API 已不适合作为无需认证的健康检查。Canopii claim/
v0.3.8 rescan、Claude Plugin Console 和 Glama Discord 仍需维护者登录，未在
本轮程序化代操作。

**结论**：完成第一次复查，但不升级为有机增长或拆包信号。下一次下载量复查
恢复到 1--2 周周期；若到 09-01 至 09-07 仍无主动反馈，按原计划发起一条简短
GitHub Discussion 投票。Canopii claim/rescan 仍是当前最高优先级人工事项。

## 2026-09-02 第二次周期复查

pypistats 逐日数据当前只到 08-31，尚未覆盖 09-01 的 Core 0.5.20 / MCP
0.3.10 SEO 发版。因此本节完成 08-25--08-31 周期复查，但不能用于判断
09-01 发版后的表现。

| 包 | 最新 day/week/month | 本周期发布尖峰 | 非发布日观察 |
|---|---:|---:|---|
| `pyobfus` | `31 / 376 / 2,338` | 08-28 `127`；08-30 `117` | 08-25/26/27/29/31 为 `27/12/23/39/31`，均值 `26.4`、中位数 `27` |
| `pyobfus-mcp` | `6 / 232 / 1,090` | 08-28 `151` | 08-25/26/27/29/30/31 为 `8/6/16/26/19/6`，均值 `13.5`、中位数 `12` |

Core 的非发布日中位数与 08-25 的 `27` 基线一致，没有抬升。MCP 的非发布日
中位数较 08-25 的 `8` 略高，但样本只有 6 天，且紧邻多次发布，证据不足以
判定有机增长。rolling month 增至 `2,338 / 1,090`，仍主要由发布尖峰累计解释。

同日 GitHub 14 天 traffic：`1,999 clones / 202 unique`、`214 views / 85 unique`。
08-28 与 08-30 的 clones 分别为 `188/28 unique`、`414/29 unique`；相邻安静日
回落到 08-29 `5/3`、08-31 `20/9`。仓库仍为 6 stars、2 forks、0 open
issue/PR；Discussions 共 6 条，无新评论或新需求。继续维持“发布/自动化流量
主导，尚无有机增长或 `dependency_advisory` 独立需求信号”的判断。

**下一检查点**：等 pypistats 至少覆盖 09-02，再比较 09-01 SEO 发版日与首个
完整非发布日；在此之前不根据 rolling week/month 作产品决策。
