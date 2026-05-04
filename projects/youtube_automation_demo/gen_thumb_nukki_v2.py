"""8 누끼 v2 — width hard cap 380 + 풀 검정 + 좌측 텍스트."""
import os, requests, time
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from rembg import remove
load_dotenv(".env")
FK = os.environ["FAL_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_NUKKI_v2"
DEST.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"
H = {"Authorization": f"Key {FK}", "Content-Type": "application/json"}


def fal(prompt):
    r = requests.post("https://queue.fal.run/fal-ai/recraft-v3", headers=H,
        json={"prompt": prompt, "image_size": "portrait_4_3", "style": "realistic_image"}, timeout=60)
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


def cutout(img_bytes, max_w, max_h):
    cut = remove(img_bytes)
    img = Image.open(BytesIO(cut)).convert("RGBA")
    bbox = img.getbbox()
    if bbox: img = img.crop(bbox)
    iw, ih = img.size
    s = min(max_w / iw, max_h / ih)
    return img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)


def badge(c):
    d = ImageDraw.Draw(c)
    d.rectangle([1040, 18, 1260, 88], fill=(0, 0, 0))
    d.rectangle([1040, 18, 1260, 88], outline=(255, 235, 30), width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = d.textbbox((0, 0), "건강정보", font=f)
    d.text((1150 - (bbox[2] - bbox[0]) // 2, 28), "건강정보", font=f, fill=(255, 235, 30))


def overlay_text(c):
    fm = ImageFont.truetype(FONT, 92)
    heavy_text(c, 40, 60, "60대 무릎 통증", fm, (255, 235, 30))
    heavy_text(c, 40, 200, "100% 없애는", fm, (255, 50, 30))
    heavy_text(c, 40, 340, "단 1가지 음식 vs", fm, (255, 255, 255))
    heavy_text(c, 40, 480, "최악의 습관 공개", fm, (255, 50, 30))


def make(name, prompt):
    print(f"[{name}]...", flush=True)
    img = fal(prompt)
    canvas = Image.new("RGB", (1280, 720), (0, 0, 0))
    person = cutout(img, 380, 700)
    pw, ph = person.size
    canvas.paste(person, (1280 - pw - 30, (720 - ph) // 2), person)
    overlay_text(canvas)
    badge(canvas)
    canvas.save(DEST / f"{name}.jpg", quality=94)
    print(f"  ok person={pw}x{ph}")


CANDIDATES = [
    ("V1_serious_authority", "Photorealistic head and shoulders portrait. Korean man in his 60s, serious authoritative expression looking forward, salt-pepper hair, white doctor coat. Pure plain white background, generous headroom above head, sharp focus, tight crop, no text."),
    ("V2_concerned_warning", "Photorealistic head and shoulders portrait. Korean man in his 60s, concerned worried expression, hand near temple, white doctor coat with stethoscope. Pure plain white background, generous headroom, dramatic, no text."),
    ("V3_warm_smile", "Photorealistic head and shoulders portrait. Korean man in his 60s, gentle warm reassuring smile, white doctor coat, salt-pepper hair. Pure plain white background, generous headroom above head, no text."),
    ("V4_shocked", "Photorealistic head and shoulders portrait. Korean man in his 60s, dramatic surprised wide-eyed expression mouth open, hands near face, white doctor coat. Pure plain white background, generous headroom, no text."),
    ("V5_pointing", "Photorealistic head and shoulders portrait. Korean man in his 60s, serious focused expression, raising index finger up beside face warning gesture, white doctor coat. Pure plain white background, generous headroom, no text."),
    ("V6_woman", "Photorealistic head and shoulders portrait. Korean woman in her 40s, kind professional smile, white doctor coat, shoulder-length dark hair. Pure plain white background, generous headroom, trustworthy, no text."),
    ("V7_thumbsup", "Photorealistic head and shoulders portrait. Korean man in his 60s, warm encouraging smile, giving thumbs up gesture beside chest, white doctor coat. Pure plain white background, generous headroom, no text."),
    ("V8_apple", "Photorealistic head and shoulders portrait. Korean man in his 60s, kind smile, holding fresh red apple in right hand at chest level, white doctor coat. Pure plain white background, generous headroom, healthy living, no text."),
]

for name, prompt in CANDIDATES:
    try: make(name, prompt)
    except Exception as e: print(f"  FAIL: {str(e)[:200]}")

print(f"\n[done] {DEST}")
