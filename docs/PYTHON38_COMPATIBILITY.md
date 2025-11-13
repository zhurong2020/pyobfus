# Python 3.8 兼容性指南

**创建日期**: 2025-11-12
**最后更新**: 2025-11-12

## 概述

本文档记录了pyobfus项目中遇到的Python 3.8兼容性问题及其解决方案，以避免将来再次遇到相同问题。

## 背景

pyobfus支持Python 3.8-3.12。Python 3.8与3.9+在AST API方面有重要差异：

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

### 3. 测试策略

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
- [ ] 测试使用独特的测试数据，不依赖随机性
- [ ] 本地运行完整测试套件: `pytest tests/ -v`
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
