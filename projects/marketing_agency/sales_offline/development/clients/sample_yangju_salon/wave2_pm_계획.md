# PM 계획 — 소상공인 영업툴 업그레이드

**작성일**: 2026-03-26
**기반 문서**: wave2_cpo_cto_합의.md, wave2_cto_cdo_합의.md, wave1_cto.md

---

## User Stories (리안 기준)

| ID | As a... | I want to... | So that... | 우선순위 |
|----|---------|-------------|------------|---------|
| US-1 | 영업자 리안 | 업체 진단 시 1~4차 메시지가 자동 생성되어야 한다 | 복붙만으로 영업 가능, 타이핑 시간 제로 | Must |
| US-2 | 영업자 리안 | PPT 표지에 충격 문구가 자동 삽입되어야 한다 | "어?" 유발해서 읽게 만듦 | Must |
| US-3 | 영업자 리안 | 진단 결과 페이지에서 영업 메시지 탭을 보고 버전을 선택하고 복사할 수 있어야 한다 | 상황에 맞는 메시지 즉시 발송 | Must |
| US-4 | 영업자 리안 | 경쟁사 대비 상대 점수가 표시되어야 한다 | "지역 1위는 리뷰 120개인데 당신은 8개"가 설득력 있음 | Must |
| US-5 | 영업자 리안 | PPT에 경쟁사 비교 슬라이드가 추가되어야 한다 | 현실 인식 → 위기감 유발 | Must |
| US-6 | 영업자 리안 | PPT에 손익분기 슬라이드가 추가되어야 한다 | "패키지 비용 / 객단가 = N명만 더 오면 본전" 시각화 | Must |
| US-7 | 영업자 리안 | 업체별 영업 우선순위 태그가 자동 부여되어야 한다 | 진단 목록에서 1순위만 필터링해서 집중 영업 | Must |
| US-8 | 영업자 리안 | xlsx 파일 경로를 지정하면 배치 진단이 자동 실행되어야 한다 | 월요일 루틴: 50건 진단 → 1순위만 골라서 DM | Must |
| US-9 | 영업자 리안 | 배치 진행 상태를 확인할 수 있어야 한다 | N/50 완료, 실패 건수 등 | Must |
| US-10 | 영업자 리안 | 업종에 맞는 가중치가 자동 적용되어야 한다 | 미용실은 사진, 식당은 리뷰에 집중 | Must |
| US-11 | 영업자 리안 | 경쟁사 크롤링 실패 시에도 진단이 완료되어야 한다 | 네이버 차단으로 전체 실패 방지 | Must |
| US-12 | 영업자 리안 | 히스토리 목록에서 우선순위 필터를 클릭하면 해당 업체만 보여야 한다 | 1순위 업체만 보면서 DM 발송 | Should |
| US-13 | 영업자 리안 | 우선순위 태그를 수동으로 변경할 수 있어야 한다 | 이미 연락한 업체는 "패스"로 변경 | Should |

---

## 핵심 플로우 (리안 기준)

```
1. 리안이 업체 검색 or xlsx 경로 입력
    ↓
2. 크롤링 + 진단 (경쟁사 비교 포함)
    ↓
3. 영업 우선순위 자동 분류 (1순위/2순위/패스)
    ↓
4. 진단 결과 페이지 표시
    ├─ 점수 바 차트 (색상 구분)
    ├─ 경쟁사 대비 상대 점수 표시
    └─ 영업 메시지 탭 (1~4차, 버전 선택 가능)
    ↓
5. 리안이 메시지 복사 → 카톡/SMS 발송
    ↓
6. PPT 다운로드 (9슬라이드, 표지 충격 문구 + 경쟁사 비교 + 손익분기)
    ↓
7. 히스토리 목록에서 우선순위 필터 → 1순위만 집중 영업
```

---

## 화면 목록 + 라우트

| 화면 | 라우트 | 설명 |
|------|--------|------|
| 메인 (검색) | `/` | 기존 유지 (단건 검색) |
| 진단 결과 | `/result/{history_id}` | 기존 화면 + 메시지 탭 추가 + 경쟁사 비교 표시 |
| 히스토리 목록 | `/history` | 기존 화면 + 우선순위 필터 추가 + 우선순위 태그 표시 |
| PPT 다운로드 | `/ppt/download/{history_id}` | 기존 유지 (슬라이드 내용만 변경) |
| 로딩 | `/loading` | 기존 유지 |
| 배치 상태 | *없음 (API만)* | UI는 2차 (MVP는 CLI 방식) |

---

## API 엔드포인트

### 기존 유지
| Method | Path | 설명 |
|--------|------|------|
| GET | `/` | 메인 페이지 |
| GET | `/search` | 검색 페이지 |
| POST | `/crawl/start` | 크롤링 시작 |
| GET | `/crawl/status/{job_id}` | 크롤링 상태 |
| POST | `/manual` | 수동 입력 진단 |
| GET | `/ppt/download/{history_id}` | PPT 다운로드 |
| GET | `/history` | 진단 이력 목록 |

### 신규 추가
| Method | Path | 설명 |
|--------|------|------|
| GET | `/message/{history_id}` | 영업 메시지 조회 (캐시 우선, 없으면 생성) |
| POST | `/message/regenerate/{history_id}` | 영업 메시지 강제 재생성 |
| POST | `/batch/start` | 배치 진단 시작 (body: file_path) |
| GET | `/batch/status/{batch_id}` | 배치 진행 상태 조회 |
| PATCH | `/api/businesses/{history_id}/priority` | 우선순위 수동 변경 |

---

## 개발 태스크 (우선순위 순)

### Phase 1: 코어 3개 (절대 빠지면 안 됨)

#### Backend

1. **[BE-1] config/industry_weights.py 생성**
   - 업종별 가중치 딕셔너리 (미용실/네일/식당/카페/학원/피부관리/default)
   - 업종별 평균 객단가 딕셔너리
   - 경쟁사 고정 평균값 딕셔너리 (폴백용)
   - 예상 시간: 15분

2. **[BE-2] models.py 확장**
   - DiagnosisHistory에 컬럼 4개 추가:
     - `sales_priority: str` (1순위/2순위/패스)
     - `competitor_data: JSON` (경쟁사 요약)
     - `relative_score: float` (경쟁사 대비 상대 점수)
     - `messages: JSON` (생성된 메시지 캐시)
   - BatchJob 모델 추가 (id, filename, total_count, completed_count, status, created_at, results)
   - 예상 시간: 20분

3. **[BE-3] services/scorer.py 업종별 가중치 + 우선순위 분류**
   - `get_industry_weights(category)` 함수: fuzzy 매칭으로 업종 판별 → 가중치 반환
   - `calculate_all()` 메서드에 category 파라미터 추가 → 업종별 가중치 적용
   - `calculate_relative_score()` 메서드: 경쟁사 평균 대비 상대 점수
   - `classify_sales_priority()` 메서드: 영업_플레이북.md 기준으로 1순위/2순위/패스 판별
   - 업종 판별 실패 시 default 가중치 사용 (에러 발생 금지)
   - 예상 시간: 45분

4. **[BE-4] services/message_generator.py 메시지 생성**
   - `SalesMessageGenerator` 클래스
   - `generate_all(diagnosis_data, competitor_data)` 메서드:
     - 1차 메시지 A/B/C 자동 선택 로직
       - A (리뷰 격차형): competitor_avg_review >= target_review x 3
       - B (손실 고객형): rank > 10 AND monthly_search >= 500
       - C (방치형): 기타
     - 2차 메시지: 진단 카드 텍스트 (카톡 형식)
     - 3차 메시지: 패키지 추천 + 손익분기 계산 (패키지 금액 / 객단가)
     - 4차 메시지: 보류 대응 (3가지 변형: 보류/비싼 반론/DIY 반론)
   - 경쟁사 데이터 없으면 고정 평균값으로 판별, 판별 불가 시 C
   - 출력 형식:
     ```python
     {
       "first": {
         "auto_version": "A",
         "text_a": "...",
         "text_b": "...",
         "text_c": "..."
       },
       "second": "...",
       "third": "...",
       "fourth": {
         "version_hold": "...",
         "version_expensive": "...",
         "version_diy": "..."
       }
     }
     ```
   - 예상 시간: 60분

5. **[BE-5] routers/message.py 메시지 API**
   - `GET /message/{history_id}`:
     - DiagnosisHistory.messages 컬럼 조회
     - 없으면 `message_generator.generate_all()` 호출 → DB 저장 → 반환
     - regenerate=true 파라미터 시 강제 재생성
   - 예상 시간: 20분

6. **[BE-6] services/ppt_generator.py 슬라이드 추가**
   - 기존 7슬라이드 유지
   - 표지 (슬라이드 1): "매달 N명의 고객이 경쟁사로 가고 있어요" 문구 자동 생성
     - N = (경쟁사 평균 리뷰수 - 내 리뷰수) / 6 (월 1회 리뷰 가정)
   - 슬라이드 2 뒤: 경쟁사 비교 슬라이드 삽입
     - 제목: "이 동네 상위 5개 업체와 비교하면..."
     - 막대 그래프: 리뷰수, 블로그수, 노출 순위 3개 항목
     - 실제 데이터면 "지역 상위 5개 기준", 폴백이면 "업종 평균 기준" 표기
   - 슬라이드 4 뒤: 손익분기 슬라이드 삽입
     - 제목: "패키지 선택 시 손익분기는?"
     - 테이블: 패키지명 / 월 비용 / 필요 신규 고객 수 / 일 평균
     - 계산식: 패키지 금액 / 업종별 객단가
   - 최종 PPT: 9슬라이드
   - 예상 시간: 50분

7. **[BE-7] routers/crawl.py 메시지 생성 통합**
   - `run_crawl_job()` 크롤링 완료 시:
     - `message_generator.generate_all()` 호출
     - DiagnosisHistory.messages 컬럼에 저장
   - result.html 렌더링 시 messages 딕셔너리 포함 (Jinja2 컨텍스트)
   - 예상 시간: 15분

#### Frontend

8. **[FE-1] Tailwind CDN 추가 (Preflight 비활성화)**
   - 모든 HTML 파일 `<head>`에 추가:
     ```html
     <script src="https://cdn.tailwindcss.com"></script>
     <script>
       tailwind.config = {
         corePlugins: { preflight: false },
         theme: {
           extend: {
             colors: {
               'naver-green': '#03C75A',
               'kakao-yellow': '#FEE500',
               'priority-red': '#FF4757',
               'priority-orange': '#FFA502',
               'priority-gray': '#A4A4A4',
             }
           }
         }
       }
     </script>
     ```
   - 예상 시간: 10분

9. **[FE-2] result.html 메시지 탭 추가**
   - 기존 진단 상세 아코디언 아래에 "영업 메시지" 탭 섹션 추가
   - 탭 4개: 1차 / 2차 / 3차 / 4차
   - 1차 메시지는 A/B/C 버전 토글 버튼 (선택된 버전만 표시)
   - 4차 메시지는 보류/비싼 반론/DIY 반론 토글 버튼
   - 각 메시지 옆에 "복사" 버튼 (클릭 시 클립보드 복사 + 1.5초간 "복사됨 ✓" 표시)
   - Jinja2로 서버사이드 렌더링: `{{ messages.first.text_a }}` 방식
   - 탭 전환은 Vanilla JS로 `display:none/block` 토글 (서버 요청 없음)
   - 예상 시간: 40분

10. **[FE-3] result.html 점수 바 차트 Pure CSS**
    - `<details>` 아코디언 안에 7개 항목 점수 막대 차트
    - Jinja2 for 루프:
      ```html
      {% for item in score_items %}
      <div class="score-row">
        <span>{{ item.name }}</span>
        <div class="score-bar-bg">
          <div class="score-bar {{ 'bar-danger' if item.score < 40 else 'bar-warning' if item.score < 60 else 'bar-good' }}"
               style="--target-width: {{ item.score }}%">
          </div>
        </div>
        <span>{{ item.score }}/100</span>
      </div>
      {% endfor %}
      ```
    - CSS transition 애니메이션: `window.load` 이벤트에서 width 적용
    - 예상 시간: 30분

11. **[FE-4] result.html 경쟁사 비교 표시**
    - 점수 섹션 아래 "경쟁사 비교" 영역 추가
    - 리뷰수, 블로그수, 노출 순위 3개 항목만 표시
    - 막대 그래프: 내 업체 vs 지역 상위 평균
    - Jinja2: `{{ competitor.avg_review }}`, `{{ diagnosis.review_count }}`
    - 경쟁사 데이터 없으면 "(업종 평균 기준)" 표기
    - 예상 시간: 25분

12. **[FE-5] history.html 우선순위 필터 + 태그 표시**
    - 히스토리 목록 상단에 필터 버튼 3개: 전체 / 1순위 / 2순위 / 패스
    - 클릭 시 JS로 `data-priority` 속성 기반 DOM 숨기기/보이기
    - 각 업체 카드에 우선순위 배지 표시 (색상: 1순위 빨강, 2순위 주황, 패스 회색)
    - 배지 클릭 → 드롭다운 선택 → `PATCH /api/businesses/{id}/priority` 호출 → 태그 색상 즉시 변경
    - 예상 시간: 35분

13. **[FE-6] 클립보드 복사 함수 + 폴백**
    - `static/js/result.js` (또는 result.html 인라인 `<script>`) 에 함수 추가:
      ```javascript
      async function copyToClipboard(text) {
        try {
          await navigator.clipboard.writeText(text);
          return true;
        } catch (err) {
          // 폴백: execCommand
          const textarea = document.createElement('textarea');
          textarea.value = text;
          textarea.style.position = 'fixed';
          textarea.style.opacity = '0';
          document.body.appendChild(textarea);
          textarea.select();
          const success = document.execCommand('copy');
          document.body.removeChild(textarea);
          return success;
        }
      }

      async function handleCopyBtn(btn, text) {
        const success = await copyToClipboard(text);
        if (success) {
          const original = btn.textContent;
          btn.textContent = '복사됨 ✓';
          btn.disabled = true;
          setTimeout(() => {
            btn.textContent = original;
            btn.disabled = false;
          }, 1500);
        }
      }
      ```
    - 예상 시간: 15분

14. **[BE-8] routers/history.py 우선순위 PATCH 엔드포인트**
    - `PATCH /api/businesses/{history_id}/priority`
    - body: `{"priority": "1순위"}`
    - 유효값 검증: "1순위", "2순위", "패스" 중 하나
    - DiagnosisHistory.sales_priority 컬럼 업데이트
    - 응답: `{"success": true, "priority": "1순위"}`
    - 예상 시간: 15분

---

### Phase 2: 경쟁사 + 배치 (경량 버전, 일정 밀리면 드랍 가능)

#### Backend

15. **[BE-9] services/naver_place_crawler.py 경쟁사 크롤링 메서드**
    - `crawl_competitors(query, limit=5)` 메서드 추가
    - 검색 결과 페이지 1회만 조회 (상세 페이지 진입 절대 금지)
    - 상위 5개 업체의 리뷰수, 블로그수, 노출 순위만 추출
    - 반환: `[{"name": "...", "review_count": N, "blog_count": M, "rank": 1}, ...]`
    - 실패 시 빈 리스트 반환 (에러 발생 금지)
    - 예상 시간: 40분

16. **[BE-10] services/competitor.py 경쟁사 분석**
    - `CompetitorAnalyzer` 클래스
    - `analyze(target_data, competitor_list)` 메서드:
      - 경쟁사 평균 계산 (리뷰수, 블로그수)
      - 상대 점수 계산 (내 점수 / 경쟁사 평균 점수 x 100)
      - 순위 계산 (타겟이 경쟁사 5개 중 몇 위인지)
    - 반환: `{"avg_review": N, "avg_blog": M, "relative_score": X, "rank": Y}`
    - 예상 시간: 20분

17. **[BE-11] routers/crawl.py 경쟁사 크롤링 통합 (Optional 단계)**
    - `run_crawl_job()` 에 경쟁사 크롤링 단계 추가 (crawling과 analyzing 사이)
    - `address + category`로 검색 쿼리 생성 (예: "양주 미용실")
    - `naver_place_crawler.crawl_competitors(query)` 호출
    - 실패 시 `industry_weights.py`의 고정 평균값으로 폴백 (조용히)
    - `competitor.analyze()` 호출 → DiagnosisHistory.competitor_data 컬럼 저장
    - 예상 시간: 30분

18. **[BE-12] services/batch_processor.py 배치 처리**
    - `BatchProcessor` 클래스
    - `parse_xlsx(file_path)` 메서드:
      - openpyxl로 파싱
      - 헤더에서 업체명 컬럼 자동 감지 ("업체명", "상호", "가게명", "업체" 등)
      - 업체명 리스트 반환
    - `process_batch(batch_job_id, business_list, browser)` 메서드:
      - 순차 크롤링 + 진단 (업체 간 3초 딜레이)
      - 1회 최대 50건 제한
      - 개별 실패 시 skip, 나머지 계속
      - 완료 시 BatchJob.completed_count 업데이트
      - 완료 후 영업 우선순위 태그 자동 부여
    - 예상 시간: 40분

19. **[BE-13] routers/batch.py 배치 API**
    - `POST /batch/start`:
      - body: `{"file_path": "C:/path/to/file.xlsx"}`
      - BatchJob 생성 (status: pending)
      - BackgroundTasks로 `batch_processor.process_batch()` 호출
      - 응답: `{"batch_id": N, "status": "pending", "total_count": M}`
    - `GET /batch/status/{batch_id}`:
      - BatchJob 조회
      - 응답: `{"batch_id": N, "status": "...", "completed_count": X, "total_count": Y}`
    - 예상 시간: 15분

---

## FE/BE 인터페이스 정의

### 진단 결과 페이지 (result.html)

**BE → FE 데이터 전달 (Jinja2 컨텍스트)**
```python
{
  "request": request,
  "diagnosis": {
    "business_name": "...",
    "total_score": 45.2,
    "grade": "C",
    "review_count": 8,
    "blog_count": 3,
    # ... 기존 필드들
    "sales_priority": "1순위",
    "relative_score": 38.5
  },
  "score_items": [
    {"name": "사진", "score": 45},
    {"name": "리뷰", "score": 30},
    # ... 7개 항목
  ],
  "competitor": {
    "avg_review": 120,
    "avg_blog": 45,
    "rank": 5,
    "is_fallback": false  # 고정 평균값 폴백 여부
  },
  "messages": {
    "first": {
      "auto_version": "A",
      "text_a": "사장님, 이 동네 1위 업체는 리뷰 120개인데 사장님은 8개예요.\n진단 결과 보내드려도 될까요?",
      "text_b": "...",
      "text_c": "..."
    },
    "second": "...",
    "third": "...",
    "fourth": {
      "version_hold": "...",
      "version_expensive": "...",
      "version_diy": "..."
    }
  }
}
```

**FE → BE API 호출**
- 복사 버튼: 클립보드만 사용, API 호출 없음
- 메시지 재생성: `POST /message/regenerate/{history_id}` (regenerate=true)

### 히스토리 목록 (history.html)

**BE → FE 데이터 전달**
```python
{
  "request": request,
  "history_list": [
    {
      "id": 1,
      "business_name": "...",
      "total_score": 45.2,
      "grade": "C",
      "sales_priority": "1순위",
      "category": "미용실",
      "created_at": "2026-03-26 14:30"
    },
    # ...
  ]
}
```

**FE → BE API 호출**
- 우선순위 변경: `PATCH /api/businesses/{history_id}/priority` (body: `{"priority": "1순위"}`)

### 배치 상태 조회 (API 전용, UI 없음)

**BE → FE 응답**
```json
{
  "batch_id": 123,
  "status": "processing",
  "total_count": 50,
  "completed_count": 23,
  "failed_count": 2,
  "results": [1, 2, 3, ...]  # DiagnosisHistory ID 목록
}
```

---

## 파일별 추가/수정 목록

### 신규 생성
- `config/industry_weights.py`
- `services/message_generator.py`
- `services/competitor.py`
- `services/batch_processor.py`
- `routers/message.py`
- `routers/batch.py`
- `static/js/result.js` (또는 result.html 인라인)

### 수정
- `models.py` — DiagnosisHistory 컬럼 4개 추가, BatchJob 모델 추가
- `services/scorer.py` — 업종별 가중치 + 우선순위 분류 + 상대 점수
- `services/naver_place_crawler.py` — `crawl_competitors()` 메서드 추가
- `services/ppt_generator.py` — 슬라이드 3개 추가/수정 (표지/경쟁사/손익분기)
- `routers/crawl.py` — 경쟁사 크롤링 통합 + 메시지 생성 통합 + result.html 컨텍스트 확장
- `routers/history.py` — PATCH 엔드포인트 추가
- `templates/result.html` — 메시지 탭 + 점수 바 차트 + 경쟁사 비교 영역 추가
- `templates/history.html` — 우선순위 필터 + 태그 표시 + 태그 변경 드롭다운

### 건드리지 않음
- `services/naver_search_ad.py` — 변경 없음
- `routers/search.py` — 변경 없음
- `routers/manual.py` — 변경 없음
- `routers/ppt.py` — 변경 없음
- `database.py` — 변경 없음
- `browser_manager.py` — 변경 없음
- `templates/index.html` — 변경 없음
- `templates/loading.html` — 변경 없음

---

## 개발 순서 (의존성 기준)

### 순서 1: 기반 작업 (병렬 가능)
- [BE-1] industry_weights.py 생성
- [BE-2] models.py 확장
- [FE-1] Tailwind CDN 추가

### 순서 2: 점수 + 메시지 (순차)
- [BE-3] scorer.py 업종별 가중치 + 우선순위 분류 (의존: BE-1, BE-2)
- [BE-4] message_generator.py 메시지 생성 (의존: BE-1)
- [BE-5] message.py API (의존: BE-4)

### 순서 3: PPT + 크롤링 통합 (순차)
- [BE-6] ppt_generator.py 슬라이드 추가 (의존: BE-1)
- [BE-7] crawl.py 메시지 생성 통합 (의존: BE-3, BE-5)

### 순서 4: 프론트엔드 (병렬 가능)
- [FE-2] result.html 메시지 탭 (의존: BE-7)
- [FE-3] result.html 점수 바 차트 (의존: BE-7)
- [FE-4] result.html 경쟁사 비교 (의존: BE-7)
- [FE-6] 클립보드 복사 함수 (의존: FE-2)

### 순서 5: 히스토리 (병렬 가능)
- [BE-8] history.py PATCH 엔드포인트 (의존: BE-2)
- [FE-5] history.html 우선순위 필터 + 태그 (의존: BE-3, BE-8)

### 순서 6: 경쟁사 (일정 밀리면 드랍)
- [BE-9] crawler 경쟁사 메서드 (의존: 없음)
- [BE-10] competitor.py 분석 (의존: BE-9)
- [BE-11] crawl.py 경쟁사 통합 (의존: BE-3, BE-10)

### 순서 7: 배치 (일정 밀리면 드랍)
- [BE-12] batch_processor.py (의존: BE-11)
- [BE-13] batch.py API (의존: BE-12)

---

## 완료 기준

### Phase 1 (코어 3개) 완료 기준
- [ ] 단건 진단 시 1~4차 메시지 자동 생성되어 result.html에 표시됨
- [ ] 메시지 탭 전환 + 버전 토글 + 복사 버튼 정상 동작
- [ ] PPT 표지에 "매달 N명이 경쟁사로" 문구 자동 삽입됨
- [ ] PPT에 경쟁사 비교 슬라이드 추가됨 (실제 데이터 없으면 고정 평균값 폴백)
- [ ] PPT에 손익분기 슬라이드 추가됨 (패키지 3개별 계산)
- [ ] 진단 완료 시 영업 우선순위 태그 자동 부여됨 (1순위/2순위/패스)
- [ ] 히스토리 목록에서 우선순위 필터 동작 (JS DOM 숨기기/보이기)
- [ ] 우선순위 태그 수동 변경 가능 (드롭다운 선택 → PATCH API → 태그 색상 변경)
- [ ] 점수 바 차트 Pure CSS 애니메이션 정상 동작
- [ ] 업종별 가중치 자동 적용됨 (미용실/식당 등 차등)
- [ ] 업종 판별 실패 시 default 가중치 사용 (에러 없음)

### Phase 2 (경쟁사 + 배치) 완료 기준
- [ ] 경쟁사 크롤링 정상 동작 (검색 페이지 1회만, 상세 페이지 진입 안 함)
- [ ] 경쟁사 크롤링 실패 시 고정 평균값 폴백 (진단 플로우 끊기지 않음)
- [ ] result.html에 경쟁사 비교 영역 표시됨 (리뷰수/블로그수/순위)
- [ ] xlsx 파일 경로 지정 → 배치 진단 시작 → 완료 (API 전용)
- [ ] 배치 진행 상태 조회 API 정상 동작 (N/50 완료, 실패 건수)
- [ ] 배치 완료 후 각 업체에 우선순위 태그 자동 부여됨
- [ ] 배치 처리 시 업체 간 3초 딜레이 유지 (차단 방지)
- [ ] 배치 개별 실패 시 skip, 나머지 계속 진행 (전체 실패 아님)

---

## 리스크 + 완화 방안

| 리스크 | 심각도 | 완화 방안 |
|--------|--------|-----------|
| 메시지 자동 버전 선택 정확도 낮음 | 중간 | 기본값 C(방치형) 사용. 리안이 수동 선택 가능하게 버전 토글 제공 |
| 경쟁사 크롤링 실패 시 진단 중단 | 높음 | Optional 단계로 구현, 실패 시 고정 평균값 폴백 |
| 배치 처리 시간 초과 (50건 = 12분) | 중간 | 1회 최대 50건 제한, 프론트 진행률 폴링 UI (2차 예정) |
| 업종 판별 실패로 잘못된 가중치 적용 | 중간 | fuzzy 매칭 + default 폴백, 리안 피드백으로 1개월 후 튜닝 |
| DB_RESET으로 기존 데이터 소실 | 낮음 | 리안에게 사전 안내, 영업 도구라 과거 데이터 보존 불필요 |
| 네이버 크롤링 차단 (경쟁사 추가로 요청 증가) | 높음 | 검색 페이지 1회만 조회, 배치 간 3초 딜레이 유지, User-Agent 로테이션 기존 활용 |

---

## 드랍 우선순위 (CPO/CTO 합의 기준)

일정 밀릴 때 아래 순서로 드랍:

1. **절대 빠지면 안 됨**: 영업 메시지 자동 생성 (US-1, US-2, US-3)
2. **절대 빠지면 안 됨**: PPT 영업 제안서 강화 (US-5, US-6)
3. **절대 빠지면 안 됨**: 영업 우선순위 자동 분류 (US-7)
4. **일정 밀리면 첫 번째로 드랍**: 경쟁사 비교 (BE-9, BE-10, BE-11, FE-4)
   - 고정 평균값 폴백으로 대체
5. **일정 밀리면 두 번째로 드랍**: xlsx 배치 (BE-12, BE-13)
   - 단건으로 우선 운영
6. **업종별 가중치 차등**: 구현 비용 15분이라 드랍 대상 아님

---

## PM 서명

리안이 진단 → 메시지 복사 → DM 발송 → PPT 다운로드까지 한 흐름으로 완성됨.
핵심은 "메시지 자동 생성". 이것만 제대로 되면 리안의 타이핑 시간이 0이 됨.
경쟁사/배치는 부착형 모듈이라 일정 밀리면 드랍 가능.
FE/BE 작업자는 이 문서 기반으로 태스크 시작.
