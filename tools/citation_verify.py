#!/usr/bin/env python
"""citation_verify.py — session 13 patch #4

Extract URLs from markdown, HEAD-check each, report.

Usage:
    python tools/citation_verify.py <markdown_path> [--budget-usd 0.00 --timeout 10]

Exit codes:
    0 — all URLs resolve 2xx/3xx
    1 — any URL returns >=400 or times out (DOCTRINE §2 no-silent-fail)
    2 — invalid input / file not found

Integration:
    - qa_reviewer.md §Factual Accuracy (Item 1) — verifier calls this on any artifact with >3 URLs.
    - smoke_test.py tier-1 regression (optional, --live only).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

URL_RE = re.compile(r"https?://[^\s\)\]\>\"]+", re.IGNORECASE)
TRAILING_PUNCT = ".,;:!?"


def extract_urls(text: str) -> list[str]:
    raw = URL_RE.findall(text)
    cleaned = []
    seen = set()
    for url in raw:
        while url and url[-1] in TRAILING_PUNCT:
            url = url[:-1]
        if url and url not in seen:
            cleaned.append(url)
            seen.add(url)
    return cleaned


def head_check(url: str, timeout: int = 10) -> dict[str, Any]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ARC-citation-verify/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"url": url, "status": resp.status, "ok": 200 <= resp.status < 400, "error": None}
    except urllib.error.HTTPError as e:
        if e.code == 405:  # Method Not Allowed — retry with GET (HEAD often blocked)
            try:
                req2 = urllib.request.Request(url, method="GET", headers={"User-Agent": "ARC-citation-verify/1.0"})
                with urllib.request.urlopen(req2, timeout=timeout) as resp:
                    return {"url": url, "status": resp.status, "ok": 200 <= resp.status < 400, "error": None}
            except Exception as e2:
                return {"url": url, "status": None, "ok": False, "error": f"GET fallback: {e2}"}
        return {"url": url, "status": e.code, "ok": False, "error": f"HTTPError {e.code}"}
    except urllib.error.URLError as e:
        return {"url": url, "status": None, "ok": False, "error": f"URLError: {e.reason}"}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "error": f"{type(e).__name__}: {e}"}


def main() -> int:
    p = argparse.ArgumentParser(description="Verify URLs in a markdown file resolve.")
    p.add_argument("path", help="Markdown file to scan.")
    p.add_argument("--timeout", type=int, default=10, help="HTTP timeout (s).")
    p.add_argument("--json", action="store_true", help="Output JSON instead of human-readable.")
    args = p.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    urls = extract_urls(text)
    if not urls:
        if args.json:
            print(json.dumps({"path": str(path), "urls": [], "total": 0, "failed": 0}))
        else:
            print(f"No URLs found in {path}.")
        return 0

    results = [head_check(u, timeout=args.timeout) for u in urls]
    failed = [r for r in results if not r["ok"]]

    if args.json:
        print(json.dumps({"path": str(path), "total": len(urls), "failed": len(failed), "results": results}, ensure_ascii=False))
    else:
        print(f"# Citation Verify — {path}")
        print(f"Total URLs: {len(urls)} | OK: {len(urls) - len(failed)} | FAILED: {len(failed)}\n")
        for r in results:
            marker = "OK " if r["ok"] else "FAIL"
            status = r["status"] if r["status"] is not None else "-"
            err = f"  [{r['error']}]" if r["error"] else ""
            print(f"  {marker} {status:>4}  {r['url']}{err}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
