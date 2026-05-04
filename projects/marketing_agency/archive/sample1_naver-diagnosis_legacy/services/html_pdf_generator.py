"""
HTML → PDF 제안서 생성기
template_10_pastel_modern.html의 {{태그}}를 실데이터로 교체하여 PDF 생성.
Playwright 사용.
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List


TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'html_templates', 'template_10_pastel_modern.html'
)

PACKAGE_BY_GRADE = {
    'D': '시선',
    'C': '집중',
    'B': '주목',
    'A': '주목',
}

# 업종별 평균 객단가
CATEGORY_UNIT_PRICE = {
    '미용실': 65000,
    '네일': 45000,
    '식당': 25000,
    '카페': 12000,
    '피부관리': 85000,
    '학원': 300000,
    '병원': 50000,
    '치과': 150000,
    '음식점': 25000,
    '의류': 45000,
    '편의점': 8000,
    '편의/생활': 15000,
}

def get_unit_price(category: str) -> int:
    """업종별 평균 객단가 조회 (기본값: 50,000원)"""
    for key, price in CATEGORY_UNIT_PRICE.items():
        if key.lower() in category.lower():
            return price
    return 50000

PACKAGE_PRICES = {
    '시선': {'정상가': '560,000', '약정가': '380,000', '합계6개월': '2,280,000'},
    '집중': {'정상가': '860,000', '약정가': '560,000', '합계6개월': '3,360,000'},
    '주목': {'정상가': '1,270,000', '약정가': '950,000', '합계6개월': '5,700,000'},
}


class HtmlPdfGenerator:

    def __init__(self, output_dir: str = "pdf_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _parse(self, value, default=None):
        if default is None:
            default = []
        if not value:
            return default
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except Exception:
            return default

    def _build_impact_copy(self, data: Dict, rank: int, lost: int, name: str, category: str) -> str:
        """{{충격카피}} — 업종/상황별 동적 생성"""
        if rank > 10:
            return f"'{category}' 검색 시 {name}은 1페이지에도 없습니다.<br>지금 이 순간에도 손님이 다른 가게로 가고 있습니다."
        elif lost > 50:
            return f"매달 약 <strong>{lost:,}명</strong>이<br>사장님 가게를 지나쳐 경쟁사로 갑니다."
        else:
            return f"{name}은 지금<br>'있지만 보이지 않는 가게'입니다."

    def _build_diagnosis_grid(self, data: Dict) -> str:
        """{{진단그리드}} — 10개 항목 HTML 생성"""
        # 판단 기준
        photo_count = data.get('photo_count') or 0
        review_count = data.get('review_count') or 0
        blog_count = data.get('blog_count') or 0
        has_intro = data.get('has_intro') or False
        has_directions = data.get('has_directions') or False
        has_news = data.get('has_news') or False
        has_coupon = data.get('has_coupon') or False
        has_menu = data.get('has_menu') or False
        has_price = data.get('has_price') or False
        has_booking = data.get('has_booking') or False
        has_talktalk = data.get('has_talktalk') or False
        receipt_review = data.get('receipt_review') or 0
        has_kakao = data.get('has_kakao') or False
        has_instagram = data.get('has_instagram') or False

        items = [
            ('대표사진 최적화', photo_count >= 10),
            ('대표 키워드 설정', data.get('keyword_count', 0) >= 3),
            ('소개 · 오시는 길', has_intro and has_directions),
            ('알림 · 이벤트 설정', has_news and has_coupon),
            ('메뉴 · 가격 세팅', has_menu and has_price),
            ('예약 시스템 세팅', has_booking and has_talktalk),
            ('영수증 리뷰 관리', receipt_review >= 5),
            ('블로그 노출 현황', blog_count >= 5),
            ('지역 커뮤니티 연계', has_kakao),
            ('외부 채널 연동', has_instagram),
        ]

        html = ""
        for item_name, is_ok in items:
            if is_ok:
                html += f'<div class="di ok"><div class="di-s ds-ok">✓</div><div class="di-name">{item_name}</div><div class="di-tag dt-ok">양호</div></div>'
            else:
                html += f'<div class="di bad"><div class="di-s ds-bad">✗</div><div class="di-name">{item_name}</div><div class="di-tag dt-bad">미흡</div></div>'
        return html

    def _build_checklist(self, data: Dict) -> str:
        """{{체크리스트}} — 부족한 항목을 X로 표시"""
        photo_count = data.get('photo_count') or 0
        review_count = data.get('review_count') or 0
        blog_count = data.get('blog_count') or 0
        has_intro = data.get('has_intro') or False
        has_directions = data.get('has_directions') or False
        has_news = data.get('has_news') or False
        has_coupon = data.get('has_coupon') or False
        has_menu = data.get('has_menu') or False
        has_price = data.get('has_price') or False
        has_booking = data.get('has_booking') or False
        has_talktalk = data.get('has_talktalk') or False
        receipt_review = data.get('receipt_review') or 0
        has_kakao = data.get('has_kakao') or False
        has_instagram = data.get('has_instagram') or False

        items = [
            ('대표사진 최적화', photo_count >= 10),
            ('대표 키워드 설정', data.get('keyword_count', 0) >= 3),
            ('소개 · 오시는 길', has_intro and has_directions),
            ('알림 · 이벤트 설정', has_news and has_coupon),
            ('메뉴 · 가격 세팅', has_menu and has_price),
            ('예약 시스템 세팅', has_booking and has_talktalk),
            ('영수증 리뷰 관리', receipt_review >= 5),
            ('블로그 노출 현황', blog_count >= 5),
            ('지역 커뮤니티 연계', has_kakao),
            ('외부 채널 연동', has_instagram),
        ]

        html = ""
        for item_name, is_ok in items:
            if is_ok:
                html += f'<div class="checklist-item has"><div class="checklist-icon">✅</div><div class="checklist-name">{item_name}</div></div>'
            else:
                html += f'<div class="checklist-item missing"><div class="checklist-icon">❌</div><div class="checklist-name">{item_name}</div></div>'
        return html

    def _build_package_grid(self, grade: str) -> str:
        """{{패키지그리드}} — 3개 패키지 카드 HTML"""
        packages = [
            {
                'name': '시선',
                'tag': '입문',
                'regular': '560,000',
                'sale': '380,000',
                'items': ['기본정보 최적화', '핵심 키워드 세팅', '월간 성과 리포트'],
                'recommended': grade in ('D',),
            },
            {
                'name': '집중',
                'tag': '추천',
                'regular': '860,000',
                'sale': '560,000',
                'items': ['시선 패키지 전체', '전문 사진 촬영', '블로그 리뷰 등록', '리뷰 답글 대행'],
                'recommended': grade in ('C',),
            },
            {
                'name': '주목',
                'tag': '프리미엄',
                'regular': '1,270,000',
                'sale': '950,000',
                'items': ['집중 패키지 전체', '인스타그램 관리', '새소식 월 2회', '전담 매니저 배정'],
                'recommended': grade in ('B', 'A'),
            },
        ]

        html = ""
        for pkg in packages:
            rec_class = ' rec' if pkg['recommended'] else ''
            rh_class = ' rh' if pkg['recommended'] else ''
            rtag_html = f'<div class="rtag">{pkg["tag"]}</div>' if pkg['recommended'] else ''

            html += f'<div class="pc{rec_class}">'
            html += f'<div class="ph{rh_class}"><div class="pn">{pkg["name"]}</div>{rtag_html}</div>'
            html += '<div class="pb">'
            html += f'<div class="ppl" style="text-decoration:line-through;color:#ccc;font-size:11px;">월 {pkg["regular"]}원</div>'
            html += f'<div class="pp">{pkg["sale"]}만<span class="ppu">원/월 (약정)</span></div>'
            html += '<div class="ps"></div>'
            for item in pkg['items']:
                html += f'<div class="pi">{item}</div>'
            html += '</div>'
            html += '</div>'
        return html

    def _build_tags(self, data: Dict) -> Dict[str, str]:
        """data dict → {{태그}}: 값 매핑 (HTML 템플릿용)"""
        name     = data.get('business_name') or '업체명'
        category = data.get('category') or '소상공인'
        rank     = data.get('naver_place_rank') or 0
        address  = data.get('address') or '주소 미확인'
        grade    = data.get('grade') or 'D'
        lost     = data.get('estimated_lost_customers') or 0

        keywords = self._parse(data.get('keywords'))
        if not keywords:
            keywords = self._parse(data.get('related_keywords'))
        improvement_points = self._parse(data.get('improvement_points'))

        # HTML 템플릿은 "패키지" 단어를 이미 포함하므로 짧은 이름 사용
        package = PACKAGE_BY_GRADE.get(grade, '시선')
        prices  = PACKAGE_PRICES[package]

        CATEGORY_LABELS = {
            'photo': '대표사진',
            'review': '리뷰 관리',
            'blog': '블로그 리뷰',
            'info': '기본정보 완성',
            'keyword': '키워드 세팅',
            'convenience': '알림/이벤트',
            'engagement': '고객 소통',
        }
        top_issue = '개선 필요'
        if improvement_points:
            top_issue = CATEGORY_LABELS.get(
                improvement_points[0].get('category', ''), '개선 필요'
            )

        total_search  = sum(k.get('search_volume', 0) for k in keywords)
        pc_search     = int(total_search * 0.3)
        mobile_search = int(total_search * 0.7)

        # HTML 템플릿에서 "위"는 하드코딩되어 있으므로 숫자만
        rank_val = str(rank) if rank else '?'

        # {{가망고객분석}} — 짧게 (HTML에서 "경쟁사 이탈/월" 레이블이 따로 있음)
        lost_val = f'약 {lost:,}명' if lost > 0 else '분석 중'

        # 새로운 태그들을 위한 데이터 계산
        # 업종별 객단가 조회
        unit_price = get_unit_price(category)

        # 우리 업체 현황
        our_review_count = data.get('review_count') or 0
        our_photo_count = data.get('photo_count') or 0

        # 경쟁사 시뮬레이션 (상위 1위로 가정)
        # 규칙: 경쟁사는 우리보다 리뷰 5~10배, 사진 5~8배
        competitor_review_multiplier = min(max(5 + rank // 5, 5), 10)  # 순위에 따라 변동
        competitor_photo_multiplier = min(max(5 + rank // 8, 5), 8)
        competitor_review = max(our_review_count * competitor_review_multiplier, 50)
        competitor_photo = max(our_photo_count * competitor_photo_multiplier, 30)

        # 월 손실금 계산
        monthly_lost_revenue = lost * unit_price

        # 목표: 패키지 비용을 회수하기 위한 추가 고객 수
        package_monthly_price = int(prices['약정가'].replace(',', ''))
        target_customers = max((package_monthly_price + 100000) // unit_price, 2)  # 최소 2명

        # 하루 비용 (월 금액 / 30)
        daily_cost = package_monthly_price // 30

        # ROI 배수 계산 (월 손실금 / 월 투자비용)
        roi_multiple = max(monthly_lost_revenue // package_monthly_price if package_monthly_price > 0 else 1, 1)

        # 진단 날짜 (YYYY. MM. DD 형식)
        diag_date = datetime.now().strftime('%Y. %m. %d')

        # 사장님 이름 추출 (비즈니스명이 개인명일 가능성이 있으므로, 첫 1~2글자 사용)
        owner_name = name.split()[0] if ' ' in name else name[:2]

        # 등급별 CSS 클래스
        grade_class_map = {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}
        grade_class = grade_class_map.get(grade, 'd')

        # 연간 손실 고객 & 손실금
        annual_lost_customers = lost * 12
        annual_lost_revenue = monthly_lost_revenue * 12

        # 리뷰 격차
        review_gap = max(competitor_review - our_review_count, 0)

        # 백분위 (하위 XX% 계산)
        percentile = min(95, int((rank / 30) * 100))  # 순위 30 = 백분위 100

        # 종합점수 (별도 계산 또는 기존 데이터)
        total_score = data.get('total_score') or int((100 - (rank * 2)) * 0.8) + 20
        total_score = max(10, min(100, total_score))

        # 순위 설명 텍스트
        rank_desc = "가시성 낮음" if rank > 10 else "경쟁 심함"

        tags: Dict[str, str] = {
            # 기존 태그
            '{{업체명}}':       name,
            '{{업종}}':         category,
            '{{순위}}':         rank_val,
            '{{주소}}':         address,
            '{{추천패키지}}':    package,
            '{{가망고객분석}}':  lost_val,
            '{{주요문제}}':     top_issue,
            '{{전체검색량}}':    f'{total_search:,}' if total_search else '0',
            '{{PC검색량}}':      f'{pc_search:,}' if pc_search else '0',
            '{{모바일검색량}}':  f'{mobile_search:,}' if mobile_search else '0',
            '{{상호명}}':       name,
            '{{패키지}}':       package,
            '{{정상가}}':       prices['정상가'],
            '{{약정가}}':       prices['약정가'],
            '{{합계6개월}}':    prices['합계6개월'],
            '{{충격카피}}':     self._build_impact_copy(data, rank, lost, name, category),
            '{{진단날짜}}':     diag_date,
            '{{진단그리드}}':   self._build_diagnosis_grid(data),
            '{{체크리스트}}':   self._build_checklist(data),
            '{{패키지그리드}}': self._build_package_grid(grade),

            # 표지 새 태그
            '{{사장님이름}}':   owner_name,
            '{{등급_클래스}}':  grade_class,
            '{{종합점수}}':     str(total_score),
            '{{등급}}':        grade,
            '{{백분위}}':      str(percentile),
            '{{추정손실고객수}}': str(lost),
            '{{순위설명}}':     rank_desc,

            # 연간 손실
            '{{연간손실고객}}': f'{annual_lost_customers:,}',
            '{{연간손실금}}':   f'{annual_lost_revenue:,}',

            # 경쟁사 비교
            '{{우리리뷰}}':     str(our_review_count),
            '{{우리사진}}':     str(our_photo_count),
            '{{경쟁사리뷰}}':   f'{competitor_review:,}',
            '{{경쟁사사진}}':   str(competitor_photo),
            '{{리뷰격차}}':     str(review_gap),

            # 손실 계산
            '{{가망고객수}}':   str(lost),
            '{{객단가}}':       f'{unit_price:,}',
            '{{월손실금}}':     f'{monthly_lost_revenue:,}',
            '{{목표명수}}':     str(target_customers),

            # CTA
            '{{하루비용}}':     f'{daily_cost:,}',
            '{{월비용}}':       f'{package_monthly_price:,}',
            '{{roi배수}}':      f'{roi_multiple}',
            '{{본전명수}}':     str(target_customers),
            '{{카톡번호}}':     '010-5641-1803',
            '{{검색량설명}}':   '월 검색 수',
        }

        # 키워드 테이블 (7행)
        for i in range(1, 8):
            kw  = keywords[i - 1] if i - 1 < len(keywords) else {}
            vol = kw.get('search_volume', 0)
            tags[f'{{{{키워드{i}}}}}'] = kw.get('keyword', '-') or '-'
            tags[f'{{{{검색량{i}}}}}'] = f'{vol:,}' if vol else '-'

        return tags

    def render_html(self, data: Dict) -> str:
        """템플릿 HTML에 실데이터 주입 후 반환"""
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            html = f.read()
        for tag, value in self._build_tags(data).items():
            html = html.replace(tag, str(value))
        return html

    def generate(self, data: Dict[str, Any]) -> str:
        """동기 래퍼 — 내부에서 asyncio 실행"""
        return asyncio.run(self._generate_async(data))

    async def _generate_async(self, data: Dict[str, Any]) -> str:
        from playwright.async_api import async_playwright

        html = self.render_html(data)

        safe_name = (data.get('business_name') or 'report') \
            .replace('/', '_').replace('\\', '_').replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename  = f"{safe_name}_{timestamp}.pdf"
        output_path = os.path.abspath(os.path.join(self.output_dir, filename))

        # Playwright가 로컬 파일로 띄울 임시 HTML
        tmp_html = output_path.replace('.pdf', '_tmp.html')
        with open(tmp_html, 'w', encoding='utf-8') as f:
            f.write(html)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page    = await browser.new_page()
            # file:/// URI (Windows 경로 슬래시 통일, 한글 인코딩 안 함)
            file_uri = 'file:///' + tmp_html.replace('\\', '/')
            await page.goto(file_uri)
            # Google Fonts 등 외부 리소스 로드 대기
            await page.wait_for_load_state('networkidle', timeout=15000)
            await page.pdf(
                path=output_path,
                format='A4',
                print_background=True,
                margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
            )
            await browser.close()

        try:
            os.remove(tmp_html)
        except Exception:
            pass

        return filename
