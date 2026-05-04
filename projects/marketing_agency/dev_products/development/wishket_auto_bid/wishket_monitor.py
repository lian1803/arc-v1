"""
위시켓 새 의뢰글 모니터 — 사이트맵 기반 (정적 HTML, JS 불필요)
전략: sitemap-project.xml → lastmod 오늘 = 신규 → og 태그 + body 파싱
실행: python wishket_monitor.py
"""
import json
import time
import re
from pathlib import Path
from datetime import date, datetime
import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET

SEEN_FILE = Path(__file__).parent / "seen_listings.jsonl"
LEADS_FILE = Path(__file__).parent / "wishket_leads.jsonl"

SITEMAP_URL = "https://www.wishket.com/sitemap-project.xml"

# IT·개발 관련 카테고리 키워드 (body 텍스트에서 매칭)
IT_KEYWORDS = [
    "웹", "앱", "모바일", "자동화", "개발", "API", "서버", "백엔드",
    "프론트", "데이터", "AI", "챗봇", "시스템", "솔루션", "플랫폼",
    "ERP", "CRM", "쇼핑몰", "커머스", "SaaS", "파이썬", "Python",
    "React", "Vue", "Flutter", "Node",
]

MIN_BUDGET = 300_000   # 30만원 미만 스킵
MAX_NEW_PER_RUN = 15   # 1회 최대 처리 건수

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://www.wishket.com/",
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


def parse_budget_from_text(text: str) -> tuple[str, int]:
    """'예상 금액 8,000,000원' → ('8,000,000원', 8000000)"""
    m = re.search(r"예상\s*금액\s*([\d,]+)\s*원", text)
    if m:
        raw = m.group(1).replace(",", "")
        return f"{int(raw):,}원", int(raw)
    m2 = re.search(r"([\d,]+)\s*만\s*원", text)
    if m2:
        raw = int(m2.group(1).replace(",", "")) * 10000
        return f"{raw // 10000}만원", raw
    return "협의", 0


def parse_duration_from_text(text: str) -> str:
    m = re.search(r"예상\s*기간\s*(\d+)\s*일", text)
    return f"{m.group(1)}일" if m else ""


def parse_category_from_text(text: str) -> str:
    for kw in IT_KEYWORDS:
        if kw in text:
            return kw
    return "IT·개발"


def fetch_project_urls_from_sitemap(top_n: int = 50) -> list[tuple[str, str]]:
    """사이트맵에서 가장 최신 N개 URL 반환 (project ID 내림차순).
    lastmod 불안정 — ID 정렬 + seen_list 중복제거로 신규만 처리."""
    try:
        r = requests.get(SITEMAP_URL, headers=HEADERS, timeout=60)
        r.raise_for_status()
    except Exception as e:
        print(f"[ERROR] 사이트맵 가져오기 실패: {e}")
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.fromstring(r.content)

    urls = []
    for url_el in root.findall("sm:url", ns):
        loc = url_el.findtext("sm:loc", default="", namespaces=ns)
        lastmod = url_el.findtext("sm:lastmod", default="", namespaces=ns)
        if not loc or "/project/" not in loc:
            continue
        m = re.search(r"/project/(\d+)/", loc)
        if not m:
            continue
        urls.append((loc, lastmod, int(m.group(1))))

    # project ID 내림차순 (높을수록 최신)
    urls.sort(key=lambda x: x[2], reverse=True)
    return [(loc, lm) for loc, lm, _ in urls[:top_n]]


def scrape_project_detail(url: str) -> dict | None:
    """프로젝트 상세 페이지 → og 태그 + body 파싱"""
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

    title = og.get("og:title", "").replace(" | 위시켓", "").strip()
    description = og.get("og:description", og.get("description", ""))[:800]

    if not title:
        return None

    body_text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
    budget_text, budget = parse_budget_from_text(body_text)
    duration = parse_duration_from_text(body_text)
    category = parse_category_from_text(body_text + " " + title)

    # ID = URL 끝 숫자
    m = re.search(r"/project/(\d+)/", url)
    listing_id = m.group(1) if m else url[-12:]

    return {
        "id": listing_id,
        "title": title,
        "description": description,
        "budget_text": budget_text,
        "budget": budget,
        "duration": duration,
        "category": category,
        "url": url,
        "scraped_at": datetime.now().isoformat(),
    }


def is_it_relevant(listing: dict) -> bool:
    text = listing["title"] + " " + listing["description"]
    return any(kw in text for kw in IT_KEYWORDS)


def monitor() -> list[dict]:
    seen = load_seen()
    print("사이트맵 스캔 중 (최신 50건)...")
    urls = fetch_project_urls_from_sitemap(top_n=50)
    print(f"후보 URL: {len(urls)}건")

    new_listings = []
    for url, lastmod in urls:
        if len(new_listings) >= MAX_NEW_PER_RUN:
            break

        m = re.search(r"/project/(\d+)/", url)
        listing_id = m.group(1) if m else url
        if listing_id in seen:
            continue

        listing = scrape_project_detail(url)
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
        time.sleep(1.5)

    return new_listings


def save_leads(listings: list[dict]):
    with LEADS_FILE.open("a", encoding="utf-8") as f:
        for item in listings:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    new = monitor()
    print(f"새 의뢰글 (IT 관련): {len(new)}건")
    if new:
        save_leads(new)
        for item in new:
            print(f"  [{item['category']}] {item['title'][:50]} / {item['budget_text']} ({item['duration']})")
