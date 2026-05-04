# selfie_factory — 인스타 셀카 자동 제작 도구 (ARC 첫 진짜 프로젝트)

> ARC 정신: 매뉴얼 < 사례, generic 금지, Reach Gate, 빌드 끝 시뮬 PASS.
> 본 프로젝트 = "scratch own itch" — Lian 본인이 매일 쓰는 도구가 곧 시드 사업.

## ICP — Lian 본인 (가상 아님, 진짜 사용자 1명)

- 직업: 1인 사업가 + 인스타 셀카 운영 (개인 피드)
- 환경: Windows 11, Python 3.14, ARC 시스템 보유, GEMINI_API_KEY/PERPLEXITY_API_KEY/FAL_KEY 보유
- 폰: 갤럭시 또는 비슷, 인스타 앱 사용
- IT: ARC + Cursor/Claude Code 활용 능숙. 단 셀카 만들 땐 매번 수동 워크플로우에 답답.
- 돈에 대한 태도: 본인 도구는 무료/저렴 우선. Gemini Nano Banana (장당 $0.04) OK. fal upscale (장당 $0.005-0.02) OK.

## Pain — Top 3 (Lian 본인 진술 2026-05-03)

1. **"매번 Pinterest 가서 레퍼런스 → ChatGPT 가서 프롬프트 → Gemini 웹 가서 합성, 매번 똑같이 수동"** — 1장당 5-10분. 일관성 X.
2. **"결과가 자연스럽지 않고 일률적으로 좋지도 않음"** — 매번 다른 얼굴, 뽀샤시, 디테일 부족.
3. **"웹에서 만들면 UI 잔재 (돋보기/확대 아이콘)가 결과에 박힘"** — 매번 손으로 지워야 함. 더 지우면 픽셀 망가짐.

## Solution — 핵심 기능 ≤3 (이미 도구 갖춤)

1. **edit (1장 편집)** — 기존 셀카에서 잡티 / UI 잔재 / 액세서리 제거
   - 도구: `tools/image/nano_banana.py edit` (Gemini 2.5 Flash Image)
   - 검증: 2026-05-03 테스트 — 귀걸이 + 돋보기/확대 아이콘 깔끔히 제거, 얼굴/배경 변형 0
2. **fuse (합성)** — 본인 얼굴 + Pinterest 참조 → 같은 얼굴 다른 장면
   - 도구: `tools/image/nano_banana.py fuse` (멀티 이미지 합성)
   - 검증: 다음 빌드에서 (refs/me.jpg + refs/style/*.jpg)
3. **post (후처리 선명도)** — 뽀샤시 → 사진 편집기 선명도 효과
   - 도구: `tools/image/sharpen.py compose` (PIL Unsharp + Sharpness + Contrast)
   - 검증: 2026-05-03 테스트 — PIL이 정답 (fal AI super-res들은 얼굴 변형 또는 용량만 ↑)

## 핵심 흐름 (Reach Gate: 5분 내 1장)

```
1. Pinterest 1장 다운로드 → projects/selfie_factory/refs/style/{name}.jpg
2. (1회만) 본인 셀카 5-10장 → projects/selfie_factory/refs/me/*.jpg
3. 명령 1줄:
   python tools/image/nano_banana.py fuse refs/me/me1.jpg refs/style/cafe.jpg \
     --prompt "이 옷/장면, 같은 얼굴, 자연광" \
     --out projects/selfie_factory/outputs/2026-05-04/cafe_v1.png
4. 후처리:
   python tools/image/sharpen.py compose outputs/2026-05-04/cafe_v1.png \
     --out outputs/2026-05-04/cafe_v1_sharp.png
5. 결과 → 인스타 업로드
```

## 가격 (본인 사용 시)

- Gemini Nano Banana: $0.039/장
- PIL sharpen: 무료
- 1장 풀 워크플로우: ~$0.04
- 월 30장: ~$1.20

## 죽일 기준 (30일 — 2026-06-03 체크)

- ❌ Lian 본인이 30일 안에 **5장 이상 안 만들면** = 죽임 (실 사용 X)
- ❌ 1장 만드는 데 평균 5분 넘으면 = 도구 너무 복잡, 단순화 또는 죽임
- ❌ "그냥 웹 Gemini가 더 빨라" 한 번 이상 발화 = 도구 패배
- ✅ 매주 1회 이상 사용 + 결과 인스타 실 업로드 = 살림 (런칭 검토 진입)

## Phase 2 진입 조건 (Lian 확인 후)

- 첫 빌드 = `make.py` (편집/합성/후처리 한 줄 batch) 또는 직접 명령 사용
- 우선 직접 명령으로 5장 만들어 보고, 매번 같은 명령 쓰면 그때 batch 박음 (lazy)
- 빌드 끝 시뮬 = 본인이 직접 1장 끝까지 → 5분 안에 만족 = PASS

## 런칭 시나리오 (30일 + 살림 시 검토)

- 타겟: 한국 1인 인스타 셀카 운영자 (남성/여성). Pinterest → ChatGPT → Gemini 같은 워크플로우 쓰는 사람.
- 차별: ARC 워크플로우 패키지 + 한국어 + 결과 일관성 + 자동 후처리
- 가격 가설: 월 $10-15 (Flamel/Mirra 가격대) 또는 장당 $0.30-0.50
- 채널: 인스타 본인 피드 자체 (build in public), 한국 indie hacker 커뮤니티

## 외부 정합

- raw/molds/external/baemin.md (협소 페인 패턴)
- raw/sources/dive_In_2026_how_do_creators_make_CONSISTENT__2026-05-03.md (정론: LoRA + IP-Adapter + Face Detailer가 표준 / Nano Banana는 빠른 합성용)
- 본 프로젝트 = "표준 워크플로우 (LoRA 학습)" 대신 "Nano Banana fuse + PIL sharpen" 단순화 시도. LoRA 학습 안 함 (1장 reference로 충분 가설 검증).

## 다음 한 동작 (Phase 2)

1. `refs/me/` 에 본인 셀카 5-10장 배치
2. `refs/style/` 에 Pinterest 참조 1장 배치
3. fuse 1번 시도 + sharpen → 결과 평가
4. 5분 안에 만족 = 첫 빌드 PASS, 실 사용 진입
