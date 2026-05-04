"""ARC deep search — perplexity + 1차 자료 fetch + YouTube transcript + 플랫폼 통합.

사용법:
    python tools/search/dive.py "쿼리"                    # 기본 (perplexity + citation)
    python tools/search/dive.py "쿼리" --reddit --hn --github --gemini  # 모든 플랫폼 동시
    python tools/search/dive.py "쿼리" --all              # 동일 (Twitter 제외)

흐름:
    1. perplexity sonar-pro 답변 + citation URL 추출
    2. YouTube URL → yt.fetch_transcript (한국어 우선)
    3. 일반 URL → browse.browse (5000자 발췌)
    4. (옵션) Reddit/HN/GitHub/Gemini 동일 쿼리로 추가 검색
    5. 통합본 = 모든 결과 1장 마크다운
    6. 저장: raw/sources/dive_{slug}_{date}.md

비용:
    - perplexity sonar-pro 1쿼리 ~$0.006
    - Gemini 2.5 Flash 1쿼리 ~$0.001
    - Reddit/HN/GitHub 무료
    - browse/yt 무료
    - --all 1회 dive ≈ $0.01

§2 No-Silent-Fail: perplexity 자체 fail은 raise. 개별 URL/플랫폼 fail은 silent skip.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ARC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARC_ROOT))

from tools.search.browse import browse  # noqa: E402
from tools.search.yt import fetch_transcript  # noqa: E402

DEFAULT_OUT_DIR = ARC_ROOT / "raw" / "sources"


def _load_pplx_key() -> str:
    env_path = ARC_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("PERPLEXITY_API_KEY="):
                return line.split("=", 1)[1].strip()
    key = os.getenv("PERPLEXITY_API_KEY", "")
    if not key:
        raise RuntimeError("PERPLEXITY_API_KEY missing (.env or env var)")
    return key


def perplexity_query(prompt: str, model: str = "sonar-pro", timeout: int = 300) -> tuple[str, list[dict]]:
    """Returns (answer_text, citations)."""
    key = _load_pplx_key()
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.loads(r.read().decode("utf-8"))
    content = j["choices"][0]["message"]["content"]
    cites_raw = j.get("citations") or j.get("search_results") or []
    cites = []
    for c in cites_raw:
        if isinstance(c, dict):
            cites.append({"url": c.get("url") or c.get("link") or "", "title": c.get("title") or "", "date": c.get("date") or ""})
        else:
            cites.append({"url": str(c), "title": "", "date": ""})
    return content, cites


def _is_youtube(url: str) -> bool:
    u = url.lower()
    return "youtube.com/watch" in u or "youtu.be/" in u


def _video_id(url: str) -> str | None:
    if "youtu.be/" in url:
        return url.rsplit("/", 1)[-1].split("?")[0]
    if "youtube.com/watch" in url:
        q = parse_qs(urlparse(url).query)
        return (q.get("v") or [None])[0]
    return None


def _fetch_yt_safe(url: str) -> dict:
    vid = _video_id(url)
    if not vid:
        return {"url": url, "ok": False, "error": "no video_id"}
    try:
        r = fetch_transcript(vid, lang_priority=["ko", "en"])
        return {"url": url, "ok": True, "type": "youtube", **r}
    except Exception as e:
        return {"url": url, "ok": False, "error": str(e)[:200]}


def _fetch_web_safe(url: str) -> dict:
    try:
        r = browse(url, timeout=15)
        return {"url": url, "ok": True, "type": "web", **r}
    except Exception as e:
        return {"url": url, "ok": False, "error": str(e)[:200]}


def _slug(s: str, n: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9가-힣\s]", "", s).strip()
    s = re.sub(r"\s+", "_", s)
    return s[:n] or "query"


# Stop words removed from compact queries (Reddit/HN/GitHub APIs reject long natural-language queries).
_STOP_WORDS = {
    "in", "the", "a", "an", "of", "to", "for", "and", "or", "but", "is", "are",
    "be", "with", "from", "by", "at", "on", "as", "how", "do", "does", "what",
    "when", "where", "why", "this", "that", "these", "those", "i", "you", "they",
    "we", "it", "its", "we're", "they're", "best", "make", "making", "answer",
    "include", "cite", "real", "current", "techniques",
}


def _compact_query(q: str, max_words: int = 10, max_len: int = 200) -> str:
    """Long natural-language query → compact keyword string for plain-search APIs.

    Reddit search: ~512 char limit. GitHub Search: 256 char limit. HN Algolia: long queries fail.
    Removes punctuation/quotes, drops common stop words, takes first N meaningful words.
    """
    s = re.sub(r"[^\w\s가-힣\-]", " ", q)
    words = []
    for w in s.split():
        wl = w.lower().strip("-")
        if not wl or wl in _STOP_WORDS or wl.isdigit():
            continue
        words.append(w)
        if len(words) >= max_words:
            break
    out = " ".join(words)
    return out[:max_len] or q[:max_len]


def _safe_call(label: str, fn, *args, **kwargs):
    """Best-effort wrapper. Returns (ok, result_or_error)."""
    try:
        return True, fn(*args, **kwargs)
    except Exception as e:
        print(f"[dive] {label} FAIL: {str(e)[:200]}", file=sys.stderr)
        return False, str(e)[:300]


def dive(
    query: str,
    fetch_yt: bool = True,
    fetch_web: bool = True,
    max_workers: int = 8,
    reddit: bool = False,
    hn: bool = False,
    github: bool = False,
    gemini: bool = False,
    twitter: bool = False,
) -> dict:
    """한 쿼리 → perplexity + citation fetch + (옵션) 플랫폼 deep."""
    print(f"[dive] perplexity sonar-pro 호출…", file=sys.stderr)
    t0 = time.time()
    answer, cites = perplexity_query(query)
    print(f"[dive] 답변 {len(answer)} bytes / citation {len(cites)}개", file=sys.stderr)

    yt_urls = [c["url"] for c in cites if _is_youtube(c["url"])]
    web_urls = [c["url"] for c in cites if c["url"] and not _is_youtube(c["url"])]

    yt_results: list[dict] = []
    web_results: list[dict] = []

    futures: dict = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        if fetch_yt and yt_urls:
            print(f"[dive] YouTube transcript {len(yt_urls)}개 fetch…", file=sys.stderr)
            for u in yt_urls:
                futures[ex.submit(_fetch_yt_safe, u)] = ("yt", u)
        if fetch_web and web_urls:
            print(f"[dive] 일반 URL {len(web_urls)}개 fetch…", file=sys.stderr)
            for u in web_urls:
                futures[ex.submit(_fetch_web_safe, u)] = ("web", u)
        for fut in as_completed(futures):
            kind, _u = futures[fut]
            r = fut.result()
            if kind == "yt":
                yt_results.append(r)
            else:
                web_results.append(r)

    # 플랫폼 deep (옵션) — 자연어 쿼리는 plain-search API에서 거부됨 → compact 키워드만 던짐.
    # Gemini는 LLM이라 long query OK → compact 안 함.
    compact_q = _compact_query(query)
    if reddit or hn or github or twitter:
        print(f"[dive] compact 쿼리 (plain-search API용): {compact_q!r}", file=sys.stderr)

    platform_results: dict = {}
    if reddit:
        from tools.search import reddit_dive
        print(f"[dive] Reddit 검색…", file=sys.stderr)
        ok, r = _safe_call("reddit", reddit_dive.search, compact_q, n=15)
        platform_results["reddit"] = {"ok": ok, "data": r, "compact_query": compact_q}
    if hn:
        from tools.search import hn_dive
        print(f"[dive] HN 검색…", file=sys.stderr)
        ok, r = _safe_call("hn", hn_dive.search, compact_q, n=15)
        platform_results["hn"] = {"ok": ok, "data": r, "compact_query": compact_q}
    if github:
        from tools.search import github_dive
        print(f"[dive] GitHub 검색…", file=sys.stderr)
        ok, r = _safe_call("github", github_dive.search_repos, compact_q, n=8)
        platform_results["github"] = {"ok": ok, "data": r, "compact_query": compact_q}
    if gemini:
        from tools.search import gemini_dive
        print(f"[dive] Gemini 검색 (Search Grounding)…", file=sys.stderr)
        ok, r = _safe_call("gemini", gemini_dive.search, query)  # full query OK for LLM
        platform_results["gemini"] = {"ok": ok, "data": r}
    if twitter:
        from tools.search import twitter_dive
        print(f"[dive] Twitter (best-effort)…", file=sys.stderr)
        ok, r = _safe_call("twitter", twitter_dive.search, compact_q, n=15)
        platform_results["twitter"] = {"ok": ok, "data": r, "compact_query": compact_q}

    return {
        "query": query,
        "answer": answer,
        "citations": cites,
        "yt_results": yt_results,
        "web_results": web_results,
        "platforms": platform_results,
        "stats": {
            "answer_bytes": len(answer),
            "citation_count": len(cites),
            "yt_attempted": len(yt_urls),
            "yt_ok": sum(1 for r in yt_results if r.get("ok")),
            "web_attempted": len(web_urls),
            "web_ok": sum(1 for r in web_results if r.get("ok")),
            "platforms_used": list(platform_results.keys()),
            "platforms_ok": [k for k, v in platform_results.items() if v["ok"]],
            "duration_sec": round(time.time() - t0, 1),
        },
    }


def compose_md(result: dict) -> str:
    q = result["query"]
    a = result["answer"]
    cites = result["citations"]
    yts = result["yt_results"]
    webs = result["web_results"]
    plats = result.get("platforms", {})
    s = result["stats"]
    today = datetime.now().strftime("%Y-%m-%d")

    out = []
    out.append(f"# dive — {q}\n")
    out.append(f"date: {today}")
    out.append(f"source: perplexity sonar-pro + citation 1차 fetch + 플랫폼 deep ({', '.join(s['platforms_used']) or 'none'})")
    out.append(f"status: 변환 재료. 매뉴얼화 X.\n")
    out.append("---\n")
    out.append(f"## 통계")
    out.append(f"- perplexity 답변: {s['answer_bytes']} bytes")
    out.append(f"- citation: {s['citation_count']}개")
    out.append(f"- YouTube transcript: {s['yt_ok']}/{s['yt_attempted']} 성공")
    out.append(f"- 일반 URL fetch: {s['web_ok']}/{s['web_attempted']} 성공")
    if s['platforms_used']:
        out.append(f"- 플랫폼 deep: {len(s['platforms_ok'])}/{len(s['platforms_used'])} 성공 ({', '.join(s['platforms_ok']) or '없음'})")
    out.append(f"- 총 시간: {s['duration_sec']}s\n")

    out.append("---\n")
    out.append(f"## 1. perplexity 답변\n")
    out.append(a)
    out.append("\n")

    if yts:
        out.append("---\n")
        out.append(f"## 2. YouTube transcript ({s['yt_ok']}개)\n")
        for r in yts:
            if not r.get("ok"):
                out.append(f"### ❌ {r['url']}\n실패: {r.get('error', '?')}\n")
                continue
            t = r.get("title") or "?"
            dur = r.get("duration_sec") or "?"
            lang = r.get("lang", "?")
            src = r.get("source", "?")
            text = r.get("text", "")
            out.append(f"### 🎬 {t}")
            out.append(f"- URL: {r['url']}")
            out.append(f"- 길이: {dur}s / 자막: {lang} ({src}) / 본문 {len(text)}자")
            preview = text[:2500].strip()
            out.append(f"\n```\n{preview}\n{'... (전체 ' + str(len(text)) + '자)' if len(text) > 2500 else ''}\n```\n")

    if webs:
        out.append("---\n")
        out.append(f"## 3. 일반 URL 본문 발췌 ({s['web_ok']}개)\n")
        for r in webs:
            if not r.get("ok"):
                out.append(f"### ❌ {r['url']}\n실패: {r.get('error', '?')}\n")
                continue
            t = r.get("title") or "?"
            text = r.get("text", "")
            out.append(f"### 📄 {t}")
            out.append(f"- URL: {r['url']}")
            preview = text[:1500].strip()
            out.append(f"\n```\n{preview}\n{'...' if len(text) > 1500 else ''}\n```\n")

    if plats:
        out.append("---\n")
        out.append(f"## 4. 플랫폼 deep\n")
        for name, pr in plats.items():
            out.append(f"\n### {name}")
            if not pr["ok"]:
                out.append(f"❌ 실패: {pr['data']}")
                continue
            data = pr["data"]
            cq = pr.get("compact_query")
            if cq and name in ("reddit", "hn", "github", "twitter"):
                out.append(f"_compact 쿼리: `{cq}`_")
            if name in ("reddit", "hn", "github", "twitter") and isinstance(data, list) and len(data) == 0:
                out.append(f"⚠️ 결과 0개 (쿼리 매칭 X 또는 API 빈 응답)")
                continue
            if name == "reddit":
                for r in data[:15]:
                    out.append(f"- **r/{r.get('subreddit', '?')}** [{r.get('score', 0)}↑ {r.get('num_comments', 0)}💬] {r.get('title', '')}")
                    out.append(f"  - {r.get('url', '')}")
                    if r.get("selftext_preview"):
                        out.append(f"  - 본문: {r['selftext_preview'][:200]}")
            elif name == "hn":
                for r in data[:15]:
                    out.append(f"- [{r.get('points', 0)}↑ {r.get('num_comments', 0)}💬] {r.get('title', '')}")
                    out.append(f"  - HN: {r.get('hn_url', '')} / 원글: {r.get('url', '')}")
            elif name == "github":
                for r in data[:8]:
                    out.append(f"- **{r.get('full_name')}** ⭐{r.get('stars', 0)} ({r.get('language', '?')})")
                    out.append(f"  - {r.get('description', '')[:200]}")
                    out.append(f"  - {r.get('url', '')}")
            elif name == "gemini":
                ans = data.get("answer", "")
                cites_g = data.get("citations", [])
                out.append(f"\n**Gemini 답** ({len(ans)} bytes, citation {len(cites_g)}개):\n")
                out.append(ans[:3000])
                if len(ans) > 3000:
                    out.append(f"\n... (전체 {len(ans)}자)")
                if cites_g:
                    out.append(f"\n\n**Gemini citation:**")
                    for i, c in enumerate(cites_g[:10], 1):
                        out.append(f"  {i}. {c.get('title', '')} — {c.get('url', '')}")
            elif name == "twitter":
                for r in data[:15]:
                    out.append(f"- {r.get('author', '')} | {r.get('date', '')}")
                    out.append(f"  {r.get('text', '')[:300]}")
                    out.append(f"  {r.get('url', '')}")

    out.append("\n---\n")
    out.append("## 출처 통합 (perplexity citation)\n")
    for i, c in enumerate(cites, 1):
        title = c.get("title") or ""
        date = c.get("date") or ""
        out.append(f"{i}. {title} — {c['url']} ({date})")

    return "\n".join(out) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="ARC deep search — perplexity + 1차 자료 + 플랫폼 deep")
    p.add_argument("query", help="검색 쿼리")
    p.add_argument("--out", help="저장 경로 (생략 시 raw/sources/dive_{slug}_{date}.md)")
    p.add_argument("--no-yt", action="store_true", help="YouTube transcript fetch 건너뜀")
    p.add_argument("--no-web", action="store_true", help="일반 URL fetch 건너뜀")
    p.add_argument("--workers", type=int, default=8, help="병렬 fetch 워커 수 (default 8)")
    p.add_argument("--reddit", action="store_true", help="Reddit 추가 검색")
    p.add_argument("--hn", action="store_true", help="HN 추가 검색")
    p.add_argument("--github", action="store_true", help="GitHub 추가 검색")
    p.add_argument("--gemini", action="store_true", help="Gemini Google Search Grounding 추가")
    p.add_argument("--twitter", action="store_true", help="Twitter best-effort (작동 보장 X)")
    p.add_argument("--all", action="store_true", help="reddit + hn + github + gemini (twitter 제외)")
    args = p.parse_args()

    reddit = args.reddit or args.all
    hn = args.hn or args.all
    github = args.github or args.all
    gemini = args.gemini or args.all
    twitter = args.twitter

    result = dive(
        args.query,
        fetch_yt=not args.no_yt,
        fetch_web=not args.no_web,
        max_workers=args.workers,
        reddit=reddit, hn=hn, github=github, gemini=gemini, twitter=twitter,
    )
    md = compose_md(result)

    if args.out:
        out_path = Path(args.out)
    else:
        slug = _slug(args.query)
        today = datetime.now().strftime("%Y-%m-%d")
        DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = DEFAULT_OUT_DIR / f"dive_{slug}_{today}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    s = result["stats"]
    print(f"\n[dive] 저장: {out_path} ({len(md)} bytes)")
    print(f"[dive] 답변 {s['answer_bytes']}자 / yt {s['yt_ok']}/{s['yt_attempted']} / web {s['web_ok']}/{s['web_attempted']} / 플랫폼 {len(s['platforms_ok'])}/{len(s['platforms_used'])} / {s['duration_sec']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
