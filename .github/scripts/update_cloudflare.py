#!/usr/bin/env python3
"""Merge Cloudflare zone analytics into _data/cloudflare_history.json and refresh cloudflare_stats.yml."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = ROOT / "_data" / "cloudflare_history.json"
STATS_PATH = ROOT / "_data" / "cloudflare_stats.yml"
GRAPHQL_URL = "https://api.cloudflare.com/client/v4/graphql"

# httpRequests1dGroups is the stable zone analytics dataset for daily totals.
DAILY_QUERY = """
query DailyVisits($zoneTag: string, $since: Date!, $until: Date!) {
  viewer {
    zones(filter: { zoneTag: $zoneTag }) {
      httpRequests1dGroups(
        limit: 14
        orderBy: [date_ASC]
        filter: { date_geq: $since, date_leq: $until }
      ) {
        dimensions {
          date
        }
        sum {
          pageViews
          requests
        }
        uniq {
          uniques
        }
      }
    }
  }
}
"""


def load_history() -> dict:
    if not HISTORY_PATH.exists():
        return {"days": {}}
    with open(HISTORY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if "days" not in data or not isinstance(data["days"], dict):
        data["days"] = {}
    return data


def graphql(token: str, query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "kylenotbrandon.github.io-cloudflare-workflow",
        },
        method="POST",
    )
    with urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        messages = "; ".join(
            err.get("message", str(err)) for err in payload["errors"] if isinstance(err, dict)
        )
        raise RuntimeError(messages or "Cloudflare GraphQL error")
    return payload.get("data") or {}


def zone_groups(data: dict, field: str) -> list:
    zones = (data.get("viewer") or {}).get("zones") or []
    if not zones:
        return []
    groups = zones[0].get(field) or []
    return groups if isinstance(groups, list) else []


def week_dates(end: datetime.date) -> list[str]:
    start = end - timedelta(days=6)
    return [(start + timedelta(days=i)).isoformat() for i in range(7)]


def main() -> int:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
    if not token or not zone_id:
        print(
            "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID not set; skipping Cloudflare sync.",
            file=sys.stderr,
        )
        return 0

    today = datetime.now(timezone.utc).date()
    since = today - timedelta(days=13)

    try:
        daily_data = graphql(
            token,
            DAILY_QUERY,
            {
                "zoneTag": zone_id,
                "since": since.isoformat(),
                "until": today.isoformat(),
            },
        )
    except HTTPError as e:
        print(f"Cloudflare API HTTP error: {e.code} {e.reason}", file=sys.stderr)
        return 1
    except (URLError, RuntimeError) as e:
        print(f"Cloudflare API error: {e}", file=sys.stderr)
        return 1

    hist = load_history()
    days: dict[str, dict[str, int]] = hist["days"]

    for row in zone_groups(daily_data, "httpRequests1dGroups"):
        dims = row.get("dimensions") or {}
        day = dims.get("date") or ""
        if not day:
            continue
        total = row.get("sum") or {}
        uniq = row.get("uniq") or {}
        days[day] = {
            "page_views": int(total.get("pageViews") or 0),
            "requests": int(total.get("requests") or 0),
            "uniques": int(uniq.get("uniques") or 0),
        }

    hist["days"] = days
    hist["last_sync"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_time_page_views = sum(day.get("page_views", 0) for day in days.values())

    rolling_week = week_dates(today)
    week_page_views = sum(days.get(day, {}).get("page_views", 0) for day in rolling_week)
    # Sum of daily uniques slightly overcounts vs. dashboard 7-day dedupe, but uses one stable API.
    week_uniques = sum(days.get(day, {}).get("uniques", 0) for day in rolling_week)

    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, sort_keys=True)
        f.write("\n")

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stats_body = f"""# Auto-updated by .github/workflows/update-traffic.yml (Cloudflare GraphQL)
# all_time_page_views sums daily page-view totals recorded since this workflow was enabled.
# last_7_days_visitors sums daily unique-visitor counts for the rolling 7-day window.
all_time_page_views: {all_time_page_views}
last_7_days_visitors: {week_uniques}
last_7_days_page_views: {week_page_views}
last_updated: "{updated}"
"""
    with open(STATS_PATH, "w", encoding="utf-8") as f:
        f.write(stats_body)

    print(
        f"all_time_page_views={all_time_page_views} "
        f"last_7_days_visitors={week_uniques} last_7_days_page_views={week_page_views}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
