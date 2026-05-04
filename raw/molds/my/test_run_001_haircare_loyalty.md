---
goal: 동네 1인 미용실 원장의 "단골 기억 못함" 페인을 카톡 자동 손님카드로 해결
setup:
  stack: Next.js 16 + Convex + Clerk(관리자) + 매장 PIN(정수민) + Toss Payments + Solapi 알림톡
  origin_pattern: baemin "협소 페인 + 함께 주문" → "1인 사장 단골 기억 못함 + 카톡 자동 손님카드"
  reference_mold: raw/molds/external/baemin.md
  premises_check: PREMISES.md (웹앱/모바일 브라우저) ✅, Reach Gate ✅ (PIN 1탭)
status: in-progress (PLAN + architecture 완성, build 미시작)
created: 2026-04-29
last_touched: 2026-05-03
actions:
  done:
    - 2026-04-29: PLAN.md 작성 (ICP 정수민 디테일 / Pain Top 3 / Solution 3기능 / 가격 / 채널 / 가설 3)
    - 2026-04-29: architecture.md 작성 (스택 / Convex 스키마 / 페이지 구조 / 인증 / 알림톡 / 결제 / mock 매핑)
    - 2026-04-29: mock/index.html 작성 (정수민 5분 자가검증 5개 통과)
  next:
    - architecture.md L131 "다음 단계" 4개 미체크
    - PLAN Phase 2 진입 (가설 1 발품 검증) Lian 결정
    - Convex 스키마 .ts 작성
    - Solapi 알림톡 검수 신청
outcomes:
  success_metrics: 미측정 (launch 0건)
  failures: 미측정
  in_progress_hypotheses:
    - h1_acceptance: 화곡동 30곳 발품 → 30%(9곳) "다이어리 사진 무료 디지털화" 수락
    - h2_self_use: 디지털화 받은 9곳 중 50%(4-5곳)가 4주 내 자발적으로 손님 카드 열어봄
    - h3_paid_conversion: 자발 사용자 중 30%(1-2곳)가 "1년 후 월 19,000원 지불 의향" 명시
lessons_so_far:
  - "Reach Gate가 BYOK 동형 패턴 회피 (invoice-snap 실패 학습 직접 차용)"
  - "PC X / 폰 1개로 모든 것 강제 = 정수민 IT 환경 fact (매장에 PC 둘 자리 X)"
  - "PIN dual-track 인증 = Clerk 백엔드 + 정수민 PIN 1회 셋업 + 일상은 무인증"
  - "한국 결제 = Toss Payments 전용 (Stripe는 USD 기본, 한국 카드 미지원 광범위)"
  - "월 1만원대가 동네 미용실 사장 결제 ceiling — 19,000원은 그 위 아슬아슬, 가설 3 실패 시 9,900원 fallback 준비"
  - "발품 = Do Things That Don't Scale (baemin 학습 #1 직접 차용)"
tags:
  - korea
  - b2c
  - 1-person-shop
  - haircare
  - mobile-first
  - kakao-business-channel
  - alimtalk
  - reach-gate-passed
  - in-progress
  - pre-launch
related_external_molds:
  - raw/molds/external/baemin.md (협소 페인 + 함께 패턴)
  - raw/molds/external/kakao.md (알림톡 13원/건)
  - raw/molds/external/toss.md (한국 결제)
related_failed_molds:
  - raw/molds/failed/luna_cloudflare_pitfalls.md (배포 함정 — Convex 사용 결정 시 참고)
  - raw/molds/failed/luna_agentic_subagent_failure.md (sub-agent 패턴 회피 = 1인 빌드 정합)
---

# test_run_001 — 동네미용실 단골카드 (정수민)

## 핵심 (BLUF)

화곡동 6.5평 1인 미용실 원장 정수민(38세)의 머릿속에 흩어진 단골 정보를 폰 1탭으로 옮겨주는 카톡봇.

## 주요 사실 (PLAN.md 발췌)

- **ICP**: 정수민 38세, 미용 13년차, 월 매출 700만원, 단골 70%/신규 30%, 객단가 4.2만원, 폰 갤럭시 1개만 사용 (매장 PC X)
- **Pain 3**: ① 단골 시술 이력 기억 X ② 노쇼 30% (펌 자리 비면 8만원 손실) ③ 다음 약속 잡기 깜빡 → 단골 자연 소실
- **Solution 3 기능**: ① 예약 30초 입력 (1탭) ② 시술 후 1탭 메모 ③ 알림톡 자동 (24h 전 + 4주차 컴백)
- **가격**: 무료 (50명 cap, 알림 X) / Pro 19,000원 (무제한 + 알림). 첫 1년 Pro 무료.
- **채널**: 화곡동 1km 30곳 발품 → 무료 다이어리 디지털화 → Pro 권유. 인스타 키치 콘텐츠 병행.

## 진척 (2026-05-03 기준)

- ✅ PLAN.md (8.6KB)
- ✅ architecture.md (6.9KB) — 스택 + 스키마 + 페이지 구조 + 인증 + 알림톡 + 결제 다 그림
- ✅ mock/index.html (12KB) — 정수민 자가검증 5개 통과
- ❌ 빌드 0줄
- ❌ 발품 0회

## 다음 한 동작

1. PLAN.md L68 "Phase 2 진입 조건" 결정 — 발품 진검증 vs 우회(빌드 먼저)
2. (B 선택 시) Convex 스키마 .ts → 코드 시작

## 풀 PLAN 원본

`projects/test_run_001/PLAN.md` 참조. 본 사례 파일은 라우팅 + 학습 추출용.
