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

PACKAGE_PRICES = {
    "주목패키지": {"정상가": "290,000", "약정가": "290,000", "합계6개월": "1,740,000"},
    "집중패키지": {"정상가": "490,000", "약정가": "490,000", "합계6개월": "2,940,000"},
    "시선패키지": {"정상가": "890,000", "약정가": "890,000", "합계6개월": "5,340,000"},
}

PACKAGE_BY_GRADE = {"A": "주목패키지", "B": "주목패키지", "C": "집중패키지", "D": "시선패키지"}


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


def generate_diagnosis_grid(data: Dict[str, Any]) -> str:
    """
    진단 그리드 HTML 생성 (10개 항목)

    항목 순서:
    1. 대표사진 (사진 >= 10개면 ok)
    2. 영업시간 (항상 ok로 가정)
    3. 메뉴/가격 (메뉴 있으면 ok)
    4. 소개글 (intro 있으면 ok)
    5. 오시는길 (directions 있으면 ok)
    6. 예약 (booking 있으면 ok)
    7. 톡톡 (talktalk 있으면 ok)
    8. 새소식 (news 있으면 ok)
    9. 블로그리뷰 (blog_review >= 5면 ok)
    10. 인스타그램 (instagram 있으면 ok)
    """

    items = [
        {
            "name": "대표사진",
            "ok": data.get("photo_count", 0) >= 10
        },
        {
            "name": "영업시간",
            "ok": True  # 항상 ok
        },
        {
            "name": "메뉴/가격",
            "ok": data.get("has_menu", False)
        },
        {
            "name": "소개글",
            "ok": data.get("has_intro", False)
        },
        {
            "name": "오시는길",
            "ok": data.get("has_directions", False)
        },
        {
            "name": "예약",
            "ok": data.get("has_booking", False)
        },
        {
            "name": "톡톡",
            "ok": data.get("has_talktalk", False)
        },
        {
            "name": "새소식",
            "ok": data.get("has_news", False)
        },
        {
            "name": "블로그리뷰",
            "ok": data.get("blog_review_count", 0) >= 5
        },
        {
            "name": "인스타그램",
            "ok": data.get("has_instagram", False)
        },
    ]

    html_parts = []
    for item in items:
        if item["ok"]:
            html_parts.append(f'''    <div class="di ok">
      <div class="di-s ds-ok">✓</div>
      <div class="di-name">{item["name"]}</div>
      <div class="di-tag dt-ok">정상</div>
    </div>''')
        else:
            html_parts.append(f'''    <div class="di bad">
      <div class="di-s ds-bad">✕</div>
      <div class="di-name">{item["name"]}</div>
      <div class="di-tag dt-bad">개선필요</div>
    </div>''')

    return '\n'.join(html_parts)


def generate_package_grid(recommended_package: str) -> str:
    """
    패키지 그리드 HTML 생성 (3개 카드, 추천 패키지에 rec class 추가)
    """

    packages = [
        {
            "name": "주목패키지",
            "price": "290,000",
            "features": [
                "기본정보 최적화",
                "핵심 키워드 마케팅",
                "월 성과 리포트"
            ]
        },
        {
            "name": "집중패키지",
            "price": "490,000",
            "features": [
                "주목패키지 전체",
                "전문 사진 촬영",
                "블로그 리뷰 대행",
                "고객 답글 관리"
            ]
        },
        {
            "name": "시선패키지",
            "price": "890,000",
            "features": [
                "집중패키지 전체",
                "인스타그램 관리",
                "새소식 제작",
                "전담 매니저 배정"
            ]
        }
    ]

    html_parts = []
    for pkg in packages:
        is_recommended = pkg["name"] == recommended_package
        rec_class = ' rec' if is_recommended else ''
        rec_header_class = 'rh' if is_recommended else ''

        features_html = '\n  '.join([f'<div class="pi">{feat}</div>' for feat in pkg["features"]])

        if is_recommended:
            html_parts.append(f'''  <div class="pc{rec_class}">
    <div class="ph {rec_header_class}"><div class="pn">{pkg["name"]}</div><span class="rtag">추천</span></div>
    <div class="pb">
      <div class="ppl">월 구독료</div>
      <div class="pp">{pkg["price"]}<span class="ppu">원/월</span></div>
      <div class="ps"></div>
      {features_html}
    </div>
  </div>''')
        else:
            html_parts.append(f'''  <div class="pc{rec_class}">
    <div class="ph {rec_header_class}"><div class="pn">{pkg["name"]}</div></div>
    <div class="pb">
      <div class="ppl">월 구독료</div>
      <div class="pp">{pkg["price"]}<span class="ppu">원/월</span></div>
      <div class="ps"></div>
      {features_html}
    </div>
  </div>''')

    return '\n'.join(html_parts)


def get_recommended_package(grade: str) -> str:
    """등급에 따른 추천 패키지 반환"""
    if grade in ["A", "B"]:
        return "주목패키지"
    elif grade == "C":
        return "집중패키지"
    else:  # D 등급
        return "시선패키지"


def get_package_pricing(package_name: str) -> Dict[str, str]:
    """패키지명에 따른 가격 정보 반환"""
    pricing = {
        "주목패키지": {"monthly": "290,000", "6month": "1,740,000"},
        "집중패키지": {"monthly": "490,000", "6month": "2,940,000"},
        "시선패키지": {"monthly": "890,000", "6month": "5,340,000"},
    }
    return pricing.get(package_name, {"monthly": "0", "6month": "0"})


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
    print(f"  등급: {data['grade']}")
    print()

    # 1. 템플릿 읽기
    template_path = Path(__file__).parent / "html_templates" / "template_10_pastel_modern.html"

    if not template_path.exists():
        print(f"❌ 템플릿 파일을 찾을 수 없습니다: {template_path}")
        sys.exit(1)

    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 2. 데이터 준비
    today = datetime.now().strftime("%Y년 %m월 %d일")
    now_str = datetime.now().strftime("%Y%m%d")
    rank = data["naver_place_rank"]
    lost = data["estimated_lost_customers"]
    biz_id = data.get("id") or data.get("business_id") or "0"

    keywords = data.get("keywords") or []
    total_search = sum(k.get("search_volume", 0) for k in keywords)
    pc_search = int(total_search * 0.3)
    mobile_search = int(total_search * 0.7)

    # 연간 기회손실 계산 (만원 단위)
    annual_loss_man = (lost * 12 * 60000) // 10000 if lost > 0 else 0

    # 순위 표시 (위 suffix 포함)
    rank_str = f"{rank}위" if rank and rank > 0 else "미확인"

    # 순위 설명
    if not rank or rank == 0:
        rank_desc = "순위 확인중"
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

    # 충격 카피 — 데이터 기반으로 가장 강한 것 선택
    if lost > 0:
        shock_copy = f"지금 이 순간에도 매달 {lost}명이 경쟁사로 가고 있습니다."
    elif rank and rank > 10:
        shock_copy = f"'{data['category']}' 검색 시 {rank}위 — 새 손님의 눈에 사실상 안 보입니다."
    else:
        shock_copy = "네이버 플레이스가 방치된 채로 매일 손님을 잃고 있습니다."

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

    recommended_pkg = PACKAGE_BY_GRADE.get(data["grade"], "시선패키지")
    prices = PACKAGE_PRICES[recommended_pkg]

    # 키워드 7개 (부족하면 빈 칸)
    kw_list = keywords[:7]
    while len(kw_list) < 7:
        kw_list.append({"keyword": "-", "search_volume": 0})

    # 3. 템플릿 변수 치환
    replacements = {
        "{{업체명}}": data["business_name"],
        "{{업종}}": data["category"],
        "{{주소}}": data["address"],
        "{{충격카피}}": shock_copy,
        "{{순위}}": rank_str,
        "{{업체명이가}}": biz_name_이가,
        "{{가망고객분석}}": str(lost),
        "{{연간기회손실}}": format_number_with_comma(annual_loss_man),
        "{{진단번호}}": f"DIAG-{now_str}-{str(biz_id).zfill(4)}",
        "{{수집일}}": datetime.now().strftime("%Y. %m. %d"),
        "{{전체검색량}}": format_number_with_comma(total_search) if total_search else "수집중",
        "{{PC검색량}}": format_number_with_comma(pc_search) if pc_search else "-",
        "{{모바일검색량}}": format_number_with_comma(mobile_search) if mobile_search else "-",
        "{{순위설명}}": rank_desc,
        "{{검색량설명}}": search_desc,
        "{{추천패키지}}": recommended_pkg,
        "{{진단날짜}}": today,
        "{{주요문제}}": main_problem,
        "{{진단그리드}}": generate_diagnosis_grid(data),
        "{{패키지그리드}}": generate_package_grid(recommended_pkg),
        "{{상호명}}": data["business_name"],
        "{{패키지}}": recommended_pkg,
        "{{정상가}}": prices["정상가"],
        "{{약정가}}": prices["약정가"],
        "{{합계6개월}}": prices["합계6개월"],
    }

    # 키워드 및 검색량 치환
    for idx, kw in enumerate(kw_list, 1):
        replacements[f"{{{{키워드{idx}}}}}"] = kw.get("keyword", "-") or "-"
        vol = kw.get("search_volume", 0) or 0
        replacements[f"{{{{검색량{idx}}}}}"] = format_number_with_comma(vol) if vol else "-"

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
