# 下一项交付验证方案：Windows Nuitka standalone

准备日期：2026-11-03。状态：单组合验收设计，尚未执行，不新增平台支持承诺。
默认候选为 Windows x64／CPython 3.12／Nuitka standalone；实际执行仍由真实交付需求触发。
本方案不修改 0.12.0 候选、不安装工具、不新增每 PR 的远端矩阵。

## 选择依据与范围

[已有打包记录](https://github.com/zhurong2020/pyobfus/blob/main/docs/P1_PACKAGING_VALIDATION_2026-10-28.md)已经覆盖公开 0.10.0 的 Linux Nuitka
standalone/onefile，以及 Windows PyInstaller onedir/onefile；Windows Nuitka 仍是独立缺口。
[10-30 路线复核](https://github.com/zhurong2020/pyobfus/blob/main/docs/ROADMAP_REVIEW_2026-10-30.md)要求一次只扩一个所需组合。
先沿用 Python 3.12 和现有小夹具，避免同时更换打包器、解释器和保护层。

| 轴 | 本次建议 | 本轮不扩展的轴 |
|---|---|---|
| 目标 | 一个明确版本的 Windows x64 | ARM、macOS、Linux 新组合 |
| 解释器 | CPython 3.12.14 x64，沿用既有 Windows 基线 | Python 3.15 / 3.15t |
| 打包器 | Nuitka 4.3.1，沿用已有 Linux 实测版本作为比较基线 | 不把此版本称为最新版，不同时评估其他版本 |
| 模式 | `--mode=standalone` | onefile、安装器、整包 Cython |
| 保护 | Community 普通跨文件输出 | L3、资源 provider、设备绑定、到期策略 |
| Core | 执行时已发布的 0.12.0 精确 wheel | 不把本地同名候选当 PyPI 发布物 |

用户/买方是准备交付 Windows Python 小应用的开发者；本次证据是已有矩阵的明确空白，
尚无新客户失败案例。因此先备好验收设计，不将候选自动升级成必须开发的功能。
基础交付正确性、诊断与公开指南属于 Community；不改变版别，参见
[edition-boundary](EDITION_BOUNDARY_POLICY.md)。

## 开始条件与执行边界

1. 有明确 Windows Nuitka 交付目标；记录所需 Windows 版本、架构、部署环境和异常调试要求。
2. Core 0.12.0 已正式发布，已核对其 wheel/sdist 来源、哈希和 PEP 740；若尚未发布则保持待执行。
3. 冻结 Python/Nuitka 版本、runner 或目标 OS build、实际 C 编译器/SDK 版本及输入哈希。
   MSVC 使用已安装的 Visual Studio 2022 或兼容工具链；`--msvc=latest` 只作选择器，
   实际解析到的 `cl.exe`/工具集必须记入记录，不宣称该标签可保证跨次相同环境。
4. 有可隔离的 Windows 消费环境。若只能在构建机清理环境变量后运行，明确记为局部验收，
   不能把它填成“干净目标通过”。目标预装 Python 的情况也必须记录，不推断无 Python 宿主已验证。
5. 维护源和命令始终来自 WSL `~/projects/` checkout。原生 Windows 测试由该 checkout
   准备和发起；Windows 临时 staging 只保存生成快照/产物，不作为新的维护或发布源。
   不编辑、构建或执行 OneDrive 迁移副本；若无法满足此边界则停止本地执行，
   在明确目标后选择单格 hosted Windows 环境并先约定私有证据保留方式。

所有 HOME/USERPROFILE、构建缓存及运行计数指向本次临时目录；清除继承的
`PYOBFUS_LICENSE_KEY`、`PYTHONPATH` 和 `PYTHONHOME`。Community 样本不需要 Vault 或真实许可。
工具缺失、编译器不可用或版本不匹配记为环境阻塞，不默默升级到 latest 或换平台后继续宣称同组通过。

## 夹具和目录

复用 [multimodule](https://github.com/zhurong2020/pyobfus/blob/main/integration_tests/packaging/multimodule/README.md) 和
[`scripts/validate_packaged_delivery.py`](https://github.com/zhurong2020/pyobfus/blob/main/scripts/validate_packaged_delivery.py)
的资源、staging、traceback 和报告处理思路。该脚本目前是 PyInstaller 验收入口，
**不能把它直接称为已实现的 Nuitka runner**。本轮不另建通用验证框架。

建议目录分离为 `source/`、`protected/`、`private/`、`build/`、`delivery/` 和 `consumer/`。
mapping、原始 trace、编译报告与构建源码只留私有证据目录，交付树只放 standalone 所需文件。

夹具仍是入口 `main.py`、`storefront` 包/子包、相对导入、跨模块调用与异常。
使用现有验收脚本的同一资源变体 `data/label.txt`，内容 `pricing-v1`；
正常参数为 `pro`，未知参数为 `bogus_tier`。
先捕获当前原文基线，再逐阶段比较：报价为 `pro: 65.88`，资源文本必须保留，
两行的顺序按实际原文基线判定，不从历史报告的叙述顺序推断。

## 执行顺序与判定

| 步骤 | 动作 | 通过标准／停止条件 |
|---|---|---|
| D1 | 新环境安装精确公共 wheel；`pip check`、记录工具/OS/编译器版本 | 来源/版本和环境满足冻结表；不使用 editable 产物证明公开 wheel |
| D2 | 原文正常/异常/资源运行 | stdout、exit、异常类型和项目帧形成基线；基线失败即停止 |
| D3 | Community 跨文件构建，mapping/report 放输出外；语法验证 | 未授权状态仍能正常构建，不出现 Pro/trial 副作用 |
| D4 | 混淆源码正常/异常运行 | 正常输出与 D2 一致；异常可解释且项目帧按当前 mapping 能力还原 |
| D5 | 原文 standalone 对照，再构建混淆 standalone；显式包含资源 | 对照构建失败先记工具链/夹具问题；不先归因于 pyobfus |
| D6 | 隐藏原文和混淆树，移交 delivery 到隔离消费目录/目标 | 运行不能依赖源树、builder、当前工作目录或继承 Python 路径 |
| D7 | 消费环境正常/异常/资源运行 | 输出、异常类别和资源与基线匹配；记录目标实际依赖和限制 |
| D8 | 用私有 mapping 对冻结异常做还原 | 只还原实际出现的帧；不臆造 Nuitka 已移除的帧/行号，不把部分恢复填成完整恢复 |
| D9 | 枚举交付文件、审查编译报告和交付检查 | 无原文、mapping、私钥、`.build`、调试证据混入；已知未知项保留 |
| D10 | 归档哈希、命令、时间、结果与支持边界 | 每项 pass/fail/blocked/unknown 独立；未执行项不得预填 pass |

Nuitka 命令轮廓如下，路径由未来的受控 staging 脚本填入；不是今天已运行的命令：

```text
<target-python> -m nuitka --mode=standalone --msvc=latest
  --include-data-files=<protected>/data/label.txt=data/label.txt
  --output-dir=<build> --report=<private>/nuitka-report.xml <protected>/main.py
```

先核对锁定版本的 `--help` 及编译器解析结果，再执行。资源纳入规则和 standalone 的含义
依据 [Nuitka 官方手册](https://nuitka.net/user-documentation/user-manual.html)
（2026-11-03 查阅）；当前手册不能替代所锁定版本或目标平台的实际验收。

## 关键负例与诊断边界

- 未知 tier 必须非零退出并保留同类异常；冻结工具增加的宿主包装行单独记录。
- 故意不带资源时应明确失败；此负例归为 staging/工具配置，不改 pyobfus 来隐式打包数据。
- 源树隐藏后仍可运行才通过独立消费门槛；仅构建成功不够。
- `.py`/`.pyc` 发现按来源分类，不能把标准库所需文件和原项目源码混为一类；
  不能靠字符串检索未命中来证明无法提取。
- 当前 `--check-delivery` 对冻结外壳报告未检查内部载荷，`warn`/exit 0 不表示内部安全。
  本方案不增加冻结载荷解析器，不执行或反序列化任意不可信载荷。
- 真实项目源码/私钥/原始 mapping 不上传公共 CI artifact。若换 hosted 环境，
  先解决证据保留边界；不能为了拿到“干净目标”结果泄露诊断材料。

## 成本、结果模板和后续门槛

未来首次执行预算：一个平台组合，构建累计最多 20 分钟、目标运行/诊断最多 10 分钟；
构建任务失败后只做有原因的定向重跑，不自动扩 OS/Python 矩阵或同时跑 onefile。
预算是停止条件，不是性能承诺；未计时不填估算结果。

| 字段 | 待执行记录 |
|---|---|
| 触发需求及去标识案例 | 待填写 |
| Core wheel URL/版本/SHA-256/来源核验 | 待填写 |
| 夹具源码提交、输入哈希、配置、资源变体 | 待填写 |
| Windows/CPU/Python/Nuitka/MSVC/SDK | 待填写 |
| 原文／混淆源码／两种 standalone 对照结果 | 待填写 |
| 隔离目标能力、是否预装 Python、源树是否隐藏 | 待填写 |
| 原始异常、还原帧与明确未恢复范围 | 私有记录，公开只写结果摘要 |
| 交付检查范围、残余 unknown、文件清单与产物哈希 | 待填写 |
| 实际耗时／预算／重跑原因 | 待填写 |
| 总结 | pass / partial / fail / blocked，当前为未执行 |

全通过只补“该样本＋该固定组合”的验证记录，不自动新增产品代码或宣称普遍支持。
发现行为差异先最小化并按正确性问题处理；需要 hook 时先产出可复制示例。
onefile、L3 冻结、macOS 或 3.15t 必须有各自需求与范围，不能从本组外推。
