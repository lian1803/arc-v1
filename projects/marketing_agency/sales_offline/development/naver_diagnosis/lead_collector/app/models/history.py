"""CollectionHistory ORM 모델"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.database import Base


class CollectionHistory(Base):
    __tablename__ = "collection_history"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    region           = Column(String(200), nullable=False)
    keyword          = Column(String(200), nullable=True)
    platforms        = Column(String(200), nullable=False)

    # 결과 요약
    total_count      = Column(Integer, default=0)
    verified_count   = Column(Integer, default=0)
    unverified_count = Column(Integer, default=0)
    closed_count     = Column(Integer, default=0)
    no_phone_count   = Column(Integer, default=0)

    # 상태
    status           = Column(String(20), default="진행중")   # "진행중" | "완료" | "오류" | "중단"
    error_log        = Column(Text, nullable=True)

    started_at       = Column(DateTime, default=datetime.utcnow)
    completed_at     = Column(DateTime, nullable=True)

    businesses       = relationship("Business", back_populates="session", cascade="all, delete-orphan")
