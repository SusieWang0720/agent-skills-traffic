#!/usr/bin/env python3
"""
GitHub Traffic 每日存档脚本
抓取 Tencent-RTC/agent-skills 的 views / clones / referrers / paths 数据,
与历史数据合并去重后写入 data/,git 提交后永久保留(不受 GitHub 14 天窗口限制)。
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = os.environ.get("TARGET_REPO", "Tencent-RTC/agent-skills")
TOKEN = os.environ["GH_TOKEN"]
API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SNAP_DIR = DATA_DIR / "snapshots"
HISTORY_FILE = DATA_DIR / "history.json"


def gh_get(path):
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "traffic-archiver",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    views = gh_get(f"/repos/{REPO}/traffic/views?per=day")
    clones = gh_get(f"/repos/{REPO}/traffic/clones?per=day")
    referrers = gh_get(f"/repos/{REPO}/traffic/popular/referrers")
    paths = gh_get(f"/repos/{REPO}/traffic/popular/paths")
    repo_info = gh_get(f"/repos/{REPO}")

    # 1) 原始快照存档(每天一份,后运行覆盖先运行,保证是当天最全数据)
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "fetched_at": now.isoformat(),
        "views": views,
        "clones": clones,
        "referrers": referrers,
        "paths": paths,
        "stars": repo_info.get("stargazers_count"),
        "forks": repo_info.get("forks_count"),
    }
    (SNAP_DIR / f"{today}.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2)
    )

    # 2) 合并进长期历史
    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text())
    else:
        history = {
            "repo": REPO,
            "views": {},
            "clones": {},
            "referrer_history": {},
            "path_history": {},
            "repo_stats": {},
        }

    # views/clones 按天合并;同一天取较大值(当天数据会随时间增长,末次抓取最全)
    for kind, payload in (("views", views), ("clones", clones)):
        bucket = history[kind]
        for item in payload.get(kind, []):
            d = item["timestamp"][:10]
            prev = bucket.get(d, {"count": 0, "uniques": 0})
            bucket[d] = {
                "count": max(prev["count"], item["count"]),
                "uniques": max(prev["uniques"], item["uniques"]),
            }

    # referrers / paths 是 14 天滚动汇总,按抓取日存快照序列,用于趋势分析
    history["referrer_history"][today] = [
        {"referrer": r["referrer"], "count": r["count"], "uniques": r["uniques"]}
        for r in referrers
    ]
    history["path_history"][today] = [
        {"path": p["path"], "title": p.get("title", ""), "count": p["count"], "uniques": p["uniques"]}
        for p in paths
    ]
    history["repo_stats"][today] = {
        "stars": repo_info.get("stargazers_count"),
        "forks": repo_info.get("forks_count"),
    }
    history["last_updated"] = now.isoformat()

    # 排序后写回
    for k in ("views", "clones", "referrer_history", "path_history", "repo_stats"):
        history[k] = dict(sorted(history[k].items()))
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2))

    days = sorted(history["views"].keys())
    print(f"OK: views {len(days)} 天已存档 ({days[0] if days else '-'} ~ {days[-1] if days else '-'})")


if __name__ == "__main__":
    sys.exit(main())
# retrigger: secret added
