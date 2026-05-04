"""Bing Maps 검색에서 업체명+전화번호 추출 — 6 region × keywords."""
import asyncio, re, sys, json
from datetime import datetime
from pathlib import Path
import openpyxl
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PHONE_RE = re.compile(r'0\d{1,2}[-\s.]?\d{3,4}[-\s.]?\d{4}')
CLEAN = re.compile(r'[^\d]')
TAG = re.compile(r'<[^>]+>')
REGIONS = ["남양주", "양주", "포천", "의정부", "동두천", "가평"]
KEYWORDS = ["미용실", "카페", "음식점", "학원", "헬스장", "네일", "피부관리",
            "고깃집", "치킨", "세탁소", "약국", "부동산", "노래방", "편의점"]
LEAD_DB = Path(__file__).resolve().parent.parent / "lead_db"
DESKTOP = Path.home() / "Desktop"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
SKIP = {"전화", "번호", "연락", "스타벅스", "맥도날드", "GS25", "CU", "이마트"}


def norm(raw: str) -> str:
    d = CLEAN.sub("", raw)
    if len(d) == 10: return f"{d[:3]}-{d[3:6]}-{d[6:]}"
    if len(d) == 11: return f"{d[:3]}-{d[3:7]}-{d[7:]}"
    return raw


def is_valid(p: str) -> bool:
    d = CLEAN.sub("", p)
    return len(d) in (9, 10, 11) and d[:2] in ("01", "02", "03", "04", "05", "06", "07")


def parse(html: str, region: str, kw: str) -> list[dict]:
    seen, out = set(), []
    for m in PHONE_RE.finditer(html):
        p = norm(m.group(0))
        d = CLEAN.sub("", p)
        if not is_valid(p) or d in seen: continue
        seen.add(d)
        ctx = html[max(0, m.start()-400):m.end()+200]
        # 업체명: JSON name 필드 또는 근처 텍스트
        name = ""
        for pat in [r'"name"\s*:\s*"([^"]{2,40})"', r'"title"\s*:\s*"([^"]{2,40})"']:
            nm = re.search(pat, ctx)
            if nm and not any(s in nm.group(1) for s in SKIP):
                name = nm.group(1); break
        if not name:
            txt = TAG.sub(" ", ctx)
            for tok in re.findall(r'[가-힣]{2,15}', txt):
                if not any(s in tok for s in SKIP):
                    name = tok; break
        out.append({"phone": p, "name": name, "region": region, "keyword": kw})
    return out


async def search_bing(page, region: str, kw: str) -> list[dict]:
    url = f"https://www.bing.com/maps?q={region}+{kw}&setlang=ko&cc=KR"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2500)
        html = await page.content()
        return parse(html, region, kw)
    except PWTimeout:
        print(f"  [timeout] {region} {kw}"); return []
    except Exception as e:
        print(f"  [err] {region} {kw}: {e}"); return []


async def main():
    all_r, seen, rc = [], set(), {r: 0 for r in REGIONS}
    total = len(REGIONS) * len(KEYWORDS)
    print(f"Bing Maps 수집 시작 ({total} 쿼리)\n")

    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=True, args=["--lang=ko-KR"])
        ctx = await br.new_context(user_agent=UA, locale="ko-KR", viewport={"width": 1280, "height": 900})
        await ctx.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}", lambda r: r.abort())
        pg = await ctx.new_page()

        for i, region in enumerate(REGIONS):
            for j, kw in enumerate(KEYWORDS):
                done = i * len(KEYWORDS) + j + 1
                recs = await search_bing(pg, region, kw)
                await asyncio.sleep(0.8)
                new = 0
                for r in recs:
                    d = CLEAN.sub("", r["phone"])
                    if d not in seen:
                        seen.add(d); all_r.append(r); rc[region] += 1; new += 1
                if new: print(f"  [{done}/{total}] {region} {kw} +{new} → 누적 {len(all_r)}건")

        await br.close()

    hdrs = ["지역", "업종", "업체명", "전화번호"]
    for out in [LEAD_DB / f"북부수도권_빙맵_{TS}.xlsx", DESKTOP / f"북부수도권_빙맵_{TS}.xlsx"]:
        wb = openpyxl.Workbook(); ws = wb.active; ws.append(hdrs)
        for r in all_r: ws.append([r["region"], r["keyword"], r["name"], r["phone"]])
        wb.save(str(out))

    bk = LEAD_DB / f"북부수도권_빙맵_{TS}.json"
    with open(str(bk), "w", encoding="utf-8") as f: json.dump(all_r, f, ensure_ascii=False, indent=2)

    print(f"\n=== 완료 ===\n총 {len(all_r)}건")
    for reg in REGIONS: print(f"  {reg}: {rc[reg]}건")
    print(f"저장: 북부수도권_빙맵_{TS}.xlsx")


if __name__ == "__main__":
    asyncio.run(main())
