"""DALL-E 3 썸네일 8장 — clean prompts (이전 400 회피)."""
import os, requests, urllib.request
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

load_dotenv(".env")
OK = os.environ["OPENAI_API_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_DALLE"
DEST.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"


def dalle(prompt):
    r = requests.post("https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {OK}", "Content-Type": "application/json"},
        json={"model": "dall-e-3", "prompt": prompt, "size": "1792x1024",
              "quality": "standard", "n": 1}, timeout=120)
    r.raise_for_status()
    url = r.json()["data"][0]["url"]
    img_bytes = urllib.request.urlopen(url, timeout=60).read()
    return img_bytes


def outline(d, x, y, t, f, fill, w=6):
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
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


def fade_panel(c, x_start, w, color=(0,0,0)):
    d = ImageDraw.Draw(c, "RGBA")
    for i in range(w):
        d.line([(x_start + i, 0), (x_start + i, 720)], fill=color + (255 - int(255 * i / w),))


def badge(d):
    d.rectangle([1040, 20, 1260, 90], fill=(0, 0, 0))
    d.rectangle([1040, 20, 1260, 90], outline=(255, 235, 30), width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = d.textbbox((0, 0), "건강정보", font=f)
    d.text((1150 - (bbox[2] - bbox[0]) // 2, 30), "건강정보", font=f, fill=(255, 235, 30))


def standard_text(c):
    d = ImageDraw.Draw(c)
    fm = ImageFont.truetype(FONT, 86)
    outline(d, 40, 60, "60대 무릎 통증", fm, (255, 235, 30))
    outline(d, 40, 180, "100% 없애는", fm, (255, 50, 30))
    outline(d, 40, 320, "단 1가지 음식 vs", fm, (255, 255, 255))
    outline(d, 40, 460, "최악의 습관 공개", fm, (255, 50, 30))
    badge(d)


def standard_layout(name, prompt):
    img = dalle(prompt)
    c = Image.new("RGB", (1280, 720), (10, 10, 10))
    c.paste(fit(img, 580, 720, "r"), (700, 0))
    fade_panel(c, 700, 180)
    standard_text(c)
    c.save(DEST / f"{name}.jpg", quality=92)


CANDIDATES = [
    ("D1_korean_doctor_warm",
     "A photorealistic professional portrait of an elderly Korean male doctor, 60 years old, wearing a clean white medical coat, warm friendly smile, salt and pepper hair. Soft studio lighting, plain light gray background. Sharp focus."),
    ("D2_korean_doctor_serious",
     "A photorealistic portrait of an elderly Korean male doctor, 60 years old, white medical coat with stethoscope, serious concerned expression, salt and pepper hair. Clean studio background, professional lighting."),
    ("D3_korean_food_macro",
     "An ultra close-up macro photograph of a healthy Korean food bowl: golden turmeric powder, sliced fresh ginger, mixed grain rice, walnuts on a rustic wooden table. Warm natural sunlight, shallow depth of field, food photography style."),
    ("D4_korean_doctor_pointing",
     "A photorealistic portrait of an elderly Korean male doctor, 60 years old, white medical coat, raising his right hand index finger pointing forward in a teaching gesture, friendly authoritative expression, plain light background, professional studio."),
    ("D5_korean_woman_doctor",
     "A photorealistic professional portrait of a Korean female doctor in her 40s, white medical coat, kind warm professional smile, shoulder length dark hair. Soft beige background, professional studio lighting."),
    ("D6_korean_anatomy_illustration",
     "A clean medical illustration of a human knee joint anatomy in cross section, showing bones cartilage and tendons in detail, rendered in 3D photorealistic style. Light blue clinical background, no text labels."),
    ("D7_korean_elderly_smiling",
     "A photorealistic portrait of an elderly Korean man, 70 years old, very happy genuine smile, casual home clothes, sitting comfortably in a bright living room, natural window light, warm domestic atmosphere."),
    ("D8_korean_doctor_chart",
     "A photorealistic portrait of an elderly Korean male doctor, 60 years old, white medical coat, holding a clipboard with health chart, professional friendly smile. Modern clinic background slightly blurred, soft clinical lighting."),
]

ok, fail = 0, 0
for name, prompt in CANDIDATES:
    print(f"[{name}]...", flush=True)
    try:
        standard_layout(name, prompt)
        ok += 1
        print(f"  OK", flush=True)
    except Exception as e:
        fail += 1
        print(f"  FAIL: {str(e)[:200]}", flush=True)

print(f"\n[done] {ok} OK / {fail} FAIL → {DEST}")
for f in sorted(DEST.iterdir()):
    print(f"  {f.name} {f.stat().st_size / 1024:.0f}KB")
