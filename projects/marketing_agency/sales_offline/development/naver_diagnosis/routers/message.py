"""
영업 메시지 라우터
GET  /message/{history_id}            — 메시지 조회 (캐시 우선)
POST /message/regenerate/{history_id} — 강제 재생성
PATCH /api/businesses/{history_id}/priority — 우선순위 수동 변경
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from database import get_db
from models import DiagnosisHistory
from services.message_generator import generate_all_messages
from services.scorer import DiagnosisScorer

router = APIRouter(tags=["message"])


class PriorityUpdateRequest(BaseModel):
    priority: str  # "1순위" | "2순위" | "패스"


def _build_diagnosis_dict(history: DiagnosisHistory) -> dict:
    """DiagnosisHistory ORM → 메시지 생성용 딕셔너리 변환."""
    out = {
        "business_name": history.business_name,
        "address": history.address or "",
        "category": history.category or "",
        "photo_count": history.photo_count,
        "review_count": (history.visitor_review_count or 0) + (history.receipt_review_count or 0),
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
        # 경쟁사 데이터 (신규 필드, 없으면 0)
        "competitor_avg_review": getattr(history, "competitor_avg_review", 0) or 0,
        "competitor_avg_photo": getattr(history, "competitor_avg_photo", 0) or 0,
        "competitor_avg_blog": getattr(history, "competitor_avg_blog", 0) or 0,
        "news_last_days": 0,  # 크롤러에서 수집 시 채워짐
        "bookmark_count": 0,
    }
    # estimated_lost_customers: DB 값이 0이면 재계산 (배치 처리 시 0으로 저장된 레코드 보정)
    stored_lost = getattr(history, "estimated_lost_customers", 0) or 0
    if stored_lost == 0:
        competitor_avg_review = getattr(history, "competitor_avg_review", 0) or 0
        review_count = (history.visitor_review_count or 0) + (history.receipt_review_count or 0)
        stored_lost = DiagnosisScorer.calculate_estimated_lost_customers(
            rank=history.naver_place_rank or 0,
            keywords=history.keywords or [],
            competitor_avg_review=competitor_avg_review,
            review_count=review_count,
        )
    out["estimated_lost_customers"] = stored_lost
    return out


@router.get("/message/{history_id}")
async def get_messages(
    history_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    영업 메시지 조회.
    DB에 캐시된 메시지가 있으면 반환, 없으면 즉시 생성.
    """
    try:
        history = await db.get(DiagnosisHistory, history_id)
        if not history:
            raise HTTPException(status_code=404, detail="진단 이력을 찾을 수 없습니다.")

        # 캐시된 메시지 있으면 반환
        cached = getattr(history, "messages", None)
        if cached and isinstance(cached, dict) and cached.get("first"):
            return {
                "success": True,
                "history_id": history_id,
                "messages": cached,
                "from_cache": True,
            }

        # 없으면 생성 후 저장
        data = _build_diagnosis_dict(history)
        messages = generate_all_messages(data)

        # messages 컬럼에 저장
        try:
            await db.execute(
                update(DiagnosisHistory)
                .where(DiagnosisHistory.id == history_id)
                .values(messages=messages)
            )
            await db.commit()
        except Exception as e:
            print(f"[Message] 캐시 저장 오류 (무시): {e}")

        return {
            "success": True,
            "history_id": history_id,
            "messages": messages,
            "from_cache": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 생성 실패: {str(e)}")


@router.post("/message/regenerate/{history_id}")
async def regenerate_messages(
    history_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    영업 메시지 강제 재생성 (캐시 무시).
    """
    try:
        history = await db.get(DiagnosisHistory, history_id)
        if not history:
            raise HTTPException(status_code=404, detail="진단 이력을 찾을 수 없습니다.")

        data = _build_diagnosis_dict(history)
        messages = generate_all_messages(data)

        try:
            await db.execute(
                update(DiagnosisHistory)
                .where(DiagnosisHistory.id == history_id)
                .values(messages=messages)
            )
            await db.commit()
        except Exception as e:
            print(f"[Message] 재생성 저장 오류: {e}")

        return {
            "success": True,
            "history_id": history_id,
            "messages": messages,
            "from_cache": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메시지 재생성 실패: {str(e)}")


@router.patch("/api/businesses/{history_id}/priority")
async def update_priority(
    history_id: int,
    body: PriorityUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    영업 우선순위 수동 변경.
    priority: "1순위" | "2순위" | "패스"
    """
    valid_priorities = {"1순위", "2순위", "패스"}
    if body.priority not in valid_priorities:
        raise HTTPException(
            status_code=422,
            detail=f"유효하지 않은 우선순위입니다. 허용값: {valid_priorities}",
        )

    try:
        history = await db.get(DiagnosisHistory, history_id)
        if not history:
            raise HTTPException(status_code=404, detail="진단 이력을 찾을 수 없습니다.")

        await db.execute(
            update(DiagnosisHistory)
            .where(DiagnosisHistory.id == history_id)
            .values(priority_tag=body.priority)
        )
        await db.commit()

        return {
            "success": True,
            "history_id": history_id,
            "priority_tag": body.priority,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"우선순위 변경 실패: {str(e)}")
