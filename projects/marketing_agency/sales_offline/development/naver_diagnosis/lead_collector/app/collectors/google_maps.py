"""구글 검색 대체 — ddgs 라이브러리 (site: 연산자로 인스타/당근/네이버 타겟 수집)"""
import logging
import re

from ddgs import DDGS

from app.collectors.base_collector import BaseCollector, IG_PATTERN, IG_EXCLUDE

logger = logging.getLogger(__name__)

DAANGN_PATTERN = re.compile(
    r'https?://(?:www\.)?daangn\.com/(?:kr/biz/|articles/|fleamarket/)[^\s"\'<>]+'
)
NAVER_PLACE_PATTERN = re.compile(
    r'https?://(?:m\.)?(?:place\.naver\.com|map\.naver\.com/p/entry/place)/[^\s"\'<>]+'
)


class GoogleMapsCollector(BaseCollector):
    platform_name = "구글"

    async def collect(self, region: str, keyword: str, limit: int = 100) -> list[dict]:
        results: list[dict] = []
        seen_names: set[str] = set()

        # site: 연산자로 특정 플랫폼 타겟 검색
        queries = [
            f"site:instagram.com {region} {keyword}",
            f"site:daangn.com {region} {keyword}",
            f"site:place.naver.com {region} {keyword}",
            f"{region} {keyword} 업체 연락처 010",
        ]

        per_query = max(50, limit // len(queries))

        for query in queries:
            if len(results) >= limit:
                break
            try:
                ddgs_results = DDGS().text(
                    query,
                    region="kr-ko",
                    max_results=per_query,
                )
                for r in ddgs_results:
                    rec = self._parse_result(r, keyword, region)
                    if rec and rec["name"] not in seen_names:
                        seen_names.add(rec["name"])
                        results.append(rec)
            except Exception as e:
                logger.error("[구글] ddgs 오류 (%s): %s", query, e)

        logger.info("[구글] %s %s → %d건", region, keyword, len(results))
        return results[:limit]

    def _parse_result(self, result: dict, keyword: str, region: str) -> dict | None:
        title = result.get("title", "")
        href = result.get("href", "")
        body = result.get("body", "")

        combined = f"{title} {body} {href}"

        name = re.split(r'[-–—|·]', title)[0].strip()
        if len(name) > 30:
            name = name[:30]
        if len(name) < 2 or self.is_franchise(name):
            return None

        phone_raw = self.extract_phone(combined)
        phone = self.normalize_phone(phone_raw) if phone_raw else ""

        # 인스타그램
        insta_url = ""
        if "instagram.com/" in href:
            m = IG_PATTERN.search(href)
            if m:
                username = m.group(1).rstrip("/")
                if username.lower() not in IG_EXCLUDE and not username.startswith("_"):
                    insta_url = f"https://www.instagram.com/{username}/"
        if not insta_url:
            for m in IG_PATTERN.finditer(combined):
                username = m.group(1).rstrip("/")
                if username.lower() not in IG_EXCLUDE and not username.startswith("_"):
                    insta_url = f"https://www.instagram.com/{username}/"
                    break

        # 당근마켓
        daangn_url = ""
        if "daangn.com" in href:
            daangn_url = href
        else:
            m = DAANGN_PATTERN.search(combined)
            if m:
                daangn_url = m.group(0)

        # 네이버플레이스
        naver_place_url = ""
        if "place.naver.com" in href:
            naver_place_url = href
        else:
            m = NAVER_PLACE_PATTERN.search(combined)
            if m:
                naver_place_url = m.group(0)

        if not phone and not insta_url and not daangn_url and not naver_place_url:
            return None

        return {
            "name": name,
            "phone": phone,
            "phone_status": "확인" if phone else "번호미확인",
            "insta_url": insta_url,
            "naver_place_url": naver_place_url,
            "daangn_url": daangn_url,
            "raw_address": region,
            "category": keyword,
            "source": self.platform_name,
            "sources": self.platform_name,
            "verify_status": "미확인",
        }
