# agent-skills-traffic

长期存档 [Tencent-RTC/agent-skills](https://github.com/Tencent-RTC/agent-skills) 的 GitHub Traffic 数据,突破官方仅保留 14 天的限制。

## 工作原理

- **GitHub Actions** 每天 UTC 01:00 / 13:00 自动运行 `scripts/fetch_traffic.py`
- 抓取 views / clones / referrers / popular paths / stars,与历史数据**合并去重**后 commit 进本仓库 → 数据在 git 历史中永久保留
- `index.html` 是前端看板(部署在 Vercel),标注了 **2026-07-02 Twitter 投放开始**,含投放前后对比与来源分析

## 数据文件

| 文件 | 说明 |
|---|---|
| `data/history.json` | 长期合并数据(看板数据源) |
| `data/snapshots/YYYY-MM-DD.json` | 每日原始 API 快照 |

## 配置

仓库 Secret `TRAFFIC_TOKEN`:对目标仓库有 push 权限的 GitHub PAT(classic,`repo` scope)。Token 过期时更新此 Secret 即可,已存档数据不受影响。

手动触发抓取:Actions → Archive GitHub Traffic → Run workflow。
