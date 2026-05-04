"""
수동 입력 라우터
POST /manual: 수동 데이터로 진단 + PPT 생성
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import DiagnosisHistory
from services.scorer import DiagnosisScorer
from services.ppt_generator import PPTGenerator

router = APIRouter(prefix="/manual", tags=["manual"])


class KeywordInput(BaseModel):
    """키워드 입력"""
    keyword: str
    search_volume: int = 0


class ManualInputRequest(BaseModel):
    """수동 입력 요청"""
    business_name: str = Field(..., min_length=1, max_length=200, description="업체명")
    address: Optional[str] = Field(None, max_length=300, description="주소")
    category: Optional[str] = Field(None, max_length=100, description="업종")

    # 직접 입력 데이터
    photo_count: int = Field(default=0, ge=0, description="사진 수")
    review_count: int = Field(default=0, ge=0, description="리뷰 수 (영수증+방문자)")
    blog_review_count: int = Field(default=0, ge=0, description="블로그 리뷰 수")
    has_menu: bool = Field(default=False, description="메뉴 등록 여부")
    has_hours: bool = Field(default=False, description="영업시간 등록 여부")
    has_price: bool = Field(default=False, description="가격 등록 여부")

    # 편의 기능
    has_booking: bool = Field(default=False, description="네이버 예약")
    has_talktalk: bool = Field(default=False, description="톡톡 상담")
    has_smartcall: bool = Field(default=False, description="스마트콜")
    has_coupon: bool = Field(default=False, description="쿠폰")
    has_news: bool = Field(default=False, description="새소식")

    # 콘텐츠 & 채널
    has_intro: bool = Field(default=False, description="소개글")
    has_directions: bool = Field(default=False, description="오시는 길")
    has_menu_description: bool = Field(default=False, description="메뉴 설명")
    has_owner_reply: bool = Field(default=False, description="사장님 댓글")
    has_instagram: bool = Field(default=False, description="인스타그램")
    has_kakao: bool = Field(default=False, description="카카오톡 채널")

    # 키워드 데이터 (선택)
    keywords: Optional[List[KeywordInput]] = Field(default=[], description="키워드 목록")


class ManualInputResponse(BaseModel):
    """수동 입력 응답"""
    success: bool
    history_id: int
    total_score: float
    grade: str
    ppt_filename: str
    download_url: str
    improvement_points: List[dict]


@router.post("", response_model=ManualInputResponse)
async def create_manual_diagnosis(
    body: ManualInputRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    수동 입력으로 진단 생성

    - 크롤링 없이 직접 데이터 입력
    - 점수 계산 및 PPT 자동 생성
    """
    try:
        # 키워드 데이터 변환
        keyword_data = [
            {"keyword": kw.keyword, "search_volume": kw.search_volume}
            for kw in (body.keywords or [])
        ]

        # 진단 데이터 구성
        diagnosis_data = {
            "business_name": body.business_name,
            "address": body.address,
            "category": body.category,
            "photo_count": body.photo_count,
            "review_count": body.review_count,
            "blog_review_count": body.blog_review_count,
            "has_menu": body.has_menu,
            "has_hours": body.has_hours,
            "has_price": body.has_price,
            # 편의 기능
            "has_booking": body.has_booking,
            "has_talktalk": body.has_talktalk,
            "has_smartcall": body.has_smartcall,
            "has_coupon": body.has_coupon,
            "has_news": body.has_news,
            # 콘텐츠 & 채널
            "has_intro": body.has_intro,
            "has_directions": body.has_directions,
            "has_menu_description": body.has_menu_description,
            "has_owner_reply": body.has_owner_reply,
            "has_instagram": body.has_instagram,
            "has_kakao": body.has_kakao,
            "keywords": keyword_data,
        }

        # 점수 계산
        scores = DiagnosisScorer.calculate_all(diagnosis_data)
        diagnosis_data.update(scores)

        # PPT 생성
        ppt_gen = PPTGenerator(output_dir="ppt_output")
        ppt_filename = ppt_gen.generate(diagnosis_data)

        # DiagnosisHistory 저장
        history = DiagnosisHistory(
            business_name=body.business_name,
            place_id=None,
            address=body.address,
            category=body.category,
            place_url=None,
            photo_count=body.photo_count,
            review_count=body.review_count,
            blog_review_count=body.blog_review_count,
            has_menu=body.has_menu,
            has_hours=body.has_hours,
            has_price=body.has_price,
            # 편의 기능
            has_booking=body.has_booking,
            has_talktalk=body.has_talktalk,
            has_smartcall=body.has_smartcall,
            has_coupon=body.has_coupon,
            has_news=body.has_news,
            # 콘텐츠 & 채널
            has_intro=body.has_intro,
            has_directions=body.has_directions,
            has_menu_description=body.has_menu_description,
            has_owner_reply=body.has_owner_reply,
            has_instagram=body.has_instagram,
            has_kakao=body.has_kakao,
            keywords=keyword_data,
            photo_score=scores["photo_score"],
            review_score=scores["review_score"],
            blog_score=scores["blog_score"],
            keyword_score=scores["keyword_score"],
            info_score=scores["info_score"],
            convenience_score=scores.get("convenience_score", 0.0),
            engagement_score=scores.get("engagement_score", 0.0),
            total_score=scores["total_score"],
            grade=scores["grade"],
            improvement_points=scores["improvement_points"],
            ppt_filename=ppt_filename,
            is_manual=True,
        )
        db.add(history)
        await db.commit()
        await db.refresh(history)

        return ManualInputResponse(
            success=True,
            history_id=history.id,
            total_score=history.total_score,
            grade=history.grade,
            ppt_filename=ppt_filename,
            download_url=f"/ppt/download/{ppt_filename}",
            improvement_points=history.improvement_points,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"진단 생성 실패: {str(e)}")
