"""
영업 메시지 자동 생성기
진단 데이터 기반 1차~4차 영업 메시지 생성
Gemini 2.5 Flash API 동적 생성 + 템플릿 폴백
원칙: 문제는 확실히 보여주되, 해결법은 절대 안 알려준다
"""
import math
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

from config.industry_weights import (
    get_avg_price,
    recommend_package,
    PACKAGES,
    detect_industry,
)

# Gemini API 임포트 (실패해도 폴백으로 진행)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# 환경변수 로더
# ─────────────────────────────────────────────────────────────

def _load_gemini_key() -> Optional[str]:
    current = Path(__file__).resolve()
    for i in range(10):
        env_path = current.parent / ".env"
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("GOOGLE_API_KEY=") or line.startswith("GEMINI_API_KEY="):
                            key = line.split("=", 1)[1].strip()
                            if key and not key.startswith("#"):
                                return key
            except Exception:
                pass
        current = current.parent
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


# ─────────────────────────────────────────────────────────────
# Gemini API 메시지 생성 헬퍼
# ─────────────────────────────────────────────────────────────

_GEMINI_KEY: Optional[str] = None  # API 키 캐시 (호출마다 새 모델 — system_instruction 다름)


def _generate_with_gemini(system_prompt: str, user_content: str) -> Optional[str]:
    global _GEMINI_KEY

    if not GEMINI_AVAILABLE:
        return None

    if _GEMINI_KEY is None:
        _GEMINI_KEY = _load_gemini_key()
        if not _GEMINI_KEY:
            return None
        try:
            genai.configure(api_key=_GEMINI_KEY)
        except Exception as e:
            print(f"[경고] Gemini 초기화 실패: {e}", file=sys.stderr)
            return None

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_prompt,
        )
        response = model.generate_content(
            user_content,
            generation_config={"max_output_tokens": 600},
        )
        text = response.text.strip()
        # 메타 레이블 제거 ("xxx님께 보낼 DM:", "보낼 메시지:" 등)
        lines = text.splitlines()
        while lines and (
            lines[0].endswith("DM:") or
            lines[0].endswith("메시지:") or
            lines[0].strip() in ("---", "")
        ):
            lines.pop(0)
        return "\n".join(lines).strip() or text
    except Exception as e:
        print(f"[경고] Gemini 생성 실패: {e}", file=sys.stderr)
        return None


# ─────────────────────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────────────────────

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
    """가장 검색량 높은 키워드 이름 반환. 없으면 빈 문자열."""
    if not keywords:
        return ""
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
    return best or ""


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
    1차 메시지 생성 — Claude API 동적 생성 + 템플릿 폴백.
    4가지 버전 (A/B/C/D) 중 자동 선택.
    충격 오프닝 + 진단 요약 바로 포함. "보내드릴까요?" 없음.
    """
    msg_type = _select_first_message_type(data)
    business_name = data.get("business_name", "사장님")
    category = data.get("category", "")
    competitor_avg_review = data.get("competitor_avg_review", 0)
    my_review = data.get("review_count", 0)
    rank = data.get("naver_place_rank", 0)
    total_search = _get_total_search_volume(data.get("keywords", []))
    top_keyword = _get_top_keyword_name(data.get("keywords", [])) or data.get("top_keyword", "주요 키워드")
    estimated_lost = data.get("estimated_lost_customers", 0)
    news_days = data.get("news_last_days", 0)
    total_score = data.get("total_score", 0)
    grade = data.get("grade", "D")

    diag = _build_diagnosis_summary(data)

    # Claude API로 1차 메시지 생성 시도
    system_prompt = """당신은 네이버 플레이스 마케팅 전문가입니다. 소상공인에게 첫 영업 DM을 보냅니다.

규칙:
- 문제는 구체적 숫자로 충격을 줘라. 경쟁사 실명과 리뷰 수를 직접 언급해라
- 해결법은 절대 알려주지 마라. "저희가 해드릴 수 있어요" 이상 설명하지 마라
- 카톡 DM 형식. 짧고 직접적. 3문단 이하
- 마무리: "상세 분석 자료 보내드릴게요." 한 줄만
- 출력: 본문만 (제목/라벨 없음)"""

    competitor_details = data.get("competitor_details", [])
    competitor_name_part = ""
    if competitor_details and competitor_avg_review > 0:
        top_comp = max(competitor_details, key=lambda x: x.get("review_count", 0))
        top_name = top_comp.get("name", "경쟁사")
        top_review = top_comp.get("review_count", competitor_avg_review)
        competitor_name_part = f"1위 [{top_name}] 리뷰 {top_review}개"
    elif competitor_avg_review > 0:
        competitor_name_part = f"경쟁사 리뷰 {competitor_avg_review}개"

    user_content = f"""업체명: {business_name}
업종: {category}
메시지 타입: {msg_type} ({'리뷰 격차' if msg_type == 'A' else '순위' if msg_type == 'B' else '방치' if msg_type == 'C' else '훅'})
네이버 순위: {rank}위
내 리뷰: {my_review}개
경쟁사: {competitor_name_part if competitor_name_part else '데이터 없음'}
월 추정 손실: {estimated_lost}명
종합 점수: {total_score:.0f}점 ({grade}등급)
주요 키워드: {top_keyword}
월 검색량: {total_search:,}명"""

    claude_text = _generate_with_gemini(system_prompt, user_content)

    if claude_text:
        # Claude 생성 성공 — SMS 텍스트도 생성
        text = claude_text
        sms_text = claude_text.split("\n")[0][:80]  # 첫 줄 80자 추출
        label = f"1차-{msg_type}형"
    else:
        # 폴백: 기존 템플릿 로직
        text, sms_text, label = _generate_first_message_fallback(
            msg_type, data, diag
        )

    return {
        "type": msg_type,
        "text": text,
        "sms_text": sms_text,
        "label": label,
    }


def generate_second_message(data: Dict[str, Any]) -> str:
    """
    2차 메시지 — 진단 결과 카톡 카드 형식.
    문제의 규모를 시각적으로 최대한 충격있게.
    Claude API 동적 생성 + 템플릿 폴백.
    """
    business_name = data.get("business_name", "업체")
    total_score = data.get("total_score", 0)
    grade = data.get("grade", "D")
    my_photo = data.get("photo_count", 0)
    my_review = data.get("review_count", 0)
    competitor_avg_photo = data.get("competitor_avg_photo", 0)
    competitor_avg_review = data.get("competitor_avg_review", 0)
    estimated_lost = data.get("estimated_lost_customers", 0)
    category = data.get("category", "")

    # Claude API로 2차 메시지 생성 시도
    system_prompt = """당신은 네이버 플레이스 마케팅 전문가입니다. 진단 결과를 카톡 카드 형식으로 전달합니다.

규칙:
- 숫자 비교를 시각적으로 강조해라. 경쟁사 vs 업체 수치 대비는 반드시 격차를 명시적으로 보여줘라
- 등급을 크게 강조해라. D등급이면 "위험"이라고 명확히 표기해라
- 비어있는 항목들을 구체적으로 나열해라 (몇 개가 빠졌는지 보여줘)
- 월 손실 추정값을 강조해라 (심리적 임팩트)
- 마무리: "상세 분석 자료 보내드릴 거예요." 한 줄로만
- 절대 해결법을 제시하지 마라. 문제의 심각성만 보여줘라
- 카톡/SMS 형식. 적절히 이모지와 구분선 사용
- 출력: 본문만 (제목/라벨 없음)"""

    competitor_details = data.get("competitor_details", [])
    top_comp_name = ""
    if competitor_details:
        top_comp = max(competitor_details, key=lambda x: x.get("review_count", 0))
        top_comp_name = top_comp.get("name", "")

    comp_label = f"1위 [{top_comp_name}]" if top_comp_name else "경쟁사"
    missing_items = _build_missing_items_text(data, max_count=5)

    user_content = f"""업체명: {business_name}
업종: {category}
종합 점수: {total_score:.0f}점
등급: {grade}등급
현재 사진: {my_photo}장
경쟁사 평균 사진: {competitor_avg_photo}장
현재 리뷰: {my_review}개
경쟁사 평균 리뷰: {competitor_avg_review}개
비어있는 항목: {missing_items}
월 추정 손실 고객: {estimated_lost}명
경쟁사 레이블: {comp_label}"""

    claude_text = _generate_with_gemini(system_prompt, user_content)

    if claude_text:
        return claude_text
    else:
        # 폴백: 기존 템플릿 로직
        grade_symbols = {"A": "✅", "B": "🟢", "C": "🟡", "D": "🔴"}
        grade_desc = {"A": "최상위", "B": "양호", "C": "주의", "D": "위험"}
        grade_label = grade_desc.get(grade, grade)
        grade_symbol = grade_symbols.get(grade, "")

        lines = [
            f"📊 {business_name} 네이버 플레이스 진단",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
        ]

        # 등급을 크게 강조 (D등급이면 위험 표시)
        if grade == "D":
            lines.append(f"{grade_symbol} {grade}등급 — 위험")
        else:
            lines.append(f"{grade_symbol} {grade}등급 — {grade_label}")

        lines += [
            f"종합 점수: {total_score:.0f}점",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
            "🔍 현재 상황",
        ]

        if competitor_avg_photo > 0:
            gap = competitor_avg_photo - my_photo
            lines.append(f"사진: {my_photo}장 vs {comp_label} {competitor_avg_photo}장 (-{gap}장)")
        else:
            lines.append(f"사진: {my_photo}장")

        if competitor_avg_review > 0:
            gap = competitor_avg_review - my_review
            lines.append(f"리뷰: {my_review}개 vs {comp_label} {competitor_avg_review}개 (-{gap}개)")
        else:
            lines.append(f"리뷰: {my_review}개")

        lines += [
            "",
            "⛔ 지금 당장 손님을 놓치는 이유",
            missing_items,
            "",
        ]

        if estimated_lost > 0:
            lines.append("💸 매달 손실")
            lines.append(f"약 {estimated_lost}명이 경쟁사로 가고 있어요")
            lines.append("")

        lines.append("상세 분석 자료 보내드릴 거예요.")

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


def _generate_first_message_fallback(
    msg_type: str, data: Dict[str, Any], diag: str
) -> tuple:
    """
    1차 메시지 템플릿 폴백 (Claude 실패 시).
    기존 로직을 함수로 추출.
    """
    business_name = data.get("business_name", "사장님")
    category = data.get("category", "")
    competitor_avg_review = data.get("competitor_avg_review", 0)
    my_review = data.get("review_count", 0)
    rank = data.get("naver_place_rank", 0)
    total_search = _get_total_search_volume(data.get("keywords", []))
    top_keyword = _get_top_keyword_name(data.get("keywords", [])) or data.get("top_keyword", "주요 키워드")
    estimated_lost = data.get("estimated_lost_customers", 0)
    news_days = data.get("news_last_days", 0)

    if msg_type == "A":
        category_str = f"{category} " if category else ""
        competitor_details = data.get("competitor_details", [])
        if competitor_details:
            top_comp = max(competitor_details, key=lambda x: x.get("review_count", 0))
            top_name = top_comp.get("name", "")
            top_review_count = top_comp.get("review_count", competitor_avg_review)
            display_review = top_review_count
            name_part = f"1위 [{top_name}] 리뷰 {top_review_count}개" if top_name else f"경쟁사 리뷰 {top_review_count}개"
        else:
            display_review = competitor_avg_review
            name_part = f"경쟁사 리뷰 {competitor_avg_review}개"

        opening = (
            f"{business_name} 사장님, 잠깐만요.\n\n"
            f"'{top_keyword}' 검색하면\n"
            f"{name_part},\n"
            f"사장님{_eun_neun(business_name)} {my_review}개예요.\n\n"
        )
        sms = f"{business_name} 리뷰 {my_review}개 vs {name_part}. 월 {estimated_lost}명 손실 중."
        label = "리뷰 격차형"

    elif msg_type == "B":
        kw_display = top_keyword if top_keyword and top_keyword != "주요 키워드" else (f"{category} {top_keyword}".strip() if category else top_keyword)
        opening = (
            f"{business_name} 사장님, 네이버 '{kw_display}' 검색해보셨어요?\n\n"
            f"지금 {rank}위예요. 1~5위 밖이면 손님 눈에 사실상 없는 거예요.\n\n"
        )
        sms = f"{kw_display} 검색 {rank}위. 월 {total_search:,}명 중 {estimated_lost}명 경쟁사로."
        label = "순위형"

    elif msg_type == "C":
        photo_count = data.get('photo_count', 0)
        if news_days >= 90:
            key_issue = f"새소식이 {news_days}일째 멈춰있어요"
            sms = f"{business_name} 새소식 {news_days}일 미업데이트. 월 {estimated_lost}명 이탈 중."
        elif photo_count < 5:
            key_issue = f"사진이 {photo_count}장밖에 없어요"
            sms = f"{business_name} 사진 {photo_count}장. 월 {estimated_lost}명 경쟁사로."
        else:
            key_issue = f"기본 정보가 비어있어요"
            sms = f"{business_name} 플레이스 기본정보 미완성. 월 {estimated_lost}명 이탈 중."
        opening = (
            f"{business_name} 사장님, {key_issue}.\n\n"
            f"네이버 검색하는 손님들이 그냥 지나치고 있어요.\n\n"
        )
        label = "방치형"

    else:  # D
        category_str = f"{category} " if category else ""
        kw_str = category_str.strip() if category_str else "우리 업종"
        opening = (
            f"{business_name} 사장님, 네이버에서 '{kw_str}' 검색하면\n"
            f"지금 몇 위인지 아세요?\n\n"
            f"상위 업체들, 서비스가 더 좋아서가 아니에요.\n"
            f"플레이스 관리를 하고 있냐 없냐 차이예요.\n\n"
        )
        sms = f"{business_name} 플레이스 진단 완료. 월 {estimated_lost}명 이탈 중."
        label = "방치-Hook형"

    text = opening + diag
    return text, sms, label


def generate_third_message(data: Dict[str, Any]) -> str:
    """
    3차 메시지 — 패키지 소개 + 손익분기 계산.
    "이 부분만 하면 바뀐다" 메시지 금지.
    Claude API 동적 생성 + 템플릿 폴백.
    """
    category = data.get("category", "")
    avg_price = get_avg_price(category)
    estimated_lost = data.get("estimated_lost_customers", 0)
    grade = data.get("grade", "D")
    business_name = data.get("business_name", "사장님")

    weak_items = _get_weak_items(data)
    recommended = _get_recommended_package(grade, weak_items)
    pkg = PACKAGES[recommended]
    plan_price = pkg["price"]
    daily_price = plan_price // 30

    # 손익분기 계산
    breakeven = math.ceil(plan_price / avg_price) if avg_price > 0 else 0

    # Claude API로 3차 메시지 생성 시도
    system_prompt = """당신은 네이버 플레이스 마케팅 대행사의 영업팀입니다. 고객에게 패키지를 제안하는 메시지를 작성합니다.

규칙:
- 손익분기를 강조해라. "이 많은 고객이 경쟁사로 가는데, 서비스비는 이 정도면 충분히 본전이다" 논리를 명확하게
- "이렇게 하면 된다" 같은 구체적 해결법은 절대 쓰지 마라. "저희가 해드릴 수 있어요"만 언급
- 시간의 긴급성을 강조해라 (경쟁사가 지금도 리뷰·사진을 쌓고 있다)
- 3개월 약정과 2주 노출 변화 보증을 언급해라
- 마무리: "시작하시겠어요?" 한 줄로 결정 압박
- 카톡 형식. 적절히 이모지와 구분선 사용
- 출력: 본문만"""

    monthly_loss = estimated_lost * avg_price if estimated_lost > 0 else 0

    user_content = f"""업체명: {business_name}
추천 패키지: {pkg['label']} (월 {plan_price:,}원)
패키지 설명: {pkg['description']}
객단가: {avg_price:,}원
월 추정 손실: {estimated_lost}명
월 손실액: {monthly_loss:,}원
손익분기: {breakeven}명 (추가 고객 {breakeven}명 오면 본전)
일일 비용: {daily_price:,}원"""

    claude_text = _generate_with_gemini(system_prompt, user_content)

    if claude_text:
        return claude_text
    else:
        # 폴백: 기존 템플릿 로직
        lines = [
            "사장님, 저희 서비스 설명드릴게요 😊",
            "",
            "━━━━━━━━━━━━━━",
            f"{pkg['emoji']} 추천 플랜: {pkg['label']} (월 {plan_price:,}원 / 하루 약 {daily_price:,}원)",
            f"   {pkg['description']}",
            "━━━━━━━━━━━━━━",
            "",
        ]

        if estimated_lost > 0 and breakeven > 0:
            lines += [
                "💰 손익분기 계산",
                f"   월 {plan_price:,}원 ÷ 객단가 {avg_price:,}원",
                f"   = {breakeven}명만 더 오시면 본전이에요",
                "",
            ]
            if monthly_loss >= plan_price:
                lines += [
                    f"지금 월 {estimated_lost}명 놓치고 계시니까",
                    "첫 달부터 본전 돼요.",
                    "",
                ]

        # 3차 메시지 마무리 강화 — 시간 경쟁 의식 + 결단 압박 + 체감 약속
        if estimated_lost > 0 and breakeven > 0:
            lines += [
                "━━━━━━━━━━━━━━━",
                "🚨 지금 경쟁사들이 쌓고 있는 리뷰·사진은",
                "나중에 따라잡기 어려워요.",
                "",
                f"{pkg['label']} 3개월 약정으로 시작할 수 있어요.",
                "2주 안에 플레이스 노출 변화 없으면 말씀해주세요.",
                "",
                "시작하시겠어요?",
            ]
        else:
            lines += [
                "━━━━━━━━━━━━━━━",
                f"{pkg['label']} 3개월 약정으로 시작할 수 있어요.",
                "2주 안에 플레이스 노출 변화 없으면 말씀해주세요.",
                "",
                "시작하시겠어요?",
            ]

        return "\n".join(lines)


def _generate_fourth_message_variant(situation: str, data: Dict[str, Any]) -> str:
    """
    4차 메시지 각 상황별 Claude API 생성 헬퍼.
    """
    category = data.get("category", "")
    business_name = data.get("business_name", "사장님")
    grade = data.get("grade", "D")
    avg_price = get_avg_price(category)
    estimated_lost = data.get("estimated_lost_customers", 0)

    weak_items = _get_weak_items(data)
    recommended = _get_recommended_package(grade, weak_items)
    pkg = PACKAGES[recommended]
    plan_price = pkg["price"]
    loss_amount = estimated_lost * avg_price if estimated_lost > 0 else 0
    breakeven = math.ceil(plan_price / avg_price) if avg_price > 0 else 0

    weak_count = len(weak_items)
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

    weak_str = ", ".join(weak_labels[:3])

    # 상황별 시스템 프롬프트
    if situation == "보류":
        system_prompt = """당신은 네이버 플레이스 마케팅 대행사 영업팀입니다. 고객이 의사결정을 보류할 때 사용할 메시지입니다.

규칙:
- 독점 정책 강조 ("같은 지역 같은 업종 1곳만 받아요")
- 경쟁사가 먼저 할 경우의 손실을 암시 (구체적 해결법은 절대 제시 금지)
- 이번 달 시작의 긴급성 강조
- 친근하고 설득력있는 톤
- 출력: 본문만"""
        user_content = f"""고객: {business_name}
상황: 의사결정 보류
패키지: {pkg['label']} (월 {plan_price:,}원)"""

    elif situation == "무응답":
        system_prompt = """당신은 네이버 플레이스 마케팅 대행사 영업팀입니다. 고객의 무응답/회신지연 상황에 대한 메시지입니다.

규칙:
- 진단 결과를 전송했었음을 상기
- 등급(D등급 등)을 다시 강조하되, "이게 무슨 의미인지" 명확히
- 독점 정책과 경쟁사의 문의가 있음을 암시 (시간의 긴급성 강조)
- 회신을 유도하는 톤
- 출력: 본문만"""
        user_content = f"""고객: {business_name}
상황: 무응답/회신지연
등급: {grade}등급"""

    elif situation == "비싸다":
        system_prompt = """당신은 네이버 플레이스 마케팅 대행사 영업팀입니다. 고객이 가격이 비싸다고 할 때 사용할 메시지입니다.

규칙:
- 공감하는 톤으로 시작 ("그 마음 충분히 이해해요")
- 가능하면 월 손실액과 비교 (손실액 > 패키지가 > "안 하는 게 더 비싼 거")
- 플레이스 순위는 "쌓이는 것"이라 최소 3개월 필요를 설명
- 3개월 후 순위 변화 없으면 1달 무상 연장을 보증
- 절대 가격을 내리거나 구체적 개선 방법을 제시하지 마라
- 출력: 본문만"""
        user_content = f"""고객: {business_name}
상황: 가격이 비싸다는 반발
패키지 가격: {plan_price:,}원
월 손실액: {loss_amount:,}원
객단가: {avg_price:,}원
월 손실 고객: {estimated_lost}명"""

    elif situation == "직접":
        system_prompt = """당신은 네이버 플레이스 마케팅 대행사 영업팀입니다. 고객이 직접 해보겠다고 할 때 사용할 메시지입니다.

규칙:
- 할 수 있다는 것을 인정하되, 시간 투자를 강조
- 진단에서 나온 취약 항목 수와 예상 시간을 구체적으로 언급
- "그 시간에 손님을 보는 게 낫지 않나?" 논리
- "저희가 해드릴 수 있다"는 제안만 하되, 구체적 방법은 절대 제시하지 마라
- 출력: 본문만"""
        user_content = f"""고객: {business_name}
상황: 직접 해보겠다는 반발
취약 항목: {weak_count}개
항목: {weak_str} 등
예상 주간 시간: {hours_per_week}시간"""

    elif situation == "경험있음":
        system_prompt = """당신은 네이버 플레이스 마케팅 대행사 영업팀입니다. 고객이 "전에 해봤는데 효과 없었다"고 할 때 사용할 메시지입니다.

규칙:
- 어떤 방식이었는지 물어보는 열린 톤
- "효과 없는 방식"과 "우리의 방식"을 구분 (구체적 개선 방법은 절대 제시 금지)
- 플레이스 점수 "변화"를 2주 내에 눈에 보게 할 수 있다는 강점 강조
- 다시 한 번 시도해보자는 긍정적 제안
- 출력: 본문만"""
        user_content = f"""고객: {business_name}
상황: 이전 경험 부정적 (효과 없었음)
약정: 3개월"""

    else:
        return ""

    claude_text = _generate_with_gemini(system_prompt, user_content)
    return claude_text if claude_text else None


def generate_fourth_messages(data: Dict[str, Any]) -> Dict[str, str]:
    """
    4차 메시지 — 5가지 상황별 대응.
    보류/무응답/비싸다/직접/경험있음
    Claude API 동적 생성 + 템플릿 폴백.
    """
    category = data.get("category", "")
    avg_price = get_avg_price(category)
    estimated_lost = data.get("estimated_lost_customers", 0)
    grade = data.get("grade", "D")
    business_name = data.get("business_name", "업체")

    weak_items = _get_weak_items(data)
    recommended = _get_recommended_package(grade, weak_items)
    pkg = PACKAGES[recommended]
    plan_price = pkg["price"]

    loss_amount = estimated_lost * avg_price if estimated_lost > 0 else 0
    breakeven = math.ceil(plan_price / avg_price) if avg_price > 0 else 0

    results = {}

    # 각 상황별로 Claude API 시도 → 폴백
    situations = ["보류", "무응답", "비싸다", "직접", "경험있음"]

    for situation in situations:
        claude_text = _generate_fourth_message_variant(situation, data)

        if claude_text:
            results[situation] = claude_text
        else:
            # 폴백: 기존 템플릿 로직
            if situation == "보류":
                results[situation] = (
                    "사장님, 한 번 더 말씀드릴게요 😊\n\n"
                    "저희는 같은 동네 같은 업종은 1곳만 받아요.\n"
                    "먼저 시작하시는 분이 이 지역 독점이에요.\n\n"
                    "경쟁 업체가 먼저 시작하면\n"
                    "저희가 사장님을 도와드리기 어려워요.\n\n"
                    "이번 달 시작하시는 건 어떠세요? 😊"
                )

            elif situation == "무응답":
                results[situation] = (
                    f"사장님, {business_name} 진단 결과 보내드렸는데\n"
                    f"못 보셨을까봐요.\n\n"
                    f"{grade}등급이에요.\n\n"
                    "솔직히 말씀드리면,\n"
                    "저희는 같은 동네 같은 업종 1곳만 받아요.\n"
                    "이미 근처 경쟁 업체 몇 곳이 문의했어요.\n\n"
                    "관심 있으시면 한 마디만 주세요."
                )

            elif situation == "비싸다":
                if estimated_lost > 0 and loss_amount > plan_price:
                    results[situation] = (
                        "그 마음 충분히 이해돼요 😊\n\n"
                        "근데 한 가지 생각해봐주세요.\n"
                        f"{pkg['label']} 한 달 {plan_price:,}원인데\n"
                        f"지금 매달 {estimated_lost}명이 경쟁사로 가고 있고\n"
                        f"한 명당 {avg_price:,}원이면\n"
                        f"월 {loss_amount:,}원 손실이에요.\n\n"
                        "안 하는 게 더 비싼 거죠.\n\n"
                        "플레이스 순위는 쌓이는 거라서 최소 3개월은 지켜봐야 결과가 나와요.\n"
                        "3개월 끝나고 순위 변화 없으면 1달 무상 연장해드려요 😊"
                    )
                else:
                    results[situation] = (
                        "그 마음 충분히 이해돼요 😊\n\n"
                        "플레이스 순위는 쌓이는 거라서\n"
                        "1개월로는 변화 보기가 어려워요.\n\n"
                        "저희가 3개월 단위로 하는 것도\n"
                        "그 안에 실제 순위 변화를 만들어드리려는 거예요.\n\n"
                        "3개월 끝나고 순위 변화 없으면\n"
                        "1달 무상 연장해드려요 😊"
                    )

            elif situation == "직접":
                weak_count = len(weak_items)
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
                weak_str = ", ".join(weak_labels[:3])

                results[situation] = (
                    "당연히 하실 수 있죠 😊\n\n"
                    f"근데 아까 진단에서 항목이 {weak_count}개 나왔는데\n"
                    f"({weak_str} 등)\n"
                    "하나하나가 다 시간 걸리는 일들이에요.\n\n"
                    f"사장님이 직접 하시려면\n"
                    f"매주 최소 {hours_per_week}시간은 써야 해요.\n\n"
                    "그 시간에 손님 보시는 게 훨씬 나잖아요?\n"
                    "저희가 대신 해드릴게요."
                )

            elif situation == "경험있음":
                results[situation] = (
                    "어떤 방식이었는지 여쭤봐도 될까요?\n\n"
                    "솔직히, 효과없는 방식들이 있어요.\n"
                    "단순히 글자 올리거나 광고비 쓰는 거면\n"
                    "저도 효과없다고 생각해요.\n\n"
                    "저희가 하는 건 달라요.\n"
                    "점수가 낮은 항목들을 하나씩 채워가는 거라서\n"
                    "2주 안에 플레이스 점수 변화가 눈에 보여요.\n\n"
                    "한 번 더 보실래요? 이번엔 다를 거예요."
                )

    return results


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
    business_name = data.get("business_name", "사장님")

    # 환경변수에서 결제 링크 읽기 (기본값: 네이버페이)
    payment_link = os.environ.get("PAYMENT_LINK", "https://pay.naver.com/")

    # 보증 멘트 추가 — 결제 망설임 방지
    warranty_msg = (
        "🛡️ 안심 보증\n"
        f"   • 3개월 시작 후 순위 변화 없으면 1개월 무상 연장\n"
        f"   • 전담 매니저가 주 1회 진행 상황 보고\n"
        f"   • 카톡/전화로 언제든 상담 가능\n"
    )

    return (
        f"그래요! 환영합니다 🎉\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"결제 정보\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{pkg['emoji']} {pkg['label']}: 월 {plan_price:,}원\n"
        f"   {pkg['description']}\n\n"
        f"{warranty_msg}\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"👉 아래 링크에서 지금 결제하세요\n"
        f"{payment_link}\n\n"
        f"✅ 결제 완료 후\n"
        f"   • 오늘 중으로 첫 상담 전화드릴게요\n"
        f"   • 내일부터 작업 시작합니다\n"
        f"   • {business_name} 네이버 플레이스 관리자 권한만 공유해주세요\n\n"
        f"감사합니다! 좋은 결과 만들어드릴게요 😊"
    )


def generate_sixth_message(data: Dict[str, Any]) -> str:
    """
    6차 메시지 — 결제 완료 후 온보딩 안내.
    """
    business_name = data.get("business_name", "사장님")

    return (
        f"결제 확인됐어요! 감사합니다 🎉\n\n"
        f"이번 주 안에 첫 작업 시작할게요.\n\n"
        f"📋 시작 전에 필요한 것\n"
        f"   • 네이버 플레이스 관리자 계정 공유\n"
        f"   • 가게 사진 있으시면 보내주세요\n"
        f"   • 메뉴/가격표 자료 있으면 첨부해주세요\n\n"
        f"궁금한 거 있으면 편하게 카톡 주세요 😊"
    )


def generate_lian_report(data: Dict[str, Any]) -> str:
    """
    리안용 내부 정보 보고서 — 업체한테는 절대 보내지 않는 전략 문서.
    경쟁사 상세 + 취약점 해결법 + 영업 우선순위 판단 근거 전부 포함.
    """
    business_name = data.get("business_name", "")
    category = data.get("category", "")
    grade = data.get("grade", "D")
    total_score = data.get("total_score", 0)
    rank = data.get("naver_place_rank", 0)
    my_review = data.get("review_count", 0)
    my_photo = data.get("photo_count", 0)
    my_blog = data.get("blog_review_count", 0)
    estimated_lost = data.get("estimated_lost_customers", 0)
    priority = data.get("priority_tag", "미분류")
    competitor_details = data.get("competitor_details", [])
    competitor_avg_review = data.get("competitor_avg_review", 0)
    competitor_avg_photo = data.get("competitor_avg_photo", 0)
    weak_items = _get_weak_items(data)
    recommended = _get_recommended_package(grade, weak_items)
    pkg = PACKAGES[recommended]

    lines = [
        "=" * 48,
        f"[리안용 내부 보고서] {business_name}",
        "=" * 48,
        "",
        f"▶ 영업 우선순위: {priority}",
        f"▶ 등급: {grade}등급 ({total_score:.0f}점) | 업종: {category}",
        f"▶ 네이버 순위: {rank}위" if rank > 0 else "▶ 네이버 순위: 미확인",
        f"▶ 월 추정 손실: {estimated_lost}명",
        "",
    ]

    # 경쟁사 상세 비교 (핵심 정보 — 업체 비공개)
    lines.append("── 경쟁사 실측 데이터 ──────────────────")
    if competitor_details:
        for i, comp in enumerate(competitor_details, 1):
            name = comp.get("name", f"경쟁사{i}")
            r = comp.get("review_count", 0)
            p = comp.get("photo_count", 0)
            b = comp.get("blog_count", 0)
            lines.append(f"  {i}위 [{name}]  리뷰 {r}개 / 사진 {p}장 / 블로그 {b}개")
        lines.append(f"  (평균 리뷰 {competitor_avg_review}개 / 평균 사진 {competitor_avg_photo}장)")
    else:
        lines.append(f"  경쟁사 데이터 없음 (폴백값: 리뷰 {competitor_avg_review}개)")

    lines += [
        "",
        f"  → 우리 업체: 리뷰 {my_review}개 / 사진 {my_photo}장 / 블로그 {my_blog}개",
        "",
    ]

    # 취약점 + 해결법 (업체한테는 절대 안 알려줌)
    lines.append("── 취약 항목별 해결 방법 ───────────────")
    fix_map = {
        "photo": ("사진 촬영/편집", "전문 사진 4컷 이상 촬영 후 업로드. 메뉴·인테리어·외관·서비스 장면 필수"),
        "review": ("리뷰 관리", "영수증 리뷰 유도 문구 현장 배치. 방문자 리뷰 유도 카드 제작"),
        "blog": ("블로그 리뷰", "체험단 3~5명 섭외 or 블로그 체험단 플랫폼 등록"),
        "info": ("기본 정보", "영업시간·소개글·오시는길·가격정보 전부 입력"),
        "keyword": ("키워드 등록", "업종 대표 키워드 3개 이상 태그 등록. 지역명+업종 조합"),
        "convenience": ("편의기능", "네이버 예약·톡톡·스마트콜 중 하나 이상 활성화"),
        "engagement": ("고객 소통", "최근 리뷰 10개 전부 사장님 답글 달기"),
    }
    for item in weak_items:
        label, fix = fix_map.get(item, (item, "개선 필요"))
        lines.append(f"  ✗ {label}: {fix}")

    lines += [
        "",
        "── 영업 전략 ────────────────────────────",
        f"  추천 패키지: {pkg['label']} (월 {pkg['price']:,}원)",
        f"  설명: {pkg['description']}",
        "",
    ]

    # 영업 우선순위 판단 근거
    reasons = []
    if grade == "D":
        reasons.append("D등급 — 충격 포인트 강함")
    if rank > 10:
        reasons.append(f"순위 {rank}위 — '사실상 없는 것' 논리 사용")
    if competitor_avg_review > 0 and competitor_avg_review >= my_review * 3:
        top_r = max((c.get("review_count", 0) for c in competitor_details), default=competitor_avg_review)
        reasons.append(f"리뷰 격차 {top_r}개 vs {my_review}개 — 숫자 충격 최강")
    if estimated_lost > 0:
        avg_price = get_avg_price(category)
        monthly_loss = estimated_lost * avg_price
        reasons.append(f"월 손실 추정 {monthly_loss:,}원 ({estimated_lost}명 × {avg_price:,}원)")

    if reasons:
        lines.append("  영업 포인트:")
        for r in reasons:
            lines.append(f"    · {r}")

    lines += [
        "",
        "=" * 48,
    ]
    return "\n".join(lines)


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
            "lian_report": generate_lian_report(data),
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


# ─────────────────────────────────────────────────────────────
# 대화형 메시지 생성 (회신 기반 / 무응답 팔로업)
# ─────────────────────────────────────────────────────────────

def generate_reply_message(data: Dict[str, Any], stage: str, reply_text: str) -> str:
    """
    대화형 영업 메시지 생성.

    stage:
      "1차_회신" | "2차_회신" | "3차_회신"
      "무응답_3일" | "무응답_7일" | "무응답_14일"

    reply_text: 상대방 답장 내용 (빈 문자열이면 무응답)
    """
    business_name = data.get("business_name", "사장님")
    grade = data.get("grade", "")
    total_score = int(data.get("total_score", 0))
    review_count = int(data.get("review_count", 0))
    competitor_avg_review = int(data.get("competitor_avg_review", 0))
    estimated_lost = int(data.get("estimated_lost_customers", 0))
    category = data.get("category", "")

    reply_stripped = (reply_text or "").strip()

    # ── 무응답 팔로업 ───────────────────────────────────────
    if not reply_stripped or "무응답" in stage:
        days_map = {"3일": 3, "7일": 7, "14일": 14}
        days = 3
        for k, v in days_map.items():
            if k in stage:
                days = v
                break

        system = (
            "당신은 소상공인 대상 네이버 플레이스 마케팅 영업 전문가입니다.\n"
            "무응답 업체에 팔로업 메시지를 보냅니다.\n"
            "원칙: 문제는 명확히 보여주되 해결법은 절대 알려주지 않습니다.\n"
            "해결책은 '저희가 해드릴 수 있어요' 한 줄로만.\n"
            "메시지만 출력하세요. 설명이나 레이블 없이."
        )
        user = (
            f"업체명: {business_name} / 업종: {category}\n"
            f"등급: {grade}등급 / 점수: {total_score}점\n"
            f"리뷰: {review_count}개 / 경쟁사 1위 리뷰: {competitor_avg_review}개\n"
            f"추정 월 손실: {estimated_lost}명\n\n"
            f"무응답 {days}일 후 팔로업 메시지를 작성하세요.\n"
            + (
                "D+3: 가볍게 확인 ('혹시 자료 확인하셨나요?' 톤)" if days == 3
                else "D+7: 손실 숫자 재강조하며 결정 유도" if days == 7
                else "D+14: '이번 달 마지막 슬롯' 마감 압박으로 클로징 시도"
            )
        )

        result = _generate_with_gemini(system, user)
        if result:
            return result

        # 폴백 템플릿
        if days == 3:
            return (
                f"안녕하세요 사장님! 며칠 전에 {business_name} 진단 자료 보내드렸는데 혹시 확인하셨나요?\n"
                f"잠깐이라도 같이 보시면 좋을 것 같아서요 😊"
            )
        elif days == 7:
            return (
                f"사장님, 지금 {business_name} 네이버 플레이스 {grade}등급 상태 기억하시죠?\n"
                f"매달 약 {estimated_lost}명이 경쟁사로 넘어가고 있어요.\n"
                f"한번 이야기 나눠보실 의향 있으신가요?"
            )
        else:
            return (
                f"사장님, 이번 달 마지막 신규 계약 슬롯 1자리 남았어요.\n"
                f"다음 달엔 자리가 없을 수 있어서 먼저 연락드려요.\n"
                f"결정 어려우시면 5분만 통화 가능하실까요?"
            )

    # ── 회신 기반 다음 메시지 ────────────────────────────────
    system = (
        "당신은 소상공인 대상 네이버 플레이스 마케팅 영업 전문가입니다.\n"
        "상대방의 답장에 맞춰 자연스럽게 대화를 이어가는 다음 메시지를 작성합니다.\n"
        "원칙: 문제는 명확히 보여주되 해결법은 절대 알려주지 않습니다.\n"
        "해결책은 '저희가 해드릴 수 있어요' 수준으로만.\n"
        "사근사근하고 부담 없는 톤. 압박은 자연스럽게.\n"
        "메시지만 출력하세요. 설명이나 레이블 없이."
    )
    user = (
        f"업체명: {business_name} / 업종: {category}\n"
        f"등급: {grade}등급 / 점수: {total_score}점\n"
        f"리뷰: {review_count}개 / 경쟁사 1위 리뷰: {competitor_avg_review}개\n"
        f"추정 월 손실: {estimated_lost}명\n\n"
        f"영업 단계: {stage}\n"
        f"상대방 답장: {reply_stripped}\n\n"
        f"이 답장에 대한 자연스러운 다음 영업 메시지를 작성하세요."
    )

    result = _generate_with_gemini(system, user)
    if result:
        return result

    # 폴백
    return (
        f"네, 알겠습니다 😊\n"
        f"궁금하신 점 있으시면 편하게 물어봐주세요.\n"
        f"저희가 충분히 도와드릴 수 있어요!"
    )
