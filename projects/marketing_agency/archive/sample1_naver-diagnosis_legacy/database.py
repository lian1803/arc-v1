"""
SQLite + SQLAlchemy 2.0 비동기 데이터베이스 설정
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

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
    from models import DiagnosisHistory, CrawlJob
    from sqlalchemy import text
    async with engine.begin() as conn:
        if drop_existing:
            # 개발 단계: 스키마 변경 시 기존 테이블 삭제 후 재생성
            await conn.run_sync(Base.metadata.drop_all)
            print("[DB] 기존 테이블 삭제됨")
        await conn.run_sync(Base.metadata.create_all)
        # WAL 모드 활성화: 배치 중 단건 진단 동시 접근 안정성 향상
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        print("[DB] 테이블 생성/확인 완료 (WAL 모드 활성화)")


async def close_db():
    """데이터베이스 연결 종료"""
    await engine.dispose()
