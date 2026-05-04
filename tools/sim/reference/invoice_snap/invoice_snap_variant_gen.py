"""Diverse invoice variant generator for §12 regression testing.

Produces Korean 세금계산서, Korean 영수증, foreign invoices, and
adversarial variants (rotation, blur, low contrast, handwriting-like).
Each variant returns (png_bytes, ground_truth_dict, variant_name).
"""

from __future__ import annotations

import io
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "C:/Windows/Fonts/malgun.ttf"


def _fonts():
    return (ImageFont.truetype(FONT, 32),
            ImageFont.truetype(FONT, 20),
            ImageFont.truetype(FONT, 16))


def _img_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def korean_tax_invoice(vendor: str, date: str, inv_no: str, items: list, vat_rate: float = 0.10):
    big, mid, sml = _fonts()
    img = Image.new("RGB", (800, 700), "white")
    d = ImageDraw.Draw(img)
    d.text((340, 30), "세금계산서", fill="black", font=big)
    d.line([(50, 80), (750, 80)], fill="black", width=2)
    d.text((50, 110), f"공급자: {vendor}", fill="black", font=mid)
    d.text((50, 150), f"작성일자: {date}", fill="black", font=mid)
    d.text((50, 190), f"송장번호: {inv_no}", fill="black", font=mid)
    y = 250
    d.text((50, y), "품목 / 수량 / 단가 / 금액", fill="black", font=mid)
    y += 30
    subtotal = 0
    for name, qty, unit in items:
        amt = qty * unit
        subtotal += amt
        d.text((50, y), f"{name} | {qty} | {unit:,} | {amt:,}", fill="black", font=sml)
        y += 30
    vat = int(subtotal * vat_rate)
    total = subtotal + vat
    d.line([(50, y + 10), (750, y + 10)], fill="black", width=1)
    d.text((50, y + 30), f"공급가액: {subtotal:,} 원", fill="black", font=mid)
    d.text((50, y + 65), f"부가세: {vat:,} 원", fill="black", font=mid)
    d.text((50, y + 100), f"합계: {total:,} 원 (KRW)", fill="black", font=big)
    gt = {"vendor": vendor, "date": date, "invoice_number": inv_no,
          "total_amount": total, "currency": "KRW", "vat_or_tax": vat,
          "line_items_count": len(items)}
    return _img_bytes(img), gt


def korean_receipt(vendor: str, date: str, inv_no: str, total: int):
    big, mid, sml = _fonts()
    img = Image.new("RGB", (500, 400), "white")
    d = ImageDraw.Draw(img)
    d.text((180, 20), "영수증", fill="black", font=big)
    d.text((50, 80), vendor, fill="black", font=mid)
    d.text((50, 115), f"일자: {date}", fill="black", font=sml)
    d.text((50, 145), f"No: {inv_no}", fill="black", font=sml)
    d.line([(50, 180), (450, 180)], fill="black", width=1)
    d.text((50, 210), f"합계: {total:,} 원", fill="black", font=big)
    d.text((50, 270), "※ 부가세 별도 아님 (간이영수증)", fill="black", font=sml)
    gt = {"vendor": vendor, "date": date, "invoice_number": inv_no,
          "total_amount": total, "currency": "KRW", "vat_or_tax": None,
          "line_items_count": 0}
    return _img_bytes(img), gt


def foreign_invoice(vendor: str, date: str, inv_no: str, items: list, currency: str):
    big, mid, sml = _fonts()
    img = Image.new("RGB", (800, 600), "white")
    d = ImageDraw.Draw(img)
    d.text((320, 30), "INVOICE", fill="black", font=big)
    d.text((50, 110), f"From: {vendor}", fill="black", font=mid)
    d.text((50, 150), f"Date: {date}", fill="black", font=mid)
    d.text((50, 190), f"Invoice #: {inv_no}", fill="black", font=mid)
    y = 250
    subtotal = 0
    for name, qty, unit in items:
        amt = qty * unit
        subtotal += amt
        d.text((50, y), f"{name}  x{qty}  @ {unit}  = {amt}", fill="black", font=sml)
        y += 28
    d.line([(50, y + 10), (750, y + 10)], fill="black", width=1)
    d.text((50, y + 30), f"Total: {subtotal:,} {currency}", fill="black", font=big)
    gt = {"vendor": vendor, "date": date, "invoice_number": inv_no,
          "total_amount": subtotal, "currency": currency, "vat_or_tax": None,
          "line_items_count": len(items)}
    return _img_bytes(img), gt


def apply_defect(png_bytes: bytes, defect: str) -> bytes:
    img = Image.open(io.BytesIO(png_bytes))
    if defect == "rotate5":
        img = img.rotate(5, fillcolor="white", expand=True)
    elif defect == "rotate-8":
        img = img.rotate(-8, fillcolor="white", expand=True)
    elif defect == "blur":
        img = img.filter(ImageFilter.GaussianBlur(radius=1.3))
    elif defect == "low_contrast":
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y][:3]
                pixels[x, y] = (min(255, r + 90), min(255, g + 90), min(255, b + 90))
    elif defect == "crop_top":
        img = img.crop((0, 80, img.width, img.height))
    return _img_bytes(img)
