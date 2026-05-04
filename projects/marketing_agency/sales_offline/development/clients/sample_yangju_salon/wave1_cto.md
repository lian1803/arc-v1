# CTO 분석 -- 소상공인 네이버 플레이스 영업툴 업그레이드

## 기술 스택 결정

| 항목 | 선택 | 이유 |
|------|------|------|
| Backend | FastAPI (기존 유지) | 비동기 처리, Playwright 연동 이미 안정 |
| 크롤링 | Playwright (기존 유지) | 네이버 플레이스 동적 렌더링 대응 |
| PPT | python-pptx (기존 유지) | 슬라이드 추가만 하면 됨 |
| DB | SQLite + SQLAlchemy 2.0 async (기존 유지) | 1인 사용 툴에 충분, 마이그레이션 불필요 |
| xlsx 처리 | openpyxl (신규 추가) | 표준 라이브러리, python-pptx와 동일 생태계 |
| Frontend | Jinja2 + Vanilla JS (기존 유지) | 프레임워크 도입 오버킬, 페이지 2-3개 수준 |
| 배포 | 로컬 실행 (현행) | 리안 1인 사용, 배포 불필요 |

추가 패키지: `openpyxl` 1개만 설치하면 됨. 그 외 신규 의존성 없음.

---

## 아키텍처

```
[기존 유지]                          [신규 추가]

main.py (FastAPI)
  |
  +-- routers/
  |     +-- search.py               (변경 없음)
  |     +-- crawl.py                (경쟁사 크롤링 로직 추가)
  |     +-- manual.py               (변경 없음)
  |     +-- ppt.py                  (변경 없음)
  |     +-- history.py              (변경 없음)
  |     +-- batch.py                *** 신규: xlsx 업로드 + 배치 진단
  |     +-- message.py              *** 신규: 영업 메시지 생성 API
  |
  +-- services/
  |     +-- naver_place_crawler.py  (경쟁사 크롤링 메서드 추가)
  |     +-- naver_search_ad.py      (변경 없음)
  |     +-- scorer.py               (업종별 가중치 + 상대점수 + 패널티)
  |     +-- ppt_generator.py        (경쟁사 비교 + 손익분기 슬라이드 추가)
  |     +-- message_generator.py    *** 신규: 1-4차 메시지 자동 생성
  |     +-- batch_processor.py      *** 신규: xlsx 파싱 + 큐 처리
  |     +-- competitor.py           *** 신규: 경쟁사 분석 로직
  |
  +-- models.py                     (CompetitorData 모델 + BatchJob 모델 추가)
  +-- database.py                   (변경 없음)
  +-- browser_manager.py            (변경 없음)
  +-- config/
        +-- industry_weights.py     *** 신규: 업종별 가중치 설정
```

---

## 파일별 수정 계획

### 1. 기존 파일 수정

#### `services/scorer.py` -- 핵심 변경
- `WEIGHTS` 딕셔너리를 업종별 분기로 변경
- `INDUSTRY_WEIGHTS` 상수 추가 (industry_weights.py에서 import)
- `calculate_all()` 에 `category` 파라미터 추가 -> 업종 감지 -> 가중치 자동 적용
- `calculate_relative_score()` 클래스 메서드 신규 추가: 경쟁사 평균 대비 상대 점수
- `calculate_news_penalty()` 정적 메서드 추가: 새소식 90일+ 미업데이트 시 감점
- `calculate_save_bonus()` 정적 메서드 추가: 저장수 반영
- `calculate_reply_rate_score()` 추가: 최근 10개 리뷰 기준 답글률
- 기존 `calculate_total_score()` 수정: 패널티/보너스 적용 후 최종 점수 산출

#### `services/naver_place_crawler.py` -- 경쟁사 크롤링 추가
- `crawl_competitors()` 메서드 추가: 같은 지역+업종 키워드로 상위 5개 업체 검색 -> 각각 기본 데이터 수집
- `crawl_place_detail()` 에 새소식 최종 업데이트일, 저장수, 사장님 답글률 수집 로직 추가
- 기존 크롤링 로직은 건드리지 않음. 메서드만 추가

#### `services/ppt_generator.py` -- 슬라이드 추가
- 기존 7슬라이드 유지
- 슬라이드 2 뒤에 "경쟁사 비교" 슬라이드 삽입 (내 업체 vs 지역 1위 vs 지역 평균, 항목별 막대 비교)
- 슬라이드 4 뒤에 "손익분기 계산" 슬라이드 삽입 (패키지별 필요 신규 고객 수 시각화)
- 표지 메시지 강화: "매달 N명의 고객이 경쟁사로" 문구 자동 생성
- 최종 PPT: 9슬라이드

#### `routers/crawl.py` -- 경쟁사 크롤링 통합
- `run_crawl_job()` 에 경쟁사 크롤링 단계 추가 (crawling과 analyzing 사이)
- 경쟁사 데이터를 DiagnosisHistory에 함께 저장

#### `models.py` -- 모델 확장
- `DiagnosisHistory` 에 컬럼 추가:
  - `competitor_data: JSON` (경쟁사 평균 데이터)
  - `competitor_rank: int` (경쟁사 대비 순위)
  - `news_last_updated: DateTime` (새소식 최종 업데이트일)
  - `save_count: int` (저장수)
  - `owner_reply_rate: float` (답글률)
  - `sales_priority: str` (영업 우선순위: 1순위/2순위/패스)
  - `relative_score: float` (경쟁사 대비 상대 점수)
  - `messages: JSON` (생성된 영업 메시지)
- `BatchJob` 모델 신규 추가:
  - `id, filename, total_count, completed_count, status, created_at`
  - `results: JSON` (업체별 진단 결과 ID 목록)

### 2. 신규 파일

#### `config/industry_weights.py`
업종별 가중치 설정 파일. 하드코딩이 아니라 딕셔너리로 관리.

```python
INDUSTRY_WEIGHTS = {
    "미용실": {"photo": 0.20, "review": 0.15, "blog": 0.10, "info": 0.10, "keyword": 0.10, "convenience": 0.15, "engagement": 0.20},
    "네일":   {"photo": 0.20, "review": 0.15, "blog": 0.10, "info": 0.10, "keyword": 0.10, "convenience": 0.15, "engagement": 0.20},
    "식당":   {"photo": 0.10, "review": 0.25, "blog": 0.15, "info": 0.15, "keyword": 0.10, "convenience": 0.10, "engagement": 0.15},
    "카페":   {"photo": 0.20, "review": 0.20, "blog": 0.15, "info": 0.10, "keyword": 0.10, "convenience": 0.10, "engagement": 0.15},
    "학원":   {"photo": 0.05, "review": 0.25, "blog": 0.20, "info": 0.15, "keyword": 0.15, "convenience": 0.10, "engagement": 0.10},
    "피부관리": {"photo": 0.15, "review": 0.20, "blog": 0.15, "info": 0.10, "keyword": 0.10, "convenience": 0.15, "engagement": 0.15},
    # "default"는 기존 가중치 그대로
    "default": {"photo": 0.15, "review": 0.20, "blog": 0.10, "info": 0.15, "keyword": 0.10, "convenience": 0.15, "engagement": 0.15},
}

# 업종별 평균 객단가 (손익분기 계산용)
INDUSTRY_AVG_PRICE = {
    "미용실": 65000,
    "네일": 50000,
    "식당": 20000,
    "카페": 8000,
    "학원": 300000,
    "피부관리": 100000,
    "default": 30000,
}
```

#### `services/competitor.py`
경쟁사 분석 전담 서비스.

- `CompetitorAnalyzer` 클래스
- `analyze(target_data, competitor_list)` -> 상대 점수, 순위, 평균 대비 차이
- 경쟁사 크롤링 결과를 받아서 비교 분석만 담당
- 크롤링 자체는 `naver_place_crawler.py`가 수행

#### `services/message_generator.py`
영업 메시지 자동 생성기.

- `SalesMessageGenerator` 클래스
- `generate_all(diagnosis_data, competitor_data)` -> 1~4차 메시지 전부 생성
- 1차 메시지: A/B/C 버전 자동 판별 로직
  - A (리뷰 격차형): `competitor_avg_review >= target_review * 5`
  - B (손실 고객형): `naver_place_rank > 10 AND monthly_search >= 500`
  - C (방치형): `news_days_ago >= 90 OR save_count == 0`
- 2차: 진단 결과 카톡 카드 포맷 텍스트
- 3차: 패키지 추천 + 손익분기 숫자 자동 계산
- 4차: 보류/무응답 대응
- 출력: `{"first": {"version": "A", "text": "..."}, "second": "...", "third": "...", "fourth": "..."}`

#### `services/batch_processor.py`
xlsx 배치 처리 서비스.

- `BatchProcessor` 클래스
- `parse_xlsx(file_path)` -> 업체 목록 파싱 (업체명 컬럼 자동 감지)
- `process_batch(batch_job_id, business_list, browser)` -> 순차 크롤링 + 진단
- 동시 크롤링 제한: 1개 (배치에서는 순차 처리, 서버 부하 방지)
- 각 업체 완료 시 `BatchJob.completed_count` 업데이트
- 완료 후 영업 우선순위 자동 태깅

#### `routers/batch.py`
배치 처리 라우터.

- `POST /batch/upload` -- xlsx 파일 업로드 -> BatchJob 생성 -> 백그라운드 처리
- `GET /batch/status/{batch_id}` -- 배치 진행 상태 조회
- `GET /batch/results/{batch_id}` -- 배치 결과 목록 (우선순위별 정렬)

#### `routers/message.py`
영업 메시지 라우터.

- `GET /message/{history_id}` -- 진단 이력 기반 1~4차 메시지 생성
- `POST /message/generate` -- 커스텀 데이터로 메시지 생성

---

## 경쟁사 비교 크롤링 전략

### 방법
1. 타겟 업체의 `address`에서 지역명 추출 (예: "양주시 덕계동" -> "양주")
2. 타겟 업체의 `category`와 합쳐서 검색 쿼리 생성 (예: "양주 미용실")
3. `naver_place_crawler.crawl_competitors("양주 미용실", limit=5)` 호출
4. 상위 5개 업체의 기본 데이터 수집: 사진수, 리뷰수, 블로그수, 편의기능 여부
5. 평균값 계산 -> `competitor_data`에 저장

### 크롤링 부하 관리
- 경쟁사 크롤링은 "검색 결과 페이지"에서만 데이터 추출 (상세 페이지 진입 X)
- 기존 `crawl_from_search()` 메서드 재활용
- 경쟁사 5개 = 검색 결과 1페이지에서 한 번에 추출 (추가 페이지 로드 불필요)
- 타겟 업체만 상세 페이지 크롤링, 경쟁사는 요약 데이터만

### 왜 이 방식인가
- 상세 페이지 5개 추가 크롤링하면 시간 5배 증가 + 차단 리스크
- 검색 결과 페이지의 요약 데이터(리뷰수, 사진 유무 등)만으로 비교 충분
- 영업 제안서 목적상 "정확한 숫자"보다 "상대적 격차 시각화"가 중요

---

## xlsx 배치 처리 아키텍처

```
[리안이 xlsx 업로드]
    |
    v
POST /batch/upload
    |
    +-- openpyxl로 파싱
    +-- 업체명 컬럼 자동 감지 (헤더에 "업체명", "상호", "가게명" 등)
    +-- BatchJob 생성 (status: pending, total_count: N)
    +-- 백그라운드 태스크 시작
    |
    v
[BackgroundTasks: batch_processor.process_batch()]
    |
    +-- for each business in list:
    |     +-- 검색 -> 크롤링 -> 점수 산출 -> PPT 생성 -> DB 저장
    |     +-- 영업 우선순위 태깅
    |     +-- completed_count += 1
    |     +-- 업체 간 3초 딜레이 (차단 방지)
    |
    v
[완료: status=done]
    |
    v
GET /batch/results/{batch_id}
    -> 우선순위별 정렬된 결과 반환
    -> 각 업체의 진단 요약 + 1차 메시지 미리보기
```

### 파일 저장 위치
- 업로드된 xlsx: `naver-diagnosis/uploads/` (임시, 24시간 후 자동 삭제)
- PPT 출력: 기존 `ppt_output/` 그대로

### 배치 크기 제한
- 1회 최대 50개 업체 (초과 시 에러 반환)
- 이유: 50개 x 15초(크롤링+분석) = 약 12분. 이 이상은 타임아웃 리스크

---

## 영업 메시지 생성기 설계

별도 서비스(`services/message_generator.py`) + 별도 라우터(`routers/message.py`)로 분리.

### 왜 분리하는가
- 메시지 생성 로직은 진단/크롤링과 독립적
- 진단 완료 후 언제든 재생성 가능해야 함 (진단은 1회, 메시지는 수정/재생성 가능)
- 라우터 확장 없이 `crawl.py`에 넣으면 책임이 과도하게 커짐

### 데이터 흐름
```
DiagnosisHistory (DB)
    + competitor_data (JSON)
    |
    v
SalesMessageGenerator.generate_all()
    |
    +-- 1차 메시지: 자동 버전 선택 (A/B/C)
    +-- 2차 메시지: 진단 카드 텍스트
    +-- 3차 메시지: 패키지 + 손익분기
    +-- 4차 메시지: 보류 대응
    |
    v
JSON 응답 (복붙 가능한 텍스트)
    + DiagnosisHistory.messages 컬럼에 캐싱
```

### 메시지 저장
- 생성된 메시지는 `DiagnosisHistory.messages` JSON 컬럼에 저장
- 재요청 시 캐시 반환 (regenerate=true 파라미터로 강제 재생성 가능)

---

## Engineering Rules (FE/BE 필수 준수)

1. **기존 API 호환성 유지**: 현재 동작하는 `/search`, `/crawl/start`, `/crawl/status`, `/manual`, `/ppt/download` 엔드포인트의 요청/응답 스키마를 변경하지 않는다. 새 필드는 Optional로 추가만 한다.

2. **DB 마이그레이션은 DB_RESET으로**: SQLite + 개발 단계이므로 Alembic 도입하지 않는다. 새 컬럼 추가 시 `DB_RESET=true`로 재생성. 기존 데이터가 중요하지 않은 도구이므로 이 방식이 맞다.

3. **크롤링 딜레이 필수**: 연속 크롤링 시 업체 간 최소 3초 딜레이. 배치 처리에서도 예외 없음. 네이버 차단 방지가 최우선.

4. **에러 시 부분 성공 허용**: 배치 처리에서 개별 업체 크롤링 실패 시 해당 업체만 skip하고 나머지 계속 진행. 전체 실패로 처리하지 않는다.

5. **경쟁사 크롤링은 검색 페이지만**: 상세 페이지 진입 금지. 검색 결과 요약 데이터만 사용. 속도와 안정성 우선.

6. **파일 정리 자동화**: 업로드된 xlsx, 생성된 PPT 모두 24시간 후 자동 삭제. 기존 `_ppt_cleanup_loop` 패턴 재활용.

7. **프론트엔드 최소 변경**: 새 기능(배치, 메시지)은 별도 페이지로 추가. 기존 index.html 건드리지 않는다. `templates/batch.html`, `templates/messages.html` 추가.

8. **업종 판별은 fuzzy 매칭**: category 문자열에 "미용", "헤어", "살롱" 등이 포함되면 "미용실"로 매핑. 정확한 일치가 아니라 부분 문자열 포함으로 판별.

---

## 기술 리스크

| 리스크 | 심각도 | 해결 방법 |
|--------|--------|-----------|
| 네이버 크롤링 차단 (경쟁사 추가 크롤링으로 요청 증가) | 높음 | 경쟁사는 검색 페이지 1회만 조회. 배치 간 3초 딜레이. User-Agent 로테이션 기존 코드 활용 |
| 경쟁사 데이터 정확도 (검색 결과 요약만 사용) | 중간 | 영업 제안서 목적상 "상대 격차"만 보여주면 충분. 정밀 수치 불필요 |
| 배치 처리 시간 (50개 x 15초 = 12분) | 중간 | 프론트에서 진행률 폴링 UI 제공. 중간 결과 실시간 확인 가능하게 |
| SQLite 동시 쓰기 제한 | 낮음 | 1인 사용 도구. 배치도 순차 처리이므로 동시 쓰기 발생 안 함 |
| 새소식/저장수 크롤링 실패 | 낮음 | 크롤링 실패 시 해당 항목 0점 처리. 기존 점수 로직에 영향 없음 |
| DB_RESET으로 기존 데이터 소실 | 낮음 | 영업 도구이므로 과거 데이터 보존 필요 없음. 리안에게 사전 안내 |

---

## CDO에게 요청

1. **배치 결과 목록 UI**: 우선순위별 색상 구분 (1순위=빨강, 2순위=노랑, 패스=회색). 카드 형태로 업체별 요약 표시.
2. **메시지 탭 UI**: 진단 결과 페이지에 "영업 메시지" 탭 추가. 1~4차 메시지를 탭으로 전환. 각 메시지 옆에 "복사" 버튼 (클릭 시 클립보드 복사).
3. **경쟁사 비교 시각화**: 결과 페이지에 내 업체 vs 경쟁사 평균 막대 그래프. PPT와 동일한 구조로.
4. **Jinja2 + Vanilla JS 범위 내에서 디자인**. 프레임워크 도입 불필요. CSS Grid/Flexbox + 간단한 Chart 라이브러리(Chart.js CDN) 정도.
5. **xlsx 업로드 UI**: 드래그앤드롭 영역 + 파일 선택 버튼. 업로드 후 진행률 바 표시.

---

## CPO에게 피드백

1. **영업 우선순위 자동 분류 기준 확인 필요**: 현재 영업_플레이북.md 기준(D등급 + 조건 2개 이상 = 1순위)을 그대로 코드에 넣겠다. 이 기준이 맞는지 CPO가 최종 확인해야 한다.

2. **패키지 금액/내용 하드코딩 이슈**: 패키지 금액(29만/49만/89만)을 코드에 직접 박을 것이다. 금액 변경 시 코드 수정 필요. 자주 바뀌면 config 파일로 빼겠지만, 현재는 하드코딩이 더 단순하다.

3. **1차 메시지 A/B/C 자동 선택 정확도**: 크롤링 데이터가 불완전할 경우(경쟁사 리뷰수 미수집 등) 메시지 버전 선택이 부정확할 수 있다. 이 경우 기본값으로 C(방치형)를 사용하겠다. CPO가 다른 기본값을 원하면 알려달라.

4. **손익분기 계산의 객단가**: 업종별 평균 객단가를 하드코딩한다. 실제 업체의 객단가와 다를 수 있으나, 영업 제안서에서는 "보수적 추정"이라고 표기하면 충분하다.

5. **경쟁사 비교 대상 수**: 상위 5개로 설정. 10개까지 늘리면 크롤링 시간은 동일(검색 결과 1페이지)하지만 평균값이 더 안정적. 다만 5개가 영업 자료로서 더 임팩트 있다 ("상위 5개 대비"가 "상위 10개 대비"보다 위기감 유발).

---

## 구현 우선순위 (Wave 3 작업 순서)

| 순서 | 작업 | 의존성 | 예상 복잡도 |
|------|------|--------|------------|
| 1 | `config/industry_weights.py` 생성 | 없음 | 낮음 |
| 2 | `scorer.py` 업종별 가중치 + 패널티 로직 | 1번 | 중간 |
| 3 | `naver_place_crawler.py` 경쟁사 크롤링 메서드 | 없음 | 중간 |
| 4 | `services/competitor.py` 경쟁사 분석 | 3번 | 낮음 |
| 5 | `models.py` 확장 | 없음 | 낮음 |
| 6 | `routers/crawl.py` 경쟁사 통합 | 2,3,4,5번 | 중간 |
| 7 | `services/message_generator.py` 메시지 생성 | 없음 | 중간 |
| 8 | `routers/message.py` 메시지 API | 7번 | 낮음 |
| 9 | `services/batch_processor.py` 배치 처리 | 6번 | 중간 |
| 10 | `routers/batch.py` 배치 API | 9번 | 낮음 |
| 11 | `ppt_generator.py` 슬라이드 추가 | 4번 | 중간 |
| 12 | 프론트엔드 페이지 추가 | 8,10번 | CDO 영역 |
