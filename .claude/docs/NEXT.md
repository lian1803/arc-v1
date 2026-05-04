# NEXT — 다음 세션 시작 가이드

> 매일 세션 시작 시 cold start 방지. 5초 안에 "오늘 무엇할지" 잡기.
> 외부 정론 Q2 (context engineering) 정합. Lian 결심 "매일 조금씩" 정합.

---

## 마지막 업데이트: 2026-05-04

## 핵심 상태 (오늘 세션 끝 기준)

- **ARC 시스템**: 외부 정론과 정합 확인 (3차 perplexity 검색 완료, raw/sources/ 4개 통합본).
- **Luna 자산 carry over**: 시뮬 도구 6개 (tools/sim/) + 실패 학습 3개 (raw/molds/failed/) + 외부 사례 1개 (raw/molds/external/cloudflare_recipes.md).
- **사업 launch**: **0건** (Pilot Graveyard 위험 진입).

## ⚠️ 가장 중요한 경고

외부 정론 Q5: **"1인 시스템은 사업 launch 1건 전엔 더 디벨롭하지 마라."**

ARC 현재 = "Pilot Graveyard" (프로토타입 12-24개월 iteration, launch 0건) 입구.
시스템 손대고 싶을 때마다 self-check: "이게 사업 launch에 직접 기여하나?"

## 진행 중 사업 (in-progress, raw/molds/my/ + projects/)

1. **test_run_001** — 동네미용실 단골카드 (정수민, 화곡동). PLAN+architecture 완성, 빌드 0줄.
   - 다음 동작: Phase 2 진입 결정 (발품 진검증 vs 빌드 우회)
2. **test_run_002** — 1인 솔로 워커 도구 (5개 후보). PLAN 0건.
   - 다음 동작: 5개 중 1개 픽 → PLAN 1장 → 빌드. 추천: #3 인보이스 자동독촉.
3. **youtube_automation_demo** (luna carry, 5/4) — 60대 무릎통증 풀 영상 + 36.7분 mp4 2개 무사. 썸네일 V5 (Lian 1계정 brand spec) 8장 → 테스트 반복 단계.
   - 다음 동작: factory_v5_lian.py 변형 테스트 (asset 캐시 재사용 = $0/30s) → 만족하는 1장 픽 → 영상 업로드.
   - Spec: `raw/sources/youtube/lian_1account_brand_spec_2026-05-04.md`
   - 캐시: `tools/image/_out/factory_v5_assets/` (의사 누끼 5명 재사용 가능)

## 다음 세션 첫 30분 (외부 정론 권장 순서)

### 옵션 A — 사업 launch 우선 (★ 강력 추천)
1. test_run_002 PLAN.md 작성 (인보이스 자동독촉, ICP/기능 ≤3/흐름/30일 죽일 기준)
2. 빌드 시작 (Cursor + Claude 1대1, sub-agent 망 X)
3. 빌드 끝 → tools/sim/ 페르소나 시뮬 PASS

### 옵션 B — 시스템 작업 (조심: Pilot Graveyard)
- raw/molds/my/ 추가 사례 정형화
- luna에서 추가 자료 carry (planning_jtbd, sales_b2b_objection_handling, llm_instruction_drift_mitigation 등)
- tools/cost_log.py / cost_gate.py carry
- 단 옵션 A 1개 launch 전엔 옵션 B 비중 ≤30%

### 옵션 C — 외부 자료 추가 검색
- 4차 perplexity 또는 직접 GitHub (BMAD-Method, Spec Kit 등)
- 단 이미 3차 검색까지 했음 — 행동 우선

## 어디에 뭐가 있나 (라우팅)

- **외부 정론**: raw/sources/INDEX.md (4개 통합본)
- **사례 (성공/외부)**: raw/molds/my/, raw/molds/external/
- **사례 (실패)**: raw/molds/failed/ (luna 3개)
- **시뮬 도구**: tools/sim/reference/ (luna invoice-snap 5개 + smoke_checks)
- **사업 진행 중**: projects/test_run_001/, projects/test_run_002/

## 룰 (CLAUDE.md / MODES.md 요약)

- 30줄 cap CLAUDE.md, generic 금지
- Phase 1 = 대화로 PLAN 1장 (ICP / 기능 ≤3 / 흐름 / 30일 죽일 기준)
- Phase 2 = Lian + Cursor/Claude 1대1, sub-agent 망 X
- 빌드 끝 = tools/sim/ 페르소나 시뮬 PASS
- 30일 내 20 signup OR 5 pre-sale 못 받으면 죽이고 다른 사례

## 매 세션 끝에 할 것

1. NEXT.md 갱신 (오늘 한 일 + 내일 첫 동작)
2. raw/molds/my/ 사례 진척 업데이트 (lessons 한 줄 추가 가능 시)
3. .tmp_* / 신규 루트 파일 = `.claude/hooks/route_root_writes.py` 자동 차단 (2026-05-04 박음). 룰: `.claude/rules/file-routing.md`. 5/4 일괄 정리분 → `archive/2026-05_root_cleanup/`.
