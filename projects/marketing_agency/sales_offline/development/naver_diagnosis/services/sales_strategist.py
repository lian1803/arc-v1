"""
업체별 영업 기획서 생성 엔진 (Gemini 2.5 Flash 기반)
- 템플릿이 아닌 업체 개별 데이터로 전략 설계
- 기존 message_generator(템플릿)와 완전 별개 모듈
- JSON 응답 기반 구조화된 영업 전략 생성
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# 로깅
logger = logging.getLogger(__name__)

# .env 로드
BASE_DIR = Path(__file__).parent.parent
for _p in BASE_DIR.resolve().parents:
    if (_p / "company" / ".env").exists():
        load_dotenv(_p / "company" / ".env")
        break
else:
    load_dotenv()

try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    GEMINI_AVAILABLE = True
except Exception as e:
    logger.warning(f"Gemini 초기화 실패: {e}")
    GEMINI_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────
# JSON 추출 및 파싱 (강화된 로직)
# ──────────────────────────────────────────────────────────────────────

def _extract_and_parse_json(response_text: str) -> Optional[Dict[str, Any]]:
    """
    응답에서 JSON을 추출하고 파싱
    1. ```json ... ``` 블록 찾기
    2. { ... } 패턴 찾기
    3. 불완전한 JSON 자동 복구 시도
    """
    text = response_text.strip()

    # 1. ```json 블록 추출
    if "```json" in text:
        try:
            start = text.index("```json") + 7
            end = text.rindex("```")
            json_text = text[start:end].strip()
            return json.loads(json_text)
        except (ValueError, json.JSONDecodeError):
            pass

    # 2. ``` 블록 추출 (언어 안 명시)
    if "```" in text:
        try:
            parts = text.split("```")
            for part in parts:
                if part.strip().startswith("{"):
                    json_text = part.strip()
                    if json_text.startswith("json"):
                        json_text = json_text[4:].strip()
                    return json.loads(json_text)
        except (ValueError, json.JSONDecodeError):
            pass

    # 3. { ... } 패턴 직접 추출
    if "{" in text:
        try:
            start = text.index("{")
            # 마지막 } 찾기
            brace_count = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == "{":
                    brace_count += 1
                elif text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break

            if end > start:
                json_text = text[start:end]
                return json.loads(json_text)
        except (ValueError, json.JSONDecodeError, IndexError):
            pass

    # 4. 불완전한 JSON 자동 복구 시도
    try:
        if "{" in text and "}" not in text[text.index("{"):]:
            # 닫히지 않은 객체
            json_text = text[text.index("{"):] + "}"
            return json.loads(json_text)
    except (ValueError, json.JSONDecodeError):
        pass

    return None


# ──────────────────────────────────────────────────────────────────────
# 핵심 함수: 업체별 맞춤 영업 기획서 생성
# ──────────────────────────────────────────────────────────────────────

def generate_sales_playbook(diagnosis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    업체 진단 데이터를 기반으로 Gemini에서 맞춤 영업 기획서 생성

    Args:
        diagnosis_data: {
            'business_name': str,
            'category': str,
            'grade': str ('A'~'D'),
            'total_score': float,
            'naver_place_rank': int,
            'review_count': int,
            'competitor_avg_review': int,
            'photo_count': int,
            'competitor_avg_photo': int,
            ... (기타 필드)
        }

    Returns:
        {
            'business_analysis': {...},
            'strategy': {...},
            'messages': {...},
            'objection_handling': {...},
            'execution_plan': {...},
            'operator_notes': {...}
        }
        또는 None (생성 실패 시)
    """
    if not GEMINI_AVAILABLE:
        logger.error("Gemini 초기화 실패. playbook 생성 불가")
        return None

    # 진단 데이터 검증
    business_name = diagnosis_data.get('business_name', '업체')
    category = diagnosis_data.get('category', '소상공인')
    grade = diagnosis_data.get('grade', 'D')
    total_score = diagnosis_data.get('total_score', 0)
    naver_rank = diagnosis_data.get('naver_place_rank', 0)
    review_count = diagnosis_data.get('review_count', 0)
    competitor_avg_review = diagnosis_data.get('competitor_avg_review', 0)
    photo_count = diagnosis_data.get('photo_count', 0)
    competitor_avg_photo = diagnosis_data.get('competitor_avg_photo', 0)

    # 프롬프트 구성 (원칙 기반 강화)
    prompt = f"""당신은 한국 소상공인 영업 전문 컨설턴트입니다. 업체 진단 데이터를 기반으로 맞춤형 영업 기획서를 생성합니다.

[CRITICAL RULES - 절대 지켜야 할 원칙]
1. 항상 "하면 안 되는 것"부터 설명하라 ("이건 손해", "타이밍 아님", "이 조건이면 이 방식이 확률 높음")
2. 모든 소통은 카카오톡 ONLY. 전화는 고객이 먼저 요청하는 경우 외에는 절대 언급 금지
3. 견적·계약도 카톡·전자계약으로만 진행.
4. FORBIDDEN WORDS (절대 사용 금지): "대면", "만나서", "만남", "통화", "전화", "찾아뵙", "방문", "오시면"
5. 모든 메시지는 카카오톡 텍스트 기반만. 다른 채널 제안 금지
6. 데이터 기반 설명만 (템플릿이 아닌 입력 수치 활용)
7. 경쟁사 평균과 비교 필수 ("현재 {review_count}개 vs 경쟁사 {competitor_avg_review}개")
8. 거절 처리는 구체적 근거 제시 (5페이지 vs 1페이지 10배 매출 차이, 순위별 회수 기간 등)

[BUSINESS DATA]
- 업체명: {business_name}
- 업종: {category}
- 등급: {grade}등급
- 종합점수: {total_score:.0f}점
- 네이버플레이스 순위: {naver_rank}위
- 현재 리뷰: {review_count}개 (경쟁사 평균: {competitor_avg_review}개, 격차: {abs(review_count - competitor_avg_review)}개)
- 현재 사진: {photo_count}개 (경쟁사 평균: {competitor_avg_photo}개, 격차: {abs(photo_count - competitor_avg_photo)}개)

[CATEGORY-SPECIFIC STRATEGY]
"""

    # 업종별 우선순위 설정
    category_focus = {
        '미용실': '영수증리뷰(최신성) > 대표사진(품질) > 블로그리뷰(전문성)',
        '식당': '메뉴사진 > 블로그리뷰 > 영수증/답글',
        '카페': '대표사진(분위기) > 영수증리뷰 > 블로그리뷰',
        '피부관리': 'Before/After사진 > 블로그리뷰(전문) > 정보란(설명)',
        '병원': '영수증/답글(최신성) > 정보란(상세) > 블로그리뷰',
        '한의원': '영수증/답글(최신성) > 정보란(전문) > 블로그리뷰'
    }

    focus = category_focus.get(category, '영수증/답글 > 블로그리뷰 > 대표사진')
    prompt += f"{category} 우선순위: {focus}\n\n"

    prompt += f"""[NAVER PLACE 11-ITEM CHECKLIST] (사키정예톡스순소메영블)
사-대표사진, 키-대표키워드, 정-정보란, 예-예약세팅, 톡-톡톡, 스-스마트콜, 순-순위, 소-소식/알람/쿠폰, 메-메뉴, 영-영수증/답글(최신성), 블-블로그리뷰

[COMPANY INFORMATION]
- 회사명: 제니스 미디어 파트너스 (다른 회사명 언급 절대 금지)
- 패키지: 기본(38만원)/표준(56만원)/프리미엄(95만원)
- 채널 우선순위: 카카오톡 > 전화 (고객 요청 또는 설명 불가능할 때만) > 오프라인 만남 절대 금지

[OBJECTION HANDLING - MUST USE DATA]
"비싸다" → "현재 순위 {naver_rank}위면 기본 패키지로 1~3개월 내 회수 가능. 1페이지 진입 시 월 매출 2~3배"
"효과없을것같다" → "1페이지 상위 업체 vs 5페이지: 매출 10배 차이 (시장 통계). 리뷰 {competitor_avg_review}개인 경쟁사도 시작할 때 {competitor_avg_review//2}개에서 시작함"
"바쁘다" → "첫 한달은 제가 직접 카톡으로 관리. 이후는 유지만"
"직접해보겠다" → "이 3가지는 하면 손해: [1] 순위 올리고 싶으면 반드시 [매뉴얼], [2] 리뷰는 자연스럽게 - 강압적 리뷰요청은 패널티, [3] 사진은 프로 사진작가가 필수"

[TRUST BUILDING SEQUENCE]
1단계: 진단 데이터 제시 (현재 상태의 구체적 약점)
2단계: 경쟁사 비교 (격차 강조, 5페이지 vs 1페이지 매출차)
3단계: 브랜드블로그 구축 안내 (증거자료 축적 - "한 달, 두 달 쌓이다 보면 신뢰도와 증거자료가 크게 달라짐")
4단계: 참고 클라이언트 제시 (사례)
5단계: 패키지 선택 (카톡/전자계약으로)

[TONE & CHANNEL]
톤: 전문적이면서도 친근함. "저는 광고 대행이 아닙니다. 사장님 상황에서 이거 하면 안 되는지부터 봐드립니다."
채널: 기본은 카카오톡. 모든 소통·견적·계약이 카톡·전자계약으로 진행. "아니면 판단만 드린 걸로 끝내셔도 됩니다" 선택지 제시

[BEFORE YOU GENERATE JSON - IMPORTANT]
이 모든 문구를 반드시 포함하되, 다음 표현은 절대 넣지 말 것:
- "대면", "만나서", "만남": 카톡만 제안
- "전화", "통화", "전화드": 고객이 먼저 요청한 경우만 언급
- "찾아뵙", "방문", "오시면": 절대 금지
모든 메시지는 카카오톡 기반만.

[JSON OUTPUT - VALID FORMAT ONLY]
반드시 다음 구조로 유효한 JSON만 출력하세요. 설명이나 다른 텍스트는 절대 금지:
"""

    # JSON 템플릿 (f-string 내에서 사용하므로 {} 이스케이프)
    json_template_str = """{
        "business_analysis": {
            "current_state": "2-3 문장 요약 (데이터 포함)",
            "critical_weaknesses": ["약점1 (구체적 수치)", "약점2"],
            "unique_strengths": ["강점1"],
            "angle_selection": "공략 각도 + 이유 (1-2 문장)"
        },
        "strategy": {
            "core_hook": "핵심 메시지 (반드시 숫자 포함)",
            "persuasion_path": "4단계 설득 경로",
            "risk_warning": "주의사항 (하면 안 되는 것)"
        },
        "messages": {
            "opening": "오프닝 메시지 (숫자로 시작, 카톡 기반)",
            "second": "2차 메시지 (경쟁사 비교, 카톡만)",
            "third": "3차 메시지 (신뢰 구축, 오프라인 만남 제안 금지)",
            "closing": "클로징 메시지 (카톡으로만 진행, 전자계약 안내)"
        },
        "objection_handling": {
            "비싸다": "데이터 기반 반박 (매출 회수 기간)",
            "효과없을것같다": "통계 기반 반박 (1페이지 vs 5페이지)",
            "바쁘다": "점진적 접근 제시",
            "직접해보겠다": "위험 요소 구체적 설명"
        },
        "execution_plan": {
            "recommended_package": "추천 패키지 + 근거",
            "priority_actions": ["액션1", "액션2", "액션3"],
            "success_metrics": "목표 수치"
        },
        "operator_notes": {
            "tone_recommendation": "친근함 + 전문성. 광고대행이 아닌 컨설턴트 포지셔닝",
            "channel_recommendation": "카카오톡 기본. 모든 소통·견적·계약 카톡·전자계약으로 진행. 오프라인 만남 제안 금지",
            "timing_recommendation": "최적 연락 시간대"
        }
    }"""

    prompt += "\n" + json_template_str
    prompt += "\n\n유효한 JSON만 출력하세요. 코드 블록이나 설명은 제외."

    try:
        # Gemini API 호출
        logger.debug(f"Calling Gemini for {business_name}")
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=3000,
            )
        )

        if not response or not response.text:
            logger.error("Gemini 응답 없음")
            return _retry_with_fallback(diagnosis_data)

        # JSON 파싱 (강화된 로직)
        response_text = response.text.strip()
        logger.debug(f"Response length: {len(response_text)}")
        playbook = _extract_and_parse_json(response_text)

        if playbook:
            logger.info(f"Playbook generated for {business_name}")
            return playbook
        else:
            logger.warning(f"JSON extraction failed, retrying...")
            return _retry_with_fallback(diagnosis_data)

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {e}")
        # 1회 재시도
        return _retry_with_fallback(diagnosis_data)
    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return _retry_with_fallback(diagnosis_data)


def _retry_with_fallback(diagnosis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """JSON 파싱 실패 시 1회 재시도 (더 짧고 명확한 프롬프트)"""
    try:
        business_name = diagnosis_data.get('business_name', '업체')
        grade = diagnosis_data.get('grade', 'D')
        total_score = diagnosis_data.get('total_score', 0)
        review_count = diagnosis_data.get('review_count', 0)
        competitor_avg_review = diagnosis_data.get('competitor_avg_review', 0)
        category = diagnosis_data.get('category', '소상공인')
        naver_rank = diagnosis_data.get('naver_place_rank', 0)

        # 재시도: 더 단순한 프롬프트
        retry_prompt = f"""당신은 영업 전문가입니다. 유효한 JSON만 출력하세요. 다른 텍스트는 금지.

[필수 규칙]
- 회사명: 제니스 미디어 파트너스 (다른 회사명 절대 언급 금지)
- 채널: 카카오톡 ONLY. 견적·계약도 카톡·전자계약으로만 진행.
- 금지 표현: "대면", "만나서", "만남", "통화", "전화", "찾아뵙", "방문", "오시면" 절대 사용 금지

업체: {business_name} ({category})
등급: {grade}등급, 점수: {total_score:.0f}점
순위: {naver_rank}위
리뷰: {review_count}개 (경쟁사 평균: {competitor_avg_review}개)

이 JSON 구조로만 출력:
{{
  "business_analysis": {{
    "current_state": "현재 상태 (1-2 문장, 수치 포함)",
    "critical_weaknesses": ["약점1", "약점2"],
    "unique_strengths": ["강점1"],
    "angle_selection": "공략 각도"
  }},
  "strategy": {{
    "core_hook": "핵심 메시지 (수치 포함)",
    "persuasion_path": "설득 경로",
    "risk_warning": "주의사항"
  }},
  "messages": {{
    "opening": "오프닝 (숫자로 시작)",
    "second": "2차 메시지",
    "third": "3차 메시지",
    "closing": "클로징"
  }},
  "objection_handling": {{
    "비싸다": "데이터 기반 반박",
    "효과없을것같다": "통계 반박",
    "바쁘다": "대안 제시",
    "직접해보겠다": "위험 설명"
  }},
  "execution_plan": {{
    "recommended_package": "추천 패키지",
    "priority_actions": ["액션1", "액션2"],
    "success_metrics": "목표"
  }},
  "operator_notes": {{
    "tone_recommendation": "톤",
    "channel_recommendation": "채널",
    "timing_recommendation": "시간"
  }}
}}"""

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(retry_prompt)

        if response.text:
            playbook = _extract_and_parse_json(response.text)
            if playbook:
                logger.info("재시도 성공")
                return playbook

    except Exception as e:
        logger.error(f"재시도 실패: {e}")

    return None


def get_playbook_from_cache(
    business_id: int,
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    캐시된 playbook 조회
    db_path: diagnosis.db 경로 (없으면 기본값)
    """
    if not db_path:
        db_path = BASE_DIR / "diagnosis.db"

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # sales_playbook_cache 테이블 조회
        cursor.execute(
            "SELECT playbook_json FROM sales_playbook_cache WHERE business_id = ? LIMIT 1",
            (business_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
    except Exception as e:
        logger.debug(f"캐시 조회 실패: {e}")

    return None


def save_playbook_to_cache(
    business_id: int,
    playbook: Dict[str, Any],
    db_path: Optional[str] = None
) -> bool:
    """
    생성된 playbook을 캐시에 저장
    """
    if not db_path:
        db_path = BASE_DIR / "diagnosis.db"

    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 테이블 생성 (없으면)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_playbook_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                playbook_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(business_id)
            )
        """)

        # 삽입 또는 업데이트
        cursor.execute(
            """
            INSERT OR REPLACE INTO sales_playbook_cache (business_id, playbook_json)
            VALUES (?, ?)
            """,
            (business_id, json.dumps(playbook, ensure_ascii=False))
        )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"캐시 저장 실패: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────
# 공개 인터페이스
# ──────────────────────────────────────────────────────────────────────

def get_or_generate_playbook(
    diagnosis_data: Dict[str, Any],
    business_id: Optional[int] = None,
    force_regenerate: bool = False
) -> Optional[Dict[str, Any]]:
    """
    playbook 조회 또는 생성
    - business_id가 있고 force_regenerate=False면 캐시 먼저 확인
    - 캐시 없으면 Gemini로 생성 후 저장
    """
    # 캐시 확인
    if business_id and not force_regenerate:
        cached = get_playbook_from_cache(business_id)
        if cached:
            logger.debug(f"[업체 {business_id}] 캐시된 playbook 반환")
            return cached

    # Gemini 생성
    logger.info(f"[{diagnosis_data.get('business_name')}] playbook 생성 중...")
    playbook = generate_sales_playbook(diagnosis_data)

    # 캐시 저장
    if playbook and business_id:
        save_playbook_to_cache(business_id, playbook)
        logger.debug(f"[업체 {business_id}] playbook 캐시 저장")

    return playbook
