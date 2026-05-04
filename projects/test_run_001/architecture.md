# test_run_001 — architecture.md

> Architecture-first (onboardinghub 패턴 차용). 코드 X. 빌드 청사진만.
> 입력: PLAN.md + mock/index.html + 6개 사례 공통 패턴 (raw/molds/external/).
> Reach Gate 통과 (스택 모순 0건 — 인증 dual-track / 결제 한국화로 해소).

## 1. 스택 결정

| 영역 | 채택 | 근거 |
|---|---|---|
| 프론트 | Next.js 16 App Router + Tailwind v4 | 모바일 우선 (PREMISES.md), 정수민 폰 first. shadcn/ui (onboardinghub 차용) |
| 백엔드 | Convex | TypeScript 풀스택, 실시간 sync, 정수민에게 안 보임 (Reach Gate 무관) |
| 인증 | **Clerk (Lian/관리자) + 매장 PIN (정수민)** dual-track | mock 가드 "회원가입/로그인 0개" 충족 + 어드민 백엔드 보안 |
| 결제 | **Toss Payments (한국 KRW)** + Stripe Subscriptions 패턴 차용 | 정수민 한국 카드, 한국어 영수증. Stripe는 글로벌 X (stripe_atlas.md 차용 후보 #2 명시) |
| 알림 | Solapi 알림톡 (kakao.md §5) | 13원/건, PLAN.md 월 100건 ≈ 1,500원 흡수 ⭕ |

## 2. DB 스키마 (Convex)

```ts
// convex/schema.ts (개념도)
shops: {  // 정수민 매장
  _id, name, ownerEmail, pinHash, businessChannelId,
  solapiSenderNo, plan: "free"|"pro", trialEndsAt, createdAt
}
customers: {  // 정수민의 단골 손님
  _id, shopId, name, phone, firstVisitAt, lastVisitAt,
  totalVisits, tags: ["단골"|"신규"]
}
visits: {  // 시술 1회 = 1 row
  _id, customerId, shopId, visitedAt,
  serviceType: "컷"|"펌"|"염색"|"케어",
  memo: string,  // "매직 + 회색 톤다운"
  nextDueWeeks: number  // "다음 4주 후 컷"
}
bookings: {  // 예약
  _id, customerId, shopId, scheduledAt,
  status: "예정"|"완료"|"노쇼"|"취소",
  remindSentAt: timestamp|null  // 알림톡 발송 추적
}
alimtalk_log: {  // 알림톡 발송 기록 (DOCTRINE §6 accumulate)
  _id, shopId, customerId, templateId,
  payload: object, sentAt, solapiResponse
}
admin_users: {  // Clerk 동기화 (Lian + 운영자만)
  _id, clerkUserId, role: "lian"|"ops", createdAt
}
```

## 3. 페이지 구조 (Next.js App Router)

```
app/
├─ (정수민용 - PIN 인증)
│  ├─ s/[shopId]/page.tsx          → mock "오늘" 화면
│  ├─ s/[shopId]/customer/page.tsx → mock "손님" 화면
│  ├─ s/[shopId]/alim/page.tsx     → mock "알림" 화면
│  ├─ s/[shopId]/customer/[id]/page.tsx → 손님 카드 모달 → 라우트
│  ├─ s/[shopId]/booking/new/page.tsx   → 예약 추가 모달 → 라우트
│  └─ s/[shopId]/login/page.tsx    → PIN 4자리 입력 (1회만)
├─ (Lian/관리자용 - Clerk 인증)
│  ├─ admin/shops/page.tsx         → 등록된 매장 목록
│  ├─ admin/shops/new/page.tsx     → Lian 발품 후 매장 생성 (PIN 셋업)
│  └─ admin/alimtalk/page.tsx      → 알림톡 템플릿 / 발송 통계
├─ api/
│  ├─ webhook/toss-payments/route.ts → 구독 결제 webhook
│  └─ cron/send-alimtalk/route.ts    → 매일 발송 큐 처리
└─ middleware.ts → /admin/** Clerk 인증, /s/** PIN 인증
```

## 4. 인증 흐름 (dual-track)

### 4.1 정수민 (일상 사용) — PIN
- **첫 셋업**: Lian 발품 시 매장 생성 → 4자리 PIN 발급 (예: 1234) → 정수민 폰에 매장 URL `/s/{shopId}` 저장 (홈화면 추가) + PIN 1회 입력 → JWT 7일 + refresh 30일
- **일상**: 폰 홈화면 아이콘 탭 → 즉시 진입 (PIN 자동 토큰)
- **PIN 만료/유실**: 같은 매장 URL + PIN 재입력. PIN 분실 시 Lian 연락 → 재발급
- **mock 가드 충족**: 가입/로그인 화면 0개 (PIN 1회는 셋업 단계 = 정수민 의식 X)

### 4.2 Lian / 운영자 — Clerk
- `/admin/**` 진입 시 Clerk 인증 (이메일 + magic link)
- 매장 생성 / PIN 발급 / 알림톡 템플릿 등록 / 발송 통계
- Clerk = 정수민 손에 안 닿음 (Reach Gate 무관)

## 5. 알림톡 통합 (Solapi 차용)

### 5.1 사전 셋업 (Lian 발품 1회 / 매장당)
1. 정수민 카카오톡 전자증명서 → business.kakao.com 비즈채널 가입 (5분, kakao.md §1)
2. Solapi 콘솔에서 비즈채널 연결 + 발신번호 등록 (1-2일)
3. 알림톡 템플릿 2종 등록 (1-3일 카카오 검수):
   - `T_REMIND_24H`: "${customer_name}님, 내일 ${time} ${shop_name} 예약 잊지 않으셨죠? :)"
   - `T_RECOMEBACK_4W`: "${customer_name}님, ${shop_name}입니다. 컷 시기네요~ 편하실 때 카톡 주세요 :)"

### 5.2 발송 흐름
- 매일 새벽 cron (`/api/cron/send-alimtalk`):
  - bookings 중 `scheduledAt` 24h 후 + `remindSentAt IS NULL` → T_REMIND_24H
  - visits 중 `visitedAt + nextDueWeeks` 도래 → T_RECOMEBACK_4W
- 발송 = Solapi POST `/v1/messaging` (kakao.md Python snippet 그대로)
- alimtalk_log에 기록 (DOCTRINE §6 accumulate)

## 6. 결제 흐름 (Toss Payments)

### 6.1 PLAN.md 매핑
- 무료 (영원히): 손님 50명 제한, 알림톡 X
- Pro 월 19,000원: 손님 무제한 + 알림톡
- 첫 1년 Pro 무료 = `trialPeriodDays: 365` (Stripe Subscriptions 패턴 차용)

### 6.2 Toss Payments 흐름 🌐
- 정수민 카드 등록 = Lian 발품 시 Toss Payments 위젯 (한국 카드 직접 입력)
- 정기결제 = Toss Payments 빌링키 발급 → 매월 자동 청구
- 한국 영수증 자동 발행 (현금영수증 옵션)
- Webhook = `/api/webhook/toss-payments` (성공/실패 → shops.plan 업데이트)

### 6.3 Stripe X 근거
- 정수민 한국 KRW + 한국 카드. Stripe는 USD 기본, 한국 카드 미지원 광범위. atlas는 Lian의 글로벌 사업 carry-over 용 (정수민 SaaS 무관).

## 7. mock UI 흐름 → architecture 매핑

| mock 화면 | 라우트 | 데이터 source |
|---|---|---|
| "오늘" 예약 4명 | `/s/[shopId]` | `bookings.where(date=today)` + `customers.lastVisit/serviceType` join |
| 손님 카드 모달 | `/s/[shopId]/customer/[id]` | `customers.byId` + `visits.where(customerId).orderBy(visitedAt desc)` |
| 메모 저장 → 토스트 | mutation `addVisit` | `visits.insert + customers.lastVisitAt update` |
| "예약 추가" 모달 | `/s/[shopId]/booking/new` | mutation `bookings.insert` |
| "알림" 탭 (예정/완료) | `/s/[shopId]/alim` | `alimtalk_log + bookings` join |

## 8. 모순 / Reach Gate 체크

- ❌ 모순 0건 (Clerk = dual-track, Stripe = Toss Payments 대체)
- ⭕ Reach Gate: 정수민 5분 = PIN 1회 + 손님 1명 등록 + 메모 1번. mock 자가검증 5개 통과.
- ⚠️ 자료 부족: Toss Payments Subscriptions API 정확 spec / 카카오 알림톡 검수 거절률 통계.

## 9. 다음 단계 (Phase 2.1 — 코드 시작 전)

- [ ] PLAN.md L68 "Phase 2 진입 조건" (가설 1 발품 검증)을 검증 모드(Lian 명시)로 우회 확인
- [ ] Convex 스키마 .ts 작성
- [ ] Toss Payments Subscriptions Perplexity 보강 1회 (자료 부족 해소)
- [ ] Solapi 템플릿 2종 카카오 검수 신청 (Lian 발품 시작점)
