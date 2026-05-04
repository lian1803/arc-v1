"""북부수도권 통합 file v2 — 이미 ✅+URL 박힌 row 는 string check, 미검증만 API."""
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
TARGETS = [("남양주", "남양주시"), ("양주", "양주시"), ("포천", "포천시"),
           ("의정부", "의정부시"), ("동두천", "동두천시"), ("가평", "가평군")]


def find_col(headers, *keys):
    for i, h in enumerate(headers):
        if any(k in str(h) for k in keys): return i
    return -1


def matched_region(addr):
    if not addr: return None
    s = str(addr)
    for r, sub in TARGETS:
        if sub in s:
            if r == "양주" and "남양주시" in s: continue
            return r
    return None


async def search(client, q):
    try:
        r = await client.get(
            "https://openapi.naver.com/v1/search/local.json",
            headers={"X-Naver-Client-Id": NID, "X-Naver-Client-Secret": NSEC},
            params={"query": q, "display": 5}, timeout=8.0)
        if r.status_code == 429:
            await asyncio.sleep(3.0); return None
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


async def api_verify(client, name, kakao_addr, file_region, industry):
    if not name: return 0, None
    qs = [(1, f"{name} {file_region}")]
    kr = matched_region(kakao_addr or "")
    if kr and kr != file_region: qs.append((2, f"{name} {kr}"))
    if industry: qs.append((3, f"{name} {industry}"))
    for step, q in qs:
        m = find_match(await search(client, q))
        if m: return step, m
    return 0, None


async def main(limit=None):
    wb = openpyxl.load_workbook(str(INPUT), read_only=True, data_only=True)
    rows_all = list(wb.active.iter_rows(values_only=True)); wb.close()
    headers = [str(h).strip() if h else "" for h in rows_all[0]]
    rows = rows_all[1:limit+1] if limit else rows_all[1:]
    ni = find_col(headers, "업체명")
    kai = find_col(headers, "수집주소")
    nai = find_col(headers, "네이버지도주소")
    npi = find_col(headers, "네이버플레이스")
    vi = find_col(headers, "검증")
    ii = find_col(headers, "업종")
    ri = find_col(headers, "지역")
    out_h = list(headers) + ["네이버주소_v", "네이버URL_v", "매칭지역", "매칭방법", "검증상태"]
    verified, unverified = [], []
    by_r = {r: 0 for r, _ in TARGETS}
    pre, api_n, api_p = 0, 0, 0
    print(f"INPUT: {INPUT.name}\n검증 대상: {len(rows)}건")

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(rows):
            name = str(row[ni]).strip() if row[ni] else ""
            kaddr = str(row[kai]).strip() if kai >= 0 and row[kai] else ""
            naddr = str(row[nai]).strip() if nai >= 0 and row[nai] else ""
            nurl = str(row[npi]).strip() if npi >= 0 and row[npi] else ""
            ind = str(row[ii]).strip() if ii >= 0 and row[ii] else ""
            file_r = str(row[ri]).strip() if ri >= 0 and row[ri] else "양주"
            vmark = str(row[vi]).strip() if vi >= 0 and row[vi] else ""
            base = list(row)
            if "✅" in vmark and nurl and nurl.startswith("http"):
                tr = matched_region(naddr or kaddr)
                if tr:
                    pre += 1; by_r[tr] += 1
                    verified.append(base + [naddr or kaddr, nurl, tr, "preverified", "verified"])
                    continue
            api_n += 1
            step, m = await api_verify(client, name, kaddr, file_r, ind)
            if m:
                api_p += 1; by_r[m["region"]] += 1
                verified.append(base + [m["address"], m["link"], m["region"], f"step{step}", "verified"])
            else:
                unverified.append(base + ["", "", "", "", "unverified"])
            if (i+1) % 200 == 0 or i == len(rows)-1:
                print(f"  [{i+1}/{len(rows)}] pre={pre} api={api_n} pass={api_p} ver={len(verified)}")
            if api_n: await asyncio.sleep(0.1)

    for path, data in [(LEAD_DB / f"북부수도권_검증v2_{TS}.xlsx", verified),
                        (LEAD_DB / f"북부수도권_unverifiedv2_{TS}.xlsx", unverified)]:
        w = openpyxl.Workbook(); s = w.active; s.append(out_h)
        for r in data: s.append(r)
        w.save(str(path))

    print(f"\n=== 완료 ===\nverified: {len(verified)} (pre={pre}, api_pass={api_p})")
    print(f"unverified: {len(unverified)}\nAPI call: {api_n}")
    print(f"지역별 verified:")
    for r, _ in TARGETS:
        print(f"  {r}: {by_r[r]}건")


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(main(lim))
