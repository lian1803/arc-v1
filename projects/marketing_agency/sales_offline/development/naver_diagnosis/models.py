"""
SQLAlchemy 2.0 Mapped 스타일 모델 정의
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class DiagnosisHistory(Base):
    """진단 이력 테이블"""
    __tablename__ = "diagnosis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    place_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    place_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # 수집 데이터
    photo_count: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)  # 영수증+방문자 리뷰 합계
    blog_review_count: Mapped[int] = mapped_column(Integer, default=0)
    has_menu: Mapped[bool] = mapped_column(Boolean, default=False)
    has_hours: Mapped[bool] = mapped_column(Boolean, default=False)
    has_price: Mapped[bool] = mapped_column(Boolean, default=False)

    # 키워드 데이터 [{"keyword": "강남 카페", "search_volume": 12000}]
    keywords: Mapped[List] = mapped_column(JSON, default=list)

    # 소개/오시는 길
    has_intro: Mapped[bool] = mapped_column(Boolean, default=False)
    intro_text_length: Mapped[int] = mapped_column(Integer, default=0)
    has_directions: Mapped[bool] = mapped_column(Boolean, default=False)
    directions_text_length: Mapped[int] = mapped_column(Integer, default=0)

    # 편의 기능
    has_booking: Mapped[bool] = mapped_column(Boolean, default=False)   # 네이버 예약
    has_talktalk: Mapped[bool] = mapped_column(Boolean, default=False)  # 톡톡
    has_smartcall: Mapped[bool] = mapped_column(Boolean, default=False) # 스마트콜

    # 알림/쿠폰/새소식
    has_coupon: Mapped[bool] = mapped_column(Boolean, default=False)
    has_news: Mapped[bool] = mapped_column(Boolean, default=False)

    # 메뉴 상세
    menu_count: Mapped[int] = mapped_column(Integer, default=0)
    has_menu_description: Mapped[bool] = mapped_column(Boolean, default=False)

    # 리뷰 상세
    receipt_review_count: Mapped[int] = mapped_column(Integer, default=0)
    visitor_review_count: Mapped[int] = mapped_column(Integer, default=0)
    has_owner_reply: Mapped[bool] = mapped_column(Boolean, default=False)

    # 외부 채널
    has_instagram: Mapped[bool] = mapped_column(Boolean, default=False)
    has_kakao: Mapped[bool] = mapped_column(Boolean, default=False)

    # 순위/키워드 확장
    naver_place_rank: Mapped[int] = mapped_column(Integer, default=0)
    related_keywords: Mapped[List] = mapped_column(JSON, default=list)

    # 점수
    photo_score: Mapped[float] = mapped_column(Float, default=0.0)
    review_score: Mapped[float] = mapped_column(Float, default=0.0)
    blog_score: Mapped[float] = mapped_column(Float, default=0.0)
    keyword_score: Mapped[float] = mapped_column(Float, default=0.0)
    info_score: Mapped[float] = mapped_column(Float, default=0.0)
    convenience_score: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    grade: Mapped[str] = mapped_column(String(2), default="D")

    # 개선 포인트 [{"category": "photo", "message": "..."}]
    improvement_points: Mapped[List] = mapped_column(JSON, default=list)

    # PPT 파일명
    ppt_filename: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # 수동 입력 여부
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── 신규 필드 (업그레이드) ──────────────────────────────────
    # 업종 타입 (자동 감지된 업종: 미용실/식당/카페/학원/default)
    industry_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 영업 우선순위 태그 (1순위/2순위/패스)
    priority_tag: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # 경쟁사 평균 리뷰 수 (크롤링 또는 폴백)
    competitor_avg_review: Mapped[int] = mapped_column(Integer, default=0)

    # 경쟁사 평균 사진 수
    competitor_avg_photo: Mapped[int] = mapped_column(Integer, default=0)

    # 경쟁사 평균 블로그 수
    competitor_avg_blog: Mapped[int] = mapped_column(Integer, default=0)

    # 경쟁사 업체명 및 브랜드 검색량
    competitor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    competitor_brand_search_volume: Mapped[int] = mapped_column(Integer, default=0)
    own_brand_search_volume: Mapped[int] = mapped_column(Integer, default=0)

    # 매달 손실 추정 고객 수
    estimated_lost_customers: Mapped[int] = mapped_column(Integer, default=0)

    # 영업 메시지 캐시 (JSON: {first, second, third, fourth})
    messages: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── AI 분석 결과 (신규) ─────────────────────────────────────
    # 크롤링된 리뷰 텍스트 (감성 분석 원본)
    review_texts: Mapped[List] = mapped_column(JSON, default=list)
    # 크롤링된 사진 URL 목록 (품질 분석 원본)
    photo_urls: Mapped[List] = mapped_column(JSON, default=list)
    # 저장 수 (북마크)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0)
    # 리뷰 감성 점수 (0~100, 높을수록 긍정)
    review_sentiment_score: Mapped[float] = mapped_column(Float, default=50.0)
    # 부정 리뷰 비율 (0.0~1.0)
    review_negative_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    # 주요 불만 사항 (AI 추출)
    review_main_complaints: Mapped[List] = mapped_column(JSON, default=list)
    # 사진 품질 점수 (0~100)
    photo_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    # 사진 품질 문제점 목록
    photo_quality_issues: Mapped[List] = mapped_column(JSON, default=list)
    # AI가 다듬은 1차 메시지 (원본 대체용)
    ai_first_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── 신규 필드 (점수/크롤링 고도화) ──────────────────────────────
    # 사장님 답글률 (최근 20개 리뷰 기준, 0.0~1.0)
    owner_reply_rate: Mapped[float] = mapped_column(Float, default=0.0)
    # 소개글 전문
    intro_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 최근 30일 리뷰 수
    review_last_30d_count: Mapped[int] = mapped_column(Integer, default=0)
    # 최근 90일 리뷰 수
    review_last_90d_count: Mapped[int] = mapped_column(Integer, default=0)
    # 새소식 마지막 게시일 (실제 날짜, news_last_days 보완)
    news_last_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "business_name": self.business_name,
            "place_id": self.place_id,
            "address": self.address,
            "category": self.category,
            "place_url": self.place_url,
            "photo_count": self.photo_count,
            "review_count": self.review_count,
            "blog_review_count": self.blog_review_count,
            "has_menu": self.has_menu,
            "has_hours": self.has_hours,
            "has_price": self.has_price,
            "keywords": self.keywords,
            # 소개/오시는 길
            "has_intro": self.has_intro,
            "intro_text_length": self.intro_text_length,
            "has_directions": self.has_directions,
            "directions_text_length": self.directions_text_length,
            # 편의 기능
            "has_booking": self.has_booking,
            "has_talktalk": self.has_talktalk,
            "has_smartcall": self.has_smartcall,
            # 알림/쿠폰/새소식
            "has_coupon": self.has_coupon,
            "has_news": self.has_news,
            # 메뉴 상세
            "menu_count": self.menu_count,
            "has_menu_description": self.has_menu_description,
            # 리뷰 상세
            "receipt_review_count": self.receipt_review_count,
            "visitor_review_count": self.visitor_review_count,
            "has_owner_reply": self.has_owner_reply,
            # 외부 채널
            "has_instagram": self.has_instagram,
            "has_kakao": self.has_kakao,
            # 순위/키워드 확장
            "naver_place_rank": self.naver_place_rank,
            "related_keywords": self.related_keywords,
            # 점수
            "photo_score": self.photo_score,
            "review_score": self.review_score,
            "blog_score": self.blog_score,
            "keyword_score": self.keyword_score,
            "info_score": self.info_score,
            "convenience_score": self.convenience_score,
            "engagement_score": self.engagement_score,
            "total_score": self.total_score,
            "grade": self.grade,
            "improvement_points": self.improvement_points,
            "ppt_filename": self.ppt_filename,
            "is_manual": self.is_manual,
            # 신규 필드
            "industry_type": self.industry_type,
            "priority_tag": self.priority_tag,
            "competitor_avg_review": self.competitor_avg_review,
            "competitor_avg_photo": self.competitor_avg_photo,
            "competitor_avg_blog": self.competitor_avg_blog,
            "competitor_name": self.competitor_name,
            "competitor_brand_search_volume": self.competitor_brand_search_volume,
            "own_brand_search_volume": self.own_brand_search_volume,
            "estimated_lost_customers": self.estimated_lost_customers,
            "messages": self.messages,
            # AI 분석 결과
            "review_texts": self.review_texts,
            "photo_urls": self.photo_urls,
            "bookmark_count": self.bookmark_count,
            "review_sentiment_score": self.review_sentiment_score,
            "review_negative_ratio": self.review_negative_ratio,
            "review_main_complaints": self.review_main_complaints,
            "photo_quality_score": self.photo_quality_score,
            "photo_quality_issues": self.photo_quality_issues,
            "ai_first_message": self.ai_first_message,
            # 신규 필드
            "owner_reply_rate": self.owner_reply_rate,
            "intro_text": self.intro_text,
            "review_last_30d_count": self.review_last_30d_count,
            "review_last_90d_count": self.review_last_90d_count,
            "news_last_date": self.news_last_date.isoformat() if self.news_last_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CrawlJob(Base):
    """크롤링 작업 상태 테이블"""
    __tablename__ = "crawl_job"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # status: pending/searching/crawling/analyzing/generating/done/failed
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    result_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # DiagnosisHistory.id
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "status": self.status,
            "progress": self.progress,
            "result_id": self.result_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BusinessPriority(Base):
    """
    업체별 영업 우선순위 관리 테이블.
    DiagnosisHistory.priority_tag와 별도로, 히스토리 없이 업체 자체에 메모 가능.
    """
    __tablename__ = "business_priority"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 우선순위: 1순위 / 2순위 / 패스
    priority_tag: Mapped[str] = mapped_column(String(20), default="2순위")

    # 연결된 DiagnosisHistory ID (선택)
    diagnosis_history_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 메모 (영업 진행 상황, 대화 내용 등)
    memo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 영업 단계: 미연락 / 1차발송 / 2차발송 / 3차발송 / 계약완료 / 거절
    sales_stage: Mapped[str] = mapped_column(String(30), default="미연락")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "business_name": self.business_name,
            "address": self.address,
            "category": self.category,
            "priority_tag": self.priority_tag,
            "diagnosis_history_id": self.diagnosis_history_id,
            "memo": self.memo,
            "sales_stage": self.sales_stage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BenchmarkPremium(Base):
    """
    상위권 벤치마크 테이블 (Phase 3)
    - 서울 핫플 상위권 업체들 수집
    - 업종별 30~50개 = 총 300~500개 선별
    - Gemini Vision으로 컨셉 분석
    """
    __tablename__ = "benchmark_premium"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 기본 정보
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # 미용실/네일/피부관리/식당/카페 등
    region: Mapped[str] = mapped_column(String(50), nullable=False)  # 강남/홍대/성수/이태원/압구정/한남/가로수길
    place_name: Mapped[str] = mapped_column(String(200), nullable=False)
    place_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    place_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # 네이버 플레이스 순위
    naver_place_rank: Mapped[int] = mapped_column(Integer, default=0)  # 검색 순위

    # 수집 데이터 (네이버)
    photo_count: Mapped[int] = mapped_column(Integer, default=0)
    receipt_review_count: Mapped[int] = mapped_column(Integer, default=0)
    visitor_review_count: Mapped[int] = mapped_column(Integer, default=0)
    blog_review_count: Mapped[int] = mapped_column(Integer, default=0)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0)
    keyword_rating_review_count: Mapped[int] = mapped_column(Integer, default=0)

    # 정보 완성도
    has_menu: Mapped[bool] = mapped_column(Boolean, default=False)
    has_hours: Mapped[bool] = mapped_column(Boolean, default=False)
    has_price: Mapped[bool] = mapped_column(Boolean, default=False)
    has_intro: Mapped[bool] = mapped_column(Boolean, default=False)
    has_directions: Mapped[bool] = mapped_column(Boolean, default=False)

    # 편의 기능
    has_booking: Mapped[bool] = mapped_column(Boolean, default=False)
    has_talktalk: Mapped[bool] = mapped_column(Boolean, default=False)
    has_smartcall: Mapped[bool] = mapped_column(Boolean, default=False)
    has_coupon: Mapped[bool] = mapped_column(Boolean, default=False)
    has_news: Mapped[bool] = mapped_column(Boolean, default=False)

    # 외부 채널
    has_owner_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    has_instagram: Mapped[bool] = mapped_column(Boolean, default=False)
    has_kakao: Mapped[bool] = mapped_column(Boolean, default=False)

    # 키워드 데이터 [{"keyword": "강남 카페", "volume": 12000}, ...]
    keywords: Mapped[List] = mapped_column(JSON, default=list)

    # 샘플 리뷰 텍스트 (최대 10개)
    review_text_samples: Mapped[List] = mapped_column(JSON, default=list)

    # 사진 URL 목록 (최대 15~20개)
    photo_urls: Mapped[List] = mapped_column(JSON, default=list)

    # Gemini Vision 분석 결과 (사진 처음 10~20장)
    # {
    #   "color_tone": "웜|쿨|모노|비비드",
    #   "mood": "미니멀|빈티지|럭셔리|캐주얼|내추럴|모던",
    #   "style_ratio": {"인물": 0.3, "공간": 0.5, "디테일": 0.2},
    #   "target_persona": "20대 여성|30대 남성|패밀리|프리미엄|캐주얼"
    # }
    concept_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 메타데이터
    crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "region": self.region,
            "place_name": self.place_name,
            "place_id": self.place_id,
            "place_url": self.place_url,
            "address": self.address,
            "naver_place_rank": self.naver_place_rank,
            "photo_count": self.photo_count,
            "receipt_review_count": self.receipt_review_count,
            "visitor_review_count": self.visitor_review_count,
            "blog_review_count": self.blog_review_count,
            "bookmark_count": self.bookmark_count,
            "keyword_rating_review_count": self.keyword_rating_review_count,
            "has_menu": self.has_menu,
            "has_hours": self.has_hours,
            "has_price": self.has_price,
            "has_intro": self.has_intro,
            "has_directions": self.has_directions,
            "has_booking": self.has_booking,
            "has_talktalk": self.has_talktalk,
            "has_smartcall": self.has_smartcall,
            "has_coupon": self.has_coupon,
            "has_news": self.has_news,
            "has_owner_reply": self.has_owner_reply,
            "has_instagram": self.has_instagram,
            "has_kakao": self.has_kakao,
            "keywords": self.keywords,
            "review_text_samples": self.review_text_samples,
            "photo_urls": self.photo_urls,
            "concept_tags": self.concept_tags,
            "crawled_at": self.crawled_at.isoformat() if self.crawled_at else None,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── CRM 테이블 ─────────────────────────────────────────────────────────────────

class CRMBusiness(Base):
    """영업 CRM 업체 테이블"""
    __tablename__ = "crm_businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    place_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="1차_발송_대기")
    naver_diagnosis_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    package: Mapped[Optional[str]] = mapped_column(String(10), default="A")
    contract_status: Mapped[Optional[str]] = mapped_column(String(30), default="진단중")
    monthly_fee: Mapped[int] = mapped_column(Integer, default=380000)
    manager: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    upsell_stage: Mapped[int] = mapped_column(Integer, default=0)

    # ── 3가지 신규 컬럼 (2026-04-20) ──
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 지역 (양주, 의정부, 파주 등)
    excel_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 엑셀 DB의 010 번호
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 업종
    today_selected: Mapped[bool] = mapped_column(Boolean, default=False)  # 오늘 영업 선택 여부
    contacted_today: Mapped[bool] = mapped_column(Boolean, default=False)  # 오늘 연락 완료 여부
    last_reset_date: Mapped[Optional[date]] = mapped_column(DateTime, nullable=True)  # 마지막 reset 날짜

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "phone": self.phone, "name": self.name,
            "location": self.location, "pdf_path": self.pdf_path,
            "place_url": self.place_url, "status": self.status,
            "naver_diagnosis_id": self.naver_diagnosis_id,
            "memo": self.memo, "package": self.package,
            "contract_status": self.contract_status,
            "monthly_fee": self.monthly_fee, "manager": self.manager,
            "upsell_stage": self.upsell_stage,
            "region": self.region, "excel_phone": self.excel_phone,
            "industry": self.industry, "today_selected": self.today_selected,
            "contacted_today": self.contacted_today,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CRMConversation(Base):
    """CRM 업체별 대화 기록"""
    __tablename__ = "crm_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("crm_businesses.id"), nullable=False)
    speaker: Mapped[str] = mapped_column(String(20), nullable=False)  # 'AI' | '고객'
    message: Mapped[str] = mapped_column(Text, nullable=False)
    message_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "business_id": self.business_id,
            "speaker": self.speaker, "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CRMMessageSequence(Base):
    """CRM 업체별 1차~4차 메시지 시퀀스"""
    __tablename__ = "crm_message_sequences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("crm_businesses.id"), nullable=False)
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "business_id": self.business_id,
            "sequence_num": self.sequence_num, "message": self.message,
        }
