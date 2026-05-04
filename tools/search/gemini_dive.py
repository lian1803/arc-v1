"""Gemini deep dive — Google Search Grounding + YouTube URL 직접 분석.

Perplexity 대비 강점:
- Google Search Grounding = 실시간 트렌드/뉴스 빠름 (구글 인덱스 직결)
- YouTube URL 직접 input → 영상 시각/음성 분석 (transcript 없는 영상도 OK)
- 가격 ~20배 저렴 (Gemini 2.5 Flash $0.30/Mtok input vs sonar-pro $6/Mtok)

약점:
- 멀티 출처 citation 깊이 약함
- 학술/논문 인용 약함

사용:
    python tools/search/gemini_dive.py search "쿼리"
    python tools/search/gemini_dive.py youtube "https://youtube.com/watch?v=..." --question "핵심 5개"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ARC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARC_ROOT))
from tools.cost.cost_log import log_call  # noqa: E402

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

MODEL_SEARCH = "gemini-2.5-flash"
MODEL_VIDEO = "gemini-2.0-flash"


def _load_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        env = ARC_ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing (.env or env var)")
    return key


def _client() -> genai.Client:
    return genai.Client(api_key=_load_key())


def search(query: str, model: str = MODEL_SEARCH) -> dict:
    """Google Search Grounding으로 실시간 검색 답변. citation 자동 포함."""
    t0 = time.time()
    client = _client()
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )
    resp = client.models.generate_content(model=model, contents=query, config=config)
    text = (resp.text or "").strip()

    citations: list[dict] = []
    search_queries: list[str] = []
    try:
        if resp.candidates and resp.candidates[0].grounding_metadata:
            gm = resp.candidates[0].grounding_metadata
            for chunk in (gm.grounding_chunks or []):
                if chunk.web:
                    citations.append({
                        "url": chunk.web.uri or "",
                        "title": chunk.web.title or "",
                    })
            search_queries = list(gm.web_search_queries or [])
    except Exception:
        pass  # grounding metadata 형식 변동 가능 — best-effort

    log_call(
        tool="gemini_dive.search",
        model=f"gemini:{model}",
        metadata={
            "query": query[:200],
            "answer_bytes": len(text),
            "citation_count": len(citations),
            "duration_ms": int((time.time() - t0) * 1000),
        },
    )
    return {
        "query": query,
        "model": model,
        "answer": text,
        "citations": citations,
        "search_queries": search_queries,
    }


def analyze_youtube(url: str, question: str | None = None, model: str = MODEL_VIDEO) -> dict:
    """YouTube URL 직접 input → 영상 시각/음성 분석.

    transcript 없는 영상도 분석 가능 (Gemini가 시각/음성 직접 처리).
    """
    if question is None:
        question = "이 영상의 핵심 내용을 한국어로 5개 bullet로 요약해줘. 시간대 (HH:MM:SS) 표시 포함."
    t0 = time.time()
    client = _client()
    contents = types.Content(parts=[
        types.Part(file_data=types.FileData(file_uri=url, mime_type="video/*")),
        types.Part(text=question),
    ])
    resp = client.models.generate_content(model=model, contents=contents)
    text = (resp.text or "").strip()

    log_call(
        tool="gemini_dive.youtube",
        model=f"gemini:{model}",
        metadata={
            "url": url[:300],
            "question_preview": question[:100],
            "answer_bytes": len(text),
            "duration_ms": int((time.time() - t0) * 1000),
        },
    )
    return {
        "url": url,
        "model": model,
        "question": question,
        "answer": text,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Gemini deep dive — Search Grounding + YouTube")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp_search = sub.add_parser("search")
    sp_search.add_argument("query")
    sp_search.add_argument("--model", default=MODEL_SEARCH)
    sp_yt = sub.add_parser("youtube")
    sp_yt.add_argument("url")
    sp_yt.add_argument("--question", default=None)
    sp_yt.add_argument("--model", default=MODEL_VIDEO)
    args = p.parse_args()

    if args.cmd == "search":
        r = search(args.query, model=args.model)
    else:
        r = analyze_youtube(args.url, question=args.question, model=args.model)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
