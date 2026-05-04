"""
AI 분석 서비스 — Claude API (claude-haiku-4-5-20251001)

1. 리뷰 감성 분석: 리뷰 텍스트 → 부정 비율 / 주요 불만 / 위험도
2. 메시지 자연어화: 템플릿 1차 메시지 → 자연스러운 구어체 DM

원칙: 빠르고 가벼운 Haiku 사용. 실패해도 원본 유지.
"""
import os
import json
import re
from typing import Dict, Any, List

import anthropic

_client: anthropic.AsyncAnthropic = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        _client = anthropic.AsyncAnthropic(api_key=api_key)
    return _client


def _parse_json_from_text(text: str) -> dict:
    """텍스트에서 JSON 블록 추출"""
    # 코드블록 제거
    text = re.sub(r"```json?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    raise ValueError("JSON 블록 없음")


# ─────────────────────────────────────────────────────────────
# 1. 리뷰 감성 분석
# ─────────────────────────────────────────────────────────────

async def analyze_review_sentiment(review_texts: List[str]) -> Dict[str, Any]:
    """
    리뷰 텍스트 리스트 → 감성 분석 결과

    Returns:
        {
            "negative_ratio": 0.0~1.0,
            "main_complaints": ["주요 불만 1", ...] (최대 3개),
            "risk_level": "none"|"low"|"medium"|"high",
            "sentiment_score": 0~100 (높을수록 긍정),
        }
    """
    fallback = {
        "negative_ratio": 0.0,
        "main_complaints": [],
        "risk_level": "none",
        "sentiment_score": 50,
    }

    if not review_texts:
        return fallback

    reviews_str = "\n".join(f"- {t}" for t in review_texts[:10])

    prompt = f"""다음은 네이버 플레이스 고객 리뷰입니다.

{reviews_str}

아래 JSON만 출력하세요 (설명 없이):
{{
  "negative_ratio": 부정 리뷰 비율 0.0~1.0,
  "main_complaints": ["주요 불만1", "주요 불만2"] (없으면 []),
  "risk_level": "none" 또는 "low" 또는 "medium" 또는 "high",
  "sentiment_score": 긍정일수록 높은 0~100 정수
}}

판단 기준:
- risk_level high: 부정 40%+, 불친절/위생/음식 맛 불만
- risk_level medium: 부정 20~39%
- risk_level low: 부정 10~19%
- risk_level none: 부정 10% 미만"""

    try:
        client = _get_client()
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return _parse_json_from_text(response.content[0].text)
    except Exception as e:
        print(f"[AI] 리뷰 감성 분석 오류: {e}")
        return fallback


# ─────────────────────────────────────────────────────────────
# 2. 메시지 자연어화
# ─────────────────────────────────────────────────────────────

async def personalize_first_message(
    template_text: str,
    business_name: str,
    context: Dict[str, Any],
) -> str:
    """
    2-agent 영업 메시지 파이프라인:
    Agent 1: 진단 데이터 기반 DM 초안 작성
    Agent 2: 영업 냄새 제거 + 사장님 말투로 교정

    실패 시 원본 template_text 반환.
    """
    if not template_text:
        return template_text

    category = context.get("category", "소상공인 업종")
    grade = context.get("grade", "D")
    estimated_lost = context.get("estimated_lost", 0)

    try:
        client = _get_client()

        # ── Agent 1: 진단 데이터 기반 개인화 초안 ──────────────────
        prompt_agent1 = f"""소상공인 네이버 플레이스 진단 결과를 바탕으로 카카오톡 첫 DM 초안을 작성하세요.

업체: {business_name} ({category})
등급: {grade}등급 / 월 손실 추정 고객: {estimated_lost}명

규칙:
- 숫자/업체명/등급 반드시 포함
- 해결 방법은 알려주지 않음 ("저희가 도와드릴 수 있어요" 한 줄만)
- 3~5문장 이내

기존 메시지 참고:
{template_text}

초안만 출력:"""

        resp1 = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt_agent1}],
        )
        draft = resp1.content[0].text.strip()
        if not draft:
            return template_text

        # ── Agent 2: 영업 냄새 제거 + 자연스러운 말투 교정 ──────────
        prompt_agent2 = f"""아래 영업 DM 메시지를 사장님이 직접 보낸 것처럼 자연스럽게 교정하세요.

교정 규칙:
1. 영업 냄새 최소화 — "제안드립니다", "서비스를 제공" 같은 딱딱한 표현 제거
2. 구어체로 — "~요", "~네요", "~죠?" 활용
3. 숫자/업체명은 그대로 유지
4. 이모지 1~2개만 (없어도 됨)
5. 길이는 원문 ±10% 이내

원문:
{draft}

교정된 메시지만 출력 (설명 없이):"""

        resp2 = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt_agent2}],
        )
        result = resp2.content[0].text.strip()
        return result if result else draft

    except Exception as e:
        print(f"[AI] 메시지 2-agent 오류: {e}")
        return template_text
