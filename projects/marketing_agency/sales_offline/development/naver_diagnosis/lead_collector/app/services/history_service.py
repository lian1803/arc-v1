"""수집 이력 관리 서비스"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.history import CollectionHistory
from app.models.business import Business


def _session_to_dict(s: CollectionHistory) -> dict:
    return {
        "id": s.id,
        "region": s.region,
        "keyword": s.keyword,
        "platforms": s.platforms,
        "total_count": s.total_count,
        "confirmed_count": s.verified_count,
        "verified_count": s.verified_count,
        "unverified_count": s.unverified_count,
        "closed_count": s.closed_count,
        "status": s.status,
        "created_at": s.started_at.strftime("%Y-%m-%d %H:%M") if s.started_at else "",
    }


def create_session(db: Session, region: str, keyword: str, platforms: str) -> CollectionHistory:
    session = CollectionHistory(
        region=region,
        keyword=keyword or "",
        platforms=platforms,
        status="진행중",
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def complete_session(db: Session, session_id: int) -> None:
    session = db.query(CollectionHistory).filter_by(id=session_id).first()
    if not session:
        return
    businesses = db.query(Business).filter_by(session_id=session_id).all()
    session.total_count      = len(businesses)
    session.verified_count   = sum(1 for b in businesses if b.verify_status == "확인됨")
    session.unverified_count = sum(1 for b in businesses if b.verify_status == "미확인")
    session.closed_count     = sum(1 for b in businesses if b.verify_status == "폐업의심")
    session.no_phone_count   = sum(1 for b in businesses if not b.phone)
    session.status           = "완료"
    session.completed_at     = datetime.utcnow()
    db.commit()


def fail_session(db: Session, session_id: int, error: str) -> None:
    session = db.query(CollectionHistory).filter_by(id=session_id).first()
    if session:
        session.status    = "오류"
        session.error_log = error[:2000]
        db.commit()


def list_history(limit: int = 30) -> list[dict]:
    """GUI용 — 자체 DB 세션 생성, dict 리스트 반환"""
    db = SessionLocal()
    try:
        sessions = (
            db.query(CollectionHistory)
            .order_by(CollectionHistory.started_at.desc())
            .limit(limit)
            .all()
        )
        return [_session_to_dict(s) for s in sessions]
    finally:
        db.close()


def get_session_businesses(session_id: int) -> list[dict]:
    """GUI용 — 자체 DB 세션 생성, dict 리스트 반환"""
    db = SessionLocal()
    try:
        businesses = db.query(Business).filter_by(session_id=session_id).all()
        return [b.to_dict() for b in businesses]
    finally:
        db.close()


def compare_sessions(session_id_a: int, session_id_b: int) -> dict:
    """두 수집 세션 비교 — 신규/삭제/공통 업체 반환"""
    biz_a = {b["name"]: b for b in get_session_businesses(session_id_a)}
    biz_b = {b["name"]: b for b in get_session_businesses(session_id_b)}

    names_a = set(biz_a.keys())
    names_b = set(biz_b.keys())

    return {
        "new":     [biz_b[n] for n in (names_b - names_a)],
        "removed": [biz_a[n] for n in (names_a - names_b)],
        "common":  [biz_b[n] for n in (names_a & names_b)],
    }
