"""
벤치마크 프리미엄 DB 구축 서비스 (Phase 3)
- 쿼리 생성 (업종 × 지역)
- 네이버 API로 Top N 업체 추출
- DB 저장
"""
import asyncio
import time
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import sys
import os
import httpx
import re
from urllib.parse import quote

# 부모 디렉토리를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from models import BenchmarkPremium
from dotenv import load_dotenv

# core/company/.env 중앙 로드
for _p in Path(__file__).resolve().parents:
    if (_p / "company" / ".env").exists():
        load_dotenv(_p / "company" / ".env")
        break
else:
    load_dotenv()


class BenchmarkBuilder:
    """벤치마크 프리미엄 DB 빌더 (API 기반)"""

    def __init__(self, db_url: str = "sqlite+aiosqlite:///./naver_diagnosis.db"):
        self.db_url = db_url
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.query_delay = 3  # 쿼리 간 딜레이 (초)
        self.total_cost = 0.0

    # 업종 × 지역 매트릭스
    CATEGORIES = [
        "미용실", "네일", "피부관리", "고깃집", "이태리안",
        "카페", "베이커리", "필라테스", "피부과", "성형외과"
    ]

    REGIONS = [
        "강남역", "홍대입구", "성수동", "이태원", "압구정",
        "한남동", "가로수길"
    ]

    async def get_existing_place_ids(self) -> set:
        """이미 저장된 place_id 가져오기"""
        async with self.async_session() as session:
            result = await session.execute(
                select(BenchmarkPremium.place_id)
            )
            return set(row[0] for row in result.fetchall())

    async def generate_queries(self) -> List[Dict[str, str]]:
        """쿼리 생성 (업종 × 지역)"""
        queries = []
        for category in self.CATEGORIES:
            for region in self.REGIONS:
                queries.append({
                    "query": f"{region} {category}",
                    "category": category,
                    "region": region
                })
        return queries

    async def search_naver_place_html(self, query: str, display: int = 10) -> List[Dict]:
        """
        네이버 플레이스 모바일 검색 HTML을 파싱해서 place_id 추출
        (Playwright 없이 httpx + 정규식으로)

        Args:
            query: 검색 쿼리
            display: 반환 개수 (최대 20)

        Returns:
            [{"place_name": "", "place_id": "", "address": "", "place_url": ""}, ...]
        """
        results = []
        try:
            from urllib.parse import quote
            encoded_query = quote(query)
            url = f"https://m.search.naver.com/search.naver?query={encoded_query}&where=m_local"

            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
            }

            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
                if resp.status_code == 200:
                    html = resp.text

                    # place_id 추출 (정규식: m.place.naver.com/place/{id})
                    pattern = r'm\.place\.naver\.com/(?:place|restaurant|hairshop|cafe)/(\d{6,})'
                    matches = re.findall(pattern, html)

                    # 중복 제거하면서 순서 유지
                    seen = set()
                    for place_id in matches[:display]:
                        if place_id not in seen:
                            seen.add(place_id)
                            # place_name은 별도로 추출 (간단히 "Business #N" 사용)
                            results.append({
                                "place_name": f"Place {len(results)+1}",
                                "place_id": place_id,
                                "address": "",
                                "place_url": f"https://m.place.naver.com/place/{place_id}/home",
                            })

                    if results:
                        print(f"    검색: {len(results)}개 place_id 추출")
                    return results
                else:
                    print(f"    HTTP 오류 ({resp.status_code})")
                    return []

        except Exception as e:
            print(f"    검색 실패: {str(e)[:60]}")
            return []

    async def crawl_and_save(self, queries: List[Dict[str, str]], display: int = 10, test_mode: bool = False):
        """
        쿼리별로 업체 정보 수집 + DB 저장

        Args:
            queries: 쿼리 리스트
            display: 각 쿼리당 검색 결과 개수
            test_mode: 테스트 모드 (1개 쿼리만)
        """
        existing_ids = await self.get_existing_place_ids()
        print(f"[INIT] 기존 place_id {len(existing_ids)}개 스킵")

        if test_mode:
            queries = queries[:1]
            print(f"[TEST MODE] 1개 쿼리만 실행")

        total_places = 0
        failed_queries = []
        saved_places = 0

        for idx, q in enumerate(queries):
            query_str = q["query"]
            category = q["category"]
            region = q["region"]

            print(f"\n[{idx+1}/{len(queries)}] {query_str} 검색 중...")

            try:
                # 네이버 플레이스 검색 (HTML 파싱)
                results = await self.search_naver_place_html(query_str, display=display)
                print(f"  → {len(results)}개 업체 발견")

                for item in results:
                    place_id = item.get("place_id")

                    if not place_id:
                        continue

                    if place_id in existing_ids:
                        print(f"    [{total_places+1}] {place_id} (skip, 기존 데이터)")
                        continue

                    try:
                        # DB에 저장 (네이버 API 데이터만)
                        await self._save_to_db(item, category, region)
                        total_places += 1
                        saved_places += 1
                        existing_ids.add(place_id)

                    except Exception as e:
                        print(f"    [FAIL] {place_id} 저장 오류: {str(e)[:60]}")
                        continue

            except Exception as e:
                print(f"  [FAIL] 쿼리 오류: {str(e)[:80]}")
                failed_queries.append(query_str)

            # 쿼리 간 딜레이 (네이버 봇 차단 방지)
            await asyncio.sleep(self.query_delay)

        print(f"\n[COMPLETE]")
        print(f"  총 발견: {total_places}개 업체")
        print(f"  새로 저장: {saved_places}개")
        print(f"  실패 쿼리: {len(failed_queries)}개 → {failed_queries[:5]}")
        return {
            "total_places": total_places,
            "saved_places": saved_places,
            "failed_queries": failed_queries
        }

    async def _save_to_db(self, item: dict, category: str, region: str):
        """네이버 API 데이터를 DB에 저장"""
        async with self.async_session() as session:
            place_id = item.get("place_id")

            # 중복 확인
            existing = await session.execute(
                select(BenchmarkPremium).where(BenchmarkPremium.place_id == place_id)
            )
            if existing.scalars().first():
                return

            # 기본 정보만 저장 (상세 크롤링은 별도 단계)
            benchmark = BenchmarkPremium(
                category=category,
                region=region,
                place_name=item.get("place_name", ""),
                place_id=place_id,
                place_url=item.get("place_url", ""),
                address=item.get("address", ""),
                naver_place_rank=0,  # 순위는 추후 추가
                crawled_at=datetime.utcnow(),
            )

            session.add(benchmark)
            await session.commit()

    async def close(self):
        """DB 연결 종료"""
        await self.engine.dispose()


async def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="벤치마크 프리미엄 DB 구축 (API 기반)")
    parser.add_argument("--test", action="store_true", help="테스트 모드 (1개 쿼리)")
    parser.add_argument("--full", action="store_true", help="전체 실행")
    parser.add_argument("--display", type=int, default=10, help="각 쿼리당 검색 결과 개수")
    args = parser.parse_args()

    if not args.test and not args.full:
        print("사용법: python benchmark_builder.py --test 또는 --full")
        return

    builder = BenchmarkBuilder()

    try:
        queries = await builder.generate_queries()
        print(f"[INIT] {len(queries)}개 쿼리 생성 (70개 = 10개 업종 × 7개 지역)")

        result = await builder.crawl_and_save(
            queries,
            display=args.display,
            test_mode=args.test
        )

        print(f"\n[RESULT]")
        print(f"  발견: {result['total_places']}개")
        print(f"  저장: {result['saved_places']}개")
        print(f"  실패: {len(result['failed_queries'])}개")

    finally:
        await builder.close()


if __name__ == "__main__":
    asyncio.run(main())
