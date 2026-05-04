"""
처방전 생성기 - 진단 결과 → 이달의 처방 패키지 + 우선순위 작업 목록

처방 철학:
- 고객에게 "스펙 표"를 보여주지 않는다
- 실제 벤치마크 숫자로 격차를 보여준다 ("평균 370건 vs 현재 5건")
- 이달 처방 3가지 우선순위를 명시한다 (패키지 내에서 가장 먼저 할 것)
"""
import math
from typing import Dict, List, Any, Optional

from config.industry_weights import (
    PACKAGES,
    INDUSTRY_AVG_PRICE,
    recommend_package,
    get_avg_price,
    get_competitor_fallback,
    detect_industry,
)

ITEM_LABEL: Dict[str, str] = {
    "photo": "대표사진",
    "review": "리뷰 관리",
    "blog": "블로그 노출",
    "info": "기본정보",
    "keyword": "키워드 세팅",
    "convenience": "예약·알림·이벤트",
    "engagement": "고객 소통",
}

ITEM_ACTION: Dict[str, str] = {
    "photo": "전문 사진 촬영",
    "review": "영수증 리뷰 집중 유도",
    "blog": "블로그 체험단 우선 집행",
    "info": "기본정보 세팅 완성",
    "keyword": "지역 핵심 키워드 등록",
    "convenience": "쿠폰·새소식 즉시 활성화",
    "engagement": "인스타·카카오채널 연동",
}

# Phase 5 실증 기반 업종별 우선순위 (d값이 높은 순서 = 상위/하위 잘 구분하는 순서)
INDUSTRY_PRIORITY_ORDER: Dict[str, List[str]] = {
    "미용실":  ["blog", "photo", "review", "info", "keyword", "convenience", "engagement"],
    "피부관리": ["review", "blog", "photo", "info", "keyword", "convenience", "engagement"],
    "카페":    ["review", "blog", "photo", "info", "keyword", "convenience", "engagement"],
    "식당":    ["review", "blog", "photo", "info", "keyword", "convenience", "engagement"],
    "네일":    ["blog", "photo", "review", "info", "keyword", "convenience", "engagement"],
    "default": ["review", "blog", "photo", "info", "keyword", "convenience", "engagement"],
}

# 패키지별 커버 가능 항목
PACKAGE_COVERS: Dict[str, set] = {
    "시선": {"photo", "keyword", "info", "convenience", "review"},
    "집중": {"photo", "keyword", "info", "convenience", "review", "blog", "engagement"},
    "주목": {"photo", "keyword", "info", "convenience", "review", "blog", "engagement"},
}

PACKAGE_INCLUDES: Dict[str, List[str]] = {
    "시선": [
        "N플레이스 기본정보 최적화",
        "대표사진·키워드 세팅",
        "소식/알림/이벤트 설정",
        "영수증 리뷰 월 3건 유도",
        "블로그 체험단 월 2팀",
        "월간 성과 리포트",
    ],
    "집중": [
        "시선 패키지 전체",
        "전문 사진·영상 촬영 1회",
        "블로그 체험단 월 4건",
        "인스타그램 피드 월 6건",
        "당근마켓 게시물 1건",
        "플레이스 방문·저장 월 1,500건",
    ],
    "주목": [
        "집중 패키지 전체",
        "블로그 기자단·체험단(고급) 월 12건",
        "인스타그램 피드+릴스 월 12건",
        "당근마켓 게시물 월 2건",
        "맘카페 침투 월 1건",
        "카카오·당근 채널 개설·단골 관리",
        "플레이스 방문·저장 월 2,000건",
        "전담 매니저 배정",
    ],
}


def _fmt(n: int) -> str:
    return f"{n:,}"


class PrescriptionGenerator:
    """진단 데이터 → 처방전 생성"""

    def generate(
        self,
        grade: str,
        score: float,
        weak_items: List[Dict],
        business_name: str,
        category: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        처방전 전체 생성.

        Args:
            grade: A/B/C/D
            score: 0~100 종합 점수
            weak_items: [{"category": "photo", "score": 30.0, ...}, ...]
            business_name: 업체명
            category: 업종
            data: 원시 크롤링 데이터 (실제 수치 포함)

        Returns:
            package / package_price / anchor_price / grade / score /
            priorities / rationale / breakeven / includes / prescription_text
        """
        data = data or {}
        weak_cat_list = [w.get("category") for w in weak_items if w.get("category")]
        package_name = recommend_package(grade, weak_cat_list)
        pkg_info = PACKAGES[package_name]

        # 벤치마크 기준값 — benchmark_scorer 또는 COMPETITOR_FALLBACK
        bench = self._get_benchmark(category, data)

        priorities = self._get_priorities(weak_items, package_name, category, data, bench)
        rationale = self._build_rationale(grade, score, package_name, weak_items, business_name, category, data, bench)
        breakeven = self._calc_breakeven(pkg_info["price"], category)
        prescription_text = self._build_prescription_text(business_name, package_name, priorities)

        return {
            "package": package_name,
            "package_price": pkg_info["price"],
            "anchor_price": pkg_info["anchor_price"],
            "grade": grade,
            "score": round(score, 1),
            "priorities": priorities,
            "rationale": rationale,
            "breakeven": breakeven,
            "includes": PACKAGE_INCLUDES[package_name],
            "prescription_text": prescription_text,
        }

    def _get_benchmark(self, category: str, data: Dict) -> Dict[str, Any]:
        """벤치마크 기준값 반환 — data에 있으면 우선 사용, 없으면 COMPETITOR_FALLBACK."""
        fb = get_competitor_fallback(category)
        return {
            "avg_review": data.get("competitor_avg_review") or fb.get("avg_review", 0),
            "avg_photo":  data.get("competitor_avg_photo")  or fb.get("avg_photo", 0),
            "avg_blog":   fb.get("avg_blog", 0),
            "top_review": fb.get("top_review", 0),
        }

    def _build_why(self, cat: str, data: Dict, bench: Dict) -> str:
        """항목별 실데이터 기반 처방 이유 문장."""
        industry_label = {
            "미용실": "서울 상위 미용실",
            "피부관리": "서울 상위 피부관리샵",
            "카페": "서울 상위 카페",
            "식당": "서울 상위 식당",
            "네일": "서울 상위 네일샵",
        }
        ind = detect_industry(data.get("category", ""))
        label = industry_label.get(ind, "상위 경쟁사")

        if cat == "blog":
            avg = bench["avg_blog"]
            cur = data.get("blog_review_count", 0) or 0
            gap = max(0, avg - cur)
            if avg > 0:
                return f"현재 블로그 리뷰 {_fmt(cur)}건 — {label} 평균 {_fmt(avg)}건, {_fmt(gap)}건 차이"
            return "블로그 리뷰는 네이버 검색 노출의 핵심입니다"

        if cat == "review":
            avg = bench["avg_review"]
            cur = (data.get("visitor_review_count", 0) or 0) + (data.get("receipt_review_count", 0) or 0)
            gap = max(0, avg - cur)
            if avg > 0:
                return f"현재 리뷰 {_fmt(cur)}건 — {label} 평균 {_fmt(avg)}건, {_fmt(gap)}건 차이"
            return "리뷰가 없으면 검색 순위에서 밀립니다"

        if cat == "photo":
            avg = bench["avg_photo"]
            cur = data.get("photo_count", 0) or 0
            gap = max(0, avg - cur)
            if avg > 0:
                return f"현재 사진 {_fmt(cur)}장 — {label} 평균 {_fmt(avg)}장, {_fmt(gap)}장 차이"
            return "대표사진이 부족하면 클릭률이 40% 떨어집니다"

        if cat == "info":
            return "소개글·영업시간·메뉴 미입력은 신뢰도를 낮춥니다"
        if cat == "keyword":
            return "키워드가 없으면 검색이 되지 않습니다"
        if cat == "convenience":
            return "쿠폰·새소식 미설정은 플레이스 활성화 지수에 영향을 줍니다"
        if cat == "engagement":
            return "외부 채널 없이는 신규 유입 경로가 없습니다"
        return ""

    def _get_priorities(
        self,
        weak_items: List[Dict],
        package_name: str,
        category: str,
        data: Dict,
        bench: Dict,
    ) -> List[Dict]:
        """
        Phase 5 실증 순서 + 실데이터 gap으로 우선순위 처방 3개 생성.
        """
        ind = detect_industry(category)
        priority_order = INDUSTRY_PRIORITY_ORDER.get(ind, INDUSTRY_PRIORITY_ORDER["default"])
        pkg_covered = PACKAGE_COVERS.get(package_name, set())

        # weak_items을 카테고리 키로 인덱싱
        weak_map = {}
        for w in weak_items:
            cat = w.get("category", "")
            if cat:
                weak_map[cat] = w

        result = []
        for cat in priority_order:
            if cat not in pkg_covered:
                continue
            if cat not in weak_map:
                continue

            item = weak_map[cat]
            cur_score = item.get("score", 0)
            why = self._build_why(cat, data, bench)

            # benchmark gap 수치
            gap_val = 0
            cur_val = 0
            bench_avg = 0
            if cat == "blog":
                cur_val = data.get("blog_review_count", 0) or 0
                bench_avg = bench["avg_blog"]
                gap_val = max(0, bench_avg - cur_val)
            elif cat == "review":
                cur_val = (data.get("visitor_review_count", 0) or 0) + (data.get("receipt_review_count", 0) or 0)
                bench_avg = bench["avg_review"]
                gap_val = max(0, bench_avg - cur_val)
            elif cat == "photo":
                cur_val = data.get("photo_count", 0) or 0
                bench_avg = bench["avg_photo"]
                gap_val = max(0, bench_avg - cur_val)

            result.append({
                "rank": len(result) + 1,
                "category": cat,
                "label": ITEM_LABEL.get(cat, cat),
                "score": round(cur_score, 1),
                "action": ITEM_ACTION.get(cat, cat),
                "why": why,
                "current_val": cur_val,
                "benchmark_avg": bench_avg,
                "gap": gap_val,
            })

            if len(result) >= 3:
                break

        return result

    def _build_rationale(
        self,
        grade: str,
        score: float,
        package_name: str,
        weak_items: List[Dict],
        business_name: str,
        category: str,
        data: Dict,
        bench: Dict,
    ) -> str:
        """패키지 추천 이유 — 실데이터 숫자 포함 영업 멘트."""
        ind = detect_industry(category)
        industry_label = {
            "미용실": "서울 상위 미용실",
            "피부관리": "서울 상위 피부관리샵",
            "카페": "서울 상위 카페",
            "식당": "서울 상위 식당",
            "네일": "서울 상위 네일샵",
        }.get(ind, "상위 경쟁사")

        my_review = (data.get("visitor_review_count", 0) or 0) + (data.get("receipt_review_count", 0) or 0)
        avg_review = bench["avg_review"]

        grade_desc = {
            "D": f"네이버 플레이스 노출이 거의 없는 상태({score:.0f}점)입니다",
            "C": f"기본 세팅은 되어있지만 경쟁사에 밀리는 구간({score:.0f}점)입니다",
            "B": f"평균 이상이지만 상위 업체와의 격차가 존재합니다({score:.0f}점)",
            "A": f"이미 잘 운영 중이지만 1등 자리를 지키려면 지속 관리가 필요합니다({score:.0f}점)",
        }
        pkg_reason = {
            "시선": "우선 플레이스 기본을 잡아 검색에 뜨기 시작하면 됩니다",
            "집중": "블로그·사진·인스타까지 한 번에 올라야 빠른 성장이 됩니다",
            "주목": "전방위 채널 관리로 지역 1등 자리를 굳혀야 합니다",
        }

        base = grade_desc.get(grade, f"현재 {score:.0f}점 상태입니다")
        reason = pkg_reason.get(package_name, "")

        # 리뷰 격차 문장 추가 (avg_review 있을 때만)
        if avg_review > 0 and my_review < avg_review:
            ratio = avg_review / my_review if my_review > 0 else 99
            if ratio >= 2:
                gap_line = f" 현재 리뷰 {_fmt(my_review)}건, {industry_label} 평균 {_fmt(avg_review)}건 — {ratio:.0f}배 차이입니다."
            else:
                gap_line = f" 현재 리뷰 {_fmt(my_review)}건, {industry_label} 평균 {_fmt(avg_review)}건 차이를 좁혀야 합니다."
        else:
            gap_line = ""

        return f"{business_name}({category})은(는) {base}.{gap_line} {reason}."

    def _calc_breakeven(self, package_price: int, category: str) -> Dict[str, Any]:
        """손익분기: 패키지 비용 ÷ 평균 객단가 = 몇 명 더 오면 본전."""
        unit_price = get_avg_price(category)
        customers_needed = math.ceil(package_price / unit_price)
        daily_needed = round(customers_needed / 30, 1)
        return {
            "package_price": package_price,
            "unit_price": unit_price,
            "customers_needed": customers_needed,
            "daily_needed": daily_needed,
            "summary": f"하루 {daily_needed}명만 더 오면 본전 ({customers_needed}명/월 · 객단가 {unit_price:,}원 기준)",
        }

    def _build_prescription_text(
        self, business_name: str, package_name: str, priorities: List[Dict]
    ) -> str:
        """처방전 한 줄 요약 — PPT/메시지 삽입용."""
        if not priorities:
            return f"이달의 처방: {package_name} 패키지 - 전반적 기본 세팅부터 시작"
        top = priorities[0]
        return (
            f"이달의 처방: {package_name} 패키지 - "
            f"1순위 {top['action']} ({top['why']})"
        )
