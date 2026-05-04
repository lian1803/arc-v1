"""알바천국 — 양주 알바공고 → 사장님 010 (시급제는 사장님 직접 연락 빈번)"""
import asyncio
import re
import time
import httpx
from ._common import UA, REGION, PHONE_010, normalize_phone, dedup_add


async def test() -> dict:
    print("[알바천국] 양주 알바 → 010")
    t0 = time.time()
    found = []
    errors = []

    try:
        async with httpx.AsyncClient(headers={"User-Agent": UA}, timeout=20,
                                     follow_redirects=True) as c:
            r = await c.get("https://www.alba.co.kr/search/Search.asp",
                            params={"strKwd": REGION})
            html = r.text

            # 공고 ID 패턴 (GI_AdNo 또는 /job-detail/)
            ad_ids = list(set(re.findall(r'GI_AdNo=([A-Z0-9]+)', html)))[:10]
            if not ad_ids:
                ad_ids = list(set(re.findall(r'/job-detail/[^/]+/([A-Z0-9]+)', html)))[:10]
            print(f"  공고 {len(ad_ids)}개")

            # list page 010
            for m in PHONE_010.finditer(html):
                dedup_add(found, normalize_phone(m.group(0)), "list_page",
                          source_part="search")

            for ad in ad_ids[:5]:
                try:
                    # 알바천국 공고 상세
                    detail = f"https://www.alba.co.kr/job/Board.asp?GI_AdNo={ad}"
                    rd = await c.get(detail)
                    if rd.status_code == 200:
                        for m in PHONE_010.finditer(rd.text):
                            dedup_add(found, normalize_phone(m.group(0)),
                                      ad, ad_id=ad)
                    await asyncio.sleep(1.0)
                except Exception as e:
                    errors.append(f"ad={ad}: {e}")

            # 알바천국 모바일 검색도 시도 (mobile 은 phone field 노출 가능성 ↑)
            try:
                rm = await c.get("https://m.alba.co.kr/search/Search.asp",
                                 params={"strKwd": REGION})
                if rm.status_code == 200:
                    for m in PHONE_010.finditer(rm.text):
                        dedup_add(found, normalize_phone(m.group(0)),
                                  "mobile_list", source_part="m_search")
            except Exception as e:
                errors.append(f"mobile: {e}")
    except Exception as e:
        errors.append(f"top: {e}")

    return {
        "source": "alba",
        "region": REGION,
        "phone_count": len(found),
        "elapsed_sec": round(time.time() - t0, 1),
        "samples": found[:5],
        "errors": errors[:3],
    }
