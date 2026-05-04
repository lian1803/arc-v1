"""
DB 마이그레이션: 경쟁사 브랜드 검색량 필드 추가
- competitor_name VARCHAR(200)
- competitor_brand_search_volume INTEGER DEFAULT 0
- own_brand_search_volume INTEGER DEFAULT 0
"""
import asyncio
import sys
from sqlalchemy import text
from database import engine


async def migrate():
    """마이그레이션 실행"""
    async with engine.begin() as conn:
        # SQLite는 IF NOT EXISTS 미지원하므로 직접 확인
        # 각 컬럼을 개별적으로 추가 시도

        columns_to_add = [
            ("competitor_name", "VARCHAR(200)"),
            ("competitor_brand_search_volume", "INTEGER DEFAULT 0"),
            ("own_brand_search_volume", "INTEGER DEFAULT 0"),
        ]

        for col_name, col_type in columns_to_add:
            try:
                # SQLite: PRAGMA table_info로 컬럼 존재 여부 확인
                result = await conn.execute(
                    text("PRAGMA table_info(diagnosis_history)")
                )
                rows = result.fetchall()
                col_names = [row[1] for row in rows]

                if col_name not in col_names:
                    await conn.execute(
                        text(f"ALTER TABLE diagnosis_history ADD COLUMN {col_name} {col_type}")
                    )
                    print("[OK] 컬럼 추가됨: " + col_name)
                else:
                    print("[SKIP] 컬럼이 이미 존재함: " + col_name)

            except Exception as e:
                print(f"[ERROR] ({col_name}): {e}")

        await conn.commit()
        print("\n마이그레이션 완료")


if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"마이그레이션 실패: {e}")
        sys.exit(1)
