# Stripe Atlas — 글로벌 SaaS 인프라 정론 사례

출처: Perplexity 3쿼리 (2026-04-29). 주 1차 출처:
- atlas.stripe.com (간접, 한국 블로그 인용)
- plisio.net/ko/education/stripe-atlas (2024)
- velog.io/@y0u_many/Stripe-SaaS (구독 시스템 가이드)
- gotodeus.scomot.co.kr/getting-started-with-atlas/ (2024)
- mashupventures.co (글로벌 결제 솔루션 2024)

웹/앱: 🌐 거의 100% 웹. 앱 없음.

## ICP — 이 패턴 쓸 빌더
글로벌 SaaS 운영 솔로 founder 또는 N개 사업 굴리는 사람. $500 가입비 가능 + 한국 founder 가입 가능 (현지 방문 X). Lian이 ARC로 굴리는 N개 사업 중 글로벌 타겟인 것에 차용. 한국 자영업자 SaaS(정수민)는 차용 X — Toss Payments가 더 정합.

## 1. 가입 흐름 (글로벌 KYC) 🌐
1. atlas.stripe.com 등록 → 회사 이름/사업 주소(미국 X 가능)/창업자/주주/지분/제품 입력. **글로벌 KYC** 동시 진행.
2. 초대 received → 공동 창업자 정보 + 문서 서명 (1-2주).
3. **Delaware C-Corp 또는 LLC 등록** (Stripe 자동, 등록 대리인 설정).
4. **EIN 발급**: IRS SS-4 자동 제출. 이메일 2주 / 우편 6-8주.
5. **은행 계좌**: Mercury 등 제휴 (Silicon Valley Bank 과거). 미국 전화번호 (Mintmobile 등) 필요. 1-2주.
6. 주식 발행 + 83(b) election 제출 + 사후 체크리스트 (직원/규정).
7. **Stripe 계정 연결** → 결제 처리 시작 + perks ($50,000+ 크레딧).
**가격**: 일회성 $500 (2024 plisio.net 기준). 연회비 무료 (등록 대리인 사후 갱신 별도).
**전체 소요**: 1-2주 (EIN 우편 제외).

## 2. 결제 / 구독 흐름 🌐
**기본 흐름**: 카드 입력 → PaymentIntent 생성 → 처리 → Webhook (서버 비동기). 카드는 토큰화로 기업 서버 미저장.
**Subscriptions 표준 패턴** (3단계, velog 인용):
```python
customer = stripe.Customer.create(email='x@x.com', payment_method=pm_id, ...)
subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[{'price': 'price_1ABC...'}],
    trial_period_days=14)  # 트라이얼 14일, 종료 후 자동 갱신
```
**Customer Portal** (셀프 관리 = 구독 취소/카드 변경/청구서):
```python
session = stripe.billing_portal.Session.create(
    customer=customer_id, return_url='https://yoursite.com/account')
# session.url 리다이렉트
```
**Webhook 주요 이벤트**: `customer.subscription.{created,updated,deleted}`, `invoice.payment_{succeeded,failed}`.
**구현 시간/코드량** (nxcode 2026 + 일반 가이드):
- Checkout 기본: 2-4h, 50-100 LOC
- 정기결제: 4-8h, 100-200 LOC
- Customer Portal: 1-2h, 20-50 LOC
- 전체 production-ready: 2-4주, 300-500 LOC
**가격** (Stripe 자체): 유럽 카드 1.5% + €0.25부터. 한국 [자료 부족].

## 3. Carry-over 패턴 (정수민 다음 사업 / Lian N개 사업 관점)
**한 번 셋업 후 영구 재사용 elements** (plisio 2024):
- **Delaware C-Corp/LLC + EIN** = 1번 발급, 여러 사업 운영 가능 (별도 새 법인 X)
- **Mercury 은행 계좌** = 모든 사업 거래 통합 관리
- **Stripe 계정** = multiple products 지원 (SaaS + 구독 + 마켓플레이스 동시)
- **Customer ID 재사용** = 사업 간 크로스셀/업셀
- **$50,000+ Stripe 크레딧** = 초기 결제 비용 흡수
- 주식 계약 + 법률 템플릿 + 글로벌 결제 인프라
**Lian 관점 가치**: 솔로 + N개 사업 = $500 한 번이면 인프라 base 영구 확보. 새 사업마다 재설립 비용 X.
**Idempotency-Key**: 모든 POST에 헤더 추가 → 재시도 시 첫 결과 반환. 업계 표준 (ttj.kr 2024). ARC v2 sub-agent 호출에 동형 차용 가능.

## 가격 / 채널 / 결과
- 가격: 가입 $500. 결제 수수료 1.5% + €0.25 (EU). API 무료.
- 채널: stripe.com/atlas 직접. 한국 founder 대상 인용 블로그 다수.
- 결과: Stripe Atlas 누적 가입자 수 / 졸업 사업 수 [자료 부족 — 공식 통계 미공개]

## ARC v2 차용 후보 (5)
1. **Stripe Atlas = Lian N개 사업 글로벌 인프라 base** — ARC v2 정신("Lian이 사업 N개 굴릴 때 쓰는 인프라")과 정확 매칭. **단 글로벌 SaaS 한정**, 한국 자영업자 대상 SaaS는 X.
2. **정수민 SaaS는 Stripe X → Toss Payments** — 한국 KRW, 한국 카드, 한국어 영수증. Stripe는 글로벌. test_run_001 architecture에서 Toss Payments 명시 차용 권장.
3. **Subscriptions 패턴 (Customer + Subscription + trial_period_days + Portal + Webhook)** — Toss Payments에서 동일 패턴. PLAN.md "월 19,000원 + 첫 1년 무료" → trial_period_days=365 정확 매핑.
4. **Customer Portal = 정수민 셀프 관리** — 정수민 본인이 카드 변경/취소 직접. 별도 페이지 X. Toss Payments 동일 기능 [추가 조사 필요].
5. **Idempotency-Key** = ARC v2 sub-agent 재시도 시 동형 패턴. 멱등성 보장 → 부작용 방지.

## 자료 부족
- 한국 founder 외환 거래 규정 detail + 미국 전화번호/주소 확보 방법
- 2025-2026 Stripe Atlas 최신 업데이트
- Toss Payments vs Stripe 한국 가격/수수료 정밀 비교
- Stripe Connect (마켓플레이스) 한국 사용 사례
- 누적 Atlas 가입자/졸업 사업 통계
