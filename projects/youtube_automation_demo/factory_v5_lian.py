"""factory_v5_lian — Lian 1계정 brand template 정확 재현.

Spec: raw/sources/youtube/lian_1account_brand_spec_2026-05-04.md

Strict:
- 검정 단색 BG (또는 빨강 단색)
- 인물 우측 누끼 + 좌측 검정 fade
- 텍스트 좌 65%, 3-4줄, 노랑/흰/빨강
- 검정 외곽선 4-6px
- 노랑 외곽 프레임 6px
- 우상단 작은 노랑 채널뱃지 "노년황금기"
- 상단 흰 작은 인용 (옵션)
- 큰 메달/화살표/큰 quote bubble = X
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

DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_FACTORY_V5_LIAN"
DEST.mkdir(exist_ok=True, parents=True)
WORK = ARC_ROOT / "tools" / "image" / "_out" / "factory_v5_assets"
WORK.mkdir(exist_ok=True, parents=True)
FONT = "C:/Windows/Fonts/malgunbd.ttf"
W, H = 1280, 720

YELLOW = (255, 235, 30)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN_NEON = (0, 255, 0)
DARK_RED = (220, 0, 0)


# ============================== Asset pool ==============================

PERSON_PROMPTS = {
    "doc_male_60": "Photorealistic portrait of a Korean male doctor in his 60s, wearing white medical coat with shirt and tie, salt-pepper hair, glasses, very serious authoritative direct gaze at camera, half body visible, plain solid black studio background. Real broadcast TV style, sharp focus, no text. Body in center of frame.",
    "doc_male_70": "Photorealistic portrait of a Korean male doctor in his 70s, wearing white medical coat, gray hair, slight gentle smile but serious eyes, looking directly at camera, half body visible, plain solid black studio background. Real broadcast TV style, sharp focus, no text. Body in center of frame.",
    "doc_female_50": "Photorealistic portrait of a Korean female doctor in her late 40s, wearing white medical coat, shoulder-length dark hair, glasses, serious professional gaze slightly off camera, half body visible, plain solid black studio background. Real broadcast TV style, sharp focus, no text. Body in center of frame.",
    "doc_male_50_mic": "Photorealistic portrait of a Korean male doctor in his 50s, casual blazer over shirt, gray hair, glasses, talking with broadcast microphone in front, serious lecture pose, half body visible, plain solid black studio background. Real broadcast TV style, sharp focus, no text.",
    "doc_male_60_chair": "Photorealistic portrait of a Korean male doctor in his late 60s, wearing white medical coat, gray hair, glasses, sitting on chair with hand on chin contemplating, half body visible, plain solid dark gray studio background. Real broadcast TV style, sharp focus, no text.",
}


def asset_path(slug):
    return WORK / f"person_{slug}.png"


def cutout_path(slug):
    return WORK / f"person_{slug}_cut.png"


def gen_or_cache_person(slug):
    p = asset_path(slug)
    if p.exists() and p.stat().st_size > 5000:
        return p
    print(f"  [person gen] {slug}", flush=True)
    nano_banana.generate(PERSON_PROMPTS[slug], out=str(p))
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

def fit_height(img, th):
    iw, ih = img.size
    s = th / ih
    return img.resize((int(iw * s), th), Image.LANCZOS)


def thick(d, x, y, t, f, fill, outline_w=5, outline_color=BLACK):
    for dx in range(-outline_w, outline_w + 1, 2):
        for dy in range(-outline_w, outline_w + 1, 2):
            d.text((x + dx, y + dy), t, font=f, fill=outline_color)
    d.text((x, y), t, font=f, fill=fill)


def measure(d, t, f):
    bb = d.textbbox((0, 0), t, font=f)
    return bb[2] - bb[0], bb[3] - bb[1]


def paste_person_with_fade(canvas, cut_path, target_h=720, x_pos="r", w_max=560, fade_w=180, bg_color=BLACK):
    """Person 누끼를 우측에 paste + 좌측 fade (Lian style 자연스러운 검정 fade)."""
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
        cx = W - pw - 10
    else:
        cx = 10
    cy = max(0, H - target_h)
    canvas.paste(fitted, (cx, cy), fitted)

    # Left-edge fade gradient (검정 → 투명)
    if fade_w > 0 and x_pos == "r":
        d = ImageDraw.Draw(canvas, "RGBA")
        for i in range(fade_w):
            alpha = int(255 * (1 - i / fade_w))
            d.line([(cx + i, 0), (cx + i, H)], fill=bg_color + (alpha,))


def channel_badge(canvas, x=W - 200, y=20, label="노년황금기", color=YELLOW):
    """우상단 작은 노랑 채널뱃지."""
    d = ImageDraw.Draw(canvas)
    d.rectangle([x, y, x + 180, y + 70], fill=color, outline=BLACK, width=2)
    f = ImageFont.truetype(FONT, 28)
    bb = d.textbbox((0, 0), label, font=f)
    d.text((x + (180 - (bb[2] - bb[0])) // 2, y + 16), label, font=f, fill=BLACK)


def top_quote(canvas, text='"99%는 몰라서 후회합니다"', y=20):
    """상단 작은 흰 인용."""
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, 32)
    bb = d.textbbox((0, 0), text, font=f)
    x = W - (bb[2] - bb[0]) - 220  # 우상단 채널뱃지 왼쪽
    thick(d, x, y, text, f, WHITE, outline_w=3)


def yellow_outer_frame(canvas, width=7):
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W - 1, H - 1], outline=YELLOW, width=width)


def text_block(canvas, lines, x=40, y_start=60, line_h=125, font_size=92, outline_w=5):
    """좌측 멀티 라인 텍스트 (lines = [(text, color), ...])."""
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, font_size)
    for i, (text, color) in enumerate(lines):
        thick(d, x, y_start + i * line_h, text, f, color, outline_w=outline_w)


# ============================== 8 Designs ==============================

def D01_dangerous_vegetable():
    """채소 위험 — 빨간 BG, 여 의사."""
    print("\n=== D01 dangerous_vegetable (빨강 BG) ===")
    cut = cutout_or_cache("doc_female_50")
    canvas = Image.new("RGB", (W, H), DARK_RED)
    paste_person_with_fade(canvas, cut, target_h=720, x_pos="r", w_max=540, fade_w=160, bg_color=DARK_RED)
    text_block(canvas, [
        ("가장 위험한 채소!", YELLOW),
        ("절대 드시지 마세요!", YELLOW),
        ("이채소가 뼈를", WHITE),
        ("파괴합니다.", WHITE),
    ], x=40, y_start=60, line_h=140, font_size=86)
    channel_badge(canvas, label="노년황금기")
    yellow_outer_frame(canvas)
    canvas.save(DEST / "01_dangerous_vegetable.jpg", quality=92)
    print("  → 01_dangerous_vegetable.jpg")


def D02_heart_attack_warning():
    """심혈관 100% — 검정 BG, 남 의사."""
    print("\n=== D02 heart_attack_warning ===")
    cut = cutout_or_cache("doc_male_60")
    canvas = Image.new("RGB", (W, H), BLACK)
    paste_person_with_fade(canvas, cut, target_h=720, x_pos="r", w_max=540, fade_w=180, bg_color=BLACK)
    text_block(canvas, [
        ("이 증상 있다면 100%", YELLOW),
        ("심혈관 터지기 직전입니다!", YELLOW),
        ("심장마비 최후의 신호", WHITE),
    ], x=40, y_start=140, line_h=160, font_size=78)
    top_quote(canvas)
    channel_badge(canvas, label="노년황금기")
    yellow_outer_frame(canvas)
    canvas.save(DEST / "02_heart_attack_warning.jpg", quality=92)
    print("  → 02_heart_attack_warning.jpg")


def D03_dementia_5_habits():
    """치매 5가지 — 검정 BG, 남 의사 mic."""
    print("\n=== D03 dementia_5_habits ===")
    cut = cutout_or_cache("doc_male_50_mic")
    canvas = Image.new("RGB", (W, H), BLACK)
    paste_person_with_fade(canvas, cut, target_h=720, x_pos="r", w_max=520, fade_w=180, bg_color=BLACK)
    text_block(canvas, [
        ("치매 없는 인생,", GREEN_NEON),
        ("5가지 비밀 습관!", YELLOW),
        ("하루 5분이면 기억력 유지됩니다!", WHITE),
        ("(60대 이상 필독!!!!)", GREEN_NEON),
    ], x=40, y_start=70, line_h=130, font_size=64)
    top_quote(canvas)
    channel_badge(canvas, label="노년황금기")
    yellow_outer_frame(canvas)
    canvas.save(DEST / "03_dementia_5_habits.jpg", quality=92)
    print("  → 03_dementia_5_habits.jpg")


def D04_pancreatic_cancer():
    """췌장암 가족 — 검정 BG, 남 의사 chair."""
    print("\n=== D04 pancreatic_cancer ===")
    cut = cutout_or_cache("doc_male_60_chair")
    canvas = Image.new("RGB", (W, H), BLACK)
    paste_person_with_fade(canvas, cut, target_h=720, x_pos="r", w_max=540, fade_w=180, bg_color=BLACK)
    text_block(canvas, [
        ("가족이 췌장암", YELLOW),
        ("걸리고 의사가 바로", WHITE),
        ("버린 가장 위험한 과일1가지", RED),
    ], x=40, y_start=140, line_h=160, font_size=72)
    top_quote(canvas)
    channel_badge(canvas, label="노년황금기")
    yellow_outer_frame(canvas)
    canvas.save(DEST / "04_pancreatic_cancer.jpg", quality=92)
    print("  → 04_pancreatic_cancer.jpg")


def D05_supplements_warning():
    """영양제 5가지 — 검정 BG, 여 의사."""
    print("\n=== D05 supplements_warning ===")
    cut = cutout_or_cache("doc_female_50")
    canvas = Image.new("RGB", (W, H), BLACK)
    paste_person_with_fade(canvas, cut, target_h=720, x_pos="r", w_max=540, fade_w=180, bg_color=BLACK)
    text_block(canvas, [
        ("60대이상 필독!!!!", YELLOW),
        ("죽음을 부르는 영양제 5가지!!", YELLOW),
        ("제발 먹지 마세요", RED),
        ("진짜 큰일 납니다", RED),
    ], x=40, y_start=60, line_h=140, font_size=70)
    top_quote(canvas)
    channel_badge(canvas, label="노년황금기")
    yellow_outer_frame(canvas)
    canvas.save(DEST / "05_supplements_warning.jpg", quality=92)
    print("  → 05_supplements_warning.jpg")


def D06_dangerous_tests():
    """위험한 검사 5가지 — 검정 BG, 남 의사 chair."""
    print("\n=== D06 dangerous_tests ===")
    cut = cutout_or_cache("doc_male_70")
    canvas = Image.new("RGB", (W, H), BLACK)
    paste_person_with_fade(canvas, cut, target_h=720, x_pos="r", w_max=540, fade_w=180, bg_color=BLACK)
    text_block(canvas, [
        ("멀쩡한 사람", YELLOW),
        ("환자 만드는", RED),
        ("최악의 검사 5가지", WHITE),
        ("(병원에 속지 마세요)", YELLOW),
    ], x=40, y_start=80, line_h=140, font_size=84)
    top_quote(canvas)
    channel_badge(canvas, label="노년황금기")
    yellow_outer_frame(canvas)
    canvas.save(DEST / "06_dangerous_tests.jpg", quality=92)
    print("  → 06_dangerous_tests.jpg")


def D07_knee_5min_habit():
    """무릎 5분 자기전 — 검정 BG, 남 의사 60."""
    print("\n=== D07 knee_5min_habit ===")
    cut = cutout_or_cache("doc_male_60")
    canvas = Image.new("RGB", (W, H), BLACK)
    paste_person_with_fade(canvas, cut, target_h=720, x_pos="r", w_max=540, fade_w=180, bg_color=BLACK)
    text_block(canvas, [
        ("자기전 단 5분!", YELLOW),
        ("60대 무릎통증", WHITE),
        ("100% 사라집니다", RED),
        ("(병원도 모르는 비법)", YELLOW),
    ], x=40, y_start=70, line_h=140, font_size=78)
    top_quote(canvas)
    channel_badge(canvas, label="노년황금기")
    yellow_outer_frame(canvas)
    canvas.save(DEST / "07_knee_5min_habit.jpg", quality=92)
    print("  → 07_knee_5min_habit.jpg")


def D08_knee_food_secret():
    """무릎 음식 1가지 — 빨강 BG, 남 의사 70 (Lian 5번 톤)."""
    print("\n=== D08 knee_food_secret (빨강 BG) ===")
    cut = cutout_or_cache("doc_male_70")
    canvas = Image.new("RGB", (W, H), DARK_RED)
    paste_person_with_fade(canvas, cut, target_h=720, x_pos="r", w_max=540, fade_w=160, bg_color=DARK_RED)
    text_block(canvas, [
        ("무릎통증 없애려면", WHITE),
        ("이 음식 1가지만", YELLOW),
        ("드세요", WHITE),
        ("(동의보감 비법)", YELLOW),
    ], x=40, y_start=80, line_h=150, font_size=84)
    channel_badge(canvas, label="노년황금기")
    yellow_outer_frame(canvas)
    canvas.save(DEST / "08_knee_food_secret.jpg", quality=92)
    print("  → 08_knee_food_secret.jpg")


# ============================== Run ==============================

DESIGNS = [
    ("01", D01_dangerous_vegetable),
    ("02", D02_heart_attack_warning),
    ("03", D03_dementia_5_habits),
    ("04", D04_pancreatic_cancer),
    ("05", D05_supplements_warning),
    ("06", D06_dangerous_tests),
    ("07", D07_knee_5min_habit),
    ("08", D08_knee_food_secret),
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
