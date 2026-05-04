"""네이버 Local Search API + 네이버 플레이스 Playwright 스크래핑"""
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

NAVER_LOCAL_API = "https://openapi.naver.com/v1/search/local.json"
NAVER_MOBILE_SEARCH = "https://m.search.naver.com/search.naver"
PLACE_ID_RE = re.compile(r'/place/(\d{6,})')


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
        "source": "네이버",
    }


class NaverPlaceCollector(BaseCollector):
    platform_name = "네이버"

    async def collect(self, region: str, keyword: str, limit: int = 100) -> list[dict]:
        results: list[dict] = []
        try:
            api_items = await self._fetch_api(region, keyword, limit)
            if api_items:
                results.extend(api_items)
                logger.info("[네이버API] %s %s → %d건", region, keyword, len(api_items))
            else:
                logger.info("[네이버API] 결과 없음, Playwright 폴백 시작")
                pw_items = await self._fetch_playwright(region, keyword, limit)
                results.extend(pw_items)
        except Exception as exc:
            logger.error("[네이버] collect 오류: %s", exc, exc_info=True)
        return results[:limit]

    # ------------------------------------------------------------------
    # 1) 네이버 Local Search API
    # ------------------------------------------------------------------
    async def _fetch_api(self, region: str, keyword: str, limit: int) -> list[dict]:
        if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
            return []

        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        }
        items: list[dict] = []
        display = 5
        api_total = None  # 첫 응답에서 total 확인 후 페이지네이션 상한 결정

        async with httpx.AsyncClient(timeout=15) as client:
            for start in range(1, 1001, display):  # Naver API start 최대 1000
                params = {
                    "query": f"{region} {keyword}",
                    "display": display,
                    "start": start,
                }
                try:
                    resp = await client.get(NAVER_LOCAL_API, headers=headers, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as exc:
                    logger.warning("[네이버API] 요청 실패: %s", exc)
                    break

                # 첫 응답에서 total 확인 → 실제 결과 수 이상 요청하지 않음
                if api_total is None:
                    api_total = int(data.get("total", 0))
                    if api_total == 0:
                        break

                raw_items = data.get("items", [])
                if not raw_items:
                    break

                for item in raw_items:
                    name = re.sub(r'<[^>]+>', '', item.get("title", "")).strip()
                    if not name or self.is_franchise(name):
                        continue
                    address = item.get("roadAddress") or item.get("address", "")
                    # region filter — Seoul/타지역 섞임 차단
                    if not self.is_in_region(address, region):
                        continue
                    phone_raw = item.get("telephone", "")
                    phone = self.normalize_phone(phone_raw) if phone_raw else ""
                    link = item.get("link", "")
                    naver_place_url = link if "naver.com" in link else ""
                    items.append(_make_record(
                        name=name,
                        phone=phone,
                        address=address,
                        naver_place_url=naver_place_url,
                        category=keyword,
                    ))

                await asyncio.sleep(DELAY_NAVER)
                # total 초과하거나 limit 도달 시 중단
                if api_total is not None and start + display > api_total:
                    break
                if len(items) >= limit:
                    break

        # 인스타 보완은 인스타그램 컬렉터가 따로 수집 — 여기서 스킵 (속도 우선)
        return items

    # ------------------------------------------------------------------
    # 2) Playwright 직접 검색 (API 키 없을 때 폴백)
    # ------------------------------------------------------------------
    async def _fetch_playwright(self, region: str, keyword: str, limit: int) -> list[dict]:
        items: list[dict] = []
        query = f"{region} {keyword}"
        encoded = quote(query)
        all_place_ids: list[str] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=MOBILE_UA)
            page = await context.new_page()

            try:
                url = f"{NAVER_MOBILE_SEARCH}?query={encoded}&where=m_local"
                await page.goto(url, timeout=25000)
                await page.wait_for_load_state("networkidle", timeout=20000)

                # 스크롤 + 더보기 반복으로 place_id 최대한 수집
                for _ in range(15):  # 최대 15회 스크롤/더보기
                    html = await page.content()
                    new_ids = PLACE_ID_RE.findall(html)
                    for pid in new_ids:
                        if pid not in all_place_ids:
                            all_place_ids.append(pid)

                    if len(all_place_ids) >= limit:
                        break

                    # "더보기" 버튼 클릭 시도
                    more_btn = await page.query_selector(
                        "a.btn_more, button.btn_more, a[class*='more'], button[class*='more']"
                    )
                    if more_btn:
                        try:
                            await more_btn.click()
                            await page.wait_for_load_state("networkidle", timeout=10000)
                            await asyncio.sleep(0.5)
                            continue
                        except Exception:
                            pass

                    # 스크롤 다운
                    prev_height = await page.evaluate("document.body.scrollHeight")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1.0)
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == prev_height:
                        break  # 더 이상 내용 없음

                logger.info("[네이버PW] %s → place_id %d개", query, len(all_place_ids))

                for pid in all_place_ids[:limit]:
                    record = await self._scrape_place_detail(context, pid, keyword)
                    if record:
                        items.append(record)
                    await asyncio.sleep(DELAY_NAVER)

            except PWTimeout:
                logger.warning("[네이버PW] 타임아웃: %s", query)
            except Exception as exc:
                logger.error("[네이버PW] 오류: %s", exc, exc_info=True)
            finally:
                await browser.close()

        return items

    # ------------------------------------------------------------------
    # 3) 네이버 플레이스 상세 페이지 스크래핑
    # ------------------------------------------------------------------
    async def _scrape_place_detail(self, context, place_id: str, category: str) -> dict | None:
        place_url = f"https://m.place.naver.com/place/{place_id}/home"
        page = await context.new_page()
        try:
            await page.goto(place_url, timeout=20000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            html = await page.content()

            # 업체명
            name = ""
            name_el = await page.query_selector("span.GHAhO, h1.zD5Nm, .place_name")
            if name_el:
                name = (await name_el.inner_text()).strip()
            if not name:
                m = re.search(r'"placeName"\s*:\s*"([^"]{2,50})"', html)
                if m:
                    name = m.group(1)

            if not name or self.is_franchise(name):
                return None

            # 전화번호
            phone = ""
            phone_el = await page.query_selector("a[href^='tel:'], span.xlx7Q")
            if phone_el:
                tel = await phone_el.get_attribute("href") or await phone_el.inner_text()
                phone_raw = tel.replace("tel:", "").strip()
                phone = self.normalize_phone(phone_raw)
            if not phone:
                phone_raw = self.extract_phone(html)
                phone = self.normalize_phone(phone_raw) if phone_raw else ""

            # 주소
            address = ""
            addr_el = await page.query_selector("span.LDgIH, .addr")
            if addr_el:
                address = (await addr_el.inner_text()).strip()

            # 인스타그램
            insta_url = self.extract_instagram(html)

            return _make_record(
                name=name,
                phone=phone,
                address=address,
                insta_url=insta_url,
                naver_place_url=place_url,
                category=category,
            )

        except PWTimeout:
            logger.warning("[네이버플레이스] 타임아웃 place_id=%s", place_id)
            return None
        except Exception as exc:
            logger.error("[네이버플레이스] place_id=%s 오류: %s", place_id, exc)
            return None
        finally:
            await page.close()

    # ------------------------------------------------------------------
    # 4) API 결과에 인스타그램 URL 보완 (place_url이 없으면 검색)
    # ------------------------------------------------------------------
    async def _enrich_instagram(self, items: list[dict]) -> list[dict]:
        needs_enrich = [i for i in items if not i.get("insta_url") and i.get("naver_place_url")]
        if not needs_enrich:
            return items

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=MOBILE_UA)

            for item in needs_enrich:
                place_url = item["naver_place_url"]
                m = PLACE_ID_RE.search(place_url)
                if not m:
                    continue
                pid = m.group(1)
                record = await self._scrape_place_detail(context, pid, item.get("category", ""))
                if record:
                    item["insta_url"] = record.get("insta_url", "")
                    if not item["phone"] and record.get("phone"):
                        item["phone"] = record["phone"]
                await asyncio.sleep(DELAY_NAVER)

            await browser.close()

        return items
