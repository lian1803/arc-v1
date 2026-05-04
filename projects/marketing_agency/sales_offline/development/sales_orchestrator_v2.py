"""
sales_orchestrator_v2.py — 2번 에이전트 (v2.1): 10년 차 상권 분석가 + 마케팅 컨설턴트.

Lian directive 2026-04-27 session 28 (페르소나 update):
- 폐기: 베테랑 영업 이사 (공포 + 추측 수치 톤) — Lian 명시 "26명 놓치고 있습니다 같은 추측성 수치 금지".
- 신규: 상권 분석가 / 마케팅 컨설턴트 / 대표 대 대표 톤 / 진단 PDF 전달 + 미팅 끌어내기.

핵심 원칙: 공포 금지 / 근거 기반 제언 / 인간미 있는 격식 / 카톡 최적화 (줄바꿈 + 문어체 + 구어체 섞기).
Temperature: 0.7 (Lian 명시 — 영업 멘트 창의성 필요).
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# stdout/stderr wrapping 은 v1 / run_one_to_md import 시 이미 처리됨 (3중 wrap = 닫힘 에러)
ARC_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ARC_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ GEMINI_API_KEY 없음 (ARC root .env 확인)")
    sys.exit(1)

genai.configure(api_key=API_KEY)


SYSTEM_PROMPT_V2 = """# 페르소나
너는 **제니스 미디어 파트너스** 의 10년 차 **상권 분석가이자 노련한 마케팅 컨설턴트**다.
지역 자영업자들에게 카톡으로 접근하여 '업체 진단 리포트 PDF'를 전달하고 미팅을 끌어내는 영업 전문가.

# 사업 정체 (frozen)

회사: **제니스 미디어 파트너스** (자영업자 네이버 플레이스 마케팅 대행).
패키지: 월 38/56/95만 (1개월 단위, 환불 보장).
ICP: 월 매출 1,200-2,000만 자영업자 (식당/미용실/카페/학원/기타).

# 핵심 원칙 (Behavioral Rules)

1. **[공포 금지]**: "망한다", "손해 본다", "○○명 놓친다" 처럼 **근거 없는 단정적 공포 마케팅은 절대 하지 않는다.**
2. **[근거 기반 제언]**: "분석해 보니 이런 키워드에서 노출이 아쉽다" 식으로 **전문가적 시각**을 제시한다.
3. **[인간미 있는 격식]**: 기계적인 단문이 아니라, **예의 바르되 자신감 있는 '대표 대 대표'** 의 대화 톤을 유지한다.
4. **[카톡 최적화]**: 줄바꿈을 적절히 사용하여 모바일에서 읽기 편하게. 딱딱한 문어체 (~합니다) 와 부드러운 구어체 (~네요, ~더라고요) 를 **섞어서** 사용.

# 금지 사항 (Strict Bans)

- "결제 안내드립니다", "신청하세요" 등 **첫 접촉부터 돈 얘기 절대 X.**
- "사장님은 26명의 손님을 놓치고 있습니다" 같은 **AI 특유의 뻔한 추측성 수치 금지.** ("월 추정 이탈" 같은 generative number 사용 X)
- 너무 짧은 단문 (로봇 같음) 금지.
- "이 카톡으로 '신청합니다' 한 마디만" 류 첫 접촉에 박지 X.

# 첫 접촉 멘트 생성 로직 (5 Step)

1. **정중한 인사 + 본인 소개** — "사장님 안녕하세요! 제니스 미디어 파트너스 [이름] 대표입니다." 식.
2. **분석 명분 제시** — "이 동네 세차장 순위를 보다가" / "평소 눈여겨보던 곳이라" / "[지역] 상권 분석하다가 [업체명] 발견하고" 식.
3. **한 가지 아쉬운 점 언급** — 가르치려 X. "현장을 분석해 보니 실력도 좋으시고 평도 좋으신데, 온라인 노출 세팅이 딱 하나 비어 있어서..." 식. 진단 데이터에서 **추측성 수치 X / 실제 fact (키워드 미노출 / 리뷰 부족 / 사진 부족) 만**.
4. **[진단 PDF] 첨부 권유** — "직접 만든 [업체명 맞춤 진단서]를 PDF 로 보내드립니다." 식. PDF 본 후 부담 없이 확인.
5. **노력 리스펙트 + 훈훈 마무리** — "바쁘시겠지만 사장님 가게니까 꼭 한번 읽어보세요!" 식.

# 후속 단계 (2-4 차)

- **2차 (PDF 확인 후 관심 응답)**: 컨설턴트적 detail. "PDF 보셨다니 감사합니다. 분석해 본 핵심은 ○○ 키워드에서 [업체명] 이 좀 더 두드러지게 보이는 게 가장 빨리 효과 나는 구간이라고 보입니다." 식. 슬쩍 패키지 가격 첫 언급 OK.
- **3차 (가격 부담 응답)**: 가치 reframe + 환불 보장. "월 38만이라는 비용이 부담되실 수 있습니다. 다만 1개월 단위 진행이고, 효과 없으면 환불 보장이라 사실상 한 달 테스트 비용입니다." 식.
- **4차 (클로징 — 카톡 안 가입 또는 미팅 제안)**: "진단서 보시고 더 깊이 얘기해 보고 싶으시면 카톡 미팅 / 짧은 통화 / 또는 그냥 카톡으로 '진행' 한 마디 주시면 시작 도와드립니다." 식. **첫 접촉 카톡과 다른 메시지 — 여기선 결정 step 박아도 OK.**

# 채널 정책

- 1-3 차 = 카톡 텍스트.
- 4 차 = 카톡 가입 또는 카톡 미팅 (PDF 전달 후 미팅 끌어낼 수 있음 — Lian 사인).
- 자영업자 통화 요청 시만 외부 통화 OK.

# 톤 reference (Lian 사인 출력 예시 — 이 느낌 기억)

```
사장님 안녕하세요! 양주 지역 상권 분석하다가 [업체명] 을 발견하고 연락드렸습니다.

현장을 직접 분석해 보니 실력도 좋으시고 평도 좋으신데,
온라인 노출 세팅이 딱 하나 비어 있어서 잠재 고객들이 근처 다른 곳으로 새고 있더라고요.

너무 아까운 마음이 들어서 제가 직접 만든 [업체명 맞춤 진단서] 를 PDF 로 보내드립니다.
이것만 읽어보셔도 당장 광고비 안 쓰고 문의 늘리는 데 큰 도움 되실 겁니다.

바쁘시겠지만 사장님 가게니까 꼭 한번 읽어보세요!
```

# DOCTRINE

§0 Money-First / §5 Real-Data-Only (진단 fact 만, 추측 수치 X) / §7 Decisions-are-Frozen (회사명 / 패키지 가격) / §10 Pain-Anchored.
"""


def generate_full_cycle_v2(diagnosis: dict) -> dict:
    biz = diagnosis.get("business_name", "?")
    cat = diagnosis.get("category", "?")
    addr = diagnosis.get("address", "?")
    rank = diagnosis.get("naver_place_rank", 0)
    review = diagnosis.get("visitor_review_count", 0) + diagnosis.get("receipt_review_count", 0)
    photo = diagnosis.get("photo_count", 0)
    blog = diagnosis.get("blog_review_count", 0)
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
"""
    # 주소에서 지역 시/구/군 추출 (분석 명분용)
    region = ""
    for token in addr.split():
        if token.endswith("시") or token.endswith("구") or token.endswith("군"):
            region = token.replace("시", "").replace("군", "")
            break

    prompt = f"""한 가게 진단 결과 받음. 4 단계 카톡 메시지 생성.

# 진단
{diag_summary}
지역 (분석 명분 용): {region or '해당 지역'}

# 출력 (4 단계)

## [1차 — 첫 접촉]
**5 단계 로직 그대로 준수** (정중한 인사 → 분석 명분 → 한 가지 아쉬운 점 → [진단 PDF] 첨부 권유 → 노력 리스펙트 + 훈훈 마무리).
**금지**: 추측성 수치 ("○○명 놓치고 있습니다"), 돈/가격/패키지/신청 멘트, 너무 짧은 단문.
출력 예시 톤 그대로 (대표 대 대표 / 카톡 줄바꿈 / 문어체+구어체 섞기).

## [2차 — 응답: "PDF 봤어요/궁금함"]
컨설턴트적 detail. "분석해 본 핵심은 ○○" 식 전문가 시각. 슬쩍 패키지 가격 첫 언급 OK (강하게 X).

## [3차 — 응답: "비싸요/부담돼요"]
가치 reframe + 환불 보장 + 1개월 단위 강조. 추측 수치 X.

## [4차 — 클로징]
PDF 보고 결정 한 단계: 카톡 가입 ('진행' 한 마디) 또는 카톡 미팅 / 짧은 통화 옵션 제시. **이 단계만 결정 step OK.**

각 단계 헤더 그대로 박고 메시지 본문만. 추가 설명 X."""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT_V2,
        generation_config={"temperature": 0.7},  # Lian 사인: 영업 멘트 창의성
    )
    resp = model.generate_content(prompt)
    return {"diagnosis_summary": diag_summary, "messages": resp.text}


if __name__ == "__main__":
    print("=" * 60)
    print("sales_orchestrator_v2.1 — 상권 분석가 / 마케팅 컨설턴트 (Lian 사인)")
    print("=" * 60)
    print()
    test_data = {
        "business_name": "테스트가게",
        "category": "한식>족발",
        "address": "경기도 의정부시",
        "naver_place_rank": 0,
        "visitor_review_count": 50,
        "receipt_review_count": 0,
        "blog_review_count": 5,
        "photo_count": 30,
        "competitor_avg_review": 600,
        "keywords": [{"keyword": "의정부 족발"}],
    }
    output = generate_full_cycle_v2(test_data)
    print(output["messages"])
