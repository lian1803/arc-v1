# Portfolio Stubs 3개 (월요일 만들기)

> 비유: 면접 자기소개 = "이런 거 만들 수 있어요" 증명 3개.
> 시간: Claude Code 로 1-2시간 / stub.

## 3 stub 카테고리 (각 1개)

| # | 카테고리 | sample 결과물 | 시간 | 결과물 위치 |
|---|---|---|---|---|
| 1 | 자동화 | 네이버 블로그 자동 포스팅 (RSS → 네이버) | 1시간 | GitHub repo |
| 2 | 웹사이트 | 식당 5페이지 (메인/메뉴/오시는길/예약/연락) | 1.5시간 | Cloudflare Pages |
| 3 | 챗봇 | 카카오 i 챗봇 FAQ (자영업자 5 질문) | 1시간 | KakaoTalk 채널 또는 web demo |

---

## Stub 1. 자동화 sample

**제목**: "네이버 블로그 자동 포스팅 — RSS → 네이버 (1시간 작동)"

**Spec**
- 입력: RSS feed URL 1개 (예: 한 IT 블로그)
- 처리: 새 글 감지 → 요약 (3 문장) → 네이버 블로그 자동 등록
- 결과물: GitHub repo (Python script + README)
- README 에 "실행 시간 평균 1초 / 1포스트", "월 비용 0원" 박기

**Lian 실행 (Claude Code 1세션)**
1. \`mkdir -p portfolio_stubs/01_naver_auto_blog\`
2. Claude Code prompt: "Python 으로 RSS feed 읽고 네이버 블로그 자동 포스팅하는 스크립트 + README. 의존성: feedparser + selenium. 환경변수: RSS_URL, NAVER_ID, NAVER_PW."
3. 실제 실행 1번 + 캡처
4. GitHub repo 만들고 link

---

## Stub 2. 웹사이트 sample

**제목**: "식당 웹사이트 5페이지 — 평균 1주 인도 sample"

**Spec**
- 5 페이지: 메인 / 메뉴 / 오시는길 / 예약 / 연락
- 반응형 (PC/모바일)
- 예약 폼: Google Form 또는 자체 폼 → 메일 알림
- 결과물: Cloudflare Pages 배포 link

**Lian 실행**
1. Claude Code prompt: "식당 5페이지 Astro 또는 Next.js 정적 사이트. 디자인: 깔끔한 modern. 메뉴 페이지 = 음식 사진 placeholder + 가격. 예약 페이지 = formspree 연동 메일 알림."
2. 빌드 → Cloudflare Pages 배포 (free tier)
3. 도메인: \`restaurant-sample-2026.pages.dev\` 같은 subdomain
4. 캡처 + link

---

## Stub 3. 챗봇 sample

**제목**: "카카오 i 챗봇 FAQ — 자영업자 5 질문 자동 응답"

**Spec**
- 5 질문: "영업시간", "메뉴", "예약", "위치", "주차"
- 카카오 i 오픈빌더 또는 Web 챗봇 (간단)
- 결과물: 챗봇 link 또는 web demo URL

**Lian 실행 (간단 버전 = web demo)**
1. Claude Code prompt: "React + Tailwind 단일 페이지 챗봇. 5 질문 hard-coded 답변. 입력 → 매칭 → 답. 모르는 질문은 '직접 연락 주세요' + 전화번호 박기."
2. Cloudflare Pages 배포
3. 캡처 + link

**Advanced (옵션, 시간 되면)**
- 카카오 i 오픈빌더 챗봇 진짜 셋업 (필요 시 비즈니스 채널 가입)

---

## 산출물 link 박기

각 stub 완성 후 \`../../marketing/templates/wishket_profile.md\` 의 \`[PORTFOLIO_LINK_1/2/3]\` 변수 채우기.

## §5.1 라벨

- "1시간 / 1포스트" = Hypothesis (Lian 실측 후 verified 로 전환)
- "월 비용 0원" = verified (네이버 블로그 + GitHub Actions free tier)
- "1주 인도 sample" = Hypothesis (실 클라 인도 1건 후 verified)
