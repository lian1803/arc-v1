"""8 누끼 (background removal) thumbnails — 인물 cutout + 풀 검정 + Pillow Pro 텍스트."""
import os, requests, time
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from rembg import remove
load_dotenv(".env")
FK = os.environ["FAL_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_NUKKI"
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


def badge(c, right=True):
    d = ImageDraw.Draw(c)
    bx = 1040 if right else 20
    d.rectangle([bx, 20, bx + 220, 90], fill=(0, 0, 0))
    d.rectangle([bx, 20, bx + 220, 90], outline=(255, 235, 30), width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = d.textbbox((0, 0), "건강정보", font=f)
    d.text((bx + 110 - (bbox[2] - bbox[0]) // 2, 30), "건강정보", font=f, fill=(255, 235, 30))


def overlay_text(c, x_start=40):
    fm = ImageFont.truetype(FONT, 92)
    grad_text(c, x_start, 50, "60대 무릎 통증", fm, (255, 245, 100), (255, 200, 30))
    grad_text(c, x_start, 180, "100% 없애는", fm, (255, 100, 60), (220, 30, 30))
    sh_text(c, x_start, 320, "단 1가지 음식 vs", fm, (255, 255, 255))
    grad_text(c, x_start, 460, "최악의 습관 공개", fm, (255, 100, 60), (220, 30, 30))


def cutout_paste(canvas, person_bytes, target_h=720, x_pos="r"):
    """Remove bg, fit to target height, paste on canvas."""
    cutout = remove(person_bytes)
    img = Image.open(BytesIO(cutout)).convert("RGBA")
    iw, ih = img.size
    s = target_h / ih
    new = img.resize((int(iw * s), target_h), Image.LANCZOS)
    nw = new.size[0]
    if x_pos == "r":
        cx = canvas.width - nw - 40
    elif x_pos == "l":
        cx = 40
    else:
        cx = (canvas.width - nw) // 2
    canvas.paste(new, (cx, 0), new)


def make(name, prompt, layout="text-left-person-right"):
    print(f"[{name}] fetch...", flush=True)
    person = fal(prompt)
    print(f"  rembg + composite...", flush=True)
    canvas = Image.new("RGB", (1280, 720), (10, 10, 10))
    if layout == "text-left-person-right":
        cutout_paste(canvas, person, 720, "r")
        overlay_text(canvas, 40)
        badge(canvas, right=True)
    elif layout == "person-left-text-right":
        cutout_paste(canvas, person, 720, "l")
        overlay_text(canvas, 540)
        badge(canvas, right=True)
    elif layout == "text-full-person-small":
        cutout_paste(canvas, person, 540, "r")
        overlay_text(canvas, 40)
        badge(canvas, right=True)
    canvas.save(DEST / f"{name}.jpg", quality=94)
    print(f"  {(DEST / (name+'.jpg')).stat().st_size / 1024:.0f}KB")


CANDIDATES = [
    ("N1_warm_smile_white_bg", "Photorealistic Korean man in his 60s, warm friendly smile, white doctor coat with stethoscope, salt-pepper hair. Pure plain white background, full body torso visible, looking slightly to viewer's left, sharp focus, professional studio lighting. No text.", "text-left-person-right"),
    ("N2_pointing_finger_white", "Photorealistic Korean man in his 60s, serious caring expression, white doctor coat, raising right hand index finger pointing forward (warning gesture). Pure plain white background, half body visible, sharp focus. No text.", "text-left-person-right"),
    ("N3_holding_turmeric_white", "Photorealistic Korean man in his 60s, gentle smile, white doctor coat, holding small ceramic bowl of bright golden turmeric powder in hands at chest level. Pure plain white background, half body, sharp focus. No text.", "text-left-person-right"),
    ("N4_ok_gesture_white", "Photorealistic Korean man in his 60s, confident smile, white doctor coat, making OK hand gesture with right hand near chest. Pure plain white background, half body, sharp focus. No text.", "text-left-person-right"),
    ("N5_shocked_face_white", "Photorealistic Korean man in his 60s, dramatic surprised wide-eyed expression mouth open in shock, white doctor coat, hands near face. Pure plain white background, half body, sharp focus, viral clickbait energy. No text.", "text-left-person-right"),
    ("N6_arms_crossed_white", "Photorealistic Korean man in his 60s, confident slight smile, arms crossed across chest, white doctor coat with stethoscope around neck. Pure plain white background, full upper body, sharp focus, authority stance. No text.", "person-left-text-right"),
    ("N7_thumbs_up_white", "Photorealistic Korean man in his 60s, encouraging warm smile, white doctor coat, giving thumbs up gesture with right hand. Pure plain white background, half body, sharp focus. No text.", "text-left-person-right"),
    ("N8_holding_apple_white", "Photorealistic Korean man in his 60s, kind smile, white doctor coat, holding fresh red apple in right hand at chest level. Pure plain white background, half body, sharp focus, healthy living vibe. No text.", "text-full-person-small"),
]

for name, prompt, layout in CANDIDATES:
    try:
        make(name, prompt, layout)
    except Exception as e:
        print(f"  FAIL: {str(e)[:200]}")

print(f"\n[done]")
for f in sorted(DEST.iterdir()):
    print(f"  {f.name} {f.stat().st_size / 1024:.0f}KB")
