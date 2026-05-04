"""
위시켓 의뢰글 → 입찰글 자동 생성 (Claude Sonnet 4.6)
"""
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
PORTFOLIO_LINK = os.environ.get("PORTFOLIO_LINK", "https://github.com/lian1803")
CALENDLY_LINK = os.environ.get("CALENDLY_LINK", "https://calendly.com/lian1803")

SYSTEM_PROMPT = """당신은 한국 1인 개발사의 위시켓 입찰 전문가입니다.
의뢰글을 읽고 250자 이내의 짧고 직접적인 입찰글을 씁니다.

규칙:
1. 의뢰글에서 핵심 Pain 1개 뽑아 첫 문장에 바로 해결 가능 언급.
2. 납기: 자동화 = "5-7일", 웹사이트 = "14-21일", 앱 = "30-45일".
3. 단가: 예산 있으면 75-80%, 없으면 카테고리 기본가.
4. 마지막에 캘린들리 링크와 "30분 미팅으로 정확히 파악하겠습니다" 포함.
5. 포트폴리오 링크 포함.
6. 자기소개 없이 바로 Pain 해결부터 시작.
7. 격식체(존댓말) 유지."""

PRICE_DEFAULTS = {
    "자동화": "80~150만원",
    "웹사이트": "200~400만원",
    "앱·모바일": "500~1,500만원",
    "IT·기타": "100~300만원",
}


def generate_bid(listing: dict) -> str:
    category = listing.get("category", "IT·기타")
    title = listing["title"]
    description = listing.get("description", "")[:800]
    budget_text = listing.get("budget_text", PRICE_DEFAULTS.get(category, "협의"))

    user_msg = (
        f"의뢰글 제목: {title}\n"
        f"카테고리: {category}\n"
        f"예산: {budget_text}\n"
        f"내용:\n{description}\n\n"
        f"포트폴리오 링크: {PORTFOLIO_LINK}\n"
        f"캘린들리 링크: {CALENDLY_LINK}\n\n"
        "위 정보로 입찰글을 작성하세요. 250자 이내."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text.strip()


def generate_batch(listings: list[dict]) -> list[dict]:
    results = []
    for listing in listings:
        print(f"  입찰글 생성: {listing['title'][:40]}...")
        bid_text = generate_bid(listing)
        results.append({**listing, "bid_text": bid_text})
    return results


if __name__ == "__main__":
    sample = {
        "id": "test001",
        "title": "쇼핑몰 주문 관리 자동화",
        "category": "자동화",
        "budget_text": "100~150만",
        "budget": 1250000,
        "description": "현재 엑셀로 주문 수동 관리 중. 자동화 필요. 주문 건수 일 50건.",
        "url": "https://www.wishket.com/project/test/",
    }
    result = generate_bid(sample)
    print("=== 생성된 입찰글 ===")
    print(result)
