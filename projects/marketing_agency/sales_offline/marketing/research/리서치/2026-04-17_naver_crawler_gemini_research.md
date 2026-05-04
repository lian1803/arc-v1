# 리서치: 네이버 크롤러 + Gemini Vision + 벤치마크 패턴
조사일: 2026-04-17

---

## 1. 네이버 플레이스 크롤러 후보

### 1.1 omnyx2/naver_place_crawling
- URL: https://github.com/omnyx2/naver_place_crawling
- Stars: 0 / 최근 커밋: 1개 커밋 (날짜 미표시)
- 스택: Selenium + BeautifulSoup4 + ChromeDriver
- 뽑는 필드: 음식점 정보 (상세 필드 목록 README 미기재, 코드 확인 필요)
- Top N 대량 수집: 네이버 서버가 검색어당 최대 5,000개 반환 → 지역 세분화(시→구→동) 필요
- 네이버 DOM 변경 대응도: **낮음** — README에 "현재 네이버 맵 음식점 검색 요청 URI 변경으로 툴 정상 작동 안 됨" 명시
- 봇 탐지 회피: 없음
- 적용 가능성: ★☆☆☆☆
- 판단: 이미 망가진 상태. 사용 불가.

### 1.2 seolhalee/Naver-Place-scraper
- URL: https://github.com/seolhalee/Naver-Place-scraper
- Stars: 1 / 최근 커밋: 불명 (4개 커밋)
- 스택: Jupyter Notebook (Python)
- 뽑는 필드: 장소 ID 추출 → 좌표 변환(UTM-K→WGS84) → 상관계수 계산. 리뷰수/평점 미수집
- Top N 대량 수집: 불명
- 네이버 DOM 변경 대응도: 불명 (코드 미공개)
- 봇 탐지 회피: 없음
- 적용 가능성: ★☆☆☆☆
- 판단: 리서치 목적 코드. 실용성 없음.

### 1.3 gpters.org 커뮤니티 구현 사례 (Selenium + Streamlit)
- URL: https://www.gpters.org/dev/post/created-naver-place-search-OM9tiP01t8fVH0i
- 스택: Selenium + Streamlit + ChromeDriver (2024년 4월 작성)
- 뽑는 필드: 업체명, 업체 ID, 검색 순위
- 구현 방식: 키워드로 네이버 검색 → "더보기" 클릭 → 무한 스크롤 → CSS 클래스 "place_bluelink"로 업체 추출
- 핵심 문제점: **네이버가 DOM을 자주 바꿔서 CSS 셀렉터 지속 수정 필요** (개발자 본인이 명시)
- 적용 가능성: ★★☆☆☆
- 판단: 순위 추적용이지 대량 수집용 아님. 패턴 참고만 가능.

### 1.4 Apify — Naver Map Search Results Scraper
- URL: https://apify.com/delicious_zebu/naver-map-search-results-scraper
- 스택: 상용 SaaS (코드 비공개)
- 뽑는 필드: 업체명, 주소, 전화번호, 평점
- 가격: $30/월 + 종량제
- Top N 대량 수집: 지원 여부 불명확 (페이지 수 파라미터 확인 필요)
- Stars: N/A, 사용자 172명, 평점 5.0
- 적용 가능성: ★★★☆☆
- 판단: 빠르게 데이터 필요하면 대안이 되나, 월 비용 발생 + 리뷰수/사진수 미지원이 치명적.

### 1.5 네이버 공식 Local Search API
- URL: https://developers.naver.com (openapi/v1/search/local.json)
- 스택: REST API (공식)
- 뽑는 필드: 업체명, 주소, 전화번호, 카테고리, 네이버 지도 URL
- **치명적 한계: display 파라미터 최대 5개**. 상위 50~100개 수집 불가.
- 리뷰수/평점/사진수: **미지원**
- 적용 가능성: ★☆☆☆☆
- 판단: 벤치마크 DB 구축 목적에 맞지 않음.

---

## 종합 판단 — 네이버 플레이스 크롤러

**결론: 쓸 만한 오픈소스가 없다. 자체 재작성이 맞다.**

이유:
- 기존 리포들이 DOM 변경으로 이미 고장났거나, 순위 추적 단일 목적이라 벤치마크 DB 구축에 부적합
- 네이버 공식 API는 display 5개 한계로 상위 N개 수집 불가
- 상용 Apify는 리뷰수/사진수를 뽑지 않아 핵심 지표 누락

**재작성 시 참고 패턴:**
- Playwright 기반 권장 (Selenium보다 빠르고 봇 탐지 회피 우수)
- 네이버 지도 내부 API 엔드포인트 직접 호출 방식 (DOM 셀렉터보다 안정적)
  - `https://pcmap.place.naver.com/place/list` 계열 XHR 요청 가로채기
  - Playwright의 `page.on('response', ...)` 이벤트로 내부 JSON 캡처
- 지역 세분화: 서울 25개 구 × 업종 키워드로 루프
- 수집 필드 목표: 업체명, 네이버ID, 평점, 리뷰수, 사진수, 영업시간, 업종, 위치

---

## 2. Gemini Vision 이미지 배치 분석 패턴

### 2.1 모델 선택 — 2026년 4월 기준 최신 상황

**중요 업데이트**: gemini-2.0-flash-lite-001은 2026년 3월 6일부로 신규 프로젝트 사용 불가. 기존 고객 전용.

| 모델 | 입력 토큰 비용 | 출력 토큰 비용 | 이미지당 토큰 | 비고 |
|------|-------------|-------------|------------|------|
| gemini-2.5-flash | $0.30/1M | $2.50/1M | 1,120 토큰/장 | 추론 기능, 이미지 무료 tier |
| gemini-2.5-flash-lite | $0.10/1M | $0.40/1M | 1,120 토큰/장 | 가성비 최고 |
| gemini-3.1-flash-lite | $0.25/1M | $1.50/1M | 1,120 토큰/장 | 품질↑ 속도 2.5x |

**이미지 20장 기준 비용 계산 (입력만)**:
- 이미지 20장 × 1,120 토큰 = 22,400 토큰
- gemini-2.5-flash-lite: 약 $0.0022 (20장당)
- gemini-2.5-flash: 약 $0.0067 (20장당)
→ 비용 부담 거의 없음. 품질 우선 선택 가능.

**권장: gemini-2.5-flash** — 이유: 추론 품질 우수, 이미지 분석 정확도, 비용도 허용 범위.

### 2.2 한 요청에 이미지 몇 장까지

- 공식 문서 기준: **최대 3,600개 파일** (HEIC/HEIF/JPEG/PNG/WEBP)
- 실용적 한계: 1M 토큰 컨텍스트 윈도우 내에서 처리
  - 이미지 20장 = 22,400 토큰 → 전혀 문제 없음
  - 이미지 50장 = 56,000 토큰 → 여전히 안전
- 레이턴시 증가 주의: 이미지 많을수록 응답 시간↑
- **매장 사진 10~20장 분석: 단일 요청으로 완전히 가능**

### 2.3 JSON 강제 방법 — 베스트 프랙티스

**방법 1: response_mime_type + response_schema (권장)**
```python
from google import genai
from pydantic import BaseModel
from typing import List

class StoreImageAnalysis(BaseModel):
    color_tone: str          # warm/cool/neutral/vibrant
    mood: str                # cozy/modern/casual/upscale/rustic
    style: str               # minimalist/industrial/traditional/etc
    target_customer: str     # 20s/30s/family/couple/etc
    cleanliness_score: int   # 1-5
    tags: List[str]          # 핵심 태그 5개 이내

client = genai.Client()

# 이미지 여러 장 + 구조화 출력
parts = [
    {"text": "아래 매장 사진들을 분석해서 컨셉과 분위기를 JSON으로 반환해줘."}
]
for img_path in image_paths:
    parts.append(client.files.upload(path=img_path))

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=parts,
    config={
        "response_mime_type": "application/json",
        "response_schema": StoreImageAnalysis
    }
)
result = response.parsed  # Pydantic 모델로 자동 파싱
```

**방법 2: Gemini Batch API (50% 할인, 비동기)**
```python
# JSONL 방식 — 여러 매장 동시 처리
batch_job = client.batches.create(
    model="gemini-2.5-flash",
    src=inline_requests,  # 각 요청에 이미지 리스트 포함
    config={
        "response_mime_type": "application/json",
        "response_schema": StoreImageAnalysis
    }
)
# 최대 24시간 비동기 처리, 비용 50% 절감
```

### 2.4 알려진 실패 패턴

- **structured output 토큰 반복 버그**: gemini-2.5-flash에서 `response_schema` 사용 시 max_tokens 도달 전까지 토큰 반복하는 버그 보고됨 (2026년 커뮤니티 이슈). `max_output_tokens` 명시적 설정으로 완화.
- **이미지 품질**: 저해상도/흐린 이미지 분석 결과 불안정. 전처리 권장.
- **언어 지정**: 한국어 태그 원하면 프롬프트에 "한국어로 응답" 명시 필수.
- **응답 스키마 토큰 비용**: 스키마 자체가 입력 토큰 소비. 필드 많을수록 비용↑.

---

## 3. 벤치마킹 시각화 패턴

### 3.1 업종별 산업 표준 지표 (외식업 기준)

| 지표 | 업계 기준 | 출처 |
|------|---------|------|
| 리뷰 누적 수 (풀서비스) | 400개+ = 건강한 수준 | BlackBox Intelligence |
| 평점 목표 | 4.25점 이상 | BlackBox Intelligence |
| 리뷰 플랫폼 점유율 | Google 96% | BlackBox Intelligence |
| 리뷰 수 분포 | 업종/지역별 상이 — 표준 없음 |  |
| 사진 수 벤치마크 | 업계 표준 데이터 미존재 |  |

**결론**: 외식업 리뷰수/사진수에 대한 공인된 분위수 기준치(p25/p50/p75/p90)는 존재하지 않는다. 우리가 실제 데이터를 수집해서 직접 산출해야 한다.

### 3.2 분위수 표기 시각화 사례

참고 패턴: DebugBear RUM 분위수 시각화 방식
- p50 = 중간값 (기준선)
- p75 = 상위 25% 진입 기준
- p90 = 상위 10% 진입 기준
- 수집한 데이터셋 내에서 `numpy.percentile()` 또는 `pandas.quantile()`로 동적 산출

```python
import numpy as np

review_counts = [12, 45, 78, 120, 230, 450, ...]  # 수집한 상위 100개 업체

benchmarks = {
    "p25": np.percentile(review_counts, 25),
    "p50": np.percentile(review_counts, 50),
    "p75": np.percentile(review_counts, 75),
    "p90": np.percentile(review_counts, 90),
}

# 특정 업체 점수: "당신의 리뷰 수 78개는 상위 몇 %?"
from scipy import stats
percentile_rank = stats.percentileofscore(review_counts, target_store_reviews)
```

### 3.3 점수화 방식 — 분위수 기반 등급

```python
def score_metric(value, benchmarks):
    if value >= benchmarks["p90"]: return 5  # 상위 10%
    elif value >= benchmarks["p75"]: return 4  # 상위 25%
    elif value >= benchmarks["p50"]: return 3  # 중간 이상
    elif value >= benchmarks["p25"]: return 2  # 하위 25~50%
    else: return 1  # 하위 25%
```

---

## 최종 권고

### 권고 1: 네이버 플레이스 크롤러 — 재작성하되 Playwright + XHR 가로채기 방식

**바로 적용할 오픈소스 없음.** 모든 기존 리포가 DOM 변경으로 고장났거나 용도 불일치.

재작성 방향:
- Playwright `page.on('response', callback)` 으로 내부 JSON API 엔드포인트 캡처
- CSS 셀렉터 의존 금지 → 내부 API JSON 파싱
- 통합 난이도: 중 (2~3일)
- 기대 효과: 안정적인 Top 50~100 대량 수집, DOM 변경에 강함

### 권고 2: Gemini Vision — 바로 적용 가능, 모델은 gemini-2.5-flash 사용

**현재 우리 시스템에 바로 적용 가능.** `response_schema` + Pydantic 패턴 그대로 쓰면 됨.

- gemini-2.0-flash-lite는 신규 프로젝트 사용 불가 → gemini-2.5-flash 또는 2.5-flash-lite 전환
- 이미지 20장 단일 요청: 완전히 가능, 비용 $0.007 이하
- 통합 난이도: 하 (1일)
- 기대 효과: 매장 사진 → 컬러톤/무드/타겟 자동 태깅

### 권고 3: 벤치마크 분위수 — 자체 산출, numpy/scipy 표준 함수 활용

**업계 공인 지표 없음.** 네이버 플레이스 상위 업체 데이터 수집 후 직접 p25/p50/p75/p90 산출.

- 추가 라이브러리 불필요 (numpy/scipy 이미 설치됨)
- 통합 난이도: 하 (0.5일)
- 기대 효과: "우리 매장은 리뷰수 상위 22%" 형태의 정확한 포지셔닝

---

## 참고 URL

- https://github.com/omnyx2/naver_place_crawling
- https://github.com/seolhalee/Naver-Place-scraper
- https://www.gpters.org/dev/post/created-naver-place-search-OM9tiP01t8fVH0i
- https://apify.com/delicious_zebu/naver-map-search-results-scraper
- https://ai.google.dev/gemini-api/docs/batch-api
- https://ai.google.dev/gemini-api/docs/pricing
- https://blackboxintelligence.com/blog/restaurant-review-benchmarks-industry-overview/
- https://artificialanalysis.ai/models/gemini-2-5-flash-lite
