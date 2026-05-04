# sales_offline — 오프라인 자영업자 영업

> 메인 사업. 010 수집 + 네이버 진단 + CRM + PPT 제안 풀 파이프라인.

## Status
**active** — 28MB, 실작동 (94 도시 010 수집, naver-diagnosis 4월 20일 최신).

## 4-folder

- **planning/** — 영업 전략 + 패키지 + 실행팀 기록.
  - `sales_strategy/` — 영업_사업검증, 영업_전략_재설계, 패키지_설계, 영업툴_개발스펙
  - `exec_team_archive/` — 7 agent 실행 기록 (autonomous run)
- **design/** — 서비스 카드 14장.
  - `service_cards/` — blog/danggeun/google/instagram/kakao/naver/sns/shortform/homepage 등
- **marketing/** — 리서치 + 영업 메시지 + 자료.
  - `research/` — 35 md (deep-dive + step2/3/4 채널별)
  - `sales_scripts/` — 영업 스크립트 v1/v2/v3 + 영업사원 가이드
  - `sales_research/` — 영업전문가 자료
- **development/** — 코드 + 데이터.
  - `naver_diagnosis/` — FastAPI (포트 8000), 진단 엔진, 40+ services
  - `sales_crm/` — Flask (포트 5000), CRM
  - `lead_db/` — 94 xlsx (가평~화성 010 수집, 16MB)
  - `clients/sample_yangju_salon/` — 샘플 클라이언트 (wave1-6 기록)
  - `clients/sample_uijeongbu_restaurant/` — 빈 placeholder

## ICP & 가격 (DOCTRINE §7 Frozen)

### 누구한테 파나
- **월 매출**: 1,200-2,000만원 (순이익 300-800만)
- **업종**: 식당 / 미용실 / 카페 / 학원 / 기타 소상공인
- **문제 신호**: 네이버 플레이스 순위 10위권 밖 OR 리뷰/사진 부족
- **이용 도구**: 엑셀 / 카톡 / 네이버 (CLI 못 씀)

### 패키지 가격 (Frozen, `_shared/pricing.md`)
| 패키지 | 월액 | 손익분기점 | 특징 |
|---|---|---|---|
| 기본 | 38만 | 신규 손님 5-8명 | 네이버 플레이스 기본 관리 |
| 표준 | 56만 | 신규 손님 10-15명 | 기본 + 블로그 리뷰 유도 |
| 프리미엄 | 95만 | 신규 손님 20-25명 | 전체 + SNS 통합 |

가격 anchor: 38만 = 월 순이익 30-40% 비중. "월 38만 기준 (정상가 50만)" 으로 할인감 생성.

### 5 업종 Pain Point + 메시지 프레임

**1. 식당** (한식 / 카페 / 피자 / 중식)
- Pain: 신규 손님 3-5명/월 정체 → 순위 하락 악순환
- 메시지 톤: 실제성 + 안심 (구체 수치, "이번 달 신규 N명 줄었어요")
- Hook: 경쟁사 대비 리뷰 격차 직접 비교

**2. 미용실** (머리 / 네일 / 피부)
- Pain: 주 2-3건 예약 유지 어려움 → 신규 손님 채널 부재
- 메시지 톤: 감정 + 예약 빈도 ("새 손님이 들어오는 채널이")
- Hook: 영수증 리뷰 (최신성 증명) > 블로그 > 방문 리뷰

**3. 카페** (카페 / 베이커리 / 디저트)
- Pain: 인생샷 트렌드 → 사진 품질/최신성 부족
- 메시지 톤: 취향 + 트렌드 ("우리 카페 사진과 저쪽 비교")
- Hook: 사진 격차 ("우리 3장 vs 저쪽 18장, 매주 업뎃")

**4. 학원** (학원 / 입시 / 어학)
- Pain: 부모 문의 → 상담 전환율 (입체적 신뢰)
- 메시지 톤: 신뢰 + 검증 ("부모님 문의가 줄었다는 느낌")
- Hook: 블로그 리뷰 (상세 후기) > 영수증 리뷰

**5. 기타** (편의점 / 세탁소 / 수리점 / 마사지)
- Pain: 존재감 희미 → 검색 노출 최소
- 메시지 톤: 현실 + 해결책 ("지금 검색하면 안 보임")
- Hook: 순위 인식도 ("지금 순위 몇 위인지 아세요?")

### Self-Image A/B 톤 분리 (자영업자 마케팅 인지도)
- **Type A** (마케팅 모름, 리뷰<10 + 사진<10): 친절·초보자 관점, 안심 톤, "여쭤볼 게 있어서요"
- **Type B** (경험 있음, 리뷰≥20 + 블로그/카톡): 전문가·데이터 중심 톤, "현재 이 상태가 맞는지 빠르게 확인해보실래요?"

자동 판별: `_detect_self_image()` 함수 (`message_generator.py`).

---

## Pending

- [ ] sales_crm/app.py 1725 LOC, §9 grandfather (in-file marker 박음 2026-04-28). 자연 수정 시점 split.
- [ ] naver_diagnosis/services/naver_place_crawler.py **1946 LOC** (1760 → 1946, 세션 29 commits ddcb381+ab1bd8f 가 split 없이 +186 LOC), §9 활성 위반. in-file marker 박음 2026-04-28. 다음 edit 시 split 의무.
- [ ] sample_yangju_salon 안 wave1-6 기록 — 4-folder 재배치 미완 (sub-sub-project 격).
- [ ] DOCTRINE §15 Target-Reach Gate 소급 — Lian (자영업자) ICP 도구 = 엑셀/카톡/네이버. 진단 PDF 받기 OK, 010 수집은 사내 운영. reach 확인.

## Phase status
ARC Phase 3 (real project run) 진입 안 함. acceptance.md 박는 시점 = Phase 3 close 결정 시.

## Parent
`../CLAUDE.md` (marketing_agency container router).
