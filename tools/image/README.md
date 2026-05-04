# tools/image — 이미지 생성/편집/합성 (Nano Banana = Gemini 2.5 Flash Image)

웹 Gemini의 "나노바나나" 와 같은 backend. API 직접 호출로 배치/자동화.

## 파일

| 파일 | 역할 |
|---|---|
| `nano_banana.py` | text→image / image+text→edit / multi-image fusion |
| `_out/` | 기본 저장 폴더 (timestamp 파일명 자동) |

## 사용 — 3가지 패턴

### 1. text → image (가장 단순)
```bash
python tools/image/nano_banana.py generate "natural-looking selfie of a Korean woman in a Seoul cafe, soft window light, no makeup"
```
→ `tools/image/_out/gen_YYYYMMDD_HHMMSS.png`

### 2. image + 명령 → 편집 (1장 가지고 변형)
```bash
python tools/image/nano_banana.py edit my_selfie.jpg "change background to outdoor cafe terrace, keep face exact"
python tools/image/nano_banana.py edit my_selfie.jpg "add Pinterest-style soft pastel filter"
```

### 3. 여러 이미지 합성 (★ Nano Banana 핵심)
```bash
python tools/image/nano_banana.py fuse my_selfie.jpg outfit_ref.jpg --prompt "wearing this outfit, same face, café setting"
python tools/image/nano_banana.py fuse my_face.jpg pose_ref.jpg bg_ref.jpg --prompt "my face, this pose, that background"
```
→ 본인 얼굴 + Pinterest 레퍼런스 + 의상 참조 = 본인이 그 스타일로 입은 새 셀카.

## 기존 Lian 워크플로우 매핑

**전:** Pinterest → ChatGPT 프롬프트 → 웹 Gemini 나노바나나 (수동, 매번)
**후:** `nano_banana.py fuse` 1줄 → 같은 결과 + 자동 저장

**Claude에게 자연어로 시키기 (앞으로 패턴):**
> "내 셀카 (D:\sel.jpg) + Pinterest 카페 1장 → 5번 합성해서 _out/ 에 저장해"
>
> Claude → fuse 5번 호출 → 결과 보고

## 비용

- **장당 약 $0.039** (Gemini 2.5 Flash Image)
- 100장 = $4
- `tools/cost/cost_log.py` 자동 기록 (`.cost_log.jsonl`)

## 모델

기본: `gemini-2.5-flash-image-preview` (2026 안정 preview).
환경변수로 override 가능:
```bash
$env:NANO_BANANA_MODEL = "gemini-2.5-flash-image"
```

## 한계 (정직)

- **얼굴 일관성**은 LoRA 학습보다 약함. 같은 얼굴 시리즈는 좋지만 100% 동일은 아님.
- 한국 얼굴은 자연스러움 좋음. 단 가끔 "AI 같은" 느낌 남음 → Krea/Higgsfield 후처리 권장.
- 이미지 출력 해상도 제한 (1024-2048 정도). 4K는 별도 upscaler.
- `safety_settings` 기본값 적용 — 일부 프롬프트 거부될 수 있음.

## 고급 — 같은 얼굴 시리즈 (캐릭터 일관성)

본인 셀카 1장을 모든 fuse 호출에 첫 인자로 박으면 같은 얼굴 유지 잘 됨:
```bash
python tools/image/nano_banana.py fuse me.jpg cafe.jpg --prompt "same face, cafe scene"
python tools/image/nano_banana.py fuse me.jpg outdoor.jpg --prompt "same face, outdoor scene"
python tools/image/nano_banana.py fuse me.jpg formal.jpg --prompt "same face, formal setting"
```
→ 같은 얼굴, 다른 배경 시리즈.

진짜 LoRA급 일관성 원하면 Replicate Flux LoRA 학습 ($1-2 일회성, 더 강함).
