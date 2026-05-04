"""숨고 — 양주 서비스 제공자 (1인 사업자) 010 추출"""
import asyncio
import re
import time
import httpx
from ._common import UA, REGION, PHONE_010, normalize_phone, dedup_add


async def test() -> dict:
    print("[숨고] 양주 서비스 → 010")
    t0 = time.time()
    found = []
    errors = []

    try:
        async with httpx.AsyncClient(headers={"User-Agent": UA}, timeout=20,
                                     follow_redirects=True) as c:
            # 숨고는 고수 페이지에 phone 직접 노출 안 함 (앱 내 채팅 유도)
            # → 검색 결과 페이지 본문의 010 패턴만 시도
            for keyword in [f"{REGION} 청소", f"{REGION} 미용", f"{REGION} 학원",
                            f"{REGION} 인테리어", f"{REGION} 이사"]:
                try:
                    r = await c.get(f"https://soomgo.com/search",
                                    params={"q": keyword})
                    if r.status_code == 200:
                        for m in PHONE_010.finditer(r.text):
                            dedup_add(found, normalize_phone(m.group(0)),
                                      keyword, source_part="search")
                except Exception as e:
                    errors.append(f"q={keyword}: {e}")
                await asyncio.sleep(1.0)
    except Exception as e:
        errors.append(f"top: {e}")

    return {
        "source": "soomgo",
        "region": REGION,
        "phone_count": len(found),
        "elapsed_sec": round(time.time() - t0, 1),
        "samples": found[:5],
        "errors": errors[:3],
    }
