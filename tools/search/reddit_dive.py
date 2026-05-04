"""Reddit deep dive — 무인증 JSON endpoint 활용.

검색 + 게시글 본문 + 댓글 트리. Reddit API key 불필요.
rate limit: User-Agent 필수, 60/min 권장.

사용:
    python tools/search/reddit_dive.py search "query" [--sub subreddit] [--n 25]
    python tools/search/reddit_dive.py fetch "https://reddit.com/r/.../comments/..."
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

UA = "ARC-research/0.1 (1-person research; contact: lian)"
HEADERS = {"User-Agent": UA}


def search(query: str, subreddit: str | None = None, n: int = 25, sort: str = "relevance") -> list[dict]:
    """sort: relevance | hot | top | new | comments"""
    t0 = time.time()
    if subreddit:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "restrict_sr": "true", "limit": min(n, 100), "sort": sort}
    else:
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "limit": min(n, 100), "sort": sort}

    resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json().get("data", {}).get("children", [])
    results = []
    for ch in data:
        d = ch.get("data", {})
        results.append({
            "id": d.get("id"),
            "title": d.get("title", ""),
            "subreddit": d.get("subreddit", ""),
            "author": d.get("author", ""),
            "score": d.get("score", 0),
            "num_comments": d.get("num_comments", 0),
            "created_utc": d.get("created_utc"),
            "url": f"https://www.reddit.com{d.get('permalink', '')}",
            "selftext_preview": (d.get("selftext") or "")[:300],
            "external_url": d.get("url_overridden_by_dest") or "",
        })

    log_call(
        tool="reddit_dive.search",
        model="reddit:json",
        metadata={"query": query[:200], "sub": subreddit or "all", "n": n, "result_count": len(results), "duration_ms": int((time.time() - t0) * 1000)},
    )
    return results


def fetch_post(url: str, max_comments: int = 50) -> dict:
    """게시글 본문 + 댓글 트리 (top N개)."""
    t0 = time.time()
    if not url.endswith(".json"):
        url = url.rstrip("/") + ".json"
    resp = requests.get(url, headers=HEADERS, params={"limit": max_comments, "depth": 5}, timeout=15)
    resp.raise_for_status()
    j = resp.json()

    if not isinstance(j, list) or len(j) < 2:
        raise RuntimeError(f"unexpected reddit response: {url}")

    post_data = j[0]["data"]["children"][0]["data"]
    post = {
        "id": post_data.get("id"),
        "title": post_data.get("title", ""),
        "subreddit": post_data.get("subreddit", ""),
        "author": post_data.get("author", ""),
        "score": post_data.get("score", 0),
        "num_comments": post_data.get("num_comments", 0),
        "selftext": post_data.get("selftext", ""),
        "url": url.rstrip(".json"),
        "external_url": post_data.get("url_overridden_by_dest") or "",
    }

    comments = _flatten_comments(j[1]["data"]["children"], max_count=max_comments)

    log_call(
        tool="reddit_dive.fetch_post",
        model="reddit:json",
        metadata={"url": url[:300], "comment_count": len(comments), "duration_ms": int((time.time() - t0) * 1000)},
    )
    return {"post": post, "comments": comments}


def _flatten_comments(children: list, max_count: int = 50, depth: int = 0) -> list[dict]:
    out = []
    for ch in children:
        if len(out) >= max_count:
            break
        if ch.get("kind") != "t1":
            continue
        d = ch.get("data", {})
        out.append({
            "depth": depth,
            "author": d.get("author", ""),
            "score": d.get("score", 0),
            "body": (d.get("body") or "")[:1500],
        })
        replies = d.get("replies")
        if isinstance(replies, dict):
            sub = _flatten_comments(replies.get("data", {}).get("children", []), max_count - len(out), depth + 1)
            out.extend(sub)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Reddit deep dive (무인증)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp_search = sub.add_parser("search")
    sp_search.add_argument("query")
    sp_search.add_argument("--sub", help="특정 subreddit")
    sp_search.add_argument("--n", type=int, default=25)
    sp_search.add_argument("--sort", default="relevance", choices=["relevance", "hot", "top", "new", "comments"])
    sp_fetch = sub.add_parser("fetch")
    sp_fetch.add_argument("url")
    sp_fetch.add_argument("--comments", type=int, default=50)
    args = p.parse_args()

    if args.cmd == "search":
        r = search(args.query, subreddit=args.sub, n=args.n, sort=args.sort)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        r = fetch_post(args.url, max_comments=args.comments)
        print(json.dumps(r, indent=2, ensure_ascii=False)[:8000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
