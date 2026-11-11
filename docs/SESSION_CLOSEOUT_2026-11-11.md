# 2026-11-11 会话收尾

## 当前结果

公开版本仍为 Core 0.13.0／MCP 0.3.17／runtime 0.1.1／扩展 0.4.3／Action v1.1.0。本次未合并 PR、配置生产 key、部署或发版。

当前分支 `feat/ci-signed-lease-v1`，草稿 [#221](https://github.com/zhurong2020/pyobfus/pull/221) 依赖未合并的 [#220](https://github.com/zhurong2020/pyobfus/pull/220)。本次代码修订 `74769cd` 已推送：签名端点的拒绝响应统一禁止缓存，inactive 错误使用固定文本；旧端点兼容行为保留。

## 验收

- 正常 HOME 下分别运行各测试根：Core 5073 passed／55 skipped（7 条 warnings），MCP 167，integration 368 passed／10 skipped，runtime 24，基准 8。
- Worker 70 项通过；包含所有签名响应 no-store、私有状态不回显、存储及限流异常不回显／不记录日志。Python 授权定向 68 项通过；完整 `scripts/check.sh` 通过。
- `74769cd` 托管 48 success／2 skipped，Core／Worker（最低依赖与 3.15 互通）／CodeQL／Packaging／Dogfood 成功。[具体运行入口](OPERATIONS_REVIEW_2026-11-11.md)。不将该结果外推为后续 revision 已通过。
- #220 源码审阅未见阻塞，托管 42 success／1 skipped。此次源码审阅不代替 #221 的独立外部审阅。

## 文档与提交分类

1. 代码与回归修订：`74769cd`（含 Worker 操作说明及当时审阅记录），已推送，保留现有提交。
2. 接口与发布说明同步：`12c45ff`，CHANGELOG、CI 授权指南、Worker 轮换／回滚说明、llms 两组镜像、集成模板、两个 Skill 与 AI catalog；候选行为均标记为 unreleased。
3. 计划与交接同步：AGENTS／CLAUDE、CURRENT_PLAN、TODO、巡检验收与本收尾记录。

私有原始日志、审阅提示和密钥轮换草案保存在忽略目录 `docs/internal/f2-ci-implementation-2026-11-11/`，不加入公共提交。

## 下一步

1. 等 #220 明确合并决定；获准并合并后同步父依赖，再复核 #221。本次文档同步与 commit 不等于合并授权。
2. #221 进行独立外部审阅；确认公钥来源、生产 key 配对、轮换升级窗口及兼容回滚。当前单 signer 不协商客户端 key 能力，旧客户端无法自动信任新 key。
3. 生产配置、兼容服务部署、live pair 验证与客户端发布分别验收；空公钥表发布 gate 保留，最终 release revision 运行完整 21 格矩阵和维护的附加工作流。工作站／离线迁移继续延后。
4. 取得 GSC 重定向错误示例；11-16 周检复核下载、反馈、CI、搜索与新增私有材料备份。专利许可专业审阅及 12 月观测继续按 [TODO](TODO.md) 执行。

长期状态以 [当前计划](CURRENT_PLAN_ZH.md) 为准，待办以 [TODO](TODO.md) 为准。
