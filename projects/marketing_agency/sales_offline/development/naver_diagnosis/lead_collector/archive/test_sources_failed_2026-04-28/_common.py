"""테스트 공통 헬퍼 — UA / phone regex / save_result"""
import json
import re
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
PHONE_010 = re.compile(r"010[-\s]?\d{3,4}[-\s]?\d{4}")
PHONE_ANY = re.compile(r"0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}")

REGION = "양주"
RESULTS_DIR = Path(__file__).parent.parent / "test_results"
RESULTS_DIR.mkdir(exist_ok=True)


def normalize_phone(s: str) -> str:
    digits = re.sub(r"[^\d]", "", s)
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return ""


def dedup_add(found: list, phone: str, name: str, **extra) -> bool:
    if not phone:
        return False
    existing = {p["phone"] for p in found}
    if phone in existing:
        return False
    found.append({"phone": phone, "name": name, **extra})
    return True


def save_result(source: str, data: dict):
    p = RESULTS_DIR / f"{source}_{REGION}.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
