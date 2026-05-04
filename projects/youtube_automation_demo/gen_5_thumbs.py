"""5 패턴 썸네일 종결본 — Gemini base + Pillow overlay."""
import os, base64, requests
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
load_dotenv(".env")
GK = os.environ["GEMINI_API_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails"
DEST.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"


def gemini_img(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GK}"
    r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}}, timeout=120)
    r.raise_for_status()
    for part in r.json().get("candidates", [{}])[0].get("content", {}).get("parts", []):
        inline = part.get("inlineData") or part.get("inline_data")
        if inline:
            return base64.b64decode(inline["data"])


def outline(draw, x, y, text, font, fill, w=6):
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
            draw.text((x + dx, y + dy), text, font=font, fill="black")
    draw.text((x, y), text, font=font, fill=fill)


def fit(img_bytes, tw, th, focus="c"):
    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    new = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    nw, nh = new.size
    left = 0 if focus == "l" else (nw - tw) if focus == "r" else (nw - tw) // 2
    return new.crop((left, (nh - th) // 2, left + tw, (nh - th) // 2 + th))


def badge(draw):
    bx, by, bw, bh = 1040, 20, 220, 70
    draw.rectangle([bx, by, bx + bw, by + bh], fill=(0, 0, 0))
    draw.rectangle([bx, by, bx + bw, by + bh], outline=(255, 235, 30), width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = draw.textbbox((0, 0), "건강정보", font=f)
    draw.text((bx + (bw - (bbox[2] - bbox[0])) // 2, by + 10), "건강정보", font=f, fill=(255, 235, 30))


# A: 검정좌 + 우인물
print("[A]", flush=True)
person = gemini_img("Photorealistic portrait, Korean man in his 60s, friendly trustworthy looking left, white doctor coat, light gray studio background, sharp focus.")
c = Image.new("RGB", (1280, 720), (0, 0, 0))
c.paste(fit(person, 540, 720), (740, 0))
d = ImageDraw.Draw(c, "RGBA")
for i in range(120):
    d.line([(740 + i, 0), (740 + i, 720)], fill=(0, 0, 0, 255 - int(255 * i / 120)))
d = ImageDraw.Draw(c)
fm = ImageFont.truetype(FONT, 86)
for t, col, y in [("60대 무릎 통증", (255, 235, 30), 60), ("100% 없애는", (255, 50, 30), 180),
                  ("단 1가지 음식 vs", (255, 255, 255), 320), ("최악의 습관 공개", (255, 50, 30), 460)]:
    outline(d, 40, y, t, fm, col)
badge(d)
c.save(DEST / "A_검정좌패널_우인물.jpg", quality=92)

# B: VS split
print("[B]", flush=True)
L = gemini_img("Photorealistic close-up healthy Korean food: golden turmeric, fresh ginger, blueberries, walnuts, mixed grain rice bowl, bright bokeh, warm sunlight.")
R = gemini_img("Photorealistic dramatic junk foods: instant noodles, white bread, donuts, soda, dark moody table, red warning lighting, harsh shadows.")
c = Image.new("RGB", (1280, 720), (0, 0, 0))
c.paste(fit(L, 600, 720), (0, 0))
c.paste(fit(R, 600, 720), (680, 0))
d = ImageDraw.Draw(c, "RGBA")
d.rectangle([600, 0, 680, 720], fill=(0, 0, 0, 230))
d = ImageDraw.Draw(c)
outline(d, 605, 290, "VS", ImageFont.truetype(FONT, 110), (255, 235, 30), 8)
d.rectangle([0, 0, 1280, 100], fill=(0, 0, 0))
outline(d, 30, 18, "60대 무릎 100% 없애는 단 1가지!", ImageFont.truetype(FONT, 56), (255, 235, 30), 4)
fb = ImageFont.truetype(FONT, 60)
outline(d, 50, 600, "음식 추천", fb, (130, 255, 130), 5)
outline(d, 850, 600, "최악 습관", fb, (255, 70, 70), 5)
badge(d)
c.save(DEST / "B_VS_좌우split.jpg", quality=92)

# C: 거대 숫자
print("[C]", flush=True)
person = gemini_img("Photorealistic Korean man 60s, white doctor coat, holding red foam number 1 sign, surprised confident expression, pure white background, studio.")
c = Image.new("RGB", (1280, 720), (255, 245, 230))
c.paste(fit(person, 500, 720), (0, 0))
d = ImageDraw.Draw(c)
outline(d, 540, 100, "1", ImageFont.truetype(FONT, 480), (255, 50, 30), 12)
ft = ImageFont.truetype(FONT, 70); fs = ImageFont.truetype(FONT, 48)
outline(d, 770, 200, "가지만", ft, (50, 50, 50), 5)
outline(d, 770, 290, "끊으세요", ft, (255, 50, 30), 5)
outline(d, 770, 400, "60대 무릎 통증", fs, (50, 50, 50), 4)
outline(d, 770, 470, "100% 사라집니다", fs, (255, 50, 30), 4)
badge(d)
c.save(DEST / "C_거대숫자1.jpg", quality=92)

# D: 음식 클로즈업
print("[D]", flush=True)
food = gemini_img("Photorealistic ultra close-up golden turmeric powder, sliced ginger, steaming Korean mixed grain rice bowl, rustic wooden table, warm sunset, shallow depth, food photography.")
c = fit(food, 1280, 720)
d = ImageDraw.Draw(c, "RGBA")
d.rectangle([0, 0, 1280, 130], fill=(0, 0, 0, 200))
d.rectangle([0, 590, 1280, 720], fill=(220, 30, 30, 240))
d = ImageDraw.Draw(c)
outline(d, 30, 30, "60대 무릎 100% 없애는", ImageFont.truetype(FONT, 70), (255, 235, 30), 4)
outline(d, 30, 615, "단 1가지 음식 공개!", ImageFont.truetype(FONT, 78), (255, 255, 255), 5)
badge(d)
c.save(DEST / "D_음식클로즈업.jpg", quality=92)

# E: 경고
print("[E]", flush=True)
person = gemini_img("Photorealistic Korean man 60s friendly serious, white doctor coat, soft beige background, looking forward, professional consultation.")
c = Image.new("RGB", (1280, 720), (250, 240, 220))
c.paste(fit(person, 460, 720), (820, 0))
d = ImageDraw.Draw(c, "RGBA")
d.rectangle([820, 0, 940, 720], fill=(250, 240, 220, 230))
d = ImageDraw.Draw(c)
fw = ImageFont.truetype(FONT, 220)
outline(d, 50, 30, "⚠", fw, (255, 200, 0), 6)
fm = ImageFont.truetype(FONT, 78)
outline(d, 280, 60, "60대 무릎", fm, (40, 40, 40), 5)
outline(d, 280, 160, "통증의 진실", fm, (220, 30, 30), 5)
outline(d, 50, 320, "단 1가지 음식이", fm, (40, 40, 40), 5)
outline(d, 50, 420, "당신을 살립니다", fm, (220, 30, 30), 5)
d.rectangle([0, 620, 1280, 720], fill=(255, 220, 0))
outline(d, 50, 640, "끝까지 보세요 — 의사가 알려드립니다", ImageFont.truetype(FONT, 56), (40, 40, 40), 3)
badge(d)
c.save(DEST / "E_경고표지.jpg", quality=92)

print("[done] 5 thumbs:")
for f in sorted(DEST.iterdir()):
    print(f"  {f.name} {f.stat().st_size / 1024:.0f}KB")
