"""
네이버 플레이스 진단 점수 산출
각 항목별 점수 계산 및 개선 포인트 생성
7개 항목으로 확장됨 (photo, review, blog, info, keyword, convenience, engagement)

업종별 가중치 자동 적용 (config/industry_weights.py)
새소식 90일+ 패널티, 사장님 답글률, 경쟁사 상대점수 반영
"""
from typing import Dict, List, Any

from config.industry_weights import get_weights, detect_industry


class DiagnosisScorer:
    """진단 점수 산출기"""

    # 기본 점수 가중치 (7개 항목) — 업종 감지 실패 시 폴백
    WEIGHTS = {
        "photo": 0.15,
        "review": 0.20,
        "blog": 0.10,
        "info": 0.15,           # 영업시간+소개+오시는길+메뉴
        "keyword": 0.10,
        "convenience": 0.15,    # 예약+톡톡+스마트콜+쿠폰+새소식
        "engagement": 0.15,     # 사장님답글+외부채널+메뉴상세
    }

    @staticmethod
    def calculate_photo_score(photo_count: int) -> float:
        """
        사진 점수 계산
        0장 -> 0점, 1-4장 -> 40점, 5-9장 -> 70점, 10-14장 -> 85점, 15+장 -> 100점
        """
        if photo_count <= 0:
            return 0.0
        elif photo_count <= 4:
            return 40.0
        elif photo_count <= 9:
            return 70.0
        elif photo_count <= 14:
            return 85.0
        else:
            return 100.0

    @staticmethod
    def calculate_review_score(review_count: int) -> float:
        """
        리뷰 점수 계산 (영수증 + 방문자 리뷰 합계 기준)
        0 -> 0점, 1-9 -> 30점, 10-29 -> 60점, 30-49 -> 80점, 50+ -> 100점
        """
        if review_count <= 0:
            return 0.0
        elif review_count <= 9:
            return 30.0
        elif review_count <= 29:
            return 60.0
        elif review_count <= 49:
            return 80.0
        else:
            return 100.0

    @staticmethod
    def calculate_blog_score(blog_count: int) -> float:
        """
        블로그 리뷰 점수 계산
        0 -> 0점, 1-4 -> 40점, 5-9 -> 70점, 10-19 -> 85점, 20+ -> 100점
        """
        if blog_count <= 0:
            return 0.0
        elif blog_count <= 4:
            return 40.0
        elif blog_count <= 9:
            return 70.0
        elif blog_count <= 19:
            return 85.0
        else:
            return 100.0

    @staticmethod
    def calculate_info_score(
        has_hours: bool,
        has_menu: bool,
        has_price: bool,
        has_intro: bool = False,
        has_directions: bool = False
    ) -> float:
        """
        정보 완성도 점수 계산 (확장)
        영업시간(25점) + 메뉴(25점) + 가격(15점) + 소개(20점) + 오시는길(15점) = 최대 100점
        """
        score = 0.0
        if has_hours:
            score += 25.0
        if has_menu:
            score += 25.0
        if has_price:
            score += 15.0
        if has_intro:
            score += 20.0
        if has_directions:
            score += 15.0
        return min(score, 100.0)

    @staticmethod
    def calculate_keyword_score(keywords: List) -> float:
        """
        키워드 점수 계산
        - 키워드 수만 있는 경우 (문자열): 키워드 개수로 기본 점수
        - 검색량 데이터 있는 경우 (딕셔너리): 검색량 기반 보너스

        키워드 등록 자체가 중요하므로 키워드 수에도 점수 부여:
        0개 -> 0점, 1-2개 -> 20점, 3-4개 -> 40점, 5-6개 -> 60점, 7+개 -> 80점
        검색량 보너스: 1000-4999 -> +10, 5000-9999 -> +15, 10000+ -> +20
        """
        keyword_count = len(keywords)

        if keyword_count == 0:
            return 0.0

        # 기본 점수 (키워드 개수)
        if keyword_count <= 2:
            base_score = 20.0
        elif keyword_count <= 4:
            base_score = 40.0
        elif keyword_count <= 6:
            base_score = 60.0
        else:
            base_score = 80.0

        # 검색량 보너스
        total_volume = sum(kw.get("search_volume", 0) for kw in keywords if isinstance(kw, dict))
        if total_volume >= 10000:
            base_score = min(base_score + 20, 100.0)
        elif total_volume >= 5000:
            base_score = min(base_score + 15, 100.0)
        elif total_volume >= 1000:
            base_score = min(base_score + 10, 100.0)

        return base_score

    @staticmethod
    def calculate_convenience_score(
        has_booking: bool,
        has_talktalk: bool,
        has_smartcall: bool,
        has_coupon: bool,
        has_news: bool
    ) -> float:
        """
        편의기능 점수: 각 항목별 점수 합산 최대 100점
        - 네이버 예약: 25점
        - 톡톡: 20점
        - 스마트콜: 20점
        - 쿠폰: 20점
        - 새소식: 15점
        """
        score = 0.0
        if has_booking:
            score += 25.0
        if has_talktalk:
            score += 20.0
        if has_smartcall:
            score += 20.0
        if has_coupon:
            score += 20.0
        if has_news:
            score += 15.0
        return min(score, 100.0)

    @staticmethod
    def calculate_engagement_score(
        has_owner_reply: bool,
        has_instagram: bool,
        has_kakao: bool,
        has_menu_description: bool
    ) -> float:
        """
        참여도 점수: 사장님답글(40) + 인스타(20) + 카카오(15) + 메뉴상세설명(25) = 최대 100점
        """
        score = 0.0
        if has_owner_reply:
            score += 40.0
        if has_instagram:
            score += 20.0
        if has_kakao:
            score += 15.0
        if has_menu_description:
            score += 25.0
        return min(score, 100.0)

    @classmethod
    def calculate_total_score(
        cls,
        scores: Dict[str, float],
        weights: Dict[str, float] = None,
    ) -> float:
        """
        총점 계산 (가중 평균).
        weights가 주어지면 업종별 가중치 사용, 없으면 기본 WEIGHTS 사용.
        """
        w = weights if weights else cls.WEIGHTS
        total = 0.0
        total += scores.get("photo", 0) * w.get("photo", cls.WEIGHTS["photo"])
        total += scores.get("review", 0) * w.get("review", cls.WEIGHTS["review"])
        total += scores.get("blog", 0) * w.get("blog", cls.WEIGHTS["blog"])
        total += scores.get("info", 0) * w.get("info", cls.WEIGHTS["info"])
        total += scores.get("keyword", 0) * w.get("keyword", cls.WEIGHTS["keyword"])
        total += scores.get("convenience", 0) * w.get("convenience", cls.WEIGHTS["convenience"])
        total += scores.get("engagement", 0) * w.get("engagement", cls.WEIGHTS["engagement"])
        return round(total, 1)

    @staticmethod
    def apply_news_penalty(convenience_score: float, news_last_days: int) -> float:
        """
        새소식 90일+ 미업데이트 패널티.
        편의기능 점수에서 감점 (최대 -15점).
        90일~180일: -8점, 180일+: -15점
        """
        if news_last_days <= 0:
            return convenience_score
        if news_last_days >= 180:
            return max(0.0, convenience_score - 15.0)
        if news_last_days >= 90:
            return max(0.0, convenience_score - 8.0)
        return convenience_score

    @staticmethod
    def apply_owner_reply_rate(engagement_score: float, reply_rate: float) -> float:
        """
        사장님 답글률 반영 (최근 10개 리뷰 기준).
        reply_rate: 0.0 ~ 1.0
        0% → -10점, 50% → 0점, 100% → +5점 보너스
        """
        if reply_rate >= 1.0:
            return min(100.0, engagement_score + 5.0)
        elif reply_rate >= 0.5:
            return engagement_score
        elif reply_rate > 0:
            penalty = (0.5 - reply_rate) * 20  # 최대 -10점
            return max(0.0, engagement_score - penalty)
        else:
            return max(0.0, engagement_score - 10.0)

    @staticmethod
    def apply_competitor_bonus(score: float, my_val: int, competitor_avg: int) -> float:
        """
        경쟁사 대비 상대 점수 보너스/패널티.
        경쟁사 평균의 2배 이상: +5점 보너스
        경쟁사 평균의 절반 미만: -5점 패널티
        """
        if competitor_avg <= 0 or my_val <= 0:
            return score
        ratio = my_val / competitor_avg
        if ratio >= 2.0:
            return min(100.0, score + 5.0)
        elif ratio < 0.5:
            return max(0.0, score - 5.0)
        return score

    @staticmethod
    def calculate_grade(total_score: float) -> str:
        """
        등급 산출
        A: 80+, B: 60-79, C: 40-59, D: 0-39
        """
        if total_score >= 80:
            return "A"
        elif total_score >= 60:
            return "B"
        elif total_score >= 40:
            return "C"
        else:
            return "D"

    @staticmethod
    def generate_improvement_points(data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        개선 포인트 자동 생성 (최대 5개).
        원칙: "이 항목이 비어있어요" 수준만. "이렇게 하세요"는 표시하지 않는다.

        Args:
            data: 진단 데이터

        Returns:
            개선 포인트 리스트 [{"category": "photo", "message": "...", "priority": 1}]
        """
        points = []

        # 사진 관련
        photo_count = data.get("photo_count", 0)
        if photo_count == 0:
            points.append({
                "category": "photo",
                "priority": 1,
                "message": "사진 0장 — 이 항목이 비어있어요.",
            })
        elif photo_count < 5:
            points.append({
                "category": "photo",
                "priority": 2,
                "message": f"사진 {photo_count}장 — 기준치 미달이에요.",
            })
        elif photo_count < 15:
            points.append({
                "category": "photo",
                "priority": 3,
                "message": f"사진 {photo_count}장 — 보완이 필요해요.",
            })

        # 리뷰 관련
        review_count = data.get("review_count", 0)
        if review_count == 0:
            points.append({
                "category": "review",
                "priority": 1,
                "message": "리뷰 0개 — 이 항목이 비어있어요.",
            })
        elif review_count < 10:
            points.append({
                "category": "review",
                "priority": 2,
                "message": f"리뷰 {review_count}개 — 기준치 미달이에요.",
            })
        elif review_count < 30:
            points.append({
                "category": "review",
                "priority": 3,
                "message": f"리뷰 {review_count}개 — 보완이 필요해요.",
            })

        # 블로그 리뷰 관련
        blog_count = data.get("blog_review_count", 0)
        if blog_count == 0:
            points.append({
                "category": "blog",
                "priority": 2,
                "message": "블로그 리뷰 0개 — 이 항목이 비어있어요.",
            })
        elif blog_count < 5:
            points.append({
                "category": "blog",
                "priority": 3,
                "message": f"블로그 리뷰 {blog_count}개 — 기준치 미달이에요.",
            })

        # 정보 완성도 관련 — 비어있는 항목만 나열
        info_missing = []
        if not data.get("has_hours", False):
            info_missing.append("영업시간")
        if not data.get("has_menu", False):
            info_missing.append("메뉴")
        if not data.get("has_price", False):
            info_missing.append("가격정보")
        if not data.get("has_intro", False):
            info_missing.append("소개글")
        if not data.get("has_directions", False):
            info_missing.append("오시는 길")

        if info_missing:
            missing_str = ", ".join(info_missing)
            points.append({
                "category": "info",
                "priority": 1 if len(info_missing) >= 3 else 2,
                "message": f"기본 정보 미완성 — [{missing_str}] 항목이 비어있어요.",
            })

        # 키워드 관련
        keywords = data.get("keywords", [])
        total_volume = 0
        for kw in keywords:
            if isinstance(kw, dict):
                total_volume += kw.get("search_volume", 0)
        if total_volume == 0:
            points.append({
                "category": "keyword",
                "priority": 2,
                "message": "키워드 검색량 0 — 이 항목이 비어있어요.",
            })
        elif total_volume < 1000:
            points.append({
                "category": "keyword",
                "priority": 3,
                "message": "키워드 노출이 부족해요.",
            })

        # 편의기능 관련
        convenience_missing = []
        if not data.get("has_booking", False):
            convenience_missing.append("네이버 예약")
        if not data.get("has_talktalk", False):
            convenience_missing.append("톡톡")
        if not data.get("has_coupon", False):
            convenience_missing.append("쿠폰")
        if not data.get("has_news", False):
            convenience_missing.append("새소식")

        if len(convenience_missing) >= 2:
            missing_str = ", ".join(convenience_missing[:3])
            points.append({
                "category": "convenience",
                "priority": 2,
                "message": f"편의기능 미활성 — [{missing_str}] 항목이 비어있어요.",
            })

        # 참여도 관련
        engagement_missing = []
        if not data.get("has_owner_reply", False):
            engagement_missing.append("사장님 답글")
        if not data.get("has_instagram", False):
            engagement_missing.append("인스타그램")
        if not data.get("has_kakao", False):
            engagement_missing.append("카카오 채널")

        if engagement_missing:
            missing_str = ", ".join(engagement_missing[:3])
            points.append({
                "category": "engagement",
                "priority": 3,
                "message": f"고객 소통 부족 — [{missing_str}] 항목이 비어있어요.",
            })

        # 우선순위로 정렬하고 최대 5개만 반환
        points.sort(key=lambda x: x["priority"])
        return points[:5]

    @staticmethod
    def calculate_estimated_lost_customers(
        rank: int,
        keywords: List,
        competitor_avg_review: int = 0,
        review_count: int = 0,
    ) -> int:
        """
        추정 손실 고객 수 계산.

        공식:
        - 순위별 손실률 적용 (더 정교한 단계별 구분)
        - 월 검색량 기반 계산
        - 경쟁사 리뷰 격차 페널티 적용
        - 8% 클릭률 기반 현실적 계산

        Returns: 0~1499 범위의 정수
        """
        # 순위별 손실률 — 더 정교한 단계별 구분
        # 순위가 낮을수록(순위 뒤로 갈수록) 더 많이 손실
        if rank <= 0:
            rank_factor = 0.35  # 순위 미확인 → 35% (중간값)
        elif rank <= 3:
            rank_factor = 0.02  # 1~3위 → 2% (거의 손실 없음, 최상위)
        elif rank <= 7:
            rank_factor = 0.20  # 4~7위 → 20% (2페이지 진입, 적당한 손실)
        elif rank <= 15:
            rank_factor = 0.45  # 8~15위 → 45% (2페이지 뒤, 상당한 손실)
        else:
            rank_factor = 0.70  # 16위 이상 → 70% (거의 안 보임, 대량 손실)

        # 키워드 월 검색량 합산
        total_search = sum(
            kw.get("search_volume", 0) for kw in keywords if isinstance(kw, dict)
        )
        if not total_search:
            total_search = 2000  # 기본값 (경기 북부 지역 평균 검색량 기준)

        # 경쟁사 리뷰 격차 페널티
        # 경쟁사보다 리뷰가 적으면 추가 손실 반영
        review_penalty = 1.0
        if competitor_avg_review > 0 and review_count < competitor_avg_review:
            review_penalty = 1.0 + (
                (competitor_avg_review - review_count) / competitor_avg_review
            )

        # 8% 클릭률 기반 계산 (3%에서 상향 — 네이버 플레이스 평균 클릭률 더 현실적 반영)
        estimated_lost = int(total_search * rank_factor * review_penalty * 0.08)
        # 0~1499 범위로 제한 (최대값 상향: 999 → 1499)
        return min(max(estimated_lost, 0), 1499)

    @classmethod
    def calculate_all(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        전체 진단 점수 계산.

        업종별 가중치 자동 적용.
        새소식 패널티, 사장님 답글률, 경쟁사 상대점수 반영.

        Args:
            data: 크롤링 결과 데이터

        Returns:
            점수 및 등급, 개선 포인트가 포함된 결과
        """
        # 업종 감지 및 가중치 로드
        category = data.get("category", "")
        industry = detect_industry(category)
        weights = get_weights(category)

        # 개별 점수 계산
        photo_score = cls.calculate_photo_score(data.get("photo_count", 0))
        review_score = cls.calculate_review_score(data.get("review_count", 0))
        blog_score = cls.calculate_blog_score(data.get("blog_review_count", 0))
        info_score = cls.calculate_info_score(
            data.get("has_hours", False),
            data.get("has_menu", False),
            data.get("has_price", False),
            data.get("has_intro", False),
            data.get("has_directions", False),
        )
        keyword_score = cls.calculate_keyword_score(data.get("keywords", []))
        convenience_score = cls.calculate_convenience_score(
            data.get("has_booking", False),
            data.get("has_talktalk", False),
            data.get("has_smartcall", False),
            data.get("has_coupon", False),
            data.get("has_news", False),
        )
        engagement_score = cls.calculate_engagement_score(
            data.get("has_owner_reply", False),
            data.get("has_instagram", False),
            data.get("has_kakao", False),
            data.get("has_menu_description", False),
        )

        # 새소식 90일+ 패널티 적용
        news_last_days = data.get("news_last_days", 0)
        convenience_score = cls.apply_news_penalty(convenience_score, news_last_days)

        # 사장님 답글률 반영
        reply_rate = data.get("owner_reply_rate", 0.0)
        engagement_score = cls.apply_owner_reply_rate(engagement_score, reply_rate)

        # 경쟁사 대비 상대 점수 보너스/패널티
        competitor_avg_review = data.get("competitor_avg_review", 0)
        if competitor_avg_review > 0:
            review_score = cls.apply_competitor_bonus(
                review_score,
                data.get("review_count", 0),
                competitor_avg_review,
            )

        competitor_avg_photo = data.get("competitor_avg_photo", 0)
        if competitor_avg_photo > 0:
            photo_score = cls.apply_competitor_bonus(
                photo_score,
                data.get("photo_count", 0),
                competitor_avg_photo,
            )

        # 총점 계산 (업종별 가중치 적용)
        scores = {
            "photo": photo_score,
            "review": review_score,
            "blog": blog_score,
            "info": info_score,
            "keyword": keyword_score,
            "convenience": convenience_score,
            "engagement": engagement_score,
        }
        total_score = cls.calculate_total_score(scores, weights=weights)

        # 등급 산출
        grade = cls.calculate_grade(total_score)

        # 개선 포인트 생성
        improvement_points = cls.generate_improvement_points(data)

        # 추정 손실 고객 수 계산
        estimated_lost_customers = cls.calculate_estimated_lost_customers(
            rank=data.get("naver_place_rank", 0),
            keywords=data.get("keywords", []),
            competitor_avg_review=competitor_avg_review,
            review_count=data.get("review_count", 0),
        )

        return {
            "photo_score": photo_score,
            "review_score": review_score,
            "blog_score": blog_score,
            "info_score": info_score,
            "keyword_score": keyword_score,
            "convenience_score": convenience_score,
            "engagement_score": engagement_score,
            "total_score": total_score,
            "grade": grade,
            "improvement_points": improvement_points,
            "industry_type": industry,
            "applied_weights": weights,
            "estimated_lost_customers": estimated_lost_customers,
        }
