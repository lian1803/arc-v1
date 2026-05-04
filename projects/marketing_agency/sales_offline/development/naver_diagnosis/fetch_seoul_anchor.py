"""서울 상위권 5 카테고리 × 10 업체 anchor fetch → seoul_anchor.json (PDF 비교 기준)."""
import sys, asyncio, json, os, io
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
load_dotenv(THIS_DIR / ".env")

# stdout wrap (한국어 console)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CATEGORIES = {
    "식당": "서울 맛집",
    "미용실": "서울 미용실",
    "카페": "서울 카페",
    "학원": "서울 학원",
    "기타": "서울 가게",
}

OUT_PATH = THIS_DIR / "seoul_anchor.json"
TOP_N = 10


async def fetch_category(crawler, category_key, query):
    """1 카테고리 — 상위 N 업체 평균."""
    print(f"\n[{category_key}] '{query}' 검색")
    try:
        place_ids = await crawler.extract_top_place_ids(query, top_n=TOP_N)
    except Exception as e:
        print(f"  ❌ 검색 fail: {e}")
        return {}
    print(f"  상위 {len(place_ids)} place_id: {place_ids[:3]}...")

    rows = []
    for idx, pid in enumerate(place_ids[:TOP_N], 1):
        try:
            d = await crawler.crawl_place_detail(pid)
            if d:
                rows.append(d)
                print(f"  [{idx}/{len(place_ids[:TOP_N])}] place_id {pid}: photo={d.get('photo_count',0)}, review={(d.get('visitor_review_count',0) or 0)+(d.get('receipt_review_count',0) or 0)}, blog={d.get('blog_review_count',0)}")
        except Exception as e:
            print(f"  [{idx}] place_id {pid} fail: {e}")

    if not rows:
        return {}

    n = len(rows)
    def avg_int(field):
        vals = [r.get(field, 0) or 0 for r in rows]
        return round(sum(vals) / n) if vals else 0
    def review_avg():
        vals = [(r.get("visitor_review_count", 0) or 0) + (r.get("receipt_review_count", 0) or 0) for r in rows]
        return round(sum(vals) / n) if vals else 0
    def bool_rate(field):
        vals = [bool(r.get(field, False)) for r in rows]
        return round(sum(vals) / n, 2) if vals else 0.0

    return {
        "sample_size": n,
        "avg_photo": avg_int("photo_count"),
        "avg_review": review_avg(),
        "avg_blog": avg_int("blog_review_count"),
        "intro_rate": bool_rate("has_intro"),
        "menu_rate": bool_rate("has_menu"),
        "directions_rate": bool_rate("has_directions"),
        "booking_rate": bool_rate("has_booking"),
        "talktalk_rate": bool_rate("has_talktalk"),
        "news_rate": bool_rate("has_news"),
        "instagram_rate": bool_rate("has_instagram"),
        "kakao_rate": bool_rate("has_kakao"),
        "place_ids": place_ids[:n],
    }


async def main():
    from playwright.async_api import async_playwright
    from services.naver_place_crawler import NaverPlaceCrawler

    print("=" * 60)
    print("서울 상위권 anchor fetch (5 카테고리 × 10 업체)")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            crawler = NaverPlaceCrawler(browser)
            results = {}
            for cat_key, query in CATEGORIES.items():
                results[cat_key] = await fetch_category(crawler, cat_key, query)
        finally:
            await browser.close()

    out = {
        "fetched_at": datetime.now().isoformat(),
        "categories": results,
    }
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}\n저장: {OUT_PATH}\n{'='*60}")
    for cat, data in results.items():
        if data:
            print(f"  [{cat}] sample={data.get('sample_size',0)} photo={data.get('avg_photo',0)} review={data.get('avg_review',0)} blog={data.get('avg_blog',0)}")
        else:
            print(f"  [{cat}] (empty)")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
