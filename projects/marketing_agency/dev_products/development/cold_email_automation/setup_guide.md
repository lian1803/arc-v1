# 콜드메일 자동화 setup (zero-signup, 산업 무관)

> dev_products (개발 외주 사업) lead 자동화. 신규 가입 0.
> 비유: Lian 집 가스/전기/마트 만 사용. 새 카드 0.

## 결론
가입 0. Lian 기존 Gmail (App Password 5분 setup) + ARC Anthropic API key. 산업 무관 — keyword 만 바꿔서 IT/마케팅/교육/의료 등 cover.

---

## 1. Gmail App Password (5분, 가입 X)

> 기존 Gmail 계정의 보안 설정. 새 계정 가입 X.
> 영업용 별 Gmail 1개 권장 (메인 정지 risk 회피).

### 단계
1. Gmail → 우상단 프로필 → "Google 계정 관리"
2. "보안" → "2단계 인증" ON
3. 보안 페이지 → "앱 비밀번호" → 앱 이름 "cold_email" → "만들기"
4. 16자 비번 복사 (한 번만 표시)
5. `.env` `SMTP_PASS` 에 paste (공백 제거)

---

## 2. Anthropic API key (ARC 기존)

ARC `.env` 에 `ANTHROPIC_API_KEY` 보유 중. cold_email_automation/.env 에 동일 paste.

---

## 3. .env 채우기

```bash
cd projects/marketing_agency/dev_products/development/cold_email_automation
cp .env.example .env
```

```
ANTHROPIC_API_KEY=sk-ant-api03-...           # ARC 기존
SMTP_USER=lian.dev@gmail.com                  # 영업용 별 Gmail (또는 메인)
SMTP_PASS=abcdefghijklmnop                    # App Password 16자 공백 제거
SENDER_EMAIL=lian.dev@gmail.com               # SMTP_USER 와 동일
OPT_OUT_REPLY_ADDRESS=lian.dev@gmail.com      # 회신 = 거부
```

---

## 4. 의존성 + dry-run

```bash
pip install -r requirements.txt

# 산업 무관 keyword 선택 — 첫주 = IT/마케팅 (홈피 보유율 높음 → 이메일 추출률 높음)
python orchestrator.py collect --keyword "백엔드 개발자" --limit 30 --out leads.jsonl

# 결과 확인 — 이메일 추출 N건 / 30건 = ?% (Hypothesis 30-50%)
head -5 leads.jsonl

# Compose
python orchestrator.py compose --leads leads.jsonl --out drafts.jsonl --industry-hint "IT 회사"

# Quality 확인 (5 draft read)
head -5 drafts.jsonl

# 첫날 5건 발송 (warmup Day 1)
python orchestrator.py send --drafts drafts.jsonl --max 5 --cadence

# 다음날 답장 분류
python orchestrator.py route_replies
```

---

## 5. Warmup 14일 ramp (Gmail 약관 회피)

| Day | Send N | 누적 |
|---|---|---|
| 1-3 | 5 | 15 |
| 4-7 | 10 | 55 |
| 8-14 | 20 | 195 |
| 15+ | 30 cap | 30/일 안정 |

§0 형사 risk + Gmail 약관 = 1일 30 hard cap (코드 박힘). 60-180초 랜덤 cadence 자동.

---

## 6. 산업 keyword 회전 (다양화)

### 첫 4주 (홈피 보유율 높은 산업 우선)
- 1주차: "백엔드 개발자" / "프론트엔드 개발자" (IT 회사)
- 2주차: "마케팅 매니저" / "퍼포먼스 마케터" (마케팅 대행사)
- 3주차: "강사 채용" / "교육 매니저" (학원)
- 4주차: "회계 사무직" / "세무 보조" (회계 사무소)

### 5주차+ 데이터 보고 산업 선택
- 답장률 높은 산업 = ramp
- 답장률 < 1% 산업 = drop

---

## 7. 운영 daily routine (Lian 5-15분)

1. 아침: `python orchestrator.py route_replies` (또는 cron)
2. interested / question = Slack / 메일 분류 → Lian 직접 답장
3. 저녁: `python orchestrator.py send --drafts drafts.jsonl --max 30 --cadence`
4. 주 1: 새 keyword collect

---

## 8. 위험 + 대응

| 위험 | 대응 |
|---|---|
| Gmail 정지 (자동발송 약관) | 1일 30 + 60-180초 랜덤 + 별 Gmail |
| 사람인 IP 차단 | 2초/요청 + 1일 30 회사 |
| 도메인 매칭 부정확 (40% sample) | 다양 keyword + Phase 2 사람인 detail page direct |
| 형사 risk | 사업자 공개 이메일 only + footer 회신=거부 |
| 첫주 답장률 < 1% | 산업 다양화 + 본문 변경 |

---

## 9. 외부 정론 (DOCTRINE_EXT §13)

- **Google Bulk Sender Guidelines (2024)**: 1일 ≤ 30 + opt-out + 자연 cadence 회피. 동의.
- **한국 정보통신망법 §50**: 영리 광고 메일 = 수신거부 + 발신자 식별. footer 자동.
- **Apollo.io warmup**: 14일 ramp. Gmail 자동.
- **반대 정론**: bulk-mailer 일부 (Mailshake) = 도메인 분리 권장. Phase 2 = 자체 도메인 fallback.
