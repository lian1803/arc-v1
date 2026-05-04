"""Sharpening / detail-enhance — 사진 편집기 "선명도" 슬라이더 효과.

PIL 기반, 무료, 즉시. AI 변형 0. super-res 아님 (해상도 그대로).

사용:
    python tools/image/sharpen.py unsharp input.png --radius 2 --percent 150 --threshold 3
    python tools/image/sharpen.py detail input.png
    python tools/image/sharpen.py edge input.png
    python tools/image/sharpen.py sharpness input.png --factor 1.5
    python tools/image/sharpen.py contrast input.png --factor 1.2
    python tools/image/sharpen.py compose input.png  # unsharp + sharpness + 약간 contrast
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ARC_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ARC_ROOT / "tools" / "image" / "_out"


def _make_out(out: str | None, prefix: str) -> Path:
    if out:
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUT_DIR / f"{prefix}_{ts}.png"


def _open(path: str) -> Image.Image:
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def unsharp(path: str, radius: float = 2.0, percent: int = 150, threshold: int = 3, out: str | None = None) -> Path:
    """Unsharp Mask — 사진 편집기 "선명도" 슬라이더와 가장 가까움. 표준 sharpening."""
    img = _open(path)
    res = img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))
    out_path = _make_out(out, "unsharp")
    res.save(out_path)
    return out_path


def detail(path: str, out: str | None = None) -> Path:
    """ImageFilter.DETAIL — 디테일 강화 (Unsharp보다 살짝 부드러움)."""
    img = _open(path)
    res = img.filter(ImageFilter.DETAIL)
    out_path = _make_out(out, "detail")
    res.save(out_path)
    return out_path


def edge(path: str, more: bool = False, out: str | None = None) -> Path:
    """EDGE_ENHANCE 또는 EDGE_ENHANCE_MORE — 경계선 강조."""
    img = _open(path)
    f = ImageFilter.EDGE_ENHANCE_MORE if more else ImageFilter.EDGE_ENHANCE
    res = img.filter(f)
    out_path = _make_out(out, "edge_more" if more else "edge")
    res.save(out_path)
    return out_path


def sharpness(path: str, factor: float = 1.5, out: str | None = None) -> Path:
    """ImageEnhance.Sharpness — 부드러운 sharpness 조절. factor 1.0 = 원본, 2.0 = 강함."""
    img = _open(path)
    res = ImageEnhance.Sharpness(img).enhance(factor)
    out_path = _make_out(out, f"sharpness_{factor}")
    res.save(out_path)
    return out_path


def contrast(path: str, factor: float = 1.15, out: str | None = None) -> Path:
    """ImageEnhance.Contrast — 명암 살짝 ↑ (디테일 보강 효과)."""
    img = _open(path)
    res = ImageEnhance.Contrast(img).enhance(factor)
    out_path = _make_out(out, f"contrast_{factor}")
    res.save(out_path)
    return out_path


def compose(path: str, out: str | None = None) -> Path:
    """Unsharp Mask + Sharpness 1.3 + Contrast 1.1 — 균형잡힌 "사진 편집기 선명도" 효과."""
    img = _open(path)
    res = img.filter(ImageFilter.UnsharpMask(radius=2.0, percent=120, threshold=3))
    res = ImageEnhance.Sharpness(res).enhance(1.3)
    res = ImageEnhance.Contrast(res).enhance(1.1)
    out_path = _make_out(out, "compose")
    res.save(out_path)
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(description="PIL 기반 sharpening — 사진 편집기 '선명도' 효과")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_u = sub.add_parser("unsharp", help="★ Unsharp Mask (사진 편집기 선명도와 가장 같음)")
    sp_u.add_argument("input")
    sp_u.add_argument("--radius", type=float, default=2.0)
    sp_u.add_argument("--percent", type=int, default=150)
    sp_u.add_argument("--threshold", type=int, default=3)
    sp_u.add_argument("--out")

    sp_d = sub.add_parser("detail", help="DETAIL 필터")
    sp_d.add_argument("input")
    sp_d.add_argument("--out")

    sp_e = sub.add_parser("edge", help="EDGE_ENHANCE")
    sp_e.add_argument("input")
    sp_e.add_argument("--more", action="store_true", help="EDGE_ENHANCE_MORE (더 강함)")
    sp_e.add_argument("--out")

    sp_s = sub.add_parser("sharpness", help="ImageEnhance.Sharpness")
    sp_s.add_argument("input")
    sp_s.add_argument("--factor", type=float, default=1.5)
    sp_s.add_argument("--out")

    sp_c = sub.add_parser("contrast", help="ImageEnhance.Contrast")
    sp_c.add_argument("input")
    sp_c.add_argument("--factor", type=float, default=1.15)
    sp_c.add_argument("--out")

    sp_co = sub.add_parser("compose", help="★ Unsharp + Sharpness + Contrast 조합 (균형)")
    sp_co.add_argument("input")
    sp_co.add_argument("--out")

    args = p.parse_args()

    if args.cmd == "unsharp":
        r = unsharp(args.input, args.radius, args.percent, args.threshold, args.out)
    elif args.cmd == "detail":
        r = detail(args.input, args.out)
    elif args.cmd == "edge":
        r = edge(args.input, args.more, args.out)
    elif args.cmd == "sharpness":
        r = sharpness(args.input, args.factor, args.out)
    elif args.cmd == "contrast":
        r = contrast(args.input, args.factor, args.out)
    elif args.cmd == "compose":
        r = compose(args.input, args.out)
    else:
        return 1

    print(f"[sharpen] saved: {r}  ({r.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
