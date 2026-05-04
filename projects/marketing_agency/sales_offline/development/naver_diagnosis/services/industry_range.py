"""
업종별 range 데이터 제공자
벤치마크 실데이터 기반 (benchmark_premium 84건 레코드) → 업계 평균 range 계산
"""
from typing import Dict, Any, Optional, List
from statistics import quantiles, mean
from collections import defaultdict
from datetime import datetime


class IndustryRangeProvider:
    """
    벤치마크 데이터 기반 업종별 range 제공.
    메모리 캐시로 빠른 조회.

    반환 형식:
    {
        'unit_price_range': (40000, 70000),
        'top_review_range': (50, 120),
        'top_photo_range': (15, 30),
        'monthly_new_revenue_range': (2000000, 4000000),
        'source': '업계 평균 (N건 기반)',
    }
    """

    def __init__(self):
        self.range_cache: Dict[str, Dict[str, Any]] = {}
        self.loaded = False
        self._load_fallback()  # 동기 폴백 데이터 로드

    def _load_fallback(self):
        """동기 로드: 벤치마크 폴백 데이터 로드 (DB 없을 때 사용)."""
        # 벤치마크 데이터가 없으면 기본값 사용
        # 이는 HtmlPdfGenerator가 DB 초기화 전에도 작동하도록 함
        from config.industry_weights import INDUSTRY_WEIGHTS, get_avg_price

        # 주요 업종에 대해 현실적 range 설정 (벤치마크 대체)
        for industry in INDUSTRY_WEIGHTS.keys():
            if industry != "default":
                unit_price = get_avg_price(industry)

                # 객단가 range: ±20%
                low_price = int(unit_price * 0.8)
                high_price = int(unit_price * 1.2)

                # 리뷰 range: 업종별 현실적 추정
                # 식당(25K): 20~50 리뷰, 미용실(65K): 30~80 리뷰
                if unit_price < 30000:  # 저가 (식당, 카페)
                    review_low, review_high = 15, 50
                elif unit_price < 100000:  # 중가 (미용, 네일)
                    review_low, review_high = 25, 80
                else:  # 고가 (치과, 학원)
                    review_low, review_high = 10, 40

                # 월 신규 매출 range (중위 리뷰 × 객단가)
                monthly_low = int((review_low + review_high) / 2 * low_price)
                monthly_high = int(review_high * high_price * 1.2)

                self.range_cache[industry] = {
                    "sample_size": 0,  # 폴백 데이터 표시
                    "unit_price": unit_price,
                    "unit_price_range": (low_price, high_price),
                    "review_range": (review_low, review_high),
                    "photo_range": (8, 20),
                    "blog_range": (3, 10),
                    "top_review_range": (review_low * 1.5, review_high * 2.5),
                    "top_photo_range": (15, 35),
                    "monthly_new_revenue_range": (monthly_low, monthly_high),
                    "source": "기본값",
                }

    async def load(self, session):
        """DB에서 벤치마크 데이터 로드 및 range 계산."""
        from models import BenchmarkPremium
        from sqlalchemy import select
        from config.industry_weights import detect_industry

        try:
            # 전체 레코드 로드
            result = await session.execute(select(BenchmarkPremium))
            records = result.scalars().all()
        except Exception as e:
            # DB 테이블이 없으면 폴백 사용
            print(f"[IndustryRangeProvider] DB 로드 실패 (폴백 사용): {e}")
            self.loaded = True
            return

        if not records:
            self.loaded = True
            return

        # 업종별 분류 (detect_industry로 정규화)
        by_industry = defaultdict(list)
        for record in records:
            industry = detect_industry(record.category or "default")
            by_industry[industry].append(record)

        # 업종별 range 계산
        for industry in sorted(by_industry.keys()):
            records_for_ind = by_industry[industry]
            count = len(records_for_ind)

            if count < 3:
                # 샘플이 너무 적으면 스킵 (신뢰도 낮음)
                continue

            # 데이터 추출
            photos = [r.photo_count or 0 for r in records_for_ind]
            total_reviews = [
                (r.visitor_review_count or 0) + (r.receipt_review_count or 0)
                for r in records_for_ind
            ]
            blogs = [r.blog_review_count or 0 for r in records_for_ind]

            # 계산: 25~75 percentile (IQR = Interquartile Range)
            # 이는 "중간 50%"의 범위이므로, "일반적" 업체의 범위를 나타냄
            review_range = self._calc_range(total_reviews)
            photo_range = self._calc_range(photos)
            blog_range = self._calc_range(blogs)

            # 객단가 range
            # 업체당 월 매출 추정 = 리뷰 수 × 평균 티켓 가격
            # 하지만 여기서는 간단히 업종별 기본값으로 통일 (후속 고도화 가능)
            from config.industry_weights import get_avg_price

            unit_price = get_avg_price(industry)

            # 월 신규 매출 range = 상위 경쟁사 리뷰 × 객단가
            # 상위 25%(p75)의 리뷰 × 객단가를 "상위 매장 월 매출" 추정
            if review_range[1] > 0:
                # high: 상위 75% 리뷰 × 객단가
                monthly_high = int(review_range[1] * unit_price)
                # low: 중위 50% 리뷰 × 객단가
                monthly_low = int(review_range[0] * unit_price)
            else:
                monthly_low = monthly_high = 0

            # range_cache에 저장
            self.range_cache[industry] = {
                "sample_size": count,
                "unit_price": unit_price,
                "unit_price_range": (unit_price * 8 // 10, unit_price * 12 // 10),  # ±20%
                "review_range": review_range,
                "photo_range": photo_range,
                "blog_range": blog_range,
                "top_review_range": (review_range[0] * 2, review_range[1] * 3),  # 상위 경쟁사 추정
                "top_photo_range": (photo_range[0] * 2, photo_range[1] * 2),
                "monthly_new_revenue_range": (monthly_low, monthly_high),
                "source": f"업계 평균 ({count}건 기반)",
            }

        self.loaded = True

    def _calc_range(self, data: List[int]) -> tuple:
        """
        25~75 percentile (IQR) 계산.
        반환: (p25, p75)
        """
        if not data:
            return (0, 0)
        if len(data) == 1:
            return (data[0], data[0])
        if len(data) == 2:
            return (min(data), max(data))

        try:
            q4 = quantiles(data, n=4)
            return (int(q4[0]), int(q4[2]))
        except Exception:
            # 데이터 부족 시 min/max 사용
            return (min(data), max(data))

    def get_industry_range(self, category: str) -> Optional[Dict[str, Any]]:
        """
        업종별 실측 기반 range 반환.
        category가 '기타'/None/데이터 없음 → None 반환.

        반환 형식:
        {
            'unit_price_range': (40000, 70000),
            'top_review_range': (50, 120),
            'top_photo_range': (15, 30),
            'monthly_new_revenue_range': (2000000, 4000000),
            'source': '업계 평균 (N건 기반)',
        }
        """
        if not category or category in ("기타", "", None):
            return None

        from config.industry_weights import detect_industry

        industry = detect_industry(category)

        if industry == "default":
            # "default"는 데이터가 명확하지 않으므로 범용 데이터도 없으면 None
            # 또는 모든 업체의 전체 평균을 사용할 수도 있음
            # 여기서는 None으로 처리 (숨김)
            return None

        return self.range_cache.get(industry)

    def get_category_stats(self, industry_key: str) -> Optional[Dict[str, Any]]:
        """산업별 전체 통계 반환 (디버그/분석용)."""
        return self.range_cache.get(industry_key)

    def all_ranges(self) -> Dict[str, Dict[str, Any]]:
        """전체 캐시 데이터 반환 (디버그용)."""
        return self.range_cache


# 글로벌 인스턴스
_provider: Optional["IndustryRangeProvider"] = None


async def init_provider(session) -> IndustryRangeProvider:
    """앱 시작 시 호출: 인더스트리 range 데이터 로드."""
    global _provider
    _provider = IndustryRangeProvider()
    await _provider.load(session)
    return _provider


def get_provider() -> Optional[IndustryRangeProvider]:
    """로드된 range 제공자 반환. lazy init 지원."""
    global _provider
    if _provider is None:
        # 처음 호출 시 폴백 데이터로 초기화
        _provider = IndustryRangeProvider()
    return _provider


def set_provider(provider: IndustryRangeProvider):
    """range 제공자 설정 (테스트용)."""
    global _provider
    _provider = provider
