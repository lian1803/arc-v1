"""잡코리아 — 양주 채용공고 → 010 추출"""
import asyncio
import re
import time
import httpx
from ._common import UA, REGION, PHONE_010, normalize_phone, dedup_add


async def test() -> dict:
    print("[잡코리아] 양주 채용 → 010")
    t0 = time.time()
    found = []
    errors = []

    try:
        async with httpx.AsyncClient(headers={"User-Agent": UA}, timeout=20,
                                     follow_redirects=True) as c:
            r = await c.get("https://www.jobkorea.co.kr/Search/",
                            params={"stext": REGION})
            html = r.text

            # 공고 GI_No 추출
            gi_nos = list(set(re.findall(r'GI_No=(\d+)', html)))[:10]
            if not gi_nos:
                gi_nos = list(set(re.findall(r'/Recruit/GI_Read/(\d+)', html)))[:10]
            print(f"  공고 {len(gi_nos)}개")

            # list page 010
            for m in PHONE_010.finditer(html):
                dedup_add(found, normalize_phone(m.group(0)), "list_page",
                          source_part="search")

            for gi in gi_nos:
                try:
                    detail = f"https://www.jobkorea.co.kr/Recruit/GI_Read/{gi}"
                    rd = await c.get(detail)
                    if rd.status_code == 200:
                        name_m = re.search(r'<title>([^<]+)</title>', rd.text)
                        name = (name_m.group(1).split("|")[0].strip()[:50]
                                if name_m else f"GI{gi}")
                        for m in PHONE_010.finditer(rd.text):
                            dedup_add(found, normalize_phone(m.group(0)), name,
                                      gi_no=gi)
                    await asyncio.sleep(1.0)
                except Exception as e:
                    errors.append(f"gi={gi}: {e}")
    except Exception as e:
        errors.append(f"top: {e}")

    return {
        "source": "jobkorea",
        "region": REGION,
        "phone_count": len(found),
        "elapsed_sec": round(time.time() - t0, 1),
        "samples": found[:5],
        "errors": errors[:3],
    }
