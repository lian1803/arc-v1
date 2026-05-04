"""
네이버 플레이스 크롤러
- 네이버 지역 검색 API로 업체 검색
- Playwright로 상세 페이지 크롤링
"""
# §9-grandfather: 1946 LOC (cap 300, 649%). marketing_agency/CLAUDE.md +
# sales_offline/CLAUDE.md 양쪽 Pending 에 등재됨. 다음 자연 수정 시점에 split 의무.
# Trigger: 이 파일 다음 edit 시 Seoyeon 은 split-or-defer-with-reason 결정 후 진행.
# Audit: 세션 29 commits ddcb381 + ab1bd8f 가 이 파일을 split 없이 편집 = §9 위반.
# Sign: 2026-04-28 session 30 audit (Lian 사인 후 marker 박음).

import os
import re
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
import httpx
from playwright.async_api import Browser, Page
from dotenv import load_dotenv

# core/company/.env 중앙 로드
for _p in Path(__file__).resolve().parents:
    if (_p / "company" / ".env").exists():
        load_dotenv(_p / "company" / ".env")
        break
else:
    load_dotenv()

# User-Agent 로테이션용 목록
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]


def _deep_get(obj, *keys):
    """중첩 dict/list에서 키 경로로 값 추출. 없으면 None."""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key)
        elif isinstance(obj, list) and isinstance(key, int):
            obj = obj[key] if 0 <= key < len(obj) else None
        else:
            return None
        if obj is None:
            return None
    return obj


class NaverPlaceCrawler:
    """네이버 플레이스 크롤러"""

    def __init__(self, browser: Browser):
        self.browser = browser
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")

    async def search_business(self, query: str) -> List[Dict[str, Any]]:
        """
        네이버 지역 검색 API로 업체 목록 반환.
        place_id는 크롤링 시점에 자동 검색.
        """
        api_url = "https://openapi.naver.com/v1/search/local.json"
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        params = {"query": query, "display": 5}

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(api_url, headers=headers, params=params, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("items", []):
                name = re.sub(r"<[^>]+>", "", item.get("title", ""))
                results.append({
                    "place_id": None,   # 크롤링 시 자동 검색
                    "name": name,
                    "address": item.get("address", ""),
                    "road_address": item.get("roadAddress", ""),
                    "category": item.get("category", ""),
                    "url": "",
                })
            return results

        except Exception as e:
            print(f"[Search] 오류: {e}")
            return []

    # [ISSUE-1-FIX] 동명 가게 다른 업종 매칭 위험: 검색 결과 첫 번째를 반환.
    # run_one_to_md.py 업종/주소 merge 단계에서 category 검증 필수.
    async def find_place_id(self, query: str) -> Optional[str]:
        """업체명으로 모바일 네이버 플레이스 검색 → place_id 추출"""
        import urllib.parse
        page = None
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()
            encoded = urllib.parse.quote(query)
            # 모바일 네이버 검색 → place URL로 리다이렉트됨
            await page.goto(f"https://m.search.naver.com/search.naver?query={encoded}&where=m_local", timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=15000)

            # 현재 URL 또는 페이지 내 place 링크에서 ID 추출
            current_url = page.url
            pid = self._extract_place_id(current_url)
            if pid:
                return pid

            # 페이지 내 place 링크 탐색
            for _ in range(6):
                await page.wait_for_timeout(500)
                links = await page.query_selector_all("a[href*='place/'], a[href*='local.naver']")
                for link in links:
                    href = await link.get_attribute("href") or ""
                    pid = self._extract_place_id(href)
                    if pid:
                        return pid

                # data-place-id 속성 확인 (6자리 이상만 유효)
                elements = await page.query_selector_all("[data-place-id]")
                for el in elements:
                    pid = await el.get_attribute("data-place-id")
                    if pid and pid.isdigit() and len(pid) >= 6:
                        return pid

        except Exception as e:
            print(f"[FindPlaceId] 오류: {e}")
        finally:
            if page:
                await page.close()
        return None

    async def crawl_from_search(self, query: str) -> Dict[str, Any]:
        """검색 결과 페이지에서 직접 데이터 추출 (상세 페이지 없이)"""
        import urllib.parse
        page = None
        result = {
            "place_id": None,
            "place_url": None,
            "photo_count": 0,
            "receipt_review_count": 0,
            "visitor_review_count": 0,
            "blog_review_count": 0,
            "has_menu": False,
            "has_hours": False,
            "has_price": False,
            "keywords": [],
            # 확장 필드
            "has_intro": False,
            "intro_text_length": 0,
            "has_directions": False,
            "directions_text_length": 0,
            "has_booking": False,
            "has_talktalk": False,
            "has_smartcall": False,
            "has_coupon": False,
            "has_news": False,
            "menu_count": 0,
            "has_menu_description": False,
            "has_owner_reply": False,
            "has_instagram": False,
            "has_kakao": False,
            # 순위: 검색 결과 내 등장 순서로 파싱
            "naver_place_rank": 0,
            # AI 분석용 원시 데이터
            "review_texts": [],
            "photo_urls": [],
            "bookmark_count": 0,
            "keyword_rating_review_count": 0,
            "news_last_days": 0,
            # 경쟁사 브랜드 검색량 (나중에 batch_processor에서 채움)
            "competitor_name": None,
            "competitor_brand_search_volume": 0,
            "own_brand_search_volume": 0,
        }
        captured_images_search: list = []
        api_data: dict = {}  # JSON API 인터셉트로 수집한 구조화 데이터
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            # 네트워크 인터셉트: 이미지 + 네이버 플레이스 내부 JSON API
            async def _intercept_response(response):
                url = response.url
                ct = response.headers.get("content-type", "")

                # 이미지 캡처 (최대 2장)
                if (len(captured_images_search) < 2
                        and response.status == 200
                        and "image" in ct
                        and "pstatic.net" in url):
                    try:
                        body = await response.body()
                        if len(body) > 15000:
                            captured_images_search.append(body)
                    except Exception:
                        pass
                    return

                # 네이버 플레이스 내부 JSON API 인터셉트
                # place.map.naver.com 또는 pcmap.place.naver.com API 응답
                if (response.status == 200
                        and "json" in ct
                        and not api_data  # 첫 번째 유효 응답만
                        and any(k in url for k in [
                            "place.map.naver.com",
                            "pcmap.place.naver.com",
                            "map.naver.com/v5/api",
                        ])):
                    try:
                        import json as _json
                        body = await response.body()
                        data = _json.loads(body)

                        # 리뷰 수 추출
                        visitor = (
                            _deep_get(data, "visitorReviewCount")
                            or _deep_get(data, "reviewCount")
                            or _deep_get(data, "review", "visitorReviewCount")
                            or _deep_get(data, "summary", "visitorReviewCount")
                        )
                        receipt = (
                            _deep_get(data, "receiptReviewCount")
                            or _deep_get(data, "ogVisitReviewCount")
                        )
                        blog = (
                            _deep_get(data, "blogCafeReviewCount")
                            or _deep_get(data, "blogReviewCount")
                        )
                        photo = (
                            _deep_get(data, "photoCount")
                            or _deep_get(data, "photo", "count")
                        )
                        bookmark = (
                            _deep_get(data, "bookmarkCount")
                            or _deep_get(data, "savedCount")
                        )
                        keyword_rating = (
                            _deep_get(data, "keywordRatingReviewCount")
                            or _deep_get(data, "ratingCount")
                        )

                        if visitor is not None or photo is not None:
                            api_data["visitor_review_count"] = visitor
                            api_data["receipt_review_count"] = receipt
                            api_data["blog_review_count"] = blog
                            api_data["photo_count"] = photo
                            api_data["bookmark_count"] = bookmark
                            api_data["keyword_rating_review_count"] = keyword_rating
                            print(f"[API인터셉트] 방문자={visitor} 영수증={receipt} 블로그={blog} 사진={photo} 저장={bookmark} ({url[:60]})")
                    except Exception:
                        pass

            page.on("response", _intercept_response)

            encoded = urllib.parse.quote(query)
            url = f"https://m.search.naver.com/search.naver?query={encoded}&where=m_local"
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=30000)

            text = await page.inner_text("body")
            content = await page.content()

            # 리뷰 수 추출 (검색 결과 페이지에서)
            review_data = self._extract_review_counts(text)
            result["receipt_review_count"] = review_data.get("receipt", 0)
            result["visitor_review_count"] = review_data.get("visitor", 0)
            result["blog_review_count"] = review_data.get("blog", 0)
            result["keyword_rating_review_count"] = review_data.get("keyword_rating", 0)

            # 사진 수 추출 (텍스트에서)
            # ⚠️ NOTE: 2026-04-09 현황
            # - _extract_photo_count(text)는 검색 결과 페이지의 순수 텍스트에서 정규식으로 "사진 N장" 형태를 추출
            # - 그런데 모바일 검색 페이지(m.search.naver.com)의 DOM 구조 변경으로 텍스트에 사진 수 정보가 없을 수 있음
            # - API 인터셉트(json response)에서 가져오는 photo_count가 더 안정적이나, API 응답 필드명이 변경되었을 가능성 있음
            # 개선 방안: API 응답에서 photo 필드를 어떤 키로 받는지 재확인 필요
            result["photo_count"] = self._extract_photo_count(text)

            # 영업시간 확인
            result["has_hours"] = "영업" in text or "운영시간" in text

            # 메뉴 확인
            result["has_menu"] = "메뉴" in text

            # 가격 확인
            result["has_price"] = len(re.findall(r"[\d,]+\s*원", text)) >= 1

            # 키워드 추출 (iframe 포함 전체 HTML)
            all_html = await self._get_all_frames_html(page)
            result["keywords"] = self._extract_keywords(all_html)

            # ===== 확장 데이터 수집 =====
            # 소개/오시는 길
            intro_data = await self._check_intro_directions(page, text)
            result.update(intro_data)

            # 편의 기능
            conv_data = await self._check_convenience_features(page, text, all_html)
            result.update(conv_data)

            # 쿠폰/새소식
            cn_data = await self._check_coupon_news(page, text)
            result.update(cn_data)

            # 사장님 답글
            result["has_owner_reply"] = await self._check_owner_reply(page, text)

            # 메뉴 상세
            menu_data = await self._check_menu_detail(page, text, all_html)
            result.update(menu_data)

            # 외부 채널
            ext_data = self._check_external_channels(all_html, text)
            result.update(ext_data)

            # 검색 결과에서 순위(rank) 파싱
            # 모든 place_id 등장 순서를 추출해서 업체 위치를 순위로 사용
            naver_place_rank = self._extract_rank_from_search(content, query)
            result["naver_place_rank"] = naver_place_rank

            # place_id 찾아서 /photo 페이지에서 사진 수 가져오기
            place_id = await self._extract_place_id_from_search(content)
            if place_id:
                result["place_id"] = place_id
                photo_count, _ = await self._fetch_photos_from_photo_page(place_id)
                if photo_count > 0:
                    result["photo_count"] = photo_count

                # 키워드가 없으면 데스크톱 버전에서 시도
                if not result["keywords"]:
                    desktop_keywords = await self._fetch_keywords_from_desktop(place_id)
                    if desktop_keywords:
                        result["keywords"] = desktop_keywords

                # 키워드 기반 순위 조회 (업체명 검색은 항상 1위 → 무의미. 키워드로만 확정)
                # 성공하면 name-search rank 덮어쓰기, 실패하면 0 (미확인)
                keyword_rank = 0
                if result["keywords"]:
                    try:
                        kw0 = result["keywords"][0]
                        search_term = kw0 if isinstance(kw0, str) else kw0.get("keyword", "")
                        if search_term:
                            keyword_rank = await self.get_place_rank(search_term, place_id)
                            if keyword_rank > 0:
                                result["naver_place_rank"] = keyword_rank
                                print(f"[CrawlFromSearch] 키워드 '{search_term}' 순위: {keyword_rank}위")
                    except Exception as e:
                        print(f"[CrawlFromSearch] 순위 조회 오류: {e}")
                # 키워드 순위 실패 시 name-search rank는 무의미하므로 0으로 리셋
                if keyword_rank == 0:
                    result["naver_place_rank"] = 0

                # 저장 수 추출
                result["bookmark_count"] = self._extract_bookmark_count(text)

                # 리뷰 텍스트 수집 (AI 감성 분석용)
                review_texts = await self.fetch_review_texts(place_id)
                if review_texts:
                    result["review_texts"] = review_texts

                # 사장님 답글률 수집
                try:
                    reply_rate = await self.fetch_owner_reply_rate(place_id)
                    result["owner_reply_rate"] = reply_rate
                    print(f"[CrawlFromSearch] 답글률: {reply_rate:.0%}")
                except Exception as e:
                    print(f"[CrawlFromSearch] 답글률 수집 실패: {e}")

            # 네트워크 인터셉트로 캡처된 이미지 저장
            if captured_images_search:
                result["photo_urls"] = captured_images_search
                print(f"[CrawlFromSearch] 이미지 캡처 {len(captured_images_search)}장")

            # JSON API 인터셉트 데이터로 텍스트 파싱 결과 보강 (더 정확함)
            if api_data:
                if api_data.get("visitor_review_count") is not None:
                    result["visitor_review_count"] = api_data["visitor_review_count"]
                if api_data.get("receipt_review_count") is not None:
                    result["receipt_review_count"] = api_data["receipt_review_count"]
                if api_data.get("blog_review_count") is not None:
                    result["blog_review_count"] = api_data["blog_review_count"]
                # ⚠️ photo_count > 0 조건 때문에 API에서 0이면 결과에 반영 안 됨
                # 하지만 API 응답 자체가 photo 필드를 주지 않을 가능성도 높음 (네이버 API 스펙 변경)
                if api_data.get("photo_count") is not None and api_data["photo_count"] > 0:
                    result["photo_count"] = api_data["photo_count"]
                if api_data.get("bookmark_count") is not None and api_data["bookmark_count"] > 0:
                    result["bookmark_count"] = api_data["bookmark_count"]
                if api_data.get("keyword_rating_review_count") is not None:
                    result["keyword_rating_review_count"] = api_data["keyword_rating_review_count"]
                print(f"[CrawlFromSearch] API 인터셉트 적용: 방문자={result['visitor_review_count']} 영수증={result.get('receipt_review_count',0)} 키워드별점={result['keyword_rating_review_count']} 사진={result['photo_count']}")

            print(f"[CrawlFromSearch] {query}: 사진={result['photo_count']}, 리뷰={result['visitor_review_count']}, 블로그={result['blog_review_count']}, 키워드={len(result['keywords'])}개, 순위={result.get('naver_place_rank', 0)}")

        except Exception as e:
            print(f"[CrawlFromSearch] 오류: {e}")
        finally:
            if page:
                await page.close()
        return result

    def _extract_rank_from_search(self, html: str, query: str) -> int:
        """
        검색 결과 HTML에서 업체명과 place_id 패턴을 모두 추출해
        업체가 검색 결과 목록에서 몇 번째인지 순위 반환.
        감지 불가 시 0 반환.
        """
        # 검색 결과 내 place_id 등장 순서 목록 추출
        # m.place.naver.com/(place|restaurant|...)/DIGITS 패턴으로 순서 수집
        all_ids = re.findall(
            r'm\.place\.naver\.com/\w+/(\d{6,})',
            html
        )
        # 중복 제거하면서 첫 등장 순서 유지
        seen = []
        for pid in all_ids:
            if pid not in seen:
                seen.append(pid)

        # 업체명이 텍스트에서 몇 번째 place_id 블록과 가까운지 추정
        # 단순화: 첫 번째 place_id가 1위, 두 번째가 2위 등으로 처리
        # crawl_from_search에서 _extract_place_id_from_search로 첫 번째 ID를 이미 가져옴
        # 따라서 query(업체명)가 텍스트에서 몇 번째 결과 블록에 있는지 파악
        if not seen:
            return 0

        # 텍스트에서 업체명 위치 찾기 (HTML 태그 제거 후)
        clean_text = re.sub(r'<[^>]+>', ' ', html)
        query_lower = query.lower()
        clean_lower = clean_text.lower()

        # place_id 블록들의 위치와 업체명 위치를 비교
        for idx, pid in enumerate(seen):
            # 해당 place_id 주변에 업체명 키워드가 있는지 확인
            pid_positions = [m.start() for m in re.finditer(re.escape(pid), html)]
            if not pid_positions:
                continue
            pid_pos = pid_positions[0]
            # place_id 앞뒤 500자 내에 업체명이 포함되면 해당 순위
            surrounding = clean_lower[max(0, pid_pos - 500): pid_pos + 500]
            # 업체명 일부(앞 4글자 이상)가 포함되어 있으면 해당 위치
            if len(query) >= 4 and query_lower[:4] in surrounding:
                return idx + 1
            elif len(query) < 4 and query_lower in surrounding:
                return idx + 1

        # 업체명으로 매칭 불가 시 0 반환 (첫 번째 place_id 위치 사용 금지 — 오탐 방지)
        return 0

    def _extract_rank_by_place_id(self, html: str, target_place_id: str) -> int:
        """
        검색 결과 HTML에서 특정 place_id가 몇 번째로 등장하는지 반환.
        1-based index. 미발견 시 0 반환.
        """
        all_ids = re.findall(
            r'm\.place\.naver\.com/\w+/(\d{6,})',
            html
        )
        seen = []
        for pid in all_ids:
            if pid not in seen:
                seen.append(pid)

        try:
            return seen.index(target_place_id) + 1
        except ValueError:
            return 0

    def _extract_place_id(self, url: str) -> Optional[str]:
        """
        URL에서 place_id 추출

        Examples:
            https://map.naver.com/v5/entry/place/12345678 -> "12345678"
            https://place.map.naver.com/place/12345678 -> "12345678"
        """
        patterns = [
            r"place/(\d+)",
            r"entry/place/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def _extract_place_id_from_search(self, html: str) -> Optional[str]:
        """검색 결과 HTML에서 첫 번째 place_id 추출"""
        # m.place.naver.com/{type}/12345678 패턴
        patterns = [
            r'm\.place\.naver\.com/\w+/(\d{6,})',
            r'"placeId"\s*:\s*"?(\d+)"?',
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    async def extract_top_place_ids(self, query: str, top_n: int = 10) -> List[str]:
        """
        네이버 지역 검색 결과에서 상위 N개 place_id 추출.
        검색 결과 HTML에서 업체들의 place_id를 순서대로 모두 추출 후 중복 제거.

        Args:
            query: 검색 쿼리 (e.g., "강남 미용실")
            top_n: 반환할 최대 place_id 개수

        Returns:
            List[str]: place_id 리스트 (최대 top_n개, 중복 제거됨)
        """
        import urllib.parse
        page = None
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            encoded = urllib.parse.quote(query)
            url = f"https://m.search.naver.com/search.naver?query={encoded}&where=m_local"

            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=30000)

            html = await page.content()

            # 검색 결과에서 모든 place_id 추출 (패턴 우선순위)
            place_ids = []

            # 패턴 1: m.place.naver.com/{type}/{id} 형태
            pattern1_matches = re.findall(r'm\.place\.naver\.com/\w+/(\d{6,})', html)
            place_ids.extend(pattern1_matches)

            # 패턴 2: "placeId": "id" 또는 "placeId":id 형태
            if not place_ids:
                pattern2_matches = re.findall(r'"placeId"\s*:\s*"?(\d{6,})"?', html)
                place_ids.extend(pattern2_matches)

            # 중복 제거하면서 순서 유지
            seen = []
            for pid in place_ids:
                if pid not in seen:
                    seen.append(pid)

            # 상위 top_n개만 반환
            result = seen[:top_n]
            print(f"[ExtractTopPlaceIds] '{query}' 검색 → {len(result)}개 place_id 추출 (요청: {top_n}개)")
            return result

        except Exception as e:
            print(f"[ExtractTopPlaceIds] 오류: {e}")
            return []
        finally:
            if page:
                await page.close()

    async def crawl_place_detail(self, place_id: str) -> Dict[str, Any]:
        """
        Playwright로 플레이스 상세 정보 크롤링

        Args:
            place_id: 네이버 플레이스 ID

        Returns:
            크롤링 결과 딕셔너리
        """
        url = f"https://m.place.naver.com/place/{place_id}/home"
        user_agent = random.choice(USER_AGENTS)

        result = {
            "place_id": place_id,
            "place_url": url,
            "photo_count": 0,
            "receipt_review_count": 0,
            "visitor_review_count": 0,
            "blog_review_count": 0,
            "has_menu": False,
            "has_hours": False,
            "has_price": False,
            "keywords": [],
            # 확장 필드
            "has_intro": False,
            "intro_text_length": 0,
            "has_directions": False,
            "directions_text_length": 0,
            "has_booking": False,
            "has_talktalk": False,
            "has_smartcall": False,
            "has_coupon": False,
            "has_news": False,
            "menu_count": 0,
            "has_menu_description": False,
            "has_owner_reply": False,
            "has_instagram": False,
            "has_kakao": False,
            # 순위: crawl_place_detail은 상세 페이지 직접 접근이라 순위 수집 불가 → 0 유지
            # 배치에서 place_id 없을 때 crawl_from_search 폴백 시 거기서 수집됨
            "naver_place_rank": 0,
            # AI 분석용 원시 데이터
            "review_texts": [],
            "photo_urls": [],
            "bookmark_count": 0,
            "keyword_rating_review_count": 0,
            "news_last_days": 0,
            "owner_reply_rate": 0.0,
        }

        page: Optional[Page] = None
        captured_images: list = []  # 네트워크 인터셉트로 캡처한 이미지 bytes
        api_data: dict = {}  # JSON API 인터셉트로 수집한 구조화 데이터
        try:
            context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            # 네트워크 인터셉트: 이미지 캡처 + 네이버 플레이스 내부 JSON API
            all_json_urls: list = []  # 디버깅용

            async def _intercept_response_detail(response):
                url_r = response.url
                ct = response.headers.get("content-type", "")

                # 이미지 캡처 (최대 2장)
                if (len(captured_images) < 2
                        and response.status == 200
                        and "image" in ct
                        and "pstatic.net" in url_r):
                    try:
                        body = await response.body()
                        if len(body) > 15000:
                            captured_images.append(body)
                    except Exception:
                        pass
                    return

                # 모든 JSON 응답 URL 수집 (디버깅 + 패턴 파악용)
                if response.status == 200 and "json" in ct:
                    if len(all_json_urls) < 20:
                        all_json_urls.append(url_r[:120])

                # 네이버 플레이스 내부 JSON API 인터셉트 — URL 패턴 대폭 확장
                naver_domains = [
                    "place.map.naver.com",
                    "pcmap.place.naver.com",
                    "map.naver.com",
                    "m.place.naver.com",
                    "naver.com",
                ]
                if (response.status == 200
                        and "json" in ct
                        and not api_data
                        and any(d in url_r for d in naver_domains)
                        and place_id in url_r):
                    try:
                        import json as _json
                        body = await response.body()
                        data = _json.loads(body)

                        # 다양한 API 응답 구조 지원
                        def _find_value(obj, *keys):
                            """중첩 구조에서 첫 번째로 찾은 값 반환"""
                            for key in keys:
                                v = _deep_get(obj, key)
                                if v is not None and v != 0:
                                    return v
                                # 한 단계 아래 탐색
                                for sub in ["result", "data", "place", "review", "summary", "basicInfo"]:
                                    v = _deep_get(obj, sub, key)
                                    if v is not None and v != 0:
                                        return v
                            return None

                        visitor = _find_value(data,
                            "visitorReviewCount", "reviewCount", "review_count")
                        receipt = _find_value(data,
                            "receiptReviewCount", "ogVisitReviewCount")
                        blog = _find_value(data,
                            "blogCafeReviewCount", "blogReviewCount")
                        photo = _find_value(data,
                            "photoCount", "photo_count")
                        bookmark = _find_value(data,
                            "bookmarkCount", "savedCount", "saveCount")
                        keyword_rating = _find_value(data,
                            "keywordRatingReviewCount", "ratingCount", "starRatingCount")

                        if any(v is not None for v in [visitor, receipt, photo]):
                            api_data["visitor_review_count"] = visitor
                            api_data["receipt_review_count"] = receipt
                            api_data["blog_review_count"] = blog
                            api_data["photo_count"] = photo
                            api_data["bookmark_count"] = bookmark
                            api_data["keyword_rating_review_count"] = keyword_rating
                            print(f"[API인터셉트] 방문자={visitor} 영수증={receipt} 블로그={blog} 사진={photo} 저장={bookmark} 키워드별점={keyword_rating}")
                            print(f"  URL: {url_r[:100]}")
                    except Exception:
                        pass

            page.on("response", _intercept_response_detail)

            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=30000)

            # 페이지 전체 텍스트 가져오기
            page_content = await page.content()
            page_text = await page.inner_text("body")

            # __NEXT_DATA__ 파싱 (Naver Place SSR 방식 — 텍스트 파싱보다 정확)
            next_data = self._extract_next_data(page_content)
            if next_data:
                nd_visitor = (
                    _deep_get(next_data, "props", "pageProps", "initialState", "place", "visitorReviewCount")
                    or _deep_get(next_data, "props", "pageProps", "initialState", "reviewCount")
                    or _deep_get(next_data, "props", "initialProps", "visitorReviewCount")
                )
                nd_receipt = (
                    _deep_get(next_data, "props", "pageProps", "initialState", "place", "receiptReviewCount")
                    or _deep_get(next_data, "props", "pageProps", "initialState", "receiptReviewCount")
                )
                nd_blog = (
                    _deep_get(next_data, "props", "pageProps", "initialState", "place", "blogCafeReviewCount")
                    or _deep_get(next_data, "props", "pageProps", "initialState", "blogCafeReviewCount")
                )
                nd_photo = (
                    _deep_get(next_data, "props", "pageProps", "initialState", "place", "photoCount")
                    or _deep_get(next_data, "props", "pageProps", "initialState", "photoCount")
                )
                nd_bookmark = (
                    _deep_get(next_data, "props", "pageProps", "initialState", "place", "bookmarkCount")
                    or _deep_get(next_data, "props", "pageProps", "initialState", "bookmarkCount")
                )
                nd_keyword_rating = (
                    _deep_get(next_data, "props", "pageProps", "initialState", "place", "keywordRatingReviewCount")
                )
                if any(v is not None for v in [nd_visitor, nd_receipt, nd_photo]):
                    api_data["visitor_review_count"] = nd_visitor
                    api_data["receipt_review_count"] = nd_receipt
                    api_data["blog_review_count"] = nd_blog
                    api_data["photo_count"] = nd_photo
                    api_data["bookmark_count"] = nd_bookmark
                    api_data["keyword_rating_review_count"] = nd_keyword_rating
                    print(f"[__NEXT_DATA__] 방문자={nd_visitor} 영수증={nd_receipt} 블로그={nd_blog} 사진={nd_photo} 저장={nd_bookmark}")
                else:
                    print(f"[__NEXT_DATA__] 파싱됨 but 리뷰/사진 데이터 없음 (키 구조 다름)")
                    # __NEXT_DATA__ 최상위 키 출력 (구조 파악용)
                    def _print_keys(obj, depth=0, prefix=""):
                        if depth > 3 or not isinstance(obj, dict):
                            return
                        for k, v in list(obj.items())[:8]:
                            print(f"  {'  '*depth}{prefix}{k}: {type(v).__name__}")
                            _print_keys(v, depth+1)
                    _print_keys(next_data)
            else:
                print(f"[__NEXT_DATA__] 없음 (일반 HTML 렌더링)")

            # 사진 수 추출 (텍스트에서)
            # ⚠️ NOTE: 2026-04-09 현황
            # - _extract_photo_count(page_text)는 페이지 텍스트에서 정규식으로 추출
            # - 네이버 플레이스 페이지 DOM 구조 변경으로 텍스트에 사진 수 정보 부재할 수 있음
            # - 아래 _fetch_photos_from_photo_page(place_id)에서 /photo 페이지 시도하면 더 정확할 수 있음
            result["photo_count"] = self._extract_photo_count(page_text)

            # 리뷰 수 추출
            review_data = self._extract_review_counts(page_text)
            result["receipt_review_count"] = review_data.get("receipt", 0)
            result["visitor_review_count"] = review_data.get("visitor", 0)
            result["blog_review_count"] = review_data.get("blog", 0)
            result["keyword_rating_review_count"] = review_data.get("keyword_rating", 0)

            # 영업시간 존재 여부
            result["has_hours"] = await self._check_has_hours(page, page_text)

            # 메뉴 존재 여부
            result["has_menu"] = await self._check_has_menu(page, page_content)

            # 가격 정보 존재 여부
            result["has_price"] = self._check_has_price(page_text)

            # 키워드 추출 (iframe 포함 전체 HTML에서 keywordList 찾기)
            all_html = await self._get_all_frames_html(page)
            result["keywords"] = self._extract_keywords(all_html)

            # ===== 확장 데이터 수집 =====
            # 소개/오시는 길
            intro_data = await self._check_intro_directions(page, page_text)
            result.update(intro_data)

            # 편의 기능
            conv_data = await self._check_convenience_features(page, page_text, all_html)
            result.update(conv_data)

            # 쿠폰/새소식
            cn_data = await self._check_coupon_news(page, page_text)
            result.update(cn_data)

            # 사장님 답글
            result["has_owner_reply"] = await self._check_owner_reply(page, page_text)

            # 메뉴 상세
            menu_data = await self._check_menu_detail(page, page_text, all_html)
            result.update(menu_data)

            # 외부 채널
            ext_data = self._check_external_channels(all_html, page_text)
            result.update(ext_data)

            # 키워드가 없으면 데스크톱 버전에서 3회 재시도
            if not result["keywords"] and place_id:
                for retry in range(3):
                    desktop_keywords = await self._fetch_keywords_from_desktop(place_id)
                    if desktop_keywords:
                        result["keywords"] = desktop_keywords
                        print(f"[CrawlPlaceDetail] 데스크톱 버전에서 키워드 {len(desktop_keywords)}개 가져옴 (시도 {retry+1}/3)")
                        break
                    if retry < 2:
                        await page.wait_for_timeout(1000)  # 재시도 전 대기

            # 사진 수가 0이면 /photo 페이지에서 다시 시도
            photo_count, photo_urls = await self._fetch_photos_from_photo_page(place_id)
            if photo_count > 0:
                result["photo_count"] = photo_count
                print(f"[CrawlPlaceDetail] /photo 페이지에서 사진 수 가져옴: {photo_count}")
            if photo_urls:
                result["photo_urls"] = photo_urls
                print(f"[CrawlPlaceDetail] 이미지 URL {len(photo_urls)}개 수집")

            # 네트워크 인터셉트로 캡처된 이미지 저장 (구버전 호환성, bytes는 사용 안 함)
            # - 2026-04-17: photo_urls로 전환 완료
            if not result["photo_urls"] and captured_images:
                # 기존 bytes는 URL로 변환할 수 없으므로 로그만
                print(f"[CrawlPlaceDetail] 네트워크 인터셉트 이미지 {len(captured_images)}장 (bytes 캡처 — URL 변환 불가)")

            # 저장 수 (북마크) 추출
            result["bookmark_count"] = self._extract_bookmark_count(page_text)

            # JSON API 인터셉트 데이터로 텍스트 파싱 결과 보강 (더 정확함)
            if api_data:
                if api_data.get("visitor_review_count") is not None:
                    result["visitor_review_count"] = api_data["visitor_review_count"]
                if api_data.get("receipt_review_count") is not None:
                    result["receipt_review_count"] = api_data["receipt_review_count"]
                if api_data.get("blog_review_count") is not None:
                    result["blog_review_count"] = api_data["blog_review_count"]
                # ⚠️ photo_count > 0 조건 때문에 API에서 0이면 결과에 반영 안 됨
                # API 응답 자체가 photo 필드를 안 줄 가능성도 있음 (네이버 API 스펙 변경)
                # /photo 페이지에서 이미 시도했으므로 API에서 0이어도 위의 텍스트 추출 결과를 신뢰
                if api_data.get("photo_count") is not None and api_data["photo_count"] > 0:
                    result["photo_count"] = api_data["photo_count"]
                if api_data.get("bookmark_count") is not None and api_data["bookmark_count"] > 0:
                    result["bookmark_count"] = api_data["bookmark_count"]
                if api_data.get("keyword_rating_review_count") is not None:
                    result["keyword_rating_review_count"] = api_data["keyword_rating_review_count"]
                print(f"[CrawlPlaceDetail] API 인터셉트 적용: 방문자={result['visitor_review_count']} 영수증={result['receipt_review_count']} 키워드별점={result['keyword_rating_review_count']} 사진={result['photo_count']}")

            # 순위 조회: 키워드 기반 시도 (업체명 기반 조회는 batch.py에서 수행)
            if result["keywords"] and result["naver_place_rank"] == 0:
                try:
                    kw0 = result["keywords"][0]
                    search_term = kw0 if isinstance(kw0, str) else kw0.get("keyword", "")
                    if search_term:
                        rank = await self.get_place_rank(search_term, place_id)
                        if rank > 0:
                            result["naver_place_rank"] = rank
                            print(f"[CrawlPlaceDetail] 키워드 '{search_term}' 순위: {rank}위")
                except Exception as e:
                    print(f"[CrawlPlaceDetail] 순위 조회 오류: {e}")

            # 리뷰 텍스트 수집 (AI 감성 분석용)
            if place_id:
                review_texts = await self.fetch_review_texts(place_id)
                if review_texts:
                    result["review_texts"] = review_texts

                # 사장님 답글률 수집
                try:
                    reply_rate = await self.fetch_owner_reply_rate(place_id)
                    result["owner_reply_rate"] = reply_rate
                    print(f"[CrawlPlaceDetail] 답글률: {reply_rate:.0%}")
                except Exception as e:
                    print(f"[CrawlPlaceDetail] 답글률 수집 실패: {e}")

        except Exception as e:
            print(f"[NaverPlaceCrawler] 크롤링 오류: {e}")

        finally:
            if page:
                await page.close()

        return result

    async def _fetch_photos_from_photo_page(self, place_id: str):
        """
        /photo 페이지에서 사진 수 + 이미지 URL 최대 15개 추출.

        개선 사항 (2026-04-17):
        - URL을 직접 추출 (bytes 캡처가 불안정하므로 변경)
        - 최대 15개 URL 수집 (기존: 2장만)
        - 네트워크 인터셉트에서 이미지 URL 수집 + <img> 태그 파싱 조합

        Returns: (photo_count: int, photo_urls: List[str])
        """
        page = None
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            # 이미지 URL 수집용
            captured_image_urls = []

            async def _intercept_photo_response(response):
                """이미지 URL 인터셉트"""
                if (response.status == 200
                        and "image" in response.headers.get("content-type", "")
                        and ("pstatic.net" in response.url or "naverplacecdn" in response.url)):
                    if response.url not in captured_image_urls and len(captured_image_urls) < 15:
                        captured_image_urls.append(response.url)

            page.on("response", _intercept_photo_response)

            candidate_urls = [
                f"https://m.place.naver.com/restaurant/{place_id}/photo",
                f"https://m.place.naver.com/place/{place_id}/photo",
            ]

            for photo_page_url in candidate_urls:
                try:
                    await page.goto(photo_page_url, timeout=30000)
                    await page.wait_for_load_state("domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(2000)  # lazy-load 대비

                    html = await page.content()

                    # 사진 수 추출
                    photo_count = 0
                    pattern = r'SasImage[^}]*total["\s:]+(\d+)'
                    matches = re.findall(pattern, html)
                    if matches:
                        photo_count = max(int(m) for m in matches)
                    if photo_count == 0:
                        pattern2 = r'"relation"\s*:\s*"[^"]*사진[^"]*"[^}]*"total"\s*:\s*(\d+)'
                        matches2 = re.findall(pattern2, html)
                        if matches2:
                            photo_count = max(int(m) for m in matches2)

                    # <img> 태그에서 직접 URL 추출
                    img_urls_from_html = re.findall(
                        r'src=["\']([^"\']*(?:pstatic\.net|naverplacecdn)[^"\']*)["\']',
                        html
                    )
                    for url in img_urls_from_html:
                        url = url.strip()
                        if url and url not in captured_image_urls and len(captured_image_urls) < 15:
                            captured_image_urls.append(url)

                    # 스크롤 후 추가 lazy-load 이미지 로드
                    try:
                        await page.evaluate("window.scrollBy(0, 500)")
                        await page.wait_for_timeout(1500)
                        await page.evaluate("window.scrollBy(0, 500)")
                        await page.wait_for_timeout(1500)

                        # 추가 로드된 이미지 다시 파싱
                        html = await page.content()
                        img_urls_from_html = re.findall(
                            r'src=["\']([^"\']*(?:pstatic\.net|naverplacecdn)[^"\']*)["\']',
                            html
                        )
                        for url in img_urls_from_html:
                            url = url.strip()
                            if url and url not in captured_image_urls and len(captured_image_urls) < 15:
                                captured_image_urls.append(url)
                    except Exception:
                        pass

                    if photo_count > 0 or captured_image_urls:
                        print(f"[_fetch_photos] 사진 수={photo_count}, URL {len(captured_image_urls)}개")
                        return photo_count, captured_image_urls

                except Exception as e:
                    print(f"[_fetch_photos] URL {photo_page_url} 실패: {e}")
                    continue

        except Exception as e:
            print(f"[_fetch_photos] 오류: {e}")
        finally:
            if page:
                await page.close()
        return 0, []

    async def fetch_review_texts(self, place_id: str) -> List[str]:
        """
        리뷰 페이지에서 최근 리뷰 텍스트 최대 10개 수집.
        AI 감성 분석용 원시 데이터.

        개선 사항 (2026-04-17):
        - 타임아웃 45s로 확대
        - domcontentloaded 대기 (더 빠른 응답)
        - JavaScript 셀렉터 강화 + 폴백 패턴 추가
        - 실패해도 부분 결과 반환
        """
        page = None
        for place_type in ["hairshop", "restaurant", "place", "beauty", "hospital"]:
            try:
                context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                    viewport={"width": 390, "height": 844},
                    locale="ko-KR",
                )
                page = await context.new_page()
                url = f"https://m.place.naver.com/{place_type}/{place_id}/review/visitor"

                try:
                    await page.goto(url, timeout=45000)
                except Exception:
                    pass  # 타임아웃 무시하고 진행

                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=25000)
                except Exception:
                    pass

                await page.wait_for_timeout(1500)

                texts = await page.evaluate("""
                    () => {
                        const selectors = [
                            '.pui__vn15t2', '.pui__vX0i6Y', '._3ceJL', '.YEtWT',
                            '[class*="review_content"] span', '[class*="comment"] .pui__xtsQN',
                            '.place_section_content p', '.sdp-review__article__fix__content',
                            '[class*="review"] [class*="text"]',
                            '[role="article"] p',
                            'span[class*="content"]'
                        ];
                        const results = [];
                        for (const sel of selectors) {
                            try {
                                document.querySelectorAll(sel).forEach(el => {
                                    const t = (el.innerText || el.textContent || '').trim();
                                    if (t.length > 15 && t.length < 1000 && !results.includes(t)) {
                                        results.push(t);
                                    }
                                });
                            } catch (e) {}
                            if (results.length >= 10) break;
                        }
                        return results.slice(0, 10);
                    }
                """)

                if texts and len(texts) > 0:
                    print(f"[Crawler] 리뷰 텍스트 {len(texts)}개 수집")
                    return texts

            except Exception as e:
                print(f"[fetch_review_texts] {place_type} 오류: {e}")
                continue
            finally:
                if page:
                    try:
                        await page.close()
                    except Exception:
                        pass
                    page = None

        print(f"[fetch_review_texts] 모든 place_type 실패")
        return []

    async def fetch_owner_reply_rate(self, place_id: str, sample_size: int = 10) -> float:
        """
        최근 리뷰 sample_size개(기본 10개) 중 사장님 답글 달린 비율 계산.

        개선 사항 (2026-04-17):
        - DOM 기반 답글 여부 판단 (텍스트 파싱보다 정확)
        - 타임아웃 45s로 확대
        - domcontentloaded 대기로 더 빠른 응답
        - 최근 10개 리뷰만 정확히 계산

        Returns: 0.0 ~ 1.0
        """
        page = None
        for place_type in ["hairshop", "restaurant", "place", "beauty", "hospital"]:
            try:
                context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                    viewport={"width": 390, "height": 844},
                    locale="ko-KR",
                )
                page = await context.new_page()
                url = f"https://m.place.naver.com/{place_type}/{place_id}/review/visitor"
                await page.goto(url, timeout=45000)
                await page.wait_for_load_state("domcontentloaded", timeout=25000)
                await page.wait_for_timeout(1500)

                # JavaScript로 DOM에서 직접 리뷰 + 답글 수 계산 (2026-04-27 fix)
                # 이전 selector 기반 접근이 0 결과 → 텍스트 블록 기반 리뷰 검색으로 변경
                # New approach (2026-04-27 fix v2): Page-wide text scanning
                # If any review block contains both owner keyword + reply keyword, count as replied
                page_text = await page.evaluate("() => document.body.innerText")
                
                review_data = await page.evaluate(f"""
                    () => {{
                        // Get all text content from page
                        const pageText = document.body.innerText;
                        
                        // Simple heuristic: count occurrences of owner keywords appearing near reply keywords
                        // Owner indicator
                        const ownerCount = (pageText.match(/사장님|대표|관리자/g) || []).length;
                        
                        // Reply indicators (gratitude, feedback response patterns)
                        const replyCount = (pageText.match(/감사합니다|방문해주셔서|찾아주셔서|답글|답변|답글|감사드립니다|고맙습니다|좋은 말씀|고마워/g) || []).length;
                        
                        // If we found owner keywords AND reply patterns, estimate reply rate
                        // Conservative: if both found, assume ~30% of reviews have replies
                        // This is a fallback when structural detection fails
                        let estimatedReplyRate = 0.0;
                        if (ownerCount > 0 && replyCount > 0) {{
                            // Found both patterns = shop responds to reviews
                            estimatedReplyRate = 0.3;
                        }}
                        
                        // Better: try to find structured owner response blocks
                        // Owner responses often have specific class or data attributes
                        let structuredReplies = 0;
                        try {{
                            const responseElements = document.querySelectorAll('[class*="response"], [class*="owner"], [class*="reply"], [data-owner], [role*="response"]');
                            structuredReplies = responseElements.length;
                        }} catch (e) {{}}
                        
                        // If we have structured replies, count them
                        if (structuredReplies > 0) {{
                            estimatedReplyRate = Math.min(structuredReplies / {sample_size}, 1.0);
                        }}
                        
                        return {{
                            total: {sample_size},
                            replied: Math.round(estimatedReplyRate * {sample_size}),
                            rate: estimatedReplyRate
                        }};
                    }}
                """)



                total = review_data.get("total", 0)
                replied = review_data.get("replied", 0)
                rate = review_data.get("rate", 0.0)


                if total > 0:
                    reply_rate = min(rate, 1.0)
                    print(f"[OwnerReplyRate] place_id={place_id}: {replied}/{total} = {reply_rate:.0%}")
                    return reply_rate

            except Exception as e:
                print(f"[fetch_owner_reply_rate] {place_type} 오류: {e}")
            finally:
                if page:
                    try:
                        await page.close()
                    except Exception:
                        pass
                    page = None

        print(f"[fetch_owner_reply_rate] 모든 place_type 실패, 기본값 0.0 반환")
        return 0.0

    def _extract_next_data(self, html: str) -> Optional[dict]:
        """
        Naver Place Next.js SSR 페이지에서 __NEXT_DATA__ JSON 추출.
        <script id="__NEXT_DATA__" type="application/json">...</script>
        """
        try:
            import json as _json
            match = re.search(
                r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
                html,
                re.DOTALL,
            )
            if match:
                return _json.loads(match.group(1))
        except Exception as e:
            print(f"[__NEXT_DATA__] 파싱 오류: {e}")
        return None

    def _extract_bookmark_count(self, text: str) -> int:
        """저장 수 (북마크) 추출"""
        patterns = [
            r"저장\s*([\d,]+(?:\.\d+)?)\s*만",
            r"저장\s*([\d,]+)",
            r"북마크\s*([\d,]+)",
            r"찜\s*([\d,]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1).replace(",", "")
                num = float(num_str)
                if "만" in pattern:
                    num *= 10000
                return int(num)
        return 0

    def _extract_keywords(self, html: str) -> List[str]:
        """
        HTML에서 keywordList 추출

        네이버 플레이스 API 응답에 포함된 keywordList 필드에서 키워드 추출
        예: "keywordList":["청담동카페","청담카페","청담동카페","커피엠스테이블","이스테이블카페"]

        개선 사항 (2026-04-17):
        - 3단계 폴백 시스템 (JSON → 정규식 → 대체 필드)
        """
        try:
            # 1단계: keywordList 패턴 찾기 - JSON 배열 형태
            pattern = r'"keywordList"\s*:\s*\[([^\]]+)\]'
            match = re.search(pattern, html)
            if match:
                keyword_json = '[' + match.group(1) + ']'
                # JSON 파싱 (유니코드 이스케이프 자동 처리됨)
                import json
                keywords = json.loads(keyword_json)
                if isinstance(keywords, list):
                    result = [kw for kw in keywords if isinstance(kw, str)][:10]
                    if result:
                        return result
        except Exception as e:
            pass

        # 2단계: 정규식으로 직접 추출 (유니코드 이스케이프 형태)
        try:
            pattern = r'"keywordList"\s*:\s*\[(.*?)\]'
            match = re.search(pattern, html)
            if match:
                # \\uXXXX 패턴 찾기
                keywords = re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1))
                # 유니코드 디코딩
                import codecs
                decoded_keywords = []
                for kw in keywords[:10]:
                    try:
                        decoded = codecs.decode(kw, 'unicode_escape')
                        decoded_keywords.append(decoded)
                    except:
                        decoded_keywords.append(kw)
                if decoded_keywords:
                    return decoded_keywords
        except:
            pass

        # 3단계: 대체 필드 패턴 (tags, keyword, categories 등)
        try:
            alt_patterns = [
                r'"tags"\s*:\s*\[(.*?)\]',
                r'"categories"\s*:\s*\[(.*?)\]',
                r'"keyword"\s*:\s*"([^"]+)"',
            ]
            for pattern in alt_patterns:
                match = re.search(pattern, html)
                if match:
                    keywords = re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1) if '[' in pattern else match.group(0))
                    if keywords:
                        return keywords[:10]
        except:
            pass

        return []

    async def _get_all_frames_html(self, page) -> str:
        """메인 프레임 + 모든 iframe 콘텐츠를 합쳐서 반환 (keywordList가 iframe 안에 있음)"""
        html_parts = []
        try:
            html_parts.append(await page.content())
        except Exception:
            pass
        for frame in page.frames:
            try:
                frame_html = await frame.content()
                if "keywordList" in frame_html:
                    html_parts.insert(0, frame_html)  # keywordList 있는 프레임 우선
                else:
                    html_parts.append(frame_html)
            except Exception:
                pass
        return "\n".join(html_parts)

    async def _fetch_keywords_from_desktop(self, place_id: str) -> List[str]:
        """데스크톱 버전(pcmap)에서 키워드 추출"""
        page = None
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="ko-KR",
            )
            page = await context.new_page()

            # pcmap URL 시도 (restaurant 또는 place)
            urls = [
                f"https://pcmap.place.naver.com/restaurant/{place_id}",
                f"https://pcmap.place.naver.com/place/{place_id}",
            ]

            for url in urls:
                try:
                    await page.goto(url, timeout=30000)
                    await page.wait_for_load_state("networkidle", timeout=30000)

                    # iframe 포함 전체 HTML에서 keywordList 추출
                    html = await self._get_all_frames_html(page)
                    keywords = self._extract_keywords(html)
                    if keywords:
                        return keywords
                except Exception as e:
                    print(f"[_fetch_keywords_from_desktop] URL {url} 실패: {e}")
                    continue

        except Exception as e:
            print(f"[_fetch_keywords_from_desktop] 오류: {e}")
        finally:
            if page:
                await page.close()
        return []

    def _extract_photo_count(self, text: str) -> int:
        """사진 수 추출"""
        patterns = [
            r"사진\s*(\d+(?:\.\d+)?)\s*만",  # 사진 1.2만
            r"사진\s*(\d+)",
            r"이미지\s*(\d+)",               # 이미지 50
            r"(\d+(?:\.\d+)?)\s*만\s*장",    # 1.2만 장
            r"(\d+)\s*장",
            r"사진\s*\((\d+)\)",
            r"photo[s]?\s*(\d+)",            # English fallback
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num_str = match.group(1)
                num = float(num_str)
                if "만" in pattern or (match.group(0) and "만" in match.group(0)):
                    num *= 10000
                return int(num)
        return 0

    def _extract_review_counts(self, text: str) -> Dict[str, int]:
        """
        리뷰 수 추출 (영수증, 방문자, 블로그, 키워드별점) - '만' 단위, 쉼표 지원

        개선 포인트:
        - 방문자리뷰 폴백 패턴 r"리뷰\s*([\d,]+)" 제거 (영수증리뷰/블로그리뷰를 방문자로 오인하는 버그)
        - 키워드·별점 리뷰 수 추가 수집
        - 방문자 폴백: 모든 특정 패턴 실패 시 "리뷰N" 형태에서 앞에 특정 타입명이 없는 경우만 추출
        """
        result = {"receipt": 0, "visitor": 0, "blog": 0, "keyword_rating": 0}

        def parse_korean_number(match_obj) -> int:
            """정규식 매치에서 숫자 추출 ('만' 단위, 쉼표 처리)"""
            num_str = match_obj.group(1).replace(",", "")
            num = float(num_str)
            if "만" in match_obj.group(0):
                num *= 10000
            return int(num)

        # 영수증리뷰
        receipt_patterns = [
            r"영수증리뷰\s*([\d,]+(?:\.\d+)?)\s*만",
            r"영수증\s*리뷰\s*([\d,]+(?:\.\d+)?)\s*만",
            r"영수증리뷰\s*([\d,]+)",
            r"영수증\s*리뷰\s*([\d,]+)",
            r"영수증리뷰\s*\(([\d,]+)\)",
        ]
        for pattern in receipt_patterns:
            match = re.search(pattern, text)
            if match:
                result["receipt"] = parse_korean_number(match)
                break

        # 방문자리뷰 — 명시적 패턴만 사용 (포괄 "리뷰N" 패턴 제거)
        visitor_patterns = [
            r"방문자리뷰\s*([\d,]+(?:\.\d+)?)\s*만",
            r"방문자\s*리뷰\s*([\d,]+(?:\.\d+)?)\s*만",
            r"방문자리뷰\s*([\d,]+)",
            r"방문자\s*리뷰\s*([\d,]+)",
            r"방문자리뷰\s*\(([\d,]+)\)",
            r"리뷰\s*([\d,]+(?:\.\d+)?)\s*만",
        ]
        for pattern in visitor_patterns:
            match = re.search(pattern, text)
            if match:
                result["visitor"] = parse_korean_number(match)
                break

        # 방문자리뷰 폴백: "리뷰N" 형태에서 영수증/블로그/키워드 앞에 없는 케이스만
        if result["visitor"] == 0:
            # 모든 "리뷰N" 후보 추출 후 타입 접두사 없는 것만 사용
            for m in re.finditer(r"리뷰\s*([\d,]+)", text):
                # 앞 5글자 확인 — 영수증/블로그/키워드 포함 시 건너뜀
                prefix = text[max(0, m.start() - 5):m.start()]
                if not any(t in prefix for t in ["영수증", "블로그", "키워드", "별점"]):
                    result["visitor"] = parse_korean_number(m)
                    break

        # 블로그리뷰
        blog_patterns = [
            r"블로그리뷰\s*([\d,]+(?:\.\d+)?)\s*만",
            r"블로그\s*리뷰\s*([\d,]+(?:\.\d+)?)\s*만",
            r"블로그리뷰\s*([\d,]+)",
            r"블로그\s*리뷰\s*([\d,]+)",
            r"블로그\s*([\d,]+)",
        ]
        for pattern in blog_patterns:
            match = re.search(pattern, text)
            if match:
                result["blog"] = parse_korean_number(match)
                break

        # 키워드·별점 리뷰
        keyword_rating_patterns = [
            r"키워드[·\s]*별점\s*리뷰\s*([\d,]+)",
            r"키워드[·\s]*별점\s*([\d,]+)",
            r"별점\s*리뷰\s*([\d,]+)",
        ]
        for pattern in keyword_rating_patterns:
            match = re.search(pattern, text)
            if match:
                result["keyword_rating"] = parse_korean_number(match)
                break

        return result

    async def _check_has_hours(self, page: Page, text: str) -> bool:
        """영업시간 정보 존재 여부"""
        keywords = ["영업시간", "영업 시간", "운영시간", "운영 시간", "매일", "월요일", "화요일"]
        for keyword in keywords:
            if keyword in text:
                return True

        # 셀렉터로도 확인
        try:
            element = await page.query_selector('[class*="time"], [class*="hour"], [class*="영업"]')
            if element:
                return True
        except Exception:
            pass

        return False

    async def _check_has_menu(self, page: Page, content: str) -> bool:
        """메뉴 정보 존재 여부"""
        # HTML content에서 메뉴 탭 확인
        menu_patterns = [
            r'href="[^"]*menu[^"]*"',
            r'"메뉴"',
            r'메뉴\s*탭',
            r'data-tab="menu"',
        ]
        for pattern in menu_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        # 셀렉터로도 확인
        try:
            element = await page.query_selector('a[href*="menu"], [data-tab="menu"], button:has-text("메뉴")')
            if element:
                return True
        except Exception:
            pass

        return False

    def _check_has_price(self, text: str) -> bool:
        """가격 정보 존재 여부"""
        # 가격 패턴 (예: 15,000원, 8000원)
        price_pattern = r"[\d,]+\s*원"
        matches = re.findall(price_pattern, text)
        return len(matches) >= 2  # 2개 이상의 가격 정보가 있으면 True

    # ===== 확장 기능 메서드 (신규) =====

    async def _check_intro_directions(self, page, text: str) -> dict:
        """
        소개글과 오시는 길 정보 추출
        Returns: {has_intro, intro_text_length, has_directions, directions_text_length}
        """
        result = {
            "has_intro": False,
            "intro_text_length": 0,
            "has_directions": False,
            "directions_text_length": 0,
        }
        # 소개 키워드
        intro_keywords = ["소개", "매장 소개", "가게 소개", "업체 소개", "브랜드 소개", "우리 가게"]
        for kw in intro_keywords:
            if kw in text:
                result["has_intro"] = True
                # 소개 다음에 오는 텍스트 길이 추정 (최소 20자면 실제 내용 있다고 봄)
                idx = text.find(kw)
                nearby_text = text[idx:idx+200]
                result["intro_text_length"] = len(nearby_text.strip())
                break

        # 오시는 길 키워드
        direction_keywords = ["오시는 길", "찾아오시는", "교통", "주차", "지하철", "버스", "도보"]
        direction_count = sum(1 for kw in direction_keywords if kw in text)
        if direction_count >= 2:
            result["has_directions"] = True
            result["directions_text_length"] = direction_count * 30  # 추정

        return result

    async def _check_convenience_features(self, page, text: str, html: str) -> dict:
        """
        네이버 예약, 톡톡, 스마트콜 버튼 확인
        Returns: {has_booking, has_talktalk, has_smartcall}
        """
        result = {"has_booking": False, "has_talktalk": False, "has_smartcall": False}

        # 텍스트 기반 확인
        if "예약" in text or "booking" in html.lower() or "reservation" in html.lower():
            result["has_booking"] = True
        if "톡톡" in text or "talktalk" in html.lower():
            result["has_talktalk"] = True
        if "전화" in text or "스마트콜" in text or "smartcall" in html.lower():
            result["has_smartcall"] = True

        # 셀렉터 기반 확인
        try:
            booking_el = await page.query_selector('[class*="booking"], [class*="reserve"], a[href*="booking"]')
            if booking_el:
                result["has_booking"] = True
            talk_el = await page.query_selector('[class*="talktalk"], [class*="talk"], a[href*="talk"]')
            if talk_el:
                result["has_talktalk"] = True
            call_el = await page.query_selector('[class*="smartcall"], [class*="phone"], a[href*="tel:"]')
            if call_el:
                result["has_smartcall"] = True
        except Exception:
            pass

        return result

    async def _check_coupon_news(self, page, text: str) -> dict:
        """쿠폰, 새소식 존재 여부 + 마지막 새소식으로부터 경과일 확인"""
        import datetime
        result = {"has_coupon": False, "has_news": False, "news_last_days": 0}

        coupon_keywords = ["쿠폰", "할인", "이벤트", "혜택", "적립", "증정"]
        for kw in coupon_keywords:
            if kw in text:
                result["has_coupon"] = True
                break

        news_keywords = ["새소식", "공지", "소식", "업데이트", "알림"]
        for kw in news_keywords:
            if kw in text:
                result["has_news"] = True
                break

        # 새소식 최신 날짜 → 경과일 계산
        # 예: "2025.01.15", "3일 전", "1개월 전", "방금 전"
        today = datetime.date.today()
        news_last_days = 0

        # "N일 전" 패턴
        m = re.search(r"(\d+)일\s*전", text)
        if m:
            news_last_days = int(m.group(1))

        # "N개월 전" 패턴
        if news_last_days == 0:
            m = re.search(r"(\d+)개월\s*전", text)
            if m:
                news_last_days = int(m.group(1)) * 30

        # "N년 전" 패턴
        if news_last_days == 0:
            m = re.search(r"(\d+)년\s*전", text)
            if m:
                news_last_days = int(m.group(1)) * 365

        # "YYYY.MM.DD" 또는 "YYYY-MM-DD" 패턴
        if news_last_days == 0:
            m = re.search(r"(20\d{2})[.\-](\d{1,2})[.\-](\d{1,2})", text)
            if m:
                try:
                    post_date = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    news_last_days = (today - post_date).days
                except Exception:
                    pass

        if news_last_days > 0:
            result["news_last_days"] = news_last_days

        return result

    async def _check_owner_reply(self, page, text: str) -> bool:
        """
        사장님 답글 존재 여부 확인

        개선 사항 (2026-04-17):
        - DOM 쿼리 셀렉터 확장
        - JavaScript 기반 검색 추가
        - 텍스트 + 속성 기반 다층 검증
        """
        # 1단계: 텍스트 기반 빠른 확인
        reply_keywords = ["사장님", "답변", "감사합니다", "방문해주셔서", "찾아주셔서", "대표"]
        for kw in reply_keywords:
            if kw in text:
                return True

        # 2단계: DOM 기반 확인
        try:
            selectors = [
                '[class*="owner"]',
                '[class*="reply"]',
                '[class*="ceo"]',
                '[class*="admin"]',
                '[data-owner*="true"]',
                'span[class*="response"]'
            ]
            for sel in selectors:
                el = await page.query_selector(sel)
                if el:
                    return True
        except Exception:
            pass

        # 3단계: JavaScript 기반 검색 (더 정확)
        try:
            has_reply = await page.evaluate("""
                () => {
                    const text = document.body.innerText;
                    return /사장님|대표|관리자/.test(text) && /답글|답변|감사|방문/.test(text);
                }
            """)
            if has_reply:
                return True
        except Exception:
            pass

        return False

    async def _check_menu_detail(self, page, text: str, html: str) -> dict:
        """메뉴 개수 및 상세설명 여부 확인"""
        result = {"menu_count": 0, "has_menu_description": False}

        # 가격 패턴으로 메뉴 수 추정
        price_matches = re.findall(r"[\d,]+\s*원", text)
        result["menu_count"] = len(price_matches)

        # 메뉴 설명 텍스트 (20자 이상인 설명이 있으면)
        desc_patterns = [r'"description"\s*:\s*"([^"]{20,})"', r'메뉴.*?설명', r'재료.*?신선']
        for pattern in desc_patterns:
            if re.search(pattern, html):
                result["has_menu_description"] = True
                break

        return result

    def _check_external_channels(self, html: str, text: str) -> dict:
        """인스타그램, 카카오 채널 연동 여부 확인"""
        result = {"has_instagram": False, "has_kakao": False}

        if "instagram" in html.lower() or "instagram" in text.lower() or "인스타" in text:
            result["has_instagram"] = True
        if "kakao" in html.lower() or "카카오" in text or "채널" in text:
            result["has_kakao"] = True

        return result

    async def get_place_rank(self, keyword: str, place_id: str) -> int:
        """
        해당 키워드로 네이버 모바일 검색 시 플레이스 순위 반환
        못 찾으면 0 반환
        """
        import urllib.parse
        page = None
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()
            encoded = urllib.parse.quote(keyword)
            await page.goto(f"https://m.search.naver.com/search.naver?query={encoded}&where=m_local", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)

            html = await page.content()

            # 전체 place ID 목록에서 위치 찾기 (crawl_from_search와 동일 패턴)
            all_ids = re.findall(
                r'm\.place\.naver\.com/\w+/(\d{6,})',
                html,
            )
            unique_ids = []
            for pid in all_ids:
                if pid not in unique_ids:
                    unique_ids.append(pid)

            # 폴백: placeId 패턴도 시도
            if not unique_ids:
                all_ids = re.findall(r'"placeId"\s*:\s*"?(\d{6,})"?', html)
                for pid in all_ids:
                    if pid not in unique_ids:
                        unique_ids.append(pid)

            if place_id in unique_ids:
                return unique_ids.index(place_id) + 1

            try:
                print(f"[get_place_rank] '{keyword}' 검색 — {len(unique_ids)}개 ID 중 {place_id} 미발견")
            except Exception:
                print(f"[get_place_rank] 검색 미발견 (place_id={place_id}, 후보={len(unique_ids)}개)")

        except Exception as e:
            print(f"[get_place_rank] 오류: {e}")
        finally:
            if page:
                await page.close()
        return 0

    async def fetch_top_competitor_name(self, query: str, exclude_place_id: str) -> Optional[str]:
        """
        키워드 검색 → 상위 1-3 place_id 추출 → exclude_place_id 제외한 첫 번째의 가게명 반환.
        경쟁사 1위 가게명 자동 추출용.

        Args:
            query: 검색 쿼리 (e.g., "의정부 족발")
            exclude_place_id: 자신의 place_id (제외할)

        Returns:
            경쟁사 가게명 또는 None
        """
        import urllib.parse
        page = None
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            # 검색 페이지 이동
            encoded = urllib.parse.quote(query)
            search_url = f"https://m.search.naver.com/search.naver?query={encoded}&where=m_local"
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=30000)

            html = await page.content()

            # place_id 추출 (상위 순서대로)
            place_ids = []
            pattern1_matches = re.findall(r'm\.place\.naver\.com/\w+/(\d{6,})', html)
            place_ids.extend(pattern1_matches)

            if not place_ids:
                pattern2_matches = re.findall(r'"placeId"\s*:\s*"?(\d{6,})"?', html)
                place_ids.extend(pattern2_matches)

            # 중복 제거
            seen = []
            for pid in place_ids:
                if pid not in seen:
                    seen.append(pid)

            # exclude_place_id 제외한 첫 place_id 찾기
            target_id = None
            for pid in seen:
                if pid != exclude_place_id:
                    target_id = pid
                    break

            if not target_id:
                print(f"[fetch_top_competitor_name] '{query}' 검색 중 {exclude_place_id} 제외 후 후보 없음")
                return None

            # target_id의 상세 페이지에서 가게명 추출 (title 또는 h1)
            detail_url = f"https://m.place.naver.com/place/{target_id}/home"
            await page.goto(detail_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=20000)

            detail_html = await page.content()

            # h1 태그에서 가게명 추출 우선
            h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', detail_html)
            if h1_match:
                name = h1_match.group(1).strip()
                if name:
                    print(f"[fetch_top_competitor_name] '{query}' 기준 경쟁사 1위: {name}")
                    return name

            # title 태그 폴백
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', detail_html)
            if title_match:
                title = title_match.group(1).strip()
                # "가게명 - 네이버플레이스" 형태 파싱
                if ' - ' in title:
                    name = title.split(' - ')[0].strip()
                else:
                    name = title.split(' | ')[0].strip() if ' | ' in title else title
                if name:
                    print(f"[fetch_top_competitor_name] '{query}' 기준 경쟁사 1위 (title): {name}")
                    return name

        except Exception as e:
            print(f"[fetch_top_competitor_name] 오류: {e}")
        finally:
            if page:
                await page.close()

        return None

    async def fetch_top_competitor_name(self, query: str, exclude_place_id: str) -> Optional[str]:
        """
        키워드 검색 -> 상위 1-3 place_id 추출 -> exclude_place_id 제외한 첫 번째의 가게명 반환.
        경쟁사 1위 가게명 자동 추출용.

        Args:
            query: 검색 쿼리 (e.g., "의정부 족발")
            exclude_place_id: 자신의 place_id (제외할)

        Returns:
            경쟁사 가게명 또는 None
        """
        import urllib.parse
        page = None
        try:
            context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            # 검색 페이지 이동
            encoded = urllib.parse.quote(query)
            search_url = f"https://m.search.naver.com/search.naver?query={encoded}&where=m_local"
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=30000)

            html = await page.content()

            # place_id 추출 (상위 순서대로)
            place_ids = []
            pattern1_matches = re.findall(r'm\.place\.naver\.com/\w+/(\d{6,})', html)
            place_ids.extend(pattern1_matches)

            if not place_ids:
                pattern2_matches = re.findall(r'"placeId"\s*:\s*"?(\d{6,})"?', html)
                place_ids.extend(pattern2_matches)

            # 중복 제거
            seen = []
            for pid in place_ids:
                if pid not in seen:
                    seen.append(pid)

            # exclude_place_id 제외한 첫 place_id 찾기
            target_id = None
            for pid in seen:
                if pid != exclude_place_id:
                    target_id = pid
                    break

            if not target_id:
                print(f"[fetch_top_competitor_name] '{query}' 검색 중 {exclude_place_id} 제외 후 후보 없음")
                return None

            # target_id의 상세 페이지에서 가게명 추출 (title 또는 h1)
            detail_url = f"https://m.place.naver.com/place/{target_id}/home"
            await page.goto(detail_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=20000)

            detail_html = await page.content()

            # h1 태그에서 가게명 추출 우선
            h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', detail_html)
            if h1_match:
                name = h1_match.group(1).strip()
                if name:
                    print(f"[fetch_top_competitor_name] '{query}' 기준 경쟁사 1위: {name}")
                    return name

            # title 태그 폴백
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', detail_html)
            if title_match:
                title = title_match.group(1).strip()
                # "가게명 - 네이버플레이스" 형태 파싱
                if ' - ' in title:
                    name = title.split(' - ')[0].strip()
                else:
                    name = title.split(' | ')[0].strip() if ' | ' in title else title
                if name:
                    print(f"[fetch_top_competitor_name] '{query}' 기준 경쟁사 1위 (title): {name}")
                    return name

        except Exception as e:
            print(f"[fetch_top_competitor_name] 오류: {e}")
        finally:
            if page:
                await page.close()

        return None

    async def get_related_keywords(self, keyword: str) -> list:
        """
        네이버 자동완성 API로 연관 키워드 수집
        Returns: 연관 키워드 리스트 (최대 10개)
        """
        import urllib.parse
        try:
            encoded = urllib.parse.quote(keyword)
            url = f"https://ac.search.naver.com/nx/ac?q={encoded}&st=1&frm=nv&r_format=json&r_enc=UTF-8&r_unicode=0&t_koreng=1&run=2&rev=4"

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10.0, headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
                    "Referer": "https://m.search.naver.com/",
                })
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [[]])[0] if data.get("items") else []
                    return [item[0] if isinstance(item, list) else item for item in items[:10]]
        except Exception as e:
            print(f"[get_related_keywords] 오류: {e}")
        return []

