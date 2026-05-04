"""GitHub deep dive — repo 검색 + README + issue/discussion 본문.

무인증 60/hr, GITHUB_TOKEN .env 추가 시 5000/hr.

사용:
    python tools/search/github_dive.py search "query" [--lang python] [--n 10] [--sort stars]
    python tools/search/github_dive.py readme owner/repo
    python tools/search/github_dive.py issues owner/repo [--state open] [--n 10]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

ARC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARC_ROOT))
from tools.cost.cost_log import log_call  # noqa: E402

API = "https://api.github.com"


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        env = ARC_ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    break
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def search_repos(query: str, lang: str | None = None, n: int = 10, sort: str = "stars") -> list[dict]:
    """sort: stars (default) | forks | updated | help-wanted-issues | best-match (None)"""
    t0 = time.time()
    q = query
    if lang:
        q = f"{q} language:{lang}"
    params = {"q": q, "per_page": min(n, 100)}
    if sort != "best-match":
        params["sort"] = sort
        params["order"] = "desc"

    resp = requests.get(f"{API}/search/repositories", headers=_headers(), params=params, timeout=15)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    results = []
    for r in items:
        results.append({
            "full_name": r.get("full_name"),
            "url": r.get("html_url"),
            "description": r.get("description") or "",
            "stars": r.get("stargazers_count", 0),
            "forks": r.get("forks_count", 0),
            "language": r.get("language") or "",
            "updated_at": r.get("updated_at"),
            "topics": r.get("topics") or [],
        })

    log_call(
        tool="github_dive.search_repos",
        model="github:api",
        metadata={"query": query[:200], "lang": lang or "any", "n": n, "result_count": len(results), "duration_ms": int((time.time() - t0) * 1000)},
    )
    return results


def fetch_readme(owner_repo: str) -> dict:
    """owner/repo → README 본문 (base64 decode)."""
    t0 = time.time()
    resp = requests.get(f"{API}/repos/{owner_repo}/readme", headers=_headers(), timeout=15)
    resp.raise_for_status()
    j = resp.json()
    content_b64 = j.get("content", "")
    try:
        text = base64.b64decode(content_b64).decode("utf-8", errors="replace")
    except Exception as e:
        text = f"<decode error: {e}>"
    out = {
        "owner_repo": owner_repo,
        "name": j.get("name"),
        "path": j.get("path"),
        "size": j.get("size"),
        "html_url": j.get("html_url"),
        "text": text,
    }
    log_call(
        tool="github_dive.fetch_readme",
        model="github:api",
        metadata={"owner_repo": owner_repo, "size": j.get("size"), "duration_ms": int((time.time() - t0) * 1000)},
    )
    return out


def fetch_issues(owner_repo: str, state: str = "open", n: int = 10, labels: str | None = None) -> list[dict]:
    """state: open | closed | all"""
    t0 = time.time()
    params = {"state": state, "per_page": min(n, 100)}
    if labels:
        params["labels"] = labels
    resp = requests.get(f"{API}/repos/{owner_repo}/issues", headers=_headers(), params=params, timeout=15)
    resp.raise_for_status()
    items = resp.json()
    results = []
    for it in items:
        if it.get("pull_request"):  # skip PRs (issues endpoint includes them)
            continue
        results.append({
            "number": it.get("number"),
            "title": it.get("title", ""),
            "state": it.get("state", ""),
            "user": (it.get("user") or {}).get("login", ""),
            "comments": it.get("comments", 0),
            "created_at": it.get("created_at"),
            "html_url": it.get("html_url"),
            "body_preview": (it.get("body") or "")[:1500],
            "labels": [lab.get("name") for lab in (it.get("labels") or [])],
        })

    log_call(
        tool="github_dive.fetch_issues",
        model="github:api",
        metadata={"owner_repo": owner_repo, "state": state, "n": n, "result_count": len(results), "duration_ms": int((time.time() - t0) * 1000)},
    )
    return results


def main() -> int:
    p = argparse.ArgumentParser(description="GitHub deep dive (API)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp_search = sub.add_parser("search")
    sp_search.add_argument("query")
    sp_search.add_argument("--lang")
    sp_search.add_argument("--n", type=int, default=10)
    sp_search.add_argument("--sort", default="stars", choices=["stars", "forks", "updated", "help-wanted-issues", "best-match"])
    sp_readme = sub.add_parser("readme")
    sp_readme.add_argument("owner_repo")
    sp_issues = sub.add_parser("issues")
    sp_issues.add_argument("owner_repo")
    sp_issues.add_argument("--state", default="open", choices=["open", "closed", "all"])
    sp_issues.add_argument("--n", type=int, default=10)
    sp_issues.add_argument("--labels")
    args = p.parse_args()

    if args.cmd == "search":
        r = search_repos(args.query, lang=args.lang, n=args.n, sort=args.sort)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    elif args.cmd == "readme":
        r = fetch_readme(args.owner_repo)
        print(json.dumps({**r, "text_preview": r["text"][:3000], "text_len": len(r["text"])}, indent=2, ensure_ascii=False))
    else:
        r = fetch_issues(args.owner_repo, state=args.state, n=args.n, labels=args.labels)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
