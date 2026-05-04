"""
검색 라우터
POST /search: 업체명으로 네이버 검색
"""
from typing import List
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    """검색 요청"""
    query: str = Field(..., min_length=1, max_length=100, description="검색할 업체명")


class SearchResult(BaseModel):
    """검색 결과 항목"""
    place_id: str | None
    name: str
    address: str
    road_address: str
    category: str
    url: str


class SearchResponse(BaseModel):
    """검색 응답"""
    success: bool
    results: List[SearchResult]
    count: int


@router.post("", response_model=SearchResponse)
async def search_business(request: Request, body: SearchRequest):
    """
    업체명으로 네이버 플레이스 검색

    - 네이버 지역 검색 API 사용
    - 최대 5개 결과 반환
    """
    try:
        browser = request.app.state.browser
        if not browser:
            raise HTTPException(status_code=503, detail="브라우저가 초기화되지 않았습니다")

        from services.naver_place_crawler import NaverPlaceCrawler
        crawler = NaverPlaceCrawler(browser)

        results = await crawler.search_business(body.query)

        return SearchResponse(
            success=True,
            results=[SearchResult(**r) for r in results],
            count=len(results)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")
