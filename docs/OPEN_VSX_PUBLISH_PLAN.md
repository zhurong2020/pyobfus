# Open VSX 发布

更新时间：2026-09-07（**已发布并经独立复核上线**；本文件由「发布准备」转为
发布记录 + 后续版本的 runbook）

## 目标

将 `vscode-extension` 发布到 Open VSX，覆盖使用 Open VSX 的 VS Code 兼容环境
（VSCodium、Gitpod、Eclipse Theia、code-server 等拿不到 Microsoft Marketplace
的场景）。**`0.4.2` 已于 2026-09-07 发布上线**；本文件后续用作再发布 runbook。

## 当前审计结果

- `package.json` 已有稳定的 `publisher`、`license`、`repository`、`homepage`、
  `bugs`、`icon` 和 Python/obfuscator 关键词。
- 扩展已有独立 README、CHANGELOG、图标和生产打包脚本。
- 发布产物应使用生产构建生成的 `.vsix`；不要提交 `.vsix`、`dist/` 或
  `node_modules/`。
- 扩展依赖的 `pyobfus` 解释器由用户配置或本地 PATH 提供，发布页需要明确这
  一点，避免用户误以为扩展内置 Python 或 Core 包。
- Marketplace 与 Open VSX 的现有版本说明必须保持一致，尤其是本地处理、无
  网络上传源码、OpenSSF/PEP 740 等可验证信号，不应夸大为安全保证。
  截至 2026-09-07 两边同为 `0.4.2`，一致。

## 2026-09-07 发布结果 ✅

本地准备：

- `npm run lint`：通过。
- `npm run typecheck`：通过。
- `npm run pretest`：通过，测试编译和夹具复制完成。
- `npx vsce package --no-dependencies`：通过，生成 `pyobfus-0.4.2.vsix`。
- VSIX 内容审计：9 个预期文件；未发现源码、测试夹具、个人路径或 token。

发布：

- 已创建 `zhurong2020` namespace，并上传 `pyobfus-0.4.2.vsix`；`ovsx` 返回
  `Published zhurong2020.pyobfus v0.4.2`。

公开验证（**已上线，独立复核通过**）：

- 上传后**立即**查询时 CLI/API 仍返回 `Extension not found`，当时按索引传播
  延迟记录、未宣称上线；同日复查已自行追上。
- 扩展页 <https://open-vsx.org/extension/zhurong2020/pyobfus> → HTTP 200，
  维护者浏览器所见与 API 一致（`zhurong2020.pyobfus · v0.4.2`，Versions 表
  `0.4.2 / Universal`，1–1 of 1）。
- API <https://open-vsx.org/api/zhurong2020/pyobfus> → HTTP 200，
  `version=0.4.2`、`license=Apache-2.0`、`timestamp=2026-09-07T00:59:01Z`、
  `allVersions=[latest, 0.4.2]`、`downloadCount=0`、`reviewCount=0`。
- VSIX 直链可用：
  `https://open-vsx.org/api/zhurong2020/pyobfus/0.4.2/file/zhurong2020.pyobfus-0.4.2.vsix`
- ⚠️ **`verified: false` 不是问题**：这是 Open VSX 的 **namespace 归属验证**
  标记，公开 namespace 默认就是 `false`，需另行向 Eclipse 申请归属验证才会变
  `true`。它与"是否发布成功"、"内容是否通过审核"无关，别读成发布异常。
- `downloadCount=0` 是发布当天的正常起点，不是失败信号；下次周期性复查时再看
  是否有真实安装量。

## 再发布 runbook（后续版本）

维护者已有 Eclipse 账号并接受 Publisher Agreement，namespace `zhurong2020`
已建；后续版本只需重跑下面这套（把版本号换成当次的）：

```bash
cd vscode-extension
npm ci
npm run lint
npm run typecheck
npm run pretest
npx vsce package --no-dependencies
npx ovsx publish pyobfus-<version>.vsix -p "$OPEN_VSX_TOKEN"
```

每次发布前必须人工确认：

1. `.vsix` 内容没有源码、token、个人路径和测试夹具；
2. `package.json` 的版本、发布者、许可证、仓库路径正确；
3. 安装后能启动扩展，并能连接用户配置的 `pyobfus`；
4. Open VSX 页面显示正确版本、README、图标和许可证；
5. Open VSX 页面与 Microsoft Marketplace 的描述没有冲突；
6. 发布结果记录到 `DISTRIBUTION_CHANNELS.md`（Open VSX 小节），并保留公开
   页面 URL；
7. 上传后**不要**用"立即查询返回 404"下结论——索引传播有延迟，隔一段时间
   用上面那两个 URL 再核一次（0.4.2 这次就是先 404、后自行追上）。

## 账号与常用入口

发布链路横跨两个账号系统：Eclipse Foundation 账号是身份根，Open VSX 用它登录。

**Eclipse Foundation**（身份根）

| 用途 | 入口 |
|---|---|
| 账号管理 / 登录 | <https://accounts.eclipse.org/> |
| 个人主页 | <https://accounts.eclipse.org/users/zhurong2020> |
| Eclipse Contributor Agreement (ECA) | <https://accounts.eclipse.org/user/eca> |

用户名 `zhurong2020`。目前 Committer / Projects / Marketplace favorites 均为空
——发布 VS Code 扩展到 Open VSX **不需要**成为 Eclipse committer 或建 Eclipse
项目，这些计数为 0 是正常的，不是缺步骤。

**Open VSX Registry**

| 用途 | 入口 |
|---|---|
| 注册表首页 / 搜索 | <https://open-vsx.org/> |
| 个人资料 | <https://open-vsx.org/user-settings/profile> |
| **Access Tokens**（发布凭证在此签发/吊销） | <https://open-vsx.org/user-settings/tokens> |
| **Namespaces**（归属验证在此申请） | <https://open-vsx.org/user-settings/namespaces> |
| 本人已发布扩展 | <https://open-vsx.org/user-settings/extensions> |
| 本扩展公开页 | <https://open-vsx.org/extension/zhurong2020/pyobfus> |
| 官方发布文档 | <https://github.com/eclipse-openvsx/openvsx/wiki/Publishing-Extensions> |
| Namespace 归属说明 | <https://github.com/eclipse-openvsx/openvsx/wiki/Namespace-Access> |

登录名 `zhurong2020`。**Open VSX Publisher Agreement 已签署**（profile 页显示
"You signed the Eclipse Foundation Open VSX Publisher Agreement."）——这是发布
的前置条件，已满足，后续版本不需要重签。

Namespace `zhurong2020` 状态为 **not verified**。这是"未申请归属验证"，不是
"被拒"或"有问题"：公开 namespace 默认如此，任何人都能正常安装扩展。要拿归属
标记需按上面的 Namespace 归属说明另行申请，属可选项。

⚠️ Open VSX 已启用**分级限流**（rate limiting tiers，站顶横幅公告）。批量脚本
化访问其 API 前先看 <https://open-vsx.org/> 顶部横幅指向的说明，别当成无限额
接口。

## 外部操作边界

Open VSX 账号注册、协议接受和 token 创建需要维护者在外部账户中操作。本轮
维护者已明确授权并完成一次发布；token 不写入仓库或 CI。

token 存放在 Vaultwarden 条目 **`Open VSX Access Token (pyobfus)`**（folder
`Publishing`，与 `PyPI Credentials (.pypirc)` 同组）。这是唯一副本，本地没有
同步的 dotfile 缓存，发布时按需取用：

```bash
export OPEN_VSX_TOKEN=$(bw get password "Open VSX Access Token (pyobfus)")
```

token 由维护者定期轮换。轮换后只需更新该 Vaultwarden 条目的 password，仓库和
CI 都不需要改动。

官方发布参考：

<https://github.com/eclipse-openvsx/openvsx/wiki/Publishing-Extensions>
