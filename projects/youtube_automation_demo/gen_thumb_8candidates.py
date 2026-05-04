"""8 image base variations × 동일 Pillow Pro 텍스트 = 후보군."""
import os, requests, time
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
load_dotenv(".env")
FK = os.environ["FAL_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_FINAL"
DEST.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"
H = {"Authorization": f"Key {FK}", "Content-Type": "application/json"}


def fal(prompt):
    r = requests.post("https://queue.fal.run/fal-ai/recraft-v3", headers=H,
        json={"prompt": prompt, "image_size": "landscape_16_9", "style": "realistic_image"}, timeout=60)
    r.raise_for_status()
    d = r.json()
    for _ in range(60):
        time.sleep(2)
        if requests.get(d["status_url"], headers=H, timeout=30).json().get("status") == "COMPLETED":
            break
    out = requests.get(d["response_url"], headers=H, timeout=30).json()
    return requests.get(out["images"][0]["url"], timeout=60).content


def grad_text(c, x, y, t, f, top, bot, ol=5):
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 6, y + 6), t, font=f, fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    c.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(c)
    for dx in range(-ol, ol + 1, 2):
        for dy in range(-ol, ol + 1, 2):
            d.text((x + dx, y + dy), t, font=f, fill="black")
    bbox = d.textbbox((0, 0), t, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tl = Image.new("RGBA", (tw + 30, th + 30), (0, 0, 0, 0))
    ImageDraw.Draw(tl).text((10, 5), t, font=f, fill="white")
    g = Image.new("RGBA", tl.size, (0, 0, 0, 0))
    for gy in range(tl.height):
        ratio = gy / tl.height
        rgb = tuple(int(top[i] * (1 - ratio) + bot[i] * ratio) for i in range(3))
        ImageDraw.Draw(g).line([(0, gy), (tl.width, gy)], fill=rgb + (255,))
    g.putalpha(tl.split()[3])
    c.paste(g, (x - 10, y - 5), g)


def sh_text(c, x, y, t, f, fill, ol=5):
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 6, y + 6), t, font=f, fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    c.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(c)
    for dx in range(-ol, ol + 1, 2):
        for dy in range(-ol, ol + 1, 2):
            d.text((x + dx, y + dy), t, font=f, fill="black")
    d.text((x, y), t, font=f, fill=fill)


def fit(b, tw, th, focus="r"):
    img = Image.open(BytesIO(b)).convert("RGB")
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    new = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    nw, nh = new.size
    left = 0 if focus == "l" else (nw - tw) if focus == "r" else (nw - tw) // 2
    return new.crop((left, (nh - th) // 2, left + tw, (nh - th) // 2 + th))


def badge(c):
    d = ImageDraw.Draw(c)
    d.rectangle([1040, 20, 1260, 90], fill=(0, 0, 0))
    d.rectangle([1040, 20, 1260, 90], outline=(255, 235, 30), width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = d.textbbox((0, 0), "건강정보", font=f)
    d.text((1150 - (bbox[2] - bbox[0]) // 2, 30), "건강정보", font=f, fill=(255, 235, 30))


def overlay_text(canvas, layout="left"):
    """layout: 'left' (Lian style 좌측) or 'center' (가운데)."""
    fm = ImageFont.truetype(FONT, 92)
    x = 40 if layout == "left" else 200
    grad_text(canvas, x, 50, "60대 무릎 통증", fm, (255, 245, 100), (255, 200, 30))
    grad_text(canvas, x, 180, "100% 없애는", fm, (255, 100, 60), (220, 30, 30))
    sh_text(canvas, x, 320, "단 1가지 음식 vs", fm, (255, 255, 255))
    grad_text(canvas, x, 460, "최악의 습관 공개", fm, (255, 100, 60), (220, 30, 30))
    badge(canvas)


def make(name, prompt, layout="left", paste_x=700, fade_w=180):
    print(f"[{name}]...", flush=True)
    img = fal(prompt)
    c = Image.new("RGB", (1280, 720), (10, 10, 10))
    c.paste(fit(img, 1280 - paste_x, 720, "r"), (paste_x, 0))
    d = ImageDraw.Draw(c, "RGBA")
    for i in range(fade_w):
        d.line([(paste_x + i, 0), (paste_x + i, 720)], fill=(10, 10, 10, 255 - int(255 * i / fade_w)))
    overlay_text(c, layout)
    c.save(DEST / f"{name}.jpg", quality=94)
    print(f"  {(DEST / (name+'.jpg')).stat().st_size / 1024:.0f}KB")


CANDIDATES = [
    ("01_warm_smile_doctor", "Photorealistic 16:9. Korean man in his 60s with kind warm smile, white doctor coat, salt-and-pepper hair. Light gray studio bg. Body on right 45%. Sharp focus, professional Korean YouTuber portrait. No text."),
    ("02_pointing_concerned", "Photorealistic 16:9. Korean man in his 60s, serious concerned expression, white doctor coat, pointing finger at viewer. Soft beige bg. Body on right 45%. Cinematic light. No text."),
    ("03_holding_turmeric", "Photorealistic 16:9. Korean man in his 60s, kind smile, white doctor coat, holding small bowl of golden turmeric powder in right hand. Warm sunset lighting kitchen bg. Body on right 50%. Food photography style. No text."),
    ("04_knee_model", "Photorealistic 16:9. Korean man in his 60s, gentle expression, white doctor coat, holding anatomical knee joint model in both hands at chest level. Clean white medical office bg. Body on right 45%. No text."),
    ("05_shocked_clickbait", "Photorealistic 16:9. Korean man in his 60s, dramatically surprised wide-eyed expression, hand raised to face. White doctor coat. Subtle red ambient lighting. Light gray bg. Body on right 45%. Bold dramatic, no text."),
    ("06_sunset_warm", "Photorealistic 16:9. Korean man in his 60s, calm reassuring smile, white doctor coat. Warm golden hour sunset bg with soft bokeh, like home consultation. Body on right 45%. Cinematic warm tones. No text."),
    ("07_arms_crossed_pro", "Photorealistic 16:9. Korean man in his 60s, confident slight smile, arms crossed, white doctor coat with stethoscope around neck. Modern clinic bg blurred. Body on right 45%. Authority pose. No text."),
    ("08_food_kitchen", "Photorealistic 16:9. Korean man in his 60s, friendly smile, casual sweater, in warm Korean kitchen with simmering pot of healthy mixed grain rice and sliced ginger on counter. Natural soft window light. Body on right 45%. Lifestyle. No text."),
]

for name, prompt in CANDIDATES:
    try:
        make(name, prompt)
    except Exception as e:
        print(f"  FAIL: {str(e)[:200]}")

print(f"\n[done] {DEST}")
for f in sorted(DEST.iterdir()):
    print(f"  {f.name} {f.stat().st_size / 1024:.0f}KB")
