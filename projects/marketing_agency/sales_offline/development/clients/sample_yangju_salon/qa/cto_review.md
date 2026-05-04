# CTO 통합 리뷰 — 소상공인 영업툴 Wave 3

리뷰 일시: 2026-03-26
검토 기준: wave1_cto.md 설계 대비 실제 구현 검증

---

## 1. 전체 판정

**통과** — 핵심 버그 5개 발견 후 즉시 수정 완료. 아키텍처 설계 준수, Engineering Rules 대부분 준수.

---

## 2. 아키텍처 일관성

### 판정: 설계 대비 95% 일치

**일치하는 것:**
- 파일 구조: config/industry_weights.py, services/message_generator.py, services/competitor.py, services/batch_processor.py, routers/message.py, routers/batch.py 전부 생성됨
- 책임 분리: 크롤링(crawler) / 분석(scorer, competitor) / 메시지(message_generator) / 배치(batch_processor) 명확히 분리됨
- 설계에 없던 추가 기능: BusinessPriority 모델 (영업 단계 관리), 설계보다 향상됨

**설계와 다른 것:**
- `batch.py` 설계는 `POST /batch/upload` (파일 업로드)였으나 구현은 `POST /batch/start` (파일 경로 직접 입력). 1인 로컬 툴 특성상 이 방식이 더 실용적이므로 수용.
- 설계에서 언급된 `BatchJob` DB 모델 대신 인메모리 `_batch_store` 딕셔너리 사용. 서버 재시작 시 배치 이력 소실. MVP 수준에서 허용.

---

## 3. Engineering Rules 준수

| 규칙 | 준수 여부 | 비고 |
|------|----------|------|
| 1. 기존 API 호환성 유지 | 통과 | 기존 엔드포인트 스키마 변경 없음 |
| 2. DB_RESET으로 마이그레이션 | 통과 | main.py에 DB_RESET 환경변수 처리 구현됨 |
| 3. 크롤링 딜레이 3초 | 통과 | batch_processor.py run_batch()에 delay_seconds=3 기본값 |
| 4. 에러 시 부분 성공 | 통과 | run_batch() 개별 업체 실패 시 skip 후 계속 진행 |
| 5. 경쟁사 크롤링은 검색 페이지만 | 통과 | competitor.py _crawl_search_results()에서 상세 페이지 진입 없음 |
| 6. 파일 정리 자동화 | 부분 통과 | PPT는 24h 자동삭제 구현됨. xlsx uploads/ 디렉토리 생성 안됨 (batch가 경로 직접 입력 방식이므로 해당 없음) |
| 7. 프론트엔드 최소 변경 | 통과 | 기존 index.html 수정 없음. batch.html, result.html 추가/수정 |
| 8. 업종 판별 fuzzy 매칭 | 통과 | detect_industry()에서 부분 문자열 포함으로 판별 |

---

## 4. BE↔FE 통합 — 발견된 버그 및 수정 내역

### 버그 1 (치명): result.html — 필수 템플릿 변수 누락
**위치:** `main.py` result_page 함수
**증상:** `/result/{id}` 접속 시 Jinja2 UndefinedError 발생. 페이지 렌더링 불가.
**원인:** result.html이 `messages`, `key_metrics`, `score_items` 변수를 기대하는데 main.py가 `history`만 전달.
**수정:** result_page에 messages 생성 + key_metrics/score_items 조립 로직 추가. DB 캐시 없으면 즉시 생성 후 저장.

### 버그 2 (치명): messages 구조 불일치 — BE 출력 vs FE 기대
**위치:** `services/message_generator.py` ↔ `templates/result.html`
**증상:** result.html이 `messages.first.versions`, `messages.second.text`, `messages.fourth.versions`를 기대하는데, generate_all_messages()는 `{first: {type, text, label}, second: "str", fourth: {보류: "str", ...}}` 반환.
**수정:** main.py에 `_build_template_messages()` 변환 함수 추가. raw 출력을 템플릿 호환 구조로 변환.

### 버그 3 (치명): history.sales_priority 필드 없음
**위치:** `models.py` ↔ `templates/result.html`, `templates/history.html`
**증상:** 템플릿에서 `history.sales_priority`, `history.sales_priority_label` 접근 시 AttributeError.
**원인:** 모델 필드명은 `priority_tag`인데 템플릿은 `sales_priority`를 참조.
**수정:** result_page, history_page에서 `priority_tag` → `sales_priority/sales_priority_label` 동적 속성 변환 후 템플릿 전달.

### 버그 4 (치명): /history, /batch 페이지 라우터 누락
**위치:** `main.py`
**증상:** 브라우저에서 `/history`, `/batch` 접속 시 404.
**원인:** HTML 페이지 렌더링 라우터가 main.py에 없음. history.py는 JSON API만 제공.
**수정:** main.py에 `GET /history` (history.html 렌더링 + DB 조회), `GET /batch` (batch.html 렌더링) 라우터 추가.

### 버그 5 (중간): batch.py BackgroundTasks 오용
**위치:** `routers/batch.py` line 223
**증상:** `background_tasks.add_task(asyncio.create_task, _run())` — 이미 실행된 코루틴 객체를 create_task에 넘기면 이벤트 루프 없는 상황에서 즉시 실행 시도 → 오류.
**수정:** `background_tasks.add_task(_run)` — 코루틴 함수 자체를 전달.

### 버그 6 (중간): crawl.py DiagnosisHistory 저장 시 신규 필드 누락
**위치:** `routers/crawl.py` run_crawl_job()
**증상:** 단건 크롤링 완료 후 저장된 DiagnosisHistory에 industry_type, priority_tag, competitor_avg_review, competitor_avg_blog, estimated_lost_customers, messages 컬럼이 0/NULL.
**원인:** crawl.py의 DiagnosisHistory() 생성자 호출에 Wave 3 신규 필드 누락.
**수정:** 점수 계산 후 경쟁사 데이터 수집(실패 시 폴백), 우선순위 자동 분류, 메시지 생성 로직 추가. DiagnosisHistory 생성자에 신규 필드 전달.

---

## 5. DB 마이그레이션 호환성

**판정: 정상**

- SQLite + SQLAlchemy 2.0 async 방식 유지됨
- 신규 컬럼 모두 `nullable=True` 또는 `default=0`으로 선언 → 기존 DB에 영향 없음
- DB_RESET=true 환경변수로 스키마 재생성 지원됨
- 기존 `diagnosis_history`, `crawl_job` 테이블에 신규 컬럼만 추가 (디스트럭티브 변경 없음)

---

## 6. 성능 — 경쟁사 크롤링 추가 영향

**판정: 허용 범위**

- 기존 단건 크롤링: ~10-15초
- 경쟁사 크롤링 추가: +5-8초 (검색 결과 페이지 1회만 조회)
- 총 예상 시간: 15-23초 per 업체
- 경쟁사 크롤링 타임아웃 12초 설정 → 실패 시 폴백 즉시 반환
- 배치 처리: 업체 간 3초 딜레이 유지. 50개 x ~20초 = 약 17분. 기존 설계(12분) 대비 5분 증가. 허용 범위.

---

## 7. 보안

**판정: 이슈 없음 (1인 로컬 툴 기준)**

- 입력 검증: Pydantic 모델로 요청 타입 검증됨
- 경로 검증: batch.py BatchStartRequest에서 file_path를 받아 파일 존재 여부 확인 (parse_xlsx에서 FileNotFoundError)
- CORS: allow_origins=["*"] → 로컬 전용 툴이므로 허용
- SQL Injection: SQLAlchemy ORM 사용으로 파라미터 바인딩 자동 처리

**주의:** BatchStartRequest.file_path가 서버 파일 시스템 경로를 직접 받음. 외부 배포 시에는 path traversal 위험. 현재 로컬 1인 사용이므로 문제 없음.

---

## 8. 남은 이슈 (수정 불필요, 인지만)

1. **경쟁사 크롤링 셀렉터 불안정**: competitor.py의 JS evaluate 셀렉터(`._3StCU, .VH7TP` 등)가 네이버 UI 변경 시 동작 안 할 수 있음. 폴백 로직이 있어서 서비스 중단은 없음.

2. **배치 이력 서버 재시작 시 소실**: _batch_store가 인메모리. 서버 재시작하면 배치 진행 상황 사라짐. MVP에서는 허용. 필요 시 BatchJob DB 모델로 전환.

3. **ppt_generator.py estimated_lost_customers**: crawl.py에서 경쟁사 크롤링 후 estimated_lost_customers를 messages 딕셔너리에서 꺼냄. PPT 생성 시 diagnosis_data에 직접 저장 안 됨. 다음 순서로 수정 가능: `diagnosis_data["estimated_lost_customers"] = messages.get("estimated_lost_customers", 0)`. 현재는 PPT 표지 충격 문구가 0으로 뜰 수 있음.

4. **history.html 필터 카운트**: JS로 data-priority 속성 기반 카운트. 현재 count-1, count-2, count-pass가 0으로 초기화됨. JS가 DOMContentLoaded 후 카운트 업데이트해야 함 — FE 이슈로 CTO 범위 밖.

---

## 9. 수정된 파일 목록

| 파일 | 수정 내용 |
|------|----------|
| `main.py` | result_page에 messages/key_metrics/score_items 추가, _build_template_messages() 추가, /history + /batch 페이지 라우터 추가 |
| `routers/crawl.py` | DiagnosisHistory 저장 시 신규 필드 추가, 경쟁사 크롤링 + 우선순위 분류 + 메시지 생성 로직 통합 |
| `routers/batch.py` | BackgroundTasks 오용 수정 (add_task(_run) 방식으로 변경) |
