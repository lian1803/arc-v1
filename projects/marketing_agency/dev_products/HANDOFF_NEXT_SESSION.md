# dev_products — Next Session Handoff

**작성:** 2026-04-26 session 27 (Lian 사인)
**상태:** plan only, 새 세션 첫 명령어부터 즉시 실행 가능

---

## 결론 한 줄
개발 외주 사업 (`dev_products`) 0→1 진입. 위시켓/크몽 입찰 + 콜드 메일. 첫 12개월 보수 매출 = 4,200만 (월 350만, **Hypothesis**). 새 세션 시작 즉시 4 결정 → 첫 1주 액션.

---

## 새 세션 첫 명령어 (Lian 또는 서연)

```
1. cat projects/marketing_agency/dev_products/planning/entry_plan.md   # 전체 기획서 read
2. cat projects/marketing_agency/dev_products/HANDOFF_NEXT_SESSION.md  # 이 파일
3. Lian 4 결정 받기 (아래)
4. 첫 1주 액션 시작 (월요일부터)
```

---

## 4 결정 대기 (Lian sign 필요)

### 결정 1. 포지셔닝 (한 마디)
- 옵션 A: **Speed** — "위시켓 평균 4주 → 우리 1주" (실측 가능 시)
- 옵션 B: **Specialization** — 특정 영역 (카카오 OpenBuilder 챗봇 / 네이버 쇼핑 자동화 / Excel 매크로 자동화 등)
- 옵션 C: **Fixed Price** — "고정가, 견적 X" (입찰 시 차별화)
- 추천: A+B 하이브리드 (첫 3개월 Speed → 4-12개월 Specialization)

### 결정 2. 주간 입찰 강도
- 옵션 A: 월-금 매일 1건 (5건/주)
- 옵션 B: 월-수 집중 (15건/주)
- 옵션 C: 매일 5건 (25건/주, 이게 위시켓 최대)
- 추천: 첫 2주 = B (15건/주), 답장률 보고 조정

### 결정 3. 콜드 메일 lead 출처
- 옵션 A: 국세청 사업자등록 API 무료 + 이메일 패턴 추측
- 옵션 B: LinkedIn Sales Navigator 유료 (월 $99-449)
- 옵션 C: 한국 lead vendor 유료 DB 구매 (월 3-10만)
- 추천: A 무료 시작, 답장률 5% 미만이면 B 추가

### 결정 4. Scraping 리스크 허용도 (DOCTRINE §0 준수)
- 옵션 A: 합법 only (국세청 API + LinkedIn 합법 검색)
- 옵션 B: 약관 위반 OK (위시켓 입찰자 정보 / GitHub 프로필 / Naver 블로그 자동 모니터)
- 옵션 C: 개인정보 무차별 수집 OK (형사처벌 risk = §0 풀 surface)
- 추천: B (약관 위반 OK, 형사 risk = X) — DOCTRINE §0 정합

---

## 첫 1주 액션 (체크리스트)

### 월요일
- [ ] 위시켓 (`https://www.wishket.com`) 계정 만들기
- [ ] 크몽 (`https://kmong.com`) 계정 만들기
- [ ] 포트폴리오 stub 3개 (Claude Code 로 1시간 내 sample 결과물 — 자동화 / 웹사이트 / 챗봇)
- [ ] 위시켓 프로필 작성 (포지셔닝 결정 1 반영)

### 화요일
- [ ] 위시켓 첫 5건 입찰 (자동화 / 웹사이트 카테고리 필터)
- [ ] 크몽 상품 등록 5개 (정형 패키지: 자동화 1건 30만, 자동화 1건 80만, 자동화 1건 150만, 웹사이트 200만, 웹사이트 500만)
- [ ] Calendly (`https://calendly.com`) 계정 만들고 30분 미팅 link 박기

### 수요일
- [ ] 답장 모니터 + 미팅 잡기
- [ ] 위시켓 추가 5건 입찰
- [ ] 답장률 측정 (5건 중 N건)

### 목요일
- [ ] 첫 미팅 (있으면) → 견적 보내기
- [ ] 위시켓 추가 5건 입찰

### 금요일
- [ ] 첫 견적 → 계약 체결 시도
- [ ] 콜드 메일 셋업 (결정 3 옵션 따라):
  - A 옵션: 국세청 API 활용신청 (`https://www.data.go.kr` → 사업자등록정보 검색 → 활용신청)
  - 1-3일 키 발급 대기
- [ ] 한 주 답장률 / 입찰 성공률 / 매출 확정 stat 기록

### 다음 주 월요일 = checkpoint
- 첫 입찰 성공률 측정
- 결정 1 (포지셔닝) 검증 → 효과 없으면 옵션 변경

---

## 참고 (기획서 위치)

- **전체 기획서**: `projects/marketing_agency/dev_products/planning/entry_plan.md` (95줄)
- **바탕화면 사본**: `C:/Users/lian1/Desktop/개발외주_기획서_2026-04-26.md`
- **외부 검증 데이터**: `decisions/2026-04-26_session27_doctrine_§0_money-first.md` (외부 정론 인용)

---

## 주의사항 (DOCTRINE 준수)

- §0 Money-First: 합법성 차감 X. 형사 risk 만 풀 surface.
- §0.5 v2 Reporting Guideline: 모든 보고 4 룰 (결론부터 / 비유 복잡 로직만 / 기술 용어 괄호 / 결정 포인트 번호+리스크+리턴).
- §10 Pain-Anchored: 모든 기능 Pain 연결. "위시켓 평균 4주 인도 → 우리 1주" Pain = "고객이 빨리 받고 싶음".
- §15 Target-Reach Gate: ICP 도달 가능 도구 검증. 위시켓/크몽/콜드 메일 = 도달 가능.
- §5.1.1 voice-scrape: 첫 클라이언트 voice 박기 (계약 후 감사인사 / 후기 → 다음 세션 marketing 자료).

---

## 위험

1. **첫 2개월 입찰 답장률 5-10% 추정** — 낮으면 포지셔닝 (결정 1) 변경.
2. **클라이언트 커뮤니케이션 병목** — 솔로 = 답장 빨라야 함. Calendly + 메일 자동화 필수.
3. **프로젝트 overrun** — 견적 오버 시 마진 0 가능. 견적 시 buffer 30% 박기.
4. **scraping 약관 risk** — DOCTRINE §0 정합 (차감 X). 단 형사 risk (개인정보) 회피.

---

## Lian 첫 명령 예시 (다음 세션)

```
"개발사 시작. 결정 1 = A+B 하이브리드, 결정 2 = B (15건/주), 결정 3 = A (국세청), 결정 4 = B (약관 OK). 월요일부터 진행."
```

이 한 줄로 서연 = 첫 1주 액션 자동 진행.
