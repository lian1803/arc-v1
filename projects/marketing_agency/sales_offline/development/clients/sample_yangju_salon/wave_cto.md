# CTO 분석 — 소상공인 네이버 플레이스 영업툴

> 작성일: 2026-04-01
> 작업 범위: naver-diagnosis/ 기존 코드 업그레이드 (새 폴더 금지)
> 기준 문서: CLAUDE.md + PRD.md

---

## 1. 기존 코드 현황 평가

### 잘 된 것

| 항목 | 평가 |
|------|------|
| FastAPI + lifespan 패턴 | Playwright 브라우저를 앱 시작/종료에 맞게 올바르게 관리함 |
| SQLAlchemy 2.0 Mapped 스타일 | 타입 안전한 모델 정의, to_dict() 완비 |
| 비동기 DB 세션 | async_session_maker 일관 사용, get_db() 의존성 주입 패턴 정상 |
| CrawlJob 상태 관리 | pending/searching/crawling/analyzing/generating/done/failed 단계 분리, 서버 재시작 시 자동 초기화 |
| 크롤링 이중 전략 | crawl_from_search(place_id 없을 때) + crawl_place_detail(place_id 있을 때) 분리, 폴백 로직 존재 |
| 경쟁사 분석 | CompetitorAnalyzer 별도 분리, 타임아웃 12초 + 업종별 폴백 상수 적용 |
| 메시지 생성 | message_generator.py 이미 구현됨 — 1~4차, A/B/C 분기, 4차 보류/무응답/비싸다/직접 4종 |
| 영업 우선순위 | _auto_priority() 구현됨, crawl.py + batch.py 양쪽에서 호출 |
| PPT 손익분기 슬라이드 | _create_breakeven_slide() 구현됨, 패키지별 손익분기 계산 포함 |
| Semaphore 보호 | _crawl_semaphore = asyncio.Semaphore(3) — 동시 크롤링 3개 제한 |
| 배치 처리 | batch_processor.py + batch.py 구현됨, openpyxl 파싱 + 업체명 컬럼 자동 감지 |

### 문제 있는 것

| 항목 | 문제 | 심각도 |
|------|------|--------|
| crawl_place() 메서드 없음 | batch.py의 `_do_crawl`에서 `crawler.crawl_place(place_id, business_name)` 호출하지만 NaverPlaceCrawler에 해당 메서드가 없음 — crawl_place_detail()만 존재 | CRITICAL |
| _auto_priority 중복 정의 | batch.py에 정의 후 crawl.py에서 `from routers.batch import _auto_priority` — 순환 import 아님이나 배치/단건 로직이 분산됨 | MEDIUM |
| models.py에 sales_priority 필드 없음 | priority_tag(str)는 있으나 PRD에서 요구하는 "핫/웜/패스" 영문 enum 필드가 없고 main.py에서 동적 속성으로 우회 중 | MEDIUM |
| batch_processor.py 인메모리 저장소 | _batch_store = {} — 서버 재시작 시 배치 이력 전부 소멸 | LOW (개인툴이므로 허용) |
| 크롤링 데이터 신뢰도 | _extract_review_counts, _extract_photo_count 가 inner_text() 기반 정규식 파싱 — DOM 구조 변경 시 즉시 0 반환 | HIGH |
| naver_place_rank 미수집 | crawl_place_detail/crawl_from_search 어디서도 순위(rank) 크롤링 로직 없음 — DB에는 필드 있으나 항상 0 | HIGH |
| result.html 미확인 | 메시지 탭 표시 구조는 main.py _build_template_messages()에 있으나 템플릿 파일 실물 확인 필요 | MEDIUM |

### 크롤링 성공 가능성 분석

현재 크롤러는 3단계 전략을 사용:

1. **inner_text() 정규식 파싱** (1차): 리뷰 수(`\d+개`), 사진 수(`사진 \d+`) — 네이버가 텍스트 렌더링 방식 바꾸면 즉시 실패
2. **iframe 전체 HTML 검색** (2차): keywordList JSON 추출 — 비교적 안정적
3. **/photo 별도 페이지 접근** (3차): 사진 수 폴백 — place_id 있어야 동작

핵심 리스크: 네이버 모바일 플레이스는 React SPA로 DOM이 자주 바뀜. `networkidle` 대기가 현재 30초 타임아웃인데, SPA 특성상 networkidle 도달 후에도 데이터 렌더링이 늦을 수 있음.

### message_generator.py 현재 상태

**구현 완료 (사용 가능)**:
- generate_all_messages(data: dict) -> dict 함수 존재
- 1차: type A/B/C 자동 선택 + text/label 반환
- 2차: 진단 요약 카드 텍스트
- 3차: 업종별 객단가 + 패키지 추천 + 손익분기 계산
- 4차: 보류/무응답/비싸다/직접 4종

result.html에서 _build_template_messages()로 변환 후 표시. 메시지 탭 UI는 main.py에 변환 로직까지 완비됨.

**남은 문제**: 메시지 탭 "복사" 버튼이 result.html 템플릿에 실제로 구현되어 있는지 확인 필요.

---

## 2. PRD Must Have 구현 계획

### 2-1. CRITICAL 버그 수정 (우선순위 0 — 나머지 전부 막힘)

**문제**: batch.py의 `_do_crawl`이 `crawler.crawl_place()` 호출 → 메서드 없어서 AttributeError

**수정 위치**: `naver-diagnosis/services/batch_processor.py`의 `_do_crawl` 콜백 내부

현재 코드:
```python
crawl_data = await crawler.crawl_place(place_id, business_name)
```

수정:
```python
crawl_data = await crawler.crawl_place_detail(place_id)
if not crawl_data or not crawl_data.get("place_id"):
    # place_id로 실패 시 검색 기반 크롤링 폴백
    crawl_data = await crawler.crawl_from_search(business_name)
```

`batch_processor.py`는 `_do_crawl` 팩토리를 `batch.py`에서 정의하므로 수정 위치는 `routers/batch.py` 내 `_crawl_callback_factory`.

### 2-2. 영업 메시지 자동 생성 [현재 90% 완성]

**구현 상태**: message_generator.py, routers/message.py 전부 존재. 단건 진단(crawl.py)에서 messages 자동 생성 후 DB 저장까지 완료.

**남은 작업**: result.html에 메시지 탭 + 복사 버튼 확인/보완

함수 시그니처 (현재 구현):
```python
# services/message_generator.py
def generate_all_messages(data: dict) -> dict:
    """
    반환 구조:
    {
      "first": {"type": "A"|"B"|"C", "text": str, "label": str},
      "second": str,
      "third": str,
      "fourth": {"보류": str, "무응답": str, "비싸다": str, "직접": str},
      "estimated_lost_customers": int,
    }
    """
```

A/B/C 분기 로직 (현재 구현):
```python
# A: competitor_avg_review >= my_review * 5
# B: rank > 10 AND top_keyword_volume >= 500
# C: news_last_days >= 90 OR bookmark_count == 0
# 기본값: A
```

result.html 메시지 탭 추가 시 주의사항:
- `_build_template_messages()` 변환 결과 구조를 그대로 사용
- 각 메시지 아래 "복사" 버튼: `navigator.clipboard.writeText(text)` Vanilla JS
- 4차 메시지는 4개 탭(보류할때/무응답/비싸다/직접) 형태로 표시

### 2-3. PPT 영업 제안서화 [현재 구현 확인 필요]

**구현 상태**: ppt_generator.py에 이미 9슬라이드 구성 + _create_breakeven_slide() 존재

현재 슬라이드 구성 (generate() 메서드 기준):
1. 표지 (충격 문구 "매달 N명이 경쟁사로" 포함)
2. 현황 분석 (7개 항목 점수)
3. 세부 체크리스트
4. 개선사항
5. 키워드 분석
6. 연관 키워드
7. 경쟁사 비교 (있으면)
8. 손익분기 계산 (신규 구현됨)
9. 마케팅 제안

손실 고객 수 계산 공식 (현재 message_generator.py 기준):
```
rank 1~3:  CTR 30%, 손실 = (30% - 내 CTR) * 월검색
rank 4~10: CTR 15%
rank 11~20: CTR 5%
rank 20+:  CTR 2%
```

PRD 요구 CTR 테이블과 차이:
- PRD: 1위 35%, 2위 17%, 3위 12%, 4~10위 4~8%, 10위+ 1~2%
- 현재: 1~3위 30% 고정, 4~10위 15%, 11~20위 5%, 20위+ 2%

수정 필요 (message_generator.py의 _estimate_lost_customers):
```python
CTR_TABLE = {1: 0.35, 2: 0.17, 3: 0.12}
# 4~10위: 0.04~0.08 선형 보간
# 10위+: 0.01~0.02

def _ctr_for_rank(rank: int) -> float:
    if rank <= 0: return 0.35  # 순위 미확인시 1위 가정
    if rank in CTR_TABLE: return CTR_TABLE[rank]
    if rank <= 10: return 0.08 - (rank - 4) * 0.006  # 4위=8%, 10위=4.4%
    if rank <= 20: return 0.02
    return 0.01
```

손익분기 슬라이드 확인 필요 항목:
- avg_price 계산 소스: config/industry_weights.py의 get_avg_price() 활용 중인지 확인
- 패키지 3종(주목 290만/집중 490만/시선 890만) 상수 올바른지 확인

### 2-4. 영업 우선순위 자동 분류 [현재 구현됨]

**구현 상태**: _auto_priority() 함수 batch.py에 정의, crawl.py에서 import 사용

현재 로직:
```python
# 1순위: D등급 + (사진<10 OR 리뷰<10 OR 순위>10 OR 블로그<5) 중 2개 이상
# 1순위: (C/D등급) + review < competitor_avg_review / 2
# 패스: A등급
# 그 외: 2순위
```

PRD 기준과 비교:
- "프랜차이즈 본사 직영, 최신 리뷰 1년+ 된 업체 → 패스" 조건이 현재 없음
- 추가 필요 조건: 업체명에 "본점", "직영" 포함 시 패스 처리

models.py 필드 현황:
- `priority_tag: Mapped[Optional[str]]` — "1순위"/"2순위"/"패스" 문자열로 이미 저장
- main.py에서 _priority_map = {"1순위": "1", "2순위": "2", "패스": "pass"}로 동적 변환
- DB 마이그레이션 불필요 — 이미 컬럼 존재

**추가 필요한 것만**: _auto_priority()에 프랜차이즈 패스 조건 1줄 추가

```python
# 프랜차이즈 패스 조건 추가 위치 (기존 grade=="A" 체크 앞에 삽입)
franchise_keywords = ["본점", "직영", "체인", "가맹"]
business_name = data.get("business_name", "")
if any(kw in business_name for kw in franchise_keywords):
    return "패스"
```

history.html 필터링/정렬은 기존 priority_tag 필드를 기준으로 JS에서 처리 가능.

### 2-5. xlsx 배치 처리 [현재 구현됨, CRITICAL 버그만 수정하면 작동]

**구현 상태**: services/batch_processor.py + routers/batch.py 완성

현재 구현:
- parse_xlsx(file_path) → List[str] 업체명 목록
- BUSINESS_NAME_CANDIDATES 배열로 헤더 자동 감지 (업체명, 상호명, 상호, 업체, 가게명 등)
- 인메모리 _batch_store로 배치 상태 관리
- POST /batch/start: 파일 경로 입력 → 백그라운드 순차 진단

**유일한 문제**: crawler.crawl_place() → crawler.crawl_place_detail() 수정 필요 (2-1항 참고)

openpyxl 이미 requirements.txt에 있음 (openpyxl==3.1.2).

---

## 3. Engineering Rules (이 프로젝트용)

### R1: 기존 코드 최소 변경 원칙
- 새 파일 생성 없이 기존 파일 내 함수 추가/수정으로 해결
- 기존 함수 삭제 금지 — 내부 로직만 교체
- to_dict()와 Pydantic 모델의 필드 목록은 건드리지 마라

### R2: Playwright async 주의사항
- page는 반드시 finally 블록에서 await page.close()
- context는 page 닫은 후 await context.close() (현재 context.close() 누락 여부 확인 필요)
- browser는 app.state에서 가져옴 — 직접 생성 금지
- `await page.wait_for_load_state("networkidle")` 이후에도 데이터가 없으면 500ms wait_for_timeout 재시도 최대 3회
- 크롤링 함수는 반드시 Semaphore(_crawl_semaphore) 하에서 실행

### R3: SQLite 동시성 처리
- aiosqlite는 단일 writer 방식 — 배치 중 단건 진단 충돌 방지법:
  - 배치는 업체당 3~5초 딜레이(현재 구현됨)
  - 단건 진단은 별도 async_session_maker() 세션 — 트랜잭션 범위 최소화
  - DB_RESET=true는 개발 시에만 — 프로덕션에서 절대 사용 금지
- WAL 모드 활성화 권장 (현재 없음):
  ```python
  # database.py engine 생성 시 connect_args 추가
  engine = create_async_engine(
      DATABASE_URL,
      echo=False,
      future=True,
      connect_args={"check_same_thread": False},
  )
  # lifespan에서 PRAGMA wal_mode=WAL 실행
  ```

### R4: 에러 핸들링 — 크롤링 실패 시 수동 입력 우회
- 크롤링 실패 시 result는 빈 값(0, False)으로 채워진 dict 반환 — None 반환 금지
- 배치에서 단건 실패 시 해당 업체만 error 상태로 표시하고 다음 업체 계속 진행
- API 키(네이버 검색광고 API) 만료 시 keyword_score = 0으로 폴백 — 에러 전파 금지
- 사용자가 /manual 경로로 수동 입력 시 크롤링 없이 점수 계산 → PPT 생성 가능 (이미 구현됨)

### R5: 메시지 복사 UX
- 각 메시지 박스 아래 복사 버튼은 async clipboard API 사용:
  ```javascript
  async function copyText(text) {
    await navigator.clipboard.writeText(text);
    // 버튼 텍스트 "복사됨!" 으로 1.5초 변경 후 원복
  }
  ```
- HTTPS 없어도 localhost에서는 clipboard API 동작함

---

## 4. 파일별 수정/신규 목록

| 파일 | 신규/수정 | 주요 변경 | 우선순위 |
|------|----------|---------|---------|
| `routers/batch.py` | 수정 | `_crawl_callback_factory` 내 `crawler.crawl_place()` → `crawler.crawl_place_detail()` + 폴백 추가 | P0 CRITICAL |
| `routers/batch.py` | 수정 | `_auto_priority()`에 프랜차이즈 패스 조건 추가 | P2 |
| `services/message_generator.py` | 수정 | `_estimate_lost_customers()`의 CTR 테이블을 PRD 기준(1위 35%, 2위 17%, 3위 12%)으로 수정 | P1 |
| `templates/result.html` | 수정 | 메시지 탭 UI 확인 + "복사" 버튼 Vanilla JS 추가 (없으면 추가, 있으면 클립보드 동작 확인) | P1 |
| `templates/history.html` | 수정 | 우선순위별 필터 드롭다운 + 정렬 기능 JS 추가 | P2 |
| `database.py` | 수정 | WAL 모드 PRAGMA 추가 (배치 중 단건 진단 안정성) | P2 |
| `services/naver_place_crawler.py` | 수정 | context.close() 누락 여부 확인 + 필요 시 finally 블록에 추가 | P2 |
| `config/industry_weights.py` | 확인 | get_avg_price(), PACKAGES 상수 PRD 값과 일치 여부 확인 | P1 |

**신규 파일 없음** — PRD 4개 Must Have가 이미 구현된 것으로 확인됨. 버그 수정 + 미세 조정이 핵심.

---

## 5. 리스크 및 해결책

### R1: 네이버 DOM 변경 리스크
- 심각도: HIGH
- 빈도: 2~3개월마다 React SPA 업데이트로 셀렉터 변경
- 현재 방어: inner_text() 정규식(1차) + iframe HTML 파싱(2차) + 별도 /photo 페이지(3차) 3단계 폴백
- 추가 방어책:
  - 크롤링 결과가 모두 0일 때 result.html에 "자동 수집 실패 — 직접 입력으로 계속하기" 버튼 노출
  - /manual 엔드포인트로 리다이렉트 파라미터 전달 (business_name 유지)
- 장기 대응: 핵심 수치(리뷰 수, 사진 수)는 JSON API 엔드포인트(`m.place.naver.com/restaurant/{id}/review`) 직접 호출로 교체 검토

### R2: 크롤링 속도 (배치 처리 시)
- 현재: 업체당 평균 15~30초 (place_id 검색 + 상세 크롤링 + 경쟁사 분석)
- 30건 배치 = 7.5~15분 소요
- 배치 딜레이 3초 포함 시 30건 = 최대 18분
- 해결책:
  - 배치 중 경쟁사 분석 타임아웃을 12초에서 8초로 단축 (이미 폴백 있음)
  - 진행률 실시간 SSE(Server-Sent Events) 표시 — 현재 /batch/status 폴링 방식 유지 (리안 1인 사용이므로 충분)
  - 배치 중 단건 진단 요청 차단 안 함 — Semaphore(3) 덕분에 자연스럽게 큐잉됨

### R3: 네이버 검색광고 API 키 만료
- 현재 대응: try/except로 감싸고 keyword_score = 0 폴백
- 추가 필요: 앱 시작 시 API 키 유효성 사전 체크 + /health 엔드포인트에 naver_ad_api_ok 필드 추가
- 폴백 시 result.html에 "키워드 검색량 조회 실패 (API 키 확인 필요)" 표시

### R4: 순위(rank) 미수집 문제
- 현재 naver_place_rank = 0 고정 (크롤러에서 수집 안 함)
- 영향: 메시지 B형(손실 고객형) 조건 "rank > 10"이 항상 false → B형 메시지 미발동
- 단기 해결: 검색 결과 페이지에서 업체 순서(1~5위) 텍스트 파싱 추가
  ```python
  # crawl_from_search()에서 업체명 위치로 순위 추정
  # 검색 결과 내 몇 번째로 등장하는지 인덱스로 rank 설정
  ```
- 이 수정 없으면 rank 기반 CTR 계산이 전부 "순위 미확인" 0 반환

---

## 6. 배포 블로커 체크리스트 (PRD 4개 항목)

| 블로커 | 상태 | 해결 방법 |
|--------|------|---------|
| Playwright 크롤링 성공률 | 미테스트 | 서버 기동 후 테스트 업체 3~5개 수동 진단으로 확인 |
| crawler.crawl_place() 메서드 없음 | CRITICAL | batch.py에서 crawl_place_detail()로 수정 (10분 작업) |
| CTR 테이블 PRD 불일치 | 코드 있음/값 다름 | message_generator.py _estimate_lost_customers() 수정 |
| 메시지 복사 버튼 | 미확인 | result.html 템플릿 확인 후 없으면 추가 |
| 네이버 검색광고 API 키 | .env 확인 필요 | NAVER_AD_API_KEY, NAVER_AD_SECRET_KEY, NAVER_AD_CUSTOMER_ID |

---

## 결론

코드베이스는 PRD 4개 Must Have가 **이미 대부분 구현되어 있는 상태**다.

- message_generator.py: 완성
- ppt_generator.py 손익분기 슬라이드: 완성
- 영업 우선순위 분류: 완성
- xlsx 배치 처리: 완성

**지금 당장 돌아가지 않는 이유는 단 하나**: `crawler.crawl_place()` 메서드가 없어서 배치 처리가 AttributeError 발생. 이 버그 1개 수정 + CTR 테이블 값 보정 + result.html 복사 버튼 확인이 전부다.

FE/BE는 버그 수정에 집중하면 된다. 아키텍처 재설계 불필요.
