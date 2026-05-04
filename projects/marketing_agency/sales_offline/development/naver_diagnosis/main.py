"""
네이버 플레이스 자동 진단 + PPT 제안서 생성 툴
FastAPI 메인 애플리케이션
"""
import os
import sys
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# 현재 디렉토리를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# core/company/.env 중앙 로드
from pathlib import Path as _Path
for _p in _Path(__file__).resolve().parents:
    if (_p / "company" / ".env").exists():
        load_dotenv(_p / "company" / ".env")
        break
else:
    load_dotenv()

from database import init_db, close_db
from sqlalchemy import update, select
from models import CrawlJob, CRMBusiness
from routers import (
    search_router,
    crawl_router,
    ppt_router,
    manual_router,
    history_router,
    message_router,
    batch_router,
    crm_router,
)


# 디렉토리 경로 설정 (lifespan보다 먼저 정의)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
PPT_OUTPUT_DIR = os.path.join(BASE_DIR, "ppt_output")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(PPT_OUTPUT_DIR, exist_ok=True)


async def _ppt_cleanup_loop(ppt_dir: str):
    """1시간마다 실행하여 24시간 지난 PPT 파일을 삭제한다."""
    while True:
        try:
            cutoff = time.time() - 24 * 3600
            for fname in os.listdir(ppt_dir):
                fpath = os.path.join(ppt_dir, fname)
                if fname.endswith(".pptx") and os.path.getmtime(fpath) < cutoff:
                    os.remove(fpath)
                    print(f"[Cleanup] 삭제: {fname}")
        except Exception as e:
            print(f"[Cleanup] 오류: {e}")
        await asyncio.sleep(3600)  # 1시간마다 반복


from browser_manager import launch_browser, get_browser


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 시작/종료 시 실행되는 lifespan 이벤트
    - Playwright 브라우저 초기화/종료
    - 데이터베이스 초기화/종료
    """
    # 시작 시
    print("[Startup] 데이터베이스 초기화 중...")
    # 개발 단계: DB_RESET=true 환경변수 설정 시 테이블 재생성 (스키마 변경 반영)
    db_reset = os.getenv("DB_RESET", "false").lower() == "true"
    await init_db(drop_existing=db_reset)
    if db_reset:
        print("[Startup] DB_RESET=true: 기존 테이블 삭제 후 재생성됨")

    # 서버 재시작 시 미완료 잡(crawling/searching/analyzing/generating)을 failed로 초기화
    from database import async_session_maker
    async with async_session_maker() as db:
        await db.execute(
            update(CrawlJob)
            .where(CrawlJob.status.in_(["pending", "searching", "crawling", "analyzing", "generating"]))
            .values(status="failed", error_message="서버 재시작으로 인해 취소됨")
        )
        await db.commit()
    print("[Startup] 미완료 크롤링 잡 초기화 완료")

    # PPT 자동 삭제 백그라운드 태스크 시작 (24시간 지난 파일 삭제)
    ppt_cleanup_task = asyncio.create_task(_ppt_cleanup_loop(PPT_OUTPUT_DIR))

    # 벤치마크 통계 로드 (Phase 4)
    print("[Startup] 벤치마크 통계 로드 중...")
    try:
        from services.benchmark_scorer import init_provider as init_benchmark
        async with async_session_maker() as db:
            await init_benchmark(db)
        print("[Startup] 벤치마크 통계 로드 완료 (benchmark_premium 84개 레코드 처리됨)")
    except Exception as e:
        print(f"[Startup] 벤치마크 로드 오류 (폴백 사용): {e}")

    # 업종별 range 데이터 로드 (월손실금 계산용)
    print("[Startup] 업종별 range 데이터 로드 중...")
    try:
        from services.industry_range import init_provider as init_industry_range
        async with async_session_maker() as db:
            await init_industry_range(db)
        print("[Startup] 업종별 range 데이터 로드 완료 (월손실금 range 계산 준비됨)")
    except Exception as e:
        print(f"[Startup] 업종별 range 로드 오류 (폴백 사용): {e}")

    # CRM 일일 리셋
    async def _crm_daily_reset():
        """자정 또는 서버 시작 시 today_selected, contacted_today 리셋"""
        from datetime import date as date_cls
        from sqlalchemy import select
        from models import CRMBusiness

        try:
            async with async_session_maker() as db:
                today = date_cls.today()
                result = await db.execute(
                    select(CRMBusiness).where(
                        (CRMBusiness.last_reset_date < today) |
                        (CRMBusiness.last_reset_date == None)
                    )
                )
                businesses = result.scalars().all()
                for biz in businesses:
                    biz.today_selected = False
                    biz.contacted_today = False
                    biz.last_reset_date = today
                await db.commit()
                if businesses:
                    print(f"[CRM] 일일 리셋: {len(businesses)}개 업체")
        except Exception as e:
            print(f"[CRM] 일일 리셋 실패: {e}")

    # CRM 초기화
    print("[Startup] CRM 초기화 중...")
    try:
        from services.crm_service import build_phone_lookup, sync_from_naver_diagnosis_to_crm, monitor_pdfs_async
        build_phone_lookup()
    except Exception as e:
        print(f"[Startup] 전화번호 캐시 구축 실패 (무시): {e}")
    try:
        async with async_session_maker() as crm_db:
            await sync_from_naver_diagnosis_to_crm(crm_db)
            await _crm_daily_reset()
    except Exception as e:
        print(f"[Startup] CRM 동기화 실패 (무시): {e}")
    pdf_monitor_task = asyncio.create_task(monitor_pdfs_async())
    print("[Startup] CRM 초기화 완료")

    print("[Startup] Playwright 브라우저 초기화 중...")
    try:
        playwright = await asyncio.wait_for(async_playwright().start(), timeout=10)
        browser = await asyncio.wait_for(launch_browser(playwright), timeout=15)
        app.state.playwright = playwright
        app.state.browser = browser
        print("[Startup] Playwright 브라우저 초기화 완료")
    except Exception as e:
        print(f"[Startup] Playwright 초기화 실패 (크롤링/PDF 기능 불가, CRM은 정상): {e}")
        app.state.playwright = None
        app.state.browser = None

    print("[Startup] 서버 준비 완료!")

    yield

    # 종료 시
    print("[Shutdown] 리소스 정리 중...")
    ppt_cleanup_task.cancel()
    pdf_monitor_task.cancel()
    if app.state.browser:
        await app.state.browser.close()
    if app.state.playwright:
        await app.state.playwright.stop()
    await close_db()
    print("[Shutdown] 서버 종료 완료")


# FastAPI 앱 생성
app = FastAPI(
    title="네이버 플레이스 진단 API",
    description="네이버 플레이스 자동 진단 및 PPT 제안서 생성 서비스",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files 마운트
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates 설정
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Routers 등록
app.include_router(search_router)
app.include_router(crawl_router)
app.include_router(ppt_router)
app.include_router(manual_router)
app.include_router(history_router)
app.include_router(message_router)
app.include_router(batch_router)
app.include_router(crm_router, prefix="")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    메인 페이지 (index.html 렌더링)
    """
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception:
        # 템플릿이 없는 경우 간단한 HTML 반환
        return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>네이버 플레이스 진단</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Malgun Gothic', sans-serif; background: #f5f5f5; min-height: 100vh; display: flex; justify-content: center; align-items: center; }
        .container { max-width: 800px; width: 90%; padding: 40px; background: white; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        h1 { color: #005a9e; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        input, textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
        input:focus, textarea:focus { outline: none; border-color: #005a9e; }
        .btn { width: 100%; padding: 14px; background: #005a9e; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; transition: background 0.3s; }
        .btn:hover { background: #004080; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .result { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; display: none; }
        .result.show { display: block; }
        .result h3 { color: #005a9e; margin-bottom: 15px; }
        .score-box { display: flex; justify-content: space-between; align-items: center; padding: 15px; background: white; border-radius: 8px; margin-bottom: 10px; }
        .grade { font-size: 32px; font-weight: bold; }
        .grade.A { color: #00c73c; } .grade.B { color: #4caf50; } .grade.C { color: #ff9800; } .grade.D { color: #f44336; }
        .download-btn { display: inline-block; margin-top: 15px; padding: 12px 24px; background: #03c75a; color: white; border-radius: 8px; text-decoration: none; }
        .api-docs { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        .api-docs a { color: #005a9e; }
        .spinner { display: none; width: 24px; height: 24px; border: 3px solid #f3f3f3; border-top: 3px solid #005a9e; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>네이버 플레이스 진단</h1>
        <p class="subtitle">업체 정보를 입력하면 플레이스 점수와 PPT 제안서를 자동 생성합니다</p>

        <form id="diagnosisForm">
            <div class="form-group">
                <label for="businessName">업체명 *</label>
                <input type="text" id="businessName" required placeholder="예: 스타벅스 강남점">
            </div>

            <div class="form-group">
                <label for="address">주소</label>
                <input type="text" id="address" placeholder="예: 서울 강남구 테헤란로 123">
            </div>

            <div class="form-group">
                <label for="category">업종</label>
                <input type="text" id="category" placeholder="예: 카페">
            </div>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                <div class="form-group">
                    <label for="photoCount">사진 수</label>
                    <input type="number" id="photoCount" min="0" value="0">
                </div>
                <div class="form-group">
                    <label for="reviewCount">리뷰 수</label>
                    <input type="number" id="reviewCount" min="0" value="0">
                </div>
                <div class="form-group">
                    <label for="blogCount">블로그 리뷰</label>
                    <input type="number" id="blogCount" min="0" value="0">
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                <label><input type="checkbox" id="hasHours"> 영업시간 등록</label>
                <label><input type="checkbox" id="hasMenu"> 메뉴 등록</label>
                <label><input type="checkbox" id="hasPrice"> 가격 등록</label>
            </div>

            <button type="submit" class="btn" id="submitBtn">진단 시작</button>
            <div class="spinner" id="spinner"></div>
        </form>

        <div class="result" id="result">
            <h3>진단 결과</h3>
            <div class="score-box">
                <div>
                    <div style="font-size: 14px; color: #666;">종합 점수</div>
                    <div style="font-size: 24px; font-weight: bold;" id="totalScore">-</div>
                </div>
                <div class="grade" id="grade">-</div>
            </div>
            <div id="improvements"></div>
            <a href="#" class="download-btn" id="downloadBtn" target="_blank">PPT 다운로드</a>
        </div>

        <div class="api-docs">
            <p>API 문서: <a href="/docs" target="_blank">/docs</a> (Swagger UI)</p>
        </div>
    </div>

    <script>
        document.getElementById('diagnosisForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const btn = document.getElementById('submitBtn');
            const spinner = document.getElementById('spinner');
            const result = document.getElementById('result');

            btn.disabled = true;
            spinner.style.display = 'block';
            result.classList.remove('show');

            const data = {
                business_name: document.getElementById('businessName').value,
                address: document.getElementById('address').value || null,
                category: document.getElementById('category').value || null,
                photo_count: parseInt(document.getElementById('photoCount').value) || 0,
                review_count: parseInt(document.getElementById('reviewCount').value) || 0,
                blog_review_count: parseInt(document.getElementById('blogCount').value) || 0,
                has_hours: document.getElementById('hasHours').checked,
                has_menu: document.getElementById('hasMenu').checked,
                has_price: document.getElementById('hasPrice').checked,
                keywords: []
            };

            try {
                const response = await fetch('/manual', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const json = await response.json();

                if (json.success) {
                    document.getElementById('totalScore').textContent = json.total_score.toFixed(1) + '점';
                    const gradeEl = document.getElementById('grade');
                    gradeEl.textContent = json.grade;
                    gradeEl.className = 'grade ' + json.grade;

                    const improvements = json.improvement_points.map(p =>
                        '<div style="padding: 8px 0; border-bottom: 1px solid #eee;">• ' + p.message + '</div>'
                    ).join('');
                    document.getElementById('improvements').innerHTML = improvements;

                    document.getElementById('downloadBtn').href = json.download_url;
                    result.classList.add('show');
                } else {
                    alert('진단 실패: ' + (json.detail || 'Unknown error'));
                }
            } catch (err) {
                alert('오류: ' + err.message);
            } finally {
                btn.disabled = false;
                spinner.style.display = 'none';
            }
        });
    </script>
</body>
</html>
        """)


@app.get("/result/{history_id}", response_class=HTMLResponse)
async def result_page(history_id: int, request: Request):
    """
    진단 결과 페이지 렌더링
    """
    from database import async_session_maker
    from models import DiagnosisHistory
    from services.message_generator import generate_all_messages

    try:
        async with async_session_maker() as db:
            history = await db.get(DiagnosisHistory, history_id)

            if not history:
                return templates.TemplateResponse("error.html", {
                    "request": request,
                    "message": "진단 이력을 찾을 수 없습니다",
                    "error_type": "not_found"
                })

            # ── priority_tag → 템플릿용 sales_priority 변환 ──────────
            # 모델: priority_tag ("1순위"/"2순위"/"패스")
            # 템플릿: sales_priority ("1"/"2"/"pass"), sales_priority_label
            _tag = history.priority_tag or "2순위"
            _priority_map = {"1순위": "1", "2순위": "2", "패스": "pass"}
            sales_priority = _priority_map.get(_tag, "2")
            sales_priority_label = _tag
            # history 객체에 동적 속성 추가 (Jinja2에서 접근)
            history.sales_priority = sales_priority
            history.sales_priority_label = sales_priority_label

            # ── 메시지 구조 → 템플릿 호환 포맷으로 변환 ──────────────
            # generate_all_messages: {first: {type, text, label}, second: str,
            #                          third: str, fourth: {보류:, 무응답:, ...}}
            # 템플릿 기대: {first: {auto_version, auto_reason, text, versions, sms_text},
            #               second: {text}, third: {text},
            #               fourth: {versions: [{label, text}]}}
            raw_messages = history.messages
            if not raw_messages:
                # 캐시 없으면 즉시 생성
                from sqlalchemy import update as sa_update
                msg_data = {
                    "business_name": history.business_name,
                    "address": history.address or "",
                    "category": history.category or "",
                    "photo_count": history.photo_count,
                    "review_count": history.review_count,
                    "blog_review_count": history.blog_review_count,
                    "has_hours": history.has_hours,
                    "has_menu": history.has_menu,
                    "has_price": history.has_price,
                    "has_intro": history.has_intro,
                    "has_directions": history.has_directions,
                    "has_booking": history.has_booking,
                    "has_talktalk": history.has_talktalk,
                    "has_smartcall": history.has_smartcall,
                    "has_coupon": history.has_coupon,
                    "has_news": history.has_news,
                    "has_owner_reply": history.has_owner_reply,
                    "has_instagram": history.has_instagram,
                    "has_kakao": history.has_kakao,
                    "has_menu_description": history.has_menu_description,
                    "keywords": history.keywords or [],
                    "naver_place_rank": history.naver_place_rank,
                    "photo_score": history.photo_score,
                    "review_score": history.review_score,
                    "blog_score": history.blog_score,
                    "info_score": history.info_score,
                    "keyword_score": history.keyword_score,
                    "convenience_score": history.convenience_score,
                    "engagement_score": history.engagement_score,
                    "total_score": history.total_score,
                    "grade": history.grade,
                    "competitor_avg_review": history.competitor_avg_review or 0,
                    "competitor_avg_photo": history.competitor_avg_photo or 0,
                    "competitor_avg_blog": history.competitor_avg_blog or 0,
                    "estimated_lost_customers": history.estimated_lost_customers or 0,
                    "news_last_days": 0,
                    "bookmark_count": 0,
                }
                raw_messages = generate_all_messages(msg_data)
                try:
                    await db.execute(
                        sa_update(DiagnosisHistory)
                        .where(DiagnosisHistory.id == history_id)
                        .values(messages=raw_messages)
                    )
                    await db.commit()
                except Exception:
                    pass

            # 템플릿 호환 구조로 변환
            messages = _build_template_messages(raw_messages)

            # ── 핵심 수치 카드 (key_metrics) ──────────────────────────
            competitor_avg_review = history.competitor_avg_review or 0
            key_metrics = []
            if history.naver_place_rank and history.naver_place_rank > 0:
                level = "warning" if history.naver_place_rank > 10 else "good"
                key_metrics.append({
                    "label": "현재 순위",
                    "value": f"{history.naver_place_rank}위",
                    "description": "1~5위 밖이면 사실상 안 보여요" if history.naver_place_rank > 5 else "상위권 노출 중",
                    "level": level,
                })
            if competitor_avg_review > 0 and history.review_count >= 0:
                level = "warning" if history.review_count < competitor_avg_review else "good"
                key_metrics.append({
                    "label": "리뷰 격차",
                    "value": f"내 {history.review_count}개 vs 경쟁사 {competitor_avg_review}개",
                    "description": "경쟁사 평균 대비 리뷰 수",
                    "level": level,
                })
            if history.estimated_lost_customers and history.estimated_lost_customers > 0:
                key_metrics.append({
                    "label": "추정 손실 고객",
                    "value": f"월 {history.estimated_lost_customers}명",
                    "description": "경쟁사로 가고 있는 추정 인원",
                    "level": "warning",
                })

            # ── 항목별 점수 (score_items) ─────────────────────────────
            score_items = [
                {"name": "사진", "score": int(history.photo_score)},
                {"name": "리뷰", "score": int(history.review_score)},
                {"name": "블로그", "score": int(history.blog_score)},
                {"name": "정보", "score": int(history.info_score)},
                {"name": "키워드", "score": int(history.keyword_score)},
                {"name": "편의기능", "score": int(history.convenience_score)},
                {"name": "참여도", "score": int(history.engagement_score)},
            ]

            return templates.TemplateResponse("result.html", {
                "request": request,
                "history": history,
                "messages": messages,
                "key_metrics": key_metrics,
                "score_items": score_items,
            })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"페이지 로딩 중 오류가 발생했습니다: {str(e)}",
            "error_type": "server_error"
        })


def _build_template_messages(raw: dict) -> dict:
    """
    generate_all_messages 출력 → result.html 템플릿 호환 구조 변환.

    raw 구조:
      first:  {type, text, label}
      second: str
      third:  str
      fourth: {보류, 무응답, 비싸다, 직접}

    템플릿 기대 구조:
      first:  {auto_version, auto_reason, text, versions: [{label, text}], sms_text}
      second: {text}
      third:  {text}
      fourth: {versions: [{label, text}]}
    """
    if not raw:
        return {}

    first_raw = raw.get("first", {})
    fourth_raw = raw.get("fourth", {})

    # 1차: 단일 버전으로 처리 (versions 리스트 포함)
    sms_text = first_raw.get("sms_text") or None
    first = {
        "auto_version": True,
        "auto_reason": f"자동 선택: {first_raw.get('label', '')} ({first_raw.get('type', '')}형)",
        "text": first_raw.get("text", ""),
        "sms_text": sms_text,
        "versions": [
            {
                "label": first_raw.get("label", ""),
                "text": first_raw.get("text", ""),
                "sms_text": sms_text,
            }
        ],
    }

    # 2차: 문자열 → {text}
    second = {"text": raw.get("second", "")}

    # 3차: 문자열 → {text}
    third = {"text": raw.get("third", "")}

    # 4차: 상황별 버전 목록으로 변환
    fourth_labels = {"보류": "보류할 때", "무응답": "무응답일 때", "비싸다": "비싸다고 할 때", "직접": "직접 하겠다고 할 때", "경험있음": "전에 해봤는데 효과없었다고 할 때"}
    fourth_versions = [
        {"label": fourth_labels.get(k, k), "text": v}
        for k, v in fourth_raw.items()
        if v
    ]
    fourth = {"versions": fourth_versions}

    return {
        "first": first,
        "second": second,
        "third": third,
        "fourth": fourth,
    }


@app.get("/error", response_class=HTMLResponse)
async def error_page(request: Request, message: str = "오류가 발생했습니다", error_type: str = "unknown"):
    """
    에러 페이지 렌더링
    """
    try:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": message,
            "error_type": error_type
        })
    except Exception:
        # 템플릿이 없는 경우 간단한 HTML 반환
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>오류 - 네이버 플레이스 진단</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Malgun Gothic', sans-serif; background: #f5f5f5; min-height: 100vh; display: flex; justify-content: center; align-items: center; }}
        .container {{ max-width: 600px; width: 90%; padding: 40px; background: white; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; }}
        h1 {{ color: #f44336; margin-bottom: 20px; }}
        p {{ color: #666; margin-bottom: 30px; line-height: 1.6; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: #005a9e; color: white; text-decoration: none; border-radius: 8px; transition: background 0.3s; }}
        .btn:hover {{ background: #004080; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>오류가 발생했습니다</h1>
        <p>{message}</p>
        <a href="/" class="btn">홈으로 돌아가기</a>
    </div>
</body>
</html>
        """)


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """
    진단 이력 목록 페이지 렌더링.
    history.html이 {histories} 컨텍스트를 기대하므로 직접 DB 조회 후 전달.
    """
    from database import async_session_maker
    from models import DiagnosisHistory
    from sqlalchemy import select, desc

    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(DiagnosisHistory)
                .order_by(desc(DiagnosisHistory.created_at))
                .limit(200)
            )
            histories = result.scalars().all()

            # priority_tag → sales_priority / sales_priority_label 동적 속성 추가
            _priority_map = {"1순위": "1", "2순위": "2", "패스": "pass"}
            for h in histories:
                _tag = h.priority_tag or "2순위"
                h.sales_priority = _priority_map.get(_tag, "2")
                h.sales_priority_label = _tag

            return templates.TemplateResponse("history.html", {
                "request": request,
                "histories": histories,
            })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"이력 페이지 로딩 오류: {str(e)}",
            "error_type": "server_error",
        })


@app.get("/batch", response_class=HTMLResponse)
async def batch_page(request: Request):
    """배치 진단 페이지 렌더링."""
    try:
        return templates.TemplateResponse("batch.html", {"request": request})
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"배치 페이지 로딩 오류: {str(e)}",
            "error_type": "server_error",
        })


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "browser": app.state.browser is not None,
    }


if __name__ == "__main__":
    import uvicorn

    # Windows에서 Playwright(subprocess) 사용을 위해 ProactorEventLoop 필요
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # reload=True는 Windows ProactorLoop와 충돌
    )
