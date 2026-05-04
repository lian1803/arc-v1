"""
GUI 없이 수집 실행 — CLI 모드
사용: python run_headless.py [지역] [키워드(선택)]
"""
import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    # ProactorEventLoop: subprocess(Playwright) 지원. SelectorEventLoop은 NotImplementedError
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
# 상위 naver_diagnosis/.env 에서 NAVER/KAKAO 키 로드
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(_env_path)

from app.models.database import init_db
from app.services.collection_service import CollectionService
from app.services.export_service import to_excel

REGION   = sys.argv[1] if len(sys.argv) > 1 else "양주"
KEYWORD  = sys.argv[2] if len(sys.argv) > 2 else ""
# KAKAO_REST_API_KEY 없으면 네이버만. 카카오는 Playwright fallback 으로 너무 느림.
PLATFORMS = ["네이버"]
DO_VERIFY = False  # 대량 수집 시 검증 생략 (속도 우선)


def progress(msg: str, pct: int):
    bar = ""
    if pct >= 0:
        filled = int(pct / 5)
        bar = f" [{'█'*filled}{'░'*(20-filled)}] {pct}%"
    print(f"{msg}{bar}", flush=True)


async def main():
    print(f"=== {REGION} 소상공인 수집 시작 ===")
    print(f"지역: {REGION} | 업종: {KEYWORD or '전체'} | 플랫폼: {', '.join(PLATFORMS)}")
    print()

    init_db()

    service = CollectionService(progress_callback=progress)
    session_id, businesses = await service.run(
        region=REGION,
        keyword=KEYWORD,
        platforms=PLATFORMS,
        do_verify=DO_VERIFY,
        limit=999999,
    )

    if not businesses:
        print("수집된 데이터가 없습니다.")
        return

    # 키 정규화 — collector 는 "address", exporter 는 "raw_address" 기대
    for b in businesses:
        if "address" in b and "raw_address" not in b:
            b["raw_address"] = b["address"]
        if "source" in b and "sources" not in b:
            b["sources"] = b["source"]

    # 엑셀 저장
    excel_path = to_excel(businesses)
    print()
    print(f"=== 완료 ===")
    print(f"총 {len(businesses)}건 수집")
    confirmed = sum(1 for b in businesses if b.get("verify_status") == "확인됨")
    print(f"확인됨: {confirmed}건 / 미확인: {len(businesses)-confirmed}건")
    print(f"엑셀 저장: {excel_path}")


asyncio.run(main())
