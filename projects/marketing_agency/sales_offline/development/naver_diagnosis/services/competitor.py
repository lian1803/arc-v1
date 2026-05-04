"""
경쟁사 비교 크롤링 (경량 버전)
- 같은 키워드 검색 결과 페이지에서 상위 5개 업체 요약만 수집
- 상세 페이지 진입 없음 (빠르고 차단 위험 낮음)
- 실패 시 업종별 고정 평균값으로 폴백
"""
import asyncio
import re
from typing import Dict, Any, List, Optional

from playwright.async_api import Browser

from config.industry_weights import get_competitor_fallback, detect_industry


class CompetitorAnalyzer:
    """경쟁사 비교 분석기 (경량)"""

    def __init__(self, browser: Browser):
        self.browser = browser

    async def get_competitor_summary(
        self,
        keyword: str,
        category: str = "",
        timeout_ms: int = 12000,
    ) -> Dict[str, Any]:
        """
        키워드 검색 결과 상위 5개 업체 요약 수집.
        성공 시 실제 데이터, 실패 시 폴백 값 반환.

        Returns:
            {
                "avg_review": int,
                "avg_photo": int,
                "avg_blog": int,
                "top_review": int,
                "competitors": [...],
                "is_fallback": bool,
            }
        """
        try:
            result = await asyncio.wait_for(
                self._crawl_search_results(keyword),
                timeout=timeout_ms / 1000,
            )
            if result and result.get("competitors"):
                return result
        except asyncio.TimeoutError:
            print(f"[Competitor] 타임아웃: {keyword}")
        except Exception as e:
            print(f"[Competitor] 오류: {e}")

        # 폴백: 업종별 고정 평균
        return self._get_fallback(category)

    async def _crawl_search_results(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        네이버 플레이스 검색 결과 페이지에서 상위 5개 업체 수집.
        상세 페이지 진입 없이 목록 페이지 정보만 파싱.
        """
        import urllib.parse
        context = None
        page = None
        try:
            context = await self.browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
                ),
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            encoded = urllib.parse.quote(keyword)
            url = f"https://m.map.naver.com/search2/search.naver?query={encoded}&type=SITE_1"
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            await page.wait_for_timeout(2500)

            # 업체 목록 파싱
            competitors = await page.evaluate("""
                () => {
                    const items = [];
                    // 모바일 플레이스 검색 결과 셀렉터
                    const cards = document.querySelectorAll('._3StCU, .VH7TP, .place_bluelink, li._item, .CHC5F');
                    cards.forEach((card, idx) => {
                        if (idx >= 5) return;
                        const nameEl = card.querySelector('._3StCU span, .OWo9H, .YzBgS, .place_bluelink, ._HeAo');
                        const reviewEl = card.querySelector('._3ugBU, .orXYY, .DkHLe, [class*="review"]');
                        const name = nameEl ? nameEl.innerText.trim() : '';
                        const reviewText = reviewEl ? reviewEl.innerText.trim() : '';
                        const reviewMatch = reviewText.match(/[0-9,]+/);
                        const reviewCount = reviewMatch ? parseInt(reviewMatch[0].replace(/,/g, '')) : 0;
                        if (name) {
                            items.push({name, review_count: reviewCount});
                        }
                    });
                    return items;
                }
            """)

            if not competitors or len(competitors) == 0:
                # 대안 셀렉터 시도
                competitors = await page.evaluate("""
                    () => {
                        const items = [];
                        const allText = document.body.innerText;
                        return items;
                    }
                """)

            # 유효한 결과 필터
            valid = [c for c in (competitors or []) if c.get("name")]

            if not valid:
                return None

            review_counts = [c.get("review_count", 0) for c in valid]
            avg_review = int(sum(review_counts) / len(review_counts)) if review_counts else 0
            top_review = max(review_counts) if review_counts else 0

            return {
                "avg_review": avg_review,
                "avg_photo": 0,   # 목록 페이지에서 사진 수 파싱 어려움
                "avg_blog": 0,
                "top_review": top_review,
                "competitors": valid,
                "is_fallback": False,
            }

        except Exception as e:
            print(f"[Competitor] 크롤링 내부 오류: {e}")
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

    def _get_fallback(self, category: str) -> Dict[str, Any]:
        """업종별 고정 평균값 반환."""
        fb = get_competitor_fallback(category)
        return {
            "avg_review": fb["avg_review"],
            "avg_photo": fb["avg_photo"],
            "avg_blog": fb["avg_blog"],
            "top_review": fb["top_review"],
            "competitors": [],
            "is_fallback": True,
        }

    async def get_rank_in_search(
        self,
        business_name: str,
        keyword: str,
        timeout_ms: int = 10000,
    ) -> int:
        """
        키워드 검색 결과에서 해당 업체 순위 반환.
        찾지 못하면 0 반환.
        """
        context = None
        page = None
        try:
            import urllib.parse
            context = await self.browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
                ),
                viewport={"width": 390, "height": 844},
                locale="ko-KR",
            )
            page = await context.new_page()

            encoded = urllib.parse.quote(keyword)
            url = f"https://m.map.naver.com/search2/search.naver?query={encoded}&type=SITE_1"
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(2000)

            safe_name = business_name.replace("'", "\\'")
            rank = await page.evaluate(f"""
                () => {{
                    const target = '{safe_name}';
                    const cards = document.querySelectorAll('li._item, .VH7TP, ._3StCU, .CHC5F');
                    for (let i = 0; i < cards.length; i++) {{
                        const text = cards[i].innerText || '';
                        if (text.includes(target)) {{
                            return i + 1;
                        }}
                    }}
                    return 0;
                }}
            """)

            return int(rank) if rank else 0

        except Exception as e:
            print(f"[Competitor] 순위 조회 오류: {e}")
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
