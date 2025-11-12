# 🚀 集成测试快速参考

## 一行命令测试

```bash
# 最简单 - 测试单个文件
python scripts/test_ml_research.py your_module.py

# 详细信息
python scripts/test_ml_research.py your_module.py -v

# 批量测试
python scripts/test_ml_research.py --all
```

## 常用命令

```bash
# 1. 测试并保存结果
python scripts/test_ml_research.py module.py -o output.py

# 2. 测试多个文件
python scripts/test_ml_research.py --all --max-files 20

# 3. 使用 pytest
pytest integration_tests/ -v

# 4. 启动 Jupyter
jupyter notebook integration_tests/interactive_testing.ipynb
```

## Python 中使用

```python
# 导入
from integration_tests.test_external_projects import obfuscate_ml_research_module

# 混淆
code = obfuscate_ml_research_module("module.py")

# 混淆并保存
code = obfuscate_ml_research_module("module.py", "output.py")
```

## 典型工作流

```bash
# 1. 修改 pyobfus 代码
vim pyobfus/transformers/...

# 2. 立即测试（无需重新安装！）
python scripts/test_ml_research.py test.py -v

# 3. 全面测试
python scripts/test_ml_research.py --all
```

## 配置

只需修改一次：

```python
# scripts/test_ml_research.py (第17行)
ML_RESEARCH_PATH = Path(r"c:\your\path\to\ml-research")
```

## 故障排除

```bash
# 找不到 pyobfus
pip install -e .

# 找不到 ml-research
# 更新上面的 ML_RESEARCH_PATH

# 修改不生效
# 确保使用了 pip install -e .
```

## 优势 ✅

- 不需要上传到 PyPI
- 修改立即生效
- 真实项目测试
- 快速迭代

## 对比传统方法

传统：修改 → 打包 → 上传 PyPI → pip install → 测试 → 发现问题 → 重复
新方法：修改 → 测试 ✅

## 示例输出

```
🧪 pyobfus Integration Testing
📁 ml-research: c:\...\ml-research

🔄 Processing: data_loader.py
=====================================
📄 Original: 150 lines, 4523 bytes
🔍 Analysis:
   - Total names: 45
   - Obfuscatable: 38
   - Excluded: 7
🔧 Name transformations: 38
🔐 String encoding:
   - Encoded: 12
   - Skipped f-strings: 3
📝 Obfuscated: 153 lines, 5421 bytes
✅ Compilation check: PASSED

✅ Successfully obfuscated data_loader.py
```
