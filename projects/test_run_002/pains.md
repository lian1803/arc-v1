# test_run_002 — Pain 후보 5개

검색일 2026-04-29. Perplexity 5쿼리. ARC v2 "발명 0건" 룰 적용.

**출처 신뢰도 주의**:
- P5 응답에 reddit/X URL과 quote가 fabricate된 정황 (citations 비어있음, URL 패턴 의심) → 카테고리만 채택, quote 인용 X.
- P1 (indie hacker launch) 응답이 "구체 사례 못 잡음" 자체 명시 → 후보 제외.
- 5개 채우기 위해 P2(HN)에서 2개 후보 추출.

## 후보 1: Code Navigation Visualizer
- **누가 (ICP)**: Linux 커널/오픈소스 코드 읽는 영어권 개발자
- **페인 (구체)**: VSCode "Peek Definition" 같은 기능을 더 시각적으로, Source Insight처럼 무료 + Linux에서 쓰고 싶음. "I have found some parts of the kernel, e.g. the file system to be convoluted, and I need to follow quite a few jumps to form the system mindset."
- **현재 해결**: VSCode Peek Definition (시각화 약함) / Source Insight (유료, Linux 미지원)
- **"오늘 런칭 가능한 도구 1개" 가설**: GitHub repo URL 붙여넣기 → 함수/심볼 누르면 정의 + 호출 트리 시각화 (단일 페이지 web tool, 회원가입 X)
- **출처**: news.ycombinator.com/item?id=46345827 (HN, 2026)

## 후보 2: AI Screen Activity Summarizer
- **누가 (ICP)**: 노트북에서 일하는 영어권 솔로 워커 (개발자/지식노동자)
- **페인 (구체)**: 하루 종일 한 일 추적 + AI 질의. "A local screen recording app but it uses local models to create detailed semantic summaries of what I'm doing each day on my computer. ... I want to ask things like 'Who did I forget to respond to yesterday?'"
- **현재 해결**: Rewind ("I've been using Rewind for a year now, and it's nowhere near as useful as it should be.")
- **"오늘 런칭 가능한 도구 1개" 가설**: 로컬 모델 의존 = 오늘 1일 안 X. **단순화 옵션**: Gmail OAuth만 받아서 "어제 받았는데 답장 안 한 메일 5개" 1페이지 표시 (스크린 녹화 X)
- **출처**: news.ycombinator.com/item?id=45421812 (HN, 2025)

## 후보 3: Invoice Auto-Follow-up
- **누가 (ICP)**: 영어권 솔로 프리랜서/1인 컨설턴트 (월 매출 $3k-$15k)
- **페인 (구체)**: 미수금 추적/리마인드 매주 반복 + 스트레스. "One of the biggest frustrations freelancers face is waiting on overdue invoices. It's easy to start questioning whether you did something wrong."
- **현재 해결**: 수동 이메일 reminder, 일부 자동화는 Stripe/Wave 등 풀 invoicing 도구 안에 묶임
- **"오늘 런칭 가능한 도구 1개" 가설**: 인보이스 PDF 업로드 + 클라이언트 이메일 입력 → D+7 / D+14 / D+21 자동 follow-up 이메일 발송 (Gmail OAuth만, 무료)
- **출처**: 4thecreatives.com/the-most-frustrating-parts-of-freelancing (블로그) + plutio.com/blog/9-things-freelancers-can-do-to-automate

## 후보 4: One-shot SEO Meta Description Generator
- **누가 (ICP)**: 영어권 1인 SEO/마케팅 운영자, 블로그/이커머스 운영자 (월 100+ 페이지 운영)
- **페인 (구체)**: 페이지마다 meta description 다시 쓰기. on-page SEO가 솔로 작업 시간 28% 차지 (nytroseo.com 통계). "Manual data validation is time-consuming"
- **현재 해결**: 수동 작성 / ChatGPT에 페이지 내용 복사 + prompt
- **"오늘 런칭 가능한 도구 1개" 가설**: URL 입력 → 페이지 fetch → 5개 meta description 후보 (155자 이내, 키워드 포함) 즉시 출력 (회원가입 X, 무료, GPT API 키는 백엔드)
- **출처**: nytroseo.com/seo-tasks-that-takes-most-of-the-time + cognitiveseo.com/blog/12703/seo-tasks

## 후보 5: CSS-to-Tailwind Converter (with edge cases)
- **누가 (ICP)**: 영어권 솔로 frontend dev, vanilla CSS/Bootstrap → Tailwind 마이그하는 1인 개발자
- **페인 (구체)**: 기존 도구들 80% 변환 가능, edge case (custom selector, complex media query, calc() 등)에서 손 봐야 함. **카테고리 인정** (일반적 dev 페인) — 단 P5 응답의 구체 quote는 검증 실패로 인용 X
- **현재 해결**: tailwindcomponents.com 변환기, ChatGPT
- **"오늘 런칭 가능한 도구 1개" 가설**: CSS paste → Tailwind 변환 + edge case 시 inline @apply 자동 fallback + diff view (회원가입 X, 무료, 클라이언트사이드 only)
- **출처**: [Perplexity P5 카테고리 — 구체 quote 검증 실패, 카테고리만 채택]

---

## 다음 단계
Lian이 1개 고름 → projects/test_run_002/PLAN.md 진입.
