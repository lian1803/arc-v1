"""§12 Pre-Launch Reality Test driver for invoice-snap.

Proves that the deployed invoice-snap product actually works end-to-end
with Lian's Gemini key, not just that static assets return HTTP 200.
Exits non-zero if any §12 check fails.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from invoice_snap_test_lib import (
    call_gemini_vision,
    generate_csv_bytes,
    generate_sample_invoice,
    validate_csv_bytes,
)

ARC_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ARC_ROOT / ".env"
OUT_DIR = ARC_ROOT / "shared" / "message_pool" / "invoice_snap_build" / "reality_test"

EXPECTED = {
    "vendor_contains": "서울테크",
    "date": "2026-04-20",
    "invoice_number": "SK-2026-00412",
    "total_amount": 1430000,
    "currency": "KRW",
    "vat_or_tax": 130000,
}


def load_key() -> str:
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("GEMINI_API_KEY not in .env")


def check_accuracy(ex: dict) -> tuple[list[tuple[str, bool]], float]:
    c = [
        ("vendor contains '서울테크'", EXPECTED["vendor_contains"] in (ex.get("vendor") or "")),
        ("date == 2026-04-20", ex.get("date") == EXPECTED["date"]),
        ("invoice_number == SK-2026-00412", ex.get("invoice_number") == EXPECTED["invoice_number"]),
        ("total_amount == 1,430,000", ex.get("total_amount") == EXPECTED["total_amount"]),
        ("currency == KRW", ex.get("currency") == EXPECTED["currency"]),
        ("vat_or_tax == 130,000", ex.get("vat_or_tax") == EXPECTED["vat_or_tax"]),
        (">= 2 line_items", len(ex.get("line_items") or []) >= 2),
    ]
    acc = sum(1 for _, ok in c if ok) / len(c)
    return c, acc


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    api_key = load_key()

    print("=" * 60)
    print("§12 Pre-Launch Reality Test — invoice-snap")
    print("=" * 60)

    print("\n[1] Generating synthetic 세금계산서 PNG...")
    img = generate_sample_invoice(OUT_DIR / "synthetic_invoice.png")
    print(f"    -> {img.relative_to(ARC_ROOT)} ({img.stat().st_size}B)")

    print("\n[2] Calling gemini-2.5-flash with deployed prompt (Lian's key)...")
    ex = call_gemini_vision(img, api_key)
    (OUT_DIR / "gemini_response.json").write_text(
        json.dumps(ex, ensure_ascii=False, indent=2), encoding="utf-8")
    for k in ["vendor", "date", "invoice_number", "total_amount", "currency", "vat_or_tax"]:
        print(f"    {k:16s} = {ex.get(k)!r}")
    print(f"    line_items       = {len(ex.get('line_items') or [])} items")

    print("\n[3] Ground-truth field accuracy vs synthetic source...")
    acc_checks, acc = check_accuracy(ex)
    for name, ok in acc_checks:
        print(f"    [{'OK' if ok else 'XX'}] {name}")
    print(f"    OCR accuracy: {acc*100:.0f}%")

    print("\n[4] Generating CSV via csv.js-equivalent port...")
    csv_bytes = generate_csv_bytes(ex)
    (OUT_DIR / "test_output.csv").write_bytes(csv_bytes)
    print(f"    -> test_output.csv ({len(csv_bytes)}B)")

    print("\n[5] Byte-level Excel compatibility validation...")
    csv_checks = validate_csv_bytes(csv_bytes)
    for name, ok, detail in csv_checks:
        print(f"    [{'OK' if ok else 'XX'}] {name:35s} {detail}")
    csv_pass = all(ok for _, ok, _ in csv_checks)

    print("\n" + "=" * 60)
    ocr_pass = acc >= 0.85
    print(f"§12 OCR reality:   {'PASS' if ocr_pass else 'FAIL'} ({acc*100:.0f}%)")
    print(f"§12 CSV reality:   {'PASS' if csv_pass else 'FAIL'}")
    overall = ocr_pass and csv_pass
    print(f"§12 OVERALL:       {'PASS' if overall else 'FAIL'}")
    print("=" * 60)
    return 0 if overall else 2


if __name__ == "__main__":
    sys.exit(main())
