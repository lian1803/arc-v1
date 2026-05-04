"""Recraft V3 base + Pillow Pro overlay (drop shadow + gradient + layered)."""
import os, requests, time
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
load_dotenv(".env")
FK = os.environ["FAL_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_v4_pro"
DEST.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"


def fal_recraft(prompt):
    H = {"Authorization": f"Key {FK}", "Content-Type": "application/json"}
    r = requests.post("https://queue.fal.run/fal-ai/recraft-v3", headers=H,
        json={"prompt": prompt, "image_size": "landscape_16_9", "style": "realistic_image"}, timeout=60)
    r.raise_for_status()
    data = r.json()
    sid, rid = data["status_url"], data["response_url"]
    for _ in range(60):
        time.sleep(2)
        s = requests.get(sid, headers=H, timeout=30).json()
        if s.get("status") == "COMPLETED":
            break
    out = requests.get(rid, headers=H, timeout=30).json()
    return requests.get(out["images"][0]["url"], timeout=60).content


def shadow_outline(canvas, x, y, text, font, fill, outline=5):
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 6, y + 6), text, font=font, fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    canvas.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(canvas)
    for dx in range(-outline, outline + 1, 2):
        for dy in range(-outline, outline + 1, 2):
            d.text((x + dx, y + dy), text, font=font, fill="black")
    d.text((x, y), text, font=font, fill=fill)


def gradient_text(canvas, x, y, text, font, top, bot, outline=5):
    bbox = ImageDraw.Draw(canvas).textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 6, y + 6), text, font=font, fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    canvas.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(canvas)
    for dx in range(-outline, outline + 1, 2):
        for dy in range(-outline, outline + 1, 2):
            d.text((x + dx, y + dy), text, font=font, fill="black")
    text_layer = Image.new("RGBA", (tw + 30, th + 30), (0, 0, 0, 0))
    ImageDraw.Draw(text_layer).text((10, 5), text, font=font, fill="white")
    grad = Image.new("RGBA", text_layer.size, (0, 0, 0, 0))
    for gy in range(text_layer.height):
        ratio = gy / text_layer.height
        r = int(top[0] * (1 - ratio) + bot[0] * ratio)
        g = int(top[1] * (1 - ratio) + bot[1] * ratio)
        b = int(top[2] * (1 - ratio) + bot[2] * ratio)
        ImageDraw.Draw(grad).line([(0, gy), (text_layer.width, gy)], fill=(r, g, b, 255))
    grad.putalpha(text_layer.split()[3])
    canvas.paste(grad, (x - 10, y - 5), grad)


def fit(img_bytes, tw, th, focus="r"):
    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    new = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    nw, nh = new.size
    left = 0 if focus == "l" else (nw - tw) if focus == "r" else (nw - tw) // 2
    return new.crop((left, (nh - th) // 2, left + tw, (nh - th) // 2 + th))


def badge(canvas):
    d = ImageDraw.Draw(canvas)
    bx, by, bw, bh = 1040, 20, 220, 70
    d.rectangle([bx, by, bx + bw, by + bh], fill=(0, 0, 0))
    d.rectangle([bx, by, bx + bw, by + bh], outline=(255, 235, 30), width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = d.textbbox((0, 0), "건강정보", font=f)
    d.text((bx + (bw - (bbox[2] - bbox[0])) // 2, by + 10), "건강정보", font=f, fill=(255, 235, 30))


print("[fetch] Recraft V3 person...", flush=True)
person = fal_recraft("Photorealistic 16:9 thumbnail. Korean man in his 60s, wise warm smile, white doctor coat, short salt-pepper hair, looking right of frame. Light gray plain studio background. Body on right 45% of frame, left 55% solid empty space. Clean professional Korean YouTuber portrait, sharp focus on face, no text, no logos.")
canvas = Image.new("RGB", (1280, 720), (10, 10, 10))
canvas.paste(fit(person, 580, 720, "r"), (700, 0))
d = ImageDraw.Draw(canvas, "RGBA")
for i in range(180):
    d.line([(700 + i, 0), (700 + i, 720)], fill=(10, 10, 10, 255 - int(255 * i / 180)))

fm = ImageFont.truetype(FONT, 92)
gradient_text(canvas, 40, 50, "60대 무릎 통증", fm, (255, 245, 100), (255, 200, 30))
gradient_text(canvas, 40, 180, "100% 없애는", fm, (255, 100, 60), (220, 30, 30))
shadow_outline(canvas, 40, 320, "단 1가지 음식 vs", fm, (255, 255, 255))
gradient_text(canvas, 40, 460, "최악의 습관 공개", fm, (255, 100, 60), (220, 30, 30))
badge(canvas)
canvas.save(DEST / "PRO_A.jpg", quality=94)
print(f"[done] {(DEST / 'PRO_A.jpg').stat().st_size / 1024:.0f}KB")
