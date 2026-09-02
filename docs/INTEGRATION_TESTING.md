# 集成测试指南

本指南说明如何在不发布到 PyPI 的前提下，用**真实项目代码**测试 pyobfus —— 既
包括仓库自带的端到端测试，也包括拿你自己的代码库做验证的日常工作流。

## 🎯 目标

- ✅ 不需要先上传 PyPI 再安装（用可编辑安装即时生效）
- ✅ 用真实代码验证混淆是否**语法正确、可运行、行为不变**
- ✅ 快速迭代：改完 pyobfus 源码立刻重测

## 🚀 环境准备

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
```

可编辑安装（`-e`）后，对 `pyobfus/` 源码的任何修改都会立即在 `pyobfus`
命令与 `python -m pyobfus` 中生效，无需重新安装、无需版本号、不污染 PyPI。

## 🧪 仓库自带的端到端测试

集成测试位于 `integration_tests/test_cli_end_to_end.py`。它**以子进程方式驱动
真实安装的 CLI**（`python -m pyobfus ...`），而不是直接调用内部函数，因此覆盖
的是用户实际运行的路径。当前覆盖：

- CLI 可用性：`--version` / `--help`
- 单文件混淆：混淆后仍能执行、输出与源码不同、字节码可编译
- 目录混淆：配合 `pyobfus.yaml` 的多文件项目
- 错误处理：缺失输入等场景干净退出

运行（作为独立 pytest 根，与核心套件分开收集）：

```bash
venv/bin/pytest integration_tests/ -v
```

> 说明：核心套件 `tests/`、MCP 套件 `pyobfus_mcp/tests/`、端到端套件
> `integration_tests/` 是**三个独立的 pytest 根**，CI 也分成独立 job 跑，不要
> 用一次 `pytest` 同时指向多个根。详见 [`AGENTS.md`](https://github.com/zhurong2020/pyobfus/blob/main/AGENTS.md) 的 build/test 小节。

## 🔧 用你自己的代码库做验证

不需要专门的辅助脚本 —— 直接对目标项目（的副本）跑 CLI 即可。建议按下面的
顺序逐层加码：

### 1. 先做预检（不写文件）

```bash
pyobfus --check /path/to/your/project --json
```

`--check` 会在真正混淆前标出 `eval`/`exec`、动态属性访问、框架反射点，以及声明
了却在公共 PyPI 上解析不到的依赖名。JSON 输出便于脚本化判断。

### 2. 预览计划（不写文件）

```bash
pyobfus /path/to/your/project -o /tmp/out --dry-run --json
```

`--dry-run --json` 返回带版本号的 `plan` 对象：生效配置、被选中/被排除的文件
及原因、以及产物的交付角色，全程不写盘。

### 3. 实际混淆 + 构建后语法校验

```bash
pyobfus /path/to/your/project -o /tmp/out --verify-syntax --json
```

`--verify-syntax` 在写盘后于内存中 `compile()` 生成的 `.py`（不 import、不执行、
不写 `__pycache__`），报告 `syntax_valid`。

### 4. 验证行为不变（最重要的一步）

混淆的正确性最终要靠**运行目标项目自己的测试套件**来判断：把混淆产物放到
`PYTHONPATH` 前面，或安装到一个干净的 venv，然后跑该项目的 pytest / 冒烟脚本，
确认结果与混淆前一致。跨文件项目请注意：顶层公开名会被改名，用
`--save-mapping mapping.json` 保存映射，需要反解生产环境 traceback 时配合
`pyobfus --unmap --trace error.log --mapping mapping.json`。

### 自定义混淆配置

日常用配置文件（`pyobfus.yaml`）或 preset 最省事：

```bash
pyobfus /path/to/your/project -o /tmp/out --config pyobfus.yaml
pyobfus --init /path/to/your/project        # 自动探测框架，生成 pyobfus.yaml
```

也可以在 Python 里构造配置对象直接调库：

```python
from pyobfus.config import ObfuscationConfig

config = ObfuscationConfig()
config.string_encoding = True
config.preserve_param_names = True
config.exclude_names.add("important_function")
```

## 💡 典型工作流（改 pyobfus 源码时）

```bash
# 1. 修改 pyobfus 代码（可编辑安装，改完即生效）
vim pyobfus/transformers/some_transformer.py

# 2. 单元测试
venv/bin/pytest tests/ -q

# 3. 端到端测试
venv/bin/pytest integration_tests/ -v

# 4. 拿真实项目回归
pyobfus --check /path/to/real/project --json
pyobfus /path/to/real/project -o /tmp/out --verify-syntax --json
#    然后在 /tmp/out 上跑该项目自己的测试确认行为不变
```

## ➕ 新增你自己的集成用例

在 `integration_tests/` 下按现有 `test_cli_end_to_end.py` 的风格加测试即可 ——
用 `run_cli(...)` 辅助函数以子进程驱动 CLI，断言退出码 / 输出 / 产物：

```python
def test_my_project_obfuscates_cleanly(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "m.py").write_text("def f(x):\n    return x + 1\n")
    out = tmp_path / "out"
    result = run_cli(str(src), "-o", str(out), "--verify-syntax", "--json")
    assert result.returncode == 0
```

## 📊 为什么用可编辑安装而不是「上传 PyPI 再装」

| 特性 | 上传 PyPI 再安装 | 可编辑安装 (`pip install -e .`) |
|------|------------------|-------------------------------|
| 迭代速度 | 慢（上传 + 安装） | 快（改完即生效） |
| PyPI 污染 | 是 | 否 |
| 版本管理 | 需要新版本号 | 无需版本号 |
| 调试 | 困难 | 容易（`-v` / `--json`） |

## 🐛 故障排除

**`ModuleNotFoundError: No module named 'pyobfus'`** —— 没做可编辑安装：

```bash
pip install -e ".[dev]"
```

**改了源码不生效** —— 当前环境不是可编辑安装：

```bash
pip uninstall pyobfus && pip install -e ".[dev]"
```

**`'pyobfus' is a package and cannot be directly executed`** —— 当前工作目录
（或其兄弟目录）恰好叫 `pyobfus`，被 `python -m pyobfus` 抢先命中。换个工作
目录运行，或直接用 `pyobfus` 命令而非 `python -m pyobfus`。

## 📚 相关文档

- [integration_tests/test_cli_end_to_end.py](https://github.com/zhurong2020/pyobfus/blob/main/integration_tests/test_cli_end_to_end.py) - 仓库内的端到端 CLI 集成测试
- [AGENTS.md](https://github.com/zhurong2020/pyobfus/blob/main/AGENTS.md) - build/test/lint 约定（三个 pytest 根、Python 3.9–3.14 目标等）
- [CURRENT_PLAN_ZH.md](CURRENT_PLAN_ZH.md) - 当前计划与冷启动入口
