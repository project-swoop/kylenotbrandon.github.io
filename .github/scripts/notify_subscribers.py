#!/usr/bin/env python3
"""Notify newsletter subscribers when new _posts/ files are added (via Apps Script webhook)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
POSTS_DIR = ROOT / "_posts"
POST_FILE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$")
FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def parse_front_matter(text: str) -> dict[str, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def slug_from_filename(name: str) -> str | None:
    match = POST_FILE.match(name)
    if not match:
        return None
    return match.group(4)


def post_url(filename: str, site_url: str) -> str | None:
    match = POST_FILE.match(filename)
    if not match:
        return None
    year, month, day, slug = match.groups()
    base = site_url.rstrip("/")
    return f"{base}/blog/{year}/{month}/{day}/{slug}/"


def format_post_date(filename: str) -> str:
    match = POST_FILE.match(filename)
    if not match:
        return ""
    year, month, day, _slug = match.groups()
    try:
        dt = datetime(int(year), int(month), int(day))
        return dt.strftime("%B %-d, %Y")
    except ValueError:
        return f"{year}-{month}-{day}"


def excerpt_for_post(path: Path, meta: dict[str, str]) -> str:
    if meta.get("excerpt"):
        return meta["excerpt"]
    text = path.read_text(encoding="utf-8")
    body = FRONT_MATTER.sub("", text, count=1).strip()
    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = paragraph.strip()
        if not paragraph or paragraph.startswith("#"):
            continue
        return paragraph
    return ""


def post_payload(path: Path, site_url: str) -> dict[str, str] | None:
    filename = path.name
    if not POST_FILE.match(filename):
        return None
    meta = parse_front_matter(path.read_text(encoding="utf-8"))
    url = post_url(filename, site_url)
    if not url:
        return None
    title = meta.get("title") or slug_from_filename(filename) or path.stem
    return {
        "title": title,
        "url": url,
        "date": format_post_date(filename),
        "excerpt": excerpt_for_post(path, meta),
    }


def new_post_files() -> list[str]:
    if os.environ.get("NOTIFY_FORCE_LATEST") == "1":
        return []

    try:
        # "sha parent1 [parent2 ...]" — merge commits have 2+ parents.
        # Diffing only HEAD~1 misses posts that already exist on the first
        # parent (typical after git pull merges remote analytics into a post tip).
        parts = run_git("rev-list", "--parents", "-n", "1", "HEAD").split()
        if len(parts) < 2:
            return []
        head, *parents = parts
        files: set[str] = set()
        for parent in parents:
            out = run_git(
                "diff",
                "--name-only",
                "--diff-filter=A",
                parent,
                head,
                "--",
                "_posts/",
            )
            for line in out.splitlines():
                path = line.strip()
                if path.endswith(".md"):
                    files.add(path)
        return sorted(files)
    except subprocess.CalledProcessError as exc:
        print(f"git diff failed: {exc.stderr}", file=sys.stderr)
        return []


def latest_post_file() -> Path | None:
    posts = sorted(POSTS_DIR.glob("*.md"))
    return posts[-1] if posts else None


def send_notification(post: dict[str, str], webhook_url: str, secret: str) -> dict:
    payload = json.dumps({"action": "send", "secret": secret, "post": post}).encode("utf-8")
    req = Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "kylenotbrandon.github.io-newsletter-workflow",
        },
        method="POST",
    )
    with urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    webhook_url = os.environ.get("NEWSLETTER_WEBHOOK_URL", "").strip()
    secret = os.environ.get("NEWSLETTER_WEBHOOK_SECRET", "").strip()
    site_url = os.environ.get("SITE_URL", "https://kylenotbrandon.blog").strip()

    if not webhook_url or not secret:
        print(
            "NEWSLETTER_WEBHOOK_URL and NEWSLETTER_WEBHOOK_SECRET are required; skipping.",
            file=sys.stderr,
        )
        return 0

    files = new_post_files()
    if not files and os.environ.get("NOTIFY_FORCE_LATEST") == "1":
        latest = latest_post_file()
        if latest:
            files = [str(latest.relative_to(ROOT)).replace("\\", "/")]

    if not files:
        print("No new posts to announce.")
        return 0

    exit_code = 0
    for rel_path in files:
        path = ROOT / rel_path
        if not path.exists():
            print(f"Skipping missing file: {rel_path}")
            continue
        post = post_payload(path, site_url)
        if not post:
            print(f"Skipping unparsable post: {rel_path}")
            continue
        print(f"Sending newsletter for: {post['title']}")
        try:
            result = send_notification(post, webhook_url, secret)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            print(f"Webhook HTTP error for {rel_path}: {exc.code} {exc.reason}", file=sys.stderr)
            if detail:
                print(detail, file=sys.stderr)
            exit_code = 1
            continue
        except URLError as exc:
            print(f"Webhook network error for {rel_path}: {exc}", file=sys.stderr)
            exit_code = 1
            continue

        print(json.dumps(result))
        if not result.get("ok"):
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
