"""
양주 lead_db 에서 random 3 가게 → 진단 + orchestrator 메시지 → 바탕화면 .md.
session 28 first batch test (Lian directive 2026-04-27).
"""
import sys
import asyncio
import random
from pathlib import Path
from datetime import datetime
import openpyxl

# stdout/stderr wrapping 은 run_one_to_md import 시 처리됨 (중복 wrap = 닫힘 에러)
THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))
sys.path.insert(0, str(THIS_DIR / "naver_diagnosis"))

from run_one_to_md import run_diagnosis  # 4 patch 박혀있는 진단
from sales_orchestrator import generate_full_cycle

EXCEL = THIS_DIR / "lead_db" / "양주_010번호_최종_20260326_144032.xlsx"
DESKTOP = Path.home() / "Desktop"


def list_businesses(xlsx_path: Path):
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
        print(f"\n{'='*60}")
        print(f"[{idx}/3] 진단 시작: {biz}")
        print(f"{'='*60}")
        try:
            data = await run_diagnosis(biz)
            if not data:
                print(f"  진단 fail (data 빈) — skip")
                continue
            if not data.get("business_name"):
                data["business_name"] = biz

            print(f"  orchestrator 메시지 생성 중...")
            cycle = generate_full_cycle(data)

            md = f"""# {biz} — 영업 사이클 테스트
> 진단 + orchestrator 메시지 (Gemini 2.5 Flash, 카톡/문자 텍스트)
> 생성일: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 진단 요약

```
{cycle['diagnosis_summary']}
```

## 메시지 (4 단계 카톡/문자)

{cycle['messages']}

---
*sales_orchestrator.py — session 28 first batch (Lian directive 2026-04-27)*
"""
            out_path = DESKTOP / f"{biz}_orchestrator_{date_str}.md"
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
