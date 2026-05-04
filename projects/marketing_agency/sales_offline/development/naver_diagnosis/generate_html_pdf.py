#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Template 10 (Pastel Modern) — DB 실제 데이터로 PDF 생성

사용:
  python generate_html_pdf.py               # 가장 최근 업체
  python generate_html_pdf.py 소리헤어       # 특정 업체명
결과: Desktop/{업체명}_진단리포트_{날짜}.pdf
"""

import sys
import io
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# UTF-8 콘솔 출력
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# playwright 임포트
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ playwright 설치 필요: pip install playwright")
    print("   설치 후: playwright install chromium")
    sys.exit(1)


# ============================================================================
# DB에서 실제 데이터 로드
# ============================================================================

DB_PATH = Path(__file__).parent / "diagnosis.db"

PACKAGES = [
    {
        "name": "플레이스 케어",
        "tag": "A",
        "price": "380,000",
        "daily": 380000 // 30,
        "items": ["플레이스 기본정보 최적화", "핵심 키워드 세팅", "리뷰 응대 대행", "월 성과 리포트"],
        "highlight": False,
    },
    {
        "name": "바이럴 성장",
        "tag": "B",
        "price": "560,000",
        "daily": 560000 // 30,
        "items": ["A 전체 포함", "블로그 체험단 모집·관리", "리뷰 수 증가 전략", "경쟁사 비교 분석"],
        "highlight": True,
        "badge": "★ 가장 많이 선택",
    },
    {
        "name": "광고 풀케어",
        "tag": "C",
        "price": "950,000",
        "daily": 950000 // 30,
        "items": ["B 전체 포함", "네이버 광고 직접 운영", "인스타그램 관리", "전담 매니저 배정"],
        "highlight": False,
    },
]

PACKAGE_BY_GRADE = {"A": "플레이스 케어", "B": "바이럴 성장", "C": "바이럴 성장", "D": "바이럴 성장"}


def load_seoul_anchor() -> Dict:
    """seoul_anchor.json 로드. 없으면 fallback."""
    anchor_path = Path(__file__).parent / "seoul_anchor.json"
    if anchor_path.exists():
        try:
            with open(anchor_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("categories", {})
        except Exception as e:
            print(f"⚠ seoul_anchor.json 로드 실패 ({e}), fallback 사용")
    return {}


def load_from_db(business_name: str = None) -> Dict:
    """DB에서 실제 진단 데이터 로드. business_name 없으면 최신 업체."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if business_name:
        cur.execute(
            "SELECT * FROM diagnosis_history WHERE business_name=? ORDER BY created_at DESC LIMIT 1",
            (business_name,)
        )
    else:
        cur.execute("SELECT * FROM diagnosis_history ORDER BY created_at DESC LIMIT 1")

    row = cur.fetchone()
    conn.close()

    if not row:
        print(f"❌ DB에서 '{business_name}' 데이터를 찾을 수 없음")
        sys.exit(1)

    d = dict(row)
    # JSON 필드 파싱
    for k in ["keywords", "related_keywords", "improvement_points"]:
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                d[k] = []
        else:
            d[k] = []

    # None 값 기본값 처리
    d["business_name"] = d.get("business_name") or "업체명"
    d["address"] = d.get("address") or "주소 미확인"

    # 업종 추론 (None이면 업체명으로 판단)
    if not d.get("category"):
        name = d["business_name"]
        if any(k in name for k in ["헤어", "살롱", "머리", "헤어톡"]):
            d["category"] = "미용실"
        elif any(k in name for k in ["피자", "치킨", "식당", "고기", "분식", "카페"]):
            d["category"] = "음식점"
        elif any(k in name for k in ["네일", "속눈썹", "왁싱"]):
            d["category"] = "네일/뷰티"
        else:
            d["category"] = "소상공인"
    d["naver_place_rank"] = d.get("naver_place_rank") or 0
    d["grade"] = d.get("grade") or "D"
    d["estimated_lost_customers"] = d.get("estimated_lost_customers") or 0
    d["photo_count"] = d.get("photo_count") or 0
    d["visitor_review_count"] = d.get("visitor_review_count") or 0
    d["receipt_review_count"] = d.get("receipt_review_count") or 0
    d["blog_review_count"] = d.get("blog_review_count") or 0

    # related_keywords도 keywords로 fallback
    if not d["keywords"] and d.get("related_keywords"):
        d["keywords"] = d["related_keywords"]

    return d


# ============================================================================
# 헬퍼 함수
# ============================================================================

def format_number_with_comma(num: int) -> str:
    """숫자를 쉼표 포맷으로 변환 (예: 4400 → 4,400)"""
    return f"{num:,}"


def get_avg_price_by_category(category: str) -> int:
    """업종별 평균 객단가 (한국 자영업자 평균, 추정값)."""
    cat = (category or "")
    if any(k in cat for k in ["식당", "음식", "한식", "중식", "양식", "분식", "치킨", "피자", "고기", "주점", "술집", "맥주"]):
        return 15000
    if any(k in cat for k in ["카페", "디저트", "베이커리", "주스", "커피"]):
        return 8000
    if any(k in cat for k in ["미용", "헤어", "네일", "속눈썹", "왁싱", "피부"]):
        return 35000
    if any(k in cat for k in ["학원", "교육", "과외", "학습"]):
        return 300000
    if any(k in cat for k in ["청소", "세차", "수리", "인테리어", "이사"]):
        return 80000
    if any(k in cat for k in ["반려동물", "동물병원", "애견"]):
        return 50000
    return 30000  # 기타 default


def classify_business_type(data: Dict, seoul_anchor: Dict) -> str:
    """가게 분류 (Lian 사인 2026-04-28) — PDF hook 분기 결정.

    Type A 부족 — review/photo/blog 모두 서울 평균 미만 → "격차 + 채워줌" hook
    Type B 우월하나 노출 부족 — 데이터 우월 + 순위 0 또는 6+ → "키워드/SEO 영역" hook
    Type C 완벽 — 데이터 우월 + 상위 1-5위 → "외부 채널 / 확장" hook
    """
    our_review = (data.get("visitor_review_count", 0) or 0) + (data.get("receipt_review_count", 0) or 0)
    our_photo = data.get("photo_count", 0) or 0
    our_blog = data.get("blog_review_count", 0) or 0
    rank = data.get("naver_place_rank", 0) or 0

    avg_r = seoul_anchor.get("avg_review", 1500) or 1500
    avg_p = seoul_anchor.get("avg_photo", 3000) or 3000
    avg_b = seoul_anchor.get("avg_blog", 500) or 500

    superior = sum([our_review >= avg_r, our_photo >= avg_p, our_blog >= avg_b])

    if superior >= 2 and rank > 0 and rank <= 5:
        return "C"  # 완벽
    if superior >= 2:
        return "B"  # 우월하나 노출 부족
    return "A"  # 부족


def get_type_hook(business_type: str, data: Dict, seoul_anchor: Dict, kw: str) -> Dict:
    """type 별 충격카피 / 주요문제 / 패키지 / lost 라벨 박음."""
    bn = data.get("business_name", "?")
    rank = data.get("naver_place_rank", 0) or 0
    our_review = (data.get("visitor_review_count", 0) or 0) + (data.get("receipt_review_count", 0) or 0)
    our_photo = data.get("photo_count", 0) or 0

    if business_type == "C":
        # 완벽: 외부 채널 / SNS 확장 / 신규 타깃
        return {
            "shock_copy": f"'{kw}' 검색 시 {rank}위 — 이미 상위권. 다음 성장 단계는 검색 외 채널 (블로그·인스타·외부 광고) 입니다.",
            "main_problem": "검색 외 신규 유입 채널 미흡 — 다음 성장 단계",
            "recommended_pkg": "광고 풀케어",
            "lost_label_override": f"검색 외 채널 (블로그·SNS) 미활용 → 추가 성장 여지",
            "type_label": "이미 상위권 / 외부 채널 확장 영역",
        }
    if business_type == "B":
        # 우월하나 노출 부족: 키워드 / 플레이스 등록 / SEO
        return {
            "shock_copy": f"리뷰 {our_review:,}개·사진 {our_photo:,}장 — 콘텐츠는 우수합니다. 단 '{kw}' 검색 시 {('순위권 밖' if rank == 0 else f'{rank}위')}, 좋은 콘텐츠가 검색에 안 잡히고 있습니다.",
            "main_problem": "콘텐츠 우수 / 키워드 최적화·플레이스 등록 정보·검색 의도 매칭 영역 부족",
            "recommended_pkg": "광고 풀케어",
            "lost_label_override": f"콘텐츠 풍부하나 노출 부족 → 잠재 고객이 가게를 못 찾는 상태",
            "type_label": "콘텐츠 우월 / 검색 노출 영역 부족",
        }
    # Type A (default): 부족
    return {
        "shock_copy": None,  # 기존 rank 기반 shock_copy 그대로
        "main_problem": None,  # 기존 problems 계산 그대로
        "recommended_pkg": None,  # 기존 PACKAGE_BY_GRADE 그대로
        "lost_label_override": None,
        "type_label": "데이터 부족 / 격차 보강 영역",
    }


def match_seoul_category(category: str, anchor_categories: Dict):
    """가게 category → 서울 anchor 5 카테고리 매핑."""
    cat = (category or "")
    if any(k in cat for k in ["식당", "음식", "한식", "중식", "양식", "분식", "치킨", "피자", "고기", "주점", "술집", "맥주", "뷔페"]):
        key = "식당"
    elif any(k in cat for k in ["미용", "헤어", "네일", "속눈썹", "왁싱", "피부"]):
        key = "미용실"
    elif any(k in cat for k in ["카페", "디저트", "베이커리", "주스", "커피"]):
        key = "카페"
    elif any(k in cat for k in ["학원", "교육", "과외", "학습", "교습"]):
        key = "학원"
    else:
        key = "기타"
    anchor = anchor_categories.get(key) or {}
    if not anchor or not anchor.get("avg_photo"):
        valid = [v for v in anchor_categories.values() if v and v.get("avg_photo")]
        if valid:
            n = len(valid)
            anchor = {
                "avg_photo": round(sum(v["avg_photo"] for v in valid) / n),
                "avg_review": round(sum(v["avg_review"] for v in valid) / n),
                "avg_blog": round(sum(v["avg_blog"] for v in valid) / n),
                "intro_rate": sum(v.get("intro_rate", 0) for v in valid) / n,
                "menu_rate": sum(v.get("menu_rate", 0) for v in valid) / n,
                "directions_rate": sum(v.get("directions_rate", 0) for v in valid) / n,
                "booking_rate": sum(v.get("booking_rate", 0) for v in valid) / n,
                "talktalk_rate": sum(v.get("talktalk_rate", 0) for v in valid) / n,
                "news_rate": sum(v.get("news_rate", 0) for v in valid) / n,
                "instagram_rate": sum(v.get("instagram_rate", 0) for v in valid) / n,
            }
            key = "서울 평균"
    return anchor, key


def generate_diagnosis_grid(data: Dict[str, Any], seoul_anchor: Dict = None) -> str:
    """진단 그리드 — 서울 상위권 anchor 비교 점수 (Lian §12.2 사인 2026-04-27)."""
    seoul_anchor = seoul_anchor or {}
    anchor, anchor_key = match_seoul_category(data.get("category", ""), seoul_anchor)
    fb = {"avg_photo": 3000, "avg_review": 1500, "avg_blog": 500,
          "intro_rate": 0.85, "menu_rate": 0.9, "directions_rate": 0.8,
          "booking_rate": 0.6, "talktalk_rate": 0.7, "news_rate": 0.5, "instagram_rate": 0.5}
    a = {**fb, **anchor}

    our_photo = data.get("photo_count", 0) or 0
    our_review = (data.get("visitor_review_count", 0) or 0) + (data.get("receipt_review_count", 0) or 0)
    our_blog = data.get("blog_review_count", 0) or 0

    def num_score(ours, avg):
        if avg <= 0:
            return 0, "비교 불가"
        pct = min(round(ours / avg * 100), 100)
        return pct, f"{ours:,}/{avg:,}"

    def bool_score(ours, rate):
        if ours:
            return 100, f"보유 (서울 {round(rate*100)}%)"
        gap = round(rate * 100)
        return max(100 - gap, 0), f"미보유 (서울 {gap}%)"

    items = [
        ("대표사진", *num_score(our_photo, a["avg_photo"])),
        ("방문 리뷰", *num_score(our_review, a["avg_review"])),
        ("블로그 리뷰", *num_score(our_blog, a["avg_blog"])),
        ("소개글", *bool_score(data.get("has_intro", False), a["intro_rate"])),
        ("메뉴/가격", *bool_score(data.get("has_menu", False), a["menu_rate"])),
        ("오시는길", *bool_score(data.get("has_directions", False), a["directions_rate"])),
        ("예약", *bool_score(data.get("has_booking", False), a["booking_rate"])),
        ("톡톡", *bool_score(data.get("has_talktalk", False), a["talktalk_rate"])),
        ("새소식", *bool_score(data.get("has_news", False), a["news_rate"])),
        ("인스타그램", *bool_score(data.get("has_instagram", False), a["instagram_rate"])),
    ]

    html_parts = []
    for name, score, vs in items:
        cls = "ok" if score >= 70 else ("mid" if score >= 40 else "bad")
        sc_cls = "ds-ok" if score >= 70 else ("ds-mid" if score >= 40 else "ds-bad")
        tag_cls = "dt-ok" if score >= 70 else ("dt-mid" if score >= 40 else "dt-bad")
        html_parts.append(f'''    <div class="di {cls}">
      <div class="di-s {sc_cls}">{score}</div>
      <div class="di-name">{name}</div>
      <div class="di-tag {tag_cls}" style="font-size:7.5px;">{vs}</div>
    </div>''')

    return '\n'.join(html_parts)


def generate_package_grid(recommended_package: str) -> str:
    """패키지 그리드 HTML 생성 (C→B→A 앵커링 순서). 단일 정찰가 (Lian frozen 2026-04-27)."""
    html_parts = []
    for pkg in reversed(PACKAGES):  # C → B → A 순서
        is_rec = pkg["name"] == recommended_package
        rec_class = ' rec' if is_rec else ''
        rec_hdr = 'rh' if is_rec else ''
        price_man = int(pkg["price"].replace(',', '')) // 10000
        badge_html = f'<span class="rtag">{pkg.get("badge", "추천")}</span>' if is_rec or pkg.get("badge") else ''
        items_html = ''.join([f'<div class="pi">{it}</div>' for it in pkg["items"]])
        html_parts.append(f'''  <div class="pc{rec_class}">
    <div class="ph {rec_hdr}"><div class="pn">{pkg["name"]}</div>{badge_html}</div>
    <div class="pb">
      <div class="pp">{price_man}만<span class="ppu">원/월</span></div>
      <div style="font-size:9px;color:#27ae60;font-weight:600;margin-bottom:2mm;">하루 {pkg["daily"]:,}원</div>
      <div class="ps"></div>
      {items_html}
      <div style="font-size:9px;color:#6b7a8d;margin-top:2mm;padding-top:2mm;border-top:1px dashed #e0e8f0;">최소 3개월 단위 계약</div>
    </div>
  </div>''')
    return '\n'.join(html_parts)


# ============================================================================
# 메인 함수
# ============================================================================

def generate_pdf(data: Dict[str, Any], output_dir: str = None) -> str:
    """
    샘플 데이터를 HTML 템플릿에 주입하고 PDF로 변환

    Args:
        data: 샘플 데이터 dict
        output_dir: 출력 디렉토리 (기본값: 바탕화면)

    Returns:
        생성된 PDF 파일 경로
    """

    # 바탕화면 경로
    if output_dir is None:
        desktop = Path.home() / "Desktop"
        output_dir = str(desktop)

    print(f"🔍 생성 중...")
    print(f"  업체명: {data['business_name']}")
    print(f"  등급: {data['grade']} → 추천 패키지: {PACKAGE_BY_GRADE.get(data['grade'], '바이럴 성장')}")
    print()

    # 0. 서울 상위권 anchor 로드 (Lian §12.2 사인 2026-04-27)
    seoul_categories = load_seoul_anchor()
    seoul_anchor, anchor_key = match_seoul_category(data.get("category", ""), seoul_categories)
    print(f"  서울 anchor: '{anchor_key}' (사진 {seoul_anchor.get('avg_photo','?')} / 리뷰 {seoul_anchor.get('avg_review','?')} / 블로그 {seoul_anchor.get('avg_blog','?')})")

    # 1. 템플릿 읽기
    template_path = Path(__file__).parent / "html_templates" / "template_10_pastel_modern.html"

    if not template_path.exists():
        print(f"❌ 템플릿 파일을 찾을 수 없습니다: {template_path}")
        sys.exit(1)

    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 2. 데이터 준비
    today = datetime.now().strftime("%Y년 %m월 %d일")
    rank = data["naver_place_rank"]
    lost = data["estimated_lost_customers"]

    keywords = data.get("keywords") or []
    total_search = sum(k.get("search_volume", 0) for k in keywords)
    pc_search = int(total_search * 0.3)
    mobile_search = int(total_search * 0.7)

    # 순위 표시 (위 suffix 포함)
    rank_str = f"{rank}위" if rank and rank > 0 else "순위권 밖"

    # 순위 설명 (Lian 사인 2026-04-27 — "미확인" / "확인중" 표현 X, 분명한 표현)
    if not rank or rank == 0:
        rank_desc = "순위권 체크 불가 (상위 노출 안 됨)"
    elif rank == 1:
        rank_desc = "지역 1위"
    elif rank <= 3:
        rank_desc = "상위 노출"
    elif rank <= 10:
        rank_desc = "노출 가능권"
    else:
        rank_desc = "하위 노출"

    # 검색량 설명
    search_desc = "명이 검색 중" if total_search > 0 else "수집중"

    # 업체명 이/가 조사
    def _이가(name):
        if not name:
            return "이"
        code = ord(name[-1])
        if 0xAC00 <= code <= 0xD7A3:
            return "이" if (code - 0xAC00) % 28 != 0 else "가"
        return "이"
    biz_name_이가 = data["business_name"] + _이가(data["business_name"])

    # 진단 핵심 (fact only — 공포 단정 X, orchestrator v3 톤 일치, Lian 사인 2026-04-27 §12.2)
    primary_kw = (keywords[0] if keywords else {}).get("keyword", "") if keywords else ""
    primary_kw_str = f"'{primary_kw}'" if primary_kw else f"'{data['category']}'"
    if not rank or rank == 0:
        shock_copy = f"네이버 플레이스에서 {primary_kw_str} 검색 시 노출되지 않고 있습니다."
    elif rank > 10:
        shock_copy = f"{primary_kw_str} 검색 결과 {rank}위로, 새 손님 노출 빈도가 낮은 위치입니다."
    elif rank > 3:
        shock_copy = f"{primary_kw_str} 검색 시 {rank}위로 노출 중입니다. 상위 진입 여지가 있습니다."
    else:
        shock_copy = f"{primary_kw_str} 검색 시 {rank}위로 상위 노출 중입니다."

    # 주요 문제
    problems = []
    if data.get("photo_count", 0) < 5:
        problems.append(f"사진 {data.get('photo_count',0)}장")
    if not data.get("has_intro"):
        problems.append("소개글 없음")
    if not data.get("has_news"):
        problems.append("새소식 미등록")
    if data.get("blog_review_count", 0) < 3:
        problems.append(f"블로그 리뷰 {data.get('blog_review_count',0)}개")
    main_problem = " / ".join(problems) if problems else "전반적인 플레이스 최적화 미흡"

    recommended_pkg = PACKAGE_BY_GRADE.get(data["grade"], "바이럴 성장")

    # 가게 type 분기 (Lian 사인 2026-04-28) — 부족/우월/완벽 type 별 hook 변경
    business_type = classify_business_type(data, seoul_anchor)
    type_hook = get_type_hook(business_type, data, seoul_anchor, primary_kw or data.get("category", ""))
    print(f"  가게 type: {business_type} ({type_hook['type_label']})")
    if type_hook["shock_copy"]:
        shock_copy = type_hook["shock_copy"]
    if type_hook["main_problem"]:
        main_problem = type_hook["main_problem"]
    if type_hook["recommended_pkg"]:
        recommended_pkg = type_hook["recommended_pkg"]

    # 키워드 7개 (부족하면 빈 칸)
    kw_list = keywords[:7]
    while len(kw_list) < 7:
        kw_list.append({"keyword": "-", "search_volume": 0})

    # 우리 업체 점유율 추정 (순위 기반)
    if rank and rank > 0:
        if rank <= 2:
            our_share = '약 35%'
        elif rank <= 5:
            our_share = '약 10%'
        elif rank <= 10:
            our_share = '약 3%'
        else:
            our_share = '≈ 0%'
    else:
        our_share = '≈ 0%'

    # 월 손실 매출 → 6개월 누적 (객단가 업종별 매핑, Lian §12.2 정정 2026-04-27)
    avg_price = get_avg_price_by_category(data.get("category", ""))
    monthly_lost = lost * avg_price if lost > 0 else 0
    loss_6m_만원 = max(round(monthly_lost * 6 / 10000), 1) if monthly_lost > 0 else 0
    # Fix B (2026-04-28): lost cap (1499) 도달 시 "최대 추정" 라벨로 정직 표기 (§5)
    is_lost_capped = lost >= 1499
    lost_label_suffix = "+ 추정 (최대)" if is_lost_capped else " (추정)"

    # 추천 패키지별 월 비용 (38/56/95만)
    pkg_obj = next((p for p in PACKAGES if p["name"] == recommended_pkg), PACKAGES[1])
    monthly_cost = int(pkg_obj["price"].replace(",", ""))
    daily_cost = monthly_cost // 30

    # 본전 / 목표 명수 (월 비용 / 객단가)
    breakeven_count = max(round(monthly_cost / avg_price), 1) if avg_price else 1
    target_count = breakeven_count * 2  # 정론 1.5-2x ROI 기준 (Wiegers SR3 외부 정합)
    roi_multiplier = "5-10배 (추정)"  # 명시 추정 라벨 (§5)

    # 우리 vs 경쟁사 fact
    our_review = (data.get("visitor_review_count", 0) or 0) + (data.get("receipt_review_count", 0) or 0)
    our_photo = data.get("photo_count", 0) or 0
    comp_review = data.get("competitor_avg_review", 0) or 0
    comp_photo = data.get("competitor_avg_photo", 0) or 0
    comp_name = data.get("competitor_name") or "지역 상위 경쟁사"
    own_brand_vol = data.get("own_brand_search_volume", 0) or 0
    comp_brand_vol = data.get("competitor_brand_search_volume", 0) or 0

    # 가망 고객 (월 검색량 × 클릭률 8%)
    prospect_count = int(total_search * 0.08) if total_search else 0

    # 진단 번호 (timestamp)
    diag_id = datetime.now().strftime("%Y%m%d-%H%M")

    # 키워드 볼륨 바 (동적)
    kw_vols = [kw.get('search_volume', 0) or 0 for kw in kw_list]
    max_vol = max(kw_vols) if any(kw_vols) else 1

    # 3. 템플릿 변수 치환 (Lian §12.2 사인 — 19 미치환 wiring 추가, 3 낭비 제거)
    replacements = {
        "{{업체명}}": data["business_name"],
        "{{업종}}": data["category"],
        "{{주소}}": data["address"],
        "{{충격카피}}": shock_copy,
        "{{순위}}": rank_str,
        "{{업체명이가}}": biz_name_이가,
        "{{가망고객분석}}": (f"{lost}{lost_label_suffix}") if lost > 0 else "?",
        "{{가망고객수}}": format_number_with_comma(prospect_count) if prospect_count else "수집중",
        "{{전체검색량}}": format_number_with_comma(total_search) if total_search else "수집중",
        "{{PC검색량}}": format_number_with_comma(pc_search) if pc_search else "-",
        "{{모바일검색량}}": format_number_with_comma(mobile_search) if mobile_search else "-",
        "{{순위설명}}": rank_desc,
        "{{검색량설명}}": search_desc,
        "{{추천패키지}}": recommended_pkg,
        "{{수집일}}": today,
        "{{주요문제}}": main_problem,
        "{{진단그리드}}": generate_diagnosis_grid(data, seoul_categories),
        "{{패키지그리드}}": generate_package_grid(recommended_pkg),
        "{{우리점유율}}": our_share,
        "{{손실6개월}}": f'{loss_6m_만원:,}' if loss_6m_만원 > 0 else '?',
        # 신규 wiring (§12.2 sign 2026-04-27)
        "{{월손실금}}": (format_number_with_comma(monthly_lost // 10000) + "만원" + lost_label_suffix) if monthly_lost else "수집중",
        "{{객단가}}": format_number_with_comma(avg_price) + "원 (업종 평균 추정)",
        "{{사장님이름}}": f"{data['business_name']} 대표",
        "{{경쟁사리뷰}}": format_number_with_comma(seoul_anchor.get("avg_review", 0)) if seoul_anchor.get("avg_review") else (format_number_with_comma(comp_review) if comp_review else "수집중"),
        "{{경쟁사사진}}": format_number_with_comma(seoul_anchor.get("avg_photo", 0)) if seoul_anchor.get("avg_photo") else (format_number_with_comma(comp_photo) if comp_photo else "수집중"),
        "{{경쟁사업체명}}": f"서울 상위권 {anchor_key} (10개 업체 평균)" if seoul_anchor.get("avg_photo") else comp_name,
        "{{경쟁사브랜드검색}}": format_number_with_comma(comp_brand_vol) if comp_brand_vol else "수집중",
        "{{우리리뷰}}": format_number_with_comma(our_review),
        "{{우리사진}}": format_number_with_comma(our_photo),
        "{{자사브랜드검색}}": format_number_with_comma(own_brand_vol) if own_brand_vol else "수집중",
        "{{본전명수}}": str(breakeven_count),
        "{{목표명수}}": str(target_count),
        "{{roi배수}}": roi_multiplier,
        "{{월비용}}": format_number_with_comma(monthly_cost // 10000) + "만원",
        "{{하루비용}}": format_number_with_comma(daily_cost) + "원",
        "{{진단번호}}": diag_id,
        "{{카톡번호}}": "010-XXXX-XXXX (담당자 입력)",
    }

    # 키워드 및 검색량 치환 (동적 바 너비 포함)
    for idx, kw in enumerate(kw_list, 1):
        vol = kw.get('search_volume', 0) or 0
        replacements[f"{{{{키워드{idx}}}}}"] = kw.get("keyword", "-") or "-"
        replacements[f"{{{{검색량{idx}}}}}"] = format_number_with_comma(vol) if vol else "-"
        bar_pct = round(vol / max_vol * 90) if max_vol > 0 and vol > 0 else 5
        replacements[f"{{{{검색량바{idx}}}}}"] = str(max(bar_pct, 5))

    # 모든 치환 수행
    for key, value in replacements.items():
        html_content = html_content.replace(key, str(value))

    # 4. 임시 HTML 파일 저장
    temp_html_path = Path(output_dir) / f"temp_{data['business_name']}.html"
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ 임시 HTML 생성: {temp_html_path}")

    # 5. Playwright로 PDF 변환
    pdf_filename = f"{data['business_name']}_진단리포트_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf_path = Path(output_dir) / pdf_filename

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # file:// URL로 로드 (경로 구분자 변환)
            file_url = f"file:///{str(temp_html_path).replace(chr(92), '/')}"
            print(f"✓ HTML 로드 중: {file_url}")

            page.goto(file_url, wait_until="networkidle")

            # PDF 생성
            print(f"📄 PDF 생성 중...")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
            )

            browser.close()

            print(f"✓ PDF 생성 완료: {pdf_path}")

    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        sys.exit(1)

    # 6. 임시 HTML 파일 삭제
    try:
        temp_html_path.unlink()
        print(f"✓ 임시 파일 삭제")
    except Exception as e:
        print(f"⚠ 임시 파일 삭제 실패: {e}")

    print()
    print(f"✅ 완료!")
    print(f"📁 저장 위치: {pdf_path}")

    return str(pdf_path)


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Template 10 (Pastel Modern) — PDF 생성 스크립트")
    print("=" * 60)
    print()

    # 커맨드라인 인자로 업체명 받기
    target = sys.argv[1] if len(sys.argv) > 1 else None
    data = load_from_db(target)

    print(f"[DB 데이터 확인]")
    print(f"  업체명: {data['business_name']}")
    print(f"  업종: {data['category']}")
    print(f"  주소: {data['address']}")
    print(f"  순위: {data['naver_place_rank']}")
    print(f"  등급: {data['grade']} / 손실추정: {data['estimated_lost_customers']}명")
    print(f"  사진: {data['photo_count']}장 / 리뷰: {data['visitor_review_count']}개 / 블로그: {data['blog_review_count']}개")
    print(f"  키워드 수: {len(data['keywords'])}개")
    print()

    generate_pdf(data)
