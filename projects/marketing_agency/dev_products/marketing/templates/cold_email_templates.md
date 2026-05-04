# 콜드 메일 템플릿 3안 (paste-ready)

> 사용 시점: 금요일 (국세청 API 키 발급 후) → 다음 주 월요일부터 매일 30개씩.
> 비유: 식당 전단지 — 짧고 (Read 30초), 한 가지 약속, 다음 행동 명확.
> §0 Money-First: scraping = 약관 위반 OK / 형사 risk 회피. lead = 사업자등록 공개 정보 + 이메일 패턴 추측 (info@ / contact@ / hello@).

## 템플릿 A. Short (직설)

**Subject**: [COMPANY_NAME] 자동화 30분 미팅

```
[NAME] 님,

[COMPANY_NAME] 의 [PAIN_GUESS] 자동화 가능합니다.
1주 내 작동 sample 보여드립니다.

30분 콜: [CALENDLY_LINK]

답장 안 주셔도 됩니다 — 이미 자동화하셨다면 무시 부탁드립니다.

[YOUR_NAME]
```

**변수**
- [NAME]: 사업자명 또는 "담당자"
- [COMPANY_NAME]: 공개 사업자명
- [PAIN_GUESS]: 산업별 (식당 = "예약·재고", 미용실 = "예약·고객 관리", 마케팅 = "보고서·캠페인")
- [CALENDLY_LINK]: 미팅 link
- [YOUR_NAME]: Lian

**적합**: 직원 1-10명 소상공인. 답장률 추정 1-3% (Hypothesis).

---

## 템플릿 B. Pain-first (medium)

**Subject**: [COMPANY_NAME] - [PAIN_KEYWORD] 매주 [HOURS]시간 → 0시간

```
[NAME] 님 안녕하세요.

[INDUSTRY] 사장님들 주에 평균 [HOURS]시간을 [PAIN_KEYWORD] 에 쓰는 것 같더라고요. (서울 [INDUSTRY] 사장님 [N] 분 인터뷰 결과)

이걸 자동화하면 0시간이 됩니다.

**비슷한 자동화 사례 (제 포트폴리오)**
- 케이스 1: [CASE_1_DESC] (납기 [DAYS]일, [PRICE]만원)
- 케이스 2: [CASE_2_DESC]

[COMPANY_NAME] 의 [PAIN_KEYWORD] 도 가능한지, 30분만 통화로 확인해 보시겠어요?

[CALENDLY_LINK]

답장 안 주셔도 무시하겠습니다. 다만 이미 다른 곳에서 견적 받으셨다면 가격만 비교해 보시는 것도 추천드립니다.

감사합니다.
[YOUR_NAME] / [PHONE]
```

**변수**
- [INDUSTRY]: 식당/미용실/마케팅대행 등
- [HOURS]: 산업별 (3-15시간 추정)
- [N]: 인터뷰 인원 (Lian 실제 인터뷰 후 채우기, 미진행 시 "여러" 사용)
- [CASE_1/2_DESC]: 포트폴리오 stub 설명

**적합**: 직원 10-50명. 답장률 추정 3-5% (Hypothesis).

---

## 템플릿 C. Reference-first (long)

**Subject**: [REFERENCE_COMPANY] 사례 — [COMPANY_NAME] 도 가능합니다

```
[NAME] 님,

[REFERENCE_COMPANY] ([INDUSTRY]) 의 [PAIN_KEYWORD] 자동화를 진행했습니다.

**Before**
- 담당자 1명이 매일 [HOURS]시간 [TASK_DESC]
- 월 인건비 [COST_BEFORE] 만원

**After (자동화 후)**
- 0시간 / 자동
- 월 인건비 [COST_AFTER] 만원
- ROI: [N] 개월 내 회수

**[COMPANY_NAME] 의 경우**
- [INDUSTRY] 이고 직원 [SIZE_GUESS] 명 규모로 보입니다
- [PAIN_GUESS] 가 비슷한 패턴이라면 1-2주 내 자동화 가능
- 견적 가이드: [PRICE_RANGE] 만원

**다음 단계**
30분 디스커버리 콜 → 24시간 내 견적서 송부.
[CALENDLY_LINK]

[REFERENCE_COMPANY] 사례 자료 (PDF) 도 콜 전에 미리 드립니다.

감사합니다.
[YOUR_NAME]
```

**변수**
- [REFERENCE_COMPANY]: 첫 클라이언트 받은 후 채우기 (사전 동의 필수, §5 Real-Data-Only)
- 첫 1개월 = 이 템플릿 사용 X (reference 0)
- 1-2개월차부터 = 첫 클라이언트 사례로 사용

**적합**: 직원 50-500명. 답장률 추정 5-10% (Hypothesis).

---

## Lead 출처 (결정 3 = A 국세청)

1. data.go.kr → "사업자등록정보 진위확인" 활용신청 (Lian 금요일 액션)
2. 키 발급 후 → ICP 산업코드 (예: 56 음식점업 / 96 개인서비스업) 로 사업자명 list
3. 이메일 패턴 추측: \`info@[domain].co.kr\`, \`contact@[domain].com\`, \`[ceo_name]@[domain]\` 등
4. bounce rate 추정 50-70% — 보낸 양 / 도달 양 = 보수 50% 가정

## Cadence

- 다음 주 월: 30개 송부
- 화-목: 30개씩 (답장 받은 곳 우선 응답)
- 금: 응답 stat 기록 (\`kpi_log.jsonl\`)

## 형사 risk 회피 (DOCTRINE §0)

- 사업자명 + 공개 이메일 (info@, contact@) = 약관 위반 risk만, 형사 risk 낮음
- **금지**: 개인 010 무차별 발송 (개인정보보호법 형사처벌 + 과태료 3,000만+)
- **금지**: 개인 비공개 이메일 (직원 이름 짐작 발송)
- 답장 받은 곳만 후속 — 무응답 30개 list = 7일 후 자동 삭제 (무차별 발송 방지)
