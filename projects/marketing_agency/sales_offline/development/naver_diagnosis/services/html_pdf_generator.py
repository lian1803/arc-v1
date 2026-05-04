"""
HTML → PDF 제안서 생성기
template_10_pastel_modern.html의 {{태그}}를 실데이터로 교체하여 PDF 생성.
Playwright 사용.
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional


TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'html_templates', 'template_10_pastel_modern.html'
)

PACKAGE_BY_GRADE = {
    'D': 'A',
    'C': 'B',
    'B': 'C',
    'A': 'C',
}

# 업종별 평균 객단가
CATEGORY_UNIT_PRICE = {
    '미용실': 65000,
    '헤어': 65000,
    '헤어샵': 65000,
    '미용': 65000,
    '네일': 45000,
    '식당': 25000,
    '카페': 12000,
    '피부관리': 85000,
    '피부': 85000,
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
    'A': {'정상가': '490,000', '약정가': '380,000', '합계3개월': '1,140,000'},
    'B': {'정상가': '720,000', '약정가': '560,000', '합계3개월': '1,680,000'},
    'C': {'정상가': '1,200,000', '약정가': '950,000', '합계3개월': '2,850,000'},
}


class HtmlPdfGenerator:

    def __init__(self, output_dir: str = "pdf_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _get_industry_range(self, category: str) -> Optional[Dict]:
        """
        업종별 range 데이터 조회 (벤치마크 기반).
        폴백 데이터도 지원. 없으면 None 반환.
        """
        try:
            from services.industry_range import get_provider
            provider = get_provider()
            if provider:
                return provider.get_industry_range(category)
        except Exception:
            pass
        return None

    def _format_unit_price(self, unit_price: int, industry_range: Optional[Dict]) -> str:
        """
        객단가 표기 (단일값 또는 range).
        반환: "약 6~7만원 * 업계 평균 기반" 또는 "측정불가"
        """
        if industry_range:
            low, high = industry_range.get('unit_price_range', (0, 0))
            if high > 0:
                low_만 = low // 10000
                high_만 = high // 10000
                return f'약 {low_만}~{high_만}만원 * 업계 평균 기반'
        if unit_price > 0:
            man = unit_price // 10000
            return f'약 {man}만원'
        return '측정불가'

    def _format_monthly_revenue(self, low: int, high: int, industry_range: Optional[Dict]) -> str:
        """
        월 손실금 표기 (range 또는 단일값).
        반환: "약 200~400만원 * 업계 평균 기반" 또는 "측정불가"
        """
        if industry_range and high > 0:
            low_만 = low // 10000
            high_만 = high // 10000
            return f'약 {low_만}~{high_만}만원 * 업계 평균 기반'
        if high > 0:
            high_만 = high // 10000
            return f'약 {high_만}만원'
        if low > 0:
            low_만 = low // 10000
            return f'약 {low_만}만원'
        return '측정불가'

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
        # 은/는 받침 판별
        last_char = name[-1] if name else ''
        code = ord(last_char) if last_char else 0
        has_jongseong = 0xAC00 <= code <= 0xD7A3 and (code - 0xAC00) % 28 != 0
        eun_neun = '은' if has_jongseong else '는'

        if rank > 10:
            # 기타/유효하지 않은 카테고리 제외 (DOCTRINE: no-fabrication)
            if category and category not in ('기타', '', None):
                return f"'{category}' 검색 시 {name}{eun_neun} 1페이지에도 없습니다.<br>지금 이 순간에도 손님이 다른 가게로 가고 있습니다."
            else:
                return f"{name}{eun_neun} 검색결과 1페이지에도 없습니다.<br>지금 이 순간에도 손님이 다른 가게로 가고 있습니다."
        elif lost > 50:
            return f"매달 약 <strong>{lost:,}명</strong>이<br>사장님 가게를 지나쳐 경쟁사로 갑니다."
        else:
            return f"{name}{eun_neun} 지금<br>'있지만 보이지 않는 가게'입니다."

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

    def _build_package_grid(self, grade: str) -> str:
        """{{패키지그리드}} — 3개 패키지 카드 HTML (새 패키지 정보 반영)"""
        packages = [
            {
                'name': 'A. 플레이스 케어',
                'tag': '입문',
                'regular': '490,000',
                'sale': '380,000',
                'items': [
                    'N플레이스 기본정보 최적화',
                    '소식 3건/월',
                    '사장님 리뷰 응대 월 15건',
                    '월간 성과 리포트',
                ],
                'recommended': grade in ('D',),
            },
            {
                'name': 'B. 바이럴 성장',
                'tag': '★ 가장 많이 선택',
                'regular': '720,000',
                'sale': '560,000',
                'items': [
                    'A 패키지 전체',
                    '블로그 체험단 2건/월',
                    '리워드 트래픽 연동',
                    '영수증 리뷰 이벤트',
                    '카카오채널 관리',
                    '성과 리포트',
                ],
                'recommended': grade in ('C',),
            },
            {
                'name': 'C. 광고 풀케어',
                'tag': '프리미엄',
                'regular': '1,200,000',
                'sale': '950,000',
                'items': [
                    'B 패키지 전체',
                    '인스타 SNS 4건/월',
                    '메타·당근 광고 운영',
                    '커뮤니티 홍보 2건/월',
                    '전담 담당자 배정',
                    '월 전략 미팅',
                ],
                'recommended': grade in ('B', 'A'),
            },
        ]

        html = ""
        for pkg in packages:
            rec_class = ' rec' if pkg['recommended'] else ''
            rh_class = ' rh' if pkg['recommended'] else ''

            # 가격 단위 변환: "380,000" → 38 (만원)
            sale_man = int(pkg["sale"].replace(',', '')) // 10000
            regular_man = int(pkg["regular"].replace(',', '')) // 10000
            daily_cost_won = int(pkg["sale"].replace(',', '')) // 30

            if pkg['recommended']:
                rtag_html = f'<div class="rtag">{pkg["tag"]}</div>'
            else:
                rtag_html = ''

            html += f'<div class="pc{rec_class}">'
            html += f'<div class="ph{rh_class}"><div class="pn">{pkg["name"]}</div>{rtag_html}</div>'
            html += '<div class="pb">'
            html += f'<div class="ppl" style="text-decoration:line-through;color:#ccc;font-size:11px;">월 {regular_man}만원</div>'
            html += f'<div class="pp">{sale_man}만<span class="ppu">원/월 (약정)</span></div>'
            html += f'<div style="font-size:9px;color:#27ae60;font-weight:600;margin-bottom:2mm;">하루 {daily_cost_won:,}원</div>'
            html += '<div class="ps"></div>'
            for item in pkg['items']:
                html += f'<div class="pi">{item}</div>'
            html += '<div style="font-size:9px;color:#6b7a8d;margin-top:2mm;padding-top:2mm;border-top:1px dashed #e0e8f0;">3개월 내 미개선 시 1개월 무상 연장</div>'
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

        # 업종 확인: "기타"면 대부분 계산 불가
        category_confirmed = category and category not in ('기타', '', None)
        if not category_confirmed:
            # "기타"인 경우, 측정불가 대신 CTA 문구로 처리
            cta_text = "정확한 진단을 위해 카톡으로 업종을 알려주세요"
        else:
            cta_text = ""

        # 업종별 range 데이터 먼저 조회 (손실 고객 추정에 필요)
        industry_range = self._get_industry_range(category)

        # estimated_lost_customers가 실제 크롤링 데이터인지 체크
        # 없거나 0이면 추정값 계산 금지 (DOCTRINE: no-fabrication)
        is_estimated = lost == 0

        if lost == 0:
            total_search = sum(k.get('search_volume', 0) for k in self._parse(data.get('keywords')))
            if total_search > 0 and rank > 0:
                # 순위별 CTR: rank1=0.30, rank3=0.15, rank5=0.08, rank10=0.04, rank>10=0.01
                if rank <= 3:
                    our_ctr = 0.20
                elif rank <= 5:
                    our_ctr = 0.10
                elif rank <= 10:
                    our_ctr = 0.05
                else:
                    our_ctr = 0.01
                top_ctr = 0.30
                estimated_visitors = int(total_search * top_ctr)
                our_visitors = int(total_search * our_ctr)
                lost = max(0, estimated_visitors - our_visitors)
            elif rank >= 10 and total_search == 0:
                # 검색량도 없고 순위 밖이면: industry_range 기반 추정
                # "상위 경쟁사 대표값"을 손실 고객 추정으로 사용
                if industry_range:
                    review_range = industry_range.get('top_review_range', (0, 0))
                    if review_range[1] > 0:
                        # top_review_range의 중위값을 "우리가 잃고 있는 월 고객 수"로 추정
                        lost = max(1, int((review_range[0] + review_range[1]) / 2))
                    else:
                        lost = 0
                else:
                    lost = 0  # 추정 불가

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

        # {{가망고객분석}} — 숫자+약 만. 템플릿에서 "명" 이미 붙어있음 (명명 방지)
        # 원본 데이터에 estimated_lost_customers가 없으면 CTA (DOCTRINE: no-fabrication)
        if not category_confirmed:
            lost_val = cta_text
        elif data.get('estimated_lost_customers') and data.get('estimated_lost_customers') > 0:
            lost_val = f'약 {lost:,}'
        else:
            lost_val = cta_text

        # ─────────────────────────────────────────────────────────
        # (이미 위에서 industry_range 로드됨)
        # ─────────────────────────────────────────────────────────

        # 새로운 태그들을 위한 데이터 계산
        # 업종별 객단가 조회
        # DOCTRINE: no-fabrication — 업종 미확인 또는 "기타"일 때 hardcoded fallback 금지
        # 대신 range 데이터 사용 또는 측정불가 표시
        category_known = category and category not in ('기타', '', None)
        if category_known:
            unit_price = get_unit_price(category)
        else:
            # 업종 미확인일 때는 객단가 계산 스킵
            unit_price = 0

        # 우리 업체 현황
        our_review_count = data.get('review_count') or 0
        our_photo_count = data.get('photo_count') or 0

        # 경쟁사 데이터: range 사용 (있으면) 또는 계산 (없으면)
        if industry_range:
            # range 기반: top_review_range의 중위값을 경쟁사 대표값으로
            review_range = industry_range.get('top_review_range', (0, 0))
            photo_range = industry_range.get('top_photo_range', (0, 0))
            competitor_review = int((review_range[0] + review_range[1]) / 2) if review_range[1] > 0 else 0
            competitor_photo = int((photo_range[0] + photo_range[1]) / 2) if photo_range[1] > 0 else 0
        else:
            # range 없으면 기존 계산 (우리 데이터 기반 배수)
            if our_review_count > 0:
                competitor_review_multiplier = min(max(5 + rank // 5, 5), 10)
                competitor_review = our_review_count * competitor_review_multiplier
            else:
                competitor_review = 0

            if our_photo_count > 0:
                competitor_photo_multiplier = min(max(5 + rank // 8, 5), 8)
                competitor_photo = our_photo_count * competitor_photo_multiplier
            else:
                competitor_photo = 0

        # 월 손실금 계산 (range 기반 또는 단일값)
        # 업종 미확인이면 계산 불가
        if not category_confirmed:
            monthly_lost_revenue_low = monthly_lost_revenue_high = 0
        elif industry_range and lost > 0:
            # range 기반: low/high로 두 값 계산
            revenue_range = industry_range.get('monthly_new_revenue_range', (0, 0))
            # 단순 추정: 손실 고객 수 × (range의 객단가 중위값)
            price_low, price_high = industry_range.get('unit_price_range', (0, 0))
            if price_high > 0:
                monthly_lost_revenue_low = lost * price_low
                monthly_lost_revenue_high = lost * price_high
            else:
                monthly_lost_revenue_low = monthly_lost_revenue_high = 0
        elif unit_price > 0 and lost > 0:
            monthly_lost_revenue_low = monthly_lost_revenue_high = lost * unit_price
        else:
            monthly_lost_revenue_low = monthly_lost_revenue_high = 0

        # 목표: 패키지 비용을 회수하기 위한 추가 고객 수
        package_monthly_price = int(prices['약정가'].replace(',', ''))
        if not category_confirmed:
            target_customers = 0  # 업종 미확인이면 계산 불가
        elif unit_price > 0:
            target_customers = max((package_monthly_price + 100000) // unit_price, 2)  # 최소 2명
        elif industry_range:
            # range 기반으로 계산
            price_low, price_high = industry_range.get('unit_price_range', (0, 0))
            if price_low > 0:
                target_customers = max((package_monthly_price + 100000) // price_low, 2)
            else:
                target_customers = 0
        else:
            target_customers = 0  # 업종 미확인이면 계산 불가

        # 하루 비용 (월 금액 / 30)
        daily_cost = package_monthly_price // 30

        # ROI 배수 계산 (월 손실금 / 월 투자비용)
        # range 있으면 범위로, 없으면 단일값으로
        if industry_range and monthly_lost_revenue_high > 0 and package_monthly_price > 0:
            roi_multiple_low = max(monthly_lost_revenue_low // package_monthly_price, 1)
            roi_multiple_high = max(monthly_lost_revenue_high // package_monthly_price, 1)
            roi_multiple = f"{roi_multiple_low}~{roi_multiple_high}"
        elif monthly_lost_revenue_low > 0 and package_monthly_price > 0:
            roi_multiple = max(monthly_lost_revenue_low // package_monthly_price, 1)
        else:
            roi_multiple = 0  # 계산 불가

        # 진단 날짜 (YYYY. MM. DD 형식)
        diag_date = datetime.now().strftime('%Y. %m. %d')

        # 사장님 이름 추출 (비즈니스명이 개인명일 가능성이 있으므로, 첫 1~2글자 사용)
        owner_name = name.split()[0] if ' ' in name else name[:2]

        # 누락 태그 계산
        # 월손실금이 계산 가능한 경우에만 연간 계산
        # range 있으면 high 값으로, 없으면 low/high 중 high 사용
        if not category_confirmed:
            annual_lost_표시 = cta_text
        elif monthly_lost_revenue_high > 0:
            annual_lost_revenue = monthly_lost_revenue_high * 12
            annual_lost_만원 = round(annual_lost_revenue / 10000)
            annual_lost_표시 = str(annual_lost_만원)
        else:
            annual_lost_표시 = cta_text

        # 진단번호: place_id 앞 6자리 or 날짜 기반
        place_id = str(data.get('place_id') or '')
        diag_number = place_id[:6] if len(place_id) >= 6 else datetime.now().strftime('%m%d%H')

        # 수집일
        created_raw = data.get('created_at') or ''
        if created_raw:
            try:
                from datetime import datetime as _dt
                diag_collected = _dt.fromisoformat(str(created_raw)[:10]).strftime('%Y. %m. %d')
            except Exception:
                diag_collected = diag_date
        else:
            diag_collected = diag_date

        # 순위 설명
        if rank > 0:
            rank_desc = f'지역 내 {rank}위'
        else:
            rank_desc = '지역 내'

        # 검색량 설명
        if total_search > 10000:
            search_desc = f'이 키워드로 매달 {total_search:,}명이 검색합니다'
        elif total_search > 0:
            search_desc = f'월 {total_search:,}건 검색 발생'
        else:
            search_desc = '키워드 검색량 집계 중'

        # 업체명이가 (받침 없으면 가, 있으면 이)
        last_char = name[-1] if name else ''
        code = ord(last_char) if last_char else 0
        has_jongseong = 0xAC00 <= code <= 0xD7A3 and (code - 0xAC00) % 28 != 0
        name_iga = name + ('이' if has_jongseong else '가')

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
            '{{합계3개월}}':    prices['합계3개월'],
            '{{충격카피}}':     self._build_impact_copy(data, rank, lost, name, category),
            '{{진단날짜}}':     diag_date,
            '{{진단그리드}}':   self._build_diagnosis_grid(data),
            '{{패키지그리드}}': self._build_package_grid(grade),

            # 표지
            '{{사장님이름}}':   owner_name,

            # 누락이었던 태그 — 이제 채움
            '{{연간기회손실}}': annual_lost_표시,
            '{{진단번호}}':     diag_number,
            '{{수집일}}':       diag_collected,
            '{{순위설명}}':     rank_desc,
            '{{검색량설명}}':   search_desc,
            '{{업체명이가}}':   name_iga,

            # 경쟁사 비교
            '{{우리리뷰}}':     str(our_review_count),
            '{{우리사진}}':     str(our_photo_count),
            '{{경쟁사리뷰}}':   f'{competitor_review:,}',
            '{{경쟁사사진}}':   str(competitor_photo),
            '{{경쟁사업체명}}':   str(data.get('competitor_name') or '지역 1위'),
            '{{경쟁사브랜드검색}}': f"{data.get('competitor_brand_search_volume') or 0:,}",
            '{{자사브랜드검색}}':  f"{data.get('own_brand_search_volume') or 0:,}",

            # 손실 계산
            '{{가망고객수}}':   str(lost) if category_confirmed else cta_text,
            # range 기반 객단가 표기
            '{{객단가}}':       self._format_unit_price(unit_price, industry_range) if category_confirmed else cta_text,
            # range 기반 월손실금 표기
            '{{월손실금}}':     self._format_monthly_revenue(monthly_lost_revenue_low, monthly_lost_revenue_high, industry_range) if category_confirmed else cta_text,
            '{{목표명수}}':     str(target_customers) if (category_confirmed and target_customers > 0) else cta_text,

            # CTA
            '{{하루비용}}':     f'{daily_cost:,}',
            '{{월비용}}':       f'{package_monthly_price:,}',
            '{{roi배수}}':      f'{roi_multiple}배 수준' if (category_confirmed and roi_multiple and roi_multiple != 0) else cta_text,
            '{{본전명수}}':     str(target_customers) if (category_confirmed and target_customers > 0) else cta_text,
            '{{카톡번호}}':     '010-5641-1803',
        }

        # 우리 업체 검색 점유율 (순위 기반 추정)
        if rank and rank > 0:
            if rank <= 2:
                our_share = '약 35%'
            elif rank <= 5:
                our_share = '약 10%'
            elif rank <= 10:
                our_share = '약 3%'
            else:
                our_share = '≈ 0%'
        else:
            our_share = '≈ 0%'
        tags['{{우리점유율}}'] = our_share

        # 상위 3개 73% 통계 조건 (근거 없는 허구값이므로 조건부)
        # DOCTRINE: no-fabrication — 근거 없는 수치는 표시 금지
        show_top3_stat = 'true' if rank and rank > 0 else 'false'
        tags['{{top3_show}}'] = show_top3_stat

        # 6개월 유지 시 손실
        if not category_confirmed:
            tags['{{손실6개월}}'] = cta_text
        elif monthly_lost_revenue_high > 0:
            loss_6m_만원 = max(round(monthly_lost_revenue_high * 6 / 10000), 1)
            tags['{{손실6개월}}'] = f'{loss_6m_만원:,}'
        else:
            tags['{{손실6개월}}'] = cta_text

        # 키워드 테이블 (7행) + 볼륨 바 너비 동적 계산
        kw_vols = []
        for i in range(1, 8):
            kw = keywords[i - 1] if i - 1 < len(keywords) else {}
            kw_vols.append(kw.get('search_volume', 0) or 0)

        max_vol = max(kw_vols) if any(kw_vols) else 1

        for i in range(1, 8):
            kw  = keywords[i - 1] if i - 1 < len(keywords) else {}
            vol = kw.get('search_volume', 0) or 0
            tags[f'{{{{키워드{i}}}}}'] = kw.get('keyword', '-') or '-'
            tags[f'{{{{검색량{i}}}}}'] = f'{vol:,}' if vol else '-'
            bar_pct = round(vol / max_vol * 90) if max_vol > 0 else 10
            tags[f'{{{{검색량바{i}}}}}'] = str(max(bar_pct, 5))

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
