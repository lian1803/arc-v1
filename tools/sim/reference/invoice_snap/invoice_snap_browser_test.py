"""§12.1 cycle 3 — real-browser batch UI test for invoice-snap.

Headless Chromium via Playwright. Uploads 3 synthetic invoices through
the actual file input, waits for queue to drain, downloads all 3 CSV
formats, validates each against expected schema.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from invoice_snap_variant_gen import korean_receipt, korean_tax_invoice

ARC = Path(__file__).resolve().parent.parent
OUT = ARC / "shared" / "message_pool" / "invoice_snap_build" / "browser_test"
LIVE = "https://invoice-snap.pages.dev"

SAMPLES = [
    ("sample1_tax", korean_tax_invoice(
        "(주)테스트코리아", "2026-04-22", "T-2604-0001",
        [("월 호스팅", 1, 100000)])),
    ("sample2_rcpt", korean_receipt("스타벅스 홍대", "2026-04-21", "SB210401", 15600)),
    ("sample3_tax", korean_tax_invoice(
        "(주)페이먼트", "2026-04-20", "P-2604-0020",
        [("월 구독", 1, 29000), ("수수료", 1, 2900)])),
]


def write_samples() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, (png_bytes, _gt) in SAMPLES:
        p = OUT / f"{name}.png"
        p.write_bytes(png_bytes)
        paths.append(p)
    return paths


def validate_csv(content: str, fmt: str) -> list[tuple[str, bool, str]]:
    checks = []
    has_bom = content.startswith("﻿")
    checks.append(("UTF-8 BOM", has_bom, content[:1].encode("utf-8").hex()))
    stripped = content.lstrip("﻿")
    lines = [l for l in stripped.split("\r\n") if l]
    checks.append(("rows count >= 4 (1 header + 3 data)", len(lines) >= 4, f"count={len(lines)}"))
    if not lines:
        return checks
    header = lines[0]
    if fmt == "kr":
        expected = ["공급자", "날짜", "송장번호", "금액", "통화", "부가세", "품목"]
    elif fmt == "xero":
        expected = ["ContactName", "InvoiceNumber", "InvoiceDate", "Description", "Quantity"]
    else:
        expected = ["거래처", "전표일자", "증빙번호", "공급가액", "부가세", "합계", "적요"]
    missing = [e for e in expected if e not in header]
    checks.append((f"{fmt} header has required cols", not missing, f"missing={missing}"))
    if len(lines) >= 4:
        korean_in_data = any(0xAC00 <= ord(c) <= 0xD7A3 for c in lines[1])
        checks.append(("Korean chars in data row", korean_in_data, lines[1][:80]))
    return checks


def main() -> int:
    paths = write_samples()
    results = {"downloads": {}}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        print("=" * 70)
        print(f"§12.1 BROWSER cycle 3 — {LIVE}")
        print("=" * 70)

        page.goto(LIVE, timeout=30000)
        print(f"\n[1] Loaded: {page.title()}")
        assert page.eval_on_selector("#fileInput", "el => el.hasAttribute('multiple')"), "multiple missing"

        print(f"\n[2] Uploading {len(paths)} files via set_input_files...")
        page.locator("#fileInput").set_input_files([str(p) for p in paths])

        print("\n[3] Waiting for batch table + all 3 rows to reach 완료...")
        page.wait_for_selector("#batchTable", state="visible", timeout=10000)
        for i in range(len(paths)):
            page.wait_for_function(
                f"document.querySelector('#status-{i}')?.textContent === '완료'",
                timeout=90000)
            print(f"    row {i}: 완료")

        vendor_vals = page.eval_on_selector_all(
            "[id^=vendor-]", "els => els.map(e => e.value)")
        amount_vals = page.eval_on_selector_all(
            "[id^=amount-]", "els => els.map(e => e.value)")
        print(f"    extracted vendors: {vendor_vals}")
        print(f"    extracted amounts: {amount_vals}")

        print("\n[4] Clicking 3 download buttons + capturing CSV contents...")
        for fmt, btn_id in [("kr", "downloadKrBtn"), ("xero", "downloadXeroBtn"),
                            ("douzone", "downloadDoozoneBtn")]:
            with page.expect_download(timeout=15000) as dl_info:
                page.click(f"#{btn_id}")
            dl = dl_info.value
            out_path = OUT / f"dl_{fmt}.csv"
            dl.save_as(out_path)
            content = out_path.read_bytes().decode("utf-8")
            checks = validate_csv(content, fmt)
            ok_count = sum(1 for _, ok, _ in checks if ok)
            print(f"    [{fmt}] downloaded {out_path.name} ({len(content)}B), "
                  f"{ok_count}/{len(checks)} checks pass")
            for n, ok, d in checks:
                print(f"      [{'OK' if ok else 'XX'}] {n:45s} {d}")
            results["downloads"][fmt] = {"bytes": len(content), "checks": ok_count,
                                          "total": len(checks)}

        browser.close()

    print("\n" + "=" * 70)
    all_ok = all(d["checks"] == d["total"] for d in results["downloads"].values())
    print(f"§12.1 BROWSER cycle 3: {'PASS' if all_ok else 'FAIL'}")
    print("=" * 70)
    return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(main())
