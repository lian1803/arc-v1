"""
크몽 enterprise requests 모니터 — sitemap/request_id.xml 기반
URL: kmong.com/enterprise/requests/{id}
og:title = 프로젝트명 | og:description = 예산 | body = 상세 설명
"""
import json
import time
import re
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET

SEEN_FILE = Path(__file__).parent / "seen_kmong.jsonl"
LEADS_FILE = Path(__file__).parent / "wishket_leads.jsonl"

SITEMAP_URL = "https://kmong.com/sitemap/request_id.xml"

IT_KEYWORDS = [
    "웹", "앱", "모바일", "자동화", "개발", "API", "서버", "백엔드",
    "프론트", "데이터", "AI", "챗봇", "시스템", "솔루션", "플랫폼",
    "ERP", "CRM", "쇼핑몰", "커머스", "SaaS", "파이썬", "Python",
    "React", "Vue", "Flutter", "Node", "C++", "Java", "클라우드",
    "AWS", "GCP", "Azure", "DevOps", "CI/CD",
]

MIN_BUDGET = 300_000
MAX_NEW_PER_RUN = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://kmong.com/",
}


def load_seen() -> set:
    if not SEEN_FILE.exists():
        return set()
    seen = set()
    for line in SEEN_FILE.read_text(encoding="utf-8").strip().splitlines():
        if line.strip():
            try:
                seen.add(json.loads(line)["id"])
            except Exception:
                pass
    return seen


def save_seen(listing_id: str):
    with SEEN_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"id": listing_id, "ts": datetime.now().isoformat()}) + "\n")


def parse_budget_from_og(og_desc: str) -> tuple[str, int]:
    """'예산: 7000000원' -> ('7,000,000원', 7000000)"""
    m = re.search(r"예산[:\s]*([\d,]+)\s*원", og_desc)
    if m:
        raw = int(m.group(1).replace(",", ""))
        return f"{raw:,}원", raw
    m2 = re.search(r"([\d,]+)\s*만\s*원", og_desc)
    if m2:
        raw = int(m2.group(1).replace(",", "")) * 10000
        return f"{raw // 10000}만원", raw
    return "협의", 0


def fetch_request_urls(top_n: int = 50) -> list[tuple[str, str]]:
    """크몽 request sitemap에서 최신 N개 URL 반환 (ID 내림차순)"""
    try:
        r = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] 크몽 사이트맵 실패: {e}")
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.fromstring(r.content)

    urls = []
    for url_el in root.findall("sm:url", ns):
        loc = url_el.findtext("sm:loc", default="", namespaces=ns)
        lastmod = url_el.findtext("sm:lastmod", default="", namespaces=ns)
        if not loc or "/enterprise/requests/" not in loc:
            continue
        m = re.search(r"/requests/(\d+)", loc)
        if not m:
            continue
        urls.append((loc, lastmod, int(m.group(1))))

    urls.sort(key=lambda x: x[2], reverse=True)
    return [(loc, lm) for loc, lm, _ in urls[:top_n]]


def scrape_request_detail(url: str) -> dict | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"  [WARN] {url}: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    og = {}
    for meta in soup.find_all("meta"):
        prop = meta.get("property") or meta.get("name", "")
        if prop.startswith("og:") or "description" in prop:
            og[prop] = meta.get("content", "")

    title = og.get("og:title", "").replace(" - 크몽", "").strip()
    og_desc = og.get("og:description", og.get("description", ""))
    if not title:
        return None

    budget_text, budget = parse_budget_from_og(og_desc)

    body_text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
    description = body_text[:800]

    m = re.search(r"/requests/(\d+)", url)
    listing_id = f"kmong_{m.group(1)}" if m else url[-10:]

    return {
        "id": listing_id,
        "title": title,
        "description": description,
        "budget_text": budget_text,
        "budget": budget,
        "duration": "",
        "category": _detect_category(title + " " + description),
        "url": url,
        "platform": "크몽",
        "scraped_at": datetime.now().isoformat(),
    }


def _detect_category(text: str) -> str:
    for kw in ["자동화", "앱", "모바일", "웹", "AI", "데이터", "ERP", "CRM"]:
        if kw in text:
            return kw
    return "IT·개발"


def is_it_relevant(listing: dict) -> bool:
    text = listing["title"] + " " + listing["description"]
    return any(kw in text for kw in IT_KEYWORDS)


def monitor() -> list[dict]:
    seen = load_seen()
    print("크몽 스캔 중 (최신 50건)...")
    urls = fetch_request_urls(top_n=50)
    print(f"후보 URL: {len(urls)}건")

    new_listings = []
    for url, lastmod in urls:
        if len(new_listings) >= MAX_NEW_PER_RUN:
            break

        m = re.search(r"/requests/(\d+)", url)
        listing_id = f"kmong_{m.group(1)}" if m else url
        if listing_id in seen:
            continue

        listing = scrape_request_detail(url)
        if not listing:
            continue

        if listing["budget"] > 0 and listing["budget"] < MIN_BUDGET:
            save_seen(listing_id)
            continue

        if not is_it_relevant(listing):
            save_seen(listing_id)
            continue

        new_listings.append(listing)
        save_seen(listing_id)
        time.sleep(1)

    return new_listings


def save_leads(listings: list[dict]):
    with LEADS_FILE.open("a", encoding="utf-8") as f:
        for item in listings:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    new = monitor()
    print(f"크몽 새 의뢰: {len(new)}건")
    if new:
        save_leads(new)
        for item in new:
            print(f"  [{item['category']}] {item['title'][:50]} / {item['budget_text']}")
