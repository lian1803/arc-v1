"""
사진 품질 분석 — Gemini Vision (gemini-2.5-flash)

URL 다운로드 방식 X → Playwright 네트워크 인터셉트 바이트 직접 수신
- IQA 사전 필터: PIL로 블러/밝기 체크 → 명백히 나쁜 사진은 Gemini 호출 없이 즉시 저점 반환
- 최대 2장만 Gemini에 전송 (비용 최소화)
- 실패 시 {"quality_score": 0, "issues": [], "summary": ""} 반환
"""
import os
import re
import json
import base64
import struct
import zlib
from typing import Dict, Any, List

_model = None

# IQA 필터 임계값
_BLUR_THRESHOLD = 80     # 라플라시안 분산 < 이 값이면 블러 판정
_DARK_THRESHOLD = 60     # 평균 밝기 < 이 값이면 어두움 판정 (0~255)
_BRIGHT_THRESHOLD = 210  # 평균 밝기 > 이 값이면 과노출 판정


def _iqa_prefilter(img_bytes: bytes) -> dict:
    """
    PIL 없이 순수 표준 라이브러리로 간단한 IQA 사전 필터.
    JPEG/PNG 바이트에서 평균 밝기만 체크 (블러 감지는 numpy 필요해서 생략).

    Returns:
        {"pass": bool, "issue": str or None}
    """
    try:
        # PIL이 있으면 사용, 없으면 패스 (Gemini에게 맡김)
        try:
            from PIL import Image, ImageFilter
            import io
            import statistics

            img = Image.open(io.BytesIO(img_bytes)).convert("L")  # 그레이스케일

            # 밝기 체크
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            if avg < _DARK_THRESHOLD:
                return {"pass": False, "issue": "사진이 너무 어두움"}
            if avg > _BRIGHT_THRESHOLD:
                return {"pass": False, "issue": "사진이 과노출됨"}

            # 블러 체크 (라플라시안 필터 분산)
            edges = img.filter(ImageFilter.FIND_EDGES)
            edge_pixels = list(edges.getdata())
            mean = sum(edge_pixels) / len(edge_pixels)
            variance = sum((p - mean) ** 2 for p in edge_pixels) / len(edge_pixels)
            if variance < _BLUR_THRESHOLD:
                return {"pass": False, "issue": "사진이 흐릿함"}

            return {"pass": True, "issue": None}

        except ImportError:
            # PIL 없으면 필터 건너뜀
            return {"pass": True, "issue": None}

    except Exception:
        return {"pass": True, "issue": None}


def _get_model():
    global _model
    if _model is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("models/gemini-2.5-flash")
    return _model


def _parse_json(text: str) -> dict:
    text = re.sub(r"```json?\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    raise ValueError("JSON 없음")


async def analyze_photo_quality_from_bytes(screenshots: List[bytes]) -> Dict[str, Any]:
    """
    Playwright 스크린샷 바이트 리스트 → Gemini Vision 품질 분석.

    Args:
        screenshots: Playwright element.screenshot() 결과 바이트 리스트 (최대 2장)

    Returns:
        {"quality_score": 0~100, "issues": [...], "summary": "..."}
    """
    fallback = {"quality_score": 0, "issues": [], "summary": ""}

    if not screenshots:
        return fallback

    try:
        model = _get_model()

        # IQA 사전 필터: 명백히 품질 나쁜 사진 Gemini 전에 걸러냄 (Lian 사인 2026-04-28: 2 → 5 장)
        filtered = []
        prefilter_issues = []
        for img_bytes in screenshots[:5]:
            check = _iqa_prefilter(img_bytes)
            if check["pass"]:
                filtered.append(img_bytes)
            else:
                prefilter_issues.append(check["issue"])
                print(f"[PhotoAnalyzer] IQA 필터 탈락: {check['issue']}")

        # 모든 사진이 필터에서 탈락한 경우
        if not filtered:
            return {
                "quality_score": 20,
                "issues": prefilter_issues[:2],
                "summary": "사진 품질 기준 미달 (IQA 필터)",
            }

        parts = []
        for img_bytes in filtered:  # 필터 통과한 사진만
            b64 = base64.b64encode(img_bytes).decode()
            parts.append({"inline_data": {"mime_type": "image/png", "data": b64}})

        parts.append("""소상공인 네이버 플레이스 업체 사진입니다.
고객 유입 관점에서 마케팅 품질을 평가해주세요.

JSON만 출력:
{
  "quality_score": 0~100,
  "issues": ["문제점"] (최대 2개. 예: "조명 어두움", "흐릿함", "배경 지저분"),
  "summary": "한 줄 요약"
}""")

        response = model.generate_content(parts)
        return _parse_json(response.text)

    except Exception as e:
        print(f"[PhotoAnalyzer] Gemini 분석 오류: {e}")
        return fallback
