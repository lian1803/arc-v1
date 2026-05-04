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
        "photo": 0.25,        # 사진 가중치 상향 (20% → 25%) — 미용은 시각 정보가 가장 중요
        "review": 0.15,
        "blog": 0.10,
        "info": 0.10,
        "keyword": 0.08,
        "convenience": 0.12,
        "engagement": 0.20,
    },
    "네일": {
        "photo": 0.25,        # 사진 가중치 상향 (20% → 25%) — 네일도 시각 정보 중심
        "review": 0.15,
        "blog": 0.08,
        "info": 0.10,
        "keyword": 0.08,
        "convenience": 0.12,
        "engagement": 0.22,
    },
    "피부관리": {
        "photo": 0.22,        # 사진 가중치 소폭 상향 (18% → 22%)
        "review": 0.18,
        "blog": 0.12,
        "info": 0.10,
        "keyword": 0.08,
        "convenience": 0.12,
        "engagement": 0.18,
    },
    "식당": {
        "photo": 0.12,
        "review": 0.30,       # 리뷰 가중치 상향 (25% → 30%) — 식당은 맛/분위기에 대한 리뷰 중시
        "blog": 0.10,
        "info": 0.12,
        "keyword": 0.10,
        "convenience": 0.12,
        "engagement": 0.14,
    },
    "카페": {
        "photo": 0.15,
        "review": 0.28,       # 리뷰 가중치 상향 (20% → 28%) — 카페도 분위기/맛 리뷰 중시
        "blog": 0.15,
        "info": 0.08,
        "keyword": 0.08,
        "convenience": 0.12,
        "engagement": 0.14,
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
# 크롤링 실패 시 업종별 지역 평균으로 대체
# ─────────────────────────────────────────────────────────────
COMPETITOR_FALLBACK: Dict[str, Dict[str, Any]] = {
    # 경기 북부(양주/포천/의정부) 기준 실제 평균값
    "미용실": {
        "avg_review": 60,
        "avg_photo": 20,
        "avg_blog": 8,
        "top_review": 200,
        "top_photo": 60,
    },
    "네일": {
        "avg_review": 50,
        "avg_photo": 18,
        "avg_blog": 6,
        "top_review": 150,
        "top_photo": 50,
    },
    "피부관리": {
        "avg_review": 40,
        "avg_photo": 15,
        "avg_blog": 6,
        "top_review": 120,
        "top_photo": 45,
    },
    "식당": {
        "avg_review": 120,
        "avg_photo": 18,
        "avg_blog": 10,
        "top_review": 300,
        "top_photo": 50,
    },
    "카페": {
        "avg_review": 150,
        "avg_photo": 25,
        "avg_blog": 12,
        "top_review": 400,
        "top_photo": 70,
    },
    "학원": {
        "avg_review": 30,
        "avg_photo": 8,
        "avg_blog": 15,
        "top_review": 80,
        "top_photo": 25,
    },
    "병원": {
        "avg_review": 80,
        "avg_photo": 15,
        "avg_blog": 6,
        "top_review": 200,
        "top_photo": 45,
    },
    "안경": {
        "avg_review": 50,
        "avg_photo": 15,
        "avg_blog": 5,
        "top_review": 120,
        "top_photo": 40,
    },
    "default": {
        "avg_review": 80,
        "avg_photo": 18,
        "avg_blog": 8,
        "top_review": 200,
        "top_photo": 50,
    },
}

# ─────────────────────────────────────────────────────────────
# 패키지 정가 (영업 메시지 손익분기 계산용)
# ─────────────────────────────────────────────────────────────
PACKAGES: Dict[str, Dict[str, Any]] = {
    "주목": {
        "price": 380000,
        "label": "주목 플랜",
        "emoji": "🔹",
        "description": "기본정보 최적화 + 키워드 등록 + 월 리포트",
    },
    "집중": {
        "price": 560000,
        "label": "집중 플랜",
        "emoji": "🔸",
        "description": "주목 + 사진 촬영 + 블로그 리뷰 관리 + 사장님 답글 대행",
    },
    "시선": {
        "price": 950000,
        "label": "시선 플랜",
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

    영업 전략:
    - D등급: 집중(49만원) — 진입장벽 낮게, 성과 보여주고 업셀
    - C등급 + SNS 약점 있으면: 시선(89만원)
    - C등급 기본: 집중(49만원)
    - B등급: 주목(29만원) or 집중
    - A등급: 주목(29만원) — 유지관리
    """
    has_sns_issue = any(item in weak_items for item in ["engagement", "convenience"])
    # D등급: 주목(29만원)으로 시작 → 진입장벽 최소화, 성과 보여주고 업셀
    if grade == "D":
        return "주목"
    # C등급 + SNS 문제 → 집중(49만원)으로 커버 가능
    if grade == "C" and has_sns_issue:
        return "집중"
    # C등급 기본 or 취약 다수 → 집중
    if grade == "C" or len(weak_items) >= 3:
        return "집중"
    # B등급 이상 → 주목 (유지관리)
    return "주목"
