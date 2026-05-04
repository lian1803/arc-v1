"""양주 10개 업체 실측 배치 — 결과를 analysis/ 에 저장"""
import sys, asyncio, json, os
from pathlib import Path
from datetime import datetime

THIS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(THIS_DIR))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(THIS_DIR / '.env')

BUSINESSES = [
    ('뉴쎈학원', '학원'),
    ('여배우살롱', '피부관리'),
    ('음식점', '음식점'),
    ('시매쓰 의정부송산센터', '수학학원'),
    ('모먼트 태권도장', '태권도'),
    ('아이스크림홈런 도봉한신공부방', '공부방'),
    ('왁싱앤유 노원점', '왁싱'),
    ('바른숨 필라테스', '필라테스'),
    ('나미스뷰티', '피부관리'),
    ('더예쁜필라테스', '필라테스'),
]

ANALYSIS_DIR = Path(__file__).parent
RESULTS = []

async def run_one(name, industry):
    from run_one_to_md import run_diagnosis
    start = datetime.now()
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 시작: {name}")
    try:
        data = await run_diagnosis(name)
        elapsed = (datetime.now() - start).seconds
        if data:
            result = {
                'name': name,
                'industry': industry,
                'status': 'success',
                'elapsed_s': elapsed,
                'total_score': data.get('total_score', 0),
                'grade': data.get('grade', '?'),
                'category': data.get('category', ''),
                'address': data.get('address', ''),
                'review_count': data.get('review_count', 0),
                'photo_count': data.get('photo_count', 0),
                'blog_review_count': data.get('blog_review_count', 0),
                'naver_place_rank': data.get('naver_place_rank', 0),
                'has_owner_reply': data.get('has_owner_reply', False),
                'owner_reply_rate': data.get('owner_reply_rate', 0),
                'competitor_name': data.get('competitor_name', ''),
                'competitor_avg_review': data.get('competitor_avg_review', 0),
                'competitor_avg_photo': data.get('competitor_avg_photo', 0),
                'own_brand_search_volume': data.get('own_brand_search_volume', 0),
                'competitor_brand_search_volume': data.get('competitor_brand_search_volume', 0),
                'estimated_lost_customers': data.get('estimated_lost_customers', 0),
                'photo_quality_score': data.get('photo_quality_score', 0),
                'review_last_30d_count': data.get('review_last_30d_count', 0),
                'keywords': data.get('keywords', []),
                'has_keywords': bool(data.get('keywords')),
                'related_keywords': bool(data.get('related_keywords')),
                'photo_urls_count': len(data.get('photo_urls', [])),
                'place_id': data.get('place_id', ''),
            }
            print(f"  ✅ {name}: {result['total_score']}점 {result['grade']}등급 ({elapsed}초)")
        else:
            result = {'name': name, 'industry': industry, 'status': 'failed', 'elapsed_s': elapsed}
            print(f"  ❌ {name}: 데이터 없음")
        return result
    except Exception as e:
        elapsed = (datetime.now() - start).seconds
        print(f"  💥 {name}: 오류 — {e}")
        return {'name': name, 'industry': industry, 'status': 'error', 'error': str(e), 'elapsed_s': elapsed}

async def main():
    results = []
    for name, industry in BUSINESSES:
        r = await run_one(name, industry)
        results.append(r)

    # JSON 저장
    out = ANALYSIS_DIR / f'run_10_results_{datetime.now().strftime("%H%M")}.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 요약 출력
    print(f"\n{'='*50}")
    print(f"실측 완료: {len(results)}개")
    print(f"성공: {sum(1 for r in results if r['status']=='success')}")
    print(f"실패: {sum(1 for r in results if r['status']!='success')}")
    print(f"\n결과 저장: {out}")

    # 간단 표
    print(f"\n{'업체명':<20} {'점수':>6} {'등급':>4} {'리뷰':>6} {'사진':>6} {'손실':>6}")
    print('-'*55)
    for r in results:
        if r['status'] == 'success':
            print(f"{r['name'][:18]:<20} {r['total_score']:>6.1f} {r['grade']:>4} {r['review_count']:>6} {r['photo_count']:>6} {r['estimated_lost_customers']:>6}")
        else:
            print(f"{r['name'][:18]:<20} {'실패':>6}")

    return results

if __name__ == '__main__':
    asyncio.run(main())
