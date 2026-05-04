"""
경쟁사 비교 크롤링 — API 인터셉트 방식
- m.search.naver.com 검색 결과에서 place_id 목록 추출 (정규식 기반)
- 상위 5개 업체 각각 개별 페이지 방문 → JSON API 인터셉트로 리뷰/사진/블로그 수집
- CSS 셀렉터 미사용 (레이아웃 변경에 무관)
- 실패 시 업종별 고정 평균값 폴백
"""
import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Tuple

from playwright.async_api import Browser

from config.industry_weights import get_competitor_fallback


def _deep_get(obj, *keys):
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


def _deep_find_lists(obj, depth: int = 0) -> List[list]:
    """JSON 트리에서 장소 배열처럼 보이는 리스트를 재귀 탐색."""
    if depth > 6 or obj is None:
        return []
    results = []
    NAME_KEYS = {"name", "businessName", "title", "plName", "placeName", "storeName"}
    REVIEW_KEYS = {
        "visitorReviewCount", "reviewCount", "ratingCount",
        "receiptReviewCount", "ogVisitReviewCount",
    }
    if isinstance(obj, list) and len(obj) >= 2:
        if isinstance(obj[0], dict):
            keys = set(obj[0].keys())
            if keys & NAME_KEYS and keys & REVIEW_KEYS:
                results.append(obj)
    if isinstance(obj, dict):
        for v in obj.values():
            results.extend(_deep_find_lists(v, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                results.extend(_deep_find_lists(item, depth + 1))
    return results


class CompetitorAnalyzer:
    """경쟁사 비교 분석기 — API 인터셉트 방식"""

    _MOBILE_UA = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )

    def __init__(self, browser: Browser):
        self.browser = browser

    # ──────────────────────────────────────────────────────────
    # 공개 API
    # ──────────────────────────────────────────────────────────

    async def get_competitor_summary(
        self,
        keyword: str,
        category: str = "",
        timeout_ms: int = 45000,
    ) -> Dict[str, Any]:
        """
        키워드 검색 상위 경쟁사 요약 수집.

        Returns:
            {
                "avg_review": int,
                "avg_photo": int,
                "avg_blog": int,
                "top_review": int,
                "competitors": [
                    {"name": str, "place_id": str, "review_count": int,
                     "photo_count": int, "blog_count": int}
                ],
                "is_fallback": bool,
            }
        """
        try:
            result = await asyncio.wait_for(
                self._crawl_competitors(keyword),
                timeout=timeout_ms / 1000,
            )
            if result and len(result.get("competitors", [])) >= 2:
                print(f"[Competitor] 실제 데이터 {len(result['competitors'])}개: {[c['name'] for c in result['competitors']]}")
                return result
            print(f"[Competitor] 수집 부족({len((result or {}).get('competitors', []))}개) → 폴백")
        except asyncio.TimeoutError:
            print(f"[Competitor] 타임아웃: {keyword}")
        except Exception as e:
            print(f"[Competitor] 오류: {e}")

        return self._get_fallback(category)

    async def get_rank_in_search(
        self,
        business_name: str,
        keyword: str,
        timeout_ms: int = 15000,
    ) -> int:
        """키워드 검색 결과에서 업체 순위 반환. 미발견 시 0."""
        try:
            return await asyncio.wait_for(
                self._find_rank(business_name, keyword),
                timeout=timeout_ms / 1000,
            )
        except Exception as e:
            print(f"[Competitor] 순위 조회 오류: {e}")
            return 0

    # ──────────────────────────────────────────────────────────
    # 내부 구현
    # ──────────────────────────────────────────────────────────

    async def _crawl_competitors(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        1단계: 검색 결과 페이지에서 place_id 목록 + 이름 추출
        2단계: 상위 5개 place_id 개별 방문 → API 인터셉트로 수치 수집
        """
        import urllib.parse

        context = None
        page = None
        try:
            context = await self.browser.new_context(
                user_agent=self._MOBILE_UA,
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            # ── 1단계: 검색 결과 페이지 로드 ──────────────────
            encoded = urllib.parse.quote(keyword)
            search_url = (
                f"https://m.search.naver.com/search.naver"
                f"?query={encoded}&where=m_local"
            )
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2500)

            html = await page.content()

            # place_id 목록 추출 (정규식 — CSS 셀렉터 미사용)
            all_ids = re.findall(r'm\.place\.naver\.com/\w+/(\d{6,})', html)
            seen_ids: List[str] = []
            for pid in all_ids:
                if pid not in seen_ids:
                    seen_ids.append(pid)

            if not seen_ids:
                print(f"[Competitor] place_id 없음: {keyword}")
                return None

            # 업체명 추출: place_id 주변 텍스트에서 파싱
            names_by_id = self._extract_names_from_html(html, seen_ids)

            top_ids = seen_ids[:5]
            print(f"[Competitor] 검색 결과 place_id {len(seen_ids)}개, 상위 {len(top_ids)}개 수집")

            await page.close()
            page = None
            await context.close()
            context = None

            # ── 2단계: 각 place_id 개별 방문 ──────────────────
            competitors = []
            for pid in top_ids:
                summary = await self._get_place_summary(pid)
                if summary:
                    # 이름이 없으면 검색 결과 HTML에서 추출한 이름 사용
                    if not summary.get("name") and names_by_id.get(pid):
                        summary["name"] = names_by_id[pid]
                    if summary.get("name"):
                        competitors.append(summary)
                        print(
                            f"[Competitor] [{summary['name']}] "
                            f"리뷰={summary['review_count']} "
                            f"사진={summary['photo_count']} "
                            f"블로그={summary['blog_count']}"
                        )

            if not competitors:
                return None

            review_counts = [c["review_count"] for c in competitors]
            photo_counts = [c["photo_count"] for c in competitors]
            blog_counts = [c["blog_count"] for c in competitors]

            def _safe_avg(lst):
                vals = [v for v in lst if v > 0]
                return int(sum(vals) / len(vals)) if vals else 0

            return {
                "avg_review": _safe_avg(review_counts),
                "avg_photo": _safe_avg(photo_counts),
                "avg_blog": _safe_avg(blog_counts),
                "top_review": max(review_counts) if review_counts else 0,
                "top_photo": max(photo_counts) if photo_counts else 0,
                "competitors": competitors,
                "is_fallback": False,
            }

        except Exception as e:
            print(f"[Competitor] _crawl_competitors 오류: {e}")
            return None
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

    async def _get_place_summary(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        개별 place_id 페이지 방문 → api.place.naver.com/graphql 인터셉트로 수치 추출.
        이름은 og:title 메타태그에서 추출.
        """
        context = None
        page = None
        review_count = 0
        photo_count = 0
        place_name: str = ""

        try:
            context = await self.browser.new_context(
                user_agent=self._MOBILE_UA,
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            async def _on_response(response):
                nonlocal review_count, photo_count
                if "api.place.naver.com/graphql" not in response.url:
                    return
                if response.status != 200:
                    return
                try:
                    body = await response.json()
                    items = body if isinstance(body, list) else [body]
                    for item in items:
                        d = item.get("data", {})
                        vrs = d.get("visitorReviewStats")
                        if vrs:
                            rc = (
                                vrs.get("visitorReviewsTotal")
                                or _deep_get(vrs, "review", "totalCount")
                                or 0
                            )
                            if rc:
                                review_count = max(review_count, int(rc))
                            pc = _deep_get(vrs, "review", "imageReviewCount") or 0
                            if pc:
                                photo_count = max(photo_count, int(pc))
                        vr = d.get("visitorReviews")
                        if vr:
                            t = vr.get("total", 0) or 0
                            if t:
                                review_count = max(review_count, int(t))
                except Exception:
                    pass

            page.on("response", _on_response)

            url = f"https://m.place.naver.com/place/{place_id}/home"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)

            # 이름: og:title 메타태그 ("업체명 : 네이버 플레이스" 형식)
            html = await page.content()
            og_match = re.search(
                r'property=["\']og:title["\']\s+content=["\']([^"\']+)["\']',
                html,
            )
            if not og_match:
                og_match = re.search(
                    r'content=["\']([^"\']+)["\']\s+property=["\']og:title["\']',
                    html,
                )
            if og_match:
                val = og_match.group(1)
                place_name = val.split(" : ")[0].strip() if " : " in val else val.strip()
                # 제네릭 타이틀 제거
                if place_name in ("네이버 플레이스", "Naver Place", ""):
                    place_name = ""

            # 폴백: 페이지 타이틀
            if not place_name:
                try:
                    title = await page.title()
                    if title and " : " in title:
                        place_name = title.split(" : ")[0].strip()
                    elif title and title not in ("네이버 플레이스", "Naver Place"):
                        place_name = title.strip()
                except Exception:
                    pass

            if not place_name:
                return None

            return {
                "place_id": place_id,
                "name": place_name,
                "review_count": review_count,
                "photo_count": photo_count,
                "blog_count": 0,
            }

        except Exception as e:
            print(f"[Competitor] _get_place_summary {place_id} 오류: {e}")
            return None
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

    def _extract_place_data(self, data: Any) -> Dict[str, Any]:
        """JSON 객체에서 리뷰/사진/블로그/이름 추출 (재귀 탐색)."""
        result: Dict[str, Any] = {}

        # 직접 키 탐색
        visitor = (
            _deep_get(data, "visitorReviewCount")
            or _deep_get(data, "reviewCount")
            or _deep_get(data, "review", "visitorReviewCount")
            or _deep_get(data, "summary", "visitorReviewCount")
            or _deep_get(data, "visitor")
        )
        receipt = (
            _deep_get(data, "receiptReviewCount")
            or _deep_get(data, "ogVisitReviewCount")
        )
        blog = (
            _deep_get(data, "blogCafeReviewCount")
            or _deep_get(data, "blogReviewCount")
            or _deep_get(data, "blog")
        )
        photo = (
            _deep_get(data, "photoCount")
            or _deep_get(data, "photo", "count")
        )
        name = (
            _deep_get(data, "name")
            or _deep_get(data, "businessName")
            or _deep_get(data, "title")
            or _deep_get(data, "placeName")
            or _deep_get(data, "storeName")
        )

        if visitor is not None:
            result["review_count"] = int(visitor or 0) + int(receipt or 0)
        if photo is not None:
            result["photo_count"] = int(photo or 0)
        if blog is not None:
            result["blog_count"] = int(blog or 0)
        if name:
            result["name"] = str(name)

        # 배열 내 place 항목 탐색
        if not result:
            lists = _deep_find_lists(data)
            for lst in lists:
                for item in lst[:1]:
                    extracted = self._extract_place_data(item)
                    if extracted:
                        return extracted

        return result

    def _extract_from_next_data(
        self, html: str, place_id: str
    ) -> Tuple[Dict[str, Any], str]:
        """<script id="__NEXT_DATA__"> 에서 place 데이터 추출."""
        match = re.search(
            r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        if not match:
            return {}, ""
        try:
            obj = json.loads(match.group(1))
            data = self._extract_place_data(obj)
            name = data.pop("name", "") or ""
            return data, name
        except Exception:
            return {}, ""

    def _extract_names_from_html(
        self, html: str, place_ids: List[str]
    ) -> Dict[str, str]:
        """
        검색 결과 HTML에서 place_id 주변 텍스트로 업체명 추출.
        og:title, data-place-name 속성, 인접 텍스트 등 시도.
        """
        names: Dict[str, str] = {}

        # data-store-name 또는 data-place-name 속성
        for pid in place_ids:
            pattern = rf'data-(?:store|place)-name=["\']([^"\']+)["\'][^>]*{pid}|{pid}[^>]*data-(?:store|place)-name=["\']([^"\']+)["\']'
            m = re.search(pattern, html)
            if m:
                name = m.group(1) or m.group(2)
                if name:
                    names[pid] = name
                    continue

            # place_id URL 주변 200자에서 한글 업체명 추정
            pattern2 = rf'{pid}.{{0,200}}'
            m2 = re.search(pattern2, html)
            if m2:
                chunk = re.sub(r'<[^>]+>', ' ', m2.group(0))
                korean_words = re.findall(r'[가-힣a-zA-Z0-9]{2,15}', chunk)
                if korean_words:
                    names[pid] = korean_words[0]

        return names

    async def _find_rank(self, business_name: str, keyword: str) -> int:
        """키워드 검색 결과에서 업체 순위 반환. place_id 목록 기반."""
        import urllib.parse

        context = None
        page = None
        try:
            context = await self.browser.new_context(
                user_agent=self._MOBILE_UA,
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            encoded = urllib.parse.quote(keyword)
            url = (
                f"https://m.search.naver.com/search.naver"
                f"?query={encoded}&where=m_local"
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(2000)

            html = await page.content()
            all_ids = re.findall(r'm\.place\.naver\.com/\w+/(\d{6,})', html)
            seen: List[str] = []
            for pid in all_ids:
                if pid not in seen:
                    seen.append(pid)

            # 각 place_id 블록 주변에서 업체명 매칭
            clean = re.sub(r'<[^>]+>', ' ', html)
            name_lower = business_name.lower()
            name_short = name_lower[:4] if len(name_lower) >= 4 else name_lower

            for idx, pid in enumerate(seen):
                positions = [m.start() for m in re.finditer(re.escape(pid), html)]
                if not positions:
                    continue
                pos = positions[0]
                surrounding = clean[max(0, pos - 400): pos + 400].lower()
                if name_short in surrounding:
                    return idx + 1

            return 0

        except Exception as e:
            print(f"[Competitor] _find_rank 오류: {e}")
            return 0
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

    def _get_fallback(self, category: str) -> Dict[str, Any]:
        """업종별 고정 평균값 폴백."""
        fb = get_competitor_fallback(category)
        return {
            "avg_review": fb["avg_review"],
            "avg_photo": fb["avg_photo"],
            "avg_blog": fb["avg_blog"],
            "top_review": fb["top_review"],
            "competitors": [],
            "is_fallback": True,
        }
