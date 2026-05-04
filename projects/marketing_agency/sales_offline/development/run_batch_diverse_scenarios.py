"""
v2.1 (상권 분석가) 다양한 응답 시나리오 batch.
random 3 가게 → 1 차 첫 접촉 + 8 분기 응답 시나리오 → 바탕화면 .md.
session 28 Lian directive 2026-04-27.
"""
import sys
import asyncio
import random
from pathlib import Path
from datetime import datetime
import openpyxl

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(THIS_DIR / "naver_diagnosis"))

from run_one_to_md import run_diagnosis
from sales_orchestrator_v2 import SYSTEM_PROMPT_V2
import google.generativeai as genai
import os
from dotenv import load_dotenv

ARC_ROOT = THIS_DIR.parent.parent.parent.parent
load_dotenv(ARC_ROOT / ".env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

EXCEL = THIS_DIR / "lead_db" / "양주_010번호_최종_20260326_144032.xlsx"
DESKTOP = Path.home() / "Desktop"


def list_businesses(xlsx_path):
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    headers = [str(h).strip() if h else "" for h in rows[0]]
    name_idx = next((i for i, h in enumerate(headers) if "업체명" in h or "상호" in h), 2)
    franchise_kw = ["본점", "직영", "체인", "가맹", "프랜차이즈", "1호점", "2호점"]
    names = []
    for row in rows[1:]:
        if not row or name_idx >= len(row):
            continue
        name = str(row[name_idx]).strip() if row[name_idx] else ""
        if not name or name == "None":
            continue
        if any(kw in name for kw in franchise_kw):
            continue
        names.append(name)
    return names


def diag_summary(d):
    biz = d.get("business_name", "?")
    cat = d.get("category", "?")
    addr = d.get("address", "?")
    rank = d.get("naver_place_rank", 0)
    review = d.get("visitor_review_count", 0) + d.get("receipt_review_count", 0)
    photo = d.get("photo_count", 0)
    blog = d.get("blog_review_count", 0)
    comp = d.get("competitor_avg_review", 0)
    keywords = d.get("keywords", [])
    kw = keywords[0].get("keyword", "") if keywords and isinstance(keywords[0], dict) else (keywords[0] if keywords else "")
    region = ""
    for token in addr.split():
        if token.endswith("시") or token.endswith("구") or token.endswith("군"):
            region = token.replace("시", "").replace("군", "")
            break
    return f"""업체명: {biz}
업종: {cat}
주소: {addr}
지역: {region}
검색 키워드: {kw}
플레이스 순위: {rank}위{' (미노출)' if rank == 0 else ''}
리뷰 합계: {review}개 (경쟁사 평균 {comp}개)
사진: {photo}장
블로그 리뷰: {blog}건
""", region


def generate_diverse(d):
    summary, region = diag_summary(d)
    prompt = f"""한 가게 진단 결과 받음. 1 차 첫 접촉 + 자영업자가 보일 8 가지 다양한 응답 시나리오에 대한 너의 답신 메시지 생성.

# 진단
{summary}

# 출력 (헤더 그대로 박고 본문만)

## [1차 — 첫 접촉]
5 단계 로직 그대로 (인사 → 분석 명분 → 한 가지 아쉬운 점 → [진단 PDF] 첨부 → 훈훈 마무리). 추측 수치/돈 얘기 X.

---

## [응답 시나리오 1: 관심 — "어떻게 하면 되는데요?"]
PDF 본 후 관심. 컨설턴트 detail. 가격 슬쩍 첫 언급.

## [응답 시나리오 2: 사기 의심 — "대행사 사기 많이 봤는데, 어떻게 믿어요?"]
신뢰 회복. 1개월 단위 + 환불 보장 + 포트폴리오/케이스 hint. 변명 X 솔직.

## [응답 시나리오 3: 시간 핑계 — "지금 바빠서요, 나중에 봐도 돼요?"]
부드러운 hold + 확실한 다음 trigger ("다음 시즌" / "PDF 만 잠깐 5분"). 압박 X.

## [응답 시나리오 4: 효과 의심 — "진짜 효과 있어요? 다른 데서도 똑같은 말 하던데"]
정직한 응답. 효과 보장 단언 X 단 데이터/케이스로 reframe. 추측 수치 X.

## [응답 시나리오 5: 가격 거절 — "얼마예요? 비쌀 것 같은데요"]
가격 정직 (38만 부터). 가치 reframe + 1개월 환불 보장. 협상 양보 X.

## [응답 시나리오 6: 본인 홀딩 — "우리 가게는 손님 충분해요, 신경 안 써도 되는데요"]
존중 + 미래 risk 1 줄 ("지금 안 하셔도 OK 단 경쟁사 변할 때 ..."). 강요 X.

## [응답 시나리오 7: 가격 협상 — "좀 깎아줄 수 있어요? 30만에 시작하면 안 돼요?"]
가격 frozen. 양보 X. "패키지 38/56/95 가 정상가 / 첫 달 trial 외엔 할인 X". 정중.

## [응답 시나리오 8: 클로징 결정 — "그럼 한 번 해볼게요"]
가입 절차. "신청합니다 한 마디" / 결제 (네이버 페이 / 계좌이체) 안내. 따뜻한 마무리.

각 분기 톤 다르게. v2.1 페르소나 (상권 분석가 / 컨설턴트 / 대표 대 대표 / 줄바꿈 / 문어체+구어체) 일관."""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT_V2,
        generation_config={"temperature": 0.7},
    )
    resp = model.generate_content(prompt)
    return summary, resp.text


async def main():
    names = list_businesses(EXCEL)
    print(f"양주 db 가게 총 {len(names)}개. random 3 추출.")
    sample = random.sample(names, min(3, len(names)))
    print(f"  추출: {sample}\n")

    date_str = datetime.now().strftime("%Y%m%d_%H%M")

    for idx, biz in enumerate(sample, 1):
        print(f"\n{'='*60}\n[{idx}/3] 진단 시작: {biz}\n{'='*60}")
        try:
            data = await run_diagnosis(biz)
            if not data:
                print(f"  진단 fail — skip")
                continue
            if not data.get("business_name"):
                data["business_name"] = biz

            print(f"  v2.1 다양 시나리오 메시지 생성 중...")
            summary, messages = generate_diverse(data)

            md = f"""# {biz} — v2.1 다양 응답 시나리오
> v2.1 = 상권 분석가 / 마케팅 컨설턴트 페르소나 (Lian 사인)
> 생성일: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 진단 요약

```
{summary}
```

## 1차 첫 접촉 + 8 응답 시나리오

{messages}

---
*sales_orchestrator_v2.py / session 28 Lian directive 2026-04-27 (다양 시나리오 batch)*
"""
            out_path = DESKTOP / f"{biz}_v2_diverse_{date_str}.md"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  ✅ 저장: {out_path.name}")
        except Exception as e:
            print(f"  ❌ fail: {e}")

    print(f"\n{'='*60}\n완료. 바탕화면 확인.\n{'='*60}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
