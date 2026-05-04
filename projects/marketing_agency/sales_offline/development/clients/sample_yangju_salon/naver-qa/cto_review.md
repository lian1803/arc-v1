# CTO 코드 리뷰 결과

## 프로젝트
네이버 플레이스 자동 진단 + PPT 제안서 생성 툴

## 리뷰 일시
2026-03-19

## 리뷰 대상 파일
- `src/main.py`
- `src/routers/crawl.py`
- `src/database.py`
- `src/models.py`
- `src/requirements.txt`
- `src/services/naver_place_crawler.py`
- `src/services/ppt_generator.py`
- `src/services/scorer.py`
- `src/static/js/progress.js`
- `src/templates/loading.html`

---

## Engineering Rules 준수 여부

| Rule | 설명 | 준수 | 비고 |
|------|------|------|------|
| 1 | Playwright 브라우저 앱 시작 시 1번 생성, app.state 저장 | O | main.py lifespan에서 정상 구현 |
| 2 | 크롤링 타임아웃 30000ms | O | naver_place_crawler.py L138-139 |
| 3 | 에러 핸들링: CrawlJob.status='failed', error_message 기록 | O | crawl.py L164-170 |
| 4 | SQLAlchemy 세션 FastAPI Depends 주입 | O | crawl.py에서 Depends(get_db) 사용 |
| 5 | PPT 파일 ppt_output/ 폴더 저장 | O | ppt_generator.py output_dir 기본값 |
| 6 | User-Agent 랜덤화 3-5개 로테이션 | O | naver_place_crawler.py 5개 정의 |

**결과: 6/6 준수**

---

## 핵심 검증 항목

### 1. main.py -> crawl.py 브라우저 접근
```python
# main.py (L56-58)
app.state.playwright = playwright
app.state.browser = browser

# crawl.py (L188)
browser = request.app.state.browser
```
**결과: 정상**

### 2. SQLAlchemy 2.0 Mapped 스타일 일관성
- `database.py`: DeclarativeBase 사용
- `models.py`: Mapped, mapped_column 사용
- 두 파일 간 Base import 연결 정상

**결과: 정상**

### 3. requirements.txt 패키지 완성도
| 패키지 | 버전 | 용도 | 존재 |
|--------|------|------|------|
| fastapi | 0.111.0 | 웹 프레임워크 | O |
| uvicorn | 0.30.1 | ASGI 서버 | O |
| sqlalchemy | 2.0.30 | ORM | O |
| aiosqlite | 0.20.0 | 비동기 SQLite | O |
| playwright | 1.44.0 | 브라우저 크롤링 | O |
| python-pptx | 0.6.23 | PPT 생성 | O |
| httpx | 0.27.0 | HTTP 클라이언트 | O |
| jinja2 | 3.1.4 | 템플릿 엔진 | O |
| python-dotenv | 1.0.1 | 환경변수 | O |
| python-multipart | 0.0.9 | 폼 데이터 | O |

**결과: 모든 필수 패키지 존재**

### 4. FE/BE 연결 포인트 (폴링 URL 일치)
- `progress.js` L54: `fetch('/crawl/status/${jobId}')`
- `crawl.py` L226: `@router.get("/status/{job_id}")`
- Router prefix: `/crawl`

**결과: 정상 (URL 일치: /crawl/status/{job_id})**

---

## 흐름 완결성 검증

### 메인 흐름: 업체명 입력 -> PPT 다운로드

1. **검색** (POST /search)
   - `services/naver_place_crawler.py` search_business()
   - 네이버 지역 검색 API 호출 -> place_id 반환

2. **크롤링 시작** (POST /crawl/start)
   - `routers/crawl.py` start_crawl()
   - CrawlJob 생성 -> BackgroundTasks 등록

3. **백그라운드 크롤링** (run_crawl_job)
   - status: pending -> searching -> crawling -> analyzing -> generating -> done
   - NaverPlaceCrawler.crawl_place_detail() 실행
   - DiagnosisScorer.calculate_all() 점수 산출
   - PPTGenerator.generate() PPT 생성
   - DiagnosisHistory 저장

4. **상태 폴링** (GET /crawl/status/{job_id})
   - progress.js에서 1초 간격 폴링
   - done 상태 시 /result/{history_id}로 리다이렉트

5. **PPT 다운로드** (GET /ppt/download/{history_id})
   - ppt_output/ 폴더의 pptx 파일 스트리밍

**결과: 흐름 완결**

---

## 발견 사항 (비차단)

### 1. 테이블명 불일치 (미미)
- `models.py`: `__tablename__ = "crawl_job"` (단수)
- `CLAUDE.md` 설계서: `crawl_jobs` (복수)
- 영향: 없음 (코드 내부 일관성 있음)

### 2. BeautifulSoup4 미사용
- 설계서에서 명시했으나 실제 코드는 정규식 파싱 사용
- 영향: 없음 (더 가벼운 구현)

---

## 판정

### 통과

**근거:**
1. Engineering Rules 6/6 모두 준수
2. 서버 정상 시작 조건 충족 (main.py 구조 정상)
3. 업체명 입력 -> PPT 다운로드 흐름이 코드상 완결
4. FE/BE 연결 포인트 정상
5. 필수 패키지 모두 존재

### "동작하면 통과" 원칙 적용
- 코드상 치명적 오류 없음
- 실행 시 정상 동작 예상

---

## 배포 전 확인 사항 (권장)

1. `playwright install chromium` 실행 필요
2. `.env` 파일에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 설정 필요
3. ppt_output/ 폴더 쓰기 권한 확인

---

**CTO 서명:** Wave 4 코드 리뷰 완료, 배포 승인
