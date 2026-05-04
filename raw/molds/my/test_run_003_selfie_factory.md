---
goal: Lian 본인의 인스타 셀카 자동 제작 (Pinterest → 본인 얼굴 + Gemini → 후처리). 검증 후 SaaS launch 검토.
setup:
  stack: Gemini 2.5 Flash Image (Nano Banana Pro) + PIL Unsharp Mask
  origin_pattern: "scratch own itch" — Lian 본인이 매일 쓰는 워크플로우 자동화
  reference_workflow: Pinterest 레퍼런스 → ChatGPT 프롬프트 → Gemini 웹 (수동) → ARC 자동 (1줄)
  premises_check: PREMISES.md (웹앱/모바일 X, CLI 사용자=Lian) ✅, Reach Gate 5분 내 1장 ✅
status: in-progress (도구 갖춤 + 첫 테스트 PASS, 실 사용 미시작)
created: 2026-05-03
last_touched: 2026-05-03
actions:
  done:
    - 2026-05-03 오후: Nano Banana Pro로 사용자 제공 셀카 2장 (1.png, 2.png) 편집 — 귀걸이 + UI 아이콘 제거 PASS, 얼굴/배경 변형 0
    - 2026-05-03 오후: PIL sharpen 5가지 + AuraSR 시도 — PIL이 정답 (fal AI super-res들은 얼굴 변형 또는 용량만 ↑)
    - 2026-05-03 오후: projects/selfie_factory/ 폴더 + PLAN.md + README.md 작성
  next:
    - refs/me/ 에 본인 셀카 5-10장 배치
    - refs/style/ 에 Pinterest 1장 배치 + fuse 첫 시도
    - 5분 안에 만족 = 첫 빌드 PASS
outcomes:
  success_metrics: 미측정 (실 사용 0회)
  failures: 미측정
  in_progress_hypotheses:
    - h1_solo_use: 30일 안에 본인이 5장 이상 만든다 (실 사용 검증)
    - h2_speed: 1장 평균 제작 시간 ≤ 5분 (Reach Gate 정합)
    - h3_quality: 결과를 인스타 실 업로드 ≥ 3회 (자기 만족 검증)
    - h4_launch: 30일 후 매주 1회 이상 사용 = SaaS 런칭 검토 진입
lessons_so_far:
  - "nano-banana-pro-preview 모델이 한국 얼굴 + 자연스러움에서 default(2.5-flash-image)보다 우위 ($0.09 vs $0.04)"
  - "fal AI super-res (clarity/esrgan/aura)는 얼굴 변형 또는 용량만 ↑ — 셀카 후처리에 부적합"
  - "PIL Unsharp Mask가 사진 편집기 '선명도' 슬라이더와 가장 동일 — AI 도구보다 정답"
  - "1장 + 1장 fuse가 LoRA 학습 없이도 실용적 (LoRA는 일관성 100% 필요 시점에 검토)"
  - "make.py batch는 같은 명령 5번 이상 반복 시 lazy 박기"
tags:
  - korea
  - solo-tool-first
  - selfie
  - instagram
  - nano-banana
  - gemini-image
  - pil-sharpen
  - mobile-first
  - in-progress
  - pre-launch
  - scratch-own-itch
related_external_molds:
  - raw/sources/dive_In_2026_how_do_creators_make_CONSISTENT__2026-05-03.md (LoRA + IP-Adapter 정론, 본 프로젝트는 단순화 시도)
  - raw/sources/perplexity_solopreneur_standard_2026-05-03.md (1인 SaaS 표준 30일 검증 → 2-8주 MVP → 베타 5-20명)
related_failed_molds:
  - raw/molds/failed/luna_agentic_subagent_failure.md (sub-agent 망 회피 = 1인 도구 정합)
---

# selfie_factory — Lian 본인용 인스타 셀카 자동 제작 (ARC 첫 진짜 프로젝트)

## 핵심 (BLUF)

기존 워크플로우(Pinterest → ChatGPT → Gemini 웹, 수동 5-10분)를 ARC 자동 1줄 명령(~3분, 일관성 ↑)로 대체. Lian 본인 30일 사용 검증 → 매주 사용 시 SaaS 런칭 검토.

## 진척 (2026-05-03 기준)

- ✅ 도구: nano_banana.py (edit/fuse/generate) + sharpen.py (PIL 6가지) + upscale.py (fal — 잔고 소진 후 보류)
- ✅ 검증: 2장 실 셀카 편집 (귀걸이/UI 제거) PASS
- ✅ 후처리 도구: PIL이 정답으로 결정
- ✅ 프로젝트 폴더 + PLAN + README
- ❌ refs/me/ 비어있음 (본인 셀카 미배치)
- ❌ fuse 첫 시도 미수행
- ❌ 인스타 실 업로드 0회

## 다음 한 동작

1. 본인 셀카 5-10장 → `projects/selfie_factory/refs/me/`
2. Pinterest 1장 → `projects/selfie_factory/refs/style/`
3. fuse + sharpen 1세트 시도
4. 5분 안에 만족 = PASS, 매일 사용 진입

## 풀 PLAN

`projects/selfie_factory/PLAN.md` 참조.
