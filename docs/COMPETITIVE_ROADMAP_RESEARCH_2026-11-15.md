# pyobfus 竞品与路线复核（2026-11-15）

状态：只读调研与路线建议；**不代表功能实施、版本范围、部署或发布已获批准**。
项目基线：Core 0.14.0 / MCP 0.3.17 / runtime 0.1.1 / VS Code 0.4.3 /
Action v1.1.0；生产 Worker `209eb969`（回滚 `13aaa4a8`）。

本次从 [当前计划](CURRENT_PLAN_ZH.md)、[TODO](TODO.md)、
[2026-10-30 路线复核](ROADMAP_REVIEW_2026-10-30.md)、
[2026-10-28 功能扩展复核](FEATURE_EXPANSION_RESEARCH_2026-10-28.md)和
[比较范围政策](COMPARISON.md)出发，重新核对主要竞品的官方文档、官网与 PyPI
公开元数据。没有购买竞品、运行同配置保护强度或性能基准，也没有新增客户访谈；
厂商的保护强度、逆向成本和市场效果描述均视为厂商声明，不作为本项目实测结论。
版本、价格、许可和平台能力会变化，引用本记录对外发布前必须重查。

## 结论摘要

pyobfus 已越过实验性 AST 混淆器阶段：多文件语义改写、普通 `.py` Community
产物、私有 mapping 与 traceback 还原、框架预设、构建／覆盖报告、交付检查、
SARIF／CycloneDX／PEP 740、MCP／VS Code／Action 和签名 CI 准入已形成完整骨架。
当前主要缺口不是变换数量，而是把这些能力凝结为一个容易理解、可重复验证的
真实交付闭环。

建议定位收敛为：

> 面向持续交付的、可验证且可调试的 Python 代码保护工具。

路线应围绕四个支柱组织：

1. **Protect**：多文件、框架感知、边界明确的本地保护。
2. **Verify**：构建／覆盖报告、交付检查、SARIF、SBOM 与 provenance。
3. **Debug**：私有 mapping、traceback 还原和 Agent 辅助排障。
4. **Deliver**：与 PyInstaller、Nuitka、CI 和离线许可组合，验证最终交付物。

前三项已较成熟；下一阶段应优先补 Deliver，而不是主动增加 AST 变换。

## 最新竞品观察

### PyArmor 9.3.0：强保护上限的对照

- PyPI 9.3.0 于 2026-10-31 发布，2026-11-13 又上传修订 wheel；公开文件没有
  PyPI provenance。
- 官方 9.3 文档列出 `rft`、`mini`、`vmc`、`ecc` 等脚本类型；环境表覆盖
  Python 3.11–3.15，并继续提供原生 runtime、绑定、有效期及打包路径。
- 官方资料：<https://pypi.org/project/pyarmor/>、
  <https://pyarmor.readthedocs.io/en/latest/>、
  <https://pyarmor.readthedocs.io/en/stable/reference/environments.html>。

判断：PyArmor 的原生／虚拟化保护、运行时控制和长期市场积累仍明显强于
pyobfus。新增更多 AST 变换不会消除架构差距。它应继续作为保护强度上限的诚实
对照，而不是本项目的功能清单来源。pyobfus 的差异应放在普通 Python 产物、较低
部署复杂度、私有映射恢复、透明 Core 和可验证构建上。

### PyLocket 1.1.21：最需要关注的产品形态

- PyPI 1.1.21 于 2026-11-02 发布，要求 Python 3.12+；公开 wheel/sdist 没有
  PyPI provenance。
- 官方页面描述函数／方法／类体／模块代码块加密、设备激活后下发密钥、原生
  hardened runtime、许可撤销／重置、一次性下载、托管 checkout、自动更新、
  webhook 以及签名产物替换和分发。
- 公开支持 PyInstaller onefile/onedir、cx_Freeze、Briefcase、wheel、ZIP、
  macOS `.app`，以及 Windows x64、Linux x64/arm64、macOS Intel/Apple Silicon。
- 价格模型为账户订阅加每份正式许可 4 美元；免费层可测试，官方条款称付费订阅
  结束并经过宽限期后，既有终端许可将失效。
- 官方资料：<https://pypi.org/project/pylocket/>、<https://pylocket.com/>、
  <https://pylocket.com/pricing.html>、
  <https://docs.pylocket.com/part-4-topics/billing/>。

判断：PyLocket 已从保护工具扩展成“保护、许可、交付、收款、更新”平台，正在
占据独立开发者销售 Python 桌面应用的完整任务。pyobfus 不应复制其商城、云端保护、
自动更新或托管下载；更有价值的对位是面向希望自己控制源码、构建、密钥、许可和
客户关系的开发者，提供 local-first、可审计、可调试的工具链。

### Nuitka 4.3.5 / Commercial：重要组合伙伴

- 官方下载页在本次核对时列当前稳定版为 4.3.5；4.3 发布说明继续推进 Python
  3.15 实验支持。
- Commercial 公开价从 250 欧元／年起，并提供代码／常量保护、数据文件嵌入和
  traceback 加密。其资源嵌入支持标准文件和 `importlib.resources` 访问路径，
  明确区分普通 onefile 临时展开与 Commercial 内嵌保护。
- 官方资料：<https://nuitka.net/doc/download.html>、
  <https://nuitka.net/posts/nuitka-release-43.html>、
  <https://nuitka.net/doc/commercial/protect-data-files.html>、
  <https://nuitka.net/doc/commercial/traceback-encryption.html>。

判断：Nuitka 已不只是“编译顺便隐藏源码”，但它仍更适合作为 pyobfus 的组合伙伴，
而不是必须击败的同类。pyobfus 负责项目级名称保护、检查、mapping 和供应链证据，
Nuitka 负责最终二进制交付；因此 Windows Nuitka standalone 的正式单组合验收应升至
近期待办。

### SOURCEdefender：传统的选定模块加密路径

- 官网仍以 AES-256 加密和专用导入路径为核心；公开价格为每开发系统每月 15 英镑、
  每年 150 英镑或 Enterprise 每年 1500 英镑。
- 客户运行加密代码无需构建许可，开发机和 CI 加密节点需要许可。
- 官方资料：<https://www.sourcedefender.co.uk/>。

判断：它在“只加密几个模块”的场景中认知成本较低，但没有形成 pyobfus 的多文件
语义改写、mapping、Agent 工具和供应链验证组合。保持比较页诚实更新即可，不需
专门追随其 loader 架构。

### 开源进入者：搜索噪声增加，产品形态尚未重合

2026 年仍有以 AES、marshal、bytecode、VM、anti-debug 和 PyInstaller EXE 为卖点的
项目活跃。GitHub topic 快照见
<https://github.com/topics/python-obfuscator?l=python&o=desc&s=updated>。
这些元数据不能证明质量或安全强度；本轮也没有发现另一个公开项目同时具备成熟的
多文件语义改写、reverse traceback mapping、框架预设、MCP／VS Code／Action、供应链
证明和 Python 3.9–3.15 验证矩阵。不要以“保护层数”或 anti-VM 宣传回应这类项目。

## 产品定位与目标用户

建议主叙事从“PyArmor 的便宜替代品”改为“本地、自主、可验证、可调试的保护工具链”。
核心用户是：

- 交付 Python 工具或私有应用的个人开发者／小团队；
- 需要多文件保护但不能接受运行语义漂移的项目；
- 需要保留生产 traceback 排障能力的维护者；
- 需要在 CI 中获得可复现、可审计证据的团队；
- 不愿把源码上传到第三方保护平台、希望自管密钥和客户关系的卖方。

Pro 的价值应围绕一个任务表达，而不是罗列变换：把私有 Python 应用交给客户运行，
同时保留自己的排障能力，并证明源码、mapping 和密钥没有误入交付物。

## 建议路线

### P0：整理 roadmap 与状态入口（只改文档，不发版）

- 把已完成事项移入历史／发布证据，删除过期版本状态和旧增长目标。
- 当前 roadmap 只保留未来 6–12 个月的 Correctness、Delivery、Protection、Trust、
  Distribution 五类任务。
- 每项写明用户／问题／证据、Community 或 Pro 归属、触发条件、验收和停止条件。

### P0：公开交付参考应用

建立一个可公开、可重复构建的小型多模块应用，包含资源、动态导入或插件、可映射
异常、Community 和 Pro L3、应用自管密钥，以及缺失／错误密钥负例。复用同一案例
依次验证普通目录、PyInstaller onedir/onefile 和 Windows Nuitka standalone。证据至少
记录固定版本、命令、输入／产物哈希、运行结果、traceback 还原、覆盖报告，以及
源码／mapping／私钥是否误入成品。

### P0：Windows Nuitka standalone 单组合正式验收

按 [下一项交付方案](NEXT_DELIVERY_VALIDATION_PLAN.md)执行；先验证公开 wheel 和真实目标
环境，先产出 cookbook 与限制。只有发现可复用的配置／诊断缺口时才增加产品代码，
不默认扩成每 PR 多平台矩阵。

### P0/P1：让 `--check-delivery` 解析一个冻结格式

首版只选择 PyInstaller 或 Nuitka 的一个有文档格式；不得执行载荷，并限制递归深度、
文件数、总展开大小和时间。结果必须区分已检查、未知格式、工具缺失和截断；空结果或
未解析结构不得报告为干净。该本地检查属于 Community 正确性能力。

### P1：资源检查与资源 key provider

- Community：检测敏感资源和原始资产是否误入交付物。
- Pro：在真实需求下设计资源加密 primitive；先定义密钥注入时机、作用域、轮换、
  并发以及缺失／错误密钥行为。
- 不把现有 L3 provider 直接当作资源 Vault 契约，不做托管密钥服务。

### P1：下一次自然 Core 发版

带上已合并的 #230 未信任签发 key 升级提示和 #231 备用公钥 `ci-2026-11b`；遵循完整
发版清单、Agent 文档同步和 Glama pin 更新。发版仍需维护者明确批准；发版后再按
TODO 发送 Pro 客户升级通知。

### P2：有需求后扩保护覆盖

L3 方法／嵌套函数实施前必须定义 descriptor、classmethod/staticmethod、装饰器顺序、
`super()`、闭包／nonlocal、继承／override、异常映射和覆盖报告的跳过原因。Python
3.15t 需用真实 free-threaded 解释器，在导入 cryptography/cffi 后记录 GIL 状态并验证
provider 并发与异常恢复；普通 3.15 通过不能替代该证据。

## 明确不提高优先级

- 不追原生 VM、VMC、BCC 或 Themida 式保护；它们与可调试、普通 Python 产物和维护
  成本边界冲突。
- 不做云端 obfuscation-as-a-service、托管商城、自动更新或托管下载。
- 不加入 anti-VM、AV bypass 或强 anti-debug 竞赛，保持防御工具与公开仓库边界。
- `--output-pyc` 只保留 spike；它未解决当前购买问题，却增加兼容与调试成本。
- 不提高 AI 自动生成 transformer 的优先级；当前真实缺口是可靠交付，不是变换不足。

## 建议执行窗口

### 0–4 周

1. 完成 11-16 周检。
2. 清理 TODO／ROADMAP 状态漂移。
3. 定义公开交付参考应用及验收合同。
4. 完成 Windows Nuitka standalone 单组合验证。
5. 按本记录刷新 `COMPARISON.md` 的版本／价格快照；不因此发 Core。

### 1–3 个月

1. 选择一个冻结格式扩展 `--check-delivery`。
2. 按参考应用的真实结果修兼容问题，不预设一定需要代码修改。
3. 设计资源扫描／provider 边界。
4. 发布带备用签发公钥的下一自然 Core，并发送发版后客户通知。
5. 以“自主管理、可验证交付”整理 Pro 的购买路径。

### 3–6 个月

1. 有需求时实现资源保护 primitive。
2. 有真实阻塞时扩展 L3 方法／嵌套覆盖。
3. 验证 Python 3.15t。
4. 根据第一个格式和真实用户反馈决定是否解析第二个冻结格式。
5. 根据多版本构建调试需求决定是否做 mapping 自动选择。

## 下一会话入口

先执行 2026-11-16 周检；若进入产品推进，则先清理当前入口并为“公开交付参考应用 +
Windows Nuitka standalone 验收”写最小范围和接受标准。不要在没有真实需求或单项授权时
并行启动资源保护、L3 方法覆盖、3.15t 和第二种冻结格式。实现、发布、Worker 部署和客户
通知仍是彼此独立的 gate。
