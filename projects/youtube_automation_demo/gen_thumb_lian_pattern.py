"""Lian 패턴 정확 재현 — 직사각형 크롭 + 두꺼운 outline + sharp seam."""
import os, requests, time
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
load_dotenv(".env")
FK = os.environ["FAL_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_LEARNED"
DEST.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"
H = {"Authorization": f"Key {FK}", "Content-Type": "application/json"}
PANEL_W = 800
PERSON_W = 480
TEXT_X = 40


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


def heavy_text(c, x, y, t, font, fill, ol=12):
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 8, y + 8), t, font=font, fill=(0, 0, 0, 220))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    c.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(c)
    for dx in range(-ol, ol + 1, 2):
        for dy in range(-ol, ol + 1, 2):
            d.text((x + dx, y + dy), t, font=font, fill="black")
    d.text((x, y), t, font=font, fill=fill)


def crop_person(img_bytes, target_w, target_h):
    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    iw, ih = img.size
    s = target_h / ih
    new = img.resize((int(iw * s), target_h), Image.LANCZOS)
    nw = new.size[0]
    if nw > target_w:
        left = (nw - target_w) // 2
        new = new.crop((left, 0, left + target_w, target_h))
    return new


def badge(c):
    d = ImageDraw.Draw(c)
    d.rectangle([1040, 18, 1260, 88], fill=(0, 0, 0))
    d.rectangle([1040, 18, 1260, 88], outline=(255, 235, 30), width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = d.textbbox((0, 0), "건강정보", font=f)
    d.text((1150 - (bbox[2] - bbox[0]) // 2, 28), "건강정보", font=f, fill=(255, 235, 30))


def overlay_text(c):
    fm = ImageFont.truetype(FONT, 96)
    heavy_text(c, TEXT_X, 60, "60대 무릎 통증", fm, (255, 235, 30))
    heavy_text(c, TEXT_X, 200, "100% 없애는", fm, (255, 50, 30))
    heavy_text(c, TEXT_X, 340, "단 1가지 음식 vs", fm, (255, 255, 255))
    heavy_text(c, TEXT_X, 480, "최악의 습관 공개", fm, (255, 50, 30))


def make(name, prompt, color=(0, 0, 0)):
    print(f"[{name}]...", flush=True)
    img = fal(prompt)
    canvas = Image.new("RGB", (1280, 720), color)
    canvas.paste(crop_person(img, PERSON_W, 720), (PANEL_W, 0))
    overlay_text(canvas)
    badge(canvas)
    p = DEST / f"{name}.jpg"
    canvas.save(p, quality=94)
    print(f"  {p.name} {p.stat().st_size / 1024:.0f}KB")


CANDIDATES = [
    ("L1_serious_authority", "Photorealistic Korean man in his 60s, serious authoritative expression, slight head tilt, white doctor coat. Soft warm studio bg, beige tones. Centered head and shoulders portrait, professional senior YouTuber, no text."),
    ("L2_concerned_warning", "Photorealistic Korean man in his 60s, concerned worried expression, white doctor coat with stethoscope. Dim lighting, dark gray studio bg. Centered head and shoulders, dramatic, no text."),
    ("L3_lecture_mic", "Photorealistic Korean man in his 60s, talking mid-speech, casual blazer over shirt, holding microphone. Dark stage bg with dim spotlight. Centered upper body, senior lecture style, no text."),
    ("L4_smile_warm_medical", "Photorealistic Korean man in his 60s, gentle warm reassuring smile, white doctor coat. Light beige soft studio bg. Centered head and shoulders, warm professional, no text."),
    ("L5_shocked_surprised", "Photorealistic Korean man in his 60s, surprised wide-eyed mouth slightly open, white doctor coat. Neutral gray studio bg. Centered head and shoulders, dramatic, no text."),
    ("L6_pointing_intense", "Photorealistic Korean man in his 60s, intense focused expression, white doctor coat, raising index finger pointing slightly upward warning gesture. Dark gray studio bg. Centered upper body, no text."),
    ("L7_woman_doctor", "Photorealistic Korean woman in her 40s, kind professional smile, white doctor coat. Soft beige warm studio bg. Centered head and shoulders, trustworthy female doctor, no text."),
    ("L8_kindly_listening", "Photorealistic Korean man in his 60s, kindly listening attentive, gentle smile, white doctor coat. Warm tan studio bg. Centered head and shoulders, consultation style, no text."),
]

for name, prompt in CANDIDATES:
    try:
        make(name, prompt)
    except Exception as e:
        print(f"  FAIL: {str(e)[:200]}")

print(f"\n[done] {DEST}")
for f in sorted(DEST.iterdir()):
    print(f"  {f.name} {f.stat().st_size / 1024:.0f}KB")
