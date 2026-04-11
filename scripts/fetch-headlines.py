#!/usr/bin/env python3
"""
fetch-headlines.py
──────────────────
Fetches the latest AI headlines from RSS feeds and writes up to 50
to headlines.json in the repo root. Called by the GitHub Action daily.

Usage (local):           python scripts/fetch-headlines.py
Usage (with archive):    python scripts/fetch-headlines.py --archive
Usage (CI):              see .github/workflows/update-headlines.yml

--archive flag:
  Also saves today's batch to headlines/YYYY-MM-DD.json and removes
  any archive files older than 7 days.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("Installing feedparser...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser"])
    import feedparser

# ─── RSS feed sources (10 feeds) ──────────────────────────────
FEEDS = [
    ("TechCrunch AI",   "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("MIT Tech Review", "https://www.technologyreview.com/feed/"),
    ("VentureBeat AI",  "https://venturebeat.com/ai/feed/"),
    ("The Verge AI",    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("Wired AI",        "https://www.wired.com/feed/tag/ai/latest/rss"),
    ("Ars Technica",    "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("ZDNet AI",        "https://www.zdnet.com/topic/artificial-intelligence/rss.xml"),
    ("AI News",         "https://artificialintelligence-news.com/feed/"),
    ("Google AI Blog",  "https://blog.research.google/feeds/posts/default"),
    ("IEEE Spectrum",   "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss"),
]

# ─── Per-feed headline cap ────────────────────────────────────
PER_FEED   = 6    # max per source
TOTAL_CAP  = 50   # overall cap
ARCHIVE_DAYS = 7  # how many days to keep in headlines/

# ─── Keywords to filter for AI relevance ─────────────────────
AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "gpt", "claude", "gemini",
    "agent", "openai", "anthropic", "machine learning", "deep learning",
    "neural", "chatgpt", "copilot", "automation", "model", "generative",
    "robot", "algorithm", "compute", "inference", "transformer", "diffusion",
]

def is_ai_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in AI_KEYWORDS)

def clean_title(title: str) -> str:
    title = re.sub(r'<[^>]+>', '', title)
    title = (title
             .replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
             .replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
             .replace('&nbsp;', ' ').replace('&#39;', "'"))
    return title.strip()[:120]

def fetch_all() -> list[dict]:
    headlines = []
    for source, url in FEEDS:
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                title = clean_title(entry.get("title", ""))
                if not title or not is_ai_relevant(title):
                    continue
                headlines.append({"source": source, "text": title})
                count += 1
                if count >= PER_FEED:
                    break
            print(f"  ✓ {source}: {count} headlines")
        except Exception as e:
            print(f"  ✗ {source}: {e}", file=sys.stderr)

    return headlines[:TOTAL_CAP]

def save_archive(headlines: list[dict], repo_root: Path) -> Path:
    """Save today's headlines to headlines/YYYY-MM-DD.json."""
    archive_dir = repo_root / "headlines"
    archive_dir.mkdir(exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_path = archive_dir / f"{today}.json"
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(headlines, f, indent=2, ensure_ascii=False)
    print(f"  📁 Archived to headlines/{today}.json")
    return archive_path

def cleanup_old_archives(repo_root: Path):
    """Delete archive files older than ARCHIVE_DAYS days."""
    archive_dir = repo_root / "headlines"
    if not archive_dir.exists():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=ARCHIVE_DAYS)
    removed = 0
    for f in sorted(archive_dir.glob("*.json")):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff:
                f.unlink()
                removed += 1
                print(f"  🗑  Removed old archive: {f.name}")
        except ValueError:
            pass  # skip files that don't match date pattern
    if removed == 0:
        print(f"  ✓ Archive clean — no files older than {ARCHIVE_DAYS} days")

def main():
    parser = argparse.ArgumentParser(description="Fetch AI headlines from RSS feeds")
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Also save today's batch to headlines/YYYY-MM-DD.json and clean up files >7 days old",
    )
    args = parser.parse_args()

    print(f"\nFetching headlines at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    headlines = fetch_all()

    if not headlines:
        print("No headlines fetched — keeping existing headlines.json", file=sys.stderr)
        sys.exit(0)

    repo_root = Path(__file__).parent.parent

    # Always write the main headlines.json
    out_path = repo_root / "headlines.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(headlines, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Wrote {len(headlines)} headlines to headlines.json")

    # Archive mode: also save dated file + clean up old ones
    if args.archive:
        print("\n📦 Archive mode:")
        save_archive(headlines, repo_root)
        cleanup_old_archives(repo_root)

    print()

if __name__ == "__main__":
    main()
