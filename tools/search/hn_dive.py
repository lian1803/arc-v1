"""Hacker News deep dive — Algolia HN search + Firebase comment tree.

무인증, 무료, rate limit 관대.

사용:
    python tools/search/hn_dive.py search "query" [--n 20] [--sort byPopularity|byDate]
    python tools/search/hn_dive.py fetch <story_id>
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

ARC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARC_ROOT))
from tools.cost.cost_log import log_call  # noqa: E402

ALGOLIA = "https://hn.algolia.com/api/v1"
FIREBASE = "https://hacker-news.firebaseio.com/v0"


def search(query: str, n: int = 20, sort: str = "byPopularity", tags: str = "story") -> list[dict]:
    """sort: byPopularity (default) | byDate. tags: story | comment | story,comment"""
    t0 = time.time()
    endpoint = f"{ALGOLIA}/search" if sort == "byPopularity" else f"{ALGOLIA}/search_by_date"
    params = {"query": query, "hitsPerPage": min(n, 100), "tags": tags}
    resp = requests.get(endpoint, params=params, timeout=15)
    resp.raise_for_status()
    hits = resp.json().get("hits", [])
    results = []
    for h in hits:
        results.append({
            "story_id": h.get("objectID"),
            "title": h.get("title") or h.get("story_title") or "",
            "author": h.get("author", ""),
            "points": h.get("points", 0),
            "num_comments": h.get("num_comments", 0),
            "created_at": h.get("created_at", ""),
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "hn_url": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "story_text_preview": (h.get("story_text") or "")[:300],
        })

    log_call(
        tool="hn_dive.search",
        model="algolia:hn",
        metadata={"query": query[:200], "n": n, "result_count": len(results), "duration_ms": int((time.time() - t0) * 1000)},
    )
    return results


def fetch_story(story_id: str | int, max_comments: int = 80, max_depth: int = 4) -> dict:
    """게시글 + 댓글 트리 (재귀, depth/count cap)."""
    t0 = time.time()
    sid = str(story_id)
    item = _get_item(sid)
    story = {
        "id": item.get("id"),
        "title": item.get("title", ""),
        "by": item.get("by", ""),
        "score": item.get("score", 0),
        "url": item.get("url", ""),
        "text": item.get("text", "") or "",
        "descendants": item.get("descendants", 0),
        "hn_url": f"https://news.ycombinator.com/item?id={sid}",
    }
    comments: list[dict] = []
    _collect_comments(item.get("kids") or [], comments, max_comments, max_depth, depth=0)

    log_call(
        tool="hn_dive.fetch_story",
        model="firebase:hn",
        metadata={"story_id": sid, "comment_count": len(comments), "duration_ms": int((time.time() - t0) * 1000)},
    )
    return {"story": story, "comments": comments}


def _get_item(item_id: str | int) -> dict:
    resp = requests.get(f"{FIREBASE}/item/{item_id}.json", timeout=10)
    resp.raise_for_status()
    return resp.json() or {}


def _collect_comments(kids: list, out: list, cap: int, max_depth: int, depth: int) -> None:
    for kid_id in kids:
        if len(out) >= cap or depth > max_depth:
            return
        item = _get_item(kid_id)
        if not item or item.get("deleted") or item.get("dead"):
            continue
        out.append({
            "depth": depth,
            "by": item.get("by", ""),
            "text": (item.get("text") or "")[:1500],
        })
        if item.get("kids"):
            _collect_comments(item["kids"], out, cap, max_depth, depth + 1)


def main() -> int:
    p = argparse.ArgumentParser(description="HN deep dive (Algolia + Firebase)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp_search = sub.add_parser("search")
    sp_search.add_argument("query")
    sp_search.add_argument("--n", type=int, default=20)
    sp_search.add_argument("--sort", default="byPopularity", choices=["byPopularity", "byDate"])
    sp_search.add_argument("--tags", default="story", help="story | comment | story,comment")
    sp_fetch = sub.add_parser("fetch")
    sp_fetch.add_argument("story_id")
    sp_fetch.add_argument("--comments", type=int, default=80)
    sp_fetch.add_argument("--depth", type=int, default=4)
    args = p.parse_args()

    if args.cmd == "search":
        r = search(args.query, n=args.n, sort=args.sort, tags=args.tags)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        r = fetch_story(args.story_id, max_comments=args.comments, max_depth=args.depth)
        print(json.dumps(r, indent=2, ensure_ascii=False)[:8000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
