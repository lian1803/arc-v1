"""네이버 웹 검색으로 당근 local-profile URL 수집 → 프로필 방문 → 010 추출."""
import asyncio, re, sys, json
from datetime import datetime
from pathlib import Path
import openpyxl
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLEAN = re.compile(r'[^\d]')
DAANGN_URL = re.compile(r'https?://(?:www\.)?daangn\.com/kr/local-profile/[^\s"\'<>&]+')
REGIONS = ["남양주", "양주", "포천", "의정부", "동두천", "가평"]
KEYWORDS = ["미용실", "카페", "음식점", "학원", "헬스장", "네일", "고깃집", "치킨", "약국", "부동산"]
LEAD_DB = Path(__file__).resolve().parent.parent / "lead_db"
DESKTOP = Path.home() / "Desktop"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"


def norm(raw: str) -> str:
    d = CLEAN.sub("", raw)
    if len(d) == 10: return f"{d[:3]}-{d[3:6]}-{d[6:]}"
    if len(d) == 11: return f"{d[:3]}-{d[3:7]}-{d[7:]}"
    return raw


def is_mobile(p: str) -> bool:
    d = CLEAN.sub("", p)
    return d.startswith("01") and len(d) in (10, 11)


async def get_daangn_urls(page, region: str, kw: str) -> list[str]:
    q = f"{region} {kw} 당근마켓"
    url = f"https://search.naver.com/search.naver?query={q}&where=web"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=18000)
        await page.wait_for_timeout(700)
        html = await page.content()
        return list(dict.fromkeys(DAANGN_URL.findall(html)))
    except Exception:
        return []


async def scrape_profile(page, url: str, region: str, kw: str) -> list[dict]:
    try:
        await page.goto(url, wait_until="load", timeout=15000)
        await page.wait_for_timeout(2500)
        html = await page.content()
        phones = []
        for pat in [r'tel:(01[016789][0-9\-\.]{8,12})', r'01[016789][-\s.]?\d{3,4}[-\s.]?\d{4}']:
            for m in re.finditer(pat, html):
                raw = m.group(1) if m.lastindex else m.group(0)
                p = norm(raw)
                if is_mobile(p) and p not in [x["phone"] for x in phones]:
                    phones.append({"phone": p})
        name_m = re.search(r'"name"\s*:\s*"([^"]{2,40})"', html)
        name = name_m.group(1) if name_m else ""
        if not name:
            h1 = re.search(r'<h1[^>]*>([^<]{2,30})</h1>', html)
            name = h1.group(1) if h1 else ""
        return [{"phone": r["phone"], "name": name, "region": region, "keyword": kw,
                 "daangn_url": url} for r in phones]
    except PWTimeout:
        return []
    except Exception as e:
        print(f"  [err] {url[:50]}: {e}")
        return []


async def main():
    all_r, seen_phones, seen_urls = [], set(), set()
    rc = {r: 0 for r in REGIONS}
    total_q = len(REGIONS) * len(KEYWORDS)
    print(f"당근 local-profile 010 수집 시작 ({total_q} 쿼리)\n")

    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=True, args=["--lang=ko-KR"])
        ctx = await br.new_context(user_agent=UA, locale="ko-KR", viewport={"width": 1280, "height": 900})
        await ctx.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}", lambda r: r.abort())
        pg = await ctx.new_page()

        for i, region in enumerate(REGIONS):
            for j, kw in enumerate(KEYWORDS):
                done = i * len(KEYWORDS) + j + 1
                urls = await get_daangn_urls(pg, region, kw)
                new_urls = [u for u in urls if u not in seen_urls][:3]
                for u in new_urls: seen_urls.add(u)

                if new_urls:
                    print(f"  [{done}/{total_q}] {region} {kw} → 당근URL {len(new_urls)}개 방문 중")

                new_count = 0
                for url in new_urls:
                    recs = await scrape_profile(pg, url, region, kw)
                    await asyncio.sleep(0.6)
                    for r in recs:
                        if r["phone"] not in seen_phones:
                            seen_phones.add(r["phone"])
                            all_r.append(r); rc[region] += 1; new_count += 1

                if new_count:
                    print(f"    +{new_count}건 → 누적 {len(all_r)}건")
                await asyncio.sleep(0.5)

        await br.close()

    hdrs = ["지역", "업종", "업체명", "010번호", "당근URL"]
    for out in [LEAD_DB / f"북부수도권_당근010_{TS}.xlsx", DESKTOP / f"북부수도권_당근010_{TS}.xlsx"]:
        wb = openpyxl.Workbook(); ws = wb.active; ws.append(hdrs)
        for r in all_r:
            ws.append([r["region"], r["keyword"], r["name"], r["phone"], r["daangn_url"]])
        wb.save(str(out))

    bk = LEAD_DB / f"북부수도권_당근010_{TS}.json"
    with open(str(bk), "w", encoding="utf-8") as f: json.dump(all_r, f, ensure_ascii=False, indent=2)

    print(f"\n=== 완료 ===\n총 {len(all_r)}건 (당근 local-profile)")
    for reg in REGIONS: print(f"  {reg}: {rc[reg]}건")
    print(f"저장: 북부수도권_당근010_{TS}.xlsx")


if __name__ == "__main__":
    asyncio.run(main())
