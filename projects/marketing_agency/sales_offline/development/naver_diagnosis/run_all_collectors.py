"""1번세션 오프라인 — 20 수집기 sequential run + 통합 dedupe.

사용: python run_all_collectors.py
다음 세션 "1세션 오프라인" trigger 시 이 파일 run 가능 (또는 개별 collect_*.py).
"""
import subprocess, sys, glob, re
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

THIS_DIR = Path(__file__).parent
LEAD_DB = THIS_DIR.parent / "lead_db"
COLLECTORS = sorted(glob.glob(str(THIS_DIR / "collect_*.py")))
TS = datetime.now().strftime("%Y%m%d_%H%M%S")


def count_unique_north() -> int:
    """경기북부 6 region cross-dedupe unique 010 카운트."""
    import openpyxl
    NORTH = ["북부수도권", "남양주", "양주", "포천", "의정부", "동두천", "가평"]
    phones = set()
    for f in LEAD_DB.glob("*.xlsx"):
        if f.name.startswith("~$") or not any(p in f.name for p in NORTH):
            continue
        try:
            wb = openpyxl.load_workbook(str(f), read_only=True, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            wb.close()
            if not rows:
                continue
            headers = [str(h) if h else "" for h in rows[0]]
            phone_idx = next((i for i, h in enumerate(headers) if "010" in h or "전화" in h), -1)
            if phone_idx < 0:
                continue
            for row in rows[1:]:
                if not row or phone_idx >= len(row):
                    continue
                p = str(row[phone_idx]).strip() if row[phone_idx] else ""
                if p and p != "None":
                    digits = re.sub(r"[^0-9]", "", p)
                    if digits.startswith("010") and len(digits) == 11:
                        phones.add(digits)
        except Exception:
            pass
    return len(phones)


def run_collector(path: str) -> tuple:
    name = Path(path).name
    print(f"\n=== {name} 시작 ===")
    try:
        r = subprocess.run([sys.executable, path], cwd=str(THIS_DIR),
                           capture_output=True, text=True, timeout=900,
                           encoding="utf-8", errors="replace")
        ok = r.returncode == 0
        tail = (r.stdout + r.stderr).splitlines()[-5:]
        print(f"  → {'PASS' if ok else 'FAIL'} (exit {r.returncode})")
        for L in tail:
            print(f"    {L}")
        return name, ok
    except Exception as e:
        print(f"  → FAIL ({type(e).__name__}: {e})")
        return name, False


def main():
    print(f"=== 1번세션 오프라인 — {len(COLLECTORS)} 수집기 run ===\n")
    before = count_unique_north()
    print(f"[before] 경기북부 unique 010: {before:,}건\n")

    results = [run_collector(cp) for cp in COLLECTORS]

    after = count_unique_north()
    print(f"\n=== 결과 ===")
    print(f"[after] 경기북부 unique 010: {after:,}건 (+{after - before:,})")
    print(f"수집기 PASS: {sum(1 for _, ok in results if ok)}/{len(results)}")
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'} {name}")


if __name__ == "__main__":
    main()
