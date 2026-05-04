"""양주 random 2 가게 진단 → DB insert → PDF 생성 (바탕화면)."""
import sys, asyncio, random, sqlite3, json, io
from pathlib import Path
from datetime import datetime
import openpyxl

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(THIS_DIR.parent))

from run_one_to_md import run_diagnosis
from generate_html_pdf import generate_pdf, load_from_db

# import 후 stdout 닫힘 → fd 직접 reopen
import os
sys.stdout = os.fdopen(1, 'w', encoding='utf-8', errors='replace', closefd=False)
sys.stderr = os.fdopen(2, 'w', encoding='utf-8', errors='replace', closefd=False)

EXCEL = THIS_DIR.parent / "lead_db" / "양주_010번호_최종_20260326_144032.xlsx"
DB = THIS_DIR / "diagnosis.db"


def list_businesses(xlsx_path):
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    headers = [str(h).strip() if h else "" for h in rows[0]]
    name_idx = next((i for i, h in enumerate(headers) if "업체명" in h or "상호" in h), 2)
    franchise = ["본점", "직영", "체인", "가맹", "프랜차이즈", "1호점", "2호점"]
    names = []
    for row in rows[1:]:
        if not row or name_idx >= len(row):
            continue
        n = str(row[name_idx]).strip() if row[name_idx] else ""
        if not n or n == "None" or any(k in n for k in franchise):
            continue
        names.append(n)
    return names


def insert_to_db(data):
    """diagnosis_history table 에 1 row insert. 누락 field 는 default."""
    conn = sqlite3.connect(str(DB))
    schema_cols = [r[1] for r in conn.execute("PRAGMA table_info(diagnosis_history)").fetchall()]

    def jdumps(v):
        try:
            return json.dumps(v if v else [], ensure_ascii=False, default=lambda x: x.decode('utf-8','replace') if isinstance(x, bytes) else str(x))
        except Exception:
            return "[]"

    defaults = {
        # 정수 0 default
        **{k: 0 for k in ["photo_count", "review_count", "blog_review_count", "menu_count", "intro_text_length",
                          "directions_text_length", "receipt_review_count", "visitor_review_count",
                          "naver_place_rank", "competitor_avg_review", "competitor_avg_photo",
                          "competitor_avg_blog", "competitor_brand_search_volume", "own_brand_search_volume",
                          "estimated_lost_customers", "bookmark_count", "keyword_rating_review_count",
                          "news_last_days", "review_last_30d_count", "review_last_90d_count"]},
        # 부울 0
        **{k: 0 for k in ["has_menu", "has_hours", "has_price", "has_intro", "has_directions",
                          "has_booking", "has_talktalk", "has_smartcall", "has_coupon", "has_news",
                          "has_menu_description", "has_owner_reply", "has_instagram", "has_kakao",
                          "is_manual"]},
        # float 0
        **{k: 0.0 for k in ["photo_score", "review_score", "blog_score", "keyword_score",
                            "info_score", "convenience_score", "engagement_score", "total_score",
                            "review_sentiment_score", "review_negative_ratio",
                            "photo_quality_score", "owner_reply_rate"]},
        # JSON
        **{k: jdumps([]) for k in ["keywords", "related_keywords", "improvement_points",
                                    "review_texts", "photo_urls", "review_main_complaints",
                                    "photo_quality_issues"]},
        # str/null
        "grade": "D",
        "messages": None, "ai_first_message": None, "intro_text": None,
        "place_id": None, "address": None, "category": None, "place_url": None,
        "ppt_filename": None, "industry_type": None, "priority_tag": None,
        "competitor_name": None, "news_last_date": None,
    }
    row = {**defaults}
    # data 의 값 덮어쓰기
    for k, v in data.items():
        if k in schema_cols:
            if k in ["keywords", "related_keywords", "improvement_points", "review_texts",
                     "photo_urls", "review_main_complaints", "photo_quality_issues"]:
                row[k] = jdumps(v) if not isinstance(v, str) else v
            elif k in ["has_menu", "has_hours", "has_price", "has_intro", "has_directions",
                       "has_booking", "has_talktalk", "has_smartcall", "has_coupon", "has_news",
                       "has_menu_description", "has_owner_reply", "has_instagram", "has_kakao", "is_manual"]:
                row[k] = 1 if v else 0
            else:
                row[k] = v if v is not None else row.get(k)
    row["business_name"] = data.get("business_name")
    row["created_at"] = datetime.now().isoformat()
    # review_count = visitor + receipt
    row["review_count"] = (row.get("visitor_review_count", 0) or 0) + (row.get("receipt_review_count", 0) or 0)

    cols = [c for c in schema_cols if c != "id"]
    placeholders = ",".join(["?"] * len(cols))
    vals = [row.get(c) for c in cols]
    conn.execute(f"INSERT INTO diagnosis_history ({','.join(cols)}) VALUES ({placeholders})", vals)
    conn.commit()
    conn.close()
    print(f"  DB insert OK: {data.get('business_name')}")


async def diagnose_and_save():
    """진단 + DB insert. PDF 는 subprocess 로 별도 (sync_playwright + asyncio 충돌 회피)."""
    names = list_businesses(EXCEL)
    sample = random.sample(names, 3)
    print(f"random 2: {sample}\n")
    saved = []
    for biz in sample:
        print(f"\n{'='*60}\n진단: {biz}\n{'='*60}")
        try:
            data = await run_diagnosis(biz)
            if not data:
                print(f"  진단 fail — skip")
                continue
            data.setdefault("business_name", biz)
            insert_to_db(data)
            saved.append(biz)
        except Exception as e:
            print(f"  진단 fail: {e}")
            import traceback; traceback.print_exc()
    return saved


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    saved = asyncio.run(diagnose_and_save())
    # PDF subprocess (sync_playwright 가 asyncio loop 와 충돌하므로 별도 process)
    import subprocess
    for biz in saved:
        print(f"\n--- PDF 생성: {biz} ---")
        r = subprocess.run([sys.executable, "generate_html_pdf.py", biz], capture_output=True, text=True, encoding="utf-8")
        print(r.stdout[-500:] if r.stdout else "(no stdout)")
        if r.returncode != 0:
            print(f"PDF fail rc={r.returncode}: {r.stderr[-300:]}")


if __name__ == "__main__":
    main()
