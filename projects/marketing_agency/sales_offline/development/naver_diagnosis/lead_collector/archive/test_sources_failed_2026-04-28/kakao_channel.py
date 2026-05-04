"""카카오 채널 — 양주 채널 → 010"""
import asyncio, re, time, httpx
from ._common import UA, REGION, PHONE_ANY, normalize_phone, dedup_add

async def test():
    print("[카카오채널] 양주 → 010")
    t0, found, errors = time.time(), [], []
    try:
        async with httpx.AsyncClient(headers={"User-Agent": UA}, timeout=20) as c:
            r = await c.get(f"https://pf.kakao.com/_/search/all?query={REGION}", params={"limit": 50})
            urls = list(set(re.findall(r'href="([^"]*pf\.kakao\.com[^"]*)"', r.text)))[:10]
            print(f"  {len(urls)}개")
            for url in urls:
                try:
                    p = await c.get(url)
                    if p.status_code == 200:
                        name = re.search(r'<title>([^<]+)</title>', p.text)
                        name = (name.group(1)[:50] if name else "kakao_ch")
                        for m in PHONE_ANY.finditer(p.text):
                            phone = normalize_phone(m.group(0))
                            if phone: dedup_add(found, phone, name, url=url)
                    await asyncio.sleep(0.5)
                except: pass
    except Exception as e: errors.append(str(e))
    return {"source": "kakao_channel", "region": REGION, "phone_count": len(found),
            "elapsed_sec": round(time.time() - t0, 1), "samples": found[:5], "errors": errors[:3]}
