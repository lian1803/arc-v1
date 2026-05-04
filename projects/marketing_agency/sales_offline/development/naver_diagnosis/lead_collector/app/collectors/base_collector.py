"""공통 수집기 인터페이스"""
import re
from abc import ABC, abstractmethod
from typing import Optional

IG_PATTERN = re.compile(
    r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]{2,30})(?:/[^"\s]*)?'
)
PHONE_PATTERN = re.compile(r'0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}')
IG_EXCLUDE = {
    "explore", "p", "reel", "reels", "stories", "accounts", "tv",
    "static.cdninstagram.com", "about", "help", "legal", "shopsig",
}


class BaseCollector(ABC):
    """모든 수집기의 공통 인터페이스"""

    platform_name: str = "base"

    @abstractmethod
    async def collect(self, region: str, keyword: str, limit: int = 100) -> list[dict]:
        """
        수집 실행.
        반환: [{"name": str, "phone": str, "address": str, "insta_url": str,
                "naver_place_url": str, "daangn_url": str, "category": str, "source": str}]
        """
        raise NotImplementedError

    @staticmethod
    def extract_instagram(html: str) -> str:
        """HTML에서 인스타그램 계정 URL 추출 (공식 계정만)"""
        for m in IG_PATTERN.finditer(html):
            username = m.group(1).rstrip("/")
            if username.lower() not in IG_EXCLUDE and not username.startswith("_"):
                return f"https://www.instagram.com/{username}/"
        return ""

    @staticmethod
    def extract_phone(text: str) -> str:
        """텍스트에서 전화번호 추출 (첫 번째 발견)"""
        m = PHONE_PATTERN.search(text)
        return m.group(0) if m else ""

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """전화번호 정규화: 숫자와 하이픈만"""
        digits = re.sub(r"[^\d]", "", phone)
        if len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        return phone

    @staticmethod
    def is_franchise(name: str) -> bool:
        from app.config import FRANCHISE_EXCLUDE
        return any(kw in name for kw in FRANCHISE_EXCLUDE)

    @staticmethod
    def is_in_region(address: str, region: str) -> bool:
        """주소가 region 시/군 안에 있는지 검증.
        '양주' → '양주시' 또는 '양주군' 매칭. '남양주시' 는 한글 char 앞 lookbehind 로 제외.
        """
        if not address or not region:
            return False
        pattern = rf'(?<![가-힣]){re.escape(region)}(?:시|군)'
        return bool(re.search(pattern, address))
