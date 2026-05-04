# 네이버 플레이스 자동 진단 + PPT 제안서 생성 툴 — 구현 지시서

## 기술 스택

| 항목 | 선택 | 버전 |
|------|------|------|
| Backend Framework | FastAPI | 0.111.0 |
| Python | Python | 3.11 |
| 크롤링 | Playwright (async) | 1.44.0 |
| HTML 파싱 | BeautifulSoup4 | 4.12.3 |
| PPT 생성 | python-pptx | 0.6.23 |
| DB | SQLite + SQLAlchemy | SQLAlchemy 2.0.30 |
| Frontend | Jinja2 템플릿 + Vanilla JS | Jinja2 3.1.4 |
| HTTP Client | httpx | 0.27.0 |
| 작업 큐 | FastAPI BackgroundTasks | (내장) |
| 환경변수 | python-dotenv | 1.0.1 |

---

## 폴더 구조

```
naver-place-tool/
├── main.py                        # FastAPI 앱 진입점
├── .env                           # 환경변수
├── requirements.txt
├── database.py                    # SQLAlchemy 엔진 + 세션
├── models.py                      # DB 테이블 정의
│
├── routers/
│   ├── search.py                  # 업체 검색 API
│   ├── crawl.py                   # 데이터 수집 API
│   ├── diagnosis.py               # 진단 점수 산출 API
│   ├── ppt.py                     # PPT 생성 + 다운로드 API
│   └── history.py                 # 이력 조회/삭제 API
│
├── services/
│   ├── naver_place_crawler.py     # 플레이스 크롤링 핵심 로직
│   ├── naver_search_ad.py         # 네이버 검색광고 API 키워드 검색량 조회
│   ├── scorer.py                  # 항목별 점수 + 등급 산출
│   └── ppt_generator.py           # python-pptx PPT 생성
│
├── templates/
│   ├── base.html
│   ├── index.html                 # 메인/검색 화면
│   ├── select.html                # 업체 선택 화면
│   ├── loading.html               # 데이터 수집 중 화면
│   ├── result.html                # 진단 결과 화면
│   ├── manual.html                # 수동 입력 화면
│   └── history.html               # 이력 목록 화면
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── progress.js            # 수집 진행 폴링 로직
│       └── result.js              # 결과 화면 인터랙션
│
├── ppt_output/                    # 생성된 .pptx 파일 저장 디렉토리
└── naver_place_tool.db            # SQLite DB 파일 (자동 생성)
```

---

## 데이터 모델

```python
# models.py — SQLAlchemy 2.0 스타일

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON
from datetime import datetime

class Base(DeclarativeBase):
    pass

class DiagnosisHistory(Base):
    __tablename__ = "diagnosis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 업체 기본 정보
    business_name: Mapped[str] = mapped_column(String(200))          # 업체명
    place_id: Mapped[str] = mapped_column(String(100), nullable=True) # 네이버 플레이스 ID
    address: Mapped[str] = mapped_column(String(300), nullable=True)  # 주소
    category: Mapped[str] = mapped_column(String(100), nullable=True) # 카테고리
    place_url: Mapped[str] = mapped_column(String(500), nullable=True)# 플레이스 URL
    
    # 수집 데이터 (raw)
    photo_count: Mapped[int] = mapped_column(Integer, default=0)       # 사진 수
    review_count: Mapped[int] = mapped_column(Integer, default=0)      # 영수증+방문 리뷰 수
    blog_review_count: Mapped[int] = mapped_column(Integer, default=0) # 블로그 리뷰 수
    has_menu: Mapped[bool] = mapped_column(default=False)              # 메뉴 정보 존재 여부
    has_hours: Mapped[bool] = mapped_column(default=False)             # 영업시간 존재 여부
    has_price: Mapped[bool] = mapped_column(default=False)             # 가격 정보 여부
    
    # 키워드 데이터 (JSON 배열)
    # 형식: [{"keyword": "강남 카페", "search_volume": 12000, "rank": 3}, ...]
    keywords: Mapped[dict] = mapped_column(JSON, default=list)
    
    # 진단 점수
    photo_score: Mapped[float] = mapped_column(Float, default=0.0)     # 0~100
    review_score: Mapped[float] = mapped_column(Float, default=0.0)
    blog_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_score: Mapped[float] = mapped_column(Float, default=0.0)
    info_score: Mapped[float] = mapped_column(Float, default=0.0)      # 정보 완성도
    total_score: Mapped[float] = mapped_column(Float, default=0.0)     # 종합 점수
    grade: Mapped[str] = mapped_column(String(2), default="D")         # A/B/C/D
    
    # 개선 포인트 (JSON 배열, 최대 3개)
    improvement_points: Mapped[dict] = mapped_column(JSON, default=list)
    
    # 메타
    ppt_filename: Mapped[str] = mapped_column(String(300), nullable=True) # 저장된 pptx 파일명
    is_manual: Mapped[bool] = mapped_column(default=False)             # 수동 입력 여부
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)     # UUID
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending / photo_done / review_done / blog_done / keyword_done / complete / failed
    progress: Mapped[int] = mapped_column(Integer, default=0)          # 0~100
    result_id: Mapped[int] = mapped_column(Integer, nullable=True)     # DiagnosisHistory.id
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/` | 메인 화면 렌더링 (index.html) |
| POST | `/search` | 업체명으로 네이버 플레이스 검색, 매칭 업체 1~3개 반환 |
| POST | `/crawl/start` | 선택된 업체 크롤링 잡 시작 → job_id 반환 |
| GET | `/crawl/status/{job_id}` | 크롤링 진행 상태 폴링 (progress %, status, result_id) |
| GET | `/result/{history_id}` | 진단 결과 화면 렌더링 |
| POST | `/manual` | 수동 입력 데이터로 진단 점수 산출 → 결과 저장 |
| GET | `/ppt/generate/{history_id}` | PPT 생성 후 .pptx 파일 스트리밍 다운로드 |
| GET | `/ppt/download/{history_id}` | 기존 생성된 pptx 재다운로드 |
| GET | `/history` | 이력 목록 화면 렌더링 (최신순 전체) |
| DELETE | `/history/{history_id}` | 이력 단건 삭제 (pptx 파일도 함께 삭제) |

---

## 핵심 구현 포인트

### 1. 업체 검색 (`services/naver_place_crawler.py`)
```
Playwright로 아래 URL 직접 접근:
https://map.naver.com/v5/search/{업체명}

접근 후 .place_bluelink 또는 [data-nclick*="place"] 셀렉터로 업체 목록 파싱.
각 업체에서 추출:
  - place_id: URL에서 추출 (/place/1234567 → "1234567")
  - 업체명: .place_bluelink 텍스트
  - 주소: .addr 텍스트
  - 카테고리: .category 텍스트

반환 형식: List[dict] 최대 3개
```

### 2. 플레이스 상세 데이터 크롤링 (`services/naver_place_crawler.py`)
```
URL: https://place.map.naver.com/place/{place_id}

Playwright page.goto() 후 page.wait_for_load_state("networkidle") 대기

추출 대상 및 셀렉터:
  - 사진 수: "사진 N장" 텍스트 파싱 → 정규식 r'사진\s*(\d+)장'
  - 영수증 리뷰 수: "영수증리뷰 N" 텍스트 파싱
  - 방문자 리뷰 수: "방문자리뷰 N" 텍스트 파싱  
  - 블로그 리뷰 수: "블로그리뷰 N" 텍스트 파싱
  - 영업시간 존재: "영업시간" 요소 존재 여부 bool
  - 메뉴 존재: "메뉴" 탭 존재 여부