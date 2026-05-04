# marketing_agency — Container Router

> Multi-product agency container. Each sub-project = independent business line with its own planning/design/marketing/development.

## Sub-projects

| Folder | Status | Description |
|---|---|---|
| `sales_offline/` | active | 오프라인 자영업자 영업 (010 수집 + 네이버 진단 + CRM, 메인 사업) |
| `marketing_online/` | active | 온라인 마케팅 (5팀: 강의코칭/온라인영업/인스타D2C/쿠팡셀러/온라인마케팅) |
| `analytics/` | active | 데이터분석 서비스 라인 |
| `dev_products/` | partial | 개발사 판매 상품 조사 + 자체 제작 (Claude Code 활용 사업) |
| `education_consulting/` | placeholder | Lian 미진입, 4-folder skeleton만 |
| `branding_design/` | placeholder | Lian 미진입, 4-folder skeleton만 |
| `smb_automation/` | placeholder | Lian 미진입, 4-folder skeleton만 |

## Shared assets

- `_shared/` — 공통 자산 (PRD_시스템 / SOW_템플릿 / 제안서_템플릿 / 온보딩_프로세스 / website hero / templates).
- `archive/` — legacy/ghost/메타 파일 (§6 Accumulate-Never-Delete 보존).

## Routing (Lian instruction → sub-project)

| 키워드 | Sub-project |
|---|---|
| "오프라인 영업", "010", "네이버 진단", "PPT 제안" | `sales_offline/` |
| "온라인 마케팅", "쿠팡", "인스타", "강의" | `marketing_online/` |
| "데이터분석" | `analytics/` |
| "개발 상품", "우리도 만들 상품" | `dev_products/` |
| 가격 / SOW / 제안서 / 온보딩 (공통) | `_shared/` |

## ARC integration (2026-05-04 갱신, luna DOCTRINE → ARC 시스템 룰)

> luna 의 DOCTRINE.md 본문은 ARC 에 carry 되지 않음. 의미 단위로만 살려서 ARC 시스템 룰에 매핑.

- **MODES.md Phase 1**: sub-project 별 PLAN.md (ICP / 기능 ≤3 / 흐름 / 30일 죽일 기준). 컨테이너 자체는 router (PLAN 대상 X).
- **MODES.md Phase 2**: Lian + Cursor/Claude 1대1, sub-agent 망 X. 빌드 끝 = `tools/sim/` 페르소나 시뮬 PASS.
- **CLAUDE.md Reach Gate**: sub-project 별 "ICP 가 5분 안에 자기 손으로 쓸 수 있나?" NO → 재설계.
- **DECISIONS.md frozen** (luna §7 의미 단위): `_shared/pricing.md` + `DECISIONS.md` 가격/lineup = AI 변경 금지. Lian 사인 + 새 commit 만 허용.
- **size cap (luna §9 의미 단위)**: 코드 ≤300 / docs ≤200 / agent prompt ≤150 LOC. legacy 1700+ LOC 파일 (sales_offline/영업툴/sales_crm/app.py 등) = grandfather 위반, 자연 수정 시점에 split.
- **외부 정론 비교 (luna §13 의미 단위)**: ≥150 LOC strategic 산출물 (blueprint / agent prompt / new pricing) handoff 전 외부 3+ 소스 인용. `tools/search/dive.py` 활용.
- **kpi_log.jsonl + .stale_exempt** (luna §11/§11.1): ARC 본체에 §11 없음. 파일 자체 정보 가치로 보존. 자동 monitor 미가동.
- **사용자 보호 영역**: `지우지마.txt` (7 카테고리 비전 정의) + `_shared/` 한국어 파일명 = 사용자 의도 명시 자료. AI 통합/영문화 시도 X.
- **외부 라우팅**:
  - mold: `raw/molds/my/marketing_agency.md`
  - 진행 등록: `.claude/docs/NEXT.md` (진행 중 사업 #4)
  - 파일 위치 룰: `.claude/rules/file-routing.md` (루트 cap hook 작동)

## Pending Phase 2 reorg

- 각 sub-project 콘텐츠를 4-folder (planning/design/marketing/development) 재배치.
- `_shared/` 한국어 파일명 영문화 (PRD_시스템.md → PRD_master.md 등).
- `sales_offline/가격전략.md` → `_shared/pricing.md` 이동 + §7 frozen 마킹.
- 각 active sub-project 에 acceptance.md / kpi_log.jsonl / DECISIONS.md 박음.
- `dev_products/` 안 cards + research 콘텐츠를 4-folder 로 재배치.
- `sales_offline/오프라인 자영업자 마케팅 대행 실행팀/` 영문화 + planning/ 으로 이동.

## Multi-LLM council (selective, 2026-04-26 session 27)

- 평소 작업: Claude single-family (SPEC §6.1 tier 라우팅).
- 큰 결정 (DOCTRINE 새 §, 가격 변경, 새 사업 진입, 큰 클라이언트 제안): `tools/llm_council.py` 거쳐 GPT + Claude + Gemini 동시 자문. 임시 도입, 30일 후 효과 재평가.
