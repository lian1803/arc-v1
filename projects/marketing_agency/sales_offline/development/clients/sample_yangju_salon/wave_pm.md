# PM 계획 — 소상공인 네이버 플레이스 영업툴

> 작성일: 2026-04-01
> 작업 폴더: `naver-diagnosis/`

---

## 현재 구현 상태 요약

| 기능 | 상태 |
|------|------|
| Playwright 크롤링 | 구현됨 (메서드명 버그만 수정하면 동작) |
| 영업 메시지 생성 (message_generator.py) | 90% 완료 (CTR 테이블 값만 보정) |
| PPT 영업 제안서 | 90% 완료 (CTR 테이블 보정 필요) |
| 영업 우선순위 분류 | 80% 완료 (프랜차이즈 패스 조건 추가 필요) |
| xlsx 배치 처리 | 80% 완료 (crawl_place → crawl_place_detail 수정 필요) |
| result.html 메시지 탭 | 미확인 (템플릿에 복사 버튼 구현 여부 확인 필요) |
| history.html 우선순위 필터 | 미구현 |
| SQLite WAL 모드 | 미적용 |

---

## 개발 태스크 목록 (우선순위 순)

### P0 CRITICAL — 이게 없으면 아무것도 안 됨

#### BE

| # | 파일 | 수정 내용 | 예상 소요 |
|---|------|---------|---------|
| P0-1 | `routers/batch.py` 또는 `services/batch_processor.py` | `_crawl_callback_factory` 또는 `_do_crawl` 내 `crawler.crawl_place(place_id, business_name)` 호출 → `crawler.crawl_place_detail(place_id)`로 교체. place_id 실패 시 `crawl_from_search(business_name)` 폴백 추가 | 15분 |

---

### P1 — 핵심 기능 (메시지/우선순위/UI)

#### BE

| # | 파일 | 수정 내용 | 예상 소요 |
|---|------|---------|---------|
| P1-1 | `services/message_generator.py` | `_estimate_lost_customers()`의 CTR 테이블을 PRD 기준(1위 35%, 2위 17%, 3위 12%, 4~10위 4~8%, 10위+ 1~2%)으로 수정. `_ctr_for_rank()` 함수 신규 또는 기존 함수 교체 | 20분 |
| P1-2 | `routers/batch.py` (또는 `services/scorer.py`) | `_auto_priority()`에 프랜차이즈 패스 조건 추가: 업체명에 "본점", "직영", "체인", "가맹" 중 하나라도 포함되면 "패스" 반환 | 10분 |

#### FE

| # | 파일 | 수정 내용 | 예상 소요 |
|---|------|---------|---------|
| P1-3 | `templates/result.html` | 메시지 탭 UI 확인 (이미 `_build_template_messages()` 호출 부분 존재). 각 메시지 박스 아래 "복사" 버튼 Vanilla JS 구현: `navigator.clipboard.writeText(text)` + "복사됨!" 1.5초 피드백. 4차 메시지는 4개 탭(보류/무응답/비싸다/직접) 형태로 표시 | 30분 |

---

### P2 — 안정성 및 완성도

#### BE

| # | 파일 | 수정 내용 | 예상 소요 |
|---|------|---------|---------|
| P2-1 | `database.py` | `create_async_engine`에 `connect_args={"check_same_thread": False}` 확인. lifespan 시작 시 `PRAGMA wal_mode=WAL` 실행하는 async 세션 연결 코드 추가 (이미 check_same_thread는 있을 수 있음, wal_mode만 추가) | 15분 |
| P2-2 | `services/naver_place_crawler.py` | `crawl_place_detail()` 및 `crawl_from_search()` 함수의 finally 블록에서 `await context.close()` 호출 확인. page.close() 이후 context.close() 누락 시 추가 | 10분 |

#### FE

| # | 파일 | 수정 내용 | 예상 소요 |
|---|------|---------|---------|
| P2-3 | `templates/history.html` | 우선순위별 필터 드롭다운 (전체/1순위/2순위/패스) + 정렬 기능 (진단일순/우선순위순/업체명순) Vanilla JS 구현. `priority_tag` 필드 활용 | 30분 |

---

## 개발 순서

```
1. [BE] P0-1  batch.py crawl_place_detail 수정        ← 이것만 먼저!
   ↓
2. [BE] P1-1  CTR 테이블 수정
   [BE] P1-2  프랜차이즈 패스 조건
   [FE] P1-3  result.html 메시지 탭 + 복사 버튼
   (세 가지 병렬 가능)
   ↓
3. [BE] P2-1  WAL 모드
   [BE] P2-2  context.close() 확인
   [FE] P2-3  history.html 우선순위 필터
   (세 가지 병렬 가능)
```

---

## 완료 기준

- [ ] P0: xlsx 배치 처리 시 AttributeError不复발 (crawl_place() 호출 → 정상 동작)
- [ ] P1: CTR 테이블 PRD 기준 일치 (1위 35%, 2위 17%, 3위 12%)
- [ ] P1: 1차 메시지 A/B/C 자동 선택 + 복사 버튼 동작 확인
- [ ] P1: 프랜차이즈("본점"/"직영" 포함) 업체 자동 패스 처리
- [ ] P2: history.html에서 1순위/2순위/패스 필터링 동작
- [ ] P2: SQLite WAL 모드 활성화 확인
- [ ] P2: 브라우저 컨텍스트リークなし (context.close() 확인)

---

PM 완료
