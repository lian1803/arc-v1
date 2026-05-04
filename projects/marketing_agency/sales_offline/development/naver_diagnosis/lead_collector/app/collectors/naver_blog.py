"""네이버 블로그/카페에서 업체명 + 전화번호 추출 (보조 수집기)"""
import asyncio
import logging
import re
from urllib.parse import quote

import httpx
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from app.collectors.base_collector import BaseCollector
from app.config import (
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
    MOBILE_UA,
    DESKTOP_UA,
    DELAY_NAVER,
)

logger = logging.getLogger(__name__)

NAVER_BLOG_API = "https://openapi.naver.com/v1/search/blog.json"
NAVER_VIEW_SEARCH = "https://search.naver.com/search.naver"

# 업체명 추출: "업체명 전화번호" 패턴
BIZ_NAME_PHONE_RE = re.compile(
    r'([가-힣A-Za-z0-9\s]{2,20})\s+'
    r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})'
)
# 전화번호 단독 패턴
PHONE_RE = re.compile(r'0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}')

# 블로그 포스트 내 불필요 키워드 필터
SPAM_KEYWORDS = {"클릭", "광고", "제공", "협찬", "이벤트", "공지", "알림", "업데이트"}


def _make_record(
    name: str = "",
    phone: str = "",
    address: str = "",
    insta_url: str = "",
    naver_place_url: str = "",
    daangn_url: str = "",
    category: str = "",
    blog_url: str = "",
) -> dict:
    return {
        "name": name,
        "phone": phone,
        "address": address,
        "insta_url": insta_url,
        "naver_place_url": naver_place_url,
        "daangn_url": daangn_url,
        "category": category,
        "source": "네이버블로그",
        "blog_url": blog_url,
    }


class NaverBlogCollector(BaseCollector):
    platform_name = "네이버블로그"

    async def collect(self, region: str, keyword: str, limit: int = 50) -> list[dict]:
        """블로그 소스는 보조적이므로 기본 limit를 50으로 낮춤"""
        results: list[dict] = []
        try:
            if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
                api_items = await self._fetch_api(region, keyword, limit)
                results.extend(api_items)
                logger.info("[블로그API] %s %s → %d건", region, keyword, len(api_items))
            else:
                logger.info("[블로그] API 키 없음, Playwright 폴백")
                pw_items = await self._fetch_playwright(region, keyword, limit)
                results.extend(pw_items)
        except Exception as exc:
            logger.error("[네이버블로그] collect 오류: %s", exc, exc_info=True)
        return results[:limit]

    # ------------------------------------------------------------------
    # 1) 네이버 블로그 검색 API
    # ------------------------------------------------------------------
    async def _fetch_api(self, region: str, keyword: str, limit: int) -> list[dict]:
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        }
        post_urls: list[str] = []
        display = 5

        async with httpx.AsyncClient(timeout=15) as client:
            for start in range(1, min(limit * 2, 100) + 1, display):
                params = {
                    "query": f"{region} {keyword}",
                    "display": display,
                    "start": start,
                    "sort": "date",
                }
                try:
                    resp = await client.get(NAVER_BLOG_API, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    logger.warning("[블로그API] 요청 실패: %s", exc)
                    break

                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    link = item.get("link", "")
                    if link and "blog.naver.com" in link:
                        post_urls.append(link)

                await asyncio.sleep(DELAY_NAVER)
                if len(post_urls) >= limit * 2:
                    break

        if not post_urls:
            return []

        return await self._scrape_posts(post_urls, keyword, limit)

    # ------------------------------------------------------------------
    # 2) Playwright 뷰탭 검색 폴백
    # ------------------------------------------------------------------
    async def _fetch_playwright(self, region: str, keyword: str, limit: int) -> list[dict]:
        post_urls: list[str] = []
        query = f"{region} {keyword}"
        encoded = quote(query)
        url = f"{NAVER_VIEW_SEARCH}?where=view&query={encoded}"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=DESKTOP_UA)
            page = await context.new_page()

            try:
                await page.goto(url, timeout=25000)
                await page.wait_for_load_state("networkidle", timeout=20000)

                link_els = await page.query_selector_all(
                    "a[href*='blog.naver.com'], a[href*='cafe.naver.com']"
                )
                for el in link_els:
                    href = await el.get_attribute("href") or ""
                    if href and href not in post_urls:
                        post_urls.append(href)

                if not post_urls:
                    # HTML에서 직접 URL 추출
                    html = await page.content()
                    found = re.findall(
                        r'https?://(?:blog|cafe)\.naver\.com/[^\s"\'<>]+',
                        html,
                    )
                    post_urls = list(dict.fromkeys(found))

            except PWTimeout:
                logger.warning("[블로그PW] 타임아웃: %s", query)
            except Exception as exc:
                logger.error("[블로그PW] 오류: %s", exc, exc_info=True)
            finally:
                await browser.close()

        return await self._scrape_posts(post_urls[:limit * 2], keyword, limit)

    # ------------------------------------------------------------------
    # 3) 블로그 포스트 본문 스크래핑 → 업체명 + 전화번호 추출
    # ------------------------------------------------------------------
    async def _scrape_posts(self, urls: list[str], category: str, limit: int) -> list[dict]:
        results: list[dict] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=MOBILE_UA)

            for url in urls:
                if len(results) >= limit:
                    break
                try:
                    records = await self._extract_from_post(context, url, category)
                    results.extend(records)
                except Exception as exc:
                    logger.debug("[블로그포스트] %s 오류: %s", url, exc)
                await asyncio.sleep(DELAY_NAVER)

            await browser.close()

        # 중복 전화번호 제거
        seen_phones: set[str] = set()
        deduped: list[dict] = []
        for r in results:
            if r["phone"] and r["phone"] in seen_phones:
                continue
            if r["phone"]:
                seen_phones.add(r["phone"])
            deduped.append(r)

        return deduped[:limit]

    async def _extract_from_post(self, context, url: str, category: str) -> list[dict]:
        """블로그 포스트 1개에서 업체명+전화번호 쌍 추출"""
        page = await context.new_page()
        records: list[dict] = []

        try:
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # 네이버 블로그는 iframe 안에 실제 컨텐츠가 있음
            frame = None
            for fr in page.frames:
                if "blog.naver.com" in fr.url and fr.url != url:
                    frame = fr
                    break

            if frame:
                content_el = await frame.query_selector(
                    "#postViewArea, .se-main-container, .post-view"
                )
                text = (await content_el.inner_text()).strip() if content_el else await frame.inner_text("body")
            else:
                content_el = await page.query_selector(
                    ".se-main-container, #postViewArea, article, .post-content"
                )
                text = (await content_el.inner_text()).strip() if content_el else await page.inner_text("body")

            if not text:
                return []

            # 스팸 포스트 필터
            spam_count = sum(1 for kw in SPAM_KEYWORDS if kw in text[:200])
            if spam_count >= 3:
                return []

            # 방식 1: 업체명 + 전화번호 쌍 패턴
            for m in BIZ_NAME_PHONE_RE.finditer(text):
                name = m.group(1).strip()
                phone_raw = m.group(2).strip()
                if len(name) < 2 or self.is_franchise(name):
                    continue
                phone = self.normalize_phone(phone_raw)
                insta_url = self.extract_instagram(text)
                records.append(_make_record(
                    name=name,
                    phone=phone,
                    insta_url=insta_url,
                    category=category,
                    blog_url=url,
                ))

            # 방식 2: 전화번호만 있을 때 — 포스트 제목에서 업체명 추출
            if not records:
                phones = list(dict.fromkeys(PHONE_RE.findall(text)))
                if phones:
                    # 제목 추출 시도
                    title_el = await page.query_selector("title, h1, .se-title-text")
                    title = ""
                    if title_el:
                        title = (await title_el.inner_text()).strip()
                        # 제목에서 불필요한 부분 제거
                        title = re.sub(r'[:\-|]\s*네이버.*$', '', title).strip()

                    for phone_raw in phones[:3]:
                        phone = self.normalize_phone(phone_raw)
                        insta_url = self.extract_instagram(text)
                        records.append(_make_record(
                            name=title or "",
                            phone=phone,
                            insta_url=insta_url,
                            category=category,
                            blog_url=url,
                        ))

        except PWTimeout:
            logger.debug("[블로그포스트] 타임아웃: %s", url)
        except Exception as exc:
            logger.debug("[블로그포스트] 파싱 오류 %s: %s", url, exc)
        finally:
            await page.close()

        return records
