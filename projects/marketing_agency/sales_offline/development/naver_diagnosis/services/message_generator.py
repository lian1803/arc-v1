"""
영업 메시지 자동 생성기
진단 데이터 기반 1차~4차 영업 메시지 생성
원칙: 문제는 확실히 보여주되, 해결법은 절대 안 알려준다
"""
import math
import os
from typing import Dict, Any, List

from config.industry_weights import (
    get_avg_price,
    recommend_package,
    PACKAGES,
    detect_industry,
    get_competitor_fallback,
)


_INDUSTRY_LABEL: Dict[str, str] = {
    "미용실":  "서울 상위 미용실",
    "피부관리": "서울 상위 피부관리샵",
    "카페":    "서울 상위 카페",
    "식당":    "서울 상위 식당",
    "네일":    "서울 상위 네일샵",
}


# ─────────────────────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────────────────────


def _enrich_with_benchmark(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    live 데이터에 없는 벤치마크 수치를 COMPETITOR_FALLBACK으로 채운다.
    - competitor_avg_review / competitor_avg_photo / competitor_avg_blog
    - review_count: visitor_review + receipt_review 합산 (없으면 유지)
    - _industry_label: 업종별 레이블 (예: "서울 상위 미용실")
    """
    enriched = dict(data)
    category = data.get("category", "")
    ind = detect_industry(category)
    fb = get_competitor_fallback(category)

    if not enriched.get("competitor_avg_review"):
        enriched["competitor_avg_review"] = fb.get("avg_review", 0)
    if not enriched.get("competitor_avg_photo"):
        enriched["competitor_avg_photo"] = fb.get("avg_photo", 0)
    if not enriched.get("competitor_avg_blog"):
        enriched["competitor_avg_blog"] = fb.get("avg_blog", 0)

    # review_count 통합 (visitor + receipt)
    if not enriched.get("review_count"):
        v = enriched.get("visitor_review_count", 0) or 0
        r = enriched.get("receipt_review_count", 0) or 0
        enriched["review_count"] = v + r

    enriched["_industry_label"] = _INDUSTRY_LABEL.get(ind, "상위 경쟁사")
    return enriched

def _get_total_search_volume(keywords: list) -> int:
    """키워드 목록에서 월 검색량 합산."""
    if not keywords:
        return 2000
    total = 0
    for kw in keywords:
        if isinstance(kw, dict):
            total += kw.get("search_volume", 0)
    return max(total, 2000)


def _eun_neun(word: str) -> str:
    """
    한국어 조사 '은/는' 선택.
    마지막 글자에 받침 있으면 '은', 없으면 '는'.
    """
    if not word:
        return "은"
    last = word[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return "은" if (code - 0xAC00) % 28 != 0 else "는"
    return "은"


def _get_top_keyword_name(keywords: list) -> str:
    """가장 검색량 높은 키워드 이름 반환."""
    if not keywords:
        return "주요 키워드"
    best = None
    best_vol = -1
    for kw in keywords:
        if isinstance(kw, dict):
            vol = kw.get("search_volume", 0)
            name = kw.get("keyword", "")
            if name and vol > best_vol:
                best_vol = vol
                best = name
        elif isinstance(kw, str) and kw:
            if best is None:
                best = kw
    return best or "주요 키워드"


# ─────────────────────────────────────────────────────
# v2 헬퍼 (session 27): 5 업종 + Self-Image A/B 분기
# DOCTRINE §0.5 v2 Reporting Guideline + §10 Pain-Anchored 적용.
# Lian 12 takeaway #3 (vertical) + #8 (Self-Image) 구현.
# ─────────────────────────────────────────────────────

_INDUSTRY_FRAMES = {
    "식당": {
        "tone": "실제성 + 안심",
        "pain_hook": "신규 손님 3-5명/월 정체",
        "data_focus": "리뷰 격차",
    },
    "미용실": {
        "tone": "감정 + 예약 빈도",
        "pain_hook": "주 2-3건 예약, 새 손님 채널 부재",
        "data_focus": "최신 영수증 리뷰",
    },
    "카페": {
        "tone": "취향 + 트렌드",
        "pain_hook": "인생샷 사진 부족",
        "data_focus": "사진 품질/최신성",
    },
    "학원": {
        "tone": "신뢰 + 검증",
        "pain_hook": "부모 문의 → 상담 전환율",
        "data_focus": "블로그 리뷰 (상세 후기)",
    },
    "기타": {
        "tone": "현실 + 해결책",
        "pain_hook": "검색 노출 부족",
        "data_focus": "순위 인식도",
    },
}


def _detect_industry(category: str) -> str:
    """업종 자동 분류. category 문자열 → 5 업종 중 하나 매핑."""
    if not category:
        return "기타"
    cat = category.lower()
    if any(k in cat for k in ["식당", "한식", "중식", "양식", "일식", "피자", "치킨", "분식", "음식", "고기", "족발", "보쌈", "삼겹살", "갈비", "곱창", "막창", "냉면", "국밥", "찌개", "탕", "쌈밥", "회", "초밥", "라멘", "쌀국수", "햄버거", "스테이크", "백반"]):
        return "식당"
    if any(k in cat for k in ["미용", "헤어", "네일", "피부", "에스테틱", "왁싱", "두피", "마사지"]):
        return "미용실"
    if any(k in cat for k in ["카페", "커피", "디저트", "베이커리", "빵", "케이크", "브런치"]):
        return "카페"
    if any(k in cat for k in ["학원", "교습", "어학", "입시", "공부", "수학", "영어", "과외"]):
        return "학원"
    return "기타"


def _detect_self_image(data) -> str:
    """
    자영업자 Self-Image 추론 (12 takeaway #8).
    A: 마케팅 모름 — 리뷰 < 10 AND 사진 < 10 (보수적 기본값)
    B: 마케팅 경험 — 리뷰 >= 20 AND (블로그 OR 카톡 OR 인스타)
    """
    review_count = data.get("review_count", 0) or 0
    photo_count = data.get("photo_count", 0) or 0
    has_blog = (data.get("blog_review_count", 0) or 0) > 0
    has_kakao = data.get("has_kakao", False)
    has_insta = data.get("has_instagram", False)

    if review_count >= 20 and (has_blog or has_kakao or has_insta):
        return "B"
    return "A"


def _select_first_message_type(data: Dict[str, Any]) -> str:
    """
    1차 메시지 타입 자동 선택.
    A: 리뷰 격차형 (경쟁사 리뷰 >= 내 리뷰 × 3, 경쟁사 데이터 있을 때만)
    B: 순위형 (rank > 10)
    C: 방치형 (새소식 90일+ OR 사진 5장 미만)
    D: Hook형 (카카오톡 채널 없음 AND 인스타 없음 AND 점수 낮음)
    """
    my_review = data.get("review_count", 0)
    competitor_avg_review = data.get("competitor_avg_review", 0)
    rank = data.get("naver_place_rank", 0)
    news_days = data.get("news_last_days", 0)
    photo_count = data.get("photo_count", 0)
    total_score = data.get("total_score", 0)

    # 조건 A: 경쟁사 데이터 있고 리뷰 격차 3배 이상 (최우선 — 숫자 충격 최강)
    if competitor_avg_review > 0 and competitor_avg_review >= my_review * 3:
        return "A"
    # 조건 B: 순위 10위 밖 (실제 수집된 순위 기준)
    if rank > 10:
        return "B"
    # 조건 C: 실제 방치 증거 있을 때만 (bookmark=0은 수집 안 됨이라 제외)
    if news_days >= 90 or photo_count < 5:
        return "C"
    # 기본값: 경쟁사보다 내 리뷰가 적을 때만 A (내 리뷰 > 경쟁사면 충격 역효과)
    if competitor_avg_review > 0 and my_review <= competitor_avg_review:
        return "A"
    if rank > 0:
        return "B"
    # D형: 아무 강한 신호 없고 카카오/인스타도 없고 점수 낮으면 Hook형
    if not data.get("has_kakao", False) and not data.get("has_instagram", False) and total_score < 40:
        return "D"
    return "C"


def _build_missing_items_text(data: Dict[str, Any], max_count: int = 5) -> str:
    """비어있는 항목 텍스트 생성 (최대 5개)."""
    missing = []
    if not data.get("has_hours", False):
        missing.append("영업시간")
    if not data.get("has_menu", False):
        missing.append("메뉴")
    if not data.get("has_price", False):
        missing.append("가격정보")
    if not data.get("has_intro", False):
        missing.append("소개글")
    if not data.get("has_directions", False):
        missing.append("오시는길")
    if data.get("photo_count", 0) < 5:
        missing.append("충분한 사진")
    if data.get("review_count", 0) < 10:
        missing.append("고객리뷰")
    if not data.get("has_owner_reply", False):
        missing.append("사장님답글")

    return ", ".join(missing[:max_count])


# ─────────────────────────────────────────────────────────────
# 메인 생성 함수
# ─────────────────────────────────────────────────────────────

def _build_diagnosis_summary(data: Dict[str, Any]) -> str:
    """
    1차 메시지 하단에 붙는 진단 요약 — 핵심만, 짧게.
    문제만 보여준다. 해결법 없음.
    """
    total_score = data.get("total_score", 0)
    grade = data.get("grade", "D")
    my_photo = data.get("photo_count", 0)
    my_review = data.get("review_count", 0)
    competitor_avg_photo = data.get("competitor_avg_photo", 0)
    competitor_avg_review = data.get("competitor_avg_review", 0)
    estimated_lost = data.get("estimated_lost_customers", 0)
    missing_items = _build_missing_items_text(data, max_count=3)

    grade_emoji = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}.get(grade, "🔴")

    lines = [
        "─────────────────",
        f"{grade_emoji} 진단 결과: {total_score:.0f}점 ({grade}등급)",
    ]

    if competitor_avg_photo > 0:
        lines.append(f"📸 사진: {my_photo}장 vs 경쟁사 {competitor_avg_photo}장")
    if competitor_avg_review > 0:
        lines.append(f"⭐ 리뷰: {my_review}개 vs 경쟁사 {competitor_avg_review}개")
    if missing_items:
        lines.append(f"❌ 비어있는 항목: {missing_items}")
    if estimated_lost > 0:
        lines.append(f"💸 월 추정 손실: {estimated_lost}명")

    lines.append("─────────────────")
    return "\n".join(lines)


def generate_first_message(data: Dict[str, Any]) -> Dict[str, str]:
    """
    1차 메시지 생성 — v4 레퍼런스 기반 (관찰 사실 + 수치 → Pain → 질문형 CTA).
    3줄 공식: 관찰(매장명+수치) → 격차/문제 → 단 하나의 질문
    피해야 할 것: 서비스 소개, "프로모션", 설명형 오프닝
    A: 리뷰격차형 — 경쟁사 수치 직접 비교
    B: 순위형 — 실제 순위 + 업데이트 격차
    C: 방치형 — 구체적 방치 증거 지적
    D: Hook형 — 검색 결과 직접 확인 유도
    """
    data = _enrich_with_benchmark(data)
    msg_type = _select_first_message_type(data)
    business_name = data.get("business_name", "사장님")
    category = data.get("category", "")
    competitor_avg_review = data.get("competitor_avg_review", 0)
    my_review = data.get("review_count", 0)
    rank = data.get("naver_place_rank", 0)
    news_days = data.get("news_last_days", 0)
    photo_count = data.get("photo_count", 0)
    industry_label = data.get("_industry_label", "상위 경쟁사")

    region = os.environ.get("SALES_REGION", "")
    region_str = region if region and region != "이 지역" else ""
    kakao_link = os.environ.get("KAKAO_LINK", "")
    cta = f"\n→ 카카오톡 오픈채팅: {kakao_link}" if kakao_link else ""

    category_str = f"{category}" if category else "업종"
    search_query = f"{region_str} {category_str}".strip() if region_str else category_str

    if msg_type == "A":  # 리뷰격차형 — 관찰 수치 + 검색 순위 연결 + 체감 질문
        gap = competitor_avg_review - my_review
        text = (
            f"{business_name} 플레이스 확인해봤는데요.\n\n"
            f"\"{search_query}\" 검색하면 {industry_label} 리뷰가 평균 {competitor_avg_review:,}개인데\n"
            f"사장님 매장은 {my_review:,}개거든요 — 지금 {gap:,}개 차이가 순위에 그대로 나와요.\n\n"
            f"{(                '현재 이 상태가 맞는지 빠르게 확인해보실래요?' if _detect_self_image(data) == 'B' else                 '최근에 새 손님이 줄었다는 느낌 받으신 적 있으세요?' if _detect_industry(category) == '미용실' else                 '우리 카페 사진과 상위 카페 사진 비교 해보셨어요?' if _detect_industry(category) == '카페' else                 '부모님 문의가 줄었다는 느낌 받으신 적 있으세요?' if _detect_industry(category) == '학원' else                 '요즘 검색으로 들어오는 신규 손님이 줄었다는 느낌 받으신 적 있으세요?'             )}{cta}"
        )
        label = f"리뷰격차형 ({_detect_industry(category)} / Type {_detect_self_image(data)})"

    elif msg_type == "B":  # 순위형 — 실제 순위 수치 + 최근 변화 관찰 + 질문
        rank_str = f"{rank}위권" if rank > 0 else "10위권 밖"
        text = (
            f"{business_name} 플레이스 봤는데요.\n\n"
            f"\"{search_query}\" 지금 검색하면 {rank_str}이에요.\n"
            f"1~3위 매장들은 이번 달에만 새소식·사진 업데이트가 몇 번씩 있고요.\n\n"
            f"{(                '현재 플레이스 상태 빠르게 확인 가능하실까요?' if _detect_self_image(data) == 'B' else                 '혹시 최근에 플레이스 직접 들어가보신 적 있으세요?'             )}{cta}"
        )
        label = f"순위형 ({_detect_industry(category)} / Type {_detect_self_image(data)})"

    elif msg_type == "C":  # 방치형 — 구체적 방치 수치 + 동네 경쟁 비교 + 질문
        if photo_count < 5:
            detail = f"사진이 {photo_count}장밖에 없더라고요."
            compare = "같은 상권 매장들은 사진 10장 이상에 새소식도 꾸준히 올리고 있고요."
        else:
            detail = f"새소식이 {news_days}일째 없더라고요."
            compare = "같은 상권 매장들은 이달에도 계속 업데이트하고 있고요."
        text = (
            f"{business_name} 플레이스 확인해봤는데요.\n\n"
            f"{detail}\n"
            f"{compare}\n\n"
            f"{(                '현재 플레이스 관리 어떤 식으로 하고 계세요?' if _detect_self_image(data) == 'B' else                 '지금 플레이스 관리 따로 하고 계신 게 있으세요?'             )}{cta}"
        )
        label = f"방치형 ({_detect_industry(category)} / Type {_detect_self_image(data)})"

    else:  # D형 — 검색 결과 직접 확인 유도 (Hook)
        text = (
            f"{business_name} 플레이스 봤는데요.\n\n"
            f"지금 \"{search_query}\" 검색하면\n"
            f"사장님 매장이 어떻게 보이는지 혹시 최근에 확인해보셨어요?\n\n"
            f"{(                '플레이스 운영 관련해서 한 가지 짚어드려도 될까요?' if _detect_self_image(data) == 'B' else                 '한 가지 여쭤봐도 될까요?'             )}{cta}"
        )
        label = f"Hook형 ({_detect_industry(category)} / Type {_detect_self_image(data)})"

    sms = f"{business_name} 플레이스 확인해봤는데 여쭤볼 게 있어서요"

    return {
        "type": msg_type,
        "text": text,
        "sms_text": sms,
        "label": label,
    }


def generate_second_message(data: Dict[str, Any]) -> str:
    """
    2차 메시지 — 진단 데이터 요약 + 손실 수치 충격 + 캡처 전달 제안.
    첫 메시지에 반응 없었거나 "어떤 내용인지" 물어볼 때 사용.
    """
    data = _enrich_with_benchmark(data)
    business_name = data.get("business_name", "업체")
    my_review = data.get("review_count", 0)
    competitor_avg_review = data.get("competitor_avg_review", 0)
    competitor_avg_blog = data.get("competitor_avg_blog", 0)
    my_blog = data.get("blog_review_count", 0) or 0
    estimated_lost = data.get("estimated_lost_customers", 0)
    rank = data.get("naver_place_rank", 0)
    industry_label = data.get("_industry_label", "상위 경쟁사")

    region = os.environ.get("SALES_REGION", "이 지역")
    category = data.get("category", "")

    # 핵심 수치 라인 구성
    numbers = []
    if competitor_avg_review > 0:
        gap = competitor_avg_review - my_review
        numbers.append(f"리뷰 {my_review:,}개 ({industry_label} 평균 {competitor_avg_review:,}개 — {gap:,}개 차이)")
    if competitor_avg_blog > 0 and my_blog < competitor_avg_blog:
        blog_gap = competitor_avg_blog - my_blog
        numbers.append(f"블로그 리뷰 {my_blog:,}건 ({industry_label} 평균 {competitor_avg_blog:,}건 — {blog_gap:,}건 차이)")
    if rank > 0:
        numbers.append(f"\"{region} {category}\" 검색 순위 {rank}위")
    if estimated_lost > 0:
        numbers.append(f"월 추정 이탈 {estimated_lost}명")

    numbers_str = "\n".join(numbers) if numbers else f"리뷰 {my_review}개"

    lines = [
        f"{business_name} 데이터 정리해봤는데요.",
        "",
        numbers_str,
        "",
        "이 수치만 봐도 지금 어디서 손님이 빠지는지 보이거든요.",
        "",
        "정리한 거 캡처 하나 보내드려도 될까요?",
    ]

    return "\n".join(lines)


def _get_weak_items(data: Dict[str, Any]) -> List[str]:
    """취약 항목 키 목록 반환."""
    weak = []
    if data.get("photo_score", 100) < 50:
        weak.append("photo")
    if data.get("review_score", 100) < 50:
        weak.append("review")
    if data.get("blog_score", 100) < 50:
        weak.append("blog")
    if data.get("info_score", 100) < 50:
        weak.append("info")
    if data.get("keyword_score", 100) < 50:
        weak.append("keyword")
    if data.get("convenience_score", 100) < 50:
        weak.append("convenience")
    if data.get("engagement_score", 100) < 50:
        weak.append("engagement")
    return weak


def _get_recommended_package(grade: str, weak_items: List[str]) -> str:
    """추천 패키지 반환."""
    return recommend_package(grade, weak_items)


def generate_third_message(data: Dict[str, Any]) -> str:
    """
    3차 메시지 — 진단 리포트 캡처 전달 + 처음으로 "저희" 소개 + CTA.
    데이터 주도 → 신뢰 획득 → 통화 제안. 패키지 가격은 아직 언급 안 함.
    """
    data = _enrich_with_benchmark(data)
    business_name = data.get("business_name", "업체")
    category = data.get("category", "")
    avg_price = get_avg_price(category)
    estimated_lost = data.get("estimated_lost_customers", 0)
    grade = data.get("grade", "D")
    my_review = data.get("review_count", 0)
    competitor_avg_review = data.get("competitor_avg_review", 0)
    competitor_avg_blog = data.get("competitor_avg_blog", 0)
    my_blog = data.get("blog_review_count", 0) or 0
    rank = data.get("naver_place_rank", 0)
    industry_label = data.get("_industry_label", "상위 경쟁사")

    weak_items = _get_weak_items(data)
    recommended = _get_recommended_package(grade, weak_items)
    pkg = PACKAGES[recommended]
    plan_price = pkg["price"]

    breakeven = math.ceil(plan_price / avg_price) if avg_price > 0 else 0

    sender_phone = os.environ.get("SENDER_PHONE", "010-XXXX-XXXX")
    region = os.environ.get("SALES_REGION", "이 지역")
    category_name = data.get("category", "")

    # 핵심 수치 라인 — 실증 벤치마크 기반
    data_lines = []
    if competitor_avg_review > 0:
        gap = competitor_avg_review - my_review
        data_lines.append(f"리뷰 {my_review:,}개 → {industry_label} 평균 {competitor_avg_review:,}개 ({gap:,}개 차이)")
    if competitor_avg_blog > 0 and my_blog < competitor_avg_blog:
        blog_gap = competitor_avg_blog - my_blog
        data_lines.append(f"블로그 리뷰 {my_blog:,}건 → {industry_label} 평균 {competitor_avg_blog:,}건 ({blog_gap:,}건 차이)")
    if rank > 0:
        data_lines.append(f"검색 순위 {rank}위")
    if estimated_lost > 0:
        data_lines.append(f"월 이탈 추정 {estimated_lost}명")

    data_str = "\n".join(f"- {l}" for l in data_lines) if data_lines else f"- 리뷰 {my_review}개"

    kakao_link = os.environ.get("KAKAO_LINK", "")
    cta_line = f"카카오톡: {kakao_link}" if kakao_link else "이 카톡으로 '궁금해요' 한 마디만 보내주시면 돼요."

    lines = [
        f"{business_name} 진단 리포트예요.",
        "",
        "[진단 리포트 이미지 첨부]",
        "",
        data_str,
        "",
        f"저희가 {region} {category_name} 쪽 플레이스 데이터 보고 있는데,",
        "어디를 먼저 손대면 순위가 바뀌는지 정리가 돼 있거든요.",
        "",
        "관심 있으시면 카톡으로 말씀해주세요.",
        cta_line,
    ]

    return "\n".join(lines)


def generate_fourth_messages(data: Dict[str, Any]) -> Dict[str, str]:
    """
    4차 메시지 — 4가지 상황별 대응.
    보류/무응답/비싸다/직접 하겠다.
    """
    data = _enrich_with_benchmark(data)
    business_name = data.get("business_name", "업체")
    category = data.get("category", "")
    avg_price = get_avg_price(category)
    estimated_lost = data.get("estimated_lost_customers", 0)
    grade = data.get("grade", "D")
    my_review = data.get("review_count", 0)
    competitor_avg_review = data.get("competitor_avg_review", 0)
    industry_label = data.get("_industry_label", "상위 경쟁사")

    weak_items = _get_weak_items(data)
    recommended = _get_recommended_package(grade, weak_items)
    pkg = PACKAGES[recommended]
    plan_price = pkg["price"]

    loss_amount = estimated_lost * avg_price if estimated_lost > 0 else 0
    breakeven = math.ceil(plan_price / avg_price) if avg_price > 0 else 0

    sender_name = os.environ.get("SENDER_NAME", "리안")
    sender_phone = os.environ.get("SENDER_PHONE", "010-XXXX-XXXX")

    anchor_price = pkg.get("anchor_price", plan_price)

    kakao_link = os.environ.get("KAKAO_LINK", "")
    kakao_cta = f"카카오톡: {kakao_link}" if kakao_link else "이 카톡으로 '확인해볼게요' 한 마디만 보내주시면 바로 정리해드릴게요."

    # [관심 있는데 보류] — 가격 첫 공개 (앵커링) + 손익분기 + 카톡 CTA
    holdback = (
        f"{business_name} 데이터 다시 봤는데요.\n\n"
        f"리뷰 {my_review:,}개 → {industry_label} 평균 {competitor_avg_review:,}개 갭이면\n"
        f"지금 매달 {estimated_lost}명은 이미 다른 데로 가고 있는 구조예요.\n\n"
        f"저희 {pkg['label']} 월 {plan_price:,}원 기준으로 (정상가 {anchor_price:,}원)\n"
        f"손님 {breakeven}명만 더 오면 본전인데,\n"
        "궁금하신 거 카톡으로 편하게 여쭤봐 주세요.\n\n"
        f"{kakao_cta}"
    )

    # [무응답 마지막] — 다른 각도 재접근 + 문 열어두기
    no_response = (
        f"{business_name} 마지막으로 한 번만요.\n\n"
        f"\"지금 이 상태가 3개월 더 지속되면\"\n"
        f"손님 {estimated_lost * 3 if estimated_lost > 0 else '여러'}명을 더 놓치는 구조예요.\n\n"
        "지금 연락이 불편하시면 괜찮아요.\n"
        "나중에 플레이스 쪽 궁금하실 때 편하게 연락 주세요.\n\n"
        "좋은 하루 되세요."
    )

    # [비싸다고 할 때] — 손실 vs 비용 재프레임
    if estimated_lost > 0 and loss_amount > plan_price:
        expensive = (
            "솔직하게 말씀드릴게요.\n\n"
            f"지금 {industry_label} 평균 리뷰 {competitor_avg_review:,}개 기준으로\n"
            f"한 달에 손님 {estimated_lost}명, 매출 {loss_amount:,}원이 빠지는 구조예요.\n\n"
            f"저희 월 {plan_price:,}원 (정상가 {anchor_price:,}원)이랑 비교하면\n"
            "안 하는 게 오히려 더 비싼 구조예요.\n\n"
            f"이 계산이 맞는지 카톡으로 여쭤봐 주시면 바로 답드릴게요.\n{kakao_cta}"
        )
    else:
        expensive = (
            "맞아요, 부담되는 금액인 거 알아요.\n\n"
            f"그래서 딱 하나만 여쭤볼게요.\n"
            f"지금 한 달에 신규 손님이 몇 명이나 네이버로 들어오세요?\n\n"
            f"월 {plan_price:,}원에 손님 {breakeven}명만 더 오면 본전이거든요.\n"
            "궁금하신 거 카톡으로 편하게 물어봐 주세요.\n\n"
            f"{kakao_cta}"
        )

    # [직접 해보겠다고 할 때] — 시간 투자 강조
    weak_count = len(weak_items)
    # 약점 개수에 따라 예상 시간 조정 (항목당 3~5시간)
    hours_per_week = max(4, weak_count * 3)

    weak_labels = []
    for item in weak_items:
        label_map = {
            "photo": "사진 촬영/편집",
            "review": "리뷰 관리",
            "blog": "블로그 리뷰 유도",
            "info": "기본 정보 입력",
            "keyword": "키워드 등록",
            "convenience": "편의기능 설정",
            "engagement": "고객 소통",
        }
        weak_labels.append(label_map.get(item, item))

    weak_str = ", ".join(weak_labels[:3])  # 최대 3개만 표시

    diy = (
        "직접 하실 수 있어요.\n\n"
        f"다만 진단에서 {weak_count}개 항목이 나왔는데 ({weak_str} 등),\n"
        "이게 세팅 한 번으로 끝나는 게 아니라\n"
        "매주 꾸준히 업데이트해야 순위가 유지되는 구조예요.\n\n"
        "해보시다가 시간이 너무 빠진다 싶으면 그때 연락 주세요.\n"
        "도움드릴 수 있어요."
    )

    # [전에 해봤는데 효과없었다고 할 때]
    experienced = (
        "그 경험, 솔직히 흔한 케이스예요.\n\n"
        "처음에 세팅만 하고 이후 업데이트가 없으면\n"
        "2~3개월 후에 순위가 다시 밀려요.\n"
        "플레이스는 세팅이 아니라 '유지'가 핵심이거든요.\n\n"
        "그때 어떻게 하셨는지 여쭤봐도 될까요?\n"
        "뭐가 달랐는지 10분이면 파악돼요."
    )

    return {
        "보류": holdback,
        "무응답": no_response,
        "비싸다": expensive,
        "직접": diy,
        "경험있음": experienced,
    }


def generate_fifth_message(data: Dict[str, Any]) -> str:
    """
    5차 메시지 — '네' 받은 후 결제/계약 안내.
    카톡에서 바로 결제 링크 전달.
    결제 링크는 환경변수(PAYMENT_LINK)에서 읽어옴.

    강화점:
    - 결제 CTA를 더 명확하고 직접적으로
    - 결제 망설임 방지를 위한 보증 멘트 추가 (환불/무상연장)
    - 심리적 안정감 제공 (전담 매니저, 즉시 시작)
    """
    grade = data.get("grade", "D")
    weak_items = _get_weak_items(data)
    recommended = _get_recommended_package(grade, weak_items)
    pkg = PACKAGES[recommended]
    plan_price = pkg["price"]
    anchor_price = pkg.get("anchor_price", plan_price)
    business_name = data.get("business_name", "사장님")

    # 환경변수에서 결제 링크 읽기 (기본값: 네이버페이)
    payment_link = os.environ.get("PAYMENT_LINK", "https://pay.naver.com/")

    return (
        f"감사합니다, 사장님.\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"결제 정보\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{pkg['label']}: 월 {plan_price:,}원 (정상가 {anchor_price:,}원)\n"
        f"   {pkg['description']}\n\n"
        f"안심 보증\n"
        f"   - 순위 변화 없으면 1개월 무상 연장\n"
        f"   - 주 1회 진행 상황 보고\n"
        f"   - 카톡으로 언제든 문의 가능\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"아래 링크에서 결제해주시면\n"
        f"{payment_link}\n\n"
        f"결제 완료 후\n"
        f"   - 카톡으로 온보딩 안내 드릴게요\n"
        f"   - 내일부터 작업 시작합니다\n"
        f"   - {business_name} 네이버 플레이스 관리자 권한만 공유해주시면 돼요\n\n"
        f"좋은 결과 만들어드릴게요."
    )


def generate_sixth_message(data: Dict[str, Any]) -> str:
    """
    6차 메시지 — 결제 완료 후 온보딩 안내.
    """
    business_name = data.get("business_name", "사장님")

    sender_phone = os.environ.get("SENDER_PHONE", "010-XXXX-XXXX")

    return (
        f"결제 확인됐어요. 감사합니다, 사장님.\n\n"
        f"이번 주 안에 첫 작업 시작할게요.\n\n"
        f"시작 전에 필요한 것\n"
        f"   - 네이버 플레이스 관리자 계정 공유\n"
        f"   - 가게 사진 있으시면 보내주세요\n"
        f"   - 메뉴/가격표 자료 있으면 첨부해주세요\n\n"
        f"궁금한 거 있으면 이 카톡으로 편하게 연락 주세요."
    )


def generate_all_messages(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    1~4차 메시지 전체 생성.
    Returns: {
        "first": {"type": "A", "text": "...", "sms_text": "...", "label": "..."},
        "second": "...",
        "third": "...",
        "fourth": {"보류": "...", "무응답": "...", "비싸다": "...", "직접": "..."},
        "recommended_package": "집중",
        "estimated_lost_customers": 45,
    }
    """
    try:
        grade = data.get("grade", "D")
        weak_items = _get_weak_items(data)
        recommended = _get_recommended_package(grade, weak_items)
        estimated_lost = data.get("estimated_lost_customers", 0)

        return {
            "first": generate_first_message(data),
            "second": generate_second_message(data),
            "third": generate_third_message(data),
            "fourth": generate_fourth_messages(data),
            "fifth": generate_fifth_message(data),
            "sixth": generate_sixth_message(data),
            "recommended_package": recommended,
            "estimated_lost_customers": estimated_lost,
        }
    except Exception as e:
        # 생성 실패 시 빈 구조 반환 (진단 자체가 실패하면 안 됨)
        return {
            "first": {
                "type": "A",
                "text": f"메시지 생성 오류: {str(e)}",
                "sms_text": "",
                "label": "오류",
            },
            "second": "",
            "third": "",
            "fourth": {"보류": "", "무응답": "", "비싸다": "", "직접": "", "경험있음": ""},
            "fifth": "",
            "sixth": "",
            "recommended_package": "집중",
            "estimated_lost_customers": 0,
        }
