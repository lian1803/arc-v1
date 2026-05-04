# OnboardingHub — Claude Code SaaS 빌드 패턴

출처: https://world.hey.com/cpinto/building-a-complete-saas-product-with-only-claude-code-cca13895 (Celso Pinto, 2026-02-08)

## ICP — 진짜 사용자 1명 (이 패턴 쓸 빌더)
- Celso Pinto (확정 인물). 2x founder (Pixie / SimpleTax). 본문 자칭 "solo developer product-minded founder with AI co-authorship".
- 작업 시간: 다른 잡 하면서 저녁 "a couple of hours"씩 8주.
- 사업 자체 = 멀티 테넌트 Rails SaaS — workspace + 온보딩 가이드 + 진행 추적 + 팀 관리.
- Lian과 동형: 1인 N개 사업 굴리는 솔로 founder 패턴 (사례 차용 의도).

## Pain — Top 3 (솔로 founder가 풀스택 SaaS 빌드 시)
1. 시간 부족 — AI 없이 풀스택 SaaS ≈ 800h. 솔로 + 사이드잡 = 사실상 불가능 (저자 본문 "~800 hours without AI" 역산).
2. AI 코딩 통제 안 하면 컨벤션/품질 드리프트 → 솔루션 = DHH-style review skill 강제.
3. 병렬 AI 세션 환경 충돌 → 솔루션 = 티켓당 격리 환경 (격리 DB + worktree + server).

## Solution — Celso의 워크플로우 (= 추출 핵심)
- **Architecture-first**: 코드 전 architecture.md 먼저. (= ARC PLAN.md 동형)
- **CLAUDE.md = "Agent Operating Manual"** — Linear 티켓, 격리 환경, Playwright 테스트, DHH-style review, 커밋 컨벤션 박음.
- **모듈러 skill 5개**: `/isolated-environment`, `/ticket-lifecycle`, `/ui-ux-review`, `/qa-testing`, `/dhh-review`.
- **`/dhh-review`** = Rails 컨벤션 강제, "APPROVED" 명시 verdict 받아야 commit. (= ARC v2 Reach Gate 동형 패턴)
- **티켓당 격리 dev instance** (격리 DB + 격리 worktree + 격리 server).
- **병렬 Claude 세션** + batch merging (assembly line). 사람 = "95%+ AI 자율 코딩, 사람은 product 결정 + 리뷰".

## 스택 (본문 인용)
Rails 8.1.1 / Hotwire (Turbo+Stimulus) / Tailwind v4 + ShadCN / PostgreSQL (SQLite 마이그) / Solid Queue/Cache/Cable / Cloudflare R2 / Stripe / Heroku (Kamal에서 피봇) / Playwright + Rails system tests + SimpleCov 85% / Honeybadger / Pundit (13 정책) / Sitepress (마케팅+docs). AI = Claude Opus 4.5 (메인) → 4.6 (polish).

## 가격 모델
- OnboardingHub 자체: Stripe 구독 + trial (실 활성). 가격 숫자는 본문 미명시 — [자료 부족 — 추가 조사 필요].
- Claude API 누적 비용: 본문 미명시 — [자료 부족 — 추가 조사 필요].

## 채널 — 어떻게 알려졌나
- onboarding-hub.com 라이브 (Heroku).
- 본 hey.com 블로그 글 자체 = 출시 채널 (founder/dev 커뮤니티 도달).
- 마케팅 채널 detail은 본문 미명시 — [자료 부족 — 추가 조사 필요].

## 결과 (숫자, 본문 인용)
- 기간: 2025-12-15 → 2026-02-08 (~8주, 55 calendar days)
- 커밋: 727 (브랜치 합 713), 40 days with commits, 피크 일 = 2/3 (71 commits)
- 코드: **38,632 LOC** (657 src files), ~89,600 LOC with tests
- 사람 시간: **25–45h** (저자 추정 "more likely 2 weeks of full-time effort")
- AI 없이 추정: ~800h → **20–30x leverage**
- 테스트: 86+ test files, 53+ policy tests, SimpleCov 85%
- 문서: 29 페이지 docs site
- Production fire (2/3-4): Solid Queue connection pool 과소, Heroku 512MB dyno 부족, R2 ActiveStorage checksum 충돌, async job silent fail.

## 핵심 학습 (Lian이 차용 가능한 패턴)
1. **CLAUDE.md = Operating Manual + 모듈 skill 분리**. Celso 5개 skill = 격리환경/티켓라이프사이클/UI리뷰/QA/DHH리뷰. ARC v2 현 CLAUDE.md (40줄 cap)에 skill 분리 추가 검토 가능.
2. **Architecture-first → PLAN.md 동형**. ARC v2 Phase 1이 이미 PLAN.md 강제 = 같은 결.
3. **병렬 격리 환경** — sub-agent 병렬 시 격리 DB+worktree. ARC v2 Phase 2 sub-agent 호출 시 차용 가능.
4. **강제 verdict 게이트** (`/dhh-review` "APPROVED" 받아야 commit) = ARC v2 Reach Gate ("ICP 5분 안 쓸 수 있나? NO면 진행 X")와 같은 패턴 — 이미 박힘 ⭕.
5. **솔로 + AI = 20-30x leverage** = ARC ("Lian 1인 N개 사업" 인프라) 정당화 데이터 포인트. 단 production fire 4건 = 자율 빌드의 한계 (DOCTRINE §12 Pre-Launch Reality Test 동형 페인 — ARC v2도 같은 가드 필요).

## 자료 부족 항목 리스트
- OnboardingHub 가격 (Stripe 구독 가격 X)
- 사용자 수 / MAU / 매출
- 마케팅 채널 detail
- Claude API 누적 비용
