"""당근마켓 비즈프로필 수집 — 네이버 검색 경유 + 당근 직접 접근"""
import asyncio
import logging
import re
from urllib.parse import quote

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from app.collectors.base_collector import BaseCollector
from app.config import DESKTOP_UA, DELAY_DAANGN

logger = logging.getLogger(__name__)

DAANGN_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?daangn\.com/(?:kr/biz/|articles/|fleamarket/)[^\s"\'<>]+'
)
NAVER_WEB_SEARCH = "https://search.naver.com/search.naver"
DAANGN_SEARCH = "https://www.daangn.com/kr/search/"


def _make_record(
    name: str = "",
    phone: str = "",
    address: str = "",
    insta_url: str = "",
    naver_place_url: str = "",
    daangn_url: str = "",
    category: str = "",
) -> dict:
    return {
        "name": name,
        "phone": phone,
        "address": address,
        "insta_url": insta_url,
        "naver_place_url": naver_place_url,
        "daangn_url": daangn_url,
        "category": category,
        "source": "당근마켓",
    }


class DaangnCollector(BaseCollector):
    platform_name = "당근마켓"

    async def collect(self, region: str, keyword: str, limit: int = 100) -> list[dict]:
        results: list[dict] = []
        try:
            # 1차: 당근마켓 직접 검색
            direct_items = await self._fetch_daangn_direct(region, keyword, limit)
            results.extend(direct_items)
            logger.info("[당근직접] %s %s → %d건", region, keyword, len(direct_items))

            # 2차: 네이버 검색으로 당근 URL 보완 (중복 제외하고 추가)
            existing_names = {r["name"] for r in results if r["name"]}
            naver_items = await self._fetch_via_naver(region, keyword, limit - len(results))
            for item in naver_items:
                if item["name"] not in existing_names:
                    results.append(item)
                    existing_names.add(item["name"])

        except Exception as exc:
            logger.error("[당근마켓] collect 오류: %s", exc, exc_info=True)
        return results[:limit]

    # ------------------------------------------------------------------
    # 1) 당근마켓 직접 검색
    # ------------------------------------------------------------------
    async def _fetch_daangn_direct(self, region: str, keyword: str, limit: int) -> list[dict]:
        items: list[dict] = []
        query = f"{keyword} {region}"
        encoded = quote(query)
        url = f"{DAANGN_SEARCH}?q={encoded}"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=DESKTOP_UA)
            page = await context.new_page()

            try:
                await page.goto(url, timeout=25000)
                await page.wait_for_load_state("networkidle", timeout=20000)

                # 비즈프로필 탭 클릭 시도
                for tab_sel in ["[data-tab='business']", "button:has-text('비즈프로필')", "a:has-text('비즈프로필')"]:
                    tab = await page.query_selector(tab_sel)
                    if tab:
                        await tab.click()
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        break

                await asyncio.sleep(1.0)

                # 스크롤로 더 많은 결과 로딩
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(0.8)

                html = await page.content()
                biz_items = await page.query_selector_all(
                    ".BizProfileCard, .business-item, [class*='BizProfile'], [class*='biz-profile']"
                )

                if biz_items:
                    for el in biz_items[:limit]:
                        record = await self._extract_biz_card(el, html, keyword)
                        if record:
                            items.append(record)
                else:
                    # 셀렉터 없으면 HTML 파싱
                    fallback = self._parse_daangn_html(html, keyword)
                    items.extend(fallback[:limit])

            except PWTimeout:
                logger.warning("[당근직접] 타임아웃: %s", query)
            except Exception as exc:
                logger.error("[당근직접] 오류: %s", exc, exc_info=True)
            finally:
                await browser.close()

        return items

    async def _extract_biz_card(self, el, page_html: str, category: str) -> dict | None:
        try:
            name = ""
            for sel in [".business-name", ".biz-name", "strong", "h2", "h3", "[class*='name']"]:
                name_el = await el.query_selector(sel)
                if name_el:
                    name = (await name_el.inner_text()).strip()
                    break

            if not name or self.is_franchise(name):
                return None

            # 당근마켓 URL 추출
            daangn_url = ""
            link_el = await el.query_selector("a[href*='daangn.com'], a[href*='/kr/biz/']")
            if link_el:
                href = await link_el.get_attribute("href") or ""
                if href.startswith("/"):
                    href = "https://www.daangn.com" + href
                daangn_url = href

            # 카테고리/업종
            category_text = ""
            cat_el = await el.query_selector(".category, .business-type, [class*='category']")
            if cat_el:
                category_text = (await cat_el.inner_text()).strip()

            return _make_record(
                name=name,
                daangn_url=daangn_url,
                category=category_text or category,
            )

        except Exception as exc:
            logger.debug("[당근] 카드 파싱 오류: %s", exc)
            return None

    def _parse_daangn_html(self, html: str, category: str) -> list[dict]:
        items: list[dict] = []
        urls = list(dict.fromkeys(DAANGN_URL_PATTERN.findall(html)))

        name_pattern = re.compile(
            r'"(?:businessName|name|title)"\s*:\s*"([^"]{2,50})"'
        )
        names = [m.group(1) for m in name_pattern.finditer(html)]

        for i, url in enumerate(urls):
            name = names[i] if i < len(names) else ""
            if name and self.is_franchise(name):
                continue
            items.append(_make_record(
                name=name,
                daangn_url=url,
                category=category,
            ))

        return items

    # ------------------------------------------------------------------
    # 2) 네이버 검색에서 당근마켓 URL 수집 (업체명 있는 경우 더 정확)
    # ------------------------------------------------------------------
    async def _fetch_via_naver(self, region: str, keyword: str, limit: int) -> list[dict]:
        if limit <= 0:
            return []

        items: list[dict] = []
        query = f"{region} {keyword} 당근마켓"
        encoded = quote(query)
        url = f"{NAVER_WEB_SEARCH}?query={encoded}&where=web"

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=DESKTOP_UA)
            page = await context.new_page()

            try:
                await page.goto(url, timeout=25000)
                await page.wait_for_load_state("networkidle", timeout=20000)
                html = await page.content()

                daangn_urls = list(dict.fromkeys(DAANGN_URL_PATTERN.findall(html)))
                logger.info("[당근네이버] %s → daangn URL %d개", query, len(daangn_urls))

                # 각 URL에서 업체명 추출 시도
                for daangn_url in daangn_urls[:limit]:
                    record = await self._scrape_daangn_profile(context, daangn_url, keyword)
                    if record:
                        items.append(record)
                    await asyncio.sleep(DELAY_DAANGN)

            except PWTimeout:
                logger.warning("[당근네이버] 타임아웃")
            except Exception as exc:
                logger.error("[당근네이버] 오류: %s", exc, exc_info=True)
            finally:
                await browser.close()

        return items

    async def _scrape_daangn_profile(self, context, daangn_url: str, category: str) -> dict | None:
        """당근마켓 비즈프로필 페이지에서 업체 정보 추출"""
        page = await context.new_page()
        try:
            await page.goto(daangn_url, timeout=20000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            html = await page.content()

            # 업체명
            name = ""
            for sel in ["h1.BizProfileName, h1[class*='name']", "h1", ".profile-name", "[class*='ProfileName']"]:
                name_el = await page.query_selector(sel)
                if name_el:
                    name = (await name_el.inner_text()).strip()
                    break
            if not name:
                m = re.search(r'"(?:name|businessName)"\s*:\s*"([^"]{2,50})"', html)
                if m:
                    name = m.group(1)

            if not name or self.is_franchise(name):
                return None

            # 인스타그램 (비즈프로필에 링크 있는 경우)
            insta_url = self.extract_instagram(html)

            # 주소 (비즈프로필에 위치 있는 경우)
            address = ""
            addr_el = await page.query_selector(".LocationText, [class*='location'], [class*='address']")
            if addr_el:
                address = (await addr_el.inner_text()).strip()

            return _make_record(
                name=name,
                address=address,
                insta_url=insta_url,
                daangn_url=daangn_url,
                category=category,
            )

        except PWTimeout:
            logger.warning("[당근프로필] 타임아웃: %s", daangn_url)
            return None
        except Exception as exc:
            logger.debug("[당근프로필] 오류 %s: %s", daangn_url, exc)
            return None
        finally:
            await page.close()
