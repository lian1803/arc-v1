"""Bing 검색 결과 파싱 — 로컬팩 + 웹 결과에서 전화번호/인스타/당근 URL"""
import asyncio
import logging
import re
from urllib.parse import quote

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from app.collectors.base_collector import BaseCollector
from app.config import DESKTOP_UA

logger = logging.getLogger(__name__)

DAANGN_PATTERN = re.compile(
    r'https?://(?:www\.)?daangn\.com/(?:kr/biz/|articles/|fleamarket/)[^\s"\'<>]+'
)
NAVER_PLACE_PATTERN = re.compile(r'https?://(?:m\.)?(?:place\.naver\.com|map\.naver\.com/p/entry/place)/[^\s"\'<>]+')


class BingCollector(BaseCollector):
    platform_name = "빙"

    async def collect(self, region: str, keyword: str, limit: int = 100) -> list[dict]:
        results: list[dict] = []
        seen_names: set[str] = set()
        query = f"{region} {keyword}"

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=DESKTOP_UA,
                    viewport={"width": 1280, "height": 900},
                    locale="ko-KR",
                )
                page = await context.new_page()
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}",
                    lambda route: route.abort(),
                )

                bing_page = 1
                while len(results) < limit and bing_page <= 5:
                    first = (bing_page - 1) * 10 + 1
                    url = f"https://www.bing.com/search?q={quote(query)}&setlang=ko&first={first}"

                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                        await page.wait_for_timeout(1000)
                    except PWTimeout:
                        logger.warning("[빙] 타임아웃: %s p%d", query, bing_page)
                        break

                    html = await page.content()
                    recs = self._parse_results(html, keyword, region)
                    for r in recs:
                        if r["name"] and r["name"] not in seen_names:
                            seen_names.add(r["name"])
                            results.append(r)

                    bing_page += 1
                    await asyncio.sleep(1.0)

                await browser.close()

        except Exception as e:
            logger.error("[빙] 수집기 오류: %s", e)

        logger.info("[빙] %s %s → %d건", region, keyword, len(results))
        return results[:limit]

    def _parse_results(self, html: str, keyword: str, region: str) -> list[dict]:
        records: list[dict] = []

        # 빙 로컬팩: <div class="b_scard"> 또는 <li class="b_algo">
        blocks = re.split(r'<(?:div[^>]+class="[^"]*b_scard[^"]*"|li[^>]+class="[^"]*b_algo[^"]*")', html)

        for block in blocks[1:]:
            name = ""

            # 업체명: <div class="b_entityTitle"> 또는 <h2>
            name_m = re.search(r'<(?:div[^>]+class="[^"]*b_entityTitle[^"]*"|h2)[^>]*>([^<]{2,50})</', block)
            if name_m:
                name = re.sub(r'<[^>]+>', '', name_m.group(1)).strip()

            if not name or self.is_franchise(name):
                continue

            phone_raw = self.extract_phone(block)
            phone = self.normalize_phone(phone_raw) if phone_raw else ""

            insta_url = self.extract_instagram(block)
            daangn_m = DAANGN_PATTERN.search(block)
            daangn_url = daangn_m.group(0) if daangn_m else ""
            naver_m = NAVER_PLACE_PATTERN.search(block)
            naver_place_url = naver_m.group(0) if naver_m else ""

            if not phone and not insta_url and not daangn_url:
                continue

            records.append({
                "name": name,
                "phone": phone,
                "phone_status": "확인" if phone else "번호미확인",
                "insta_url": insta_url,
                "naver_place_url": naver_place_url,
                "daangn_url": daangn_url,
                "raw_address": region,
                "category": keyword,
                "source": self.platform_name,
                "sources": self.platform_name,
                "verify_status": "미확인",
            })

        return records
