"""카카오맵 REST API + Playwright 스크래핑"""
import asyncio
import logging
import os
import re
from urllib.parse import quote

import httpx
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from app.collectors.base_collector import BaseCollector
from app.config import DESKTOP_UA, DELAY_KAKAO

logger = logging.getLogger(__name__)

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY", "")
KAKAO_KEYWORD_API = "https://dapi.kakao.com/v2/local/search/keyword.json"
KAKAO_MAP_URL = "https://map.kakao.com"


def _make_record(
    name: str = "",
    phone: str = "",
    address: str = "",
    insta_url: str = "",
    naver_place_url: str = "",
    daangn_url: str = "",
    category: str = "",
    kakao_place_url: str = "",
) -> dict:
    return {
        "name": name,
        "phone": phone,
        "address": address,
        "insta_url": insta_url,
        "naver_place_url": naver_place_url,
        "daangn_url": daangn_url,
        "category": category,
        "source": "카카오맵",
        "kakao_place_url": kakao_place_url,
    }


class KakaoMapsCollector(BaseCollector):
    platform_name = "카카오맵"

    async def collect(self, region: str, keyword: str, limit: int = 100) -> list[dict]:
        results: list[dict] = []
        try:
            if KAKAO_REST_API_KEY:
                api_items = await self._fetch_api(region, keyword, limit)
                results.extend(api_items)
                logger.info("[카카오API] %s %s → %d건", region, keyword, len(api_items))
            else:
                logger.info("[카카오] API 키 없음, Playwright 폴백 시작")
                pw_items = await self._fetch_playwright(region, keyword, limit)
                results.extend(pw_items)
        except Exception as exc:
            logger.error("[카카오맵] collect 오류: %s", exc, exc_info=True)
        return results[:limit]

    # ------------------------------------------------------------------
    # 1) 카카오맵 REST API
    # ------------------------------------------------------------------
    async def _fetch_api(self, region: str, keyword: str, limit: int) -> list[dict]:
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        items: list[dict] = []
        page = 1

        async with httpx.AsyncClient(timeout=15) as client:
            while len(items) < limit:
                params = {
                    "query": f"{region} {keyword}",
                    "size": 15,
                    "page": page,
                }
                try:
                    resp = await client.get(KAKAO_KEYWORD_API, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    logger.warning("[카카오API] 요청 실패: %s", exc)
                    break

                docs = data.get("documents", [])
                if not docs:
                    break

                for doc in docs:
                    name = doc.get("place_name", "").strip()
                    if not name or self.is_franchise(name):
                        continue

                    phone_raw = doc.get("phone", "")
                    phone = self.normalize_phone(phone_raw) if phone_raw else ""
                    address = doc.get("road_address_name") or doc.get("address_name", "")

                    # region filter — Seoul/타지역 섞임 차단
                    if not self.is_in_region(address, region):
                        continue

                    place_url = doc.get("place_url", "")
                    category_raw = doc.get("category_name", "")

                    items.append(_make_record(
                        name=name,
                        phone=phone,
                        address=address,
                        category=keyword,
                        kakao_place_url=place_url,
                    ))

                meta = data.get("meta", {})
                if meta.get("is_end", True):
                    break
                page += 1
                await asyncio.sleep(DELAY_KAKAO)

        return items

    # ------------------------------------------------------------------
    # 2) Playwright 직접 스크래핑
    # ------------------------------------------------------------------
    async def _fetch_playwright(self, region: str, keyword: str, limit: int) -> list[dict]:
        items: list[dict] = []
        query = f"{region} {keyword}"
        encoded = quote(query)
        search_url = f"{KAKAO_MAP_URL}/?q={encoded}"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=DESKTOP_UA)
            page = await context.new_page()

            try:
                await page.goto(search_url, timeout=25000)
                await page.wait_for_load_state("networkidle", timeout=20000)

                # 검색 결과 로딩 대기
                try:
                    await page.wait_for_selector(
                        ".PlaceItem, .info_title, .item_name",
                        timeout=10000,
                    )
                except PWTimeout:
                    logger.warning("[카카오PW] 결과 셀렉터 없음: %s", query)

                html = await page.content()
                page_num = 1

                while len(items) < limit:
                    place_items = await page.query_selector_all(
                        ".PlaceItem, li[data-id], .link_name"
                    )

                    if not place_items:
                        # 대체 파싱: HTML에서 직접 추출
                        fallback = await self._parse_html_fallback(html, keyword)
                        items.extend(fallback)
                        break

                    for el in place_items:
                        if len(items) >= limit:
                            break
                        record = await self._extract_place_item(el, keyword)
                        if record:
                            items.append(record)

                    # 다음 페이지 존재 확인
                    next_btn = await page.query_selector(
                        ".btn_page_next:not(.disabled), a[data-page-no]"
                    )
                    if not next_btn or page_num >= 20:
                        break

                    await next_btn.click()
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    page_num += 1
                    await asyncio.sleep(DELAY_KAKAO)

            except PWTimeout:
                logger.warning("[카카오PW] 타임아웃: %s", query)
            except Exception as exc:
                logger.error("[카카오PW] 오류: %s", exc, exc_info=True)
            finally:
                await browser.close()

        return items

    async def _extract_place_item(self, el, category: str) -> dict | None:
        try:
            # 업체명
            name = ""
            for sel in [".info_title", ".link_name", ".place_title", "strong"]:
                name_el = await el.query_selector(sel)
                if name_el:
                    name = (await name_el.inner_text()).strip()
                    break

            if not name or self.is_franchise(name):
                return None

            # 전화번호
            phone = ""
            for sel in [".contact-area", ".phone", ".tel", "[class*='phone']", "[class*='tel']"]:
                phone_el = await el.query_selector(sel)
                if phone_el:
                    phone_text = (await phone_el.inner_text()).strip()
                    phone_raw = self.extract_phone(phone_text)
                    if phone_raw:
                        phone = self.normalize_phone(phone_raw)
                        break

            # 주소
            address = ""
            for sel in [".addr", ".address", ".lot_number_address", "[class*='addr']"]:
                addr_el = await el.query_selector(sel)
                if addr_el:
                    address = (await addr_el.inner_text()).strip()
                    break

            # 카카오플레이스 URL
            kakao_place_url = ""
            link_el = await el.query_selector("a[href*='kakaomap'], a[href*='place']")
            if link_el:
                kakao_place_url = await link_el.get_attribute("href") or ""

            return _make_record(
                name=name,
                phone=phone,
                address=address,
                category=category,
                kakao_place_url=kakao_place_url,
            )

        except Exception as exc:
            logger.debug("[카카오] 아이템 파싱 오류: %s", exc)
            return None

    async def _parse_html_fallback(self, html: str, category: str) -> list[dict]:
        """HTML 직접 파싱 폴백 — 셀렉터가 없을 때"""
        items: list[dict] = []

        # 업체명 패턴: data-place-name 또는 place_name JSON 키
        name_pattern = re.compile(
            r'(?:data-place-name|"place_name")\s*[=:]\s*"([^"]{2,50})"'
        )
        phone_blocks = re.compile(
            r'"([^"]*)"[^"]*"(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})"'
        )

        names = [m.group(1) for m in name_pattern.finditer(html)]
        for name in names:
            name = name.strip()
            if not name or self.is_franchise(name):
                continue
            items.append(_make_record(name=name, category=category))

        # 전화번호 매칭 시도 (순서 기반)
        phones = [self.normalize_phone(m.group(2)) for m in phone_blocks.finditer(html)]
        for i, phone in enumerate(phones):
            if i < len(items):
                items[i]["phone"] = phone

        return items
