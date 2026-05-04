"""Twitter/X deep dive — best-effort via nitter mirror.

⚠️ 2026 현재 Twitter 무인증 검색 = 매우 어려움.
- X API v2 = 유료 ($100/월 basic)
- snscrape = 2024년 X API 변경 후 거의 작동 X
- nitter = 인스턴스 대부분 폐쇄, 살아있는 것도 rate limit / 막힘 많음

본 모듈은 nitter 인스턴스 1-2개 시도 후 실패하면 명확한 에러.
**사용 시점에 작동 여부 확인 필요.** 안 되면 perplexity citation 의존.

사용:
    python tools/search/twitter_dive.py search "query" [--n 20]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

ARC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARC_ROOT))
from tools.cost.cost_log import log_call  # noqa: E402

# Public nitter instances (자주 폐쇄/막힘 — 사용 시점 검증 필요)
# 최신 목록: https://github.com/zedeus/nitter/wiki/Instances
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.tiekoetter.com",
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ARC-research/0.1"
HEADERS = {"User-Agent": UA}


def search(query: str, n: int = 20, instance: str | None = None) -> list[dict]:
    """nitter 검색 시도. 모든 인스턴스 fail 시 RuntimeError."""
    t0 = time.time()
    instances = [instance] if instance else NITTER_INSTANCES
    last_error = None
    for inst in instances:
        try:
            results = _search_one(inst, query, n)
            log_call(
                tool="twitter_dive.search",
                model="nitter",
                metadata={"instance": inst.replace("https://", ""), "query": query[:200], "n": n, "result_count": len(results), "duration_ms": int((time.time() - t0) * 1000)},
            )
            return results
        except Exception as e:
            last_error = f"{inst}: {str(e)[:200]}"
            continue
    raise RuntimeError(
        f"모든 nitter 인스턴스 실패. 2026 현재 Twitter 무인증 검색 매우 어려움.\n"
        f"마지막 에러: {last_error}\n"
        f"권장: perplexity dive 결과의 X citation 활용 또는 X API v2 ($100/월) 가입."
    )


def _search_one(instance: str, query: str, n: int) -> list[dict]:
    url = f"{instance}/search"
    params = {"f": "tweets", "q": query}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    items = soup.select(".timeline-item")[:n]
    if not items:
        raise RuntimeError("no tweets parsed (instance may be broken)")

    results = []
    for el in items:
        author_el = el.select_one(".username")
        author = author_el.get_text(strip=True) if author_el else ""
        content_el = el.select_one(".tweet-content")
        text = content_el.get_text(separator=" ", strip=True) if content_el else ""
        link_el = el.select_one(".tweet-link")
        href = link_el.get("href", "") if link_el else ""
        tweet_url = f"https://twitter.com{href}" if href.startswith("/") else href

        date_el = el.select_one(".tweet-date a")
        date_str = date_el.get("title", "") if date_el else ""

        stats = {}
        for stat in el.select(".tweet-stats .tweet-stat"):
            txt = stat.get_text(strip=True)
            m = re.match(r"(\d+[\.,]?\d*[KMB]?)", txt)
            if m:
                # 순서: comments, retweets, quotes, likes (nitter 기본)
                stats[f"stat_{len(stats)}"] = m.group(1)

        results.append({
            "author": author,
            "text": text,
            "url": tweet_url,
            "date": date_str,
            "stats": stats,
        })
    return results


def main() -> int:
    p = argparse.ArgumentParser(description="Twitter/X deep dive (best-effort via nitter)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp_search = sub.add_parser("search")
    sp_search.add_argument("query")
    sp_search.add_argument("--n", type=int, default=20)
    sp_search.add_argument("--instance", help="특정 nitter 인스턴스 강제 (default: 라운드 로빈)")
    args = p.parse_args()

    if args.cmd == "search":
        try:
            r = search(args.query, n=args.n, instance=args.instance)
            print(json.dumps(r, indent=2, ensure_ascii=False))
        except RuntimeError as e:
            print(f"\n[twitter_dive] FAIL: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
