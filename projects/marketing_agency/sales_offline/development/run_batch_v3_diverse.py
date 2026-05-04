"""
v3 (Inevitable Choice) 다양 시나리오 batch.
random 3 가게 → 1차 + 8 응답 시나리오 → 바탕화면 .md.
session 28 Lian directive 2026-04-27.
"""
import sys
import asyncio
import random
from pathlib import Path
from datetime import datetime
import openpyxl

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(THIS_DIR / "naver_diagnosis"))

from run_one_to_md import run_diagnosis
from sales_orchestrator_v3 import generate_diverse_v3

EXCEL = THIS_DIR / "lead_db" / "양주_010번호_최종_20260326_144032.xlsx"
DESKTOP = Path.home() / "Desktop"


def list_businesses(xlsx_path):
    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    headers = [str(h).strip() if h else "" for h in rows[0]]
    name_idx = next((i for i, h in enumerate(headers) if "업체명" in h or "상호" in h), 2)
    franchise_kw = ["본점", "직영", "체인", "가맹", "프랜차이즈", "1호점", "2호점"]
    names = []
    for row in rows[1:]:
        if not row or name_idx >= len(row):
            continue
        name = str(row[name_idx]).strip() if row[name_idx] else ""
        if not name or name == "None":
            continue
        if any(kw in name for kw in franchise_kw):
            continue
        names.append(name)
    return names


async def main():
    names = list_businesses(EXCEL)
    print(f"양주 db 가게 총 {len(names)}개. random 3 추출.")
    sample = random.sample(names, min(3, len(names)))
    print(f"  추출: {sample}\n")

    date_str = datetime.now().strftime("%Y%m%d_%H%M")

    for idx, biz in enumerate(sample, 1):
        print(f"\n{'='*60}\n[{idx}/3] 진단 시작: {biz}\n{'='*60}")
        try:
            data = await run_diagnosis(biz)
            if not data:
                print(f"  진단 fail — skip")
                continue
            if not data.get("business_name"):
                data["business_name"] = biz

            print(f"  v3 (Inevitable Choice) 메시지 생성 중...")
            summary, messages = generate_diverse_v3(data)

            md = f"""# {biz} — v3 다양 응답 시나리오 (Inevitable Choice)
> v3 = v2.1 base + 4 심리 설계 (격차/권위/자율/비대칭) + 3개월 단위 정정 + 환불 X
> 생성일: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 진단 요약

```
{summary}
```

## 1차 첫 접촉 + 8 응답 시나리오

{messages}

---
*sales_orchestrator_v3.py / session 28 Lian directive 2026-04-27 (Inevitable Choice 박음)*
"""
            out_path = DESKTOP / f"{biz}_v3_diverse_{date_str}.md"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"  ✅ 저장: {out_path.name}")
        except Exception as e:
            print(f"  ❌ fail: {e}")

    print(f"\n{'='*60}\n완료. 바탕화면 확인.\n{'='*60}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
