# Python 3.8 兼容性指南

> ⚠️ **历史文档（2026-06-18 起）**：Python 3.8 已于 **0.5.0** 移除（EOL 2024-10，`requires-python>=3.9`）。本文记录的 astunparse/3.8 问题已不再适用，仅作历史归档保留。

**创建日期**: 2025-11-12
**最后更新**: 2026-04-22

## 概述

本文档记录了pyobfus项目中遇到的Python 3.8兼容性问题及其解决方案，以避免将来再次遇到相同问题。

## 背景

pyobfus支持Python 3.8-3.14。Python 3.8与3.9+在AST API方面有重要差异：

- **Python 3.9+**: 内置 `ast.unparse()` 函数
- **Python 3.8**: 无 `ast.unparse()`，需要使用 `astunparse` 库

## 问题记录

### 问题1: ast.arguments() 缺少必需参数

**发现时间**: 2025-11-12
**影响范围**: 43个测试失败（Python 3.8 CI）

#### 错误信息
```
AttributeError: 'arguments' object has no attribute 'vararg'
```

#### 根本原因
在手动创建 `ast.arguments()` 节点时，未提供 `vararg` 和 `kwarg` 参数。

**错误代码**:
```python
ast.arguments(
    posonlyargs=[],
    args=[ast.arg(arg="s", annotation=None)],
    kwonlyargs=[],
    kw_defaults=[],
    defaults=[],
)
```

#### 解决方案
显式提供 `vararg=None` 和 `kwarg=None` 参数：

```python
ast.arguments(
    posonlyargs=[],
    args=[ast.arg(arg="s", annotation=None)],
    vararg=None,           # 必需！
    kwonlyargs=[],
    kw_defaults=[],
    kwarg=None,            # 必需！
    defaults=[],
)
```

#### 修复提交
- Commit: 62e39f3
- 文件: `pyobfus/transformers/string_encoder.py`, `pyobfus_pro/anti_debug.py`, `pyobfus_pro/string_aes.py`

---

### 问题2: ast.Constant() 缺少 kind 参数

**发现时间**: 2025-11-12
**影响范围**: 43个测试失败（Python 3.8 CI）

#### 错误信息
```
'Constant' object has no attribute 'kind'
```

#### 根本原因
在Python 3.8中，`astunparse` 期望 `ast.Constant` 节点有 `kind` 属性。手动创建Constant节点时未提供此参数。

**错误代码**:
```python
ast.Constant(value=encoded)
```

#### 解决方案
显式提供 `kind=None` 参数：

```python
ast.Constant(value=encoded, kind=None)  # kind=None 对所有版本都兼容
```

#### 修复提交
- Commit: a0d7a9d
- 文件: `pyobfus/transformers/string_encoder.py` (2处), `pyobfus_pro/anti_debug.py` (2处), `pyobfus_pro/string_aes.py` (3处)

---

### 问题3: 测试代码直接使用 ast.unparse()

**发现时间**: 2025-11-12
**影响范围**: 7个测试失败（Python 3.8 CI）

#### 错误信息
```
AttributeError: module 'ast' has no attribute 'unparse'
```

#### 根本原因
测试代码直接调用 `ast.unparse()`，在Python 3.8中不存在。

**错误代码** (tests/test_issue_7_class_attributes.py):
```python
obfuscated_code = ast.unparse(transformed)
```

#### 解决方案
使用我们的 `CodeGenerator` 类，它有内置的Python 3.8回退逻辑：

```python
from pyobfus.core.generator import CodeGenerator

obfuscated_code = CodeGenerator.generate(transformed)
```

#### 修复提交
- Commit: b3bc1b7
- 文件: `tests/test_issue_7_class_attributes.py`

---

### 问题4: 随机数据导致的不稳定测试

**发现时间**: 2025-11-12
**影响范围**: 1个测试间歇性失败（所有Python版本）

#### 问题描述
`test_string_aes.py::test_empty_string` 检查字符串 "ab" 不在生成的代码中，但随机生成的加密密钥有时包含 "ab" 子串（如 "6YThA29sZHpcDOgG2NVZ36zY**ab**2HQ="）。

#### 解决方案
使用更独特的测试字符串，不太可能在base64编码中随机出现：

```python
# Before: short = "ab"
# After:  short = "test_xyz"

# Before: assert "ab" not in obfuscated_code
# After:  assert '"test_xyz"' not in obfuscated_code  # 更精确的断言
```

#### 修复提交
- Commit: b3bc1b7
- 文件: `tests/test_string_aes.py`

---

### 问题5: 类型提示语法不兼容 (v0.2.0)

**发现时间**: 2025-12-09
**影响范围**: 多个源文件在Python 3.8 CI失败

#### 错误信息
```
TypeError: 'type' object is not subscriptable
```

#### 根本原因
Python 3.9+ 支持直接使用 `tuple[str, dict]` 和 `list[Set[str]]` 语法。但在Python 3.8中，必须从 `typing` 模块导入 `Tuple` 和 `List`。

**错误代码**:
```python
def some_function() -> tuple[str, dict]:  # Python 3.9+ only
    pass

self._scope_stack: list[Set[str]] = []  # Python 3.9+ only
```

#### 解决方案
使用 `typing` 模块中的类型：

```python
from typing import Tuple, List, Set

def some_function() -> Tuple[str, dict]:  # 兼容 Python 3.8+
    pass

self._scope_stack: List[Set[str]] = []  # 兼容 Python 3.8+
```

#### 修复提交
- Commit: e72efc9
- 文件:
  - `pyobfus/transformers/exported_name_transformer.py`
  - `pyobfus/transformers/imported_name_transformer.py`
  - `pyobfus/transformers/local_name_transformer.py`
  - `pyobfus/transformers/import_rewriter.py`
  - `pyobfus/transformers/all_list_updater.py`

---

### 问题6: astunparse 输出格式差异 (v0.2.0)

**发现时间**: 2025-12-09
**影响范围**: 测试断言失败

#### 错误信息
```
AssertionError: 'class I0:' not in 'class I0():'
```

#### 根本原因
`astunparse` 库（Python 3.8）和 `ast.unparse()`（Python 3.9+）生成的代码格式略有不同：

| 代码结构 | ast.unparse (3.9+) | astunparse (3.8) |
|---------|-------------------|-----------------|
| 空基类 | `class Foo:` | `class Foo():` |

#### 解决方案
测试断言需要同时处理两种格式：

```python
# 错误做法：精确匹配
assert "class I0:" in new_source  # Python 3.8 失败！

# 正确做法：兼容两种格式
assert "class I0" in new_source and (
    "class I0:" in new_source or "class I0():" in new_source
)
```

#### 修复提交
- Commits: b40d5cc, 9963bdb
- 文件:
  - `tests/transformers/test_exported_name_transformer.py`
  - `tests/transformers/test_all_list_updater.py`
  - `tests/transformers/test_import_rewriter.py`

---

### 问题7: 便利函数中使用 ast.unparse (v0.2.0)

**发现时间**: 2025-12-09
**影响范围**: 便利函数调用在Python 3.8失败

#### 错误信息
```
AttributeError: module 'ast' has no attribute 'unparse'
```

#### 根本原因
不仅测试文件，源代码中的便利函数（如 `rewrite_imports()`）也直接使用了 `ast.unparse()`。

**错误代码** (pyobfus/transformers/import_rewriter.py):
```python
import ast as ast_module
new_source = ast_module.unparse(new_tree)  # Python 3.8 失败！
```

#### 解决方案
在所有源代码中也使用 `CodeGenerator`：

```python
from pyobfus.core.generator import CodeGenerator
new_source = CodeGenerator.generate(new_tree)
```

#### 修复提交
- Commit: d4d44ae
- 文件: `pyobfus/transformers/import_rewriter.py`

---

### 问题8: 单个 Pro 特性的 CLI 集成测试在 Python 3.8 上 flaky

**发现时间**: 2026-04-22
**影响范围**: `tests/test_cli_pro_paths.py::TestProFeatureExecution` 的 4 个单特性测试

#### 症状

非确定性失败：同一次 push 第一次 CI 运行可能是 macOS 3.8 失败、重跑后 Windows 3.8 失败。Ubuntu 3.8 和 Python 3.9-3.14 × 所有 OS 全过。失败时的错误只是：

```
FAILED tests/test_cli_pro_paths.py::TestProFeatureExecution::test_dead_code_injection - assert 1 == 0
 +  where 1 = <Result SystemExit(1)>.exit_code
```

首次失败（macOS 3.8）甚至显示 `648 passed, 7 skipped`，但 `Process completed with exit code 1` 没有具体 traceback —— astunparse 在某些输入上生成的 AST pytest-cov 收尾阶段异常退出。

#### 根本原因

单特性 Pro CLI 测试（`test_control_flow_flattening` / `test_string_encryption` / `test_anti_debug` / `test_dead_code_injection`）都走 `CliRunner().invoke(main, [..., "--<feature>", "-v"])`，最终会穿过 `astunparse → 生成代码` 的路径。和问题 #1/#2 一样，这条路径在 Python 3.8 上对某些 AST 输入行为不一致，在 macOS ARM64 / Windows runner 上表现为 flaky。

和 `ee80edf` 提交里已处理的 *组合* Pro 测试（`test_all_pro_features_combined` 等）同一问题，只是单特性测试当时没触发。

#### 解决方案

对这 4 个单特性 CLI 测试加 `@requires_py39` 装饰器（与已有的组合 Pro 测试保持一致）：

```python
@requires_py39
@patch("pyobfus.cli.is_trial_active", return_value=True)
@patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
def test_dead_code_injection(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
    ...
```

纯 transformer 单元测试（`tests/test_control_flow_flattening.py`、`tests/test_dead_code_injection.py`、`tests/test_string_aes.py`、`tests/test_anti_debug.py`）**继续在所有 Python 版本上运行** —— 它们不经 astunparse 生成代码路径，所以不受影响。

#### 修复提交

- Commit: （即将提交）
- 文件: `tests/test_cli_pro_paths.py`

#### 诊断要点（下次遇到直接照抄）

| 信号 | 判断 |
|---|---|
| 只有 Python 3.8 matrix 某一个 OS 失败，其他 OS 3.8 和所有 3.9+ 通过 | Python 3.8 astunparse flake |
| `Process completed with exit code 1` 但显示 "648 passed, 7 skipped" | pytest-cov 退出码受 astunparse 副作用污染 |
| `test_dead_code_injection` / `test_string_encryption` / `test_anti_debug` / `test_control_flow_flattening` 失败 | 应用 `@requires_py39`，已有同类先例 |

---

## 最佳实践

### 1. 创建 AST 节点时

✅ **正确做法**:
```python
# ast.arguments - 始终提供 vararg 和 kwarg
ast.arguments(
    posonlyargs=[],
    args=[...],
    vararg=None,      # 必需
    kwonlyargs=[],
    kw_defaults=[],
    kwarg=None,       # 必需
    defaults=[],
)

# ast.Constant - 始终提供 kind 参数
ast.Constant(value="some_value", kind=None)
```

❌ **错误做法**:
```python
# 缺少 vararg 和 kwarg
ast.arguments(
    posonlyargs=[],
    args=[...],
    kwonlyargs=[],
    kw_defaults=[],
    defaults=[],
)

# 缺少 kind 参数
ast.Constant(value="some_value")
```

### 2. 代码生成

✅ **正确做法**:
```python
from pyobfus.core.generator import CodeGenerator

# 使用我们的 CodeGenerator，它有 Python 3.8 回退
code = CodeGenerator.generate(tree)
```

❌ **错误做法**:
```python
# 直接使用 ast.unparse - Python 3.8 中不存在！
code = ast.unparse(tree)
```

### 3. 类型提示

✅ **正确做法**:
```python
from typing import Tuple, List, Set, Dict

# 使用 typing 模块中的类型
def func() -> Tuple[str, dict]:
    pass

self._items: List[Set[str]] = []
```

❌ **错误做法**:
```python
# Python 3.9+ 语法 - Python 3.8 不支持！
def func() -> tuple[str, dict]:
    pass

self._items: list[Set[str]] = []
```

### 4. 测试断言

✅ **正确做法**:
```python
# 处理 astunparse 和 ast.unparse 输出差异
assert "class Foo" in new_source and (
    "class Foo:" in new_source or "class Foo():" in new_source
)
```

❌ **错误做法**:
```python
# 精确匹配 - astunparse 输出 "class Foo():"！
assert "class Foo:" in new_source
```

### 5. 测试策略

✅ **正确做法**:
```python
# 使用不太可能随机出现的测试数据
test_string = "unique_test_value_xyz123"
assert '"unique_test_value_xyz123"' not in output  # 精确匹配

# 或使用固定种子
random.seed(42)
```

❌ **错误做法**:
```python
# 使用可能在随机数据中出现的短字符串
test_string = "ab"  # 可能在 base64 中出现！
assert "ab" not in output  # 太宽泛
```

---

## 验证清单

在提交涉及AST操作的代码前，请检查：

- [ ] 所有 `ast.arguments()` 调用都包含 `vararg=None, kwarg=None`
- [ ] 所有 `ast.Constant()` 调用都包含 `kind=None`
- [ ] 使用 `CodeGenerator.generate()` 而非 `ast.unparse()`
- [ ] 类型提示使用 `Tuple`, `List` 而非 `tuple`, `list` (从 typing 导入)
- [ ] 测试断言处理 astunparse 输出格式差异 (`class X():` vs `class X:`)
- [ ] 测试使用独特的测试数据，不依赖随机性
- [ ] 本地运行完整测试套件: `pytest tests/ -v`
- [ ] 运行 ruff 检查: `ruff check pyobfus/ tests/`
- [ ] 检查CI在所有Python版本上通过

---

## 参考资料

### AST 文档
- [Python 3.8 ast module](https://docs.python.org/3.8/library/ast.html)
- [Python 3.9+ ast.unparse()](https://docs.python.org/3.9/library/ast.html#ast.unparse)
- [astunparse package](https://pypi.org/project/astunparse/)

### 相关提交
- `62e39f3`: fix: Add Python 3.8 compatibility for AST node creation
- `a0d7a9d`: fix: Add kind=None to ast.Constant for Python 3.8 astunparse compatibility
- `b3bc1b7`: fix: Use CodeGenerator in tests for Python 3.8 compatibility
- `e72efc9`: fix: Use typing.Tuple and typing.List for Python 3.8 compatibility
- `b40d5cc`: test: Fix test_exported_name_transformer.py for Python 3.8 compatibility
- `c720875`: fix: Remove unused imports and fix f-string lint errors
- `9963bdb`: test: Fix remaining Python 3.8 compatibility issues in tests
- `d4d44ae`: fix: Use CodeGenerator in import_rewriter.py convenience function

### 依赖配置
`pyproject.toml`:
```toml
dependencies = [
    'astunparse>=1.6.3; python_version<"3.9"',  # Python 3.8 需要
]
```

---

## 故障排除

### CI 在 Python 3.8 上失败但本地通过？

1. 检查本地Python版本: `python --version`
2. 创建Python 3.8测试环境:
   ```bash
   python3.8 -m venv .venv38
   source .venv38/bin/activate  # Windows: .venv38\Scripts\activate
   pip install -e ".[dev]"
   pytest tests/ -v
   ```

### astunparse 相关错误？

确保依赖正确安装:
```bash
pip list | grep astunparse
# Python 3.8 应该显示: astunparse x.x.x
```

### 新的AST兼容性问题？

1. 查阅 [Python AST Changes](https://docs.python.org/3/whatsnew/)
2. 在 `pyobfus/core/generator.py` 中添加兼容性处理
3. 更新此文档

---

**维护者**: 如发现新的Python 3.8兼容性问题，请更新此文档！
