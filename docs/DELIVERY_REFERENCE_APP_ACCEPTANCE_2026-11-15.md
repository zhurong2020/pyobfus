# 公开交付参考应用：最小范围与验收合同

日期：2026-11-15。状态：**范围与接受标准已定义；公开应用和 Community 目录契约
已实现，Windows Nuitka 验收尚未执行**。本文不批准发布、扩平台矩阵、引入托管密钥或改变 Community／Pro
边界。

## 目的

用一个公开、可重复构建的小应用回答同一个交付问题：保护后的多模块 Python 应用能否
保留正常行为、资源访问和可诊断异常，并在冻结交付后证明源码、mapping 和密钥没有
误入成品。

它不是强度基准、样板商城或新框架。第一版只把现有能力串成一条可审计路径，并作为
[Windows Nuitka standalone 单组合方案](NEXT_DELIVERY_VALIDATION_PLAN.md)的唯一输入。

## 用户、问题与版别

- 用户：向客户交付 Windows Python 小应用的个人开发者或小团队。
- 问题：现有功能分散在示例、打包夹具和验收脚本中，用户无法从一个公开案例看清
  “保护 → 构建 → 运行 → 排障 → 交付检查”的完整闭环。
- Community：原文基线、多模块普通保护、mapping 私下保存、traceback 还原、构建／
  覆盖报告和交付检查。
- Pro：在同一应用上的 L3 与应用自管 key 注入、缺失／错误 key 负例。Pro lane 只能在
  隔离 trial 或明确许可环境运行，不读取维护者真实 `~/.pyobfus`。
- 不新增付费墙：正确性、诊断和本地交付检查仍属于 Community。

## 第一版应用

第一版以现有 `integration_tests/packaging/multimodule/` 的 storefront 为语义基线，
公开副本放入 `examples/delivery_reference/`。复用可以避免同时发明新业务逻辑和新打包
路径，但公开示例必须是自包含、可阅读的源树，不能依赖测试目录运行。

最小文件与行为：

| 组成 | 最小要求 |
|---|---|
| 入口 | `main.py`；默认或 `pro` 参数打印确定性报价 |
| 多模块 | `storefront` 包、子包、相对导入和跨模块类调用 |
| 资源 | `data/label.txt`，通过 `importlib.resources` 或明确的应用资源 API 读取 |
| 动态导入 | 一个固定 allowlist 的本地插件模块；不得从用户输入拼任意模块名 |
| 可映射异常 | `bogus_tier` 触发稳定的 `ValueError` 和项目帧 |
| key provider | 单独的应用模块从进程环境读取测试 key；不把 key 常量写进仓库或产物 |
| 配置 | Community 与 Pro L3 分开；默认命令不需要许可 |
| 文档 | README 给出原文、保护、运行、unmap 和交付检查命令及边界 |

确定性基线至少包括：

- 正常：退出 0，输出资源标签与 `pro: 65.88`；同一环境重复运行一致。
- 业务负例：`bogus_tier` 非零退出，异常类型为 `ValueError`，信息不依赖随机名称。
- 资源负例：移除资源后明确失败，不由 pyobfus 隐式补包。
- Pro key 负例：缺失／错误 key 均失败关闭；错误不得回退到 Community 或静默跳过 L3。

## 目录与证据边界

每次验收使用独立临时根，分为：

```text
source/       公开参考应用快照
protected/    生成的保护源码
private/      mapping、原始 trace、许可／trial 状态、完整日志
build/        冻结工具中间产物
delivery/     唯一允许交给消费者的树
consumer/     隐藏 source/protected 后的运行位置
```

`private/`、`source/`、`protected/` 和 `build/` 不得复制到 `delivery/`。HOME、USERPROFILE、
trial、run counter 和缓存全部绑定到临时根；清除继承的 `PYOBFUS_LICENSE_KEY`、
`PYTHONPATH` 与 `PYTHONHOME`。任何真实客户源码、许可、私钥或客户标识都不进入公开案例、
日志、artifact 或提交。

## 分阶段接受标准

| 阶段 | 必须通过的标准 |
|---|---|
| A. 原文 | 正常、业务负例、资源负例形成固定基线；输入文件哈希已记录 |
| B. Community 保护 | 普通目录输出通过语法验证；正常行为与 A 一致；异常可用私有 mapping 还原到实际项目帧 |
| C. Pro L3 | 仅在隔离状态运行；正确 key 行为与 A 一致；缺失／错误 key 失败关闭；覆盖报告如实列出保护和跳过项 |
| D. PyInstaller | onedir、onefile 仅复用已有验证路径；若重跑，固定工具版本并在隐藏源码后运行 |
| E. Windows Nuitka | 只执行 Windows x64／CPython 3.12／standalone 一格，严格采用 `NEXT_DELIVERY_VALIDATION_PLAN.md` 的 D1–D10 |
| F. 交付审计 | delivery 不含项目原始 `.py`、mapping、私钥、trial/license 状态、构建目录或原始 trace；unknown 与未解析结构不得写成 clean |
| G. 可复现记录 | 记录 OS、Python、pyobfus wheel URL/SHA-256、打包器、编译器、命令、输入／产物哈希、耗时和 pass/fail/blocked/unknown |

第一版总体通过要求：A、B、E、F、G 全部通过；C 可在没有隔离 Pro 条件时明确记为
blocked，但不得伪装为已验证；D 的既有结果可以引用，不过必须注明日期、版本和不同的
fixture 提交。任何关键项为 unknown 时，总结最多为 partial。

## 停止条件

- 原文基线失败：先修参考应用，不进入保护或冻结。
- Community 保护源码行为漂移：最小化为正确性缺陷，不通过打包参数绕过。
- 原文 Nuitka 对照也失败：归为工具链／夹具问题，不先归因于 pyobfus。
- 需要联网下载、编译器或系统变更而环境未获允许：记 blocked，不换平台后宣称同组通过。
- 首次 Windows 构建累计超过 20 分钟，或诊断超过 10 分钟：停止并记录证据，不自动扩矩阵。
- 发现敏感材料可能进入公开 artifact：立即停止，不上传、不提交该产物。

## 实施顺序

1. ~~从现有 multimodule 语义复制一个自包含公开示例；补资源、固定 allowlist 动态导入、
   key-provider 接口和 README。~~ 2026-11-15 完成于 `examples/delivery_reference/`。
2. ~~增加轻量测试，验证原文正常／负例和 Community 保护目录行为；不在普通 CI 安装
   Nuitka。~~ 2026-11-15 定向测试 5 项及 `scripts/check.sh` 通过。
3. ~~用仓库 `venv/` 验证 mapping/unmap 与 `--check-delivery` 的完整证据记录。~~
   2026-11-15 完成；测试明确携带 build report 与 provenance，未记录 Python 文件会产生
   medium 而非 clean。
4. 在明确许可的隔离状态验证 Pro lane；不能满足时保留 blocked。
5. 以该示例执行单一 Windows Nuitka standalone 方案，先产出结果和 cookbook；只有发现
   可复用的产品缺口才提出代码改动。

完成本合同本身不等于批准第 1–5 步的发布或外部上传。实现提交仍须经过
`scripts/check.sh` 和相关测试；任何发布、Worker 部署或客户通知另设 gate。

## 2026-11-15 Windows 执行门槛结果

只读环境盘点发现原生 Windows 只有 CPython 3.11，未发现目标 CPython 3.12、Nuitka、
`cl.exe` 或 Visual Studio 2022。依照停止条件，本次记为 **blocked（工具链缺失）**：未
自动安装、未换版本、未把 WSL 或 3.11 结果填作 Windows 3.12 standalone 通过。解除阻塞
需要维护者另行同意安装固定 Python 3.12、Nuitka 与 MSVC，或批准一个边界明确的单格
hosted Windows 验收。

## How to run

The focused runner is `scripts/validate_windows_nuitka_delivery.py`. Push the
prepared revision to `acceptance/windows-nuitka`, or dispatch
`windows-nuitka-acceptance.yml` once it is available on the default branch.
The maintainer approved one hosted Windows run; do not trigger both paths or
rerun automatically. This preparation does not launch that run.

The workflow uses Windows 2022, x64 Python `3.12` (actual patch recorded;
3.12.14 availability was not confirmed), public `pyobfus==0.14.0`, and
`nuitka==4.3.1`. This supersedes the plan's historical Core 0.12.0 input only.
No existing upload-artifact SHA pin was found; v4.6.2 is pinned to
`ea165f8d65b6e75b540449e92b4886f43607fa02`.
Only sanitized `evidence/` is uploaded, retained for 14 days. Full logs,
mapping, traces and compiler reports remain in the ephemeral private staging
root. A failed or blocked required stage fails the job; unknowns (for example
uninspected frozen internals) keep the overall status at `partial` in the
evidence, never `pass`. The
consumer runs on the builder with Python preinstalled, not a clean target.
Results are recorded only after execution; no step is pre-filled as passed.
Pro stage C stays blocked and is never attempted with a real key.
