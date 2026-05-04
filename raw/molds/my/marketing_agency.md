---
goal: AI 시스템(ARC = Claude Code 기반)으로 7개 카테고리 사업 라인을 굴리는 multi-product 에이전시 컨테이너
setup:
  structure: 7 sub-project + _shared + archive (container router 패턴)
  active: sales_offline / marketing_online / analytics / dev_products
  placeholder: education_consulting / branding_design / smb_automation
  pricing_frozen: 38만 / 56만 / 95만 (DECISIONS.md, 사용자 사인)
  origin_pattern: luna 시절 enterprise 패턴 (4-folder × 7 sub-project) → ARC carry (구조 보존)
  reference_mold: 본 사례가 ARC 첫 multi-product 컨테이너 (single-product 사례 = test_run_001/003)
  premises_check: PREMISES.md (웹앱/모바일) ✅ — 7 카테고리 모두 웹 기반 / Reach Gate sub-project별 별도 검증
status: in-progress (luna carry 완료, ARC 시스템 호환성 연결 = 2026-05-04, sub-project 별 launch 0건)
created: 2026-04-26 (luna session 27 Phase 1 reorg)
last_touched: 2026-05-04 (ARC 호환성 연결)
actions:
  done:
    - 2026-04-26 (luna): 9 한국어 root → 7 영문 sub-project + _shared + archive 재배치
    - 2026-04-26 (luna): _shared/ PRD_master.md (25.9KB) + SOW_template.md (16.9KB) + pricing.md + proposal_template.md + onboarding.md
    - 2026-04-27 (luna): dev_products bootstrap (6 paste-ready 파일, 652 LOC)
    - 2026-05-03 (ARC): luna 통째 carry, ARC projects/marketing_agency/ 로 이동
    - 2026-05-04 (ARC): 호환성 연결 (raw/molds/my 등록, NEXT.md 등록, CLAUDE.md ARC integration 섹션 갱신)
  next:
    - active 4개 sub-project 중 1개 pick → ARC MODES.md Phase 1 PLAN.md 1장 (ICP/기능 ≤3/흐름/30일 죽일 기준)
    - placeholder 3개는 사용자 진입 시점까지 동결
    - sales_offline/영업툴/sales_crm/app.py (1700+ LOC) §9 size cap 위반 — 자연 수정 시점에 split
outcomes:
  success_metrics: 미측정 (sub-project 모두 launch 0건)
  failures:
    - "luna enterprise 패턴 (4-folder × 7 sub-project)이 ARC v3 미니멀 정신과 충돌. 사용자 '지우지마.txt' = 비전 보존 의지로 구조 유지"
    - "외부 정론 Q5: '1인 시스템은 사업 launch 1건 전엔 더 디벨롭하지 마라' — sub-project 7개 디벨롭은 위반 시그널. active 4 → 1로 좁히는 결정 미루는 중"
  in_progress_hypotheses:
    - h1_pricing: 38만/56만/95만 3-package가 자영업/SMB 타겟에 적정 (검증: pre-sale 5건)
    - h2_lineup: 7 카테고리 중 sales_offline 또는 dev_products가 첫 launch (검증: 30일 내 1개 파일럿 수주)
lessons_so_far:
  - "사용자 '지우지마.txt'에 7 카테고리 직접 정의 = 비전 보호 영역. 시스템 차원 통합 시도 X"
  - "DECISIONS.md (DOCTRINE §7 frozen) = 가격/lineup 동결. AI 자체 변경 금지"
  - "container-level kpi_log.jsonl + .stale_exempt 마커 = luna §11/§11.1 패턴 carry. ARC에 §11 없으나 파일 자체 보존 (정보 가치)"
  - "_shared/ 한국어 파일명 (지우지마.txt 등) 영문화 보류 — 사용자 의도 명시 자료라 그대로 유지"
arc_integration:
  modes_md: "Phase 1 PLAN.md = sub-project별로 작성. 컨테이너 자체는 PLAN 대상 X (router)"
  raw_molds_my: "본 파일 = mold. sub-project별 launch 시 sub-project별 mold 추가 가능"
  next_md: "진행 중 사업 #4 등록 (2026-05-04 박음)"
  hook_routing: ".claude/hooks/route_root_writes.py 영향 X (projects/ 하위)"
  doctrine_legacy: "marketing_agency/CLAUDE.md L34-38 luna DOCTRINE §7/§9/§11/§13/§15 참조 = ARC에 미존재. 의미 단위로만 살림 (가격 동결 = §7 / size cap = §9 / 외부 비교 = §13 / Reach Gate = §15)"
---

# marketing_agency — 사용자 지우지마.txt 7 카테고리

사용자 정의 7개 사업 카테고리 (지우지마.txt 원문):

1. **개발회사** — Claude Code(ARC 시스템)으로 받은 모든 종류 개발. 고객 모집 자유.
2. **교육·컨설팅** — ARC 시스템으로 전략·기획. 타겟 = 중소·소소기업.
3. **데이터분석** — 미정의 (사용자 위임)
4. **브랜딩·디자인** — 콘텐츠/브랜딩/로고/상세페이지/홈페이지/쇼핑몰
5. **오프라인** — 식당 등 오프라인 매장 마케팅
6. **온라인** — 온라인 매장 (정의 미정)
7. **중소기업 자동화 플로우** — 엑셀도 안 쓰는/단순 반복 직원 → 자동화 시스템

매핑:
- 1 → `dev_products/`
- 2 → `education_consulting/` (placeholder)
- 3 → `analytics/`
- 4 → `branding_design/` (placeholder)
- 5 → `sales_offline/` (메인)
- 6 → `marketing_online/`
- 7 → `smb_automation/` (placeholder)
