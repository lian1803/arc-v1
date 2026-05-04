"""Detail-restore upscale via fal.ai.

3媛吏 紐⑤뱶:
- clarity   ??clarity-upscaler (Real-ESRGAN + ControlNet Tile + AI ?뷀뀒??異붽?) ???移?沅뚯옣
- face      ??GFPGAN v1.4 (?쇨뎬 ?뷀뀒???뚮났 ?뱁솕, 鍮좊쫫)
- codeformer ??CodeFormer (?쇨뎬 + ?먯뿰?ㅻ윭?)

?ъ슜:
    python tools/image/upscale.py clarity input.png --scale 2 --creativity 0.35
    python tools/image/upscale.py face input.png
    python tools/image/upscale.py codeformer input.png --fidelity 0.5

鍮꾩슜 (???:
    clarity:    ~$0.02 / image
    face:       ~$0.005 / image
    codeformer: ~$0.005 / image
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

import fal_client  # noqa: E402
import requests  # noqa: E402

DEFAULT_OUT_DIR = ARC_ROOT / "tools" / "image" / "_out"


def _load_key() -> str:
    key = os.getenv("FAL_KEY", "")
    if not key:
        env = ARC_ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("FAL_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise RuntimeError("FAL_KEY missing (.env or env var)")
    os.environ["FAL_KEY"] = key
    return key


def _mime_for(p: Path) -> str:
    s = p.suffix.lower()
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(s, "image/png")


def _upload_safe(src: Path) -> str:
    """fal CDN upload ??URL. fail ??base64 data URL fallback."""
    try:
        return fal_client.upload_file(str(src))
    except Exception as e:
        import base64 as _b64
        sys.stderr.write(f"[fal upload_file fail: {str(e)[:120]}; fallback base64]\n")
        b = _b64.b64encode(src.read_bytes()).decode()
        return f"data:{_mime_for(src)};base64,{b}"


def _make_out(out: str | None, prefix: str) -> Path:
    if out:
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUT_DIR / f"{prefix}_{ts}.png"


def _extract_image_url(result: dict) -> str | None:
    if isinstance(result.get("image"), dict):
        u = result["image"].get("url")
        if u:
            return u
    imgs = result.get("images") or []
    if imgs and isinstance(imgs[0], dict):
        return imgs[0].get("url")
    return None


def _download(url: str, out_path: Path) -> int:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    out_path.write_bytes(r.content)
    return len(r.content)


def clarity(input_path: str, scale: int = 2, creativity: float = 0.35,
            prompt: str | None = None, out: str | None = None) -> Path:
    """Clarity Upscaler ??Real-ESRGAN + Tile + AI ?뷀뀒??異붽?. ???移?沅뚯옣."""
    _load_key()
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(input_path)
    t0 = time.time()

    image_url = _upload_safe(src)
    args = {
        "image_url": image_url,
        "upscale_factor": scale,
        "creativity": creativity,
        "guidance_scale": 4,
        "num_inference_steps": 18,
        "resemblance": 0.6,
    }
    if prompt:
        args["prompt"] = prompt

    result = fal_client.subscribe("fal-ai/clarity-upscaler", arguments=args, with_logs=False)
    img_url = _extract_image_url(result)
    if not img_url:
        raise RuntimeError(f"no image url in result keys: {list(result.keys())}")

    out_path = _make_out(out, "clarity")
    out_bytes = _download(img_url, out_path)
    log_call(
        tool="upscale.clarity",
        model="fal:clarity-upscaler",
        metadata={
            "input": str(src)[:200],
            "scale": scale,
            "creativity": creativity,
            "prompt_preview": (prompt or "")[:100],
            "out_bytes": out_bytes,
            "duration_ms": int((time.time() - t0) * 1000),
        },
    )
    return out_path


def face(input_path: str, version: str = "v1.4", scale: int = 2, out: str | None = None) -> Path:
    """GFPGAN ???쇨뎬 ?뷀뀒???뚮났 ?뱁솕. 鍮좊Ⅴ怨????"""
    _load_key()
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(input_path)
    t0 = time.time()

    image_url = _upload_safe(src)
    result = fal_client.subscribe(
        "fal-ai/gfpgan",
        arguments={"image_url": image_url, "version": version, "scale": scale},
        with_logs=False,
    )
    img_url = _extract_image_url(result)
    if not img_url:
        raise RuntimeError(f"no image url in result keys: {list(result.keys())}")

    out_path = _make_out(out, "face")
    out_bytes = _download(img_url, out_path)
    log_call(
        tool="upscale.face",
        model="fal:gfpgan",
        metadata={"input": str(src)[:200], "version": version, "scale": scale, "out_bytes": out_bytes, "duration_ms": int((time.time() - t0) * 1000)},
    )
    return out_path


def esrgan(input_path: str, scale: int = 4, face_enhance: bool = False, model: str = "RealESRGAN_x4plus",
           out: str | None = None) -> Path:
    """Real-ESRGAN ??蹂댁〈??super-resolution. ?쇨뎬 蹂??X. ??"?⑥닚 ?좊챸???? 耳?댁뒪 沅뚯옣."""
    _load_key()
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(input_path)
    t0 = time.time()

    image_url = _upload_safe(src)
    args = {
        "image_url": image_url,
        "scale": scale,
        "model": model,
        "face": face_enhance,
    }
    result = fal_client.subscribe("fal-ai/esrgan", arguments=args, with_logs=False)
    img_url = _extract_image_url(result)
    if not img_url:
        raise RuntimeError(f"no image url in result keys: {list(result.keys())}")

    out_path = _make_out(out, "esrgan")
    out_bytes = _download(img_url, out_path)
    log_call(
        tool="upscale.esrgan",
        model="fal:esrgan",
        metadata={"input": str(src)[:200], "scale": scale, "model_variant": model, "face_enhance": face_enhance, "out_bytes": out_bytes, "duration_ms": int((time.time() - t0) * 1000)},
    )
    return out_path


def aura(input_path: str, out: str | None = None) -> Path:
    """AuraSR ??4x super-res, photo 蹂댁〈??媛뺥븿. ?쇨뎬 蹂??嫄곗쓽 X."""
    _load_key()
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(input_path)
    t0 = time.time()

    image_url = _upload_safe(src)
    result = fal_client.subscribe(
        "fal-ai/aura-sr",
        arguments={"image_url": image_url, "upscaling_factor": 4},
        with_logs=False,
    )
    img_url = _extract_image_url(result)
    if not img_url:
        raise RuntimeError(f"no image url in result keys: {list(result.keys())}")

    out_path = _make_out(out, "aura")
    out_bytes = _download(img_url, out_path)
    log_call(
        tool="upscale.aura",
        model="fal:aura-sr",
        metadata={"input": str(src)[:200], "out_bytes": out_bytes, "duration_ms": int((time.time() - t0) * 1000)},
    )
    return out_path


def codeformer(input_path: str, fidelity: float = 0.5, scale: int = 2, out: str | None = None) -> Path:
    """CodeFormer ???쇨뎬 蹂듭썝, fidelity ?믪쓣?섎줉 ?먮낯 蹂댁〈."""
    _load_key()
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(input_path)
    t0 = time.time()

    image_url = _upload_safe(src)
    result = fal_client.subscribe(
        "fal-ai/codeformer",
        arguments={"image_url": image_url, "fidelity": fidelity, "upscaling": scale},
        with_logs=False,
    )
    img_url = _extract_image_url(result)
    if not img_url:
        raise RuntimeError(f"no image url in result keys: {list(result.keys())}")

    out_path = _make_out(out, "codeformer")
    out_bytes = _download(img_url, out_path)
    log_call(
        tool="upscale.codeformer",
        model="fal:codeformer",
        metadata={"input": str(src)[:200], "fidelity": fidelity, "scale": scale, "out_bytes": out_bytes, "duration_ms": int((time.time() - t0) * 1000)},
    )
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(description="Detail-restore upscale via fal.ai")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_c = sub.add_parser("clarity", help="Clarity Upscaler (???移?沅뚯옣, AI ?뷀뀒??異붽?)")
    sp_c.add_argument("input")
    sp_c.add_argument("--scale", type=int, default=2)
    sp_c.add_argument("--creativity", type=float, default=0.35,
                      help="0.1 (?먮낯 蹂댁〈) ~ 0.9 (蹂??. default 0.35.")
    sp_c.add_argument("--prompt", help="?듭뀡 ???뷀뀒??媛?대뱶 (?? 'photographic, sharp skin pores')")
    sp_c.add_argument("--out")

    sp_f = sub.add_parser("face", help="GFPGAN (?쇨뎬 ?뷀뀒???뚮났)")
    sp_f.add_argument("input")
    sp_f.add_argument("--version", default="v1.4")
    sp_f.add_argument("--scale", type=int, default=2)
    sp_f.add_argument("--out")

    sp_e = sub.add_parser("esrgan", help="??Real-ESRGAN ??蹂댁〈??(?쇨뎬 蹂??X, ?⑥닚 ?좊챸??")
    sp_e.add_argument("input")
    sp_e.add_argument("--scale", type=int, default=4)
    sp_e.add_argument("--face-enhance", action="store_true", help="GFPGAN ?쇨뎬 蹂닿컯 (?듭뀡)")
    sp_e.add_argument("--model", default="RealESRGAN_x4plus")
    sp_e.add_argument("--out")

    sp_a = sub.add_parser("aura", help="AuraSR ????4x 紐⑤뜽, 蹂댁〈??醫뗭쓬")
    sp_a.add_argument("input")
    sp_a.add_argument("--out")

    sp_cf = sub.add_parser("codeformer", help="CodeFormer (?쇨뎬 + ?먯뿰?ㅻ윭?)")
    sp_cf.add_argument("input")
    sp_cf.add_argument("--fidelity", type=float, default=0.5,
                       help="0.0 (媛뺥븳 蹂듭썝) ~ 1.0 (?먮낯 蹂댁〈). default 0.5.")
    sp_cf.add_argument("--scale", type=int, default=2)
    sp_cf.add_argument("--out")

    args = p.parse_args()

    if args.cmd == "clarity":
        r = clarity(args.input, args.scale, args.creativity, args.prompt, args.out)
    elif args.cmd == "face":
        r = face(args.input, args.version, args.scale, args.out)
    elif args.cmd == "esrgan":
        r = esrgan(args.input, args.scale, args.face_enhance, args.model, args.out)
    elif args.cmd == "aura":
        r = aura(args.input, args.out)
    elif args.cmd == "codeformer":
        r = codeformer(args.input, args.fidelity, args.scale, args.out)
    else:
        return 1

    print(f"[upscale] saved: {r}  ({r.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
