"""bulk Gemini 썸네일 — 16 designs, no fal. fal 잔고 소진 우회."""
import os, base64, requests, time
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

load_dotenv(".env")
GK = os.environ["GEMINI_API_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_BULK_GEMINI"
DEST.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"


def gemini_img(prompt, retries=2):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GK}"
    for i in range(retries + 1):
        try:
            r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}}, timeout=120)
            r.raise_for_status()
            for part in r.json().get("candidates", [{}])[0].get("content", {}).get("parts", []):
                inline = part.get("inlineData") or part.get("inline_data")
                if inline:
                    return base64.b64decode(inline["data"])
            if i < retries:
                time.sleep(3)
                continue
            raise RuntimeError("no image in response")
        except Exception as e:
            if i < retries:
                time.sleep(3)
                continue
            raise


def outline(d, x, y, t, f, fill, w=6):
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
            d.text((x + dx, y + dy), t, font=f, fill="black")
    d.text((x, y), t, font=f, fill=fill)


def shadow_outline(c, x, y, t, f, fill, ol=5):
    sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 6, y + 6), t, font=f, fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    c.paste(sh, (0, 0), sh)
    d = ImageDraw.Draw(c)
    for dx in range(-ol, ol + 1, 2):
        for dy in range(-ol, ol + 1, 2):
            d.text((x + dx, y + dy), t, font=f, fill="black")
    d.text((x, y), t, font=f, fill=fill)


def fit(b, tw, th, focus="c"):
    img = Image.open(BytesIO(b)).convert("RGB")
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    new = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    nw, nh = new.size
    left = 0 if focus == "l" else (nw - tw) if focus == "r" else (nw - tw) // 2
    return new.crop((left, (nh - th) // 2, left + tw, (nh - th) // 2 + th))


def badge(d, right=True):
    bx = 1040 if right else 20
    d.rectangle([bx, 20, bx + 220, 90], fill=(0, 0, 0))
    d.rectangle([bx, 20, bx + 220, 90], outline=(255, 235, 30), width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = d.textbbox((0, 0), "건강정보", font=f)
    d.text((bx + 110 - (bbox[2] - bbox[0]) // 2, 30), "건강정보", font=f, fill=(255, 235, 30))


def fade_panel(c, x_start, w, color=(0,0,0)):
    d = ImageDraw.Draw(c, "RGBA")
    for i in range(w):
        d.line([(x_start + i, 0), (x_start + i, 720)], fill=color + (255 - int(255 * i / w),))


# ============================== 16 DESIGNS ==============================

def d01_doctor_pointing():
    """검정 좌패널 + 우인물(가리키는 의사)."""
    p = gemini_img("Photorealistic Korean man in his 60s, white doctor coat, salt-pepper hair, serious caring expression, raising right hand index finger pointing forward in warning gesture. Plain light gray studio background, half body, sharp focus, professional. No text.")
    c = Image.new("RGB", (1280, 720), (10, 10, 10))
    c.paste(fit(p, 580, 720, "r"), (700, 0))
    fade_panel(c, 700, 180)
    d = ImageDraw.Draw(c)
    fm = ImageFont.truetype(FONT, 86)
    outline(d, 40, 60, "60대 무릎 통증", fm, (255, 235, 30))
    outline(d, 40, 180, "100% 없애는", fm, (255, 50, 30))
    outline(d, 40, 320, "단 1가지 음식 vs", fm, (255, 255, 255))
    outline(d, 40, 460, "최악의 습관 공개", fm, (255, 50, 30))
    badge(d)
    c.save(DEST / "01_doctor_pointing.jpg", quality=92)


def d02_warm_smile_centered():
    p = gemini_img("Photorealistic Korean man in his 60s, warm gentle reassuring smile, white doctor coat, salt-pepper hair. Soft warm beige studio background, head and shoulders centered. Sharp focus. No text.")
    c = fit(p, 1280, 720, "c")
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, 1280, 130], fill=(0, 0, 0, 210))
    d.rectangle([0, 590, 1280, 720], fill=(220, 30, 30, 230))
    d2 = ImageDraw.Draw(c)
    outline(d2, 30, 30, "60대 무릎 100% 없애는", ImageFont.truetype(FONT, 64), (255, 235, 30))
    outline(d2, 30, 615, "단 1가지 음식, 최악의 습관", ImageFont.truetype(FONT, 70), (255, 255, 255))
    badge(d2)
    c.save(DEST / "02_warm_smile_overlay.jpg", quality=92)


def d03_food_close_warm():
    p = gemini_img("Photorealistic ultra close-up Korean traditional health food: golden turmeric powder, sliced fresh ginger root, walnuts, mixed grain rice steaming bowl, on rustic wooden table, warm sunset lighting, shallow depth of field, food photography masterpiece.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 540, 1280, 720], fill=(0, 0, 0, 230))
    d2 = ImageDraw.Draw(c)
    fb = ImageFont.truetype(FONT, 76)
    outline(d2, 30, 560, "60대 무릎이 살아나는", fb, (255, 235, 30))
    outline(d2, 30, 640, "단 1가지 음식 공개", fb, (255, 50, 30))
    badge(d2)
    c.save(DEST / "03_food_macro_overlay.jpg", quality=92)


def d04_shocked_clickbait():
    p = gemini_img("Photorealistic Korean man in his 60s, dramatically surprised wide-eyed expression mouth open in shock, both hands raised near face. White doctor coat. Bright clinical lighting, plain light gray background. Half body, sharp focus, viral clickbait energy. No text.")
    c = Image.new("RGB", (1280, 720), (255, 245, 230))
    c.paste(fit(p, 600, 720, "c"), (680, 0))
    fade_panel(c, 680, 180, (255, 245, 230))
    d = ImageDraw.Draw(c)
    fm = ImageFont.truetype(FONT, 92)
    outline(d, 40, 60, "충격", ImageFont.truetype(FONT, 140), (255, 50, 30), 8)
    outline(d, 40, 240, "60대 무릎이", fm, (40, 40, 40))
    outline(d, 40, 360, "이 1가지로", fm, (255, 50, 30))
    outline(d, 40, 480, "100% 사라진다", fm, (40, 40, 40))
    badge(d)
    c.save(DEST / "04_shocked_clickbait.jpg", quality=92)


def d05_knee_anatomy():
    p = gemini_img("Photorealistic medical anatomical knee joint cross-section 3D render, transparent skin showing bones cartilage and tendons, glowing red inflammation in cartilage. Clean blue-gray medical background, photorealistic medical illustration. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, 1280, 200], fill=(0, 0, 0, 220))
    d.rectangle([0, 540, 1280, 720], fill=(220, 30, 30, 230))
    d2 = ImageDraw.Draw(c)
    outline(d2, 30, 30, "60대 무릎 통증의 진짜 원인", ImageFont.truetype(FONT, 56), (255, 235, 30))
    outline(d2, 30, 100, "병원에서 안 알려주는 이유", ImageFont.truetype(FONT, 56), (255, 255, 255))
    outline(d2, 30, 565, "단 1가지 음식이 살립니다", ImageFont.truetype(FONT, 76), (255, 255, 255))
    badge(d2)
    c.save(DEST / "05_anatomy_warning.jpg", quality=92)


def d06_pill_vs_food():
    p = gemini_img("Photorealistic split scene: left side scattered colorful prescription pills on dark surface with red ambient lighting (warning); right side fresh golden turmeric and ginger and walnuts on bright wooden surface with warm sunlight (healthy). Dramatic contrast composition. Cinematic.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([580, 0, 700, 720], fill=(0, 0, 0, 200))
    d2 = ImageDraw.Draw(c)
    outline(d2, 595, 290, "VS", ImageFont.truetype(FONT, 110), (255, 235, 30), 8)
    d.rectangle([0, 0, 1280, 110], fill=(0, 0, 0, 230))
    outline(d2, 30, 25, "약 vs 음식 — 무엇이 진짜?", ImageFont.truetype(FONT, 60), (255, 235, 30))
    fb = ImageFont.truetype(FONT, 56)
    outline(d2, 50, 610, "약 평생 복용", fb, (255, 70, 70))
    outline(d2, 850, 610, "1가지로 끝", fb, (130, 255, 130))
    badge(d2)
    c.save(DEST / "06_pill_vs_food.jpg", quality=92)


def d07_woman_doctor():
    p = gemini_img("Photorealistic Korean woman in her 40s, kind professional warm smile, white doctor coat, shoulder-length dark hair, holding stethoscope. Soft beige warm studio background. Centered head and shoulders, trustworthy female doctor portrait. No text.")
    c = Image.new("RGB", (1280, 720), (250, 240, 220))
    c.paste(fit(p, 580, 720, "l"), (0, 0))
    fade_panel(c, 410, 180, (250, 240, 220))
    d = ImageDraw.Draw(c)
    fm = ImageFont.truetype(FONT, 86)
    outline(d, 620, 60, "여의사가", fm, (40, 40, 40))
    outline(d, 620, 180, "직접 알려드립니다", fm, (220, 30, 30))
    outline(d, 620, 340, "60대 무릎", fm, (40, 40, 40))
    outline(d, 620, 460, "100% 회복법", fm, (220, 30, 30))
    badge(d)
    c.save(DEST / "07_woman_doctor.jpg", quality=92)


def d08_holding_apple():
    p = gemini_img("Photorealistic Korean man in his 60s, kind smile, white doctor coat, holding fresh red apple in right hand near chest level, salt-pepper hair. Pure plain white background, half body visible, sharp focus, healthy living vibe. No text.")
    c = Image.new("RGB", (1280, 720), (255, 250, 240))
    c.paste(fit(p, 600, 720, "r"), (680, 0))
    fade_panel(c, 680, 150, (255, 250, 240))
    d = ImageDraw.Draw(c)
    fm = ImageFont.truetype(FONT, 88)
    outline(d, 40, 50, "하루 1개로", fm, (40, 40, 40))
    outline(d, 40, 170, "60대 무릎", fm, (40, 40, 40))
    outline(d, 40, 290, "통증 사라짐", fm, (220, 30, 30))
    outline(d, 40, 460, "+ 절대 먹지마", ImageFont.truetype(FONT, 70), (255, 50, 30))
    badge(d)
    c.save(DEST / "08_apple_lifestyle.jpg", quality=92)


def d09_giant_arrow():
    p = gemini_img("Photorealistic Korean man in his 60s, looking down concerned at his own knee, sitting on chair, wearing comfortable home clothes, holding hand on knee, soft natural window light, home setting living room. Half body, sharp focus, sympathetic. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, 1280, 720], fill=(0, 0, 0, 80))
    d2 = ImageDraw.Draw(c)
    outline(d2, 50, 60, "↓", ImageFont.truetype(FONT, 220), (255, 235, 30), 8)
    fm = ImageFont.truetype(FONT, 80)
    outline(d2, 280, 80, "이 자세 위험!", fm, (255, 235, 30))
    outline(d2, 280, 200, "당신 무릎 죽어요", fm, (255, 50, 30))
    outline(d2, 50, 480, "60대 100% 회복 단 1가지", fm, (255, 255, 255))
    badge(d2)
    c.save(DEST / "09_warning_posture.jpg", quality=92)


def d10_exercise_demo():
    p = gemini_img("Photorealistic Korean man in his 60s, athletic relaxed pose, demonstrating gentle leg stretch on yoga mat in bright living room, wearing comfortable training clothes, calm focused expression, natural window light. Sharp focus. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 540, 1280, 720], fill=(40, 100, 50, 230))
    d2 = ImageDraw.Draw(c)
    outline(d2, 30, 565, "하루 5분 이 동작이면", ImageFont.truetype(FONT, 60), (255, 255, 255))
    outline(d2, 30, 640, "60대 무릎 평생 안 아픕니다", ImageFont.truetype(FONT, 60), (255, 235, 30))
    badge(d2)
    c.save(DEST / "10_exercise_demo.jpg", quality=92)


def d11_before_after():
    p = gemini_img("Photorealistic split before-after composition: left side same Korean man 60s grimacing in pain holding knee in dim cool blue light, right side same person smiling and walking confidently in bright warm golden light. Cinematic dramatic transformation. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([580, 0, 700, 720], fill=(0, 0, 0, 220))
    d2 = ImageDraw.Draw(c)
    outline(d2, 595, 280, "→", ImageFont.truetype(FONT, 130), (255, 235, 30), 8)
    d.rectangle([0, 0, 580, 90], fill=(0, 0, 0, 210))
    d.rectangle([700, 0, 1280, 90], fill=(0, 80, 30, 210))
    outline(d2, 50, 18, "Before — 통증 지옥", ImageFont.truetype(FONT, 50), (255, 70, 70))
    outline(d2, 750, 18, "After — 2주만에", ImageFont.truetype(FONT, 50), (130, 255, 130))
    d.rectangle([0, 620, 1280, 720], fill=(220, 30, 30, 230))
    outline(d2, 30, 640, "단 1가지 음식 + 1가지 습관", ImageFont.truetype(FONT, 64), (255, 255, 255))
    badge(d2)
    c.save(DEST / "11_before_after.jpg", quality=92)


def d12_doctor_chart():
    p = gemini_img("Photorealistic Korean man in his 60s, white doctor coat, professional smile, holding clipboard with medical chart pointing at it. Modern clinic background blurred, soft cool clinical lighting. Half body, sharp focus, authority. No text.")
    c = Image.new("RGB", (1280, 720), (235, 240, 245))
    c.paste(fit(p, 580, 720, "r"), (700, 0))
    fade_panel(c, 700, 180, (235, 240, 245))
    d = ImageDraw.Draw(c)
    fm = ImageFont.truetype(FONT, 80)
    outline(d, 40, 60, "전문의 직접 발표", ImageFont.truetype(FONT, 56), (60, 60, 60))
    outline(d, 40, 150, "60대 80%가", fm, (40, 40, 40))
    outline(d, 40, 270, "잘못 먹는 음식", fm, (220, 30, 30))
    outline(d, 40, 430, "지금 끊어야할", fm, (40, 40, 40))
    outline(d, 40, 520, "단 1가지 습관", fm, (220, 30, 30))
    badge(d)
    c.save(DEST / "12_doctor_chart.jpg", quality=92)


def d13_patient_grateful():
    p = gemini_img("Photorealistic Korean elderly woman in her 70s, very grateful warm smile, holding hands, dressed in comfortable home clothes, soft afternoon window light. Half body, sharp focus, emotional moment, testimonial style. No text.")
    c = fit(p, 1280, 720, "l")
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, 1280, 130], fill=(0, 0, 0, 220))
    d.rectangle([700, 130, 1280, 720], fill=(255, 245, 220, 240))
    d2 = ImageDraw.Draw(c)
    outline(d2, 30, 30, "70대 어머니 후기", ImageFont.truetype(FONT, 56), (255, 235, 30))
    fm = ImageFont.truetype(FONT, 64)
    outline(d2, 720, 170, "\"2주만에", fm, (40, 40, 40))
    outline(d2, 720, 270, "무릎 통증이", fm, (40, 40, 40))
    outline(d2, 720, 370, "사라졌어요\"", fm, (220, 30, 30))
    outline(d2, 720, 520, "단 1가지 음식", ImageFont.truetype(FONT, 56), (60, 60, 60))
    outline(d2, 720, 595, "+ 1가지 습관", ImageFont.truetype(FONT, 56), (60, 60, 60))
    badge(d2)
    c.save(DEST / "13_patient_testimonial.jpg", quality=92)


def d14_red_alert_banner():
    p = gemini_img("Photorealistic Korean man in his 60s, very serious authoritative expression, white doctor coat with stethoscope, looking directly forward at camera. Plain dark charcoal gray studio background, head and shoulders, sharp focus, dramatic. No text.")
    c = Image.new("RGB", (1280, 720), (10, 10, 10))
    c.paste(fit(p, 700, 720, "c"), (290, 0))
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, 1280, 110], fill=(220, 20, 20, 240))
    d.rectangle([0, 540, 1280, 720], fill=(0, 0, 0, 230))
    d2 = ImageDraw.Draw(c)
    outline(d2, 30, 25, "긴급 — 60대 필독", ImageFont.truetype(FONT, 56), (255, 255, 255))
    fm = ImageFont.truetype(FONT, 70)
    outline(d2, 30, 560, "당신 무릎이 죽어가는 이유", fm, (255, 235, 30))
    outline(d2, 30, 640, "1가지 음식만 끊어도 살아남", fm, (255, 50, 30))
    badge(d)
    c.save(DEST / "14_red_alert.jpg", quality=92)


def d15_timer_countdown():
    p = gemini_img("Photorealistic Korean man in his 60s, urgent serious expression, white doctor coat, holding wrist watch up showing time. Dark dramatic studio background. Half body, sharp focus, urgency, time pressure. No text.")
    c = Image.new("RGB", (1280, 720), (20, 20, 30))
    c.paste(fit(p, 580, 720, "r"), (700, 0))
    fade_panel(c, 700, 180, (20, 20, 30))
    d = ImageDraw.Draw(c)
    outline(d, 40, 30, "2주", ImageFont.truetype(FONT, 220), (255, 235, 30), 10)
    fm = ImageFont.truetype(FONT, 64)
    outline(d, 40, 290, "안에 무릎 통증", fm, (255, 255, 255))
    outline(d, 40, 380, "사라지는 단", fm, (255, 255, 255))
    outline(d, 40, 470, "1가지 음식", fm, (255, 50, 30))
    outline(d, 40, 580, "지금 안 보면 후회", ImageFont.truetype(FONT, 50), (255, 235, 30))
    badge(d)
    c.save(DEST / "15_timer_2weeks.jpg", quality=92)


def d16_yellow_caution():
    p = gemini_img("Photorealistic Korean man in his 60s holding up his palm in stop gesture, white doctor coat, very serious concerned expression. Bright lighting, plain light yellow studio background. Half body, sharp focus, dramatic warning. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, 1280, 720], fill=(255, 220, 0, 100))
    d.rectangle([0, 590, 1280, 720], fill=(0, 0, 0, 240))
    d2 = ImageDraw.Draw(c)
    fw = ImageFont.truetype(FONT, 200)
    outline(d2, 50, 30, "⚠", fw, (220, 30, 30), 6)
    fm = ImageFont.truetype(FONT, 70)
    outline(d2, 280, 60, "지금 이 음식", fm, (40, 40, 40))
    outline(d2, 280, 160, "당장 끊으세요!", fm, (220, 30, 30))
    outline(d2, 30, 615, "60대 무릎 100% 살리는 단 1가지", ImageFont.truetype(FONT, 56), (255, 235, 30))
    badge(d2)
    c.save(DEST / "16_yellow_caution.jpg", quality=92)


# ============================== RUN ==============================
DESIGNS = [
    ("01", d01_doctor_pointing), ("02", d02_warm_smile_centered),
    ("03", d03_food_close_warm), ("04", d04_shocked_clickbait),
    ("05", d05_knee_anatomy), ("06", d06_pill_vs_food),
    ("07", d07_woman_doctor), ("08", d08_holding_apple),
    ("09", d09_giant_arrow), ("10", d10_exercise_demo),
    ("11", d11_before_after), ("12", d12_doctor_chart),
    ("13", d13_patient_grateful), ("14", d14_red_alert_banner),
    ("15", d15_timer_countdown), ("16", d16_yellow_caution),
]

ok, fail = 0, 0
for tag, fn in DESIGNS:
    print(f"[{tag}] {fn.__name__}...", flush=True)
    try:
        fn()
        ok += 1
        print(f"  OK", flush=True)
    except Exception as e:
        fail += 1
        print(f"  FAIL: {str(e)[:200]}", flush=True)

print(f"\n[done] {ok} OK / {fail} FAIL → {DEST}")
for f in sorted(DEST.iterdir()):
    print(f"  {f.name} {f.stat().st_size / 1024:.0f}KB")
