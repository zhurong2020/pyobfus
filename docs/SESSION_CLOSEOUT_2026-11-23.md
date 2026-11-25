# 会话收尾 — 2026-11-23

## 当前状态

- 查询时工作区在 `main`，本地与 `origin/main` 相同；工作区已有 11-20 收尾文档及指针/TODO 修改，均保留，未提交或推送。
- 最新远端提交 `ee41bcb`（Dependabot npm 开发依赖更新 #261）；Core 最新发布仍为 0.15.0（11-15）。
- 最近 CI、Dogfood、License Endpoint Monitor、VS Code Extension CI 和 CodeQL 均成功；无开放 issue，唯一开放 PR 为草稿 [#252](https://github.com/zhurong2020/pyobfus/pull/252)。
- 本次仅查询与记录，未改产品、发版、部署、合并、签发许可或发送邮件。

## 下载与访问

2026-11-23 15:21 UTC 运行 `venv/bin/python scripts/download_snapshot.py --days 14`，数据截至 11-22：

- Core：近 7 天 508，安静日中位数 44；近 30 天 3962，安静日中位数 58。对比 11-20 的中位数 46/60，略降；周总量受 11-15 发版尖峰移出窗口影响，不作为增长证据。
- MCP：近 7 天 90、中位数 8；近 30 天 634、中位数 10。
- Marketplace 安装 20（前次 19）；Open VSX 累计下载 906（前次 898，含重复抓取/镜像，不等同用户数）；Action 可见引用仍为 0。
- GitHub 近 14 天访问 237／独立 124（前次 249／127）；来源有 vuink.com、Google、GitHub、PyPI、Bing、DuckDuckGo 等，未见 dev.to 或 reddit.com。
- runtime 近 30 天下载 4118，主要受本仓 CI 影响，不作为采用指标。

## 邮件

Gmail 检索 11-19 之后 pyobfus/Glama 及购买、许可、退款相关关键词：

- 11-22 mcprush 称已收录 pyobfus-mcp，邀请免费认领 listing 和查看 analytics；尚未独立核验 listing 内容或认领状态。邮件：[查看](https://mail.google.com/mail/u/0/#all/1a2039efd57b1ebe)。
- 11-22 Anthropic 支持称 Plugin Directory 仓库锁问题仍在处理，无解决方案或时间表，有进展会通知；目前无需采取行动。邮件：[查看](https://mail.google.com/mail/u/0/#all/1a2030e3792eb059)。
- 未发现新的购买、退款或客户交付阻塞邮件。检索范围为上述日期和关键词，不代表全收件箱逐封复核。

## 后续接续

1. 验收 Worker `39d425d7` 于 11-23 03:17 UTC 的首次定时清扫：比对当日 KV 与 `kv_backup_20261116T083109Z`，确认只清理 90 天以上设备审计记录、`ci_usage` 仅保留 `last_used`，许可有效性和设备槽位不变。端点监控成功不等于清扫已验收；发现异常按既定恢复流程处理。
2. 维护者审定 #252 与私有客户通知稿，确认删除请求 30 天处理承诺及生效日；通知与合并需沿用既定批准边界。
3. 12-01～05 完成 T6 搜索／AI 可见性复盘；之后再判断独立域名。12 月中旬前无 Core 发版计划。

依据：[执行台账](ROADMAP_EXECUTION_2026-11-16.md)、[TODO](TODO.md)、[11-20 会话收尾](SESSION_CLOSEOUT_2026-11-20.md)。
