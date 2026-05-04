"""§12.2 검증 — 양주 db random 10 가게 진단 → 핵심 field 가변/실측 확인. PDF 생성 X."""
import sys
import asyncio
import random
from pathlib import Path
from datetime import datetime
import openpyxl

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(THIS_DIR / "naver_diagnosis"))

from run_one_to_md import run_diagnosis

EXCEL = THIS_DIR / "lead_db" / "양주_010번호_최종_20260326_144032.xlsx"


def list_businesses(xlsx_path):
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    headers = [str(h).strip() if h else "" for h in rows[0]]
    name_idx = next((i for i, h in enumerate(headers) if "업체명" in h or "상호" in h), 2)
    franchise_kw = ["본점", "직영", "체인", "가맹", "프랜차이즈", "1호점", "2호점"]
    names = []
    for row in rows[1:]:
        if not row or name_idx >= len(row):
            continue
        name = str(row[name_idx]).strip() if row[name_idx] else ""
        if not name or name == "None":
            continue
        if any(kw in name for kw in franchise_kw):
            continue
        names.append(name)
    return names


async def main():
    names = list_businesses(EXCEL)
    SAMPLE_SIZE = 20
    sample = random.sample(names, min(SAMPLE_SIZE, len(names)))
    print(f"[양주 db] 총 {len(names)} 중 random {SAMPLE_SIZE} 추출:")
    for i, n in enumerate(sample, 1):
        print(f"  {i:2d}. {n}")
    print()

    results = []
    for idx, biz in enumerate(sample, 1):
        print(f"\n{'='*70}\n[{idx}/10] {biz}\n{'='*70}")
        try:
            data = await run_diagnosis(biz)
            if not data:
                print(f"  ❌ 진단 fail")
                results.append({"name": biz, "ok": False})
                continue
            r = {
                "ok": True,
                "name": biz,
                "category": data.get("category") or "?",
                "address": (data.get("address") or "")[:40] or "(빈)",
                "rank": data.get("naver_place_rank", 0),
                "review": (data.get("visitor_review_count", 0) or 0) + (data.get("receipt_review_count", 0) or 0),
                "photo": data.get("photo_count", 0),
                "blog": data.get("blog_review_count", 0),
                "lost": data.get("estimated_lost_customers", 0),
                "comp_review": data.get("competitor_avg_review", 0),
                "comp_name": data.get("competitor_name") or "(없음)",
                "own_brand": data.get("own_brand_search_volume", 0) or 0,
                "comp_brand": data.get("competitor_brand_search_volume", 0) or 0,
                "owner_reply": data.get("owner_reply_rate", 0) or 0,
                "kw_first": (data.get("keywords") or [{}])[0].get("keyword", "(없음)") if data.get("keywords") else "(없음)",
                "kw_count": len(data.get("keywords") or []),
            }
            results.append(r)
            print(f"  ✓ category={r['category']} addr={r['address']}")
            print(f"    rank={r['rank']} review={r['review']} photo={r['photo']} blog={r['blog']}")
            print(f"    lost={r['lost']} keyword='{r['kw_first']}' (kw_count={r['kw_count']})")
            print(f"    comp_review={r['comp_review']} comp_name={r['comp_name']}")
            print(f"    own_brand={r['own_brand']} comp_brand={r['comp_brand']} owner_reply={r['owner_reply']:.0%}")
        except Exception as e:
            print(f"  ❌ exception: {e}")
            results.append({"name": biz, "ok": False, "err": str(e)})

    # Summary
    ok_results = [r for r in results if r.get("ok")]
    print(f"\n\n{'='*70}\n[SUMMARY] {len(ok_results)}/10 진단 성공\n{'='*70}")
    print(f"\n{'NAME':<24} {'CAT':<14} {'RANK':>4} {'REV':>5} {'PHOTO':>5} {'LOST':>5} {'KW':<14}")
    for r in ok_results:
        print(f"  {r['name'][:22]:<22} {r['category'][:12]:<12} {r['rank']:>4} {r['review']:>5} {r['photo']:>5} {r['lost']:>5} {r['kw_first'][:12]:<12}")

    # 가변 vs 고정 분석
    print(f"\n\n[§12.2 3번 가변 vs 고정 분석]")
    if ok_results:
        for field in ['rank', 'review', 'photo', 'blog', 'lost', 'comp_review', 'own_brand', 'comp_brand', 'owner_reply']:
            vals = [r[field] for r in ok_results]
            unique = set(vals)
            uniq_str = "✅ 가변" if len(unique) > 1 else f"❌ 고정 ({list(unique)[0]})"
            print(f"  {field:>15}: {uniq_str} (uniq={len(unique)}, range={min(vals)}-{max(vals)})")
        # category / addr / comp_name 도
        cats = set(r['category'] for r in ok_results)
        addrs_ok = sum(1 for r in ok_results if r['address'] != '(빈)')
        comp_ok = sum(1 for r in ok_results if r['comp_name'] != '(없음)')
        print(f"  {'category':>15}: {'✅ 가변' if len(cats) > 1 else '❌ 고정'} ({len(cats)} 종류)")
        print(f"  {'address (채워짐)':>15}: {addrs_ok}/{len(ok_results)}")
        print(f"  {'comp_name (채워짐)':>15}: {comp_ok}/{len(ok_results)}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
