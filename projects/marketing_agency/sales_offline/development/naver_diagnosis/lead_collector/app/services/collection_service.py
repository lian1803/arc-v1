"""수집 오케스트레이터 — 플랫폼별 수집 → 필터 → 중복제거 → 검증 → DB 저장"""
import asyncio
import random
import sys
from datetime import datetime
from typing import Callable, Optional

from app.config import DEFAULT_CATEGORIES, MAX_PER_SESSION
from app.models.database import SessionLocal
from app.models.business import Business
from app.services.history_service import create_session, complete_session, fail_session


class CollectionService:
    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        progress_callback(msg: str, pct: int) — GUI에 진행상황 전달
        """
        self.progress_cb = progress_callback or (lambda msg, pct: None)
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def _emit(self, msg: str, pct: int = -1):
        self.progress_cb(msg, pct)

    async def run(
        self,
        region: str,
        keyword: str,
        platforms: list[str],
        do_verify: bool = True,
        limit: int = MAX_PER_SESSION,
    ) -> tuple[int, list[dict]]:
        """
        실행 후 (session_id, businesses_dict_list) 반환
        """
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        db = SessionLocal()
        session_id = None
        try:
            # DB 세션 생성
            hist = create_session(db, region, keyword, ",".join(platforms))
            session_id = hist.id

            all_records: list[dict] = []

            # ── 1. 플랫폼별 수집 ────────────────────────
            total_platforms = len(platforms)
            for i, platform in enumerate(platforms):
                if self._stop_requested:
                    break

                pct_start = int(i / total_platforms * 50)
                self._emit(f"[{platform}] 수집 시작...", pct_start)

                try:
                    records = await self._collect_platform(platform, region, keyword, limit)
                    all_records.extend(records)
                    self._emit(f"[{platform}] {len(records)}건 수집 완료", pct_start + int(50 / total_platforms))
                except Exception as e:
                    self._emit(f"[{platform}] 오류: {e} — 건너뜀", pct_start)

            if self._stop_requested:
                fail_session(db, session_id, "사용자 중단")
                return session_id, []

            self._emit(f"총 {len(all_records)}건 수집. 필터링 중...", 52)

            # ── 2. 010 필터링 ───────────────────────────
            from app.validators.phone_filter import filter_phones
            passed, filtered = filter_phones(all_records)
            self._emit(f"010 번호 필터 완료 — 통과: {len(passed)}건, 번호미확인: {len(filtered)}건", 56)
            all_records = passed + filtered  # 번호미확인도 보존

            # ── 3. 중복 제거 ────────────────────────────
            from app.validators.deduplicator import deduplicate
            all_records = deduplicate(all_records)
            self._emit(f"중복 제거 후 {len(all_records)}건", 60)

            # 최대 건수 제한
            all_records = all_records[:limit]

            # ── 4. 네이버플레이스 검증 (선택) ────────────
            if do_verify and not self._stop_requested:
                self._emit(f"네이버플레이스 검증 시작 ({len(all_records)}건)...", 62)
                from app.validators.naver_place import validate_businesses
                all_records = await validate_businesses(
                    all_records,
                    progress_callback=lambda msg, n, total: self._emit(
                        f"검증 중: {msg} ({n}/{total})",
                        62 + int(n / max(total, 1) * 30),
                    ),
                )
                self._emit("네이버플레이스 검증 완료", 92)

            # ── 5. DB 저장 ──────────────────────────────
            self._emit("DB 저장 중...", 94)
            for rec in all_records:
                biz = Business(
                    session_id    = session_id,
                    name          = rec.get("name", ""),
                    phone         = rec.get("phone") or None,
                    phone_status  = rec.get("phone_status", "확인"),
                    insta_url     = rec.get("insta_url") or None,
                    naver_place_url = rec.get("naver_place_url") or None,
                    daangn_url    = rec.get("daangn_url") or None,
                    sources       = rec.get("sources", rec.get("source", "")),
                    category      = rec.get("category") or None,
                    raw_address   = rec.get("address") or None,
                    verify_status = rec.get("verify_status", "미확인"),
                    verified_at   = datetime.utcnow() if rec.get("verify_status") == "확인됨" else None,
                )
                db.add(biz)

            db.commit()
            complete_session(db, session_id)

            result = [rec for rec in all_records]
            self._emit(f"완료! {len(result)}건", 100)
            return session_id, result

        except Exception as e:
            if session_id:
                fail_session(db, session_id, str(e))
            raise
        finally:
            db.close()

    async def _collect_platform(self, platform: str, region: str, keyword: str, limit: int) -> list[dict]:
        cats = [keyword] if keyword else DEFAULT_CATEGORIES

        if platform == "네이버":
            from app.collectors.naver_place import NaverPlaceCollector
            collector = NaverPlaceCollector()
        elif platform == "카카오맵":
            from app.collectors.kakao_maps import KakaoMapsCollector
            collector = KakaoMapsCollector()
        elif platform in ("구글맵", "구글"):
            from app.collectors.google_maps import GoogleMapsCollector
            collector = GoogleMapsCollector()
        elif platform == "당근마켓":
            from app.collectors.daangn import DaangnCollector
            collector = DaangnCollector()
        elif platform == "인스타그램":
            from app.collectors.instagram import InstagramCollector
            collector = InstagramCollector()
        elif platform == "네이버블로그":
            from app.collectors.naver_blog import NaverBlogCollector
            collector = NaverBlogCollector()
        elif platform == "덕덕고":
            from app.collectors.duckduckgo import DuckDuckGoCollector
            collector = DuckDuckGoCollector()
        elif platform == "빙":
            from app.collectors.bing import BingCollector
            collector = BingCollector()
        else:
            return []

        results = []
        per_cat = max(10, limit // max(len(cats), 1))
        for cat in cats:
            if self._stop_requested or len(results) >= limit:
                break
            try:
                recs = await collector.collect(region, cat, limit=per_cat)
                results.extend(recs)
                await asyncio.sleep(random.uniform(0.3, 0.6))
            except Exception as e:
                self._emit(f"  [{platform}] {cat} 오류: {e}", -1)

        return results[:limit]
