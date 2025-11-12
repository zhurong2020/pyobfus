# Integration Tests for External Projects

这个目录包含用于测试 pyobfus 在真实项目（如 ml-research）上的功能的集成测试。

## 设置

### 1. 配置 ml-research 路径

编辑测试文件中的路径配置：

```python
# integration_tests/test_external_projects.py
ML_RESEARCH_PATH = Path(r"c:\path\to\your\ml-research")
```

或在脚本中：

```python
# scripts/test_ml_research.py
ML_RESEARCH_PATH = Path(r"c:\path\to\your\ml-research")
```

### 2. 安装 pyobfus（开发模式）

```bash
pip install -e .
```

## 使用方法

### 方法 1: 使用便捷脚本（推荐）

```bash
# 测试单个文件
python scripts/test_ml_research.py data_loader.py

# 测试特定路径的文件
python scripts/test_ml_research.py "utils/preprocessing.py"

# 测试所有文件（前 10 个）
python scripts/test_ml_research.py --all

# 测试更多文件
python scripts/test_ml_research.py --all --max-files 20

# 详细输出
python scripts/test_ml_research.py module.py -v

# 保存混淆后的代码
python scripts/test_ml_research.py module.py -o obfuscated/module_obf.py
```

### 方法 2: 使用 pytest

```bash
# 运行所有集成测试
pytest integration_tests/ -v

# 运行特定测试
pytest integration_tests/test_external_projects.py::TestMLResearchModules::test_obfuscation_preserves_functionality -v

# 批量测试
pytest integration_tests/test_external_projects.py::TestMLResearchModules::test_batch_obfuscation -v
```

### 方法 3: Python 脚本中使用

```python
from integration_tests.test_external_projects import obfuscate_ml_research_module

# 混淆单个模块
obfuscated_code = obfuscate_ml_research_module(
    "data_processing.py",
    output_path="obf/data_processing_obf.py",
    enable_string_encoding=True
)

print(obfuscated_code)
```

### 方法 4: 交互式测试（Python REPL）

```python
# 在 pyobfus 项目根目录
python

>>> from pathlib import Path
>>> from integration_tests.test_external_projects import obfuscate_ml_research_module

>>> # 测试你的模块
>>> code = obfuscate_ml_research_module("your_module.py")
>>> print(code)

>>> # 保存到文件
>>> Path("obf_output.py").write_text(code)
```

## 测试场景

### 场景 1: 快速验证（单个文件）

当你修改了 pyobfus 代码后，想快速验证：

```bash
# 1. 修改 pyobfus 代码
vim pyobfus/transformers/string_encoder.py

# 2. 立即测试
python scripts/test_ml_research.py test_module.py -v

# 3. 查看输出，发现问题
# 4. 修改 pyobfus
# 5. 重新测试（无需重新安装）
```

### 场景 2: 全面回归测试

发布新版本前，测试所有模块：

```bash
# 测试所有文件
python scripts/test_ml_research.py --all --max-files 50

# 查看摘要
# ✅ Successful: 45/50
# ❌ Failed: 5/50
```

### 场景 3: 调试特定问题

当某个模块混淆失败时：

```bash
# 详细模式查看问题
python scripts/test_ml_research.py problematic_module.py -v

# 输出会显示：
# - 代码分析统计
# - 名称转换数量
# - 字符串编码统计
# - 编译检查结果
# - 详细错误信息
```

### 场景 4: 对比测试

测试混淆前后的功能等价性：

```python
# integration_tests/test_external_projects.py
def test_obfuscate_and_execute(self):
    # 执行原始代码
    original_namespace = {}
    exec(original_code, original_namespace)

    # 执行混淆代码
    obfuscated_namespace = {}
    exec(obfuscated_code, obfuscated_namespace)

    # 对比结果
    assert original_namespace['result'] == obfuscated_namespace['result']
```

## 自定义测试

### 添加特定模块测试

编辑 `integration_tests/test_external_projects.py`：

```python
def test_specific_ml_modules(self):
    modules_to_test = [
        "data_loader.py",
        "model_trainer.py",
        "utils/preprocessing.py",
    ]

    for module_name in modules_to_test:
        # ... 测试逻辑 ...
```

### 自定义混淆配置

```python
from pyobfus.config import ObfuscationConfig

# 创建自定义配置
config = ObfuscationConfig()
config.string_encoding = True
config.preserve_param_names = True
config.add_exclude_name("important_function")

# 使用自定义配置测试
obfuscated_code = self.obfuscate_file(file_path, config)
```

## 工作流示例

### 典型开发流程

```bash
# 1. 在 pyobfus 中开发新功能
cd /path/to/pyobfus
vim pyobfus/transformers/new_feature.py

# 2. 单元测试
pytest tests/test_new_feature.py -v

# 3. 集成测试（使用 ml-research）
python scripts/test_ml_research.py --all

# 4. 如果发现问题，查看详细信息
python scripts/test_ml_research.py problematic_file.py -v

# 5. 修复问题
vim pyobfus/transformers/new_feature.py

# 6. 重新测试（无需重新安装！）
python scripts/test_ml_research.py problematic_file.py -v

# 7. 全部通过后提交
git add .
git commit -m "feat: Add new feature"
```

## 优势

✅ **快速迭代**：修改后立即测试，无需重新安装
✅ **真实场景**：使用实际项目的代码测试
✅ **不污染 PyPI**：无需发布到 PyPI 即可测试
✅ **方便调试**：详细的错误信息和统计数据
✅ **批量测试**：一次测试多个文件
✅ **灵活配置**：可自定义混淆配置

## 故障排除

### 问题：找不到 ml-research

```
❌ ml-research project not found at: ...
```

**解决**：更新测试文件中的 `ML_RESEARCH_PATH`

### 问题：导入错误

```
ModuleNotFoundError: No module named 'pyobfus'
```

**解决**：安装开发版本
```bash
pip install -e .
```

### 问题：编译错误

```
❌ Syntax error in obfuscated code
```

**解决**：使用详细模式查看详细信息
```bash
python scripts/test_ml_research.py module.py -v
```

## 下一步

- 根据测试结果修复问题
- 添加更多特定场景的测试
- 自动化测试流程（CI/CD）
- 性能基准测试
