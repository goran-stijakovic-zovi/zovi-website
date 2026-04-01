#!/usr/bin/env python3
"""
fetch-headlines.py
──────────────────
Fetches the latest AI headlines from RSS feeds and writes the top 20
to headlines.json in the repo root. Called by the GitHub Action daily.

Usage (local):  python scripts/fetch-headlines.py
Usage (CI):     see .github/workflows/update-headlines.yml
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import feedparser
except ImportError:
    print("Installing feedparser...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser"])
    import feedparser

# ─── RSS feed sources ─────────────────────────────────────────
FEEDS = [
    ("TechCrunch AI",  "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("MIT Tech Review","https://www.technologyreview.com/feed/"),
    ("VentureBeat AI", "https://venturebeat.com/ai/feed/"),
    ("Google AI Blog", "https://blog.research.google/feeds/posts/default"),
    ("The Verge AI",   "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
]

# ─── Keywords to filter for AI relevance ─────────────────────
AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "gpt", "claude", "gemini",
    "agent", "openai", "anthropic", "machine learning", "deep learning",
    "neural", "chatgpt", "copilot", "automation", "model", "generative"
]

def is_ai_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in AI_KEYWORDS)

def clean_title(title: str) -> str:
    # Remove HTML entities and strip to 120 chars
    title = re.sub(r'<[^>]+>', '', title)
    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    title = title.replace('&#8217;', "'").replace('&#8220;', '"').replace('&#8221;', '"')
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
                if count >= 6:
                    break
            print(f"  ✓ {source}: {count} headlines")
        except Exception as e:
            print(f"  ✗ {source}: {e}", file=sys.stderr)

    return headlines[:20]

def main():
    print(f"\nFetching headlines at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    headlines = fetch_all()

    if not headlines:
        print("No headlines fetched — keeping existing headlines.json", file=sys.stderr)
        sys.exit(0)

    out_path = Path(__file__).parent.parent / "headlines.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(headlines, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Wrote {len(headlines)} headlines to {out_path.name}\n")

if __name__ == "__main__":
    main()
