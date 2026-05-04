"""
이력 라우터
GET /history: 진단 이력 목록 조회
GET /history/{id}: 진단 상세 조회
DELETE /history/{id}: 진단 이력 삭제
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models import DiagnosisHistory

router = APIRouter(prefix="/history", tags=["history"])


class HistoryListItem(BaseModel):
    """이력 목록 항목"""
    id: int
    business_name: str
    address: Optional[str]
    category: Optional[str]
    total_score: float
    grade: str
    is_manual: bool
    ppt_filename: Optional[str]
    created_at: str


class HistoryListResponse(BaseModel):
    """이력 목록 응답"""
    success: bool
    items: List[HistoryListItem]
    total: int
    page: int
    page_size: int


class HistoryDetailResponse(BaseModel):
    """이력 상세 응답"""
    success: bool
    data: dict


class DeleteResponse(BaseModel):
    """삭제 응답"""
    success: bool
    message: str


@router.get("", response_model=HistoryListResponse)
async def get_history_list(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    page_size: int = Query(default=20, ge=1, le=100, description="페이지 크기"),
    db: AsyncSession = Depends(get_db),
):
    """
    진단 이력 목록 조회

    - 최신순 정렬
    - 페이지네이션 지원
    """
    try:
        # 전체 개수 조회
        count_query = select(DiagnosisHistory)
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # 페이지네이션 적용하여 조회
        offset = (page - 1) * page_size
        query = (
            select(DiagnosisHistory)
            .order_by(desc(DiagnosisHistory.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        histories = result.scalars().all()

        items = [
            HistoryListItem(
                id=h.id,
                business_name=h.business_name,
                address=h.address,
                category=h.category,
                total_score=h.total_score,
                grade=h.grade,
                is_manual=h.is_manual,
                ppt_filename=h.ppt_filename,
                created_at=h.created_at.isoformat() if h.created_at else "",
            )
            for h in histories
        ]

        return HistoryListResponse(
            success=True,
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이력 조회 실패: {str(e)}")


@router.get("/{history_id}", response_model=HistoryDetailResponse)
async def get_history_detail(
    history_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    진단 이력 상세 조회
    """
    try:
        history = await db.get(DiagnosisHistory, history_id)

        if not history:
            raise HTTPException(status_code=404, detail="진단 이력을 찾을 수 없습니다")

        return HistoryDetailResponse(
            success=True,
            data=history.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상세 조회 실패: {str(e)}")


@router.delete("/{history_id}", response_model=DeleteResponse)
async def delete_history(
    history_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    진단 이력 삭제
    """
    try:
        history = await db.get(DiagnosisHistory, history_id)

        if not history:
            raise HTTPException(status_code=404, detail="진단 이력을 찾을 수 없습니다")

        await db.delete(history)
        await db.commit()

        return DeleteResponse(
            success=True,
            message=f"진단 이력 {history_id}가 삭제되었습니다"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")
