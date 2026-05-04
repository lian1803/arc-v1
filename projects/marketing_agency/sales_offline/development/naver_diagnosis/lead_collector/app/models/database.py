"""SQLAlchemy 엔진 및 세션 설정"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import DB_PATH


class Base(DeclarativeBase):
    pass


engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """테이블 + 인덱스 생성"""
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        # WAL 모드: 읽기/쓰기 동시 접근 시 충돌 방지 (HIGH 이슈 수정)
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_businesses_session  ON businesses(session_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_businesses_phone    ON businesses(phone)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_businesses_verify   ON businesses(verify_status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_history_region      ON collection_history(region)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_history_started     ON collection_history(started_at DESC)"))
        conn.commit()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
