# P1 打包交付验证：公开 wheel 的 Linux 小矩阵（2026-10-28）

状态：Linux/Windows 的最小交付矩阵完成；其他解释器及复杂应用仍待验证。此记录是组合交付证据，不是新增编译器或完整平台支持声明。两平台均使用公开 PyPI `pyobfus==0.10.0` wheel，而非本仓 editable checkout。Linux x86_64/WSL2 为 Python 3.12.3、PyInstaller 6.21.0、Nuitka 4.3.1、patchelf 0.19.1.0；Windows 11 为 Python 3.12.14、PyInstaller 6.21.0。具体包版本是本次固定实验环境，不代表滚动最新版；本地 Windows 临时环境避免了新增 GitHub Actions 分钟。

## 样本和流程

基于 [多模块夹具](https://github.com/zhurong2020/pyobfus/blob/main/integration_tests/packaging/multimodule/README.md)：入口 `main.py`、`storefront` 包及子包、相对导入、跨模块类/函数调用、正常报价和未知 tier 的异常。先由公开 wheel 混淆整个目录，mapping 存放在输出树之外；原文和混淆源码对 `pro` 均输出 `pro: 65.88`。资源变体另加 `data/label.txt`（内容 `pricing-v1`）及入口读取 `Path(__file__).resolve().parent / 'data' / 'label.txt'`；资源由打包命令显式纳入，原文和混淆源码均输出两行 `pricing-v1`、`pro: 65.88`。

| 工具/模式 | 输入与资源参数 | 隔离运行结果 | 异常与 mapping |
|---|---|---|---|
| PyInstaller onedir | 混淆入口；`--add-data SOURCE:data` | 正常报价、资源变体均通过 | 未知 tier 的三个项目帧可映射 |
| PyInstaller onefile | 同上 | 正常报价、资源变体均通过 | 异常帧符合 onedir；本仓既有 onefile 回归覆盖相同基准夹具 |
| Nuitka onefile | 混淆入口；`--include-data-files=SOURCE=data/label.txt` | 正常报价、资源变体均通过 | 从临时解包目录产生的三个项目帧全部映射，`unmatched_names=[]` |

Windows 的 PyInstaller onedir/onefile 使用同一资源变体：公开 wheel 从 WSL 临时源目录生成 Windows staging；原文与混淆源码均输出 `pricing-v1` 和 `pro: 65.88`。两种冻结产物去掉继承的 `PYTHONPATH` 后仍输出相同结果，未知 tier 均非零退出；各自记录的三个项目帧经 Windows 上的私有 mapping 恢复，`unmatched_names=[]`。PowerShell 重定向给错误日志增加宿主包装行，但没有改变 Python 帧的映射结果。Windows onefile 的递归归档列表仅观察到预期 `storefront` 模块和 `data\label.txt`，没有 mapping/私有目录名称。

Linux 可执行文件在 `/tmp` 中以清空环境变量、仅设置临时 `HOME` 和基本 `PATH` 的命令运行；Windows 可执行文件在临时目录中去掉继承的 `PYTHONPATH` 后运行。两者均未依赖项目源码目录或 pyobfus 运行时命令。故意的未知 tier 均以非零退出并报告相同的 `ValueError`。PyInstaller 归档递归目录只列出 `storefront` 模块与显式纳入的 `data/label.txt`，没有 mapping、私钥或构建私有目录。对 Linux 三个打包输出的普通文件枚举未发现 `.py`、`.pyc`、mapping 或私钥侧车文件；对 onefile 二进制做 `strings` 搜索未发现五个被改名标识符与 `mapping.json`，但这不能证明无法提取或恢复。

公开 0.10.0 的 `--check-delivery` 对 PyInstaller onedir 外层目录返回 0 个已知问题，但不解析内部归档；对 Nuitka 的 `main.bin` 返回“需要目录或 `.whl`”错误。两者都不能据此判定冻结包内没有原始源码、字节码或秘密；这属于 [P2 交付诊断](ROADMAP.md) 的独立候选。

## 本次结论和剩余验收

这五个本地平台/模式组合在此小样本无需修改 pyobfus 产品代码。资源文件需要由调用方在混淆之后复制到 staging，并使用打包工具的数据文件参数；mapping 必须留在交付物外。Nuitka standalone 已由 [现有 Linux packaging lane](COMPILED_PACKAGING_COOKBOOK.md)验证，Nuitka onefile 本轮新增本地证据。Windows 上的 Nuitka、macOS、Python 3.15、复杂插件/动态导入以及真实应用未验证；遇到具体失败再最小化原因并决定是否提供 hook/示例。账户账单限制解除前，不增设高成本的远端全矩阵或 private 仓库运行。

## L3 预览的离线应用可用性

同一资源变体小应用另选 `storefront.checkout.quote_order` 为唯一 L3 顶层函数，使用公开 Core 0.10.0 和本地临时隔离 trial 构建，mapping 与 build report 保存在私有 staging。目标虚拟环境只安装公开 `pyobfus-runtime==0.1.1` 及其依赖，`pip show pyobfus` 确认没有 builder；在清空环境变量的目标进程中，设置应用密钥或在首次项目导入前注册 `set_key_provider` 都能输出 `pricing-v1` 和 `pro: 65.88`。缺失密钥在导入时抛出明确的 `LicenseBindingError`；错误密钥在调用加密函数时抛出 `OpacityRuntimeError`。未知 tier 的 traceback 经私有 mapping 还原：普通项目帧有原始行号，加密 `quote_order` 帧为 `name_only`、原始行号为空，runtime wrapper 帧保留未映射状态。

干净的新构建目录用 build report 执行 `--check-delivery`，6 个生成 `.py` 均匹配且无已知发现；在该目录运行后，检查器报告新生成的 5 个 `.pyc` 为信息项，但无法判断其来源。最终 staging 应在执行验证和打包前后分开管理，避免把运行产生的缓存误带入交付物。这里验证的是源目录交付，不推断 L3 与冻结包组合已兼容；该组合需要单独验收。
