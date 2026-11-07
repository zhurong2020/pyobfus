---
title: 卖给客户前如何保护 Python 源码
description: 用 AI 或手工写的 Python 工具交付客户前：先分清交付形式，再混淆、测试产物、保管映射文件；授权与密钥要放在服务器上。
---

# 卖给客户前如何保护 Python 源码

**简短回答：** 用 AI 写的 Python 工具卖给客户前，先确定交付形式，再混淆、测试交付物，并私有保存映射文件。Python 默认以可读源码交付，任何在客户机器上运行的代码都可以被研究，所以目标是**提高读懂代码的成本**，而不是做到不可读。常见做法是：先改名混淆，需要时再用 PyInstaller 打包或用 Nuitka/Cython 编译；必须保密的算法、API key 和授权判断放在你控制的服务器上。

本页是英文指南
[How to protect Python code before selling software](../guides/protect-python-before-selling.md)
的中文要点版，命令以英文页为准。

## 先看你交付的是什么

| 交付形式 | 用什么保护 | pyobfus 的位置 |
|---|---|---|
| `.py` 文件或库，客户用自己的 Python 运行 | 混淆，让源码难以阅读；客户运行的仍是普通 Python | 适合作为第一个评估的工具：免费、本地运行、产物仍是可移植的 `.py`，线上报错仍可还原 |
| 双击即用的程序，客户不装 Python | 打包或编译：PyInstaller、Nuitka、Cython | 可作为前一步：先混淆再打包，打包后的代码带的是混淆后的名字 |
| 绝不能出现在客户机器上的逻辑（核心算法、模型、提示词） | 放在你的服务器上，只给客户 API 客户端 | 不适用。发出去的东西都能被研究 |
| API key、授权签名密钥、数据库密码 | 不放进客户端：服务器调用、按客户发放的有限凭证、非对称签名 | 不适用。混淆不是密钥管理 |

两条在所有情况下都成立：

- 客户机器上的保护只能**提高阅读成本**。改名混淆挡不住有能力的人，也挡不住大模型推断代码的用途。
- 授权或到期检查只要在本地运行，就可能被删掉、被调回系统时钟或被复制授权文件；能可靠执行的授权必须由服务器判断，并让产品持续依赖服务器提供的必要功能或数据。详见
  [FAQ](../guides/protect-python-code-faq.md)。

## 用 pyobfus 的四步

```bash
pip install pyobfus
pyobfus --check src/                                   # 1. 检查会被混淆破坏的写法
pyobfus src/ -o dist/ --dry-run --json                 # 2. 预览将写出的文件
pyobfus src/ -o dist/ --save-mapping private/build-map.json --verify-syntax
pyobfus --check-delivery dist/ --json                  # 3. 发出前检查产物
```

1. **先检查**：先修复或排除检查发现的问题，再构建。`--check` 会列出 `getattr` 字符串名、`eval`/`exec`、框架反射等容易出问题的写法。AI 生成的代码常用这类动态写法，更要先看。框架项目用 `--preset fastapi` 等预设（`pyobfus --list-presets` 查看）。
2. **构建并保存映射**：`dist/` 是交付物；`private/build-map.json` **不能**交付，它能把混淆后的名字还原回来。每个版本单独保存一份。`--verify-syntax` 只检查语法，不代表程序行为正确。
3. **测试产物，而不只是源码**：用客户实际使用的入口（命令行、HTTP 接口、对外函数）在 `dist/` 上跑一遍，和原程序的输出对比。`--check-delivery` 会找出误放进产物的映射文件和私钥：返回 1（高风险发现）或 2（检查未完成）时应停止交付，返回 0 仍要查看警告。
4. **需要时再打包**：客户不装 Python 时，把**混淆后的** `dist/` 交给 PyInstaller 或 Nuitka。仅用 PyInstaller 打包并不能保护源码，字节码可以被提取并反编译。

## 售后：客户发来报错怎么办

客户看到的 traceback 是混淆后的名字。用同一构建的映射文件还原即可，见
[Python 混淆后客户报错，怎样定位原来的函数](debug-obfuscated-python.md)。

## 常见问题

- **免费的 Community 版能用于商业产品吗？** 可以。Community/Core 采用 Apache-2.0 许可，没有文件或行数限制；Pro 功能单独授权，见 [版本边界](../EDITION_BOUNDARY_POLICY.md)。
- **混淆能保护代码里的 API key 吗？** 不能。仅改名不会隐藏字符串；即使开启字符串编码或加密，客户端运行时仍需取得密钥，不能替代密钥管理。高权限密钥放服务器。
- **源码会被上传吗？** 不会。pyobfus 在本机运行、无遥测；`--check` 默认会向 PyPI 查询依赖名，用 `--offline` 可关闭。见 [网络行为](../NETWORK_BEHAVIOR.md)。
