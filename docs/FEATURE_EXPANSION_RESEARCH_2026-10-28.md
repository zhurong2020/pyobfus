# pyobfus 功能扩展复核（2026-10-28）

状态：竞品官方资料与本仓已知缺口复核完成；以下为**提案**，不是实现、合并或发版授权。当前公开基线为 Core 0.10.0、MCP 0.3.16、runtime 0.1.1。优先级摘要写入 [ROADMAP](ROADMAP.md)，执行状态仍以 [TODO](TODO.md) 与 [当前计划](CURRENT_PLAN_ZH.md) 为准。

## 证据边界

本轮查阅公开官方手册、PyPI 项目页面与本仓验证记录；未购买竞品、未进行同配置保护强度或性能基准，也没有新客户访谈。竞品页面是滚动文档，以下只记录 2026-10-28 观察到的功能范围，不据此断言某项未列功能不存在。版本和公开行为应在实际选型或发布比较文章时重查。沿用 [比较范围政策](COMPARISON.md)。

| 对象 | 本轮官方资料所述 | 对本项目的启发与界限 |
|---|---|---|
| [PyArmor 9.3.0 文档](https://pyarmor.readthedocs.io/en/latest/)及[命令手册](https://pyarmor.readthedocs.io/en/latest/reference/man.html) | `--pack` 可调用 PyInstaller 生成 onefile/onedir；外部 runtime key 可附有效期或设备绑定。其[环境表](https://pyarmor.readthedocs.io/en/latest/reference/environments.html)列到 Python 3.15 | 打包与外部 key 的交付路径值得验证；不等于 pyobfus 要复制绑定、VM 或授权服务器，也不代表这些选项在本仓目标环境已实测 |
| [Nuitka 官方手册](https://nuitka.net/user-documentation/user-manual.html) | standalone、onefile 与数据文件/模块纳入规则明确；Python 代码不能当普通 data file 随意纳入 | 先做组合交付的真实产物测试，必要时提供配置示例；不新建编译后端 |
| [PyInstaller 官方手册](https://pyinstaller.org/en/stable/operating-mode.html)及[hooks 文档](https://pyinstaller.org/en/latest/hooks.html) | onefile 启动时解包到临时目录；官方建议先验证 one-folder；动态导入可需要 hook | 按 onedir→onefile 验证运行、数据路径、隐藏导入与交付内容；不能把 onefile 当作不可提取的保密机制 |
| [PyLocket 官方 PyPI 页面](https://pypi.org/project/pylocket/) | 页面描述对 PyInstaller、wheel、脚本等成品保护，以及按设备授权、下载分发；列 Python 3.12–3.14 | 属另一种交付/商业模式，页面的安全强度描述是厂商声明，未经本轮复现；可借鉴清晰的支持矩阵与交付步骤，不把云服务加入当前路线 |

CPython 的[自由线程说明](https://docs.python.org/3/howto/free-threading-python.html)指出部分扩展模块可能重新启用 GIL；其[C 扩展说明](https://docs.python.org/3/howto/free-threading-extensions.html)要求扩展明确声明支持。因此普通 3.15 通过不能推出 free-threaded 3.15 已验证。

## 本仓当前基线与缺口

- 3.15 基础兼容、`--no-cross-file` mapping、MCP SDK 2.x、受限多模块 L3 已发布；见 [3.15 验证](PYTHON315_VALIDATION.md)、[L3 验证](CROSSFILE_OPACITY_VALIDATION.md)和 [TODO](TODO.md)。不重开这些已完成范围。
- `json`/`unittest` 标准库目录冒烟暴露模块属性证明限制；当前记录显示 main 的生成产物导入失败。先最小化与分类，不能把它直接推断为所有 3.15 项目失效，也不能忽略已观察到的生成行为。
- L3 预览只覆盖受限顶层函数及应用提供的密钥；方法、嵌套函数、复杂初始化/循环导入、冻结交付和 free-threading 仍未验证。覆盖报告与真实产物要一致，不能以构建成功替代运行证明。
- `--check-delivery` 已检查 mapping、私钥、原始源码等；`.pyc` 来源判定和冻结包解析仍是候选。已有单例 Nuitka standalone 证据，不能推广到 PyInstaller onefile、Nuitka onefile 或 Windows。

## 建议顺序与验收门槛

1. **P0：正确性/明确失败。** 用最小 `json`、`unittest` 类案例及真实小包复现属性访问，区分分析器无法证明、错误拒绝、已产出的错误行为。对原文与变换产物做导入、调用、异常和 traceback 差分；修正缺陷或明确报出不支持边界。保持 `verify-names` 的安全约束。只在修正的受影响 Python/平台格验证，不为此扩大整仓 CI。
2. **P1：打包交付兼容。** 以已发布 wheel 构建一个含两个模块、资源和异常的代表性应用；先 PyInstaller onedir、Nuitka standalone，再针对同一案例试 onefile，至少覆盖 Linux 和 Windows 的一个受支持解释器。全新目标环境运行并核对映射、错误密钥、来源文件、mapping 和私钥是否进入交付物。先本地/手动验证，出现实际需求或复现缺口后决定是否增设定时 CI；计时和限制并发。若需 hook，先产出可复制示例和诊断，再考虑 API。
3. **P1：L3 预览的可用性交付。** 选择一个可公开的离线小应用，把应用自管 key 注入、runtime-only 环境、缺失/错误 key、异常反向映射和覆盖报告贯通。只有具体部署障碍出现，才单独设计资源 key provider API；不得把示例密钥写进成品。
4. **P2：交付诊断。** 先建干净/误交付/无法识别的 `.pyc` 与冻结包样本；定义可解释的 high、medium、unknown，以及误报容忍度。增量扩展 `--check-delivery`，报告扫描范围与未解析范围。空结果或未识别结构不代表安全。
5. **P2：有条件的保护覆盖。** L3 方法与嵌套、参数改名、复杂 `__init__`/循环导入分开做提案。每项需最小真实需求、关键字调用/反射/框架兼容契约、原文与产物行为差分和明确跳过统计；不因竞品具备某模式就排期。
6. **独立研究 gate：free-threaded 3.15。** 用真正的 free-threaded 解释器和相关 runtime/扩展路径验证，再决定支持级别；普通 3.15 CI 不计作证据。

排序依据：P0 已有本仓可复现的生成行为；P1 直接决定受保护产物能否交付与调试，且与竞品文档所示的主流工作流相交；P2 需要先有使用案例和误报约束。当前没有足够的客户需求或对比实验支持原生 VM、云授权或新一轮 AST 变换。账单限制解除前，避免 private 仓库远端运行和新增高成本全矩阵。

## 重新排序的触发条件

若用户提交可公开的真实失败样本，按影响与可复现性提升相应任务；若打包样本全部通过，先发布兼容指南，不制造不必要的代码项目；若出现明确离线 key 生命周期需求，再评估 provider。每项从“提案”进入实施前，应写清可验收的最小范围、所属版本层和回退方案。
