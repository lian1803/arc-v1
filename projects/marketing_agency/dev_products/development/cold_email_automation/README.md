# Cold Email Automation (zero-signup, 산업 무관)

> dev_products (개발 외주 사업) lead 자동화. 신규 가입 0 — Lian 기존 Gmail + ARC Anthropic API.

## 한 줄
사람인 채용공고 검색 (산업 무관) → 회사명 → 도메인 → 이메일 추출 → Claude 가 한국어 메일 → Gmail SMTP 발송 (1일 30 cap, 60-180초 랜덤) → IMAP 답장 분류.

## ICP (산업 무관)
**반복 업무 많은 + 개발 인력 없는 SMB.** 산업 한정 X.
- 채용 keyword 만 바꾸면 cover: "백엔드 개발자" / "마케팅 매니저" / "강사 채용" / "회계 사무직" / "물류 관리" / "관리자" 등.
- 메일 채널 reach 가능한 곳 = 홈페이지 보유 SMB (실측: IT/마케팅/교육/회계/의료 = 50-95% / 자영업자 미용실·식당 = ~0%).
- 자영업자는 sales_offline sub-project 영역 (다른 채널 = 카톡/SMS).

## 폴더 구조

```
cold_email_automation/
├── collect_via_saramin.py  — 사람인 → 회사명 → naver 검색 → 도메인 → 이메일
├── email_guesser.py        — 도메인 → 홈피 fetch + DNS MX (재사용 컴포넌트)
├── composer.py             — Claude Sonnet 4.6 → 한국어 메일 (산업 무관 Pain catalog)
├── sender.py               — Gmail SMTP + 1일 30 cap + 정통법 footer
├── reply_router.py         — IMAP → Claude Haiku 4.5 분류 → opt-out / Slack
├── orchestrator.py         — CLI: collect/compose/send/route_replies
├── setup_guide.md          — 5분 setup
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore              — runtime artifacts
```

## Quick start (5분)

1. Gmail App Password 발급 (`setup_guide.md §1`)
2. `pip install -r requirements.txt`
3. `cp .env.example .env` + 키 paste
4. `python orchestrator.py collect --keyword "백엔드 개발자" --limit 30`
5. `python orchestrator.py compose --leads leads.jsonl --out drafts.jsonl --industry-hint "IT 회사"`
6. `python orchestrator.py send --drafts drafts.jsonl --max 5 --cadence` (warmup Day 1)
7. `python orchestrator.py route_replies`

## Keyword 예시 (산업별)

| 산업 | keyword 예시 | 홈피 보유율 추정 |
|---|---|---|
| IT / SaaS | "백엔드 개발자", "프론트엔드", "DevOps" | 95%+ |
| 마케팅 대행사 | "마케팅 매니저", "퍼포먼스 마케터" | 90%+ |
| 교육 / 학원 | "강사 채용", "교육 매니저", "교무" | 60-80% |
| 회계 / 세무 / 법률 | "회계 사무직", "세무 보조", "법무 비서" | 60-80% |
| 의료 | "원무 직원", "간호조무사" | 50-70% |
| 부동산 | "공인중개사 보조", "부동산 사무직" | 50-70% |
| 제조 / 유통 | "물류 관리", "구매 사무직", "QC 관리자" | 40-70% |
| 일반 사무 | "사무직", "관리자", "총무 보조" | 다양 |

## DOCTRINE 정합

- **§0 Money-First**: 사업자 공개 이메일 only (홈피 박힌 info@/contact@). 010/개인 X.
- **§2 No-Silent-Fail**: 네트워크/SMTP raise. 한도 초과 raise.
- **§4 Delegate-by-Default**: 5 모듈 독립.
- **§5 Real-Data-Only**: 회사명/홈피 = scraped (verified). Pain = "추정" 라벨.
- **§9 Size-Cap**: 모든 .py < 230 LOC (300 cap 내).
- **§10 Pain-Anchored**: 산업 무관 — 반복 업무 자동화 Pain 직결.

## 비용 (월)

| 항목 | 비용 |
|---|---|
| 사람인 검색 + 네이버 검색 + 홈피 fetch | 무료 |
| Claude API (월 900 메일 + 답장) | $5-15 |
| Gmail SMTP (월 900 메일) | 무료 (Lian 기존) |
| **합계** | **$5-15/월** |

vs Apollo.io ($99-149) / Instantly ($37-97) — 가입 0 + 비용 1/10 + 한국 lead 정합.

## 실측 (5 sample, 백엔드 개발자 키워드)

- 회사명 추출: 5/5 (100%)
- 홈페이지 매칭: 5/5 (네이버 검색 첫 외부 도메인)
- 이메일 추출: 2/5 (40%) — sankun.com, ideatec.co.kr
- compose 결과 Claude Sonnet 4.6 한국어 quality OK

## 위험

| 위험 | 대응 |
|---|---|
| Gmail 자동발송 정지 | 1일 30 + 60-180초 랜덤 + 별 Gmail (메인 분리 권장) |
| 사람인 IP 차단 | 2초/요청 + 1일 30 회사 |
| 도메인 매칭 부정확 (40% rate) | Phase 2 = 회사명 → 사람인 detail page 직접 fetch (홈피 link 더 정확) |
| 형사 risk | 사업자 공개 이메일 only + 정통법 footer (회신=거부) |

## Phase 2 (warmup 14일 후)

- 사람인 회사 detail page 직접 fetch → 홈피 link 정확도 ↑
- 잡코리아 / 원티드 multi-source
- 자체 도메인 메일 (Gmail 정지 fallback)
