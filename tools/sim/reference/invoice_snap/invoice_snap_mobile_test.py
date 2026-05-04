"""Cycle 5b — mobile viewport test for invoice-snap.

Emulates iPhone 14 (390x844) and verifies: no horizontal scroll, hero
visible, dropzone accessible, beta banner readable, batch table
renders without overflow when populated.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from invoice_snap_variant_gen import korean_tax_invoice

ARC = Path(__file__).resolve().parent.parent
OUT = ARC / "shared" / "message_pool" / "invoice_snap_build" / "mobile_test"
LIVE = "https://invoice-snap.pages.dev"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print(f"§12.1 cycle 5b — mobile viewport — {LIVE}")
    print("=" * 70)

    with sync_playwright() as pw:
        iphone = pw.devices["iPhone 14"]
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(**iphone)
        page = ctx.new_page()
        page.goto(LIVE, timeout=30000)

        print("\n[1] Viewport + overflow...")
        vp = iphone["viewport"]
        print(f"    viewport: {vp['width']}x{vp['height']}")
        overflow = page.evaluate("""() => ({
            scrollWidth: document.body.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
            scrollHeight: document.body.scrollHeight,
        })""")
        no_hscroll = overflow['scrollWidth'] <= overflow['clientWidth'] + 2
        print(f"    scrollWidth={overflow['scrollWidth']}, clientWidth={overflow['clientWidth']}")
        print(f"    [{'OK' if no_hscroll else 'XX'}] no horizontal overflow")

        print("\n[2] Hero visibility...")
        hero = page.query_selector(".hero-title")
        hero_visible = hero.is_visible() if hero else False
        hero_text = hero.inner_text() if hero else ""
        print(f"    [{'OK' if hero_visible else 'XX'}] hero-title visible — {hero_text[:60]!r}")

        print("\n[3] Beta banner readable...")
        banner = page.query_selector(".beta-banner")
        banner_visible = banner.is_visible() if banner else False
        banner_text = banner.inner_text() if banner else ""
        print(f"    [{'OK' if banner_visible else 'XX'}] beta-banner visible — {banner_text[:80]!r}")

        print("\n[4] Dropzone accessible...")
        dz = page.query_selector("#dropZone")
        dz_visible = dz.is_visible() if dz else False
        if dz:
            box = dz.bounding_box()
            print(f"    dropzone bounding box: {box}")
            dz_fits = box['x'] >= 0 and (box['x'] + box['width']) <= vp['width'] + 2
        else:
            dz_fits = False
        print(f"    [{'OK' if dz_visible and dz_fits else 'XX'}] dropzone visible + within viewport")

        print("\n[5] Batch table renders without overflow (populated)...")
        pngs = []
        for n in range(2):
            png, _ = korean_tax_invoice(f"(주)모바일테스트{n}", f"2026-04-{20+n:02d}",
                                         f"MOB-{n:03d}", [("품목", 1, 10000 * (n + 1))])
            p = OUT / f"mobile_sample_{n}.png"
            p.write_bytes(png)
            pngs.append(str(p))

        page.locator("#fileInput").set_input_files(pngs)
        page.wait_for_selector("#batchTable", state="visible", timeout=10000)
        for i in range(2):
            page.wait_for_function(
                f"document.querySelector('#status-{i}')?.textContent === '완료'",
                timeout=90000)

        table_overflow = page.evaluate("""() => {
            const t = document.querySelector('#batchTable');
            return t ? { sw: t.scrollWidth, cw: t.clientWidth, bw: document.body.scrollWidth } : null;
        }""")
        print(f"    table: {table_overflow}")
        table_fits = table_overflow and table_overflow['bw'] <= vp['width'] + 30
        print(f"    [{'OK' if table_fits else 'XX'}] batch table does not push body beyond viewport")

        page.screenshot(path=str(OUT / "mobile_full.png"), full_page=True)
        print(f"\n    screenshot -> mobile_full.png")

        browser.close()

    checks = [no_hscroll, hero_visible, banner_visible, dz_visible and dz_fits, table_fits]
    passed = sum(checks)
    print("\n" + "=" * 70)
    print(f"§12.1 cycle 5b mobile: {passed}/5 passed")
    print("=" * 70)
    return 0 if passed == 5 else 2


if __name__ == "__main__":
    sys.exit(main())
