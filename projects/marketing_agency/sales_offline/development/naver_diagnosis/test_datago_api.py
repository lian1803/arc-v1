"""data.go.kr 소상공인 상가정보 — 경기도 전체 페이지 수 + 샘플 레코드 확인."""
import httpx, sys, json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KEY = "35a48f5e6d8a13b08f03c32647e91cd1fd5bd045e90be62190fce9c779a02f43"
URL = "https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInDong"

r = httpx.get(URL, params={
    "serviceKey": KEY, "divId": "ctprvnCd", "key": "41",
    "type": "json", "pageNo": "1", "numOfRows": "1000"
}, timeout=30, follow_redirects=True)

data = r.json()
hdr = data.get("header", {})
body = data.get("body", {})
print(f"resultCode: {hdr.get('resultCode','ok')}")
print(f"totalCount: {body.get('totalCount')}")
print(f"pageNo: {body.get('pageNo')}")
print(f"numOfRows: {body.get('numOfRows')}")
items = body.get("items", [])
if isinstance(items, dict):
    items = items.get("item", [])
    if isinstance(items, dict): items = [items]
print(f"items in page: {len(items)}")
if items:
    s = items[0]
    print(f"\n샘플: {s.get('상호명')} / {s.get('시군구명')} / {s.get('전화번호','(없음)')}")
    # 전화번호 field name 확인
    print("keys with tel:", [k for k in s.keys() if '전화' in k or 'tel' in k.lower()])
    print("all keys:", list(s.keys())[:20])
