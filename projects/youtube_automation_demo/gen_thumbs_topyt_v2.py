"""topyt_v2 — 실제 top performer 패턴 strict 적용.
변경:
- 메인 폰트 86 → 140-170px
- 외곽선 5 → 13px
- 단어별 컬러 분리 (yellow/cyan/red/white 한 thumbnail 안에 3-4색)
- AI 스튜디오 portrait → body part close-up + real broadcast feel
- 페이드 panel → hard color block
- 명사 나열 → 동사+느낌표
"""
import os, base64, requests, time
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv(".env")
GK = os.environ["GEMINI_API_KEY"]
DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_TOPYT_V2"
DEST.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"

YELLOW = (255, 235, 30)
CYAN = (30, 217, 240)
RED = (255, 30, 30)
WHITE = (255, 255, 255)
LIGHTBLUE = (130, 200, 255)
GREEN = (130, 255, 130)


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
            if i < retries: time.sleep(3); continue
            raise RuntimeError("no image in response")
        except Exception:
            if i < retries: time.sleep(3); continue
            raise


def fit(b, tw, th, focus="r"):
    img = Image.open(BytesIO(b)).convert("RGB")
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    new = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    nw, nh = new.size
    left = 0 if focus == "l" else (nw - tw) if focus == "r" else (nw - tw) // 2
    return new.crop((left, (nh - th) // 2, left + tw, (nh - th) // 2 + th))


def thick(d, x, y, t, f, fill, w=13):
    """13px 외곽선 + 흰 또는 컬러."""
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
            d.text((x + dx, y + dy), t, font=f, fill="black")
    d.text((x, y), t, font=f, fill=fill)


def measure(d, t, f):
    bbox = d.textbbox((0, 0), t, font=f)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def multi_color_line(d, x, y, segments, font, w=13):
    """한 줄에 여러 색. segments = [(text, color), ...]. 자동 좌→우 배치."""
    cx = x
    for text, color in segments:
        thick(d, cx, y, text, font, color, w)
        tw, _ = measure(d, text, font)
        cx += tw + 12  # 단어 간격


def badge_top_right(d, label="건강정보", color=YELLOW):
    d.rectangle([1040, 18, 1260, 88], fill=(0, 0, 0))
    d.rectangle([1040, 18, 1260, 88], outline=color, width=4)
    f = ImageFont.truetype(FONT, 38)
    bbox = d.textbbox((0, 0), label, font=f)
    d.text((1150 - (bbox[2] - bbox[0]) // 2, 28), label, font=f, fill=color)


def view_badge_top_left(d, view_text="90만 조회수"):
    """노랑 별 모양 view count 뱃지 (top performer #6 패턴)."""
    d.rectangle([20, 18, 200, 100], fill=YELLOW, outline="black", width=4)
    f = ImageFont.truetype(FONT, 32)
    parts = view_text.split(" ", 1) if " " in view_text else (view_text, "")
    if isinstance(parts, tuple):
        d.text((30, 28), parts[0], font=f, fill="black")
        d.text((30, 60), parts[1], font=f, fill="black")
    else:
        d.text((30, 35), parts[0], font=f, fill="black")
        if len(parts) > 1:
            d.text((30, 65), parts[1], font=f, fill="black")


# ============================== 12 DESIGNS ==============================

def t01():
    """4줄 멀티컬러 + 무릎잡은 손 우측 (top #2 패턴)."""
    p = gemini_img("Photorealistic close-up of an elderly Korean person's hand gripping their own painful knee, wrinkled hand pressing on knee joint, casual home clothes pants visible, soft warm window light, dramatic shadow on knee. Body on right side. Plain blurred background. Sharp focus on hand and knee. No text.")
    c = Image.new("RGB", (1280, 720), (0, 0, 0))
    c.paste(fit(p, 720, 720, "c"), (560, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, 580, 720], fill=(0, 0, 0))
    f1 = ImageFont.truetype(FONT, 78)
    f2 = ImageFont.truetype(FONT, 92)
    multi_color_line(d, 30, 50, [("걷기 대신", CYAN), ("이", WHITE)], f1)
    multi_color_line(d, 30, 160, [("무릎통증", YELLOW), ("없어지고", WHITE)], f1)
    multi_color_line(d, 30, 320, [("매일", WHITE), ("5분", RED), ("하면", WHITE)], f1)
    thick(d, 30, 480, "강철무릎 됩니다!", f2, WHITE)
    badge_top_right(d)
    c.save(DEST / "01_kneehand_4line_multi.jpg", quality=92)


def t02():
    """수술없이 / 단 1가지로 / 사라진다 — top #3 빨간 띠 패턴."""
    p = gemini_img("Photorealistic Korean male doctor in his 50s, white medical coat, slight serious smile, salt and pepper hair, plain green/blue solid color clinic background. Real broadcast TV style, not studio. Looking slightly off camera. Half body. Sharp focus. No text.")
    c = Image.new("RGB", (1280, 720), (40, 130, 90))
    c.paste(fit(p, 480, 720, "c"), (800, 0))
    d = ImageDraw.Draw(c)
    # red top banner
    d.rectangle([0, 0, 800, 130], fill=(220, 30, 30))
    f_top = ImageFont.truetype(FONT, 86)
    thick(d, 200, 25, "수술없이", f_top, WHITE, 8)
    # blue main box
    d.rectangle([0, 130, 800, 590], fill=(40, 80, 200))
    f_main = ImageFont.truetype(FONT, 90)
    thick(d, 60, 180, "무릎 연골이", f_main, WHITE, 10)
    thick(d, 60, 290, "재생되는", f_main, WHITE, 10)
    f_bottom = ImageFont.truetype(FONT, 100)
    thick(d, 80, 420, "단 하나의 방법", f_bottom, WHITE, 10)
    badge_top_right(d)
    c.save(DEST / "02_red_blue_block_surgery.jpg", quality=92)


def t03():
    """거대 텍스트 좌측 + 의사 우 (top #1 4M view 패턴 — 텍스트 60% 면적)."""
    p = gemini_img("Photorealistic Korean male doctor in his 50s, dark suit and tie, looking slightly off camera, plain blurred TV studio background light blue tones. Real broadcast TV portrait style. Half body. Sharp focus. No text.")
    c = Image.new("RGB", (1280, 720), (180, 200, 220))
    c.paste(fit(p, 600, 720, "l"), (0, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([580, 0, 1280, 720], fill=(180, 200, 220))
    f = ImageFont.truetype(FONT, 168)
    thick(d, 620, 50, "퇴행성", f, (90, 130, 230), 14)
    thick(d, 620, 240, "관절염", f, (90, 130, 230), 14)
    f2 = ImageFont.truetype(FONT, 168)
    thick(d, 620, 460, "치료법", f2, (90, 130, 230), 14)
    badge_top_right(d)
    c.save(DEST / "03_giant_text_doctor_left.jpg", quality=92)


def t04():
    """음료 잔 우 + 4줄 멀티컬러 좌 (top #7 596K view 패턴)."""
    p = gemini_img("Photorealistic close-up of a hand holding a clear glass of warm golden tea or healthy drink, soft gradient warm beige background, hand visible from elbow, natural soft window light from right. Hand on right side. No face visible. Sharp focus. No text.")
    c = Image.new("RGB", (1280, 720), (50, 50, 60))
    c.paste(fit(p, 700, 720, "r"), (580, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, 600, 720], fill=(50, 50, 60))
    f = ImageFont.truetype(FONT, 88)
    thick(d, 30, 40, "식사 후", f, YELLOW, 12)
    thick(d, 30, 175, "한 잔씩", f, GREEN, 12)
    thick(d, 30, 320, "매일 마시면", f, WHITE, 12)
    thick(d, 30, 480, "무릎통증", f, WHITE, 12)
    thick(d, 30, 600, "사라진다!", f, CYAN, 12)
    badge_top_right(d)
    c.save(DEST / "04_drink_4line_yellow_green.jpg", quality=92)


def t05():
    """MRI/X-ray 배경 + 큰 흰 텍스트 (top #8 384K 패턴)."""
    p = gemini_img("Photorealistic medical knee MRI scan side view image, sepia tone, showing knee joint cross section, with a small inset of a Korean doctor in white coat top left corner. Medical clinical style. Sharp medical imaging focus. No text labels.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 280, 1280, 720], fill=(0, 0, 0, 200))
    d2 = ImageDraw.Draw(c)
    f = ImageFont.truetype(FONT, 128)
    thick(d2, 40, 310, "반월상", f, WHITE, 13)
    thick(d2, 40, 470, "연골판 파열", f, YELLOW, 13)
    f2 = ImageFont.truetype(FONT, 56)
    thick(d2, 40, 630, "운동 계속하면 큰일", f2, RED, 7)
    badge_top_right(d2, "헬스조선", YELLOW)
    c.save(DEST / "05_mri_warning_block.jpg", quality=92)


def t06():
    """음식 close-up + 짧은 약속 (top #2 / #7 hybrid)."""
    p = gemini_img("Photorealistic ultra macro close-up of a small ceramic bowl of golden bright turmeric powder, mixed with sliced fresh ginger root, on a rustic wooden table, warm natural sunset light, very shallow depth of field, food photography masterpiece. Centered subject. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, 1280, 130], fill=(220, 30, 30))
    f_top = ImageFont.truetype(FONT, 78)
    thick(d, 30, 25, "의사가 절대 말 안 하는", f_top, WHITE, 8)
    d.rectangle([0, 540, 1280, 720], fill=(0, 0, 0))
    f_bot = ImageFont.truetype(FONT, 110)
    thick(d, 30, 565, "이 음식 1개로 끝!", f_bot, YELLOW, 12)
    badge_top_right(d)
    c.save(DEST / "06_turmeric_doctor_secret.jpg", quality=92)


def t07():
    """90만 조회수 뱃지 + 무릎 close-up (top #6 940K 패턴 정확 재현)."""
    p = gemini_img("Photorealistic close-up of an elderly Korean person's bare knees and lower legs while sitting comfortably, wearing soft loungewear shorts, both hands gently massaging the knee, warm home lighting, intimate sympathetic angle. Body filling frame. Sharp focus on knee. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 360, 1280, 720], fill=(0, 0, 0, 220))
    d2 = ImageDraw.Draw(c)
    view_badge_top_left(d2, "90만 조회수")
    f = ImageFont.truetype(FONT, 110)
    thick(d2, 30, 400, "자기전 5분", f, WHITE, 12)
    thick(d2, 30, 540, "20대 무릎 됩니다", f, WHITE, 12)
    badge_top_right(d2)
    c.save(DEST / "07_knee_massage_90M_views.jpg", quality=92)


def t08():
    """걷기 대신 / 이 운동 + 운동 자세 (top #2 변형, 강한 cyan/yellow/red 분리)."""
    p = gemini_img("Photorealistic Korean elderly person doing a gentle leg raise exercise on a yoga mat in a bright living room, side angle showing the knee bend movement clearly, comfortable training clothes, natural window light, focus on body posture. Half body. Sharp focus. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, 1280, 720], fill=(0, 0, 0, 90))
    d2 = ImageDraw.Draw(c)
    f = ImageFont.truetype(FONT, 92)
    multi_color_line(d2, 30, 60, [("걷기 대신", CYAN), ("이", WHITE)], f)
    f2 = ImageFont.truetype(FONT, 88)
    thick(d2, 30, 200, "이 운동 1가지", f2, YELLOW, 12)
    f3 = ImageFont.truetype(FONT, 88)
    thick(d2, 30, 350, "무릎통증", f3, WHITE, 12)
    thick(d2, 30, 480, "100% 사라진다!", f3, RED, 12)
    badge_top_right(d2)
    c.save(DEST / "08_exercise_walking_alternative.jpg", quality=92)


def t09():
    """4줄 / 의사 + 거대 폰트 (top #4 1.9M 패턴)."""
    p = gemini_img("Photorealistic Korean male doctor in his 50s wearing white medical coat, gentle confident smile, dark studio background, professional broadcast TV style portrait. Half body, sharp focus, real-feel not AI staged. No text.")
    c = Image.new("RGB", (1280, 720), (0, 0, 0))
    c.paste(fit(p, 580, 720, "r"), (700, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([700, 0, 720, 720], fill=(60, 130, 200), outline=None)
    f = ImageFont.truetype(FONT, 100)
    thick(d, 30, 40, "무릎연골주사", f, WHITE, 13)
    f2 = ImageFont.truetype(FONT, 92)
    thick(d, 30, 200, "에 대해", f2, WHITE, 12)
    thick(d, 30, 340, "꼭 알아야 할", f2, WHITE, 12)
    thick(d, 30, 500, "9가지", ImageFont.truetype(FONT, 130), YELLOW, 14)
    badge_top_right(d)
    c.save(DEST / "09_doctor_9things_must_know.jpg", quality=92)


def t10():
    """수술 vs 자연 — 분할 (대비 hard cut)."""
    p_l = gemini_img("Photorealistic close-up of surgical tools, scalpel and forceps on stainless tray, dim cool blue lighting, dramatic medical clinical photography, ominous mood. Sharp focus. No text.")
    p_r = gemini_img("Photorealistic close-up of fresh healthy Korean food: golden turmeric, sliced ginger, walnuts on a wooden bowl, warm sunset light, shallow depth, food photography. Sharp focus. No text.")
    c = Image.new("RGB", (1280, 720), (0, 0, 0))
    c.paste(fit(p_l, 600, 720, "c"), (0, 0))
    c.paste(fit(p_r, 600, 720, "c"), (680, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([590, 0, 690, 720], fill=(0, 0, 0))
    f_vs = ImageFont.truetype(FONT, 130)
    thick(d, 605, 280, "VS", f_vs, YELLOW, 12)
    d.rectangle([0, 0, 1280, 110], fill=(220, 30, 30))
    f_top = ImageFont.truetype(FONT, 70)
    thick(d, 30, 18, "60대 무릎 — 수술이냐 음식이냐?", f_top, WHITE, 8)
    d.rectangle([0, 600, 1280, 720], fill=(0, 0, 0))
    f_bot = ImageFont.truetype(FONT, 84)
    thick(d, 30, 620, "단 1가지로 무릎 살아납니다", f_bot, YELLOW, 10)
    badge_top_right(d)
    c.save(DEST / "10_surgery_vs_food_split.jpg", quality=92)


def t11():
    """이 음식 끊으세요 — 강한 경고 (junk food close-up)."""
    p = gemini_img("Photorealistic dramatic close-up of unhealthy junk food: instant noodles, white bread slices, sugary donuts, soda cans on a dark moody table, harsh red ambient lighting, harsh shadows, ominous mood. Centered. Sharp focus. No text.")
    c = fit(p, 1280, 720)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle([0, 0, 1280, 720], fill=(0, 0, 0, 110))
    d2 = ImageDraw.Draw(c)
    f = ImageFont.truetype(FONT, 128)
    thick(d2, 30, 50, "이 음식 끊으세요", f, YELLOW, 14)
    f2 = ImageFont.truetype(FONT, 110)
    thick(d2, 30, 240, "60대 무릎이", f2, WHITE, 13)
    thick(d2, 30, 380, "썩고 있습니다!", f2, RED, 13)
    f3 = ImageFont.truetype(FONT, 70)
    thick(d2, 30, 580, "지금 안 보면 평생 후회", f3, WHITE, 8)
    badge_top_right(d2)
    c.save(DEST / "11_junk_food_warning.jpg", quality=92)


def t12():
    """7일만에 / 큰 숫자 + 의사 (속도 약속 패턴)."""
    p = gemini_img("Photorealistic Korean male doctor in his 50s, white medical coat, smiling confidently, holding up a clipboard with chart, plain warm beige clinic background, soft natural lighting. Real broadcast TV portrait. Half body. Sharp focus. No text.")
    c = Image.new("RGB", (1280, 720), (240, 230, 210))
    c.paste(fit(p, 540, 720, "r"), (740, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([740, 0, 760, 720], fill=(220, 30, 30))
    f_big = ImageFont.truetype(FONT, 240)
    thick(d, 30, 30, "7일", f_big, RED, 14)
    f = ImageFont.truetype(FONT, 80)
    thick(d, 350, 80, "만에", f, (40, 40, 40), 10)
    thick(d, 350, 200, "연골 재생!", f, RED, 10)
    f2 = ImageFont.truetype(FONT, 76)
    thick(d, 30, 380, "60대 무릎통증", f2, (40, 40, 40), 10)
    thick(d, 30, 510, "단 1가지 음식만", f2, RED, 10)
    badge_top_right(d, "의학정보", RED)
    c.save(DEST / "12_7days_giant_number.jpg", quality=92)


# ============================== RUN ==============================
DESIGNS = [
    ("01", t01), ("02", t02), ("03", t03), ("04", t04),
    ("05", t05), ("06", t06), ("07", t07), ("08", t08),
    ("09", t09), ("10", t10), ("11", t11), ("12", t12),
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
