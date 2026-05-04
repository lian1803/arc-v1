"""§12 Reality-Test helpers for invoice-snap (lib).

Split from driver per Hook D-prime 150 LOC gate. Generates synthetic
Korean 세금계산서 PNG, calls deployed Gemini prompt, ports csv.js logic,
and validates CSV bytes for Excel compatibility.
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

DEPLOYED_PROMPT = """You are an invoice/receipt field extractor. This may be a printed invoice, a handwritten receipt, a scanned document of low quality, or a photo taken at an angle. ALWAYS do your best to extract the fields, even from messy handwriting or poor scans — use context clues (typical invoice layout, surrounding text). Only use null if the field is genuinely absent or completely illegible after best effort.

Return ONLY valid JSON (no prose, no markdown fences).

Schema:
{
  "vendor": "string — 공급자/판매처 이름 (상호명)",
  "date": "YYYY-MM-DD (convert any date format to ISO)",
  "invoice_number": "string — 송장/계산서 번호",
  "total_amount": "number — digits only, no currency symbol, no commas",
  "currency": "KRW | USD | EUR | JPY | other",
  "vat_or_tax": "number — 부가세, null if none listed",
  "line_items": [ { "name": "string", "qty": "number", "unit_price": "number" } ],
  "confidence": { "vendor": "high|medium|low", "date": "high|medium|low", "invoice_number": "high|medium|low", "total_amount": "high|medium|low" }
}"""


def generate_sample_invoice(out_path: Path) -> Path:
    W, H = 800, 700
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_big = ImageFont.truetype(FONT_PATH, 32)
    f_mid = ImageFont.truetype(FONT_PATH, 20)
    f_sml = ImageFont.truetype(FONT_PATH, 16)

    d.text((W // 2 - 100, 30), "세금계산서", fill="black", font=f_big)
    d.line([(50, 80), (W - 50, 80)], fill="black", width=2)
    d.text((50, 110), "공급자: (주)서울테크코리아", fill="black", font=f_mid)
    d.text((50, 145), "사업자번호: 214-86-12345", fill="black", font=f_sml)
    d.text((50, 180), "작성일자: 2026-04-20", fill="black", font=f_mid)
    d.text((50, 215), "송장번호: SK-2026-00412", fill="black", font=f_mid)
    d.text((50, 250), "공급받는자: (주)리안컴퍼니", fill="black", font=f_mid)

    d.line([(50, 300), (W - 50, 300)], fill="black", width=1)
    d.text((50, 310), "품목 / 수량 / 단가 / 금액", fill="black", font=f_mid)
    d.line([(50, 345), (W - 50, 345)], fill="black", width=1)
    d.text((50, 360), "클라우드 서버 호스팅  |  1  |  500,000  |  500,000", fill="black", font=f_sml)
    d.text((50, 395), "개발 컨설팅 (시간제)   |  10 |  80,000   |  800,000", fill="black", font=f_sml)
    d.line([(50, 450), (W - 50, 450)], fill="black", width=1)
    d.text((50, 470), "공급가액: 1,300,000 원", fill="black", font=f_mid)
    d.text((50, 505), "부가세(VAT 10%): 130,000 원", fill="black", font=f_mid)
    d.text((50, 540), "합계금액: 1,430,000 원 (KRW)", fill="black", font=f_big)

    img.save(out_path, "PNG")
    return out_path


def call_gemini_vision(img_path: Path, api_key: str) -> dict:
    b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [
        {"text": DEPLOYED_PROMPT},
        {"inlineData": {"mimeType": "image/png", "data": b64}},
    ]}]}
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise
        return json.loads(m.group(0))


def generate_csv_bytes(ex: dict) -> bytes:
    def s(v): return "" if v is None else str(v)
    lines = ex.get("line_items") or []
    lines_txt = "; ".join(f"{it.get('name','')} x{it.get('qty','')} @ {it.get('unit_price','')}" for it in lines)
    header = ["공급자", "날짜", "송장번호", "금액", "통화", "부가세", "품목"]
    row = [s(ex.get("vendor")), s(ex.get("date")), s(ex.get("invoice_number")),
           s(ex.get("total_amount")), s(ex.get("currency")), s(ex.get("vat_or_tax")), lines_txt]

    def esc(f): return '"' + str(f).replace('"', '""') + '"'
    content = "﻿" + ",".join(esc(f) for f in header) + "\r\n" + ",".join(esc(f) for f in row) + "\r\n"
    return content.encode("utf-8")


def validate_csv_bytes(b: bytes) -> list[tuple[str, bool, str]]:
    checks = [("UTF-8 BOM (EF BB BF)", b[:3] == b"\xef\xbb\xbf", b[:3].hex())]
    crlf_n = b.count(b"\r\n")
    checks.append(("CRLF line endings (== 2)", crlf_n == 2, f"count={crlf_n}"))
    try:
        text = b.decode("utf-8")
        checks.append(("UTF-8 decodes clean", True, "OK"))
    except UnicodeDecodeError as e:
        return checks + [("UTF-8 decodes clean", False, str(e))]
    lines = text.strip().split("\r\n")
    checks.append(("Header row present", "공급자" in lines[0] and "품목" in lines[0], lines[0][:60]))
    checks.append(("Data row present", len(lines) >= 2, f"lines={len(lines)}"))
    if len(lines) >= 2:
        has_ko = any(0xAC00 <= ord(c) <= 0xD7A3 for c in lines[1])
        checks.append(("Korean chars survive in data row", has_ko, lines[1][:80]))
    return checks
