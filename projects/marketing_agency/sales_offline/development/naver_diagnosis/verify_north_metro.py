"""북부수도권 6지역 통합 db verify — 다지역 매칭.
각 row: query "{이름} {지역}" → Naver API → 6 target 중 하나에 매칭되면 verified."""
import asyncio, os, re, sys
from datetime import datetime
from pathlib import Path
import httpx, openpyxl
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

THIS = Path(__file__).resolve().parent
LEAD_DB = THIS.parent / "lead_db"
load_dotenv(THIS / ".env")
NID, NSEC = os.getenv("NAVER_CLIENT_ID"), os.getenv("NAVER_CLIENT_SECRET")
INPUT = max(LEAD_DB.glob("북부수도권_통합_*.xlsx"), key=lambda p: p.stat().st_mtime)
TS = datetime.now().strftime("%Y%m%d_%H%M%S")

# 양주 vs 남양주 구분: 더 specific 한 (남양주) 먼저 체크
TARGETS = [("남양주", "경기도 남양주시"), ("양주", "경기도 양주시"),
           ("포천", "경기도 포천시"), ("의정부", "경기도 의정부시"),
           ("동두천", "경기도 동두천시"), ("가평", "경기도 가평군")]


def find_col(headers, *keys):
    for i, h in enumerate(headers):
        if any(k in h for k in keys):
            return i
    return -1


def matched_region(addr):
    if not addr: return None
    for r, prefix in TARGETS:
        if prefix in addr:
            return r
    return None


async def search(client, q):
    try:
        r = await client.get(
            "https://openapi.naver.com/v1/search/local.json",
            headers={"X-Naver-Client-Id": NID, "X-Naver-Client-Secret": NSEC},
            params={"query": q, "display": 5}, timeout=8.0)
        if r.status_code == 429:
            await asyncio.sleep(2.0); return None
        return r.json().get("items", [])
    except Exception:
        return None


def find_match(items):
    if not items: return None
    for it in items:
        addr = (it.get("address", "") + " " + it.get("roadAddress", "")).strip()
        r = matched_region(addr)
        if r:
            return {"address": addr, "link": it.get("link", ""),
                    "name": re.sub(r"<[^>]+>", "", it.get("title", "")), "region": r}
    return None


async def verify(client, name, kakao_addr, file_region, industry):
    if not name: return 0, None
    queries = [(1, f"{name} {file_region}")]
    kr = matched_region(kakao_addr or "")
    if kr and kr != file_region:
        queries.append((2, f"{name} {kr}"))
    if industry:
        queries.append((3, f"{name} {industry}"))
    for step, q in queries:
        m = find_match(await search(client, q))
        if m: return step, m
    return 0, None


async def main(limit=None):
    wb = openpyxl.load_workbook(str(INPUT), read_only=True, data_only=True)
    rows_all = list(wb.active.iter_rows(values_only=True)); wb.close()
    headers = [str(h).strip() if h else "" for h in rows_all[0]]
    rows = rows_all[1:limit+1] if limit else rows_all[1:]

    ni = find_col(headers, "업체명", "상호")
    ai = find_col(headers, "수집주소", "주소")
    ii = find_col(headers, "업종")
    ri = find_col(headers, "지역")
    out_headers = list(headers) + ["네이버주소", "네이버URL", "매칭지역", "매칭방법", "검증상태"]
    verified, unverified = [], []
    stats = {0: 0, 1: 0, 2: 0, 3: 0}
    by_region = {}
    total = len(rows)
    print(f"검증 대상: {total}건 (~{total*0.15/60:.1f}분 예상)")

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(rows):
            name = str(row[ni]).strip() if row[ni] else ""
            kaddr = str(row[ai]).strip() if ai >= 0 and row[ai] else ""
            ind = str(row[ii]).strip() if ii >= 0 and row[ii] else ""
            file_r = str(row[ri]).strip() if ri >= 0 and row[ri] else "양주"
            step, m = await verify(client, name, kaddr, file_r, ind)
            stats[step] += 1
            base = list(row)
            if m:
                verified.append(base + [m["address"], m["link"], m["region"], f"step{step}", "verified"])
                by_region[m["region"]] = by_region.get(m["region"], 0) + 1
            else:
                unverified.append(base + ["", "", "", "", "unverified"])
            if (i + 1) % 200 == 0 or i == total - 1:
                print(f"  [{i+1}/{total}] s1={stats[1]} s2={stats[2]} s3={stats[3]} fail={stats[0]}")
            await asyncio.sleep(0.1)

    for path, data in [(LEAD_DB / f"북부수도권_검증_{TS}.xlsx", verified),
                        (LEAD_DB / f"북부수도권_unverified_{TS}.xlsx", unverified)]:
        w = openpyxl.Workbook(); s = w.active; s.append(out_headers)
        for r in data: s.append(r)
        w.save(str(path))

    pct = len(verified) * 100 // max(total, 1)
    print(f"\n=== 완료 ===\nverified: {len(verified)} ({pct}%)")
    print(f"unverified: {len(unverified)}")
    print(f"step: 1={stats[1]} 2={stats[2]} 3={stats[3]} fail={stats[0]}")
    print(f"지역별 verified:")
    for r in ["양주", "포천", "의정부", "남양주", "동두천", "가평"]:
        print(f"  {r}: {by_region.get(r,0)}건")


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(main(lim))
