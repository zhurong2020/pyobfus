# pyobfus 本地目录与清理审计（2026-11-15）

状态：本地资产盘点与经维护者批准的分批清理记录；三批清理已于 2026-11-15
完成并复核。本文只描述本机目录边界，
不改变公开产品架构、版本、发布或部署状态。

## 数量口径

pyobfus 有 6 个直接命名的本地顶层目录，另有 5 个运维／索引目录，共 11 个相关
本地目录。真正的当前软件源仓只有 2 个：`pyobfus` 与 `pyobfus-action`。
`pyobfus_mcp` 是主仓内部目录，不是独立 Git 仓库，不应重复计数。

## 直接相关目录

| 路径 | 性质 | 决定 |
|---|---|---|
| `~/projects/pyobfus` | 当前公开主仓；Core、Pro builder、runtime、MCP、VS Code、Worker、skills 与 docs 的实现源 | 保留；当前软件权威源 |
| `~/projects/pyobfus-action` | 独立公开 Action 仓库和 Marketplace 发布源 | 保留；独立版本和标签 |
| `~/projects/pyobfus-legal` | 本地法律工作区，含专利、软著、商业化记录与 PII；不是公开 Git 仓 | 保留；不默认加入普通开发工作区，按需显式访问 |
| `~/projects/pyobfus-pro-dev` | 申请日前后的历史私有发明／实现证据，当前实现已集成到主仓 | 保留为只读审计源；只清可再生环境与缓存 |
| `~/projects/pyobfus-wt` | 空目录；无 `.git`，主仓也没有 `.git/worktrees` 登记 | 已删除 |
| `~/projects/pyobfus-backup-pre-filter-repo-20260503-2231` | 2026-05-03 PII 历史重写前的 `.git` tar、bundle 与 hash 清单 | 已核验并删除；记录中的 OneDrive 父路径已不存在 |

## 运维与索引目录

| 路径 | 作用 | 决定 |
|---|---|---|
| `~/projects/workspace-meta` | 跨仓路由、私有归档和会话同步 | 保留；不是产品代码源 |
| `~/projects/home` | 跨项目个人索引和状态路由 | 保留；不是产品代码源 |
| `~/scripts` | KV 导出、每日备份和恢复检查 | 保留 |
| `~/.pyobfus` | 真实本机试用／许可状态 | 保留；测试不得读取、写入或删除 |
| `~/.pyobfus-backups` | Cloudflare KV 许可／试用记录导出，含客户数据 | 保留并按既有轮转策略管理；不得入 Git |

## 安全与备份边界

- `pyobfus-legal` 由 `~/scripts/wsl_daily_backup.sh` 备份到
  `pyobfus_local_only/pyobfus-legal/`，并进入既有云端镜像。它含 PII，永不进入
  公开仓库。
- `pyobfus-pro-dev` 的逐提交历史与 `PATENT_NOTES.md` 被法律材料引用，至少保留到
  专利审查和潜在争议窗口结束；不得从该仓继续开发或发布。
- filter-repo 前备份原 README 只要求重写成功后保留至少 30 天；截至本审计已超过
  六个月。它可能重新暴露当初特意从公开历史清除的 PII，且不是当前发布、恢复或
  专利证据链的权威源，因此长期保留的风险大于收益。
- OneDrive 迁移残留不是本地开发、构建、提交、打 tag 或发布的合法来源。

## 分批清理决定

维护者于 2026-11-15 批准按下列顺序推进：

1. 删除空的 `~/projects/pyobfus-wt`；删除前确认目录为空且无 worktree 登记。
2. 核验当前主仓入口、备份内容与用途后，删除
   `~/projects/pyobfus-backup-pre-filter-repo-20260503-2231`，并检查／处理 OneDrive
   同名迁移残留。删除原因是恢复窗口已过且备份含 PII 历史风险，不是空间不足。
3. 只删除 `pyobfus-pro-dev` 中可再生的 `venv/`、`venv-3.13/`、`venv-3.14/`、
   `.pytest_cache/` 与 `.ruff_cache/`；保留 `.git/`、源码、测试、设计文档、
   `PATENT_NOTES.md` 和所有不可再生证据。

每批操作须解析绝对路径，确保目标仍在上述明确目录内；不得使用通配递归删除，
不得触碰主仓、legal、运维脚本、真实许可状态或 KV 备份。

## 执行结果（2026-11-15）

1. 删除 `~/projects/pyobfus-wt` 前确认目录为 0 项，主仓注册 worktree 为 0；删除后
   复核路径不存在。
2. pre-filter 备份删除前确认仍为 5 个原始文件，并记录 SHA-256；当前主仓
   `main` HEAD 为 `cde07ebefb128d1fd7b7e5e400e743a8a77c1f33`，origin 仍为
   `https://github.com/zhurong2020/pyobfus.git`。记录中的
   `C:\onedrive\msft\OneDrive - MSFT\rong\3-job\program` 父路径已不存在，因而
   没有可在该路径清理的同名迁移残留。WSL 备份目录已删除并复核不存在。
3. 已删除 `pyobfus-pro-dev` 的 `venv/`、`venv-3.13/`、`venv-3.14/`、
   `.pytest_cache/` 与 `.ruff_cache/`。Windows 文件 API 在 Linux Python 符号链接
   处只能完成部分删除，随后用 WSL 对三个已经核验的绝对虚拟环境路径收尾；最终
   五个目标均不存在。历史仓的 `.git/`、`.github/`、`docs/`、源码、tests、
   `PATENT_NOTES.md`、README 与项目元数据均保留。

删除的空目录、PII 历史恢复备份和可再生环境不可从原路径恢复；当前产品源、远端、
法律材料、专利证据、真实许可状态和 KV 备份均未删除。

## 当前产品路由

当前实现与发布边界仍以 [项目结构](PROJECT_STRUCTURE.md) 和
`~/projects/workspace-meta/PYOBFUS_REPOSITORY_MAP.md` 为准。本审计完成后，新会话
不应重新把空 worktree、PII 历史备份或历史私有仓当作新的产品实现源。
