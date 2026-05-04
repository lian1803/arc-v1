"""
지역 벤치마크 크롤러
같은 카테고리+지역의 상위 N개 업체를 크롤링해서 실제 경쟁 수치 반환.
캐시 유효기간 7일.
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)


class LocalBenchmark:
    def __init__(self, browser):
        self.browser = browser

    def _cache_path(self, category: str, region: str) -> Path:
        safe = f"{category}_{region}".replace(" ", "_").replace("/", "_")
        return CACHE_DIR / f"benchmark_{safe}.json"

    def _load_cache(self, category: str, region: str) -> Optional[Dict]:
        path = self._cache_path(category, region)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(data["cached_at"])
            if datetime.now() - cached_at < timedelta(days=7):
                return data["result"]
        except Exception:
            pass
        return None

    def _save_cache(self, category: str, region: str, result: Dict):
        path = self._cache_path(category, region)
        path.write_text(
            json.dumps(
                {"cached_at": datetime.now().isoformat(), "result": result},
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    async def get_benchmark(
        self, category: str, region: str, top_n: int = 10
    ) -> Dict[str, Any]:
        """
        지역+업종 상위 top_n개 업체 크롤링 → 평균 수치 반환.
        캐시 있으면 캐시 반환.
        """
        cached = self._load_cache(category, region)
        if cached:
            print(f"[Benchmark] 캐시 사용: {region} {category}")
            return cached

        from services.naver_place_crawler import NaverPlaceCrawler

        crawler = NaverPlaceCrawler(self.browser)
        query = f"{region} {category}"
        print(f"[Benchmark] 크롤링 시작: {query} 상위 {top_n}개")

        try:
            # 검색 결과에서 상위 place_id 목록 추출
            place_ids = await self._get_top_place_ids(crawler, query, top_n)
            if not place_ids:
                return self._fallback(category)

            stats = []
            for pid in place_ids[:top_n]:
                try:
                    data = await crawler.crawl_place_detail(pid)
                    if data:
                        stats.append({
                            "review_count": (
                                data.get("visitor_review_count", 0) +
                                data.get("receipt_review_count", 0)
                            ),
                            "photo_count": data.get("photo_count", 0),
                            "blog_count": data.get("blog_review_count", 0),
                            "has_news": data.get("has_news", False),
                            "has_booking": data.get("has_booking", False),
                        })
                except Exception as e:
                    print(f"[Benchmark] {pid} 실패: {e}")

            if not stats:
                return self._fallback(category)

            # 통계 계산
            reviews = sorted([s["review_count"] for s in stats], reverse=True)
            photos = sorted([s["photo_count"] for s in stats], reverse=True)
            blogs = sorted([s["blog_count"] for s in stats], reverse=True)

            def avg(lst): return round(sum(lst) / len(lst)) if lst else 0
            def top3_avg(lst): return avg(lst[:3])

            result = {
                "region": region,
                "category": category,
                "sample_size": len(stats),
                "avg_review": avg(reviews),
                "avg_photo": avg(photos),
                "avg_blog": avg(blogs),
                "top3_avg_review": top3_avg(reviews),
                "top3_avg_photo": top3_avg(photos),
                "top10pct_review": (
                    reviews[max(0, len(reviews) // 10)] if reviews else 0
                ),
                "has_news_ratio": round(
                    sum(1 for s in stats if s["has_news"]) / len(stats), 2
                ),
                "has_booking_ratio": round(
                    sum(1 for s in stats if s["has_booking"]) / len(stats), 2
                ),
            }

            self._save_cache(category, region, result)
            print(
                f"[Benchmark] 완료: 평균 리뷰 {result['avg_review']}개, "
                f"평균 사진 {result['avg_photo']}장"
            )
            return result

        except Exception as e:
            print(f"[Benchmark] 크롤링 실패: {e}")
            return self._fallback(category)

    async def _get_top_place_ids(
        self, crawler, query: str, top_n: int
    ) -> list:
        """
        검색 결과에서 상위 place_id 목록 추출.
        새 메서드 extract_top_place_ids 사용 → 상위 N개 place_id 모두 반환.
        """
        try:
            return await crawler.extract_top_place_ids(query, top_n)
        except Exception as e:
            print(f"[Benchmark] place_id 추출 실패: {e}")
            return []

    def _fallback(self, category: str) -> Dict:
        """크롤링 실패 시 폴백 (config/industry_weights.py 기준값)"""
        from config.industry_weights import get_competitor_fallback

        fb = get_competitor_fallback(category)
        return {
            "avg_review": fb["avg_review"],
            "avg_photo": fb["avg_photo"],
            "avg_blog": fb["avg_blog"],
            "top3_avg_review": fb["avg_review"] * 2,
            "top3_avg_photo": fb["avg_photo"] * 2,
            "sample_size": 0,
            "has_news_ratio": 0.3,
            "has_booking_ratio": 0.2,
        }
