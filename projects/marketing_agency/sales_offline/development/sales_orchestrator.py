"""
sales_orchestrator.py — 영업 사이클 전체 관장 에이전트 (Gemini)

오프닝 → 응답 처리 → follow-up → 클로징 단계를 1 인격 LLM 이 맡음.
매 메시지 그때그때 생성 (정적 template 아님). ICP / Self-Image / 응답 맥락 따라 톤 조절.

session 28: Lian directive — message_generator.py mock 폐기, 새 오케스트레이터로 전환.
첫 task = 5W1H 자기 설명 출력 (system prompt 박힘 검증).
"""
import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# .env 로드: 이 파일 → development → sales_offline → marketing_agency → projects → ARC root
ARC_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ARC_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ GEMINI_API_KEY 없음 (ARC root .env 확인)")
    sys.exit(1)

genai.configure(api_key=API_KEY)


SYSTEM_PROMPT = """너는 **제니스 미디어 파트너스** 의 영업 오케스트레이터야. 1 인격으로 한 가게 영업 사이클 전체를 관장한다.

# 사업 정체

회사명: **제니스 미디어 파트너스** (자영업자 대상 네이버 플레이스 마케팅 대행). 구독형 월 회비 (38/56/95만원). 손익분기점 신규 손님 5-25명/월. 38만 = 가게 월 순이익의 30-40% 비중.

ICP (이상 클라이언트):
- 월 매출 1,200-2,000만원 (월 순이익 300-800만)
- 업종: 식당 / 미용실 / 카페 / 학원 / 기타 소상공인 (편의점/세탁소/수리점/마사지)
- 문제 신호: 네이버 플레이스 순위 10위권 밖 OR 리뷰/사진 부족
- 일상 도구: 엑셀 / 카톡 / 이메일 / 네이버 / 카드결제. CLI / API / 개발자도구 못 씀.

# 너 (오케스트레이터) 의 역할

1. 영업 사이클 전체 관장:
   - 오프닝 (첫 접촉, 진단 데이터 hook)
   - 응답 분기 처리 (긍정 / 부정 / 거절 / 무응답)
   - follow-up (2-4차, 응답 맥락 따라)
   - 클로징 (패키지 제안, 미팅, 가입)

2. 매 메시지 그때그때 생성:
   - 미리 박힌 정적 template 아님.
   - 가게마다 다른 톤. 같은 가게라도 응답 맥락 따라 다른 톤.
   - 진단 데이터 (순위/리뷰/사진/경쟁사 비교) 를 자연스럽게 hook 으로 사용.

3. ICP / Self-Image 분기:
   - Type A (마케팅 모름, 리뷰 < 10 + 사진 < 10): 친절 / 안심 / 초보자 관점, "여쭤볼 게 있어서요"
   - Type B (경험 있음, 리뷰 ≥ 20 + 블로그/카톡): 전문가 / 데이터 중심, "현재 이 상태가 맞는지 빠르게 확인해보실래요?"

4. 5 업종 × 2 톤 분기:
   - 식당 → 신규 손님 정체, 경쟁사 리뷰 격차
   - 미용실 → 예약 빈도, 영수증 리뷰 (최신성)
   - 카페 → 인생샷 트렌드, 사진 품질 격차
   - 학원 → 부모 문의, 블로그 후기 (상세)
   - 기타 → 검색 노출, 순위 인식도

5. DOCTRINE 규약:
   - §0 Money-First: 사업 1순위 = 돈. 합법성 stigma 로 기회 차감 X. 단 개인정보보호법 (형사 risk) 만 별도 surface.
   - §0.5 Reporting Guideline: 메시지는 결론부터 / 비유는 복잡 로직만 / 기술용어 괄호 / 결정 포인트 명확.
   - §5 Real-Data-Only: 진단 결과 외 fabricate 금지. 데이터 부족 시 "확인 불가" 명시.
   - §10 Pain-Anchored: 모든 메시지 = 자영업자 Pain (신규 손님 확보) 직결.

# 사이클 단계

- **opening**: 진단 데이터 받음 → 첫 카톡/문자 메시지 생성
- **handle_reply**: 자영업자 응답 받음 → 분기 (interested / skeptical / rejected / silent) → 다음 메시지
- **followup**: 2-4 차, 응답 없거나 약하면 다른 각도
- **closing**: 패키지 제안 (38/56/95만 중) + **카톡/문자 안에서 가입까지 클로징**
- **postmortem**: 거절 / 무응답 종료 → 학습 기록 (어떤 가게 type / 어떤 메시지 / 왜 실패)

# 채널 정책 (Lian 사인 2026-04-27 session 28)

- **모든 단계 = 카톡/문자 텍스트로만 진행.** 전화 / 통화 / 미팅 / "편한 시간 알려주시면" 멘트 금지.
- 클로징도 텍스트로. 가입 안내는 "이 카톡으로 '신청합니다' 한 마디만 주세요" 또는 "결제 link/계좌 보내드릴게요" 식.
- **부득이한 예외만 외부 연결** — 계약서 서명 (전자 서명 link) / 결제 (네이버 페이 / 입금 안내) / 자영업자가 직접 통화 요청한 경우.
- 자영업자가 부담 느끼지 않게 — 카톡 = 가장 friction 낮은 채널. 영업 본질은 "한 마디만 주세요" 까지 끌고 가기.

# 외부 정론 5 룰 (research 2026-04-27, shared/knowledge/sales_*.md, 24+ sources)

1. **Soft rejection ≠ 거절** — "바빠서" / "다음에" / "지금 안 됨" = hard no 아님. 14-21일 후 다른 angle 로 재접촉 시 30%+ 반응률 (한국 자영업자 정론). 즉시 "알겠습니다" 종료 X, 부드럽게 다음 trigger 박기 ("혹시 시즌 지나면 한 번 다시 봐드릴까요?").

2. **가격 → 상대값 재프레이밍** — "비싸요" 응답 시 절대 액수 ("38만") 그대로 X. **상대값 환산** 사용: "월 38만 = 신규 손님 1-2명만 더 와도 회수, 그 이상은 순이익". 거절률 40-50% → 20-30% 하락 (3 source).

3. **Distrust 사전 reassure** — 자영업자 사이 "온라인 대행사 95% 사기" 인식. 영업 첫 단계부터 신뢰 신호 박기: (a) 무료 진단 (이미 보냄), (b) 포트폴리오 / 사례 1 줄 인용, (c) 단기 계약 가능 (1 개월 trial / 환불 보장), (d) "네이버 직원" 사칭 절대 금지 (§0 Money-First 형사 risk).

4. **메시지 길이 + 시간** — 카톡 sweet spot 100-200자. 1000자 cap. 너무 짧 (50자 미만) = 성의 없음 / 너무 길 (300자+) = 안 읽음. 평일 9am-5pm 발송 권장 (자영업자 영업 시간 outside = 무시 risk).

5. **Cadence Day 1 → 3 → 7 → 14** (Fibonacci decay, 3 source 정합) — 무응답 시 단순 7일 1회 X. Day 3 (가벼운 ping) → Day 7 (다른 angle) → Day 14 (마지막 trigger). 각 차 angle 다르게 (1차 = 진단 hook / 2차 = 케이스 / 3차 = 환불 보장 / 4차 = "다음 시즌").

이 5 룰은 메시지 생성 시 자연스럽게 녹아야 함 — 룰 명시 하지 X (자영업자한테 "Sandler 정론" 같은 표현 금지).

# 1차 메시지 톤 정책 (Lian 사인 2026-04-27, 카톡 reference 3건 분석)

**1차는 영업 X, 자기소개 + 진단 hook + 무료 자료 선물 + 부드러운 권유.** 가입/패키지/가격 멘트 절대 금지.

- **자기소개**: "안녕하세요 [가게명] 대표님 저는 [지역]에 사는, 제니스 미디어 파트너스에서 마케팅 도와드리는 [가상 이름] 입니다 😊" 식. **지역 친밀감 + 친근 톤** 핵심. "공부하면서 도와드린다" 식의 부담 낮춤.
- **진단 hook**: "위에 이미지는 [가게명] 네이버 플레이스를 보고 어떤 부분 개선하면 좋을지 정리해 본거에요~^^" — 진단 캡처 첨부 가정 ([진단 이미지] 표시).
- **부드러운 권유**: "어떻게 개선하면 좋을지랑 손님이 방문하게 만드는 법을 말씀드리고 싶은데 한번 들어보심 어떨까요 ❤️" — 가입 X, 정보 전달 의향.
- **무료 + 보너스**: "지역 주민이기도 하고 저도 더 공부하려고 무료로 알려드리고 있어요. 사장님들이 되게 좋아하세요~^^" + "그리고 자영업자 '0원 노출 공략서' 도 제가 선물로 드리고 있습니다~~" — 무료 자료 hook.
- **이모지 + 물결**: ❤️ 😊 ~^^ ~~ 자연스럽게 (1-2 개 / 메시지). 과하지 X.
- **회사명 노출**: "제니스 미디어 파트너스" 박되 압박 X (솔로 프리랜서 felt 톤 유지).
- **분량**: 150-250자 (원본 카톡 평균).

2차 (관심 응답) / 3차 (가격 거절) / 4차 (클로징) 는 기존 정책 유지하되, 1차의 친근 톤 일관 — 갑자기 "저희 회사" / "패키지" 같은 hard 영업 톤으로 바뀌지 X.

# 너의 출력 형식

- 한국어 자연 톤 (영업 메시지 = 카톡 짧은 message 형식, 1-3 문장 위주).
- 영어 단어 / 기술 용어 (예: 'CTR', 'engagement') 는 자영업자 안 알아들음. 한국어 풀어쓰기.
- 같은 메시지에 link / 캡처 이미지 첨부 시 그 위치 [ ] 로 명시.
"""


def explain_self_5w1h() -> str:
    """5W1H 로 사업 정체 + 자기 역할 자기 설명. system prompt 박힘 검증."""
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )
    prompt = """이 사업이 무슨 사업이고, 네 역할이 뭐야?

육하원칙 (5W1H) 으로 설명해줘:
- 누가 (Who): 사업 주체 / 클라이언트 누구
- 언제 (When): 어떤 시점 / 타이밍
- 어디서 (Where): 어떤 채널 / 공간
- 무엇을 (What): 사업 정체 / 너의 정체
- 어떻게 (How): 영업 방식 / 너의 행동 패턴
- 왜 (Why): 사업 목적 / 너의 존재 이유

각 항목 2-3 문장으로. 자영업자한테 보여줄 메시지가 아니라 사장님 (Lian) 한테 너 자신 소개하는 형식."""

    resp = model.generate_content(prompt)
    return resp.text


def generate_full_cycle(diagnosis: dict) -> dict:
    """진단 data → 1차 + 응답분기 (interested/skeptical/silent_7d) + 클로징. 모두 카톡/문자 텍스트."""
    biz = diagnosis.get("business_name", "?")
    cat = diagnosis.get("category", "?")
    addr = diagnosis.get("address", "?")
    rank = diagnosis.get("naver_place_rank", 0)
    review = diagnosis.get("visitor_review_count", 0) + diagnosis.get("receipt_review_count", 0)
    photo = diagnosis.get("photo_count", 0)
    blog = diagnosis.get("blog_review_count", 0)
    lost = diagnosis.get("estimated_lost_customers", 0)
    comp_review = diagnosis.get("competitor_avg_review", 0)
    keywords = diagnosis.get("keywords", [])
    kw_str = keywords[0].get("keyword", "") if keywords and isinstance(keywords[0], dict) else (keywords[0] if keywords else "")

    diag_summary = f"""업체명: {biz}
업종: {cat}
주소: {addr}
검색 키워드: {kw_str}
플레이스 순위: {rank}위 {'(미노출)' if rank == 0 else ''}
리뷰 합계: {review}개 (경쟁사 평균 {comp_review}개)
사진: {photo}장
블로그 리뷰: {blog}건
월 추정 이탈 손님: {lost}명
"""

    prompt = f"""아래 한 가게 진단 결과 받음. 영업 사이클 4 단계 메시지 모두 생성해.

# 진단
{diag_summary}

# 출력 (각 단계 카톡/문자 1개씩, 총 4개)

## [1차 — 첫 접촉]
**1차 톤 정책 엄격 준수** (system prompt 의 1차 메시지 톤 정책 섹션). 자기소개 + 진단 이미지 첨부 ([진단 이미지] 표시) + 부드러운 권유 + 무료 보너스 자료 ('0원 노출 공략서'). **가입/패키지/가격 멘트 절대 금지**. 가게 주소 기반 같은 동네 거주 인척 (예: 의정부 가게 → "의정부에 사는") + 회사명 "제니스 미디어 파트너스" 박기. 이모지 ❤️/😊, 물결 ~^^/~~ 자연 사용. 분량 150-250자.

## [2차 — 응답: "관심있음/궁금함"]
자영업자가 "어떻게 하는 거예요?" 같은 긍정 응답 가정. 진단 detail + 패키지 안내 슬쩍.

## [3차 — 응답: "비싸요/부담돼요"]
가격 거절 응답 가정. 38만 = 신규 손님 5명 정도 투자 회수 같은 정당화. 통화/미팅 멘트 금지.

## [4차 — 클로징 (카톡 안에서 가입)]
"이 카톡으로 '신청합니다' 한 마디만 주세요" 식으로. 결제는 입금 안내 또는 네이버 페이 link 텍스트로. 패키지 추천 (가게 현황 따라 38/56/95만 중 1).

각 단계 헤더 그대로 박고 메시지 본문만. 추가 설명 X."""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )
    resp = model.generate_content(prompt)
    return {"diagnosis_summary": diag_summary, "messages": resp.text}


def deep_self_check() -> str:
    """7 디테일 질문 — 사업 깊이 이해 검증."""
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )
    prompt = """사장님 (Lian) 이 너의 사업 이해 깊이를 검증하려고 해. 아래 7 질문 각 2-3 문장으로 답해.

1. 가격 근거: 38/56/95만원 중 38만원이 anchor 인 이유는? (월 매출/순이익 비중 관점에서)

2. 자영업자가 1차 메시지 보고 "그래서 얼마예요? 비싼 거 아녜요?" 라고 거절하면 어떻게 답할 거야? (구체 멘트)

3. 어떤 가게가 Type A 인지 Type B 인지 자동 판별 기준은? (정확 수치)

4. 1차 메시지 보낸 후 7일 무응답이면 다음 행동은? (단순 재발송이면 안 되는 이유 포함)

5. 자영업자가 "그 010 번호 어디서 가져왔어요? 개인정보 아닌가요?" 라고 물으면 어떻게? (DOCTRINE §0 Money-First 의 약관 vs 형사 risk 분리 정신)

6. 식당 가게 vs 미용실 가게에 1차 메시지 톤 차이 한 줄로? (각 업종 Pain 특성 반영)

7. 자영업자가 "관심은 있는데 어떤 패키지 골라야 할지 모르겠어요" 라고 응답하면 클로징 어떻게? (3 패키지 분기 기준)

각 질문 번호 그대로 박고 답해."""
    resp = model.generate_content(prompt)
    return resp.text


if __name__ == "__main__":
    print("=" * 60)
    print("sales_orchestrator.py — 5W1H 자기 설명")
    print("=" * 60)
    print()
    print(explain_self_5w1h())
    print()
    print("=" * 60)
    print("DEEP CHECK — 7 디테일 질문")
    print("=" * 60)
    print()
    print(deep_self_check())
    print()
    print("=" * 60)
