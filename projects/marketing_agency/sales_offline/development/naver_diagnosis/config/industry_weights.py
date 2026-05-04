"""
업종별 가중치 및 기준값 설정
- 업종별 진단 점수 가중치
- 업종별 평균 객단가 (손익분기 계산용)
- 경쟁사 고정 평균값 (크롤링 실패 시 폴백용)
"""
from typing import Dict, Any

# ─────────────────────────────────────────────────────────────
# 업종별 진단 가중치
# 7개 항목 합계 = 1.0
# ─────────────────────────────────────────────────────────────
INDUSTRY_WEIGHTS: Dict[str, Dict[str, float]] = {
    "미용실": {
        # Phase 5 실증: blog d=2.27 > photo d=2.63 > review d=1.78 / engagement d=-0.42 (무의미)
        "photo": 0.25,
        "review": 0.18,
        "blog": 0.22,         # 0.10 → 0.22 (블로그가 top/bot 가장 잘 구분)
        "info": 0.10,
        "keyword": 0.08,
        "convenience": 0.12,
        "engagement": 0.05,   # 0.20 → 0.05 (booking/talktalk/insta 전원 100% — 차별화 없음)
    },
    "네일": {
        # 샘플 부족(n=1) — 미용실과 유사 패턴 적용
        "photo": 0.25,
        "review": 0.18,
        "blog": 0.20,
        "info": 0.10,
        "keyword": 0.08,
        "convenience": 0.12,
        "engagement": 0.07,
    },
    "피부관리": {
        # Phase 5 실증: review d=1.38, blog d=1.28 비슷 / engagement d=0.00 (무의미)
        # 특이점: has_coupon top=71% vs bot=14% (+0.57) — 쿠폰이 핵심 차별화
        "photo": 0.22,
        "review": 0.22,       # 0.18 → 0.22
        "blog": 0.20,         # 0.12 → 0.20
        "info": 0.10,
        "keyword": 0.08,
        "convenience": 0.13,
        "engagement": 0.05,   # 0.18 → 0.05
    },
    "식당": {
        # Phase 5 실증: review d=3.27 압도적 / blog d=2.23 / photo d=1.97
        "photo": 0.17,        # 0.12 → 0.17 (사진도 유효)
        "review": 0.28,       # 유지 (이미 높음)
        "blog": 0.18,         # 0.10 → 0.18
        "info": 0.12,
        "keyword": 0.10,
        "convenience": 0.10,
        "engagement": 0.05,   # 0.14 → 0.05
    },
    "카페": {
        # Phase 5 실증: review d=2.55 최고 / blog d=1.82 / photo d=1.48
        "photo": 0.15,
        "review": 0.28,       # 유지
        "blog": 0.22,         # 0.15 → 0.22
        "info": 0.08,
        "keyword": 0.08,
        "convenience": 0.14,
        "engagement": 0.05,   # 0.14 → 0.05
    },
    "학원": {
        "photo": 0.10,
        "review": 0.18,       # 리뷰 가중치 소폭 상향 (15% → 18%) — 학원은 커리큘럼 후기 중요
        "blog": 0.20,
        "info": 0.15,
        "keyword": 0.15,
        "convenience": 0.08,
        "engagement": 0.14,
    },
    "병원": {
        "photo": 0.12,
        "review": 0.28,       # 리뷰 가중치 상향 (25% → 28%) — 병원은 진료 후기 매우 중요
        "blog": 0.10,
        "info": 0.18,
        "keyword": 0.08,
        "convenience": 0.12,
        "engagement": 0.12,
    },
    "안경": {
        "photo": 0.15,
        "review": 0.25,       # 리뷰 가중치 상향 (20% → 25%)
        "blog": 0.08,
        "info": 0.15,
        "keyword": 0.10,
        "convenience": 0.12,
        "engagement": 0.15,
    },
    "default": {
        "photo": 0.15,
        "review": 0.23,       # 리뷰 가중치 소폭 상향 (20% → 23%)
        "blog": 0.10,
        "info": 0.14,
        "keyword": 0.10,
        "convenience": 0.14,
        "engagement": 0.14,
    },
}

# ─────────────────────────────────────────────────────────────
# 업종 자동 감지 키워드
# category 필드에서 이 키워드가 포함되면 해당 업종으로 매핑
# ─────────────────────────────────────────────────────────────
INDUSTRY_KEYWORDS: Dict[str, list] = {
    "미용실": [
        "미용", "헤어", "헤어샵", "헤어살롱", "미용실", "매직", "펌", "염색",
        "탈모", "매직", "헤어디자인", "헤어스타일", "매직스트레이트",
    ],
    "네일": [
        "네일", "젤네일", "손톱", "네일샵", "네일아트", "젤", "아크릴",
        "페디큐어", "매니큐어", "루비큐어",
    ],
    "피부관리": [
        "피부", "에스테틱", "왁싱", "관리샵", "스킨", "피부관리", "페이셜",
        "스킨케어", "미용관리", "체관리", "셀룰라이트", "여드름", "점",
    ],
    "식당": [
        "음식", "식당", "한식", "중식", "일식", "양식", "치킨", "피자", "분식",
        "고기", "삼겹살", "국밥", "면요리", "해산물", "초밥", "떡볶이",
        "순두부", "찜닭", "스테이크", "로스트", "구이", "복어", "매운탕",
        "족발", "보쌈", "불고기", "소불고기", "곱창", "막창", "김밥",
        "주먹밥", "우동", "라면", "파스타", "카레", "돈까스", "샤브샤브",
    ],
    "카페": [
        "카페", "커피", "베이커리", "브런치", "디저트", "카페테리아",
        "커피숍", "커피전문점", "에스프레소", "라떼", "아메리카노",
        "음료", "음료점",
    ],
    "학원": [
        "학원", "교습소", "교습", "레슨", "교육", "스쿨", "아카데미", "과외",
        "학습", "교육센터", "영어학원", "수학학원", "미술학원", "음악학원",
        "댄스", "피아노", "기타", "성악", "요가", "필라테스",
    ],
    "병원": [
        "병원", "의원", "클리닉", "치과", "한의원", "약국", "의료",
        "진료", "상담", "검진", "수술",
    ],
    "안경": [
        "안경", "렌즈", "안경점", "안과", "콘택트렌즈", "선글라스",
    ],
}

# ─────────────────────────────────────────────────────────────
# 업종별 평균 객단가 (원)
# 손익분기 계산 시 사용: ceil(패키지금액 / 객단가) = 몇 명만 더 오면 본전
# ─────────────────────────────────────────────────────────────
INDUSTRY_AVG_PRICE: Dict[str, int] = {
    "미용실": 65000,     # 5~8만원 중간값
    "네일": 60000,       # 5~7만원 중간값
    "피부관리": 115000,   # 8~15만원 중간값
    "식당": 20000,       # 1.5~3만원 중간값
    "카페": 8000,        # 6천~1만원
    "학원": 300000,      # 20~40만원 중간값
    "병원": 150000,      # 10~20만원 중간값
    "안경": 250000,      # 20~30만원 중간값
    "default": 30000,    # 기본값
}

# ─────────────────────────────────────────────────────────────
# 경쟁사 고정 평균값 (폴백)
# benchmark_premium 테이블 실데이터 기반 (p25=avg, p75=top_review)
# Phase 4: 2026-04-17 벤치마크 데이터 기반 업데이트
# ─────────────────────────────────────────────────────────────
COMPETITOR_FALLBACK: Dict[str, Dict[str, Any]] = {
    # benchmark_premium 데이터 기반 (서울 핫플 상위권 84개 샘플)
    "미용실": {
        "avg_review": 1451,      # p25 (n=30, 서울 상권 고급 미용실 중위)
        "avg_photo": 770,        # p25
        "avg_blog": 370,         # p25
        "top_review": 9257,      # p75 (상위 경쟁사 수준)
    },
    "네일": {
        "avg_review": 980,       # p25 (n=7)
        "avg_photo": 17386,      # p25 (네일은 포토 집약적)
        "avg_blog": 920,         # p25
        "top_review": 5935,      # p75
    },
    "피부관리": {
        "avg_review": 157,       # p25 (n=23, 피부관리는 리뷰 적음)
        "avg_photo": 1132,       # p25
        "avg_blog": 126,         # p25
        "top_review": 1174,      # p75
    },
    "카페": {
        "avg_review": 437,       # p25 (n=8)
        "avg_photo": 4941,       # p25
        "avg_blog": 298,         # p25
        "top_review": 1713,      # p75
    },
    "식당": {
        # benchmark에 명시 식당 카테고리 없음: default + 참고값(유사 업태)
        "avg_review": 1451,      # 미용실 대체 (리뷰 집약적 업태 기준)
        "avg_photo": 770,        #
        "avg_blog": 370,         #
        "top_review": 9257,      #
    },
    "학원": {
        # benchmark에 명시 학원 카테고리 없음: default
        "avg_review": 600,       # 전체 평균 추정값
        "avg_photo": 500,        #
        "avg_blog": 300,         #
        "top_review": 2000,      #
    },
    "병원": {
        # benchmark에 명시 병원 카테고리 없음: default
        "avg_review": 600,       # 전체 평균 추정값
        "avg_photo": 500,        #
        "avg_blog": 300,         #
        "top_review": 2000,      #
    },
    "안경": {
        # benchmark에 명시 안경 카테고리 없음: default
        "avg_review": 600,       # 전체 평균 추정값
        "avg_photo": 500,        #
        "avg_blog": 300,         #
        "top_review": 2000,      #
    },
    "default": {
        "avg_review": 600,       # 전체 샘플 p25 대략값
        "avg_photo": 800,        #
        "avg_blog": 300,         #
        "top_review": 3000,      # 전체 샘플 p75 대략값
    },
}

# ─────────────────────────────────────────────────────────────
# 패키지 정가 (영업 메시지 손익분기 계산용)
# ─────────────────────────────────────────────────────────────
PACKAGES: Dict[str, Dict[str, Any]] = {
    "시선": {
        "price": 380000,
        "anchor_price": 560000,
        "label": "시선 플랜",
        "emoji": "🔹",
        "description": "기본정보 최적화 + 키워드 등록 + 월 리포트",
    },
    "집중": {
        "price": 560000,
        "anchor_price": 850000,
        "label": "집중 플랜",
        "emoji": "🔸",
        "description": "시선 + 사진 촬영 + 블로그 리뷰 관리 + 사장님 답글 대행",
    },
    "주목": {
        "price": 950000,
        "anchor_price": 1270000,
        "label": "주목 플랜",
        "emoji": "⭐",
        "description": "집중 + 인스타 관리 + 새소식 2회/월 + 전담 매니저",
    },
}


def detect_industry(category: str) -> str:
    """
    category 문자열에서 업종 자동 감지.
    매칭 없으면 'default' 반환.
    """
    if not category:
        return "default"
    cat_lower = category.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in cat_lower:
                return industry
    return "default"


def get_weights(category: str) -> Dict[str, float]:
    """업종에 맞는 가중치 딕셔너리 반환."""
    industry = detect_industry(category)
    return INDUSTRY_WEIGHTS.get(industry, INDUSTRY_WEIGHTS["default"])


def get_avg_price(category: str) -> int:
    """업종 평균 객단가 반환."""
    industry = detect_industry(category)
    return INDUSTRY_AVG_PRICE.get(industry, INDUSTRY_AVG_PRICE["default"])


def get_competitor_fallback(category: str) -> Dict[str, Any]:
    """크롤링 실패 시 폴백 경쟁사 데이터 반환."""
    industry = detect_industry(category)
    return COMPETITOR_FALLBACK.get(industry, COMPETITOR_FALLBACK["default"])


def recommend_package(grade: str, weak_items: list) -> str:
    """
    등급과 취약 항목 기반 추천 패키지 반환.

    처방 전략 (가격: 시선 38만 < 집중 56만 < 주목 95만):
    - D등급: 시선(38만) — 진입장벽 최소화, 빠른 성과 보여주고 업셀
    - C등급: 집중(56만) — 중간 투자, 성장 견인
    - B/A등급: 주목(95만) — 프리미엄 유지·강화
    """
    # D등급: 시선(38만)으로 시작 → 진입장벽 최소화, 성과 보여주고 업셀
    if grade == "D":
        return "시선"
    # C등급 → 집중(56만)
    if grade == "C":
        return "집중"
    # B/A등급 → 주목(95만) 프리미엄
    return "주목"


def recommend_package_by_score(score: float, weak_items: list) -> str:
    """
    점수 직접 기반 패키지 추천 (등급 변환 없이).

    - score < 50: 시선 (38만) — D등급 영역
    - 50 ≤ score < 70: 집중 (56만) — C등급 영역
    - score ≥ 70: 주목 (95만) — B/A등급 영역
    """
    if score < 50:
        return "시선"
    if score < 70:
        return "집중"
    return "주목"
