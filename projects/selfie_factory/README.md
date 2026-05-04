# selfie_factory — 사용 가이드 (Lian 본인용)

ARC 첫 진짜 프로젝트. PLAN.md 참조.

## 폴더

```
projects/selfie_factory/
├── PLAN.md              # ICP / 기능 / 죽일 기준
├── README.md            # 본 파일
├── refs/
│   ├── me/              # 본인 셀카 5-10장 (1회만 채움)
│   └── style/           # Pinterest 참조 (그때마다)
└── outputs/
    └── YYYY-MM-DD/      # 결과 (날짜별)
```

## 첫 셋업 (1회만, 5분)

1. 본인 셀카 5-10장 → `refs/me/me_001.jpg ~ me_010.jpg`
   - 다양한 각도 / 표정 / 조명
   - 얼굴 잘 보이는 거 위주
   - jpg/png 둘 다 OK

## 매일 사용 (1장당 ~3분)

### 패턴 1 — Pinterest 풍 합성

```bash
# 1. Pinterest 1장 다운 → refs/style/cafe_2026.jpg
# 2. 합성:
$env:NANO_BANANA_MODEL = "nano-banana-pro-preview"
python tools/image/nano_banana.py fuse `
  projects/selfie_factory/refs/me/me_003.jpg `
  projects/selfie_factory/refs/style/cafe_2026.jpg `
  --prompt "이 옷/장면 같은 분위기, 같은 얼굴, 자연광, 인스타 셀카" `
  --out "projects/selfie_factory/outputs/2026-05-04/cafe_v1.png"

# 3. 후처리 (선명도):
python tools/image/sharpen.py compose `
  "projects/selfie_factory/outputs/2026-05-04/cafe_v1.png" `
  --out "projects/selfie_factory/outputs/2026-05-04/cafe_v1_sharp.png"

# 4. cafe_v1_sharp.png → 인스타 업로드
```

### 패턴 2 — 기존 셀카 편집 (잡티 / UI / 장식 제거)

```bash
$env:NANO_BANANA_MODEL = "nano-banana-pro-preview"
python tools/image/nano_banana.py edit `
  "C:\path\to\my_selfie.jpg" `
  "Remove the earring and any UI icons. Keep face/pose/clothing/background identical." `
  --out "projects/selfie_factory/outputs/2026-05-04/cleaned.png"
```

### 패턴 3 — 텍스트만으로 새 셀카 (얼굴 reference 없이)

```bash
python tools/image/nano_banana.py generate `
  "natural Korean man selfie in Seoul cafe, soft window light, casual" `
  --out "projects/selfie_factory/outputs/2026-05-04/text_v1.png"
```

(얼굴 일관성 X — 매번 다른 얼굴. 패턴 1이 본인 얼굴 유지엔 더 적합)

## Claude한테 자연어 시키기 (간단)

> "내 selfie_factory 에서 me_003.jpg + style/cafe.jpg 가지고 카페 셀카 3장 만들어줘"
>
> Claude → 자동으로 fuse 3번 + sharpen 3번 → outputs/2026-05-04/ 에 6장 (raw + sharp)

## 비용 (장당)

- Nano Banana Pro fuse/edit: ~$0.09 (default 모델은 $0.04, Pro가 한국 얼굴 더 강함)
- PIL sharpen: 무료
- 1장 풀: **~$0.09**
- 월 30장: **~$3**

## 죽일 기준 (30일 후 체크 — 2026-06-03)

- 30일 안에 5장 이상 안 만들었으면 → 도구 폐기, refs/outputs 만 archive 보관
- "웹 Gemini가 더 빨라" 1번이라도 들면 → 단순화 또는 폐기
- 매주 1회 이상 + 인스타 실 업로드 = 런칭 검토 진입 (PLAN.md 런칭 시나리오 참조)

## 향후 (지금 X)

- `make.py` — 1줄 batch ("style 5개 → 본인 얼굴 + 5개 → 25장 한 번에"). 같은 명령 5번 이상 반복 발견 시 박음 (lazy).
- LoRA 학습 (Replicate Flux LoRA) — Nano Banana 일관성 부족 시 검토.
- fal upscale (충전 후 재시도) — sharpen으로 부족 시.
