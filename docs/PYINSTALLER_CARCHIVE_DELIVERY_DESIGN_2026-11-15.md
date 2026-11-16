# `--check-delivery`：PyInstaller CArchive 顶层检查设计

Status 2026-11-16: shipped in Core 0.15.0 for direct executables; this document is historical design. Embedded PYZ remains uninspected.

日期：2026-11-15。状态：实现前安全设计；目标是一个冻结格式的保守增量，不宣称检查
嵌入 PYZ 字节码。

## 选择

首个格式选择 PyInstaller CArchive，而不是 Nuitka。项目已有 PyInstaller onedir／onefile
夹具与 6.21.0 验证环境，CArchive 的 cookie 和 TOC 是有界的二进制结构；Nuitka 的最终
布局随编译／standalone 模式不同，不适合作为当前最小解析入口。

## 安全边界

不得直接使用 PyInstaller `ZlibArchiveReader` 读取不可信交付物：6.21.0 的官方 reader
会对 PYZ TOC 调用 `marshal.load`，模块提取还会 `marshal.loads`。本实现只自行解析：

1. 从文件尾分块查找 CArchive cookie magic；
2. 验证 archive、TOC 和成员偏移均落在实际文件／archive 边界内；
3. 限制 TOC 字节、成员数、单成员压缩／解压大小和总解压大小；
4. 只对 CArchive 顶层普通成员做有上限的 zlib 解压；不写临时文件、不导入、不执行；
5. 不读取 PYZ TOC、不反序列化 marshal、不递归打开嵌入 archive。

畸形 cookie、重复／非法名称、越界、解压不完整或资源超限必须使 CLI 返回 error（退出
2），不能退化成 clean。非 PyInstaller 可执行文件保持现有 `frozen_uninspected` warning。

## 检查结果

- 顶层普通成员复用现有 mapping、PEM 私钥和 provenance 原文哈希检查。
- `inspection.frozen_executables` 增加格式、顶层成员数和明确的 unknown 数量。
- 只要存在未检查的 PYZ／嵌入 archive，保留 medium `delivery.frozen_uninspected`；顶层
  没发现问题也只能是 warn，不能是 ok。
- mapping、私钥或 byte-identical 原文仍为 high，整体 fail。
- JSON 只增加字段，不删除或改名，保持现有消费者兼容。

## 接受标准

- 合成 CArchive：正常成员可检查；mapping／私钥／原文分别触发既有 finding code。
- 畸形 archive：短 cookie、TOC 越界、成员越界、重复名称、解压超限均 error。
- 非 PyInstaller PE／ELF／Mach-O：行为保持 warn + inspected 0。
- 真实 PyInstaller onefile：识别为 PyInstaller，顶层已检查，PYZ 明确 unknown；不执行
  产物、不调用 PyInstaller reader。
- `scripts/check.sh`、delivery-check 测试和相关 integration 测试通过。

后续若要检查 PYZ，必须另写安全格式研究和资源预算；不得以本增量为由引入 marshal
反序列化。
