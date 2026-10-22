# 首次使用流程核查（2026-10-22）

状态：阶段 1 完成。合成样例、PyPI Core 0.8.0、Linux / Python 3.12.3；不是客户使用调查，也不代表 Windows／所有框架验收。

## 方法与结果

先检查公开文档首页和产品页的发现／安装／版本选择入口，再在工作树之外创建两个全新 venv。构建环境只执行 `pip install pyobfus==0.8.0`，不安装本 checkout；目标环境仅有 Python 与 pip，确认不能导入 `pyobfus` 或 `pyobfus_runtime`。所有 CLI 使用隔离的 HOME，避免读取维护者许可证；未启动试用、购买或激活。

| 检查 | 结果 |
|---|---|
| 安装、发行版本、导入路径、`pip check` | 通过；来自公开 0.8.0 安装包 |
| 多模块原文正常运行与异常基线 | 通过；数量 2 输出 60，数量 0 抛出预期 ValueError |
| 按首页流程 `--check`、JSON dry-run | 通过 |
| 目录构建 + mapping + syntax/names verification + build report + trace marker | 通过 |
| 干净目标环境运行产物 | 输出同原文；不依赖 builder/runtime |
| 目标异常 + `--unmap` | 恢复 `invoice_total`、`checked_quantity` 原函数名及可用语句位置 |
| `--check-delivery` | 通过；mapping 与报告在交付目录外 |
| Pro 选择／命令入口 | 公开页可达；trial/register 帮助可用；未验证试用服务、付款或激活成功 |
| 独立文件目录构建请求 mapping | 构建成功、stderr 警告、没有 mapping；两个独立脚本异常只能保留混淆名 |

共 18 个命令步骤完成；私有日志和可复跑脚本在本地忽略目录 `docs/internal/adoption-2026-10-22/`。下载数据与邮箱不是本轮验收标准。

## 最小输入与复现

默认多模块样例：`src/demoapp/__main__.py` 从 `.invoice` 导入 `invoice_total`，后者从 `.rules` 导入数量校验函数；执行 `python -m demoapp 2` 和 `python -m demoapp 0` 对照。

独立文件缺口可用两个不相互导入的脚本复现：

```python
# independent/alpha.py
def calculate_invoice():
    raise ValueError("synthetic failure")
calculate_invoice()
```

`beta.py` 将函数名换为 `validate_receipt`。两文件会独立分配相同短标识符；不能把名字表直接并到一个全局反向字典。

```bash
pyobfus independent/ -o independent-dist/ --no-cross-file \
  --save-mapping private/independent.json --verify-syntax --json
python independent-dist/alpha.py
python independent-dist/beta.py
```

## 决策

默认 Community 的安装、构建、运行、调试流程在此合成样例中成立，没有证据表明需要重做首屏或新增用户限制。独立文件目录 mapping 是明确且可复现的现有工作流缺口，进入阶段 2。Pro 多模块保护范围应在阶段 3 单独设计，不把目录 warning 当作已经具备保护。公开入口检查：[文档首页](https://pyobfus.readthedocs.io/en/latest/)、[产品页](https://zhurong2020.github.io/pyobfus/)。
