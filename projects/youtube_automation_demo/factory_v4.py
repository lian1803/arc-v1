"""factory_v4 — Asset 풀 cache → 변형 합성 (MARCELO 패턴 + 60-corpus 인사이트).

차이 vs v3:
- Asset 풀 1회 생성 → 합성마다 재사용 (비용 ½)
- 3-track tone: doctor / trainer / patient (60-corpus의 개인후기 톤 추가)
- 외곽 프레임 컬러 mix (초록/노랑/빨강)
- GIANT 텍스트 mode = outline 5px (단색 명도)
- multi-color 텍스트 (yellow/cyan/red/white/green) 단어별 split
"""
from __future__ import annotations
import math, os, sys
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

ARC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARC_ROOT))
load_dotenv(ARC_ROOT / ".env")

from tools.image import nano_banana
from rembg import remove

DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_FACTORY_V4"
DEST.mkdir(exist_ok=True, parents=True)
WORK = ARC_ROOT / "tools" / "image" / "_out" / "factory_v4_assets"
WORK.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"
W, H = 1280, 720

YELLOW = (255, 235, 30)
CYAN = (30, 217, 240)
RED = (255, 30, 30)
WHITE = (255, 255, 255)
GREEN = (130, 255, 130)
DARK_BLUE = (30, 80, 180)
ORANGE = (255, 140, 30)


# ============================== Asset Pool ==============================

BG_ASSETS = {
    "anatomy_red": "Photorealistic medical illustration of a human knee joint anatomy with surrounding hand and skin, entire image overlaid with strong red color tint, dramatic intense red lighting, knee bones cartilage and tendons visible, blurred edges, no text labels.",
    "food_turmeric": "Photorealistic ultra macro close-up of a wooden bowl of golden turmeric powder mixed with sliced fresh ginger root and walnuts, on a rustic dark wooden table, warm sunset light from upper left, very shallow depth of field, food photography masterpiece.",
    "exercise_mat": "Photorealistic clean bright living room with a yoga mat on hardwood floor, large windows with natural soft white light, minimalist beige walls, no people, wide open space empty room ready for exercise.",
    "junk_food_red": "Photorealistic dramatic close-up of unhealthy junk food: instant noodles, white bread, sugary donuts, soda cans on dark moody table, harsh red ambient lighting overlay, harsh shadows, ominous warning mood, cinematic.",
    "mri_scan": "Photorealistic medical knee MRI scan side view, sepia and orange tones, showing knee joint cross section anatomy, dramatic medical imaging fills frame, blurred edges, no text labels.",
    "drink_glass": "Photorealistic close-up of a hand holding a clear glass of warm golden tea or healthy traditional drink, hand visible from forearm, soft warm beige gradient background, natural soft window light, glass fills upper right of frame.",
    "knee_grab": "Photorealistic close-up of an elderly Korean person hand gripping their own painful knee, wrinkled hand pressing on knee joint, casual loungewear pants visible, soft warm window light, dramatic shadow on knee, hand and knee fill frame.",
    "white_bg_mat": "Photorealistic clean plain white wall background room with light hardwood floor, completely empty, soft natural daylight, minimalist studio space, no people, no objects, just empty bright clean room.",
}

PERSON_ASSETS = {
    "doctor_male_50": "Photorealistic Korean male doctor in his 50s, white medical coat, slight serious smile, salt-pepper hair, looking directly at camera, plain solid white studio background. Real broadcast TV portrait style. Half body torso visible. Sharp focus.",
    "doctor_female_40": "Photorealistic Korean female doctor in her 40s, white medical coat with stethoscope, gentle warm professional smile, shoulder-length dark hair, plain solid white studio background. Real broadcast TV portrait. Half body. Sharp focus.",
    "hanui_male_50": "Photorealistic Korean male traditional medicine doctor in his 50s, dark traditional Korean hanbok-style medical coat, kind authoritative smile, slight gray hair, plain solid white studio background. Real broadcast TV portrait. Half body. Sharp focus.",
    "trainer_male_30": "Photorealistic Korean male fitness trainer in his early 30s, athletic blue polo shirt and shorts, friendly confident smile giving thumbs up with both hands, fit muscular build, plain solid white studio background. Real broadcast TV portrait. Half body. Sharp focus.",
    "patient_female_60": "Photorealistic ordinary Korean grandmother in her late 60s, casual home clothes light cardigan, very happy genuine smile, holding hands together gratefully, gray hair short style, plain solid white studio background. Authentic home photo style not staged. Half body. Sharp focus.",
    "patient_lying": "Photorealistic ordinary Korean person in their 50s lying on yoga mat doing leg raise exercise, side angle view showing knee bend clearly, comfortable training clothes black shorts blue shirt, plain solid white background bright clean room. Authentic exercise photo. Full body. Sharp focus on body posture.",
}

ASSETS_FILE = WORK / "_assets_index.txt"


def asset_path(slug, kind="bg"):
    return WORK / f"{kind}_{slug}.png"


def cutout_path(slug):
    return WORK / f"person_{slug}_cut.png"


def gen_or_cache_bg(slug):
    p = asset_path(slug, "bg")
    if p.exists() and p.stat().st_size > 5000:
        return p
    print(f"  [bg gen] {slug}", flush=True)
    nano_banana.generate(BG_ASSETS[slug], out=str(p))
    return p


def gen_or_cache_person(slug):
    p = asset_path(slug, "person")
    if p.exists() and p.stat().st_size > 5000:
        return p
    print(f"  [person gen] {slug}", flush=True)
    nano_banana.generate(PERSON_ASSETS[slug], out=str(p))
    return p


def cutout_or_cache(slug):
    cut = cutout_path(slug)
    if cut.exists() and cut.stat().st_size > 5000:
        return cut
    src = gen_or_cache_person(slug)
    print(f"  [cutout] {slug}", flush=True)
    cut.write_bytes(remove(src.read_bytes()))
    return cut


# ============================== Composition utilities ==============================

def fit_cover(img, tw, th, focus="c"):
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    new = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    nw, nh = new.size
    left = 0 if focus == "l" else (nw - tw) if focus == "r" else (nw - tw) // 2
    return new.crop((left, (nh - th) // 2, left + tw, (nh - th) // 2 + th))


def fit_height(img, target_h):
    iw, ih = img.size
    s = target_h / ih
    return img.resize((int(iw * s), target_h), Image.LANCZOS)


def thick(d, x, y, t, f, fill, w=13):
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
            d.text((x + dx, y + dy), t, font=f, fill="black")
    d.text((x, y), t, font=f, fill=fill)


def measure(d, t, f):
    bb = d.textbbox((0, 0), t, font=f)
    return bb[2] - bb[0], bb[3] - bb[1]


def multi_color_line(d, x, y, segments, font, w=13):
    cx = x
    for text, color in segments:
        thick(d, cx, y, text, font, color, w)
        tw, _ = measure(d, text, font)
        cx += tw + 14


def paste_person(canvas, cut_path, target_h=620, x_pos="r", w_max=460):
    p = Image.open(cut_path).convert("RGBA")
    bbox = p.getbbox()
    if bbox: p = p.crop(bbox)
    fitted = fit_height(p, target_h)
    pw = fitted.size[0]
    if pw > w_max:
        left = (pw - w_max) // 2
        fitted = fitted.crop((left, 0, left + w_max, target_h))
        pw = w_max
    if x_pos == "r":
        cx = W - pw - 25
    elif x_pos == "l":
        cx = 25
    else:
        cx = (W - pw) // 2
    cy = H - target_h - 5
    canvas.paste(fitted, (cx, cy), fitted)


def curved_arrow(canvas, start, end, color=YELLOW, thickness=14):
    d = ImageDraw.Draw(canvas, "RGBA")
    sx, sy = start; ex, ey = end
    mx = (sx + ex) // 2
    my = min(sy, ey) - 80
    pts = []
    for i in range(40):
        t = i / 39
        bx = (1 - t) ** 2 * sx + 2 * (1 - t) * t * mx + t ** 2 * ex
        by = (1 - t) ** 2 * sy + 2 * (1 - t) * t * my + t ** 2 * ey
        pts.append((bx, by))
    for px, py in pts:
        d.ellipse([px - thickness/2 - 4, py - thickness/2 - 4, px + thickness/2 + 4, py + thickness/2 + 4], fill=(0, 0, 0, 255))
    for px, py in pts:
        d.ellipse([px - thickness/2, py - thickness/2, px + thickness/2, py + thickness/2], fill=color + (255,))
    px2, py2 = pts[-1]; px1, py1 = pts[-3]
    angle = math.atan2(py2 - py1, px2 - px1)
    head = 40
    d.polygon([(px2, py2),
               (px2 - head * math.cos(angle - 0.5), py2 - head * math.sin(angle - 0.5)),
               (px2 - head * math.cos(angle + 0.5), py2 - head * math.sin(angle + 0.5))],
              fill=color + (255,), outline=(0, 0, 0))


def view_medal(canvas, x, y, line1="200만", line2="조회수", color=YELLOW):
    d = ImageDraw.Draw(canvas, "RGBA")
    cx, cy = x + 80, y + 80
    pts = []
    for i in range(24):
        ang = -math.pi / 2 + i * math.pi / 12
        r = 95 if i % 2 == 0 else 80
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=color + (255,), outline=(0, 0, 0))
    d.polygon([(cx - 50, cy + 70), (cx - 40, cy + 130), (cx - 20, cy + 110), (cx, cy + 75)], fill=(220, 30, 30))
    d.polygon([(cx + 50, cy + 70), (cx + 40, cy + 130), (cx + 20, cy + 110), (cx, cy + 75)], fill=(220, 30, 30))
    f1 = ImageFont.truetype(FONT, 44)
    f2 = ImageFont.truetype(FONT, 30)
    bb1 = d.textbbox((0, 0), line1, font=f1)
    bb2 = d.textbbox((0, 0), line2, font=f2)
    d.text((cx - (bb1[2] - bb1[0]) // 2, cy - 35), line1, font=f1, fill="black")
    d.text((cx - (bb2[2] - bb2[0]) // 2, cy + 12), line2, font=f2, fill="black")


def quote(canvas, x, y, lines, color=WHITE, size=34):
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, size)
    for i, line in enumerate(lines):
        thick(d, x, y + i * (size + 12), line, f, color, w=5)


def outer_frame(canvas, color=YELLOW, width=12):
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W - 1, H - 1], outline=color, width=width)


def bottom_strip(canvas, fill=(0, 0, 0, 230), top_y=460):
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([0, top_y, W, H], fill=fill)


def top_strip(canvas, fill=(220, 30, 30), bot_y=110):
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, bot_y], fill=fill)


# ============================== Designs (10) ==============================

def D01_doctor_red_anatomy():
    """REF clone refined — 빨간 anatomy + 의사 + 거대 흰 텍스트."""
    print("\n=== D01 doctor_red_anatomy ===")
    bg = gen_or_cache_bg("anatomy_red")
    cut = cutout_or_cache("doctor_male_50")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    paste_person(canvas, cut, target_h=600, x_pos="r", w_max=440)
    curved_arrow(canvas, (380, 230), (540, 320), color=YELLOW)
    quote(canvas, 380, 130, ['"이곳을 누르면', '놀라운 변화가 생깁니다"'], color=WHITE, size=36)
    bottom_strip(canvas, top_y=400)
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 130)
    thick(d, 30, 420, "자기전 5분", f, WHITE, 13)
    thick(d, 30, 565, "20대 무릎 됩니다.", f, WHITE, 13)
    view_medal(canvas, 20, 20, "90만", "조회수")
    outer_frame(canvas, GREEN, 10)
    canvas.save(DEST / "01_doctor_red_anatomy.jpg", quality=92)
    print("  → 01_doctor_red_anatomy.jpg")


def D02_trainer_review_tone():
    """후기 톤 + 트레이너 thumbsup + 흰 배경."""
    print("\n=== D02 trainer_review_tone ===")
    bg = gen_or_cache_bg("white_bg_mat")
    cut = cutout_or_cache("trainer_male_30")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    paste_person(canvas, cut, target_h=620, x_pos="r", w_max=440)
    # multi-color 4-line review tone
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 84)
    thick(d, 40, 60, "누워서 따라했더니", f, (40, 40, 40), 12)
    multi_color_line(d, 40, 200, [("무릎 통증", (40, 40, 40)), ("사라지고", YELLOW)], f)
    thick(d, 40, 340, "걷기", f, (40, 40, 40), 12)
    f2 = ImageFont.truetype(FONT, 84)
    thick(d, 200, 340, "편해졌어요!", f2, RED, 12)
    f3 = ImageFont.truetype(FONT, 130)
    thick(d, 40, 480, "하루 5분", f3, DARK_BLUE, 13)
    view_medal(canvas, 20, 590, "300만", "조회수", color=YELLOW)
    outer_frame(canvas, YELLOW, 12)
    canvas.save(DEST / "02_trainer_review_tone.jpg", quality=92)
    print("  → 02_trainer_review_tone.jpg")


def D03_giant_minimal():
    """흰 벽 + 사람 누운 자세 + 거대 단색 검정 텍스트 (#001 패턴)."""
    print("\n=== D03 giant_minimal ===")
    bg = gen_or_cache_bg("white_bg_mat")
    cut = cutout_or_cache("patient_lying")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    p = Image.open(cut).convert("RGBA")
    bbox = p.getbbox()
    if bbox: p = p.crop(bbox)
    fitted = fit_height(p, 350)
    pw = fitted.size[0]
    cx = (W - pw) // 2
    canvas.paste(fitted, (cx, H - 360), fitted)
    d = ImageDraw.Draw(canvas)
    # GIANT 단색 검정 (outline 5px만)
    f_top = ImageFont.truetype(FONT, 70)
    thick(d, 50, 30, "누워서 하니까 무릎이 안아픈", f_top, (40, 40, 40), 5)
    f_main = ImageFont.truetype(FONT, 200)
    thick(d, 70, 110, "하체 근력", f_main, (10, 10, 10), 5)
    f_min = ImageFont.truetype(FONT, 80)
    thick(d, 870, 230, "(18분)", f_min, (10, 10, 10), 4)
    canvas.save(DEST / "03_giant_minimal.jpg", quality=92)
    print("  → 03_giant_minimal.jpg")


def D04_food_doctor_secret():
    """음식 매크로 + 여 의사 + 노랑 화살표."""
    print("\n=== D04 food_doctor_secret ===")
    bg = gen_or_cache_bg("food_turmeric")
    cut = cutout_or_cache("doctor_female_40")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    paste_person(canvas, cut, target_h=620, x_pos="r", w_max=420)
    curved_arrow(canvas, (420, 200), (280, 380), color=YELLOW)
    quote(canvas, 350, 80, ['"이거 매일 한 술이면', '무릎 평생 안 아픕니다"'], color=WHITE, size=34)
    bottom_strip(canvas, top_y=420)
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 100)
    thick(d, 30, 440, "60대 무릎 살리는", f, YELLOW, 13)
    thick(d, 30, 580, "단 1가지 음식!", f, WHITE, 13)
    view_medal(canvas, 20, 20, "60만", "구독자", color=YELLOW)
    outer_frame(canvas, GREEN, 10)
    canvas.save(DEST / "04_food_doctor_secret.jpg", quality=92)
    print("  → 04_food_doctor_secret.jpg")


def D05_patient_grateful_review():
    """환자 본인 후기 — 70대 할머니 + 4줄 multi-color."""
    print("\n=== D05 patient_grateful_review ===")
    bg = gen_or_cache_bg("white_bg_mat")
    cut = cutout_or_cache("patient_female_60")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    paste_person(canvas, cut, target_h=620, x_pos="r", w_max=420)
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 76)
    thick(d, 40, 50, "70대 김순자 할머니", f, (40, 40, 40), 10)
    f2 = ImageFont.truetype(FONT, 80)
    multi_color_line(d, 40, 180, [('"', (40, 40, 40)), ("2주만에", RED), ("무릎이", (40, 40, 40))], f2)
    thick(d, 40, 320, '사라졌어요!"', f2, DARK_BLUE, 12)
    f3 = ImageFont.truetype(FONT, 88)
    thick(d, 40, 480, "단 1가지 음식 + 1가지 습관", ImageFont.truetype(FONT, 56), (60, 60, 60), 8)
    thick(d, 40, 560, "지금 끊으세요", f3, RED, 13)
    view_medal(canvas, 20, 590, "150만", "조회수", color=YELLOW)
    outer_frame(canvas, YELLOW, 12)
    canvas.save(DEST / "05_patient_grateful_review.jpg", quality=92)
    print("  → 05_patient_grateful_review.jpg")


def D06_red_warning_food():
    """긴급 빨간 경고 + 정크푸드."""
    print("\n=== D06 red_warning_food ===")
    bg = gen_or_cache_bg("junk_food_red")
    cut = cutout_or_cache("doctor_male_50")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    paste_person(canvas, cut, target_h=620, x_pos="r", w_max=440)
    top_strip(canvas, fill=(220, 30, 30), bot_y=110)
    d = ImageDraw.Draw(canvas)
    f_top = ImageFont.truetype(FONT, 70)
    thick(d, 30, 25, "긴급 — 60대 필독", f_top, WHITE, 8)
    curved_arrow(canvas, (580, 220), (280, 360), color=RED)
    quote(canvas, 400, 130, ['"이거 드시면', '무릎이 죽습니다"'], color=WHITE, size=36)
    bottom_strip(canvas, top_y=460)
    d2 = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 100)
    thick(d2, 30, 480, "지금 끊어야 할", f, YELLOW, 13)
    thick(d2, 30, 600, "최악의 음식 3가지", f, WHITE, 13)
    view_medal(canvas, 20, 130, "120만", "조회수", color=YELLOW)
    outer_frame(canvas, RED, 12)
    canvas.save(DEST / "06_red_warning_food.jpg", quality=92)
    print("  → 06_red_warning_food.jpg")


def D07_exercise_chair_review():
    """의자 운동 후기 — 앉아서 + 멀티컬러 4줄."""
    print("\n=== D07 exercise_chair_review ===")
    bg = gen_or_cache_bg("exercise_mat")
    cut = cutout_or_cache("trainer_male_30")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    paste_person(canvas, cut, target_h=620, x_pos="r", w_max=440)
    # multi-color 4 lines (Lian style #012 reproduction)
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 76)
    thick(d, 40, 50, "의자에 앉아서", f, YELLOW, 11)
    thick(d, 40, 160, "매일 했더니", f, GREEN, 11)
    multi_color_line(d, 40, 280, [("무릎통증", RED), ("사라지고", (40, 40, 40))], f)
    thick(d, 40, 410, "걷기 편해졌어요!", f, CYAN, 11)
    f2 = ImageFont.truetype(FONT, 110)
    thick(d, 40, 540, "하루 5분만", f2, (10, 10, 10), 13)
    view_medal(canvas, 20, 590, "100만", "조회수", color=RED)
    outer_frame(canvas, YELLOW, 12)
    canvas.save(DEST / "07_exercise_chair_review.jpg", quality=92)
    print("  → 07_exercise_chair_review.jpg")


def D08_drink_hanui():
    """한방차 잔 + 한의사 + 곡선 화살표."""
    print("\n=== D08 drink_hanui ===")
    bg = gen_or_cache_bg("drink_glass")
    cut = cutout_or_cache("hanui_male_50")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    paste_person(canvas, cut, target_h=620, x_pos="l", w_max=420)
    curved_arrow(canvas, (480, 230), (820, 280), color=YELLOW)
    quote(canvas, 600, 110, ['"식사 후 한 잔씩,', '무릎통증 사라집니다"'], color=WHITE, size=32)
    bottom_strip(canvas, top_y=440)
    d = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT, 86)
    thick(d, 30, 460, "한의사 추천", f1, YELLOW, 12)
    f2 = ImageFont.truetype(FONT, 100)
    thick(d, 30, 580, "이 차 1잔으로 끝!", f2, WHITE, 13)
    view_medal(canvas, 20, 20, "75만", "조회수", color=YELLOW)
    outer_frame(canvas, RED, 10)
    canvas.save(DEST / "08_drink_hanui.jpg", quality=92)
    print("  → 08_drink_hanui.jpg")


def D09_knee_grab_giant():
    """무릎 잡은 손 close-up + 거대 텍스트 좌측."""
    print("\n=== D09 knee_grab_giant ===")
    bg = gen_or_cache_bg("knee_grab")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    # No person overlay — bg is already body close-up
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([0, 0, 620, 720], fill=(0, 0, 0, 220))
    d2 = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 100)
    thick(d2, 30, 50, "걷기 대신", f, CYAN, 13)
    thick(d2, 30, 200, "이 운동 1가지", f, YELLOW, 13)
    thick(d2, 30, 360, "무릎통증", f, WHITE, 13)
    thick(d2, 30, 510, "100% 사라진다!", f, RED, 13)
    view_medal(canvas, 20, 600, "250만", "조회수", color=YELLOW)
    outer_frame(canvas, GREEN, 10)
    canvas.save(DEST / "09_knee_grab_giant.jpg", quality=92)
    print("  → 09_knee_grab_giant.jpg")


def D10_mri_orthopedic():
    """MRI + 정형외과 + 거대 텍스트."""
    print("\n=== D10 mri_orthopedic ===")
    bg = gen_or_cache_bg("mri_scan")
    cut = cutout_or_cache("doctor_male_50")
    canvas = fit_cover(Image.open(bg).convert("RGB"), W, H).copy()
    paste_person(canvas, cut, target_h=620, x_pos="r", w_max=440)
    curved_arrow(canvas, (420, 280), (250, 380), color=RED)
    quote(canvas, 360, 130, ['"이 부위가 망가지면', '평생 못 걷습니다"'], color=WHITE, size=34)
    bottom_strip(canvas, top_y=470)
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 96)
    thick(d, 30, 490, "수술 안 하고", f, WHITE, 13)
    thick(d, 30, 610, "연골 재생하는 법", f, YELLOW, 13)
    view_medal(canvas, 20, 20, "180만", "조회수", color=YELLOW)
    outer_frame(canvas, GREEN, 10)
    canvas.save(DEST / "10_mri_orthopedic.jpg", quality=92)
    print("  → 10_mri_orthopedic.jpg")


# ============================== Run ==============================

DESIGNS = [
    ("01", D01_doctor_red_anatomy),
    ("02", D02_trainer_review_tone),
    ("03", D03_giant_minimal),
    ("04", D04_food_doctor_secret),
    ("05", D05_patient_grateful_review),
    ("06", D06_red_warning_food),
    ("07", D07_exercise_chair_review),
    ("08", D08_drink_hanui),
    ("09", D09_knee_grab_giant),
    ("10", D10_mri_orthopedic),
]


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    ok = fail = 0
    for tag, fn in DESIGNS:
        if only and only != tag:
            continue
        try:
            fn()
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  FAIL [{tag}]: {str(e)[:300]}")
    print(f"\n[done] {ok} OK / {fail} FAIL → {DEST}")
