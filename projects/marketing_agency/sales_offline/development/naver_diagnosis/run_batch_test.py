"""
배치 테스트 — 엑셀 10개 업체 진단 → 바탕화면 .md 출력
"""
import sys, io, os, asyncio
from pathlib import Path
from datetime import datetime

# Windows cp949 환경에서 UTF-8 강제 적용
if sys.platform == "win32" and getattr(sys.stdout, "encoding", "").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))

DESKTOP = Path.home() / "Desktop" / "오프라인진단"
DESKTOP.mkdir(parents=True, exist_ok=True)
EXCEL_PATH = Path(__file__).parent.parent / "lead_db" / "양주_010번호_최종_20260326_144032.xlsx"
BATCH_SIZE = 100


def read_businesses(xlsx_path: Path, count: int = 10, skip_franchise: bool = True) -> list:
    import openpyxl
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    franchise_kw = ["본점", "직영", "체인", "가맹", "프랜차이즈", "1호점", "2호점", "3호점"]
    headers = [str(h).strip() if h else "" for h in rows[0]]
    name_idx = next((i for i, h in enumerate(headers) if "업체명" in h or "상호" in h), 2)
    names = []
    for row in rows[1:]:
        if len(names) >= count:
            break
        if not row or name_idx >= len(row):
            continue
        name = str(row[name_idx]).strip() if row[name_idx] else ""
        if not name or name == "None":
            continue
        if skip_franchise and any(kw in name for kw in franchise_kw):
            continue
        names.append(name)
    return names


def build_md(data: dict, messages: dict) -> str:
    def _safe_vol(v) -> int:
        """검색량 안전 변환 - '< 10< 10' 같은 비정상 값 처리"""
        if v is None:
            return 0
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    biz = data.get("business_name", "업체")
    grade = data.get("grade", "?")
    score = round(data.get("total_score", 0), 1)
    rank = data.get("naver_place_rank", 0)
    lost = int(data.get("estimated_lost_customers") or 0)
    category = data.get("category", "")
    address = data.get("address", "")
    today = datetime.now().strftime("%Y-%m-%d")
    keywords = data.get("keywords") or []
    kw_lines = "\n".join(
        f"  - {k.get('keyword','-')}: {_safe_vol(k.get('search_volume')):,}회/월"
        for k in keywords[:5] if isinstance(k, dict)
    ) or "  - 수집 중"
    def yn(v): return "✅" if v else "❌"
    improvement = data.get("improvement_points") or []
    imp_lines = "\n".join(f"  - {p.get('message', str(p))}" for p in improvement[:5]) or "  - 없음"
    msg1 = str(messages.get("first", "") or "")
    msg2 = str(messages.get("second", "") or "")
    msg3 = str(messages.get("third", "") or "")
    competitor_name = data.get("competitor_name") or "지역 1위"
    comp_brand_vol = int(data.get("competitor_brand_search_volume") or 0)
    own_brand_vol = int(data.get("own_brand_search_volume") or 0)
    reply_rate = data.get("owner_reply_rate", 0)
    return f"""# {biz} 네이버 플레이스 진단 리포트
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
| 사장님 답글률 | {reply_rate:.0%} |
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
*자동 생성 — naver-diagnosis 시스템 (고도화 v2)*
"""


async def run_all(names: list):
    from playwright.async_api import async_playwright
    from services.naver_place_crawler import NaverPlaceCrawler
    from services.scorer import DiagnosisScorer
    from config.industry_weights import get_competitor_fallback
    from services.message_generator import generate_all_messages

    results = []
    date_str = datetime.now().strftime("%Y%m%d_%H%M")

    print(f"\n브라우저 시작...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            crawler = NaverPlaceCrawler(browser)

            for i, name in enumerate(names, 1):
                print(f"\n[{i}/{len(names)}] {name}")
                print("-" * 40)
                try:
                    place_id = await crawler.find_place_id(name)
                    if place_id:
                        data = await crawler.crawl_place_detail(place_id)
                        if not data or not data.get("place_id"):
                            data = await crawler.crawl_from_search(name)
                    else:
                        data = await crawler.crawl_from_search(name)

                    if not data:
                        print(f"  [실패] 크롤링 데이터 없음")
                        results.append({"name": name, "success": False})
                        continue

                    if not data.get("business_name"):
                        data["business_name"] = name

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
                            print(f"  키워드 실패 (계속): {e}")

                    data["review_count"] = int(data.get("visitor_review_count") or 0) + int(data.get("receipt_review_count") or 0)

                    # owner_reply_rate 추가 수집
                    if data.get("place_id") and not data.get("owner_reply_rate"):
                        try:
                            rr = await crawler.fetch_owner_reply_rate(data["place_id"])
                            data["owner_reply_rate"] = rr
                            print(f"  답글률: {rr:.0%}")
                        except Exception:
                            pass

                    scores = DiagnosisScorer.calculate_all(data)
                    data.update(scores)

                    fb = get_competitor_fallback(data.get("category", ""))
                    data.setdefault("competitor_avg_review", fb["avg_review"])
                    data.setdefault("competitor_avg_photo", fb["avg_photo"])
                    data.setdefault("competitor_avg_blog", fb["avg_blog"])

                    data["estimated_lost_customers"] = DiagnosisScorer.calculate_estimated_lost_customers(
                        rank=data.get("naver_place_rank", 0),
                        keywords=data.get("keywords", []),
                        competitor_avg_review=fb["avg_review"],
                        review_count=data.get("review_count", 0),
                    )

                    # 메시지
                    messages = {}
                    try:
                        messages = generate_all_messages(data)
                    except Exception as e:
                        print(f"  메시지 실패 (계속): {e}")

                    md = build_md(data, messages)
                    out_path = DESKTOP / f"{name}_진단_{date_str}.md"
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(md)

                    print(f"  등급: {data.get('grade')} | 점수: {round(data.get('total_score',0),1)} | 손실: {data.get('estimated_lost_customers',0):,}명")
                    print(f"  저장: {out_path.name}")

                    results.append({
                        "name": name,
                        "success": True,
                        "grade": data.get("grade"),
                        "score": round(data.get("total_score", 0), 1),
                        "lost": data.get("estimated_lost_customers", 0),
                        "reply_rate": data.get("owner_reply_rate", 0),
                    })

                except Exception as e:
                    print(f"  [오류] {e}")
                    results.append({"name": name, "success": False, "error": str(e)})

        finally:
            await browser.close()

    return results


async def main():
    print(f"{'='*50}")
    print(f"배치 테스트 - {BATCH_SIZE}개 업체")
    print(f"{'='*50}")

    names = read_businesses(EXCEL_PATH, BATCH_SIZE)
    if not names:
        print("업체명을 읽을 수 없음")
        sys.exit(1)

    print(f"\n대상 업체 ({len(names)}개):")
    for i, n in enumerate(names, 1):
        print(f"  {i}. {n}")

    results = await run_all(names)

    print(f"\n{'='*50}")
    print(f"배치 완료 — 결과 요약")
    print(f"{'='*50}")
    ok = [r for r in results if r.get("success")]
    fail = [r for r in results if not r.get("success")]
    print(f"성공: {len(ok)}개 / 실패: {len(fail)}개")
    print()
    for r in ok:
        rr = f" 답글률:{r['reply_rate']:.0%}" if r.get("reply_rate") else ""
        print(f"  {r['name']:15s} {r['grade']}등급 {r['score']:5.1f}점  손실:{r['lost']:,}명{rr}")
    if fail:
        print("\n실패:")
        for r in fail:
            print(f"  {r['name']}: {r.get('error','알 수 없음')[:60]}")
    print(f"\n바탕화면에 .md 파일 {len(ok)}개 저장됨")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
