# 개발사 첫 1주 playbook (Lian paste-ready)

> dev_products 0→1 진입. 4 결정 박힘 (A+B / B / A / B). 월요일부터 순서대로.
> 비유: 새 식당 첫 주 = 간판 → 메뉴판 → 입소문. 순서 깨면 첫 손님 0.

## 결정 4개 (Lian 사인 2026-04-27)

1. **포지셔닝 = A+B 하이브리드** — 첫 3개월 Speed (1주 인도, 자동화 한정), 4개월부터 Specialization
2. **입찰 강도 = B (15건/주)** — 첫 2주 측정 후 조정
3. **Lead 출처 = A 국세청 API** (무료) — 답장률 5% 미만 시 LinkedIn 추가
4. **Scraping risk = B (약관 위반 OK)** — 본 계정 lock 방어 위해 별 도구 분리. 형사 risk 회피.

---

## 월요일 — 간판 달기

### 1. 위시켓 가입 (10분, Lian 직접)
- URL: https://www.wishket.com/signup/
- 사업자등록번호 보유 시 입력 / 미보유 시 개인 계정으로 시작
- 프로필 = `../marketing/templates/wishket_profile.md` 본문 그대로 paste

### 2. 크몽 가입 (10분, Lian 직접)
- URL: https://kmong.com/register/
- 전문가 등록 → 카테고리 = "IT·프로그래밍"
- 프로필 = wishket_profile 같은 본문

### 3. 포트폴리오 stub 3개 (Claude Code 활용, 1-2시간)
- Spec: `../development/portfolio_stubs/INDEX.md`
- 자동화 / 웹사이트 / 챗봇 1개씩
- 결과물 = GitHub repo 또는 Cloudflare Pages link

### 4. 위시켓 프로필 등록 + 포트폴리오 link 3개 박기

---

## 화요일 — 메뉴판 인쇄

### 1. 위시켓 첫 5건 입찰 (1시간)
- 카테고리 필터: "IT·프로그래밍 → 자동화" + "웹사이트 개발"
- 입찰글 = `../marketing/templates/wishket_bid_templates.md` 변수 채우기 (2분/건)

### 2. 크몽 상품 등록 5개 (30분)
- `../marketing/templates/kmong_listings.md` 5개 그대로 등록
- 가격: 자동화 30/80/150만, 웹사이트 200/500만

### 3. Calendly 셋업 (10분, Lian 직접)
- URL: https://calendly.com/signup
- 30분 미팅 link "30분 디스커버리 콜"
- 미팅 link 위시켓/크몽 프로필 + 입찰글에 박기

---

## 수요일 — 모니터 + 추가 입찰

- 답장 모니터 (위시켓 메시지함 + 크몽 채팅)
- 위시켓 추가 5건 입찰 (총 10)
- 답장률 측정 첫 기록 (`kpi_log.jsonl` append)

---

## 목요일 — 첫 미팅 + 추가 입찰

- 답장 받은 의뢰사 미팅 잡기 (Calendly)
- 미팅 = 30분 (5분 인사 / 20분 의뢰내용 / 5분 견적 가이드)
- 견적 = 단가 + 납기 + 30% buffer
- 위시켓 추가 5건 입찰 (총 15건/주)

---

## 금요일 — 콜드 메일 셋업 + 마무리

### 1. 국세청 데이터 활용신청 (Lian 직접, 5-10분)
- URL: https://www.data.go.kr
- 검색: "사업자등록정보 진위확인 및 상태조회 서비스"
- 활용신청 → 1-3일 키 발급 대기

### 2. 첫 견적 → 계약 시도
- 미팅 의뢰사 답장 시 견적서 송부
- 계약 = 위시켓 자체 에스크로 사용 (안전)

### 3. 한 주 stat 기록 (`kpi_log.jsonl`)
- 입찰 = 15건 / 답장 N건 (rate %) / 미팅 N건 / 견적 N건 / 계약 N건 / 매출 ₩N

---

## 다음 주 월요일 = checkpoint

- 답장률 5% 미만 → 결정 1 포지셔닝 변경 또는 결정 3 LinkedIn 추가
- 답장률 10%+ → 결정 2 강도 25건/주 ramp

---

## 위험 + 대응

| 위험 | 대응 |
|---|---|
| 위시켓 계정 정지 (scraping 약관) | 본 계정 = 합법 입찰만, scraping 별 계정/도구 분리 |
| 1주 인도 약속 후 overrun | 1주 = 자동화 카테고리만, 200만+ 웹사이트 = "2-3주" 차등 |
| 개인정보보호법 형사 risk | scraping = 사업자명/공개 이메일 (info@/contact@) 까지만, 개인 010 무차별 금지 |
| 입찰글 quality 떨어짐 (15건/주) | 템플릿 변수만 채우기, 매번 새로 쓰지 않기 |

---

## 산출물 위치 (dev_products/)

- `planning/week1_playbook.md` — 이 파일 (1주 절차)
- `planning/entry_plan.md` — 0→1 기획서
- `marketing/templates/wishket_profile.md` — 위시켓/크몽 프로필 본문
- `marketing/templates/wishket_bid_templates.md` — 위시켓 입찰글 (자동화 + 웹사이트)
- `marketing/templates/kmong_listings.md` — 크몽 5 상품
- `marketing/templates/cold_email_templates.md` — 콜드메일 3안
- `development/portfolio_stubs/INDEX.md` — 포트폴리오 stub 3 spec

---

**Created**: 2026-04-27 session 29 (Seoyeon)
**Status**: Lian 4 결정 박힘. 월요일 액션 시작 가능.
