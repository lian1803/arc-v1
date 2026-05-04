# marketing_agency — Agency-Level Decisions

> Frozen per DOCTRINE §7. Edit only with explicit Lian sign + new commit.

## Pricing (frozen)

- 3-package strategy: **38만 / 56만 / 95만**.
- Source detail: `sales_offline/가격전략.md` (Phase 2에서 `_shared/pricing.md` 로 이동 예정).
- Lian 사인: 이전 세션 (정확 날짜 확인 필요).

## Sub-project lineup (2026-04-26 session 27)

- **Active**: sales_offline / marketing_online / analytics / dev_products
- **Placeholder (Lian 미진입)**: education_consulting / branding_design / smb_automation

## LLM routing for agency decisions (2026-04-26 session 27)

- **평소 작업**: Claude single-family (Opus/Sonnet/Haiku tier per SPEC §6.1).
- **큰 결정**: `tools/llm_council.py` 거쳐 GPT + Claude + Gemini 동시 자문 (selective council, 임시).
- **Trigger**: DOCTRINE 새 §, 가격 변경, 새 사업 진입, 큰 클라이언트 제안, Lian 명시 호출.
- **30일 후 재평가**: cost vs Lian 결정 reversal 빈도 비교 후 stay/expand/drop 결정.

## Reorg history

- **2026-04-26 session 27 Phase 1**: container-level reorg.
  - 9 한국어 root → 7 영문 sub-project + `_shared/` + `archive/`.
  - 옛날/잡 4건 archive 로 이동 (sample1 naver-diagnosis legacy fork / ghost folder / 5 critique meta files / 온라인.zip).
  - 빈 sub-project 4개 (dev_products / education_consulting / branding_design / smb_automation) 4-folder skeleton 박음.
- **Phase 2 (next)**: sub-project 안 콘텐츠 4-folder 재배치 + 각 sub-project 메타 파일 박음.
