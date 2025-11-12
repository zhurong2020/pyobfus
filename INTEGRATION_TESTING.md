# 跨项目集成测试指南

本指南说明如何在 pyobfus 环境中直接测试 ml-research 或其他外部项目的模块。

## 🎯 目标

- ✅ 不离开 pyobfus 开发环境
- ✅ 不需要上传到 PyPI
- ✅ 快速迭代和测试
- ✅ 使用真实项目的代码

## 🚀 快速开始

### 1. 配置路径

编辑以下文件中的 `ML_RESEARCH_PATH`：

```python
# scripts/test_ml_research.py
ML_RESEARCH_PATH = Path(r"c:\path\to\your\ml-research")

# integration_tests/test_external_projects.py
ML_RESEARCH_PATH = Path(r"c:\path\to\your\ml-research")
```

### 2. 安装开发版本

```bash
# 在 pyobfus 目录中
pip install -e .
```

### 3. 开始测试

```bash
# 方法 1: 使用便捷脚本（最简单）
python scripts/test_ml_research.py your_module.py

# 方法 2: 使用 pytest
pytest integration_tests/ -v

# 方法 3: 交互式测试
jupyter notebook integration_tests/interactive_testing.ipynb
```

## 📖 使用方法

### 方法 1: 便捷脚本（推荐日常使用）

```bash
# 测试单个文件
python scripts/test_ml_research.py data_loader.py

# 详细输出
python scripts/test_ml_research.py data_loader.py -v

# 保存混淆结果
python scripts/test_ml_research.py data_loader.py -o output.py

# 批量测试
python scripts/test_ml_research.py --all
python scripts/test_ml_research.py --all --max-files 20
```

### 方法 2: pytest（推荐自动化测试）

```bash
# 运行所有集成测试
pytest integration_tests/ -v

# 测试特定功能
pytest integration_tests/test_external_projects.py::TestMLResearchModules -v
```

### 方法 3: Python 脚本

```python
from integration_tests.test_external_projects import obfuscate_ml_research_module

# 混淆单个模块
code = obfuscate_ml_research_module("your_module.py")
print(code)

# 保存到文件
code = obfuscate_ml_research_module(
    "your_module.py",
    output_path="obfuscated/output.py"
)
```

### 方法 4: Jupyter Notebook（推荐探索和调试）

```bash
# 启动 notebook
jupyter notebook integration_tests/interactive_testing.ipynb
```

在 notebook 中可以交互式地测试和调试。

## 💡 典型工作流

### 场景 1: 开发新功能

```bash
# 1. 修改 pyobfus 代码
vim pyobfus/transformers/new_feature.py

# 2. 单元测试
pytest tests/test_new_feature.py

# 3. 集成测试（使用 ml-research）
python scripts/test_ml_research.py test_module.py -v

# 4. 发现问题，回到步骤 1
# 5. 修改后立即重新测试（无需重新安装！）
```

### 场景 2: 修复 Bug

```bash
# 1. 复现问题
python scripts/test_ml_research.py problematic_module.py -v

# 2. 查看详细错误信息
# 3. 修复代码
# 4. 重新测试
python scripts/test_ml_research.py problematic_module.py -v

# 5. 验证修复
python scripts/test_ml_research.py --all
```

### 场景 3: 发布前验证

```bash
# 1. 运行所有测试
pytest tests/ -v
pytest integration_tests/ -v

# 2. 批量测试真实项目
python scripts/test_ml_research.py --all --max-files 50

# 3. 检查结果
# ✅ Successful: 48/50
# ❌ Failed: 2/50

# 4. 修复失败的案例
# 5. 重新测试
```

## 🔧 自定义测试

### 添加特定模块测试

编辑 `integration_tests/test_external_projects.py`：

```python
def test_specific_ml_modules(self):
    modules_to_test = [
        "data_loader.py",
        "model_trainer.py",
        "utils/preprocessing.py",
    ]
    # ... 测试逻辑
```

### 自定义混淆配置

```python
from pyobfus.config import ObfuscationConfig

config = ObfuscationConfig()
config.string_encoding = True
config.preserve_param_names = True
config.add_exclude_name("important_function")
```

## 📊 对比：传统方法 vs 新方法

| 特性 | 传统方法 | 新方法（集成测试） |
|------|---------|-----------------|
| **环境** | 需要切换项目 | 留在 pyobfus 中 |
| **安装** | 上传 PyPI 再安装 | 可编辑安装 (pip install -e .) |
| **迭代速度** | 慢（上传+安装） | 快（即时生效） |
| **PyPI 污染** | 是 | 否 |
| **版本管理** | 需要新版本号 | 无需版本号 |
| **调试** | 困难 | 容易（详细输出） |
| **自动化** | 困难 | 容易（pytest） |

## 🎓 最佳实践

1. **使用可编辑安装**: `pip install -e .`
2. **先单元测试**: `pytest tests/`
3. **再集成测试**: `python scripts/test_ml_research.py --all`
4. **详细模式调试**: `-v` 标志查看详细信息
5. **批量测试回归**: 发布前测试所有模块
6. **保存测试结果**: 使用 `-o` 保存混淆后的代码

## 🐛 故障排除

### 问题：找不到 ml-research

```
❌ ml-research project not found
```

**解决**: 更新脚本中的 `ML_RESEARCH_PATH`

### 问题：导入错误

```
ModuleNotFoundError: No module named 'pyobfus'
```

**解决**: 
```bash
pip install -e .
```

### 问题：修改不生效

**原因**: 没有使用可编辑安装

**解决**:
```bash
pip uninstall pyobfus
pip install -e .
```

## 📚 相关文档

- [integration_tests/README.md](integration_tests/README.md) - 详细使用说明
- [scripts/test_ml_research.py](scripts/test_ml_research.py) - 便捷测试脚本
- [integration_tests/test_external_projects.py](integration_tests/test_external_projects.py) - pytest 测试套件
- [integration_tests/interactive_testing.ipynb](integration_tests/interactive_testing.ipynb) - 交互式测试

## 🚀 下一步

1. 配置你的 ml-research 路径
2. 运行第一个测试
3. 根据需要自定义测试
4. 集成到 CI/CD（可选）

---

**提示**: 这个测试方法适用于任何 Python 项目，不仅限于 ml-research！
