"""Business ORM 모델"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    session_id       = Column(Integer, ForeignKey("collection_history.id"), nullable=False)

    # 핵심 데이터
    name             = Column(String(200), nullable=False)
    phone            = Column(String(20),  nullable=True)
    phone_status     = Column(String(20),  default="확인")      # "확인" | "번호미확인"
    insta_url        = Column(String(500), nullable=True)
    naver_place_url  = Column(String(500), nullable=True)
    daangn_url       = Column(String(500), nullable=True)

    # 수집 메타
    sources          = Column(String(200), nullable=False)       # "네이버,카카오맵" (콤마 구분)
    category         = Column(String(100), nullable=True)
    raw_address      = Column(String(500), nullable=True)

    # 검증 상태
    verify_status    = Column(String(20),  default="미확인")     # "확인됨" | "미확인" | "폐업의심"

    # 타임스탬프
    collected_at     = Column(DateTime, default=datetime.utcnow)
    verified_at      = Column(DateTime, nullable=True)

    session          = relationship("CollectionHistory", back_populates="businesses")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone or "",
            "phone_status": self.phone_status,
            "insta_url": self.insta_url or "",
            "naver_place_url": self.naver_place_url or "",
            "daangn_url": self.daangn_url or "",
            "sources": self.sources,
            "category": self.category or "",
            "raw_address": self.raw_address or "",
            "verify_status": self.verify_status,
            "collected_at": self.collected_at.strftime("%Y-%m-%d %H:%M") if self.collected_at else "",
        }
