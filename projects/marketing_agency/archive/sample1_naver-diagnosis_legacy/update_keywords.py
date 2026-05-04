#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB에 저장된 모든 업체의 키워드 검색량 업데이트 (Naver Search Ad API 사용)
실행: python update_keywords.py
"""

import sys
import io
import json
import sqlite3
import asyncio
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))

from services.naver_search_ad import NaverSearchAdAPI

DB_PATH = Path(__file__).parent / "diagnosis.db"


async def update_all():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 각 업체의 최신 진단 레코드 가져오기
    cur.execute('''
        SELECT dh.id, dh.business_name, dh.category, dh.address, dh.keywords
        FROM diagnosis_history dh
        JOIN (
            SELECT business_name, MAX(created_at) as max_ts
            FROM diagnosis_history
            GROUP BY business_name
        ) latest ON dh.business_name = latest.business_name AND dh.created_at = latest.max_ts
        ORDER BY dh.business_name
    ''')
    rows = conn.execute('''
        SELECT dh.id, dh.business_name, dh.category, dh.address, dh.keywords
        FROM diagnosis_history dh
        JOIN (
            SELECT business_name, MAX(created_at) as max_ts
            FROM diagnosis_history
            GROUP BY business_name
        ) latest ON dh.business_name = latest.business_name AND dh.created_at = latest.max_ts
        ORDER BY dh.business_name
    ''').fetchall()

    api = NaverSearchAdAPI()
    updated = 0

    for row in rows:
        biz = row['business_name']
        keywords_json = row['keywords']
        if not keywords_json:
            print(f"  [{biz}] 키워드 없음 — 스킵")
            continue

        try:
            keywords = json.loads(keywords_json)
        except Exception:
            print(f"  [{biz}] 키워드 JSON 파싱 오류 — 스킵")
            continue

        if not keywords:
            print(f"  [{biz}] 키워드 리스트 비어있음 — 스킵")
            continue

        print(f"\n[{biz}] {len(keywords)}개 키워드 업데이트 중...")
        new_keywords = []
        total = 0
        for kw in keywords:
            kw_text = kw.get("keyword", "")
            if not kw_text or kw_text == "-":
                new_keywords.append(kw)
                continue
            result = await api.get_keyword_stats(kw_text)
            def _int(v):
                try: return int(v)
                except: return 0
            pc = _int(result.get("monthly_search_pc", 0))
            mob = _int(result.get("monthly_search_mobile", 0))
            sv = pc + mob
            total += sv
            new_kw = dict(kw)
            new_kw["search_volume"] = sv
            new_kw["monthly_search_pc"] = pc
            new_kw["monthly_search_mobile"] = mob
            new_keywords.append(new_kw)
            print(f"  {kw_text}: {sv:,}")

        # DB 업데이트
        conn.execute(
            "UPDATE diagnosis_history SET keywords=? WHERE id=?",
            (json.dumps(new_keywords, ensure_ascii=False), row['id'])
        )
        conn.commit()
        print(f"  → 총 검색량: {total:,} / DB 업데이트 완료")
        updated += 1

    conn.close()
    print(f"\n완료: {updated}개 업체 키워드 업데이트")


if __name__ == "__main__":
    asyncio.run(update_all())
