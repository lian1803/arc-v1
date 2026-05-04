"""DuckDuckGo 검색 (ddgs 라이브러리) — 전화번호 + 인스타 + 당근 URL"""
import logging
import re

from ddgs import DDGS

from app.collectors.base_collector import BaseCollector, IG_PATTERN, IG_EXCLUDE

logger = logging.getLogger(__name__)

DAANGN_PATTERN = re.compile(
    r'https?://(?:www\.)?daangn\.com/(?:kr/biz/|articles/|fleamarket/)[^\s"\'<>]+'
)


class DuckDuckGoCollector(BaseCollector):
    platform_name = "덕덕고"

    async def collect(self, region: str, keyword: str, limit: int = 100) -> list[dict]:
        results: list[dict] = []
        seen_names: set[str] = set()

        queries = [
            f"{region} {keyword}",
            f"{region} {keyword} 전화번호",
            f"{region} {keyword} 010",
            f"{region} {keyword} 당근마켓",
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
                logger.error("[덕덕고] 검색 오류 (%s): %s", query, e)

        logger.info("[덕덕고] %s %s → %d건", region, keyword, len(results))
        return results[:limit]

    def _parse_result(self, result: dict, keyword: str, region: str) -> dict | None:
        title = result.get("title", "")
        href = result.get("href", "")
        body = result.get("body", "")

        combined = f"{title} {body} {href}"

        name = self._extract_name(title)
        if not name or self.is_franchise(name):
            return None

        phone_raw = self.extract_phone(combined)
        phone = self.normalize_phone(phone_raw) if phone_raw else ""

        insta_url = self._extract_ig(combined, href)
        daangn_url = self._extract_daangn(combined, href)

        if not phone and not insta_url and not daangn_url:
            return None

        return {
            "name": name,
            "phone": phone,
            "phone_status": "확인" if phone else "번호미확인",
            "insta_url": insta_url,
            "naver_place_url": "",
            "daangn_url": daangn_url,
            "raw_address": region,
            "category": keyword,
            "source": self.platform_name,
            "sources": self.platform_name,
            "verify_status": "미확인",
        }

    def _extract_name(self, title: str) -> str:
        name = re.split(r'[-–—|·]', title)[0].strip()
        if len(name) > 30:
            name = name[:30]
        return name if len(name) >= 2 else ""

    def _extract_ig(self, text: str, href: str) -> str:
        for m in IG_PATTERN.finditer(text):
            username = m.group(1).rstrip("/")
            if username.lower() not in IG_EXCLUDE and not username.startswith("_"):
                return f"https://www.instagram.com/{username}/"
        if "instagram.com/" in href:
            m = IG_PATTERN.search(href)
            if m:
                username = m.group(1).rstrip("/")
                if username.lower() not in IG_EXCLUDE:
                    return f"https://www.instagram.com/{username}/"
        return ""

    def _extract_daangn(self, text: str, href: str) -> str:
        if "daangn.com" in href:
            return href
        m = DAANGN_PATTERN.search(text)
        return m.group(0) if m else ""
