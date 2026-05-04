"""
Gemini Vision 컨셉 분석기 (Phase 3)
- 사진 10~20장 분석
- 컬러톤, 무드, 스타일 비율, 타겟 페르소나 추출
- JSON 응답 파싱
"""
import asyncio
import json
import base64
from typing import Optional, List, Dict
from pathlib import Path
import sys
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))


class ConceptAnalyzer:
    """Gemini Vision으로 매장 컨셉 분석"""

    def __init__(self, google_api_key: str):
        self.api_key = google_api_key
        # gemini-2.0-flash-lite는 2026-03-06부로 신규 프로젝트 사용 불가 → gemini-2.5-flash로 교체
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        self.total_cost = 0.0
        self.total_calls = 0

    async def analyze_photos(self, photo_urls: List[str], max_photos: int = 20) -> Optional[Dict]:
        """
        사진들을 분석해서 컨셉 태그 추출

        Args:
            photo_urls: 사진 URL 리스트
            max_photos: 분석할 최대 사진 수

        Returns:
            {
                "color_tone": "웜|쿨|모노|비비드",
                "mood": "미니멀|빈티지|럭셔리|캐주얼|내추럴|모던",
                "style_ratio": {"인물": float, "공간": float, "디테일": float},
                "target_persona": "..."
            }
        """
        if not photo_urls:
            return None

        # 최대 사진 수 제한
        urls_to_analyze = photo_urls[:max_photos]

        try:
            return await self._call_gemini(urls_to_analyze)
        except Exception as e:
            print(f"  [FAIL] Gemini 분석 실패: {str(e)[:100]}")
            return None

    async def _call_gemini(self, photo_urls: List[str]) -> Optional[Dict]:
        """Gemini API 호출"""
        self.total_calls += 1

        prompt = """다음 매장 사진들을 분석하고 JSON 형식으로 답변해주세요. 꼭 JSON만 반환하세요:

{
  "color_tone": "웜/쿨/모노/비비드 중 선택",
  "mood": "미니멀/빈티지/럭셔리/캐주얼/내추럴/모던 중 선택",
  "style_ratio": {
    "인물": 0.0~1.0 사이 비율,
    "공간": 0.0~1.0 사이 비율,
    "디테일": 0.0~1.0 사이 비율
  },
  "target_persona": "20대 여성/30대 남성/패밀리/프리미엄/캐주얼 등"
}

사진이 여러 장이면 전체 평균/특징을 반영해서 분석하세요."""

        # 사진을 base64로 다운로드 또는 URL 직접 사용
        # 여기서는 URL 직접 사용 (Gemini API가 지원함)
        content = {
            "parts": []
        }

        # 텍스트 프롬프트
        content["parts"].append({
            "text": prompt
        })

        # 이미지 URL 추가
        for url in photo_urls:
            try:
                content["parts"].append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": await self._download_image_base64(url)
                    }
                })
            except Exception as e:
                print(f"    이미지 다운로드 실패 ({url[:50]}...): {e}")
                continue

        if len(content["parts"]) == 1:  # 텍스트만 있음
            return None

        # Gemini 2.5 Flash — JSON 스키마 강제
        response_schema = {
            "type": "object",
            "properties": {
                "color_tone": {"type": "string", "enum": ["웜", "쿨", "모노", "비비드"]},
                "mood": {"type": "string", "enum": ["미니멀", "빈티지", "럭셔리", "캐주얼", "내추럴", "모던"]},
                "style_ratio": {
                    "type": "object",
                    "properties": {
                        "인물": {"type": "number"},
                        "공간": {"type": "number"},
                        "디테일": {"type": "number"},
                    },
                    "required": ["인물", "공간", "디테일"],
                },
                "target_persona": {"type": "string"},
            },
            "required": ["color_tone", "mood", "style_ratio", "target_persona"],
        }

        payload = {
            "contents": [content],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            },
        }

        # API 호출
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    response_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    result = self._parse_json_response(response_text)
                    return result
                else:
                    print(f"    [API ERR {resp.status_code}] {resp.text[:200]}")
                    return None
        except asyncio.TimeoutError:
            print(f"    [TIMEOUT]")
            return None
        except Exception as e:
            print(f"    [ERR] {str(e)[:100]}")
            return None

    async def _download_image_base64(self, url: str) -> str:
        """이미지 URL을 base64로 변환"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return base64.b64encode(resp.content).decode('utf-8')
                else:
                    raise Exception(f"HTTP {resp.status_code}")
        except Exception as e:
            raise Exception(f"이미지 다운로드 실패: {str(e)}")

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Gemini 응답에서 JSON 추출"""
        try:
            # 문자열에서 JSON 블록 찾기
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                result = json.loads(json_str)
                # 필수 필드 확인
                if all(k in result for k in ["color_tone", "mood", "style_ratio", "target_persona"]):
                    return result
            return None
        except json.JSONDecodeError:
            return None

    async def batch_analyze(self, places_data: List[Dict]) -> List[Dict]:
        """
        여러 업체의 사진을 일괄 분석

        Args:
            places_data: [{"place_id": "...", "photo_urls": [...]}, ...]

        Returns:
            [{"place_id": "...", "concept_tags": {...} or null}, ...]
        """
        results = []
        for idx, place in enumerate(places_data):
            place_id = place.get("place_id")
            photo_urls = place.get("photo_urls", [])

            print(f"[{idx+1}/{len(places_data)}] {place_id} 분석 중...")
            concept_tags = await self.analyze_photos(photo_urls)
            results.append({
                "place_id": place_id,
                "concept_tags": concept_tags
            })

            # API 요청 제한을 위한 딜레이
            await asyncio.sleep(1)

        return results

    def get_stats(self) -> Dict:
        """API 사용 통계"""
        return {
            "total_calls": self.total_calls,
            "estimated_cost": self._estimate_cost()
        }

    def _estimate_cost(self) -> float:
        """
        예상 비용 계산 (gemini-2.0-flash-lite 기준)
        - 입력: $0.075/million tokens
        - 출력: $0.3/million tokens
        - 대략 사진 15장 분석 시 ~30KB = ~7500 tokens
        """
        # 보수적으로 사진당 10000 tokens 가정
        input_tokens_per_call = 10000  # 사진 15장 기준
        output_tokens_per_call = 500    # 응답
        input_cost_per_million = 0.075
        output_cost_per_million = 0.3

        input_cost = (self.total_calls * input_tokens_per_call) / 1_000_000 * input_cost_per_million
        output_cost = (self.total_calls * output_tokens_per_call) / 1_000_000 * output_cost_per_million

        return round(input_cost + output_cost, 4)


async def main():
    """테스트 함수"""
    import os
    from pathlib import Path as _Path
    from dotenv import load_dotenv

    for _p in _Path(__file__).resolve().parents:
        if (_p / "company" / ".env").exists():
            load_dotenv(_p / "company" / ".env")
            break
    else:
        load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("GOOGLE_API_KEY 환경변수 설정 필요")
        return

    analyzer = ConceptAnalyzer(api_key)

    # 테스트 URL (네이버 플레이스 이미지)
    test_urls = [
        "https://ldb-phinf.pstatic.net/20210101_1/image.jpg",  # 실제 URL 필요
    ]

    print("[TEST] 컨셉 분석 시작...")
    result = await analyzer.analyze_photos(test_urls[:5])

    if result:
        print("[SUCCESS]")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("[FAILED] 분석 실패")

    stats = analyzer.get_stats()
    print(f"\n[STATS]")
    print(f"  호출: {stats['total_calls']}회")
    print(f"  예상 비용: ${stats['estimated_cost']}")


if __name__ == "__main__":
    asyncio.run(main())
