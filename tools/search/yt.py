"""YouTube scout — search + transcript only (no comments).

§2 No-Silent-Fail: missing key / no transcript / network = raise loud.
§5.1.1: returned dict has video_id + url + ISO timestamp 박힌 메타.
DOCTRINE §0: yt-dlp = YouTube ToS 회색 (정보로만 표시, 차감 X).
"""
import json
import os
import sys
import time
from pathlib import Path
from xml.etree import ElementTree as ET

import requests
import yt_dlp

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.cost.cost_log import log_call


def search(query: str, n: int = 5, api_key: str | None = None) -> list[dict]:
    """Search YouTube. Data API if YOUTUBE_API_KEY set, else yt-dlp ytsearch fallback."""
    api_key = api_key or os.getenv("YOUTUBE_API_KEY")
    t0 = time.time()
    mode = "data_api" if api_key else "ytdlp_fallback"
    if api_key:
        results = _search_data_api(query, n, api_key)
    else:
        results = _search_ytdlp(query, n)
    log_call(
        tool="youtube_scout.search",
        model=f"youtube:{mode}",
        metadata={
            "query": query[:200],
            "n": n,
            "result_count": len(results),
            "duration_ms": int((time.time() - t0) * 1000),
        },
    )
    return results


def _search_data_api(query: str, n: int, api_key: str) -> list[dict]:
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": min(n, 50),
        "type": "video",
        "key": api_key,
        "regionCode": "KR",
        "relevanceLanguage": "ko",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return [
        {
            "video_id": it["id"]["videoId"],
            "title": it["snippet"]["title"],
            "channel": it["snippet"]["channelTitle"],
            "published_at": it["snippet"]["publishedAt"],
            "description": it["snippet"]["description"][:300],
            "url": f"https://www.youtube.com/watch?v={it['id']['videoId']}",
        }
        for it in items
    ]


def _search_ytdlp(query: str, n: int) -> list[dict]:
    ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
    return [
        {
            "video_id": e.get("id"),
            "title": e.get("title"),
            "channel": e.get("channel") or e.get("uploader"),
            "duration_sec": e.get("duration"),
            "view_count": e.get("view_count"),
            "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
        }
        for e in info.get("entries", []) if e
    ]


def fetch_transcript(video_id: str, lang_priority: list[str] | None = None) -> dict:
    """Fetch transcript. Tries manual subs in lang order, then auto-generated. Raises if none."""
    lang_priority = lang_priority or ["ko", "en"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    t0 = time.time()
    ydl_opts = {
        "quiet": True, "skip_download": True, "no_warnings": True,
        "writesubtitles": True, "writeautomaticsub": True,
        "subtitleslangs": lang_priority,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    subs = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    title = info.get("title", "")
    duration = info.get("duration")

    for lang in lang_priority:
        for source_dict, source_label in ((subs, "manual"), (auto, "auto")):
            entries = source_dict.get(lang)
            if not entries:
                continue
            for entry in entries:
                if entry.get("ext") not in ("json3", "vtt", "srv1"):
                    continue
                resp = requests.get(entry["url"], timeout=15)
                resp.raise_for_status()
                text = _parse_subtitle(resp.text, entry["ext"])
                if not text:
                    continue
                log_call(
                    tool="youtube_scout.transcript",
                    model="yt_dlp",
                    metadata={
                        "video_id": video_id, "lang": lang, "source": source_label,
                        "char_count": len(text), "duration_ms": int((time.time() - t0) * 1000),
                    },
                )
                return {
                    "video_id": video_id, "title": title, "duration_sec": duration,
                    "lang": lang, "source": source_label, "text": text, "url": url,
                }

    raise RuntimeError(
        f"§2 No transcript available for {video_id} in langs {lang_priority} "
        f"(manual={list(subs.keys())[:5]}, auto={list(auto.keys())[:5]})"
    )


def _parse_subtitle(text: str, ext: str) -> str:
    if ext == "json3":
        data = json.loads(text)
        out = []
        for ev in data.get("events", []):
            for seg in ev.get("segs") or []:
                if "utf8" in seg:
                    out.append(seg["utf8"])
        return "".join(out).strip()
    if ext == "vtt":
        out = []
        for line in text.splitlines():
            line = line.strip()
            if not line or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or line.isdigit():
                continue
            out.append(line)
        return " ".join(out)
    if ext == "srv1":
        root = ET.fromstring(text)
        return " ".join((t.text or "") for t in root.findall(".//text"))
    return text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:\n  python youtube_scout.py search '<query>' [n=5]\n  python youtube_scout.py transcript <video_id>")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "search":
        q = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        print(json.dumps(search(q, n), indent=2, ensure_ascii=False))
    elif cmd == "transcript":
        vid = sys.argv[2]
        result = fetch_transcript(vid)
        result["text_preview"] = result["text"][:1500]
        result["text_len"] = len(result["text"])
        del result["text"]
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
