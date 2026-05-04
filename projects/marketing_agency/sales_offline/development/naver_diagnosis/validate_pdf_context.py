"""
PDF 영업 목적 부합 AI 검증 (Lian 사인 2026-04-28).

목적: "자기 가게가 타 회사 대비 부족한 게 있다 / 그게 뭐다 / 우린 해결해줄 수 있다."
LLM 이 PDF 데이터 받아 영업 fail risk 자동 catch.
"""
import os, sys, json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

ARC_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(ARC_ROOT / ".env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


SYSTEM_PROMPT = """너는 영업 PDF 검증 컨설턴트. 제니스 미디어 파트너스가 자영업자한테 보내는 진단 PDF 를 발송 전 검증.

# PDF 의 목적 (절대 잊지 마)
1. 자영업자가 자기 가게의 약점 (타 업체 대비 부족) 을 인식하게.
2. 그 약점이 구체적으로 무엇인지 명확.
3. 제니스 미디어 파트너스가 그 약점을 해결할 수 있다는 신뢰.

# 판단 기준 (영업 fail risk)
1. **데이터 우열 모순**: 우리 가게 데이터 (사진 / 리뷰 / 블로그) 가 서울 평균보다 큰데도 "부족" 단정 / "이탈 1499 명" 같은 비논리 표시 → CRITICAL.
2. **순위 vs 데이터 mismatch**: 순위권 밖인데 데이터 모두 우월 → "왜 안 보이지?" 라는 hook 이 자영업자한테 합리적 의문 유발 X (오히려 의심).
3. **추측성 수치 불일치**: lost / prospect_count / breakeven 등 다른 라벨로 다른 숫자가 나오면 mismatch.
4. **2위 / 3위 가게에 "안 보임" 톤**: 이미 상위 노출 가게에 "검색량 대부분 경쟁사 흡수" 같은 hook = 모순.
5. **출처 없는 % 사례**: "248% 증가" 같은 단정 = §5 violation, 자영업자 distrust trigger.
6. **라벨 vs 실 데이터**: "지역 상위 경쟁사" 라벨이 사실은 "서울 평균" → 라벨 거짓.

# 출력 형식 (JSON)
{
  "verdict": "PASS" | "REVISE" | "BLOCK",
  "issues": [
    {"severity": "CRITICAL" | "MINOR", "field": "...", "problem": "...", "fix_suggestion": "..."},
    ...
  ],
  "summary": "한 줄 요약"
}

verdict 룰:
- PASS = 영업 자료로 그대로 발송 가능
- REVISE = 수정 후 발송 (minor issue 들)
- BLOCK = 자영업자한테 보내면 신뢰 손상 (critical issue 1+)
"""


def validate(pdf_data: dict) -> dict:
    """PDF data dict 받아 LLM 검증."""
    # 핵심 데이터만 추출 (LLM context 절약)
    bn = pdf_data.get("business_name", "?")
    cat = pdf_data.get("category", "?")
    rank = pdf_data.get("naver_place_rank", 0)
    rev = (pdf_data.get("visitor_review_count", 0) or 0) + (pdf_data.get("receipt_review_count", 0) or 0)
    photo = pdf_data.get("photo_count", 0) or 0
    blog = pdf_data.get("blog_review_count", 0) or 0
    lost = pdf_data.get("estimated_lost_customers", 0) or 0
    seoul_avg_review = pdf_data.get("_seoul_avg_review", 0)
    seoul_avg_photo = pdf_data.get("_seoul_avg_photo", 0)
    seoul_avg_blog = pdf_data.get("_seoul_avg_blog", 0)
    seoul_label = pdf_data.get("_seoul_anchor_key", "?")
    keywords = pdf_data.get("keywords", []) or []
    kw_str = (keywords[0] if keywords else {}).get("keyword", "") if keywords else ""

    summary = f"""# 가게: {bn}
카테고리: {cat}
검색 키워드: {kw_str}
플레이스 순위: {rank}위 ({"순위권 밖" if rank == 0 else "노출"})

# 우리 가게 데이터
- 방문 리뷰: {rev}
- 대표 사진: {photo}
- 블로그 리뷰: {blog}

# 서울 상위권 {seoul_label} (10개 업체) 평균
- 방문 리뷰 평균: {seoul_avg_review}
- 대표 사진 평균: {seoul_avg_photo}
- 블로그 리뷰 평균: {seoul_avg_blog}

# PDF 가 표시하는 영업 hook
- 월 추정 이탈 손님: {lost}{"+" if lost >= 1499 else ""} 명
- 추천 패키지: 월 38/56/95만 (3개월 단위)
- 사용 라벨: '서울 상위권 {seoul_label} (10개 업체 평균)'

위 PDF 데이터로 영업 자료를 자영업자한테 보낼 때 영업 목적 (약점 인식 + 우리 해결) 에 부합하는지, 모순 / 비논리 / 신뢰 손상 위험 발견하면 list 로 출력.

JSON 형식만 출력 (markdown 블록 X)."""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config={"temperature": 0.3, "response_mime_type": "application/json"},
    )
    resp = model.generate_content(summary)
    try:
        return json.loads(resp.text)
    except Exception as e:
        return {"verdict": "ERROR", "issues": [], "summary": f"JSON parse fail: {e} / raw: {resp.text[:300]}"}


if __name__ == "__main__":
    # 1 가게 시험
    biz = sys.argv[1] if len(sys.argv) > 1 else "레이크스토어"
    sys.path.insert(0, str(Path(__file__).parent))
    import generate_html_pdf as g
    data = g.load_from_db(biz)
    seoul_categories = g.load_seoul_anchor()
    seoul_anchor, anchor_key = g.match_seoul_category(data.get("category", ""), seoul_categories)
    data["_seoul_avg_review"] = seoul_anchor.get("avg_review", 0)
    data["_seoul_avg_photo"] = seoul_anchor.get("avg_photo", 0)
    data["_seoul_avg_blog"] = seoul_anchor.get("avg_blog", 0)
    data["_seoul_anchor_key"] = anchor_key
    result = validate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
