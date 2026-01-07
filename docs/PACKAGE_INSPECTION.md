# 如何通过Python查看第三方包信息

本文档介绍如何使用Python代码来获取pyobfus包（或任何第三方包）的详细信息。

## 快速参考

### 1. 最简单：查看版本

```python
import pyobfus
print(pyobfus.__version__)
# 输出: 0.1.0
```

### 2. 命令行快速查看

```bash
# 方法1：使用pip
pip show pyobfus

# 方法2：使用Python
python -c "import pyobfus; print(pyobfus.__version__)"

# 方法3：查看详细元数据
python -c "from importlib.metadata import metadata; m=metadata('pyobfus'); print(m['Summary'])"
```

## 详细方法

### 方法1：包的内置属性

```python
import pyobfus

# 基本信息
print(f"包名: {pyobfus.__name__}")           # pyobfus
print(f"版本: {pyobfus.__version__}")        # 0.1.0
print(f"位置: {pyobfus.__file__}")           # 文件路径
print(f"描述: {pyobfus.__doc__}")            # 包的文档字符串

# 包的作者和许可
print(f"作者: {pyobfus.__author__}")         # Rong Zhu
print(f"许可: {pyobfus.__license__}")        # Apache-2.0
```

### 方法2：使用 importlib.metadata（推荐）

```python
from importlib.metadata import metadata, version, requires

# 版本信息
print(version('pyobfus'))  # 0.1.0

# 完整元数据
meta = metadata('pyobfus')
print(meta['Name'])              # pyobfus
print(meta['Version'])           # 0.1.0
print(meta['Summary'])           # 描述
print(meta['Author-email'])      # Rong Zhu <email>
print(meta['License'])           # Apache-2.0
print(meta['Requires-Python'])   # >=3.8

# 项目链接
for url in meta.get_all('Project-URL'):
    print(url)
# 输出：
# Homepage, https://github.com/zhurong2020/pyobfus
# Documentation, https://pyobfus.readthedocs.io/
# Repository, https://github.com/zhurong2020/pyobfus
# ...

# 依赖包
deps = requires('pyobfus')
for dep in deps:
    print(dep)
# 输出：
# click>=8.0
# pyyaml>=5.4
# astunparse>=1.6.3; python_version < "3.9"
# ...
```

### 方法3：探索包的结构和内容

```python
import pyobfus
import inspect

# 查看所有公开成员
for name, obj in inspect.getmembers(pyobfus):
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")

# 输出：
# ASTParser: type
# CodeGenerator: type
# NameMangler: ABCMeta
# SymbolAnalyzer: type
# config: module
# ...

# 查看子模块
import pkgutil
for importer, modname, ispkg in pkgutil.iter_modules(pyobfus.__path__):
    print(f"{modname} ({'包' if ispkg else '模块'})")

# 输出：
# cli (模块)
# config (模块)
# core (包)
# transformers (包)
# ...
```

### 方法4：使用 dir() 和 help()

```python
import pyobfus

# 列出所有属性
print(dir(pyobfus))
# ['ASTParser', 'CodeGenerator', ..., '__version__']

# 查看详细文档
help(pyobfus)
# 显示完整的帮助信息

# 查看特定类的文档
help(pyobfus.ASTParser)
```

### 方法5：检查版本兼容性

```python
from importlib.metadata import version
from packaging.version import Version

# 获取安装的版本
installed = Version(version('pyobfus'))
required = Version('0.1.0')

# 检查是否满足要求
if installed >= required:
    print(f"✓ 版本满足要求: {installed} >= {required}")
else:
    print(f"✗ 版本不满足要求: {installed} < {required}")
```

### 方法6：查看命令行工具

```python
from importlib.metadata import entry_points

# Python 3.10+
scripts = entry_points(group='console_scripts')
for ep in scripts:
    if 'pyobfus' in ep.value:
        print(f"{ep.name}: {ep.value}")

# 输出: pyobfus: pyobfus.cli:main
```

## 实用代码片段

### 检查包是否安装

```python
try:
    import pyobfus
    print(f"✓ pyobfus {pyobfus.__version__} 已安装")
except ImportError:
    print("✗ pyobfus 未安装")
    print("请运行: pip install pyobfus")
```

### 检查可选依赖

```python
import sys
from importlib.metadata import requires

# 检查Pro功能依赖
deps = requires('pyobfus')
pro_deps = [d for d in deps if 'extra == "pro"' in d]

print("Pro功能依赖:")
for dep in pro_deps:
    pkg_name = dep.split(';')[0].split('>=')[0]
    try:
        __import__(pkg_name)
        print(f"  ✓ {dep}")
    except ImportError:
        print(f"  ✗ {dep} (未安装)")
```

### 获取所有元数据为字典

```python
from importlib.metadata import metadata

meta = metadata('pyobfus')
info = {
    'name': meta['Name'],
    'version': meta['Version'],
    'summary': meta['Summary'],
    'author': meta['Author-email'],
    'license': meta['License'],
    'python_requires': meta['Requires-Python'],
    'keywords': meta.get('Keywords', '').split(','),
    'urls': dict(url.split(', ', 1) for url in meta.get_all('Project-URL')),
}

import json
print(json.dumps(info, indent=2, ensure_ascii=False))
```

## 常用场景

### 场景1：在程序中检查依赖版本

```python
from importlib.metadata import version, PackageNotFoundError
from packaging.version import Version

def check_dependency(package, min_version):
    """检查包是否安装且满足最低版本要求"""
    try:
        installed = Version(version(package))
        required = Version(min_version)
        return installed >= required
    except PackageNotFoundError:
        return False

# 使用
if check_dependency('pyobfus', '0.1.0'):
    import pyobfus
    # 继续执行
else:
    print("请安装 pyobfus>=0.1.0")
```

### 场景2：动态获取包信息显示

```python
from importlib.metadata import metadata

def show_package_info(package_name):
    """显示包的完整信息"""
    meta = metadata(package_name)

    print(f"{'='*60}")
    print(f"Package: {meta['Name']} v{meta['Version']}")
    print(f"{'='*60}")
    print(f"Description: {meta['Summary']}")
    print(f"Author: {meta['Author-email']}")
    print(f"License: {meta['License']}")
    print(f"Python: {meta['Requires-Python']}")
    print(f"\nProject Links:")
    for url in meta.get_all('Project-URL'):
        name, link = url.split(', ', 1)
        print(f"  {name:15s} {link}")

# 使用
show_package_info('pyobfus')
```

### 场景3：生成依赖报告

```python
from importlib.metadata import requires, version

def generate_dependency_report(package_name):
    """生成依赖分析报告"""
    deps = requires(package_name)

    report = {
        'package': package_name,
        'version': version(package_name),
        'dependencies': {
            'required': [],
            'optional': {},
        }
    }

    for dep in deps:
        if 'extra ==' in dep:
            # 可选依赖
            extra = dep.split('extra == "')[1].split('"')[0]
            pkg = dep.split(';')[0].strip()
            if extra not in report['dependencies']['optional']:
                report['dependencies']['optional'][extra] = []
            report['dependencies']['optional'][extra].append(pkg)
        else:
            # 必需依赖
            report['dependencies']['required'].append(dep)

    return report

# 使用
report = generate_dependency_report('pyobfus')
print(f"Package: {report['package']} v{report['version']}")
print(f"\nRequired: {len(report['dependencies']['required'])}")
for dep in report['dependencies']['required']:
    print(f"  - {dep}")
print(f"\nOptional:")
for extra, deps in report['dependencies']['optional'].items():
    print(f"  [{extra}]")
    for dep in deps:
        print(f"    - {dep}")
```

## 参考链接

- [Python importlib.metadata 文档](https://docs.python.org/3/library/importlib.metadata.html)
- [PEP 566 - Metadata for Python Software Packages 2.1](https://www.python.org/dev/peps/pep-0566/)
- [pyobfus GitHub](https://github.com/zhurong2020/pyobfus)
- [pyobfus PyPI](https://pypi.org/project/pyobfus/)

## 示例脚本

完整的示例脚本请参见：[examples/inspect_package.py](../examples/inspect_package.py)

运行示例：
```bash
cd examples
python inspect_package.py
```
