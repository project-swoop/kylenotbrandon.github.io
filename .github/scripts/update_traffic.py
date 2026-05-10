#!/usr/bin/env python3
"""Merge GitHub repo Traffic API views into _data/traffic_history.json and refresh traffic_stats.yml."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = ROOT / "_data" / "traffic_history.json"
STATS_PATH = ROOT / "_data" / "traffic_stats.yml"


def load_history() -> dict:
    if not HISTORY_PATH.exists():
        return {"days": {}}
    with open(HISTORY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if "days" not in data or not isinstance(data["days"], dict):
        data["days"] = {}
    return data


def fetch_views(repo: str, token: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/traffic/views"
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(req, timeout=60) as resp:
        return json.load(resp)


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("GITHUB_TOKEN and GITHUB_REPOSITORY are required", file=sys.stderr)
        return 1

    try:
        payload = fetch_views(repo, token)
    except HTTPError as e:
        print(f"Traffic API HTTP error: {e.code} {e.reason}", file=sys.stderr)
        return 1
    except URLError as e:
        print(f"Traffic API network error: {e}", file=sys.stderr)
        return 1

    hist = load_history()
    days: dict[str, int] = hist["days"]

    for row in payload.get("views") or []:
        ts = row.get("timestamp") or ""
        day = ts[:10] if len(ts) >= 10 else ""
        if not day:
            continue
        days[day] = int(row.get("count") or 0)

    hist["days"] = days
    hist["last_sync"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_time = sum(days.values())

    today = datetime.now(timezone.utc).date()
    week_total = 0
    for i in range(7):
        d = (today - timedelta(days=i)).isoformat()
        week_total += days.get(d, 0)

    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, sort_keys=True)
        f.write("\n")

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stats_body = f"""# Auto-updated by .github/workflows/update-traffic.yml
# all_time_views sums daily page-view totals recorded since this workflow was enabled (GitHub exposes ~14 days per sync; history merges over time).
all_time_views: {all_time}
last_7_days_views: {week_total}
last_updated: "{updated}"
"""
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        f.write(stats_body)

    print(f"all_time_views={all_time} last_7_days_views={week_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
