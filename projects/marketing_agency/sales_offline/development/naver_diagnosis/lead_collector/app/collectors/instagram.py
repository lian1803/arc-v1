"""인스타그램 계정 수집기 — 네이버/구글 검색 경유"""
import asyncio
import logging
import re
from urllib.parse import quote

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from app.collectors.base_collector import BaseCollector, IG_PATTERN, IG_EXCLUDE
from app.config import MOBILE_UA, DESKTOP_UA, DELAY_INSTA

logger = logging.getLogger(__name__)

# 네이버 블로그/카페에서 업체명+인스타URL 쌍 추출용 패턴
BIZ_NAME_PATTERN = re.compile(r'<[^>]+class="[^"]*title[^"]*"[^>]*>([^<]{2,30})</[^>]+>')


class InstagramCollector(BaseCollector):
    platform_name = "인스타그램"

    async def collect(self, region: str, keyword: str, limit: int = 30) -> list[dict]:
        """
        네이버 블로그/카페 검색에서 region+keyword 관련 업체명과 인스타 URL 쌍 추출.
        예: "의정부시 카페 인스타그램 맛집" 검색 결과에서 업체명+인스타URL 파싱.
        """
        results: list[dict] = []
        seen_accounts: set[str] = set()

        queries = [
            f"{region} {keyword} 인스타그램",
            f"{region} {keyword} 인스타",
            f"{region} {keyword} instagram",
        ]

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=MOBILE_UA,
                    viewport={"width": 390, "height": 844},
                    locale="ko-KR",
                )
                page = await context.new_page()

                await page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}",
                    lambda route: route.abort(),
                )

                for query in queries:
                    if len(results) >= limit:
                        break

                    # 방법 1: 네이버 블로그/카페 검색
                    naver_results = await self._search_naver(page, query, region, keyword, limit - len(results))
                    for r in naver_results:
                        acct = r.get("insta_url", "")
                        if acct and acct not in seen_accounts:
                            seen_accounts.add(acct)
                            results.append(r)

                    if len(results) < limit // 2:
                        # 방법 2: 구글 검색 폴백
                        google_results = await self._search_google(page, query, region, keyword, limit - len(results))
                        for r in google_results:
                            acct = r.get("insta_url", "")
                            if acct and acct not in seen_accounts:
                                seen_accounts.add(acct)
                                results.append(r)

                await browser.close()

        except Exception as e:
            logger.error("InstagramCollector: 전체 오류 — %s", e)

        logger.info("InstagramCollector: 최종 %d건 수집 완료", len(results))
        return results

    async def _search_naver(self, page, query: str, region: str, keyword: str, limit: int) -> list[dict]:
        """네이버 웹 검색에서 인스타그램 URL 추출"""
        results: list[dict] = []
        try:
            encoded = quote(query)
            url = f"https://search.naver.com/search.naver?query={encoded}&where=web"
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(DELAY_INSTA * 1000)

            html = await page.content()
            records = self._extract_insta_pairs_from_html(html, region, keyword)
            results.extend(records[:limit])

            # 블로그 탭도 시도
            blog_url = f"https://search.naver.com/search.naver?query={encoded}&where=blog"
            await page.goto(blog_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(DELAY_INSTA * 1000)
            html = await page.content()
            blog_records = self._extract_insta_pairs_from_html(html, region, keyword)
            results.extend(blog_records[:max(0, limit - len(results))])

        except PWTimeout:
            logger.warning("InstagramCollector: 네이버 검색 타임아웃 — %s", query)
        except Exception as e:
            logger.error("InstagramCollector: 네이버 검색 오류 — %s", e)

        return results

    async def _search_google(self, page, query: str, region: str, keyword: str, limit: int) -> list[dict]:
        """구글 검색에서 인스타그램 URL 추출 (폴백)"""
        results: list[dict] = []
        try:
            encoded = quote(f"{query} site:instagram.com OR instagram.com/{region}")
            url = f"https://www.google.com/search?q={encoded}&hl=ko&num=20"
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(DELAY_INSTA * 1000)

            html = await page.content()
            records = self._extract_insta_pairs_from_html(html, region, keyword)
            results.extend(records[:limit])

        except PWTimeout:
            logger.warning("InstagramCollector: 구글 검색 타임아웃 — %s", query)
        except Exception as e:
            logger.error("InstagramCollector: 구글 검색 오류 — %s", e)

        return results

    def _extract_insta_pairs_from_html(self, html: str, region: str, keyword: str) -> list[dict]:
        """HTML에서 업체명+인스타URL 쌍 추출"""
        records: list[dict] = []
        seen: set[str] = set()

        # 텍스트 블록 단위로 분리해서 근처 업체명과 인스타URL 연결
        # 구조: 검색 결과 각 항목에서 제목 근방의 instagram.com URL 추출
        blocks = re.split(r'<(?:li|div|article)[^>]*>', html)

        for block in blocks:
            insta_url = self.extract_instagram(block)
            if not insta_url:
                continue
            if insta_url in seen:
                continue
            seen.add(insta_url)

            # 블록에서 업체명으로 쓸 만한 텍스트 추출
            name = self._extract_name_from_block(block, region, keyword)

            records.append({
                "name": name,
                "phone": "",
                "phone_status": "번호미확인",
                "insta_url": insta_url,
                "naver_place_url": "",
                "daangn_url": "",
                "raw_address": region,
                "category": keyword,
                "source": self.platform_name,
                "sources": self.platform_name,
                "verify_status": "미확인",
            })

        return records

    def _extract_name_from_block(self, block: str, region: str, keyword: str) -> str:
        """HTML 블록에서 업체명 후보 추출"""
        # 태그 제거 후 텍스트만 추출
        text = re.sub(r'<[^>]+>', ' ', block)
        text = re.sub(r'\s+', ' ', text).strip()

        # 지역명이나 키워드 포함된 짧은 텍스트 조각을 업체명으로 사용
        sentences = [s.strip() for s in re.split(r'[|·\-–—·,\n]', text) if s.strip()]
        for sentence in sentences:
            # 3~30자, 영문 '@' 없음, 괄호 없음
            if 3 <= len(sentence) <= 30 and "@" not in sentence and "http" not in sentence:
                if keyword in sentence or region in sentence:
                    return sentence

        # 후보 없으면 첫 번째 짧은 문장
        for sentence in sentences:
            if 3 <= len(sentence) <= 30 and "@" not in sentence and "http" not in sentence:
                return sentence

        return f"{region} {keyword}"

    async def enrich_with_instagram(self, page, business_name: str, region: str) -> str:
        """
        단일 업체명으로 인스타 URL 검색 (다른 수집기 결과 보완용).
        반환: 인스타 URL 문자열 또는 ""
        """
        try:
            query = f"{business_name} {region} 인스타그램"
            encoded = quote(query)
            url = f"https://search.naver.com/search.naver?query={encoded}&where=web"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(DELAY_INSTA * 1000)
            html = await page.content()
            return self.extract_instagram(html)
        except Exception as e:
            logger.debug("enrich_with_instagram 오류 (%s): %s", business_name, e)
            # 구글 폴백
            try:
                query = f"{business_name} {region} instagram"
                encoded = quote(query)
                url = f"https://www.google.com/search?q={encoded}&hl=ko"
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(DELAY_INSTA * 1000)
                html = await page.content()
                return self.extract_instagram(html)
            except Exception as e2:
                logger.debug("enrich_with_instagram 구글 폴백 오류 (%s): %s", business_name, e2)
                return ""
