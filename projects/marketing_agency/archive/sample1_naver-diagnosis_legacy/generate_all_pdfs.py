#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB에 있는 모든 업체 PDF 일괄 생성 → 바탕화면
실행: python generate_all_pdfs.py
"""

import sys
import io
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

DB_PATH = Path(__file__).parent / "diagnosis.db"
DESKTOP = Path.home() / "Desktop"


def get_all_businesses():
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute('''
        SELECT DISTINCT dh.business_name
        FROM diagnosis_history dh
        JOIN (
            SELECT business_name, MAX(created_at) as max_ts
            FROM diagnosis_history
            GROUP BY business_name
        ) latest ON dh.business_name = latest.business_name AND dh.created_at = latest.max_ts
        ORDER BY dh.business_name
    ''').fetchall()
    conn.close()
    return [r[0] for r in rows]


if __name__ == "__main__":
    from generate_html_pdf import load_from_db, generate_pdf

    businesses = get_all_businesses()
    print(f"총 {len(businesses)}개 업체 PDF 생성 시작\n")

    success = []
    failed = []

    for biz in businesses:
        print(f"{'='*50}")
        print(f"▶ {biz}")
        try:
            data = load_from_db(biz)
            generate_pdf(data, str(DESKTOP))
            success.append(biz)
        except Exception as e:
            print(f"❌ 오류: {e}")
            failed.append((biz, str(e)))

    print(f"\n{'='*50}")
    print(f"완료: {len(success)}/{len(businesses)}")
    if failed:
        print("실패:")
        for biz, err in failed:
            print(f"  {biz}: {err}")
    else:
        print("모두 성공!")
    print(f"\n📁 저장 위치: {DESKTOP}")
