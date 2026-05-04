"""factory_thumb — 공장 체인 썸네일 빌더.
체인:
  1. nano_banana.generate(BG prompt) → red-tinted knee anatomy BG
  2. nano_banana.generate(person prompt) → real-feel Korean doctor portrait
  3. rembg.remove(person) → 누끼
  4. PIL: composite (bg + person right)
  5. PIL: yellow curved arrow + quote bubble (옵션)
  6. PIL: 거대 title (multi-color, 13px outline)
  7. PIL: top-left ribbon badge
  8. PIL: outer color border frame
"""
import os, sys, time
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import math

ARC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ARC_ROOT))
load_dotenv(ARC_ROOT / ".env")

from tools.image import nano_banana
from rembg import remove

DEST = Path.home() / "Desktop" / "youtube_v3_DELIVERY" / "thumbnails_FACTORY"
DEST.mkdir(exist_ok=True, parents=True)
WORK = ARC_ROOT / "tools" / "image" / "_out" / "factory_work"
WORK.mkdir(exist_ok=True, parents=True)

FONT = "C:/Windows/Fonts/malgunbd.ttf"
W, H = 1280, 720

YELLOW = (255, 235, 30)
CYAN = (30, 217, 240)
RED = (255, 30, 30)
WHITE = (255, 255, 255)
GREEN = (50, 200, 80)


# ---- Step utilities ---------------------------------------------------------

def gen_bg(prompt, slug):
    out = WORK / f"{slug}_bg.png"
    if out.exists():
        print(f"  [bg cached] {out.name}")
        return out
    print(f"  [bg gen] {prompt[:60]}...")
    saved = nano_banana.generate(prompt, out=str(out))
    return saved[0]


def gen_person(prompt, slug):
    out = WORK / f"{slug}_person_raw.png"
    if out.exists():
        print(f"  [person cached] {out.name}")
        return out
    print(f"  [person gen] {prompt[:60]}...")
    saved = nano_banana.generate(prompt, out=str(out))
    return saved[0]


def cutout(person_path, slug):
    out = WORK / f"{slug}_person_cut.png"
    if out.exists():
        print(f"  [cutout cached] {out.name}")
        return out
    print(f"  [cutout]...")
    src = Path(person_path).read_bytes()
    cut = remove(src)
    Path(out).write_bytes(cut)
    return out


def fit_height(img, target_h):
    iw, ih = img.size
    s = target_h / ih
    return img.resize((int(iw * s), target_h), Image.LANCZOS)


def fit_cover(img, tw, th, focus="c"):
    iw, ih = img.size
    s = max(tw / iw, th / ih)
    new = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    nw, nh = new.size
    left = 0 if focus == "l" else (nw - tw) if focus == "r" else (nw - tw) // 2
    return new.crop((left, (nh - th) // 2, left + tw, (nh - th) // 2 + th))


def thick(d, x, y, t, f, fill, w=13):
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
            d.text((x + dx, y + dy), t, font=f, fill="black")
    d.text((x, y), t, font=f, fill=fill)


def draw_curved_arrow(canvas, start, end, color=YELLOW, thickness=14):
    """Yellow curved arrow from start to end."""
    d = ImageDraw.Draw(canvas, "RGBA")
    sx, sy = start
    ex, ey = end
    # Bezier mid point above the line for curve
    mx = (sx + ex) // 2
    my = min(sy, ey) - 80
    # Approximate curve as line segments
    pts = []
    for i in range(40):
        t = i / 39
        # quadratic bezier
        bx = (1 - t) ** 2 * sx + 2 * (1 - t) * t * mx + t ** 2 * ex
        by = (1 - t) ** 2 * sy + 2 * (1 - t) * t * my + t ** 2 * ey
        pts.append((bx, by))
    # outline (black) then color
    for px, py in pts:
        d.ellipse([px - thickness / 2 - 4, py - thickness / 2 - 4,
                   px + thickness / 2 + 4, py + thickness / 2 + 4], fill=(0, 0, 0, 255))
    for px, py in pts:
        d.ellipse([px - thickness / 2, py - thickness / 2,
                   px + thickness / 2, py + thickness / 2], fill=color + (255,))
    # Arrow head triangle
    px2, py2 = pts[-1]
    px1, py1 = pts[-3]
    angle = math.atan2(py2 - py1, px2 - px1)
    head_size = 40
    a1 = (px2, py2)
    a2 = (px2 - head_size * math.cos(angle - 0.5),
          py2 - head_size * math.sin(angle - 0.5))
    a3 = (px2 - head_size * math.cos(angle + 0.5),
          py2 - head_size * math.sin(angle + 0.5))
    d.polygon([a1, a2, a3], fill=color + (255,), outline=(0, 0, 0))


def draw_ribbon_badge(canvas, x, y, line1="90만", line2="조회수"):
    """Top-left yellow ribbon star badge."""
    d = ImageDraw.Draw(canvas, "RGBA")
    # Star shape (12-point burst)
    cx, cy = x + 80, y + 80
    r1, r2 = 80, 95
    pts = []
    for i in range(24):
        angle = -math.pi / 2 + i * math.pi / 12
        r = r2 if i % 2 == 0 else r1
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    d.polygon(pts, fill=YELLOW + (255,), outline=(0, 0, 0))
    # Ribbon tails below
    d.polygon([(cx - 50, cy + 70), (cx - 40, cy + 130), (cx - 20, cy + 110), (cx, cy + 75)], fill=(220, 30, 30))
    d.polygon([(cx + 50, cy + 70), (cx + 40, cy + 130), (cx + 20, cy + 110), (cx, cy + 75)], fill=(220, 30, 30))
    # Text
    f1 = ImageFont.truetype(FONT, 44)
    f2 = ImageFont.truetype(FONT, 30)
    bb1 = d.textbbox((0, 0), line1, font=f1)
    bb2 = d.textbbox((0, 0), line2, font=f2)
    d.text((cx - (bb1[2] - bb1[0]) // 2, cy - 35), line1, font=f1, fill="black")
    d.text((cx - (bb2[2] - bb2[0]) // 2, cy + 12), line2, font=f2, fill="black")


def add_outer_border(canvas, color=GREEN, width=10):
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W - 1, H - 1], outline=color, width=width)


def draw_quote_bubble(canvas, x, y, lines, color=WHITE, size=36):
    """Italic-style quote text in white."""
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, size)
    for i, line in enumerate(lines):
        thick(d, x, y + i * (size + 12), line, f, color, w=5)


def composite_bg_person(bg_path, person_cut_path, person_h=720, person_x_pos="r", person_w_max=580):
    """Step 4: BG (full-bleed) + person cutout (right or left, fitted height)."""
    bg_img = Image.open(bg_path).convert("RGB")
    canvas = fit_cover(bg_img, W, H).copy()
    person_img = Image.open(person_cut_path).convert("RGBA")
    bbox = person_img.getbbox()
    if bbox: person_img = person_img.crop(bbox)
    fitted = fit_height(person_img, person_h)
    pw = fitted.size[0]
    if pw > person_w_max:
        # crop center to max width
        left = (pw - person_w_max) // 2
        fitted = fitted.crop((left, 0, left + person_w_max, person_h))
        pw = person_w_max
    if person_x_pos == "r":
        cx = W - pw - 20
    elif person_x_pos == "l":
        cx = 20
    else:
        cx = (W - pw) // 2
    canvas.paste(fitted, (cx, 0), fitted)
    return canvas


# ---- Variant builders --------------------------------------------------------

def build_v1_ref_clone():
    """REF 정확 클론: red-tinted knee anatomy bg + 의사 우 + curved arrow + quote + 거대 title + 리본 + 초록 프레임."""
    slug = "v1_ref_clone"
    print(f"\n=== {slug} ===")
    bg = gen_bg(
        "Photorealistic medical illustration of a human knee joint anatomy with surrounding hand and skin, entire image overlaid with a strong red color tint and red lighting effect, dramatic intense red atmosphere, knee bones cartilage and tendons visible, blurred edges. No text, no labels.",
        slug)
    person = gen_person(
        "Photorealistic Korean male doctor in his 40s, white medical coat, slight serious smile, salt-pepper hair, looking directly at camera, plain solid white studio background. Real broadcast TV portrait style. Half body torso visible. Sharp focus. No text.",
        slug)
    cut = cutout(person, slug)

    canvas = composite_bg_person(bg, cut, person_h=620, person_x_pos="r", person_w_max=460)

    # Curved arrow pointing to a knee spot (left-center area)
    draw_curved_arrow(canvas, start=(380, 230), end=(540, 320))

    # Quote bubble (italic-feel) above arrow target
    draw_quote_bubble(canvas, 380, 130,
                      ['"이곳을 누르면', '놀라운 변화가 생깁니다"'],
                      color=WHITE, size=36)

    # Bottom black strip + huge white title
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([0, 380, W, H], fill=(0, 0, 0, 220))
    d2 = ImageDraw.Draw(canvas)
    f_title = ImageFont.truetype(FONT, 130)
    thick(d2, 30, 410, "자기전 5분", f_title, WHITE, 13)
    thick(d2, 30, 555, "20대 무릎 됩니다.", f_title, WHITE, 13)

    # Top-left ribbon badge
    draw_ribbon_badge(canvas, 20, 20, "90만", "조회수")

    # Outer green border
    add_outer_border(canvas, color=GREEN, width=10)

    out = DEST / f"01_{slug}.jpg"
    canvas.save(out, quality=92)
    print(f"  → {out.name}")


def build_v2_food_arrow():
    """음식 close-up bg + 의사 누끼 + 화살표 + 거대 텍스트."""
    slug = "v2_food_arrow"
    print(f"\n=== {slug} ===")
    bg = gen_bg(
        "Photorealistic ultra macro close-up of a wooden bowl of golden turmeric powder mixed with sliced fresh ginger root and walnuts, on a rustic dark wooden table, warm sunset light from upper left, very shallow depth of field, food photography masterpiece, the food fills the entire frame.",
        slug)
    person = gen_person(
        "Photorealistic Korean female doctor in her 40s, white medical coat with stethoscope, gentle warm professional smile, shoulder-length dark hair, plain solid white studio background. Real broadcast TV portrait style. Half body. Sharp focus. No text.",
        slug)
    cut = cutout(person, slug)

    canvas = composite_bg_person(bg, cut, person_h=620, person_x_pos="r", person_w_max=460)

    # Yellow arrow pointing to food
    draw_curved_arrow(canvas, start=(420, 200), end=(280, 380), color=YELLOW)

    # Quote bubble
    draw_quote_bubble(canvas, 350, 80,
                      ['"이거 매일 한 술이면', '무릎 평생 안 아픕니다"'],
                      color=WHITE, size=34)

    # Bottom black strip + title
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([0, 420, W, H], fill=(0, 0, 0, 230))
    d2 = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT, 100)
    thick(d2, 30, 440, "60대 무릎 살리는", f1, YELLOW, 13)
    thick(d2, 30, 580, "단 1가지 음식!", f1, WHITE, 13)

    draw_ribbon_badge(canvas, 20, 20, "60만", "구독자")
    add_outer_border(canvas, color=GREEN, width=10)

    out = DEST / f"02_{slug}.jpg"
    canvas.save(out, quality=92)
    print(f"  → {out.name}")


def build_v3_drink_chain():
    """음료 잔 bg + 한의사 누끼 + 곡선 화살표."""
    slug = "v3_drink_chain"
    print(f"\n=== {slug} ===")
    bg = gen_bg(
        "Photorealistic close-up of a hand holding a clear glass of warm golden tea or healthy traditional drink, hand visible from forearm, soft warm beige gradient background, natural soft window light from right, professional product photography, glass fills upper right of frame.",
        slug)
    person = gen_person(
        "Photorealistic Korean male traditional medicine doctor in his 50s, dark traditional Korean hanbok-style medical coat, kind authoritative smile, slight gray hair, plain solid white studio background. Real broadcast TV portrait. Half body. Sharp focus. No text.",
        slug)
    cut = cutout(person, slug)

    canvas = composite_bg_person(bg, cut, person_h=620, person_x_pos="l", person_w_max=440)

    # Arrow from doctor to drink
    draw_curved_arrow(canvas, start=(480, 230), end=(800, 280), color=YELLOW)

    # Quote bubble near drink
    draw_quote_bubble(canvas, 600, 110,
                      ['"식사 후 한 잔씩,', '무릎통증 사라집니다"'],
                      color=WHITE, size=32)

    # Bottom black strip
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([0, 440, W, H], fill=(0, 0, 0, 230))
    d2 = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT, 86)
    thick(d2, 30, 460, "한의사 추천", f1, YELLOW, 12)
    f2 = ImageFont.truetype(FONT, 100)
    thick(d2, 30, 580, "이 차 1잔으로 끝!", f2, WHITE, 13)

    draw_ribbon_badge(canvas, 20, 20, "75만", "조회수")
    add_outer_border(canvas, color=(220, 30, 30), width=10)

    out = DEST / f"03_{slug}.jpg"
    canvas.save(out, quality=92)
    print(f"  → {out.name}")


def build_v4_red_warning():
    """빨간 위험 음식 bg + 의사 + 경고 화살표."""
    slug = "v4_red_warning"
    print(f"\n=== {slug} ===")
    bg = gen_bg(
        "Photorealistic dramatic close-up of unhealthy junk food: instant noodles, white bread, sugary donuts, soda cans on a dark moody table, with strong red ambient lighting overlay, harsh red shadows, ominous warning mood, cinematic. Food fills frame.",
        slug)
    person = gen_person(
        "Photorealistic Korean male doctor in his 50s, white medical coat with stethoscope, very serious concerned warning expression, raising right hand index finger up in stop gesture, salt-pepper hair, plain solid white studio background. Real broadcast TV portrait. Half body. Sharp focus. No text.",
        slug)
    cut = cutout(person, slug)

    canvas = composite_bg_person(bg, cut, person_h=620, person_x_pos="r", person_w_max=480)

    # Red warning arrow pointing at food
    draw_curved_arrow(canvas, start=(580, 220), end=(280, 360), color=RED)

    # Quote
    draw_quote_bubble(canvas, 400, 90,
                      ['"이거 드시면', '무릎이 죽습니다"'],
                      color=WHITE, size=36)

    # Bottom red strip + title
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, 110], fill=(220, 30, 30))
    f_top = ImageFont.truetype(FONT, 70)
    thick(d, 30, 25, "긴급 — 60대 필독", f_top, WHITE, 8)

    d2 = ImageDraw.Draw(canvas, "RGBA")
    d2.rectangle([0, 460, W, H], fill=(0, 0, 0, 230))
    d3 = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT, 100)
    thick(d3, 30, 480, "지금 끊어야 할", f1, YELLOW, 13)
    thick(d3, 30, 600, "최악의 음식 3가지", f1, WHITE, 13)

    draw_ribbon_badge(canvas, 20, 130, "120만", "조회수")
    add_outer_border(canvas, color=(220, 30, 30), width=12)

    out = DEST / f"04_{slug}.jpg"
    canvas.save(out, quality=92)
    print(f"  → {out.name}")


def build_v5_exercise_arrow():
    """운동 자세 bg + 의사 누끼 + 노랑 곡선 화살표."""
    slug = "v5_exercise_arrow"
    print(f"\n=== {slug} ===")
    bg = gen_bg(
        "Photorealistic close-up of an elderly Korean person bare knees and lower legs while sitting comfortably on a yoga mat, doing a gentle leg raise stretch, side angle showing knee bend movement clearly, comfortable training clothes, bright warm room with soft window light, focus on body posture and knee.",
        slug)
    person = gen_person(
        "Photorealistic Korean male physical therapist in his 40s, athletic blue polo shirt, friendly confident smile, fit build, plain solid white studio background. Real broadcast TV portrait. Half body. Sharp focus. No text.",
        slug)
    cut = cutout(person, slug)

    canvas = composite_bg_person(bg, cut, person_h=620, person_x_pos="r", person_w_max=460)

    # Yellow arrow pointing to knee
    draw_curved_arrow(canvas, start=(420, 250), end=(280, 420), color=YELLOW)

    draw_quote_bubble(canvas, 380, 110,
                      ['"하루 5분만,', '걷기 대신 이거 하세요"'],
                      color=WHITE, size=34)

    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([0, 460, W, H], fill=(0, 0, 0, 230))
    d2 = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT, 100)
    thick(d2, 30, 480, "걷기 대신 이 운동", f1, CYAN, 13)
    thick(d2, 30, 600, "강철무릎 됩니다!", f1, WHITE, 13)

    draw_ribbon_badge(canvas, 20, 20, "250만", "조회수")
    add_outer_border(canvas, color=GREEN, width=10)

    out = DEST / f"05_{slug}.jpg"
    canvas.save(out, quality=92)
    print(f"  → {out.name}")


def build_v6_mri_doctor():
    """MRI bg + 의사 + 거대 텍스트."""
    slug = "v6_mri_doctor"
    print(f"\n=== {slug} ===")
    bg = gen_bg(
        "Photorealistic medical knee MRI scan side view, sepia and orange tones, showing knee joint cross section anatomy, dramatic medical imaging, fills the frame, blurred edges. No text labels.",
        slug)
    person = gen_person(
        "Photorealistic Korean male orthopedic surgeon in his 50s, white medical coat with name badge, professional confident smile, glasses, salt-pepper hair, plain solid white studio background. Real broadcast TV portrait. Half body. Sharp focus. No text.",
        slug)
    cut = cutout(person, slug)

    canvas = composite_bg_person(bg, cut, person_h=620, person_x_pos="r", person_w_max=460)

    draw_curved_arrow(canvas, start=(420, 280), end=(250, 380), color=RED)

    draw_quote_bubble(canvas, 360, 130,
                      ['"이 부위가 망가지면', '평생 못 걷습니다"'],
                      color=WHITE, size=34)

    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle([0, 470, W, H], fill=(0, 0, 0, 230))
    d2 = ImageDraw.Draw(canvas)
    f1 = ImageFont.truetype(FONT, 96)
    thick(d2, 30, 490, "수술 안 하고", f1, WHITE, 13)
    thick(d2, 30, 610, "연골 재생하는 법", f1, YELLOW, 13)

    draw_ribbon_badge(canvas, 20, 20, "180만", "조회수")
    add_outer_border(canvas, color=GREEN, width=10)

    out = DEST / f"06_{slug}.jpg"
    canvas.save(out, quality=92)
    print(f"  → {out.name}")


# ---- Run ---------------------------------------------------------------------

VARIANTS = [
    ("01_ref_clone", build_v1_ref_clone),
    ("02_food_arrow", build_v2_food_arrow),
    ("03_drink_chain", build_v3_drink_chain),
    ("04_red_warning", build_v4_red_warning),
    ("05_exercise_arrow", build_v5_exercise_arrow),
    ("06_mri_doctor", build_v6_mri_doctor),
]

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    ok = fail = 0
    for tag, fn in VARIANTS:
        if only and only not in tag:
            continue
        try:
            fn()
            ok += 1
        except Exception as e:
            fail += 1
            print(f"  FAIL [{tag}]: {str(e)[:300]}")
    print(f"\n[done] {ok} OK / {fail} FAIL → {DEST}")
