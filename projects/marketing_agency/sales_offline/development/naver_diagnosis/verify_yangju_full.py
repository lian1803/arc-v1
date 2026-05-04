"""양주 통합 db 전체 검증 — 3-step Naver Local API fallback.
1차: "이름 양주" / 2차: "이름 {동}" / 3차: "이름 {업종}" → 경기도 양주시 매칭."""
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
INPUT = LEAD_DB / "양주_통합_20260428_141556.xlsx"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
PREFIX = "경기도 양주시"
DONG_RE = re.compile(r"([가-힣]{2,5}(?:동|읍|면))")


def find_col(headers, *keys):
    for i, h in enumerate(headers):
        if any(k in h for k in keys):
            return i
    return -1


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


def match(items):
    if not items: return None
    for it in items:
        addr = (it.get("address", "") + " " + it.get("roadAddress", "")).strip()
        if PREFIX in addr:
            return {"address": addr, "link": it.get("link", ""),
                    "name": re.sub(r"<[^>]+>", "", it.get("title", ""))}
    return None


async def verify(client, name, kakao_addr, industry):
    if not name: return 0, None
    queries = [(1, f"{name} 양주")]
    dm = DONG_RE.search(kakao_addr or "")
    if dm: queries.append((2, f"{name} {dm.group(1)}"))
    if industry: queries.append((3, f"{name} {industry}"))
    for step, q in queries:
        m = match(await search(client, q))
        if m: return step, m
    return 0, None


async def main(limit=None):
    wb = openpyxl.load_workbook(str(INPUT), read_only=True, data_only=True)
    rows_all = list(wb.active.iter_rows(values_only=True)); wb.close()
    headers = [str(h).strip() if h else "" for h in rows_all[0]]
    rows = rows_all[1:limit+1] if limit else rows_all[1:]

    ni = find_col(headers, "업체명", "상호")
    ai = find_col(headers, "주소")
    ii = find_col(headers, "업종")
    out_headers = list(headers) + ["네이버주소", "네이버URL", "매칭방법", "검증상태"]
    verified, unverified = [], []
    stats = {0: 0, 1: 0, 2: 0, 3: 0}
    total = len(rows)
    print(f"검증 대상: {total}건")

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(rows):
            name = str(row[ni]).strip() if row[ni] else ""
            kaddr = str(row[ai]).strip() if ai >= 0 and row[ai] else ""
            ind = str(row[ii]).strip() if ii >= 0 and row[ii] else ""
            step, m = await verify(client, name, kaddr, ind)
            stats[step] += 1
            base = list(row)
            if m:
                verified.append(base + [m["address"], m["link"], f"step{step}", "verified"])
            else:
                unverified.append(base + ["", "", "", "unverified"])
            if (i + 1) % 100 == 0 or i == total - 1:
                print(f"  [{i+1}/{total}] s1={stats[1]} s2={stats[2]} s3={stats[3]} fail={stats[0]}")
            await asyncio.sleep(0.1)

    for path, data in [(LEAD_DB / f"양주_검증_{TS}.xlsx", verified),
                        (LEAD_DB / f"양주_unverified_{TS}.xlsx", unverified)]:
        w = openpyxl.Workbook(); s = w.active; s.append(out_headers)
        for r in data: s.append(r)
        w.save(str(path))

    pct = len(verified) * 100 // max(total, 1)
    print(f"\n=== 완료 ===\nverified: {len(verified)} ({pct}%)")
    print(f"unverified: {len(unverified)}")
    print(f"step: 1={stats[1]} 2={stats[2]} 3={stats[3]} fail={stats[0]}")


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(main(lim))
