"""앱 전역 설정 및 상수"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH  = DATA_DIR / "db" / "local.db"
EXPORT_DIR = DATA_DIR / "exports"
LOG_DIR  = BASE_DIR / "logs"

# 디렉토리 자동 생성
for d in [DATA_DIR / "db", EXPORT_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 네이버 API (없으면 Playwright 폴백)
NAVER_CLIENT_ID     = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

# 카카오 API (없으면 Playwright 폴백)
KAKAO_REST_API_KEY  = os.getenv("KAKAO_REST_API_KEY", "")

# User Agents
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)
DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 수집 제한
MAX_PER_SESSION = 999999  # 제한 없음
MAX_PER_DAY     = 999999  # 제한 없음

# 플랫폼별 딜레이 (초)
DELAY_NAVER   = 0.8
DELAY_KAKAO   = 0.8
DELAY_GOOGLE  = 1.2
DELAY_INSTA   = 0.6
DELAY_DAANGN  = 0.6

# 제외할 대형 프랜차이즈 / 공공기관
FRANCHISE_EXCLUDE = {
    "스타벅스", "이마트", "홈플러스", "롯데마트", "코스트코", "다이소",
    "맥도날드", "버거킹", "롯데리아", "KFC", "서브웨이", "맘스터치",
    "GS25", "CU", "세븐일레븐", "미니스톱", "이마트24",
    "올리브영", "무신사", "탑텐", "유니클로", "자라", "H&M",
    "크린토피아", "한화리조트", "대명리조트",
    "국군복지단", "하나로마트", "경기도의료원",
    "BBQ", "교촌치킨", "bhc", "네네치킨", "처갓집",
    "파리바게뜨", "뚜레쥬르", "베스킨라빈스",
    "CJ", "삼성", "현대", "LG",
}

# 업종 카테고리 (수집 시 순차 검색)
DEFAULT_CATEGORIES = [
    "음식점", "카페", "미용실", "네일샵", "병원", "학원",
    "헬스장", "필라테스", "요가", "마트", "세탁소", "꽃집",
    "약국", "치과", "피부과", "노래방", "베이커리", "부동산",
    "숙박", "자동차수리", "인테리어", "옷가게", "안경원",
    "펜션", "고깃집", "닭갈비", "횟집", "술집", "편의점",
]
