"""
샘플 데이터로 PPT + 멘트 바탕화면에 뽑기
"""
import sys
import os
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 경로 설정
THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))

DESKTOP = Path.home() / "Desktop"

# ── 샘플 데이터 (양주 미용실 "헤어림") ────────────────────────────────────────
SAMPLE_DATA = {
    "business_name": "헤어림",
    "category": "미용실",
    "address": "경기도 양주시 회정동",
    "naver_place_rank": 13,
    "grade": "D",
    "total_score": 28,
    "estimated_lost_customers": 557,

    # 사진/리뷰
    "photo_count": 4,
    "visitor_review_count": 11,
    "receipt_review_count": 0,
    "blog_review_count": 2,

    # 경쟁사 비교
    "competitor_avg_photo": 38,
    "competitor_avg_review": 127,

    # 기본 정보
    "has_intro": False,
    "has_directions": False,
    "has_booking": False,
    "has_talktalk": False,
    "has_smartcall": False,
    "has_news": False,
    "has_coupon": False,
    "has_instagram": False,
    "has_kakao": False,
    "has_price": False,
    "has_menu": True,
    "menu_count": 3,
    "has_menu_description": False,
    "has_hours": True,

    # 점수 (항목별)
    "photo_score": 20,
    "review_score": 15,
    "blog_score": 30,
    "info_score": 25,
    "keyword_score": 40,
    "convenience_score": 10,
    "engagement_score": 20,

    # 키워드
    "keywords": [
        {"keyword": "양주 미용실", "search_volume": 4400},
        {"keyword": "양주 헤어샵", "search_volume": 1900},
        {"keyword": "회정동 미용실", "search_volume": 720},
        {"keyword": "양주 커트", "search_volume": 590},
        {"keyword": "양주 염색", "search_volume": 480},
    ],

    # 기타
    "news_last_days": 120,
    "bookmark_count": 3,
}


def generate_ppt():
    from services.ppt_generator import PPTGenerator
    gen = PPTGenerator(output_dir=str(DESKTOP))
    filename = gen.generate(SAMPLE_DATA)
    print(f"✅ PPT 저장: {DESKTOP / filename}")
    return filename


def generate_messages():
    from services.message_generator import generate_all_messages
    msgs = generate_all_messages(SAMPLE_DATA)

    lines = []
    biz = SAMPLE_DATA["business_name"]

    lines += [
        f"# {biz} 영업 메시지 — 복붙용",
        "=" * 60,
        "",
        "## ① 1차 카톡 (첫 접촉 — 진단 결과 보내도 되냐고 물어보기)",
        f"[{msgs['first']['label']}]",
        msgs['first']['text'],
        "",
        "## ① 1차 SMS (짧은 버전)",
        msgs['first']['sms_text'],
        "",
        "=" * 60,
        "## ② 2차 카톡 (진단 결과 카드)",
        msgs['second'],
        "",
        "=" * 60,
        "## ③ 3차 카톡 (패키지 + 손익분기)",
        msgs['third'],
        "",
        "=" * 60,
        "## ④ 4차 — 보류 대응",
        msgs['fourth']['보류'],
        "",
        "## ④ 4차 — 무응답 대응",
        msgs['fourth']['무응답'],
        "",
        "## ④ 4차 — 비싸다 대응",
        msgs['fourth']['비싸다'],
        "",
        "## ④ 4차 — 직접 하겠다 대응",
        msgs['fourth']['직접'],
        "",
        "=" * 60,
        "## ⑤ 5차 카톡 (계약 의향 확인 후 결제 안내)",
        msgs['fifth'],
        "",
        "=" * 60,
        "## ⑥ 6차 카톡 (결제 완료 후 온보딩)",
        msgs['sixth'],
        "",
    ]

    out_path = DESKTOP / f"{biz}_영업멘트.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ 멘트 저장: {out_path}")


if __name__ == "__main__":
    print(f"\n업체: {SAMPLE_DATA['business_name']} ({SAMPLE_DATA['category']})")
    print(f"등급: {SAMPLE_DATA['grade']} / 순위: {SAMPLE_DATA['naver_place_rank']}위 / 손실: 월 {SAMPLE_DATA['estimated_lost_customers']}명\n")

    try:
        generate_ppt()
    except Exception as e:
        print(f"❌ PPT 오류: {e}")

    try:
        generate_messages()
    except Exception as e:
        print(f"❌ 멘트 오류: {e}")

    print("\n완료! 바탕화면 확인해봐.")
