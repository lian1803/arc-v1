"""
네이버 검색광고 API - 키워드 검색량 조회
HMAC-SHA256 서명 인증 방식 사용
"""
import os
import time
import hmac
import hashlib
import base64
from typing import Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()


class NaverSearchAdAPI:
    """네이버 검색광고 API 클라이언트"""

    BASE_URL = "https://api.searchad.naver.com"

    def __init__(self):
        self.customer_id = os.getenv("NAVER_AD_CUSTOMER_ID")
        self.access_license = os.getenv("NAVER_AD_ACCESS_LICENSE")
        self.secret_key = os.getenv("NAVER_AD_SECRET_KEY")

    def _generate_signature(self, timestamp: str, method: str, path: str) -> str:
        """
        HMAC-SHA256 서명 생성

        Args:
            timestamp: Unix timestamp (밀리초)
            method: HTTP 메서드 (GET, POST 등)
            path: API 경로 (/keywordstool 등)

        Returns:
            Base64 인코딩된 서명
        """
        message = f"{timestamp}.{method}.{path}"
        secret_bytes = self.secret_key.encode("utf-8")
        message_bytes = message.encode("utf-8")

        signature = hmac.new(secret_bytes, message_bytes, hashlib.sha256).digest()
        return base64.b64encode(signature).decode("utf-8")

    def _get_headers(self, method: str, path: str) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path)

        return {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": self.access_license,
            "X-Customer": self.customer_id,
            "X-Signature": signature,
        }

    async def get_keyword_stats(self, keyword: str) -> Dict[str, Any]:
        """
        키워드 검색량 조회

        Args:
            keyword: 검색할 키워드

        Returns:
            {"monthly_search_pc": int, "monthly_search_mobile": int}
        """
        path = "/keywordstool"
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers("GET", path)

        # API는 공백 포함 키워드를 지원하지 않으므로 공백 제거해서 hint 전달
        hint_keyword = keyword.replace(" ", "")

        params = {
            "hintKeywords": hint_keyword,
            "showDetail": "1",
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=15.0
                )

                if response.status_code == 200:
                    data = response.json()
                    keyword_list = data.get("keywordList", [])

                    if keyword_list:
                        # 원본 키워드(공백 포함)와 정확히 일치하는 결과 우선
                        for item in keyword_list:
                            rel = item.get("relKeyword", "").lower()
                            if rel == keyword.lower() or rel == hint_keyword.lower():
                                return {
                                    "keyword": keyword,
                                    "monthly_search_pc": item.get("monthlyPcQcCnt", 0) or 0,
                                    "monthly_search_mobile": item.get("monthlyMobileQcCnt", 0) or 0,
                                    "competition": item.get("compIdx", ""),
                                }

                        # 일치하는 게 없으면 첫 번째 결과 반환
                        first_item = keyword_list[0]
                        return {
                            "keyword": keyword,
                            "monthly_search_pc": first_item.get("monthlyPcQcCnt", 0) or 0,
                            "monthly_search_mobile": first_item.get("monthlyMobileQcCnt", 0) or 0,
                            "competition": first_item.get("compIdx", ""),
                        }

                    return {
                        "keyword": keyword,
                        "monthly_search_pc": 0,
                        "monthly_search_mobile": 0,
                        "competition": "",
                    }

                else:
                    print(f"[NaverSearchAdAPI] API 오류 ({keyword}): {response.status_code} - {response.text}")
                    return {
                        "keyword": keyword,
                        "monthly_search_pc": 0,
                        "monthly_search_mobile": 0,
                        "competition": "",
                    }

        except Exception as e:
            print(f"[NaverSearchAdAPI] 요청 오류: {e}")
            return {
                "keyword": keyword,
                "monthly_search_pc": 0,
                "monthly_search_mobile": 0,
                "competition": "",
            }

    async def get_multiple_keyword_stats(self, keywords: list) -> list:
        """
        여러 키워드의 검색량 일괄 조회

        Args:
            keywords: 키워드 리스트

        Returns:
            검색량 데이터 리스트
        """
        results = []
        for keyword in keywords:
            stats = await self.get_keyword_stats(keyword)
            total_search = stats.get("monthly_search_pc", 0) + stats.get("monthly_search_mobile", 0)
            results.append({
                "keyword": keyword,
                "search_volume": total_search,
                "monthly_search_pc": stats.get("monthly_search_pc", 0),
                "monthly_search_mobile": stats.get("monthly_search_mobile", 0),
            })
        return results
