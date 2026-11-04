# 2026-11-04 发布后当日巡检

观察时间：2026-11-04 12:04 UTC / 20:04 CST。此记录补充
[发布会话收尾](SESSION_CLOSEOUT_2026-11-04.md)，不替代尚未到期的 T+24h 观察。

## 下载与采用线索

使用仓库 `venv/bin/python scripts/download_snapshot.py --days 30` 查询；
三个 PyPI 包的 `data_through` 均为 **2026-11-03**，尚不包含 Core 0.12.0 发布日。
对照为 [11-03 巡检](EXECUTION_PROGRESS_2026-11-03.md)，其数据截至 11-01。

| 指标 | 本次 | 上次 |
|---|---:|---:|
| Core 30 天无镜像下载 | 4044 | 3862 |
| Core 30 天安静日中位数／样本天数 | 82 / 8 | 56 / 8 |
| MCP 30 天无镜像下载 | 915 | 923 |
| MCP 30 天安静日中位数／样本天数 | 12 / 20 | 12 / 20 |
| Marketplace installs | 16 | 16 |
| Open VSX downloads | 824 | 812 |
| GitHub 14 天 views／unique | 143 / 115 | 139 / 102 |

Core 近 7 天合计 1074，安静日 3 天，中位数 149；11-01 至 11-03 分别为
169、131、149。MCP 近 7 天合计 211，安静日 5 天，中位数 13。
安静日仅排除各包发布日及次日，无法排除 CI、发布准备和内容活动影响；
滚动合计差值不等于新增用户，不能据此认定持续自然增长或 0.12.0 发布效果。

runtime 近 7/30 天为 1194/3150，本仓 CI 安装影响显著，不作用户规模指标。
Marketplace 仍为扩展 0.4.3，updates 20、ratings 0；Open VSX reviews 0。
Open VSX 下载含重复获取与爬虫，不与 Marketplace 安装数相加。
Action 可检索引用仓库数为 0，不等于实际采用为零。
GitHub 返回的来源列表未见 DEV／LinkedIn，不据此断言无内容导流。

## 工程与文档状态

本轮检查时工作区干净，本地及 GitHub `main` 均为 `9c87645`，开放 PR／Issue 均为 0。
该提交的 [CI](https://github.com/zhurong2020/pyobfus/actions/runs/41818194997)
及 [CodeQL](https://github.com/zhurong2020/pyobfus/actions/runs/41758433435) 成功。
RTD API 返回最新构建 **35630935**，revision `9c87645`，状态 finished、success；
完成时间为 2026-11-04 02:06:14 UTC。此前交接中的 35630733 是上一接续 revision 的证据。

## 邮件与后续

本次相关邮件检索未发现新增待回复的客户支持、激活失败或构建回归来信；
目录审核仍待处理，渠道成功通知及账户提醒的细节仅留私有
`docs/internal/operations-review-2026-11-04/email-review.md`。

- 11-05 09:27 CST 后执行 T+24h，11-07 同时点后执行 T+72h；本次不提前填写结果。
- LinkedIn 单帖一周复盘仍待约 11-05 晚的帖子后台数据。
- 下一次自然备份须核对本次巡检与此前发布证据的包含性；本轮未检查新快照或云端文件。
- 未发送邮件、改变标签、归档或删除邮件；未发布产品或部署服务。
