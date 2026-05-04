"""Nano Banana — Gemini 2.5 Flash Image API.

웹 Gemini의 "나노바나나" = `gemini-2.5-flash-image-preview` API. 같은 backend, 더 강력 (배치/자동화).

기능 3개:
- generate(prompt) — 텍스트 → 이미지 (text-to-image)
- edit(image, prompt) — 이미지 1장 + 명령 → 편집된 이미지
- fuse([img1, img2, ...], prompt) — 여러 이미지 합성 (★ 핵심)

사용:
    python tools/image/nano_banana.py generate "한국 카페 셀카, 자연광"
    python tools/image/nano_banana.py edit my.jpg "배경만 카페로"
    python tools/image/nano_banana.py fuse selfie.jpg outfit.jpg --prompt "이 옷 입은 모습"

비용: 이미지 1장당 약 $0.039 (Gemini 2.5 Flash Image).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ARC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARC_ROOT))
from tools.cost.cost_log import log_call  # noqa: E402

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

# 모델 옵션 (2026-05-03 ListModels 확인):
#   gemini-2.5-flash-image          — 안정 정식 (default)
#   gemini-3.1-flash-image-preview  — 최신 3.1 preview (성능 ↑)
#   nano-banana-pro-preview         — Nano Banana Pro (한국 얼굴 강함, Pro 가격)
#   gemini-3-pro-image-preview      — Gemini 3 Pro (가장 강력, 가장 비쌈)
MODEL = os.environ.get("NANO_BANANA_MODEL", "gemini-2.5-flash-image")
DEFAULT_OUT_DIR = ARC_ROOT / "tools" / "image" / "_out"


def _load_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        env = ARC_ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing (.env or env var)")
    return key


def _client() -> genai.Client:
    return genai.Client(api_key=_load_key())


def _mime_for(path: Path) -> str:
    suf = path.suffix.lower()
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".gif": "image/gif", ".bmp": "image/bmp",
    }.get(suf, f"image/{suf.lstrip('.')}")


def _make_out_path(out: str | None, prefix: str = "img") -> Path:
    if out:
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUT_DIR / f"{prefix}_{ts}.png"


def _save_images(response, base_out: Path) -> list[Path]:
    """Extract image bytes from Gemini response, save as PNG/JPG."""
    saved: list[Path] = []
    text_msgs: list[str] = []
    try:
        cand = response.candidates[0]
        parts = cand.content.parts if cand.content else []
    except (AttributeError, IndexError) as e:
        raise RuntimeError(f"Unexpected response shape: {e}; raw={str(response)[:500]}")

    img_count = 0
    for part in parts:
        if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
            img_count += 1
            p = base_out if img_count == 1 else base_out.with_stem(f"{base_out.stem}_{img_count}")
            p.write_bytes(part.inline_data.data)
            saved.append(p)
        elif getattr(part, "text", None):
            text_msgs.append(part.text)

    if not saved:
        msg = " | ".join(text_msgs)[:500] if text_msgs else "no parts returned"
        raise RuntimeError(f"No image returned. Model said: {msg}")
    return saved


def generate(prompt: str, out: str | None = None) -> list[Path]:
    """Text → Image."""
    t0 = time.time()
    client = _client()
    out_path = _make_out_path(out, prefix="gen")
    response = client.models.generate_content(model=MODEL, contents=prompt)
    saved = _save_images(response, out_path)
    log_call(
        tool="nano_banana.generate",
        model=f"gemini:{MODEL}",
        metadata={
            "prompt_preview": prompt[:200],
            "image_count": len(saved),
            "duration_ms": int((time.time() - t0) * 1000),
        },
    )
    return saved


def edit(input_image: str, prompt: str, out: str | None = None) -> list[Path]:
    """Image + Text → Edited image."""
    t0 = time.time()
    client = _client()
    src = Path(input_image)
    if not src.exists():
        raise FileNotFoundError(f"input image not found: {input_image}")
    img_bytes = src.read_bytes()
    mime = _mime_for(src)

    out_path = _make_out_path(out, prefix="edit")
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part(inline_data=types.Blob(mime_type=mime, data=img_bytes)),
            prompt,
        ],
    )
    saved = _save_images(response, out_path)
    log_call(
        tool="nano_banana.edit",
        model=f"gemini:{MODEL}",
        metadata={
            "input_image": str(src)[:200],
            "input_bytes": len(img_bytes),
            "prompt_preview": prompt[:200],
            "image_count": len(saved),
            "duration_ms": int((time.time() - t0) * 1000),
        },
    )
    return saved


def fuse(input_images: list[str], prompt: str, out: str | None = None) -> list[Path]:
    """Multiple images + Text → Fused image (★ Nano Banana 핵심)."""
    t0 = time.time()
    client = _client()
    parts: list = []
    total_bytes = 0
    for img_str in input_images:
        src = Path(img_str)
        if not src.exists():
            raise FileNotFoundError(f"input image not found: {img_str}")
        img_bytes = src.read_bytes()
        total_bytes += len(img_bytes)
        parts.append(types.Part(inline_data=types.Blob(mime_type=_mime_for(src), data=img_bytes)))
    parts.append(types.Part(text=prompt))

    out_path = _make_out_path(out, prefix="fuse")
    response = client.models.generate_content(model=MODEL, contents=parts)
    saved = _save_images(response, out_path)
    log_call(
        tool="nano_banana.fuse",
        model=f"gemini:{MODEL}",
        metadata={
            "input_count": len(input_images),
            "input_bytes_total": total_bytes,
            "prompt_preview": prompt[:200],
            "image_count": len(saved),
            "duration_ms": int((time.time() - t0) * 1000),
        },
    )
    return saved


def main() -> int:
    p = argparse.ArgumentParser(description="Nano Banana — Gemini 2.5 Flash Image API")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_gen = sub.add_parser("generate", help="텍스트 → 이미지")
    sp_gen.add_argument("prompt")
    sp_gen.add_argument("--out", help="저장 경로 (default: tools/image/_out/gen_TS.png)")

    sp_edit = sub.add_parser("edit", help="이미지 1장 + 명령 → 편집")
    sp_edit.add_argument("input_image")
    sp_edit.add_argument("prompt")
    sp_edit.add_argument("--out")

    sp_fuse = sub.add_parser("fuse", help="여러 이미지 + 명령 → 합성")
    sp_fuse.add_argument("input_images", nargs="+", help="이미지 path 1개 이상")
    sp_fuse.add_argument("--prompt", required=True)
    sp_fuse.add_argument("--out")

    args = p.parse_args()

    if args.cmd == "generate":
        r = generate(args.prompt, out=args.out)
    elif args.cmd == "edit":
        r = edit(args.input_image, args.prompt, out=args.out)
    elif args.cmd == "fuse":
        r = fuse(args.input_images, args.prompt, out=args.out)
    else:
        return 1

    print(f"[nano_banana] saved {len(r)} image(s):")
    for path in r:
        print(f"  {path}  ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
