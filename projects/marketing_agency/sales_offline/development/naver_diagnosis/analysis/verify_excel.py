"""
양주 Excel 업체 전체 검증
- 이름으로 네이버 검색
- 지역 주소 필터(양주/의정부/동두천 등)로 올바른 가게 확인
- 결과: verified_businesses.json (place_id + 검증주소)
"""
import sys, asyncio, json, re, time
from pathlib import Path
import httpx, openpyxl, os
from dotenv import load_dotenv

THIS_DIR = Path(__file__).parent.parent
load_dotenv(THIS_DIR / '.env')
sys.stdout.reconfigure(encoding='utf-8')

EXCEL_PATH = THIS_DIR.parent / 'lead_db' / '양주_010번호_최종_20260326_144032.xlsx'
OUT_PATH = Path(__file__).parent / 'verified_businesses.json'

VALID_REGIONS = ['양주', '의정부', '동두천', '포천', '가평', '연천', '파주', '남양주']
# 남양주는 "양주"를 포함하므로 별도 처리
STRICT_YANGJU = ['경기도 양주시', '경기도 의정부시', '경기도 동두천시', '경기도 포천시',
                  '경기도 가평군', '경기도 연천군', '경기도 파주시', '경기도 남양주시']

NAVER_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_SECRET = os.getenv('NAVER_CLIENT_SECRET')


def read_excel():
    wb = openpyxl.load_workbook(str(EXCEL_PATH), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    headers = [str(h).strip() if h else '' for h in rows[0]]
    name_idx = next((i for i, h in enumerate(headers) if '업체명' in h or '상호' in h), 2)
    phone_idx = next((i for i, h in enumerate(headers) if '010' in h or '전화' in h), 1)
    industry_idx = next((i for i, h in enumerate(headers) if '업종' in h), 3)
    result = []
    for row in rows[1:]:
        if not row or name_idx >= len(row):
            continue
        name = str(row[name_idx]).strip() if row[name_idx] else ''
        phone = str(row[phone_idx]).strip() if phone_idx < len(row) and row[phone_idx] else ''
        industry = str(row[industry_idx]).strip() if industry_idx < len(row) and row[industry_idx] else ''
        if not name or name == 'None':
            continue
        result.append({'name': name, 'phone': phone, 'industry': industry})
    return result


def is_valid_region(addr):
    for strict in STRICT_YANGJU:
        if strict in addr:
            return True
    return False


async def search_naver(query, client):
    try:
        resp = await client.get(
            'https://openapi.naver.com/v1/search/local.json',
            headers={'X-Naver-Client-Id': NAVER_ID, 'X-Naver-Client-Secret': NAVER_SECRET},
            params={'query': query, 'display': 5},
            timeout=8.0
        )
        return resp.json().get('items', [])
    except Exception as e:
        return []


async def verify_one(biz, client):
    name = biz['name']
    # 1차: 이름만
    items = await search_naver(name, client)
    for item in items:
        addr = item.get('address', '') + ' ' + item.get('roadAddress', '')
        if is_valid_region(addr):
            n = re.sub(r'<[^>]+>', '', item.get('title', ''))
            return {**biz, 'status': 'verified_1', 'matched_name': n,
                    'address': addr.strip(), 'link': item.get('link', '')}
    # 2차: "양주 이름"
    items2 = await search_naver('양주 ' + name, client)
    for item in items2:
        addr = item.get('address', '') + ' ' + item.get('roadAddress', '')
        if is_valid_region(addr):
            n = re.sub(r'<[^>]+>', '', item.get('title', ''))
            return {**biz, 'status': 'verified_2', 'matched_name': n,
                    'address': addr.strip(), 'link': item.get('link', '')}
    return {**biz, 'status': 'not_found', 'matched_name': '', 'address': '', 'link': ''}


async def main(limit=None):
    businesses = read_excel()
    if limit:
        businesses = businesses[:limit]
    total = len(businesses)
    print(f'총 {total}개 업체 검증 시작...')

    results = []
    verified = 0
    not_found = 0

    async with httpx.AsyncClient() as client:
        for i, biz in enumerate(businesses):
            r = await verify_one(biz, client)
            results.append(r)
            if r['status'].startswith('verified'):
                verified += 1
            else:
                not_found += 1

            # 진행 상황 (50개마다)
            if (i + 1) % 50 == 0 or i == total - 1:
                print(f'  [{i+1}/{total}] 검증: {verified} / 미발견: {not_found}')

            # API rate limit 방지
            await asyncio.sleep(0.1)

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\n=== 검증 완료 ===')
    print(f'전체: {total}개')
    print(f'검증 성공: {verified}개 ({verified/total*100:.1f}%)')
    print(f'미발견: {not_found}개 ({not_found/total*100:.1f}%)')
    print(f'결과 저장: {OUT_PATH}')

    # 미발견 샘플
    nf = [r for r in results if r['status'] == 'not_found']
    if nf:
        print(f'\n미발견 샘플 10개:')
        for r in nf[:10]:
            print(f'  - {r[\"name\"]} ({r[\"industry\"]})')

    return results

if __name__ == '__main__':
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(main(limit))
