"""
SQLite + SQLAlchemy 2.0 비동기 데이터베이스 설정
"""
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

# core/company/.env 중앙 로드
for _p in Path(__file__).resolve().parents:
    if (_p / "company" / ".env").exists():
        load_dotenv(_p / "company" / ".env")
        break
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./diagnosis.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI 의존성 주입용 DB 세션 제공"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(drop_existing: bool = False):
    """
    데이터베이스 테이블 생성

    Args:
        drop_existing: True면 기존 테이블 삭제 후 재생성 (개발용)
    """
    from models import DiagnosisHistory, CrawlJob, BenchmarkPremium
    from sqlalchemy import text
    async with engine.begin() as conn:
        if drop_existing:
            # 개발 단계: 스키마 변경 시 기존 테이블 삭제 후 재생성
            await conn.run_sync(Base.metadata.drop_all)
            print("[DB] 기존 테이블 삭제됨")
        await conn.run_sync(Base.metadata.create_all)

        # 신규 컬럼 추가 (기존 DB 호환)
        migration_columns = [
            ("owner_reply_rate", "REAL DEFAULT 0.0"),
            ("intro_text", "TEXT"),
            ("review_last_30d_count", "INTEGER DEFAULT 0"),
            ("review_last_90d_count", "INTEGER DEFAULT 0"),
            ("news_last_date", "DATETIME"),
        ]
        for col_name, col_def in migration_columns:
            try:
                await conn.execute(text(f"ALTER TABLE diagnosis_history ADD COLUMN {col_name} {col_def}"))
                print(f"[DB] 신규 컬럼 추가됨: {col_name}")
            except Exception as e:
                # 이미 존재하는 컬럼이면 무시
                if "duplicate column" not in str(e).lower() and "already exists" not in str(e).lower():
                    print(f"[DB] 컬럼 추가 오류 {col_name}: {e}")

        # CRMBusiness 신규 컬럼 추가 (2026-04-20)
        crm_migration_columns = [
            ("region", "TEXT"),
            ("excel_phone", "TEXT"),
            ("industry", "TEXT"),
            ("today_selected", "BOOLEAN DEFAULT 0"),
            ("contacted_today", "BOOLEAN DEFAULT 0"),
            ("last_reset_date", "DATETIME"),
        ]
        for col_name, col_def in crm_migration_columns:
            try:
                await conn.execute(text(f"ALTER TABLE crm_businesses ADD COLUMN {col_name} {col_def}"))
                print(f"[DB] CRM 신규 컬럼 추가됨: {col_name}")
            except Exception as e:
                if "duplicate column" not in str(e).lower() and "already exists" not in str(e).lower():
                    print(f"[DB] CRM 컬럼 추가 오류 {col_name}: {e}")

        # WAL 모드 활성화: 배치 중 단건 진단 동시 접근 안정성 향상
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        print("[DB] 테이블 생성/확인 완료 (WAL 모드 활성화 + benchmark_premium 테이블)")


async def close_db():
    """데이터베이스 연결 종료"""
    await engine.dispose()
