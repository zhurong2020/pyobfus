# 0.11.0 后路线与设计复核（2026-10-30）

状态：文档与设计复核；不代表新功能实现、平台支持扩大或发布批准。
基线：Core 0.11.0 / MCP 0.3.16 / runtime 0.1.1。
本轮核对本仓源码、CHANGELOG、验证记录及下列官方在线文档；没有新增客户
访谈、竞品实测或打包运行。在线手册为本日观察，旧实测的工具版本保持原样。

## 已完成事项与真实剩余范围

| 原待办 | 核对结果 | 后续范围 |
|---|---|---|
| 独立目录 mapping | 0.9.0 已发布；`mapping.py` 的 `independent_files` 与 `tests/test_independent_mapping*.py` 已落地 | 不重复开发；多版本自动选择是另一项需求 |
| README / RTD / Pages 首屏 | 三处均说明多文件、import 改写、Community 普通 `.py` 与私有 mapping | 关闭措辞待办；11 月观察检索效果，不以排名作为验收 |
| Nuitka onefile / Windows 打包 | 公开 0.10.0 的 Linux Nuitka onefile、Windows PyInstaller onedir/onefile 已有记录 | 不等于最新 wheel、Windows Nuitka、macOS、3.15 或 L3 冻结包已验证 |
| P0 包根诊断、P2 字节码／冻结外壳诊断 | 已随 0.11.0 发布 | 不再待发版；冻结包内部仍未检查 |
| dogfood 与独立产物验证 | `scripts/dogfood/run.py` 已有 A–D lane | 复用现有机制；不新建同功能验证框架，不直接升级为必需检查 |

证据：[0.11.0 发布](CORE_0_11_0_RELEASE_2026-10-29.md)、
[打包矩阵](P1_PACKAGING_VALIDATION_2026-10-28.md)、
[自用验证边界](SELF_DOGFOODING_BEST_PRACTICES.md)。

## 官方实践与设计决定

以下设计决定是本项目根据资料作出的取舍，不是官方对 pyobfus 的背书。

| 官方依据（2026-10-30 查阅） | 本项目采用的设计约束 |
|---|---|
| [CPython 3.15 free-threading](https://docs.python.org/3.15/howto/free-threading-python.html)：构建支持与运行时 GIL 状态不同，扩展导入可能重新开启 GIL | 同时记录构建标志及依赖导入后的运行时状态；普通 3.15 通过不能替代 3.15t |
| [PyInstaller 运行模式](https://pyinstaller.org/en/stable/operating-mode.html)：先 onedir 后 onefile；构建与 OS、解释器相关 | 每次只扩一个所需组合；分别记录构建机、目标机、资源读取和异常行为 |
| [Nuitka 手册](https://nuitka.net/user-documentation/user-manual.html)：standalone/onefile 与默认 accelerated 模式不同 | 记录实际模式、编译器、依赖和数据文件参数；构建成功不能代替隔离运行 |
| [GitHub SARIF 支持](https://docs.github.com/en/code-security/reference/code-scanning/sarif-files/sarif-support)：稳定 ruleId、路径与 fingerprint 用于匹配告警 | 保持既有身份契约；自扫描问题先做证据分类，不通过排除整个源码树消除结果 |
| [SLSA 1.2 产物验证](https://slsa.dev/spec/v1.2/verifying-artifacts)：将签名、builder 身份和构建参数与预期比较 | 发布证据记录产物哈希与预期来源；本地 report 哈希不升级为签名或 SLSA 等级声明 |
| [PyPI attestations](https://docs.pypi.org/attestations/)及[消费验证](https://docs.pypi.org/attestations/consuming-attestations/) | 继续使用独立工具核验公开产物来源；来源证明与运行正确性分别验收 |

## 可推进顺序

| 顺序 | 工作 | 当前判断 | 产出／停止条件 |
|---|---|---|---|
| A | 清理已完成待办与发布状态 | 本轮完成文档修订 | TODO、roadmap、当前计划不再重开上述项目 |
| B | 真实问题的最小复现与设计 | 可推进取证；收到案例再实现 | 原文／产物差分、最小依赖、预期行为、支持范围；无法复现则保留 unknown |
| C | 打包剩余组合 | 可推进单组合验证设计；执行等目标需求 | 优先实际交付需要的一个组合，复用现有 fixture；无目标就不扩矩阵 |
| D | 3.15t 公共 wheel 验证 | 可设计；执行等目标平台需求 | 干净目标安装、导入依赖后的 GIL 状态、并发与 traceback；跨文件 L3 保持拒绝 |
| E | 采用与运营观察 | 按现有日期推进 | 首日／一周／月度快照；私有 CI 在恢复条件满足后才同步 |
| F | L3 方法／嵌套、资源 provider、参数改名、冻结内部解析 | 条件候选 | 明确阻塞、边界及单项范围后启动；本轮不自动纳入实现 |

## 下一项正确性工作的验收设计

用户是交付多模块 Python 应用的开发者，问题是变换后导入、动态访问或异常
行为偏离原文。现有证据是既往限制及已发布修复，本轮没有新的未修复最小案例。
正确性与基本诊断属于 Community，不以 Pro 许可作为修复前提。

1. 案例包记录 Python/OS、工具版本、配置、入口及期望输出；公开夹具只保留
   技术结构，不携带客户标识、源码秘密或真实密钥。
2. 在隔离临时目录运行原文、公开 0.11.0 和待修 checkout；比较退出码、输出、
   异常类型及项目 traceback 帧。公开版本用于回归对照，不是绝对正确的判据。
3. 区分已证明可重写、保守保留可运行、明确拒绝和产物错误；不把告警消失当
   正确性证明。导入顺序、循环、re-export 和动态绑定只扩到复现所需范围。
4. 保持 JSON `status` / `ai_hint` 与 MCP `next_tool` 契约、mapping 兼容性及
   名称验证。改动默认行为需写迁移说明，不顺带扩大改名或加密范围。
5. 先定向回归，再按仓库要求运行质量检查与分开的测试根；测试状态路径和
   生成代码的 HOME / USERPROFILE 指向临时目录。发布仍单独验收。

## 打包与 3.15t 的有界验证设计

复用 `integration_tests/packaging/multimodule/`；不新增打包器产品代码。
每个组合的证据需含固定工具版本、输入／产物哈希、命令、耗时、资源结果、
异常映射、实际检查过的内容和未检查范围。来源／mapping／密钥放在交付树外；
staging 与运行缓存分开。先验证原文，再验证混淆产物，最后验证冻结产物。

执行优先级由用户目标确定：3.15 普通打包、Windows Nuitka、macOS、L3 与
冻结包的组合互不代替。Windows 新验证应由 WSL checkout 准备并使用适当的
原生目标执行环境；不使用 OneDrive 旧副本。远端先手动单格、记录成本，
再决定是否定时运行；不加每 PR 全矩阵，不修改 ruleset。

3.15t 需记录 `Py_GIL_DISABLED`，并在导入 cryptography/cffi 等实际依赖后
检查 `sys._is_gil_enabled()`。正常输出、异常映射和有界并发分别记录。
缺依赖、GIL 被重新开启或缺目标平台只记未完成，不能记通过。
应用 provider 的并发烟测不证明跨文件 L3 加密产物兼容；解除守卫需要
独立的 runtime 线程安全设计、负例及产物验收。

## 较大功能的设计边界

- L3 方法／嵌套属于 Pro 保护覆盖：先约定 descriptor、闭包、装饰器、继承和
  异常映射语义；不支持的选择必须在覆盖报告中可见，不能静默降级。
- 资源 key provider 属于 Pro 资产保护：先确定密钥注入时机、作用域、轮换、
  并发及缺失／错误密钥行为；不把当前 L3 provider 直接当作 Vault 契约。
- 冻结内部检查属于 Community 本地检查：如有需求，首版只选一个有文档的
  容器格式，限定递归深度、文件数、总展开大小、时间和路径；不得执行载荷。
  截断、未知格式或工具缺失仍为未检查，不能得出干净结论。
- 参数改名和自动选择多版本 mapping 继续等待具体接口／多构建调试需求；
  不把已完成的 per-file mapping 与它们混为同一项。

所有新增能力按 [版本边界政策](EDITION_BOUNDARY_POLICY.md) 记录用户、买方、
问题与证据；Community 正确性底线和 Pro/Core 源码隔离不变。
