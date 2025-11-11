#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
示例：如何通过Python代码查看第三方包的详细信息

这个脚本演示了多种方法来获取pyobfus包的元数据和功能信息。
"""

import sys


def method1_basic_info():
    """方法1：使用包的内置属性"""
    print("=" * 60)
    print("方法1：包的基本属性")
    print("=" * 60)

    import pyobfus

    print(f"包名: {pyobfus.__name__}")
    print(f"版本: {pyobfus.__version__}")
    print(f"文件位置: {pyobfus.__file__}")
    print(f"包路径: {pyobfus.__path__}")
    print(f"\n包描述:\n{pyobfus.__doc__}")
    print()


def method2_importlib_metadata():
    """方法2：使用importlib.metadata（推荐）"""
    print("=" * 60)
    print("方法2：使用 importlib.metadata")
    print("=" * 60)

    from importlib.metadata import metadata, version, requires

    # 基本信息
    print(f"版本: {version('pyobfus')}")

    # 完整元数据
    meta = metadata('pyobfus')
    print(f"名称: {meta['Name']}")
    print(f"描述: {meta['Summary']}")
    print(f"作者: {meta['Author-email']}")
    print(f"许可证: {meta['License']}")
    print(f"Python版本: {meta['Requires-Python']}")

    # 项目链接
    print("\n项目链接:")
    for url in meta.get_all('Project-URL') or []:
        name, link = url.split(', ', 1)
        print(f"  {name:20s} {link}")

    # 关键词
    print(f"\n关键词: {meta.get('Keywords')}")

    # 依赖
    print("\n依赖包:")
    for req in requires('pyobfus') or []:
        print(f"  {req}")
    print()


def method3_pkg_resources():
    """方法3：使用pkg_resources（旧方法，但仍然有效）"""
    print("=" * 60)
    print("方法3：使用 pkg_resources")
    print("=" * 60)

    try:
        import pkg_resources

        dist = pkg_resources.get_distribution('pyobfus')
        print(f"包名: {dist.project_name}")
        print(f"版本: {dist.version}")
        print(f"位置: {dist.location}")

        # 获取元数据
        if dist.has_metadata('METADATA'):
            metadata_content = dist.get_metadata('METADATA')
            print("\n前几行元数据:")
            for i, line in enumerate(metadata_content.split('\n')[:10]):
                print(f"  {line}")
        print()
    except ImportError:
        print("pkg_resources 不可用（setuptools未安装）\n")


def method4_inspect_module():
    """方法4：使用inspect模块查看包内容"""
    print("=" * 60)
    print("方法4：查看包的内容和结构")
    print("=" * 60)

    import inspect
    import pyobfus

    # 列出所有公开的类和函数
    print("包中的公开成员:")
    for name, obj in inspect.getmembers(pyobfus):
        if not name.startswith('_'):
            obj_type = type(obj).__name__
            print(f"  {name:30s} ({obj_type})")

    # 查看子模块
    print("\n子模块:")
    if hasattr(pyobfus, '__path__'):
        import pkgutil
        for importer, modname, ispkg in pkgutil.iter_modules(pyobfus.__path__):
            pkg_type = "包" if ispkg else "模块"
            print(f"  {modname:30s} ({pkg_type})")
    print()


def method5_help_and_dir():
    """方法5：使用help()和dir()探索包"""
    print("=" * 60)
    print("方法5：使用 dir() 查看所有属性")
    print("=" * 60)

    import pyobfus

    print("所有属性和方法:")
    for attr in dir(pyobfus):
        print(f"  {attr}")

    print("\n使用 help(pyobfus) 可以查看完整文档")
    print("（这里不展示完整输出，避免太长）")
    print()


def method6_entry_points():
    """方法6：查看命令行工具（entry points）"""
    print("=" * 60)
    print("方法6：查看命令行工具")
    print("=" * 60)

    from importlib.metadata import entry_points

    # Python 3.10+ 使用 select()，3.8-3.9 使用字典访问
    if sys.version_info >= (3, 10):
        console_scripts = entry_points(group='console_scripts')
    else:
        eps = entry_points()
        console_scripts = eps.get('console_scripts', [])

    print("命令行工具:")
    for ep in console_scripts:
        if hasattr(ep, 'value'):  # Python 3.10+
            if 'pyobfus' in ep.value.lower():
                print(f"  {ep.name}: {ep.value}")
        else:  # Python 3.8-3.9
            if 'pyobfus' in str(ep).lower():
                print(f"  {ep}")
    print()


def method7_practical_usage():
    """方法7：实际使用示例"""
    print("=" * 60)
    print("方法7：实际使用示例")
    print("=" * 60)

    import pyobfus

    print("快速检查包是否安装并获取版本:")
    print("-" * 40)
    print("import pyobfus")
    print(f"print(pyobfus.__version__)  # 输出: {pyobfus.__version__}")
    print()

    print("检查是否满足最低版本要求:")
    print("-" * 40)
    code = """
from importlib.metadata import version
from packaging.version import Version

installed = Version(version('pyobfus'))
required = Version('0.1.0')
print(f"安装版本: {installed}")
print(f"需要版本: {required}")
print(f"满足要求: {installed >= required}")
"""
    print(code)

    # 实际执行
    try:
        from importlib.metadata import version
        from packaging.version import Version
        installed = Version(version('pyobfus'))
        required = Version('0.1.0')
        print(f"安装版本: {installed}")
        print(f"需要版本: {required}")
        print(f"满足要求: {installed >= required}")
    except ImportError:
        print("（需要安装 packaging 包）")
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("如何通过Python查看第三方包信息 - pyobfus示例")
    print("=" * 60 + "\n")

    try:
        method1_basic_info()
        method2_importlib_metadata()
        method3_pkg_resources()
        method4_inspect_module()
        method5_help_and_dir()
        method6_entry_points()
        method7_practical_usage()

        print("=" * 60)
        print("总结：推荐使用方法")
        print("=" * 60)
        print("""
1. 快速查看版本:
   import pyobfus
   print(pyobfus.__version__)

2. 查看详细元数据（推荐）:
   from importlib.metadata import metadata, version
   print(version('pyobfus'))
   meta = metadata('pyobfus')
   print(meta['Summary'])

3. 查看依赖:
   from importlib.metadata import requires
   print(requires('pyobfus'))

4. 探索包内容:
   import pyobfus
   print(dir(pyobfus))
   help(pyobfus)

5. 在命令行快速查看:
   python -c "import pyobfus; print(pyobfus.__version__)"
   pip show pyobfus
""")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
