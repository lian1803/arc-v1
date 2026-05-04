"""
엑셀 업체 1개 진단 → 바탕화면 .md 파일 출력

사용: python run_one_to_md.py [업체명]
업체명 없으면 엑셀 첫 번째 업체 자동 사용
"""
import sys, io, os, asyncio, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
load_dotenv(THIS_DIR / ".env")

DESKTOP = Path.home() / "Desktop" / "오프라인진단"
DESKTOP.mkdir(parents=True, exist_ok=True)
EXCEL_PATH = Path(__file__).parent.parent / "lead_db" / "양주_010번호_최종_20260326_144032.xlsx"


def read_first_business(xlsx_path: Path, skip_franchise=True) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    franchise_kw = ["본점", "직영", "체인", "가맹", "프랜차이즈", "1호점", "2호점"]
    headers = [str(h).strip() if h else "" for h in rows[0]]
    name_idx = next((i for i, h in enumerate(headers) if "업체명" in h or "상호" in h), 2)
    for row in rows[1:]:
        if not row or name_idx >= len(row):
            continue
        name = str(row[name_idx]).strip() if row[name_idx] else ""
        if not name or name == "None":
            continue
        if skip_franchise and any(kw in name for kw in franchise_kw):
            continue
        return name
    return ""


def build_md(data: dict, messages: dict) -> str:
    biz = data.get("business_name", "업체")
    grade = data.get("grade", "?")
    score = round(data.get("total_score", 0), 1)
    rank = data.get("naver_place_rank", 0)
    lost = data.get("estimated_lost_customers", 0)
    category = data.get("category", "")
    address = data.get("address", "")
    today = datetime.now().strftime("%Y-%m-%d")

    keywords = data.get("keywords") or []
    kw_lines = "\n".join(
        f"  - {k.get('keyword','-')}: {k.get('search_volume',0):,}회/월"
        for k in keywords[:5]
    ) or "  - 수집 중"

    def yn(v): return "✅" if v else "❌"

    improvement = data.get("improvement_points") or []
    imp_lines = "\n".join(f"  - {p.get('message', str(p))}" for p in improvement[:5]) or "  - 없음"

    msg1 = ""
    msg2 = ""
    msg3 = ""
    if messages:
        try: msg1 = messages.get("first", {}).get("text", "") or messages.get("first", "")
        except: msg1 = str(messages.get("first", ""))
        try: msg2 = messages.get("second", "")
        except: msg2 = ""
        try: msg3 = messages.get("third", "")
        except: msg3 = ""

    competitor_name = data.get("competitor_name") or "지역 1위"
    comp_brand_vol = data.get("competitor_brand_search_volume", 0)
    own_brand_vol = data.get("own_brand_search_volume", 0)

    md = f"""# {biz} 네이버 플레이스 진단 리포트
> 진단일: {today}

---

## 기본 정보
| 항목 | 내용 |
|---|---|
| 업체명 | {biz} |
| 업종 | {category} |
| 주소 | {address} |
| 네이버 플레이스 순위 | {rank}위 |
| 종합 등급 | **{grade}등급** |
| 종합 점수 | {score}/100 |
| 월 예상 손실 고객 | **{lost:,}명** |

---

## 항목별 점수
| 항목 | 점수 |
|---|---|
| 사진 | {round(data.get('photo_score',0),1)} |
| 리뷰 | {round(data.get('review_score',0),1)} |
| 블로그 | {round(data.get('blog_score',0),1)} |
| 키워드 | {round(data.get('keyword_score',0),1)} |
| 정보 | {round(data.get('info_score',0),1)} |
| 편의기능 | {round(data.get('convenience_score',0),1)} |
| 참여도 | {round(data.get('engagement_score',0),1)} |

---

## 플레이스 현황
| 항목 | 현황 |
|---|---|
| 사진 | {data.get('photo_count',0)}장 |
| 방문자 리뷰 | {data.get('visitor_review_count',0)}개 |
| 영수증 리뷰 | {data.get('receipt_review_count',0)}개 |
| 블로그 리뷰 | {data.get('blog_review_count',0)}개 |
| 북마크 | {data.get('bookmark_count',0)}개 |
| 메뉴 | {yn(data.get('has_menu'))} ({data.get('menu_count',0)}개) |
| 소개글 | {yn(data.get('has_intro'))} |
| 오시는길 | {yn(data.get('has_directions'))} |
| 영업시간 | {yn(data.get('has_hours'))} |
| 가격 | {yn(data.get('has_price'))} |
| 네이버 예약 | {yn(data.get('has_booking'))} |
| 톡톡 | {yn(data.get('has_talktalk'))} |
| 스마트콜 | {yn(data.get('has_smartcall'))} |
| 쿠폰 | {yn(data.get('has_coupon'))} |
| 새소식 | {yn(data.get('has_news'))} |
| 인스타그램 | {yn(data.get('has_instagram'))} |
| 카카오 | {yn(data.get('has_kakao'))} |

---

## 경쟁사 비교
| 항목 | 우리 | 경쟁사 평균 |
|---|---|---|
| 리뷰 수 | {data.get('visitor_review_count',0)+data.get('receipt_review_count',0)}개 | {data.get('competitor_avg_review',0)}개 |
| 사진 수 | {data.get('photo_count',0)}장 | {data.get('competitor_avg_photo',0)}장 |
| 블로그 수 | {data.get('blog_review_count',0)}개 | {data.get('competitor_avg_blog',0)}개 |
| 브랜드 검색량 | {own_brand_vol:,}회 | {comp_brand_vol:,}회 ({competitor_name}) |

---

## 키워드 검색량
{kw_lines}

---

## 개선 포인트
{imp_lines}

---

## 영업 메시지

### 1차 (첫 접촉)
{msg1}

### 2차 (진단 결과)
{msg2}

### 3차 (패키지 제안)
{msg3}

---
*자동 생성 — naver-diagnosis 시스템*
"""
    return md


async def run_diagnosis(business_name: str) -> dict:
    from playwright.async_api import async_playwright
    from services.naver_place_crawler import NaverPlaceCrawler
    from services.scorer import DiagnosisScorer
    from config.industry_weights import get_competitor_fallback

    print(f"  Playwright 브라우저 시작...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            crawler = NaverPlaceCrawler(browser)

            print(f"  place_id 검색 중: {business_name}")
            place_id = await crawler.find_place_id(business_name)
            if place_id:
                print(f"  place_id 발견: {place_id} → 상세 크롤링")
                data = await crawler.crawl_place_detail(place_id)
                if not data or not data.get("place_id"):
                    print(f"  상세 크롤링 실패 → 검색 기반 폴백")
                    data = await crawler.crawl_from_search(business_name)
            else:
                print(f"  place_id 없음 → 검색 기반 크롤링")
                data = await crawler.crawl_from_search(business_name)

            if not data:
                print(f"  크롤링 실패")
                return {}

            # business_name 보정
            if not data.get("business_name"):
                data["business_name"] = business_name

            # 업종/주소 merge: detail 흐름은 category/address 미수집 → search_business 보정
            # Issue 1 fix (2026-04-28): find_place_id 동명 가게 다른 업종 매칭 검증
            search_match = None  # 후속 카테고리 cross-check 용
            if not data.get("category") or not data.get("address"):
                try:
                    search_results = await crawler.search_business(business_name)
                    if search_results:
                        # 정확 매칭만 사용 (이름 일치). 정확 매칭 없으면 merge skip (다른 가게 가능성).
                        exact_match = next((r for r in search_results if r.get("name", "").strip() == business_name.strip()), None)
                        if exact_match:
                            search_match = exact_match
                            data["category"] = data.get("category") or exact_match.get("category", "")
                            data["address"] = data.get("address") or exact_match.get("address", "") or exact_match.get("road_address", "")
                            print(f"  업종/주소 merge (정확 매칭): {data.get('category','?')} / {data.get('address','?')[:30]}")
                        else:
                            print(f"  ⚠ search_business 정확 매칭 없음 — merge skip (find_place_id 가 다른 가게 잡았을 가능)")
                except Exception as e:
                    print(f"  업종/주소 merge 실패 (계속 진행): {e}")

            # Issue 1 추가 검증: detail 카테고리 vs search 카테고리 root 비교
            if data.get("category") and search_match and search_match.get("category"):
                detail_root = data["category"].split(">")[0] if ">" in data["category"] else data["category"]
                search_root = search_match["category"].split(">")[0] if ">" in search_match["category"] else search_match["category"]
                if detail_root != search_root and detail_root not in search_root and search_root not in detail_root:
                    print(f"  ⚠ 카테고리 mismatch (find_place_id 동명 다른 가게 의심): detail='{data['category']}' vs search='{search_match['category']}' — search 우선 적용")
                    data["category"] = search_match["category"]
                    data["address"] = search_match.get("address", "") or data.get("address", "")

            # Fix A (2026-04-28): category 빈/없음 시 가게이름 키워드 기반 fallback 추론
            if not data.get("category") or data.get("category") in ("?", ""):
                bn = (business_name or "").lower()
                bn_orig = business_name or ""
                # 우선순위 매핑 (구체 → 일반)
                inferred = None
                if any(k in bn_orig for k in ["수학학원", "영어학원", "교습소", "독서", "공부방", "학습지", "학원", "공부", "교실", "교습", "어학", "음악학원", "미술", "피아노", "플룻"]):
                    inferred = "교육,학문>학원"
                elif any(k in bn_orig for k in ["필라테스", "헬스", "요가", "휘트니스", "피트니스", "PT", "크로스핏", "복싱", "수영", "테니스", "골프"]):
                    inferred = "스포츠시설>운동시설"
                elif any(k in bn_orig for k in ["뷰티", "네일", "왁싱", "속눈썹", "피부", "에스테틱", "타투", "마사지", "체형", "산소", "테라피", "다이어트"]):
                    inferred = "미용>뷰티샵"
                elif any(k in bn_orig for k in ["헤어", "미용실", "살롱", "쌀롱"]):
                    inferred = "미용>미용실"
                elif any(k in bn_orig for k in ["카페", "디저트", "베이커리", "커피", "다방", "찻집"]):
                    inferred = "음식점>카페,디저트"
                elif any(k in bn_orig for k in ["한식", "중식", "양식", "분식", "치킨", "피자", "고기", "맛집", "식당", "주점", "술상", "술집", "맥주", "라멘", "라면", "마라탕", "보쌈", "족발", "막창", "곱창", "초밥", "스시", "삼겹살", "갈비", "뷔페", "한정식", "백반", "국밥", "냉면", "쌈밥", "포차", "부대찌개", "감자탕"]):
                    inferred = "음식점>식당"
                elif any(k in bn_orig for k in ["청소", "세차", "이사", "수리", "인테리어", "에어컨", "도어록", "열쇠", "방역", "소독", "구충"]):
                    inferred = "지원,대행>청소·서비스"
                elif any(k in bn_orig for k in ["반려", "애견", "동물병원", "댕댕", "펫", "강아지", "고양이"]):
                    inferred = "반려동물>반려동물업"
                elif any(k in bn_orig for k in ["사진관", "스튜디오", "포토"]):
                    inferred = "생활,편의>사진,스튜디오"
                elif any(k in bn_orig for k in ["부동산", "공인중개"]):
                    inferred = "부동산>중개업"
                elif any(k in bn_orig for k in ["꽃집", "플라워", "플로르", "꽃다발", "꽃배달"]):
                    inferred = "생활,편의>꽃집,꽃배달"
                elif any(k in bn_orig for k in ["병원", "치과", "약국", "한의원", "의원", "정형외과"]):
                    inferred = "의료>병원"
                if inferred:
                    data["category"] = inferred
                    print(f"  카테고리 fallback (가게이름 추론): {inferred}")
                else:
                    data["category"] = "기타,소상공인"
                    print(f"  카테고리 fallback (default): 기타,소상공인")

            # 키워드 보정 1: detail 흐름이 키워드 미수집 → desktop pcmap 페이지에서 fetch
            if not data.get("keywords") and place_id:
                try:
                    kws = await crawler._fetch_keywords_from_desktop(place_id)
                    if kws:
                        data["keywords"] = [{"keyword": k, "search_volume": 0} for k in kws[:5]]
                        print(f"  키워드 desktop fetch: {[k for k in kws[:5]]}")
                except Exception as e:
                    print(f"  키워드 desktop fetch 실패 (계속 진행): {e}")

            # 키워드 보정 2: desktop fetch 도 빈 결과면 추측 키워드 (지역시 + 업종 끝부분) 생성
            if not data.get("keywords"):
                try:
                    addr = data.get("address", "")
                    cat = data.get("category", "")
                    # "경기도 의정부시 의정부동..." → "의정부" (특별시/광역시 처리 추가)
                    # 긴 suffix부터 검사해야 "특별시" 문자열이 깨지지 않음
                    region = ""
                    for token in addr.split():
                        for suffix in ["특별자치시", "특별자치도", "광역시", "특별시", "도", "시", "군", "구"]:
                            if token.endswith(suffix):
                                region = token[:-len(suffix)]
                                break
                        if region:
                            break
                    # "한식>족발,보쌈" → "족발"
                    cat_tail = cat.split(">")[-1].split(",")[0] if cat else ""
                    if region and cat_tail:
                        guess_kw = f"{region} {cat_tail}"
                        data["keywords"] = [{"keyword": guess_kw, "search_volume": 0}]
                        print(f"  키워드 추측: '{guess_kw}'")
                except Exception as e:
                    print(f"  키워드 추측 실패 (계속 진행): {e}")

            # 순위 보정: 키워드 있으면 첫 키워드로 순위 매김
            if data.get("keywords") and not data.get("naver_place_rank") and place_id:
                try:
                    first_kw = data["keywords"][0]
                    kw_str = first_kw if isinstance(first_kw, str) else first_kw.get("keyword", "")
                    if kw_str:
                        rank = await crawler.get_place_rank(kw_str, place_id)
                        if rank:
                            data["naver_place_rank"] = rank
                            print(f"  순위: '{kw_str}' 기준 {rank}위")
                        else:
                            print(f"  순위: '{kw_str}' 기준 미노출 (top 결과에 없음)")
                except Exception as e:
                    print(f"  순위 매김 실패 (계속 진행): {e}")

            # 경쟁사 가게명 보정: competitor_name이 None이면 fetch
            if not data.get("competitor_name") and data.get("keywords") and place_id:
                try:
                    first_kw = data["keywords"][0]
                    kw_str = first_kw if isinstance(first_kw, str) else first_kw.get("keyword", "")
                    if kw_str:
                        competitor = await crawler.fetch_top_competitor_name(kw_str, place_id)
                        if competitor:
                            data["competitor_name"] = competitor
                            print(f"  경쟁사 1위: {competitor}")
                        else:
                            print(f"  경쟁사 추출 실패 (계속 진행)")
                except Exception as e:
                    print(f"  경쟁사 추출 실패 (계속 진행): {e}")

            # owner_reply_rate가 0이고 place_id 있으면 별도 수집
            if data.get("place_id") and not data.get("owner_reply_rate"):
                try:
                    reply_rate = await crawler.fetch_owner_reply_rate(data["place_id"])
                    data["owner_reply_rate"] = reply_rate
                except Exception as e:
                    print(f"  답글률 재수집 실패 (계속 진행): {e}")

            # 키워드 검색량
            if data.get("keywords"):
                try:
                    from services.naver_search_ad import NaverSearchAdAPI
                    ad_api = NaverSearchAdAPI()
                    enriched = []
                    for kw in data["keywords"][:5]:
                        kw_name = kw if isinstance(kw, str) else kw.get("keyword", "")
                        if not kw_name:
                            continue
                        stats = await ad_api.get_keyword_stats(kw_name)
                        enriched.append({
                            "keyword": kw_name,
                            "search_volume": (stats.get("monthly_search_pc", 0) or 0) + (stats.get("monthly_search_mobile", 0) or 0),
                        })
                    if enriched:
                        data["keywords"] = enriched
                except Exception as e:
                    print(f"  키워드 검색량 실패 (계속 진행): {e}")

            # address 최종 fallback: 여전히 None이면 placeholder
            if not data.get("address"):
                data["address"] = "주소 정보 미수집"
                print(f"  주소: placeholder 설정")

            # 브랜드 검색량 (본사 + 경쟁사)
            data.setdefault("own_brand_search_volume", 0)
            data.setdefault("competitor_brand_search_volume", 0)
            data.setdefault("competitor_name", "지역 1위")
            try:
                from services.naver_search_ad import NaverSearchAdAPI
                ad_api = NaverSearchAdAPI()

                # 우리 업체 브랜드 검색량
                own_stats = await ad_api.get_keyword_stats(business_name)
                own_brand_vol = (own_stats.get("monthly_search_pc", 0) or 0) + (own_stats.get("monthly_search_mobile", 0) or 0)
                data["own_brand_search_volume"] = own_brand_vol
                print(f"  브랜드 검색량 - '{business_name}': {own_brand_vol:,}회")

                # 경쟁사: 우선 fetch_top_competitor_name 보정 layer 가 박은 값 사용 (L262-275)
                # fallback: related_keywords 에서 1위 업체명 추출 시도
                competitor_name = data.get("competitor_name")
                if not competitor_name and data.get("related_keywords"):
                    for kw_item in data.get("related_keywords", []):
                        if isinstance(kw_item, dict) and kw_item.get("business_name"):
                            competitor_name = kw_item.get("business_name")
                            break

                # 최종 fallback: 여전히 None이면 기본값 사용
                if not competitor_name:
                    competitor_name = "지역 상위 경쟁사"
                    print(f"  경쟁사: placeholder 설정 (정보 미수집)")

                if competitor_name:
                    comp_stats = await ad_api.get_keyword_stats(competitor_name)
                    comp_brand_vol = (comp_stats.get("monthly_search_pc", 0) or 0) + (comp_stats.get("monthly_search_mobile", 0) or 0)
                    data["competitor_brand_search_volume"] = comp_brand_vol
                    data["competitor_name"] = competitor_name
                    print(f"  경쟁사 검색량 - '{competitor_name}': {comp_brand_vol:,}회")
                else:
                    print(f"  경쟁사명 미검출 → default 사용")
            except Exception as e:
                print(f"  브랜드 검색량 실패 (계속 진행): {e}")

            # 리뷰 합계
            data["review_count"] = data.get("visitor_review_count", 0) + data.get("receipt_review_count", 0)

            # 점수 계산
            scores = DiagnosisScorer.calculate_all(data)
            data.update(scores)

            # 경쟁사 폴백
            fb = get_competitor_fallback(data.get("category", ""))
            data.setdefault("competitor_avg_review", fb["avg_review"])
            data.setdefault("competitor_avg_photo", fb["avg_photo"])
            data.setdefault("competitor_avg_blog", fb["avg_blog"])

            # 손실 고객
            data["estimated_lost_customers"] = DiagnosisScorer.calculate_estimated_lost_customers(
                rank=data.get("naver_place_rank", 0),
                keywords=data.get("keywords", []),
                competitor_avg_review=fb["avg_review"],
                review_count=data.get("review_count", 0),
            )

            return data

        finally:
            await browser.close()


async def main():
    # 업체명 결정
    if len(sys.argv) > 1:
        business_name = sys.argv[1]
    else:
        print(f"엑셀에서 첫 업체 읽는 중: {EXCEL_PATH.name}")
        business_name = read_first_business(EXCEL_PATH)
        if not business_name:
            print("❌ 업체명을 찾을 수 없음")
            sys.exit(1)

    print(f"\n{'='*50}")
    print(f"진단 시작: {business_name}")
    print(f"{'='*50}\n")

    # 크롤링 실행
    data = await run_diagnosis(business_name)

    if not data:
        print("❌ 진단 데이터 수집 실패")
        sys.exit(1)

    # 메시지 생성
    messages = {}
    try:
        from services.message_generator import generate_all_messages
        messages = generate_all_messages(data)
        print("  영업 메시지 생성 완료")
    except Exception as e:
        print(f"  메시지 생성 실패 (계속 진행): {e}")

    # 마크다운 생성
    md_content = build_md(data, messages)

    # 바탕화면에 저장
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = DESKTOP / f"{business_name}_진단_{date_str}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n{'='*50}")
    print(f"✅ 완료!")
    print(f"   업체: {data.get('business_name')}")
    print(f"   등급: {data.get('grade')} / 점수: {round(data.get('total_score',0),1)}")
    print(f"   손실 추정: 월 {data.get('estimated_lost_customers',0):,}명")
    print(f"   저장: {out_path}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())



