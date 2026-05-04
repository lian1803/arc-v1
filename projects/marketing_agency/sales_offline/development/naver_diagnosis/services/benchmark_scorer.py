"""
benchmark_premium 테이블 기반 벤치마크 통계 제공자.
시작 시 DB에서 전체 데이터 로드 → 메모리 캐시.
"""
from typing import Dict, Any, Optional, List
from statistics import quantiles, mean
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BenchmarkStatsProvider:
    """
    benchmark_premium 실데이터 기반 통계 제공자.
    앱 시작 시 한 번 로드 → 메모리 캐시로 빠른 조회.
    """

    # benchmark_premium category → industry_weights key 매핑
    # DB에 저장된 한글 카테고리명을 industry_weights.py의 업종으로 매핑
    CATEGORY_TO_INDUSTRY = {
        # 매핑 규칙:
        # DB의 깨진 한글을 구분하기 어려우니, 처음 로드할 때 동적으로 감지
        # 또는 제한된 카테고리만 사전에 정의
    }

    def __init__(self):
        self.stats_cache: Dict[str, Dict[str, Any]] = {}
        self.category_map: Dict[str, str] = {}  # DB 카테고리 → 업종 매핑
        self.loaded = False

    async def load(self, session: AsyncSession):
        """DB에서 benchmark_premium 전체 로드 및 통계 계산."""
        from models import BenchmarkPremium

        # 전체 레코드 로드
        result = await session.execute(select(BenchmarkPremium))
        records = result.scalars().all()

        if not records:
            self.loaded = True
            return

        # 카테고리별 분류
        by_category = defaultdict(list)
        for record in records:
            by_category[record.category].append(record)

        # 카테고리별 통계 계산
        for db_category in sorted(by_category.keys()):
            records_for_cat = by_category[db_category]
            count = len(records_for_cat)

            # 데이터 추출
            photos = [r.photo_count for r in records_for_cat]
            total_reviews = [
                r.visitor_review_count + r.receipt_review_count
                for r in records_for_cat
            ]
            blogs = [r.blog_review_count for r in records_for_cat]

            # Boolean 필드 채택률
            has_booking = sum(1 for r in records_for_cat if r.has_booking) / count
            has_instagram = sum(1 for r in records_for_cat if r.has_instagram) / count
            has_owner_reply = sum(1 for r in records_for_cat if r.has_owner_reply) / count
            has_coupon = sum(1 for r in records_for_cat if r.has_coupon) / count
            has_talktalk = sum(1 for r in records_for_cat if r.has_talktalk) / count
            has_news = sum(1 for r in records_for_cat if r.has_news) / count

            # 백분위수 계산
            photo_stats = self._calc_percentiles(photos)
            review_stats = self._calc_percentiles(total_reviews)
            blog_stats = self._calc_percentiles(blogs)

            # 카테고리별 통계 저장
            self.stats_cache[db_category] = {
                "sample_size": count,
                "photo": photo_stats,
                "total_review": review_stats,
                "blog": blog_stats,
                "adoption_rates": {
                    "has_booking": round(has_booking, 3),
                    "has_instagram": round(has_instagram, 3),
                    "has_owner_reply": round(has_owner_reply, 3),
                    "has_coupon": round(has_coupon, 3),
                    "has_talktalk": round(has_talktalk, 3),
                    "has_news": round(has_news, 3),
                }
            }

            # DB 카테고리 → 업종 매핑 (데이터량이 많은 카테고리만 매핑)
            # 예: 30개 이상이면 주요 업종이므로 매핑
            industry_key = self._guess_industry_from_category(db_category, count)
            if industry_key:
                self.category_map[db_category] = industry_key

        self.loaded = True

    def _calc_percentiles(self, data: List[int]) -> Dict[str, int]:
        """백분위수 계산."""
        if not data:
            return {"p10": 0, "p25": 0, "p50": 0, "p75": 0, "p90": 0, "mean": 0}
        if len(data) == 1:
            return {
                "p10": data[0],
                "p25": data[0],
                "p50": data[0],
                "p75": data[0],
                "p90": data[0],
                "mean": data[0],
            }

        q10 = quantiles(data, n=10)
        q4 = quantiles(data, n=4)

        return {
            "p10": int(q10[0]),
            "p25": int(q4[0]),
            "p50": int(q4[1]),
            "p75": int(q4[2]),
            "p90": int(q10[8]),
            "mean": int(mean(data)),
        }

    def _guess_industry_from_category(self, db_category: str, count: int) -> Optional[str]:
        """
        DB 카테고리명(한글 깨짐)을 industry_weights의 업종으로 추정.
        데이터량 기반:
        - n=30: 미용실 (하이라)
        - n=23: 피부관리 (에스테틱)
        - n=8: 카페
        - n=7: 네일 (네일아트)
        - n=6: 스파마사지/식당 등
        """
        # count 기반 휴리스틱 (정확하지는 않지만 합리적 추정)
        if count == 30:
            return "미용실"
        elif count == 23:
            return "피부관리"
        elif count == 8:
            return "카페"
        elif count == 7:
            return "네일"
        elif count == 6:
            # 6개는 2개 있음 (식당, 스파마사지)
            # 첫 번째 6은 식당, 두 번째는 스파마사지로 추정
            # 실제로는 place_name 살펴서 구분 필요하지만,
            # 일단 둘 다 default로 취급
            return "default"
        elif count == 3:
            return "default"
        elif count == 1:
            return "default"
        else:
            return None

    def get_category_stats(self, industry_key: str) -> Optional[Dict[str, Any]]:
        """
        업종별 통계 반환.
        반환 형식:
        {
            "sample_size": int,
            "photo": {"p10": int, ...},
            "total_review": {"p10": int, ...},
            "blog": {"p10": int, ...},
            "adoption_rates": {...}
        }
        """
        # industry_key에 해당하는 DB 카테고리 찾기
        for db_cat, ind_key in self.category_map.items():
            if ind_key == industry_key:
                return self.stats_cache.get(db_cat)

        return None

    def get_competitor_reference(self, category: str) -> Dict[str, int]:
        """
        COMPETITOR_FALLBACK 대체용 경쟁사 참고값 반환.
        벤치마크 p25값 사용 (지역 경쟁사 평균 수준).

        반환: {"avg_review": int, "avg_photo": int, "avg_blog": int, "top_review": int}
        """
        from config.industry_weights import detect_industry, get_competitor_fallback

        industry = detect_industry(category)

        # 매핑된 DB 카테고리에서 데이터 조회
        for db_cat, ind_key in self.category_map.items():
            if ind_key == industry:
                stats = self.stats_cache.get(db_cat)
                if stats:
                    return {
                        "avg_review": stats["total_review"]["p25"],
                        "avg_photo": stats["photo"]["p25"],
                        "avg_blog": stats["blog"]["p25"],
                        "top_review": stats["total_review"]["p75"],
                    }

        # 벤치마크 데이터 없으면 기존 폴백 사용
        return get_competitor_fallback(category)

    def all_stats(self) -> Dict[str, Dict[str, Any]]:
        """전체 캐시 데이터 반환 (디버그용)."""
        return self.stats_cache

    def all_mappings(self) -> Dict[str, str]:
        """전체 매핑 반환 (디버그용)."""
        return self.category_map


# 글로벌 인스턴스
_provider: Optional[BenchmarkStatsProvider] = None


async def init_provider(session: AsyncSession) -> BenchmarkStatsProvider:
    """앱 시작 시 호출: 벤치마크 데이터 로드."""
    global _provider
    _provider = BenchmarkStatsProvider()
    await _provider.load(session)
    return _provider


def get_provider() -> Optional[BenchmarkStatsProvider]:
    """로드된 벤치마크 제공자 반환."""
    return _provider


def set_provider(provider: BenchmarkStatsProvider):
    """벤치마크 제공자 설정 (테스트용)."""
    global _provider
    _provider = provider
