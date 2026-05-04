"""
크롤링 라우터
POST /crawl/start: 크롤링 시작 (백그라운드)
GET /crawl/status/{job_id}: 크롤링 상태 조회
"""
import uuid
import asyncio
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db, async_session_maker
from models import CrawlJob, DiagnosisHistory
from services.naver_place_crawler import NaverPlaceCrawler
from services.naver_search_ad import NaverSearchAdAPI
from services.scorer import DiagnosisScorer
from services.ppt_generator import PPTGenerator
from browser_manager import get_browser

router = APIRouter(prefix="/crawl", tags=["crawl"])

# 동시 크롤링 최대 3개 제한 (메모리 보호)
_crawl_semaphore = asyncio.Semaphore(3)


class CrawlStartRequest(BaseModel):
    """크롤링 시작 요청"""
    place_id: Optional[str] = Field(None, description="네이버 플레이스 ID (없으면 업체명으로 자동 검색)")
    business_name: str = Field(..., description="업체명")
    address: Optional[str] = Field(None, description="주소")
    category: Optional[str] = Field(None, description="업종")
    keywords: Optional[List[str]] = Field(default=[], description="분석할 키워드 목록")


class CrawlStartResponse(BaseModel):
    """크롤링 시작 응답"""
    success: bool
    job_id: str
    message: str


class CrawlStatusResponse(BaseModel):
    """크롤링 상태 응답"""
    job_id: str
    status: str
    progress: int
    result_id: Optional[int]
    error_message: Optional[str]


async def run_crawl_job(
    job_id: str,
    place_id: str,
    business_name: str,
    address: Optional[str],
    category: Optional[str],
    keywords: List[str],
    browser,
):
    """
    백그라운드 크롤링 작업 실행

    상태 진행:
    - pending -> searching (20%)
    - searching -> crawling (50%)
    - crawling -> analyzing (75%)
    - analyzing -> generating (90%)
    - generating -> done (100%)
    """
    async with _crawl_semaphore:
        async with async_session_maker() as db:
            try:
                # 1. searching: 검색 단계
                job = await db.get(CrawlJob, job_id)
                if not job:
                    return

                job.status = "searching"
                job.progress = 20
                await db.commit()

                crawler = NaverPlaceCrawler(browser)

                # place_id 없으면 업체명+주소로 자동 검색 (주소 있으면 더 정확)
                if not place_id:
                    search_query = f"{address} {business_name}".strip() if address else business_name
                    place_id = await crawler.find_place_id(search_query)

                # 2. crawling: Playwright 크롤링
                job.status = "crawling"
                job.progress = 50
                await db.commit()

                # place_id가 있으면 상세 페이지, 없으면 검색 결과에서 직접 추출
                if place_id:
                    crawl_result = await crawler.crawl_place_detail(place_id)
                else:
                    # 검색 결과 페이지에서 직접 데이터 추출
                    search_query = f"{address} {business_name}".strip() if address else business_name
                    crawl_result = await crawler.crawl_from_search(search_query)

                # 데이터가 모두 0이면 검색 결과에서 다시 시도
                if (crawl_result.get("photo_count", 0) == 0 and
                    crawl_result.get("visitor_review_count", 0) == 0 and
                    crawl_result.get("blog_review_count", 0) == 0):
                    print(f"[Crawl] 상세 페이지 데이터 없음, 검색 결과에서 재시도")
                    crawl_result = await crawler.crawl_from_search(business_name)

                # crawl_from_search가 내부적으로 place_id를 찾은 경우 로컬 변수에 반영
                if not place_id and crawl_result.get("place_id"):
                    place_id = crawl_result["place_id"]

                # 3. analyzing: 점수 계산
                job.status = "analyzing"
                job.progress = 75
                await db.commit()

                # 데이터 정리
                diagnosis_data = {
                    "business_name": business_name,
                    "place_id": place_id,
                    "address": address,
                    "category": category,
                    "place_url": crawl_result.get("place_url"),
                    "photo_count": crawl_result.get("photo_count", 0),
                    "review_count": (
                        crawl_result.get("receipt_review_count", 0) +
                        crawl_result.get("visitor_review_count", 0)
                    ),
                    "blog_review_count": crawl_result.get("blog_review_count", 0),
                    "has_menu": crawl_result.get("has_menu", False),
                    "has_hours": crawl_result.get("has_hours", False),
                    "has_price": crawl_result.get("has_price", False),
                    "keywords": crawl_result.get("keywords", []),
                    # 확장 필드
                    "has_intro": crawl_result.get("has_intro", False),
                    "intro_text_length": crawl_result.get("intro_text_length", 0),
                    "has_directions": crawl_result.get("has_directions", False),
                    "directions_text_length": crawl_result.get("directions_text_length", 0),
                    "has_booking": crawl_result.get("has_booking", False),
                    "has_talktalk": crawl_result.get("has_talktalk", False),
                    "has_smartcall": crawl_result.get("has_smartcall", False),
                    "has_coupon": crawl_result.get("has_coupon", False),
                    "has_news": crawl_result.get("has_news", False),
                    "menu_count": crawl_result.get("menu_count", 0),
                    "has_menu_description": crawl_result.get("has_menu_description", False),
                    "receipt_review_count": crawl_result.get("receipt_review_count", 0),
                    "visitor_review_count": crawl_result.get("visitor_review_count", 0),
                    "has_owner_reply": crawl_result.get("has_owner_reply", False),
                    "has_instagram": crawl_result.get("has_instagram", False),
                    "has_kakao": crawl_result.get("has_kakao", False),
                    "naver_place_rank": crawl_result.get("naver_place_rank", 0),
                    "related_keywords": [],
                }

                # 키워드 검색량 조회 (NaverSearchAdAPI)
                if diagnosis_data["keywords"]:
                    try:
                        ad_api = NaverSearchAdAPI()
                        enriched = []
                        for kw in diagnosis_data["keywords"][:5]:
                            kw_name = kw if isinstance(kw, str) else kw.get("keyword", "")
                            if not kw_name:
                                continue
                            stats = await ad_api.get_keyword_stats(kw_name)
                            enriched.append({
                                "keyword": kw_name,
                                "search_volume": (stats.get("monthly_search_pc", 0) or 0) + (stats.get("monthly_search_mobile", 0) or 0),
                                "rank": 0,
                            })
                        if enriched:
                            diagnosis_data["keywords"] = enriched
                    except Exception as e:
                        print(f"[Crawl] 키워드 검색량 조회 오류: {e}")

                # 연관 키워드 및 순위 조회
                try:
                    # 순위 조회용 키워드: 지역+업종 (태그 키워드 X)
                    _addr = address or ""
                    _region = _addr.split()[0] if _addr else ""
                    _cat = category or ""
                    rank_kw = f"{_region} {_cat}".strip() or business_name
                    related = await crawler.get_related_keywords(rank_kw)
                    diagnosis_data["related_keywords"] = related

                    if place_id:
                        rank = await crawler.get_place_rank(rank_kw, place_id)
                        diagnosis_data["naver_place_rank"] = rank
                except Exception as e:
                    print(f"[Crawl] 연관 키워드/순위 조회 오류: {e}")

                # 점수 계산
                scores = DiagnosisScorer.calculate_all(diagnosis_data)
                diagnosis_data.update(scores)

                # 경쟁사 데이터: 실시간 크롤링 후 폴백 보정
                from services.competitor import CompetitorAnalyzer
                from config.industry_weights import get_competitor_fallback
                competitor_avg_review = 0
                competitor_avg_photo = 0
                competitor_avg_blog = 0
                try:
                    _comp = CompetitorAnalyzer(browser)
                    _addr = address or ""
                    # 주소에서 시/군/구 추출 ("경기도 양주시..." → "양주")
                    _region = ""
                    for _word in _addr.split()[:4]:
                        if _word.endswith(("시", "군", "구")):
                            _region = _word[:-1]  # "양주시" → "양주"
                            break
                    if not _region and _addr:
                        _region = _addr.split()[0]  # 못 찾으면 첫 단어 폴백
                    _cat = category or ""
                    _kw = f"{_region} {_cat}".strip() if _region else _cat
                    if _kw:
                        comp_data = await _comp.get_competitor_summary(_kw, _cat)
                        competitor_avg_review = comp_data.get("top_review", 0)
                        competitor_avg_photo = comp_data.get("top_photo", 0)
                        competitor_avg_blog = comp_data.get("avg_blog", 0)
                        diagnosis_data["competitor_avg_review"] = competitor_avg_review
                        diagnosis_data["competitor_avg_photo"] = competitor_avg_photo
                        diagnosis_data["competitor_avg_blog"] = competitor_avg_blog
                        # 실제 경쟁사 상세 목록 (이름+수치) — 메시지 생성기에 전달
                        diagnosis_data["competitor_details"] = comp_data.get("competitors", [])
                except Exception as e:
                    print(f"[Crawl] 경쟁사 크롤링 오류 (폴백 사용): {e}")
                    fb = get_competitor_fallback(category or "")
                    competitor_avg_review = fb["top_review"]
                    competitor_avg_photo = fb.get("top_photo", fb["avg_photo"])
                    competitor_avg_blog = fb["avg_blog"]

                # 영업 우선순위 자동 분류
                from routers.batch import _auto_priority
                priority_tag = _auto_priority(diagnosis_data)
                diagnosis_data["priority_tag"] = priority_tag

                # ─── AI 분석 (병렬) ────────────────────────────────
                # 리뷰 감성 분석 + 사진 품질 분석을 동시에 실행
                from services.ai_analyzer import analyze_review_sentiment, personalize_first_message
                from services.photo_analyzer import analyze_photo_quality_from_bytes

                _review_texts = crawl_result.get("review_texts", [])
                _photo_screenshots = crawl_result.get("photo_urls", [])  # 이제 bytes 리스트
                diagnosis_data["review_texts"] = _review_texts
                diagnosis_data["photo_urls"] = []  # bytes는 DB 저장 불필요 → 빈 리스트
                diagnosis_data["bookmark_count"] = crawl_result.get("bookmark_count", 0)

                # 병렬 AI 분석
                _fallback_sentiment = {"negative_ratio": 0.0, "main_complaints": [], "risk_level": "none", "sentiment_score": 50}
                _fallback_photo = {"quality_score": 0, "issues": [], "summary": ""}

                async def _run_sentiment():
                    if _review_texts:
                        return await analyze_review_sentiment(_review_texts)
                    return _fallback_sentiment

                async def _run_photo():
                    if _photo_screenshots:
                        return await analyze_photo_quality_from_bytes(_photo_screenshots)
                    return _fallback_photo

                sentiment_result = _fallback_sentiment
                photo_result = _fallback_photo
                try:
                    _s, _p = await asyncio.gather(_run_sentiment(), _run_photo(), return_exceptions=True)
                    if not isinstance(_s, Exception):
                        sentiment_result = _s
                    else:
                        print(f"[Crawl] 감성 분석 실패: {_s}")
                    if not isinstance(_p, Exception):
                        photo_result = _p
                    else:
                        print(f"[Crawl] 사진 품질 분석 실패: {_p}")
                except Exception as e:
                    print(f"[Crawl] AI 분석 오류: {e}")

                # AI 결과 저장
                diagnosis_data["review_sentiment_score"] = float(sentiment_result.get("sentiment_score", 50))
                diagnosis_data["review_negative_ratio"] = float(sentiment_result.get("negative_ratio", 0.0))
                diagnosis_data["review_main_complaints"] = sentiment_result.get("main_complaints", [])
                diagnosis_data["photo_quality_score"] = float(photo_result.get("quality_score", 0))
                diagnosis_data["photo_quality_issues"] = photo_result.get("issues", [])

                # AI 기반 점수 조정 (감성 위험도 → 리뷰 점수 조정)
                risk_level = sentiment_result.get("risk_level", "none")
                if risk_level == "high":
                    diagnosis_data["review_score"] = max(0, diagnosis_data.get("review_score", 0) - 15)
                    diagnosis_data["improvement_points"].insert(0, {
                        "category": "review",
                        "priority": 1,
                        "message": f"부정 리뷰 {int(diagnosis_data['review_negative_ratio'] * 100)}% — {', '.join(diagnosis_data['review_main_complaints'][:2])}",
                    })
                elif risk_level == "medium":
                    diagnosis_data["review_score"] = max(0, diagnosis_data.get("review_score", 0) - 8)

                # 사진 품질이 낮으면 사진 점수 추가 조정
                photo_q = diagnosis_data["photo_quality_score"]
                if 0 < photo_q < 40:
                    diagnosis_data["photo_score"] = max(0, diagnosis_data.get("photo_score", 0) - 10)
                    if photo_result.get("issues"):
                        diagnosis_data["improvement_points"].insert(0, {
                            "category": "photo",
                            "priority": 1,
                            "message": f"사진 품질 낮음 — {', '.join(photo_result['issues'][:2])}",
                        })

                # 총점 재계산 (AI 조정 반영)
                from config.industry_weights import get_weights
                _weights = get_weights(diagnosis_data.get("category", ""))
                _recalc_scores = {k: diagnosis_data.get(f"{k}_score", 0) for k in _weights}
                diagnosis_data["total_score"] = DiagnosisScorer.calculate_total_score(_recalc_scores, weights=_weights)
                diagnosis_data["grade"] = DiagnosisScorer.calculate_grade(diagnosis_data["total_score"])
                # ───────────────────────────────────────────────────

                # 메시지 생성
                from services.message_generator import generate_all_messages
                messages = generate_all_messages(diagnosis_data)
                diagnosis_data["messages"] = messages
                # PPT 표지 충격 문구용: estimated_lost_customers를 diagnosis_data에 직접 저장
                diagnosis_data["estimated_lost_customers"] = messages.get("estimated_lost_customers", 0)

                # AI 1차 메시지 자연어화
                try:
                    ai_first = await personalize_first_message(
                        messages["first"]["text"],
                        business_name,
                        {
                            "category": category or "",
                            "grade": diagnosis_data.get("grade", "D"),
                            "msg_type": messages["first"].get("type", "A"),
                            "estimated_lost": diagnosis_data.get("estimated_lost_customers", 0),
                        },
                    )
                    diagnosis_data["ai_first_message"] = ai_first
                    # messages 딕셔너리에도 반영
                    messages["first"]["ai_text"] = ai_first
                except Exception as e:
                    print(f"[Crawl] AI 메시지 자연어화 오류: {e}")
                    diagnosis_data["ai_first_message"] = None

                # 4. generating: PPT 생성
                job.status = "generating"
                job.progress = 90
                await db.commit()

                ppt_gen = PPTGenerator(output_dir="ppt_output")
                ppt_filename = ppt_gen.generate(diagnosis_data)
                diagnosis_data["ppt_filename"] = ppt_filename

                # DiagnosisHistory 저장
                history = DiagnosisHistory(
                    business_name=diagnosis_data["business_name"],
                    place_id=diagnosis_data["place_id"],
                    address=diagnosis_data.get("address"),
                    category=diagnosis_data.get("category"),
                    place_url=diagnosis_data.get("place_url"),
                    photo_count=diagnosis_data["photo_count"],
                    review_count=diagnosis_data["review_count"],
                    blog_review_count=diagnosis_data["blog_review_count"],
                    has_menu=diagnosis_data["has_menu"],
                    has_hours=diagnosis_data["has_hours"],
                    has_price=diagnosis_data["has_price"],
                    keywords=diagnosis_data["keywords"],
                    # 확장 필드
                    has_intro=diagnosis_data.get("has_intro", False),
                    intro_text_length=diagnosis_data.get("intro_text_length", 0),
                    has_directions=diagnosis_data.get("has_directions", False),
                    directions_text_length=diagnosis_data.get("directions_text_length", 0),
                    has_booking=diagnosis_data.get("has_booking", False),
                    has_talktalk=diagnosis_data.get("has_talktalk", False),
                    has_smartcall=diagnosis_data.get("has_smartcall", False),
                    has_coupon=diagnosis_data.get("has_coupon", False),
                    has_news=diagnosis_data.get("has_news", False),
                    menu_count=diagnosis_data.get("menu_count", 0),
                    has_menu_description=diagnosis_data.get("has_menu_description", False),
                    receipt_review_count=diagnosis_data.get("receipt_review_count", 0),
                    visitor_review_count=diagnosis_data.get("visitor_review_count", 0),
                    has_owner_reply=diagnosis_data.get("has_owner_reply", False),
                    has_instagram=diagnosis_data.get("has_instagram", False),
                    has_kakao=diagnosis_data.get("has_kakao", False),
                    naver_place_rank=diagnosis_data.get("naver_place_rank", 0),
                    related_keywords=diagnosis_data.get("related_keywords", []),
                    # 점수
                    photo_score=diagnosis_data["photo_score"],
                    review_score=diagnosis_data["review_score"],
                    blog_score=diagnosis_data["blog_score"],
                    keyword_score=diagnosis_data["keyword_score"],
                    info_score=diagnosis_data["info_score"],
                    convenience_score=diagnosis_data.get("convenience_score", 0.0),
                    engagement_score=diagnosis_data.get("engagement_score", 0.0),
                    total_score=diagnosis_data["total_score"],
                    grade=diagnosis_data["grade"],
                    improvement_points=diagnosis_data["improvement_points"],
                    ppt_filename=ppt_filename,
                    is_manual=False,
                    # 신규 필드
                    industry_type=diagnosis_data.get("industry_type", ""),
                    priority_tag=priority_tag,
                    competitor_avg_review=competitor_avg_review,
                    competitor_avg_photo=competitor_avg_photo,
                    competitor_avg_blog=competitor_avg_blog,
                    estimated_lost_customers=messages.get("estimated_lost_customers", 0),
                    messages=messages,
                    # AI 분석 결과
                    review_texts=diagnosis_data.get("review_texts", []),
                    photo_urls=diagnosis_data.get("photo_urls", []),
                    bookmark_count=diagnosis_data.get("bookmark_count", 0),
                    review_sentiment_score=diagnosis_data.get("review_sentiment_score", 50.0),
                    review_negative_ratio=diagnosis_data.get("review_negative_ratio", 0.0),
                    review_main_complaints=diagnosis_data.get("review_main_complaints", []),
                    photo_quality_score=diagnosis_data.get("photo_quality_score", 0.0),
                    photo_quality_issues=diagnosis_data.get("photo_quality_issues", []),
                    ai_first_message=diagnosis_data.get("ai_first_message"),
                )
                db.add(history)
                await db.commit()
                await db.refresh(history)

                # 5. done: 완료
                job.status = "done"
                job.progress = 100
                job.result_id = history.id
                await db.commit()

            except Exception as e:
                # 실패 처리
                job = await db.get(CrawlJob, job_id)
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    await db.commit()


@router.post("/start", response_model=CrawlStartResponse)
async def start_crawl(
    request: Request,
    body: CrawlStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    크롤링 시작 (백그라운드 실행)

    1. CrawlJob 생성
    2. 백그라운드 태스크로 크롤링 실행
    3. job_id 반환
    """
    try:
        browser = await get_browser(request.app)
        if not browser:
            raise HTTPException(status_code=503, detail="브라우저가 초기화되지 않았습니다")

        # CrawlJob 생성
        job_id = str(uuid.uuid4())
        job = CrawlJob(
            id=job_id,
            status="pending",
            progress=0,
        )
        db.add(job)
        await db.commit()

        # 백그라운드 태스크 등록
        background_tasks.add_task(
            run_crawl_job,
            job_id=job_id,
            place_id=body.place_id,
            business_name=body.business_name,
            address=body.address,
            category=body.category,
            keywords=body.keywords or [],
            browser=browser,
        )

        return CrawlStartResponse(
            success=True,
            job_id=job_id,
            message="크롤링이 시작되었습니다. job_id로 상태를 확인하세요."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"크롤링 시작 실패: {str(e)}")


@router.get("/status/{job_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    크롤링 작업 상태 조회

    상태 종류:
    - pending: 대기 중
    - searching: 검색 중
    - crawling: 크롤링 중
    - analyzing: 분석 중
    - generating: PPT 생성 중
    - done: 완료
    - failed: 실패
    """
    try:
        job = await db.get(CrawlJob, job_id)

        if not job:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

        return CrawlStatusResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            result_id=job.result_id,
            error_message=job.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")
