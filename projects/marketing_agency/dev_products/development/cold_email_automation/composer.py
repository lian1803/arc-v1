"""
콜드 메일 개인화 — Claude API 로 사업자 정보 → 메일 본문 생성.

§5 Real-Data-Only: 사업자명/산업 = verified. Pain = "추정" 라벨.
§0.5 v2: 메일 본문 4 룰 (결론부터 / 비유 복잡만 / 기술 용어 괄호 / 결정 옵션 명확).
§10 Pain-Anchored: 산업 무관 — 반복 업무 많은 모든 SMB cover.

환경변수: ANTHROPIC_API_KEY
모델: claude-sonnet-4-6 (SPEC §6.1 Implementation tier)
"""

import os
import json
from anthropic import Anthropic
from dataclasses import dataclass


@dataclass
class ColdEmailDraft:
    subject: str
    body: str
    industry: str
    pain_estimate: str
    template_used: str


SYSTEM_PROMPT = """당신은 한국 시장 콜드 메일 카피라이터입니다. Claude Code 기반 솔로 개발자가 SMB (산업 무관) 에게 자동화·웹사이트·챗봇 외주를 제안하는 메일을 작성합니다.

규칙:
1. 결론부터 (1 줄): 사업자명 + 추정 Pain
2. 효과 (1 줄): 시간/돈 절감 (Hypothesis 라벨)
3. 다음 단계 (1 줄): 30분 콜 + Calendly link
4. 압박 X — "답장 안 줘도 OK"

작성 원칙:
- 과장 금지. reference 없으면 "비슷한 자동화 사례" 정도까지만
- 실제 데이터 없는 수치 = "Hypothesis" / "추정" 어조
- 길이 = 5-10 줄
- 한국어 존댓말

산업별 추정 Pain (default — 사업자 정보로 추측):
- IT 회사 / SaaS: 보고서 / 이슈 트래킹 / 내부 커뮤니케이션
- 마케팅 대행사: 캠페인 보고서 / 클라이언트 메일 / 데이터 dashboard
- 교육 / 학원: 출석 / 시험 채점 / 부모 알림
- 의료 / 병원: 예약 / 보험 청구 / 환자 안내
- 회계 / 세무 / 법률: 문서 / 일정 / 자료 정리
- 부동산: 매물 게시 / 분석 / 고객 응대
- 제조 / 유통: 재고 / 발주 / 송장 / 매출 보고
- 자영업자 (식당/미용실/카페): 예약 / 재고 / 후기 답변 / 매출 보고서
- 건축사사무소: 견적 / 도면 / 일정 / 관공서 서류
- 일반 SMB: 반복 행정 업무 / 데이터 정리 / 보고서 / 메일 응대

JSON 응답 (마크다운 금지):
{"subject": "...", "body": "...", "pain_estimate": "..."}
"""


TEMPLATES = ["short", "pain_first", "reference"]


def compose_email(
    business_name: str,
    industry: str,
    address: str | None = None,
    template: str = "short",
    calendly_link: str = "[CALENDLY_LINK]",
    sender_name: str = "Lian",
    homepage_summary: str | None = None,
) -> ColdEmailDraft:
    if template not in TEMPLATES:
        raise ValueError(f"template must be one of {TEMPLATES}")

    client = Anthropic()

    user_prompt = f"""사업자 정보:
- 이름: {business_name}
- 업종/산업: {industry}
- 주소: {address or 'unknown'}
{('- 홈페이지 요약: ' + homepage_summary) if homepage_summary else ''}

템플릿: {template}
보내는 사람: {sender_name}
Calendly: {calendly_link}

위 정보로 콜드 메일 1통 작성. 산업 default Pain 참조하되 사업자명 / 업종 / 홈피 요약 단서 활용해 자연스럽게.
JSON 만 출력 (마크다운 금지).""".strip()

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = msg.content[0].text
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"no JSON in Claude response: {text[:200]}")

    parsed = json.loads(text[start:end + 1])

    if not parsed.get("subject") or not parsed.get("body"):
        raise ValueError(f"missing subject/body: {parsed}")

    return ColdEmailDraft(
        subject=parsed["subject"],
        body=parsed["body"],
        industry=industry,
        pain_estimate=parsed.get("pain_estimate", ""),
        template_used=template,
    )


def main():
    """CLI: python composer.py "사업자명" "산업" [template]"""
    import sys

    if len(sys.argv) < 3:
        print("usage: python composer.py <business_name> <industry> [template]")
        sys.exit(1)

    name = sys.argv[1]
    industry = sys.argv[2]
    template = sys.argv[3] if len(sys.argv) > 3 else "short"

    draft = compose_email(name, industry, template=template)

    print(f"Subject: {draft.subject}")
    print()
    print(draft.body)
    print()
    print(f"---\nIndustry: {draft.industry}")
    print(f"Pain estimate: {draft.pain_estimate}")
    print(f"Template: {draft.template_used}")


if __name__ == "__main__":
    main()
