"""사람인 — 양주 채용공고 → 사장님 010 추출"""
import asyncio
import re
import time
import httpx
from ._common import UA, REGION, PHONE_010, normalize_phone, dedup_add


async def test() -> dict:
    print("[사람인] 양주 채용 → 010")
    t0 = time.time()
    found = []
    errors = []

    try:
        async with httpx.AsyncClient(headers={"User-Agent": UA}, timeout=20,
                                     follow_redirects=True) as c:
            params = {
                "searchType": "search",
                "searchword": REGION,
                "recruitPage": 1,
                "recruitPageCount": 40,
                "recruitSort": "reg_dt",
            }
            r = await c.get("https://www.saramin.co.kr/zf_user/search/recruit",
                            params=params)
            r.raise_for_status()
            html = r.text

            # 채용공고 ID 추출
            rec_ids = list(set(re.findall(r'rec_idx=(\d+)', html)))[:15]
            print(f"  공고 {len(rec_ids)}개 발견")

            # 검색 list page 자체 010 패턴 (드물게 노출)
            for m in PHONE_010.finditer(html):
                dedup_add(found, normalize_phone(m.group(0)), "list_page",
                          source_part="search")

            # 각 공고 상세 fetch
            for rid in rec_ids:
                try:
                    detail_url = f"https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx={rid}"
                    rd = await c.get(detail_url)
                    if rd.status_code == 200:
                        # 회사명 추출
                        name_m = re.search(r'<title>([^<]+)</title>', rd.text)
                        name = (name_m.group(1).split("|")[0].strip()[:50]
                                if name_m else f"공고{rid}")
                        for m in PHONE_010.finditer(rd.text):
                            dedup_add(found, normalize_phone(m.group(0)), name,
                                      rec_id=rid)
                    await asyncio.sleep(1.0)
                except Exception as e:
                    errors.append(f"rec_id={rid}: {e}")
    except Exception as e:
        errors.append(f"top: {e}")

    return {
        "source": "saramin",
        "region": REGION,
        "phone_count": len(found),
        "elapsed_sec": round(time.time() - t0, 1),
        "samples": found[:5],
        "errors": errors[:3],
    }
