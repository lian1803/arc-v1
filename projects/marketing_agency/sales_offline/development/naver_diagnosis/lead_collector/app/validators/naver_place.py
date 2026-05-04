"""네이버플레이스에서 업체 실존 검증"""
import asyncio
import logging
import re
from typing import Callable, Optional
from urllib.parse import quote

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from app.config import MOBILE_UA

logger = logging.getLogger(__name__)

# 네이버플레이스 PID 추출 패턴
NAVER_PLACE_PID_PATTERN = re.compile(r'/place/(\d{6,})')


async def validate_businesses(
    businesses: list[dict],
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> list[dict]:
    """
    네이버플레이스 모바일 검색으로 업체 실존 검증.

    각 업체에 verify_status, naver_place_url 추가:
    - "확인됨": 네이버플레이스에서 찾아서 PID 매핑됨
    - "미확인": 검색됐지만 정확히 매칭 안됨 또는 결과 없음
    - "폐업의심": "폐업" 텍스트가 검색 결과에 나옴
    """
    if not businesses:
        return businesses

    total = len(businesses)
    results = list(businesses)  # 원본 수정 방지용 복사

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=MOBILE_UA,
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            # 탭 2개로 병렬 처리 (네이버 차단 방지를 위해 소수 유지)
            pages = [await context.new_page() for _ in range(2)]

            for p in pages:
                await p.route(
                    "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}",
                    lambda route: route.abort(),
                )

            async def verify_one(idx: int, record: dict, page) -> dict:
                name = record.get("name", "").strip()
                address = record.get("raw_address", "").strip()

                if not name:
                    record["verify_status"] = "미확인"
                    record["naver_place_url"] = record.get("naver_place_url", "")
                    return record

                # 업체명 + 주소 앞부분으로 검색 정확도 향상
                search_query = name
                if address:
                    # 주소에서 시/구/동 단위만 추출
                    addr_short = re.sub(r'\s+', ' ', address).split()
                    if len(addr_short) >= 2:
                        search_query = f"{name} {addr_short[0]} {addr_short[1]}"

                try:
                    encoded = quote(search_query)
                    url = f"https://m.search.naver.com/search.naver?query={encoded}&where=m_local"
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_load_state("networkidle", timeout=20000)

                    html = await page.content()

                    # 폐업 여부 먼저 확인
                    if "폐업" in html or "영업종료" in html or "permanently closed" in html.lower():
                        # 업체명 주변에서 폐업 텍스트 확인 (단순 포함이 아닌 연관성 확인)
                        name_escaped = re.escape(name[:5])  # 업체명 앞 5자로 근접 확인
                        if re.search(rf'{name_escaped}.{{0,100}}폐업|폐업.{{0,100}}{name_escaped}', html):
                            record["verify_status"] = "폐업의심"
                            record["naver_place_url"] = record.get("naver_place_url", "")
                            logger.debug("naver_place: 폐업의심 — %s", name)
                            return record

                    # 네이버플레이스 PID 추출
                    pid_match = NAVER_PLACE_PID_PATTERN.search(html)
                    if pid_match:
                        pid = pid_match.group(1)
                        place_url = f"https://map.naver.com/p/entry/place/{pid}"

                        # 검색 결과에 업체명이 포함되어 있는지 확인
                        if name[:3] in html or _name_in_results(name, html):
                            record["verify_status"] = "확인됨"
                            record["naver_place_url"] = place_url
                            logger.debug("naver_place: 확인됨 — %s → %s", name, place_url)
                        else:
                            record["verify_status"] = "미확인"
                            record["naver_place_url"] = record.get("naver_place_url", "")
                    else:
                        record["verify_status"] = "미확인"
                        record["naver_place_url"] = record.get("naver_place_url", "")

                except PWTimeout:
                    logger.warning("naver_place: 타임아웃 — %s", name)
                    record["verify_status"] = "미확인"
                    record["naver_place_url"] = record.get("naver_place_url", "")
                except Exception as e:
                    logger.error("naver_place: 검증 오류 (%s) — %s", name, e)
                    record["verify_status"] = "미확인"
                    record["naver_place_url"] = record.get("naver_place_url", "")

                return record

            # 2개 탭으로 교차 처리
            for i in range(0, total, 2):
                batch = results[i:i + 2]
                tasks = [
                    verify_one(i + j, record, pages[j % 2])
                    for j, record in enumerate(batch)
                ]
                verified_batch = await asyncio.gather(*tasks)
                for j, verified in enumerate(verified_batch):
                    results[i + j] = verified

                done = min(i + 2, total)
                if progress_callback:
                    try:
                        progress_callback(results[i].get("name", ""), done, total)
                    except Exception:
                        pass

                # 네이버 요청 간격 유지
                await asyncio.sleep(0.8)

            for p in pages:
                await p.close()
            await browser.close()

    except Exception as e:
        logger.error("naver_place: 검증기 전체 오류 — %s", e)
        # 오류 시 모든 레코드 "미확인" 처리
        for record in results:
            if "verify_status" not in record:
                record["verify_status"] = "미확인"
            if "naver_place_url" not in record:
                record["naver_place_url"] = ""

    confirmed = sum(1 for r in results if r.get("verify_status") == "확인됨")
    closed = sum(1 for r in results if r.get("verify_status") == "폐업의심")
    logger.info(
        "naver_place: 검증 완료 — 전체 %d건 / 확인됨 %d건 / 폐업의심 %d건",
        total, confirmed, closed,
    )
    return results


def _name_in_results(name: str, html: str) -> bool:
    """업체명의 핵심 부분이 HTML에 포함되어 있는지 확인"""
    # 업체명에서 의미 있는 부분 추출 (특수문자 제거, 앞 4자)
    core = re.sub(r'[^\w가-힣]', '', name)
    if len(core) >= 4:
        return core[:4] in html
    return core in html
