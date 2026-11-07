---
title: Python 混淆后客户报错，怎样定位原来的函数
description: 每次构建保存私有映射文件，用同一构建的映射把混淆后的 traceback 还原成原来的函数名、文件和行号（pyobfus --unmap）。
---

# Python 混淆后客户报错，怎样定位原来的函数

**简短回答：** 每次构建都保存一份私有的映射文件（混淆名 → 原名），客户发来报错时，用**客户正在运行的那个构建**的映射，把 traceback（异常堆栈）还原成原来的名字。用 pyobfus 就是构建时加 `--save-mapping`，事后运行 `pyobfus --unmap`。0.7.0 及以后生成的映射，标准 CPython 堆栈帧还能还原原始文件和行号。还原在免费的 Community 版中即可完成。

本页是英文指南
[How to debug production tracebacks after Python obfuscation](../guides/debug-obfuscated-python.md)
的中文要点版，细节以英文页为准。

## 支持 traceback 映射的工具都适用的三条

具体能还原到什么程度、用什么命令，以各工具文档为准。

- **一个构建一份映射。** 源码、配置或工具版本一变，名字和行号映射都可能改变，所以每个交付的构建都要保存对应的映射。按版本号存放，并在交付文件里记录构建标识（pyobfus 的 `--trace-marker` 会写入）。
- **映射绝不交付。** 映射会暴露原始标识符，并可用来还原 traceback 位置，必须私有保存，不要放进发布包、公开的 CI 产物或 issue。
- **拿到完整的 traceback。** 文件名、行号和异常链是还原的依据。

## 用 pyobfus 的做法

```bash
# 构建：保存映射，并在产物里写入构建标识
pyobfus src/ -o dist/ --save-mapping private/maps/1.4.2/app.map.json --trace-marker

# 客户报错后：把 traceback 存成 error.log，再还原
pyobfus --unmap --trace error.log --mapping private/maps/1.4.2/app.map.json

# Core 0.9.1 起默认按 UTF-8（允许 BOM）读取；仅当日志实际是 cp1252 等其他编码时才指定
# 编码不对会以退出码 2 失败；更早的版本请先把日志另存为 UTF-8
pyobfus --unmap --trace error.log --mapping private/maps/1.4.2/app.map.json --trace-encoding cp1252
```

客户发来的报错类似：

```
  File ".../dist/pricing.py", line 18, in I5
    I1 = I7 * I3[0]['discount_rate']
KeyError: 'discount_rate'
```

还原后：

```
  File "pricing.py", line 13, in order_total  [obfuscated: .../dist/pricing.py:18]
    discount = subtotal * line_items[0]['discount_rate']
KeyError: 'discount_rate'
```

`I5` 是 `order_total`，`I7` 是 `subtotal`，`I3` 是 `line_items`。加 `--json` 可以得到原始和还原后的 traceback，方便交给脚本或 AI 助手继续分析。

## 能还原什么、不能还原什么

- **能还原**：pyobfus 改过的函数、类、方法、变量和参数名；0.7.0 及以后的映射还能还原标准帧的原始文件和语句起始行。旧映射只还原名字。
- **不能还原**：注释、docstring 和原始排版不在映射里；`^^^^` 标记的列位置仍对应产物代码。
- Pro 的跨文件 L3 预览（加密函数）帧只还原名字。
- 没有对应构建的映射，就无法还原名字，这正是混淆的目的。
