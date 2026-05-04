# perplexity 메타 검색 — AI 빌드 갭 (5쿼리)

date: 2026-05-03
source: Perplexity sonar-pro 5쿼리 (Lian 지시)
status: 변환 재료. 매뉴얼화 X. ARC 정합 부분만 발췌 적용. 원본은 `.tmp_pplx_out_meta/` 5개 파일.
배경: core/luna/ARC 셋이 공통으로 못 푼 문제 — "기획은 잘하는데 실 빌드에서 비개발자 ICP에게 끝까지 매끄러운 웹앱 X". Lian 시도("실제 웹 설계도 배워오기")가 정답인지 외부 정론으로 검증.

---

## 핵심 발견 (BLUF)

1. **사용자 시도("reference-driven UX 학습")는 부분 정답.** WebArena 벤치마크: 표면 시각 70% / 기능 UX **<40%** 전이 (Q2). Anthropic 공식 인정: "vision strong on visuals, weak on latent logic." 사례 학습만으로는 절대 안 풀림.
2. **이건 ARC 고유 실패 X = 산업 전체 미해결 문제.** AI PR이 일반 대비 **75% 더 많은 logic 오류** (Stack Overflow 2026.1), 1.9M row DB 삭제 사고 (Replit Agent 추정, FOX 보도) (Q1). core/luna가 못 푼 자리 = 시장 전체가 못 푼 자리.
3. **시장에 "비개발자용 end-to-end 작동 + 결제 작동 + 자유 launch"의 postmortem 사례 0건** (Q5). 즉 ARC가 풀면 사업 자체가 됨.
4. **빠진 축 = ICP-loop 자동 검증.** Anthropic Computer Use 41%, Browser-Use 64%, Harness 86% (real web tasks). 정형 framework 아직 시장 미정착 (Q3) = ARC가 직접 만드는 게 차별화.
5. **2025-2026 도구들 (Lovable/v0/Bolt/Cursor)도 prototype 단계까지만**. Bubble/Taskade Genesis가 end-to-end에 가장 가깝지만 drag-drop 학습곡선 (Q4).

---

## Q1 — AI 빌드 도구 실패 패턴 + 산업 해결법

### 실패 패턴 (수치 + 사고)

| 수치/사고 | 출처 | 날짜 |
|---|---|---|
| AI PR 75% 더 많은 logic/correctness 오류 (194/100 PRs) | Stack Overflow Blog | 2026-01-28 |
| AI 코드 1.5-2x 보안 버그, 8x 과도 I/O (모바일 슬로우다운) | 동일 | 2026-01-28 |
| Replit Agent 추정 production DB 1.9M row 삭제, 백업도 함께 wipe | YouTube + FOX 보도 | 2026 초 |
| 17% PR fail = CI/test 깨짐, 모바일 edge case 무시 (bug-fix PR merge율 가장 낮음) | arXiv 2601.15195 "Where Do AI Coding Agents Fail" | 2026-01 |
| v0 생성 앱에서 browser-side 토큰 도난 → API key end-user 노출 → 결제 손상 | Penligent | 2026 |

### 4가지 실패 모드
1. **회원가입/결제 무한 루프, silent failure** — 모바일 입력 미처리, 세션 timeout 미처리
2. **개발자용 UX를 비개발자에게 박음** — env var 노출, CLI 강요, API key 화면 노출
3. **보안/성능/동시성 production 문제** — 부적절 password handling, 결제 루프 동시성
4. **Generalist blind spot** — 큰 컨텍스트 가진 1개 거대 에이전트가 모든 영역 동시 처리 시 깊이 X

### 산업 해결법 (정론)

- **(1) 전문 에이전트 분리 + 사용자 프로파일 prompt** ("mobile-only, no CLI"). YouTube "Why Your AI Coding Agent Will Fail in Production" (2026): "Generalist Blind Spot 회피 — 모바일 UX / 결제 등 좁은 specialist 사용".
- **(2) Real-user simulator 통합** (Playwright 등 모바일 path 자동 클릭). arXiv 2026.1: 사용자 fit 체크 통과 PR만 merge.
- **(3) User-fit oracle 체크리스트** — Lovable/Bolt가 2025 후 update에 prompt-enforced 체크 추가: "no API keys visible / mobile-first". Substack 2026: 80% fix rate.
- **(4) Defensive coding + human review** — Stack Overflow: AI는 error handling 2x 잘함. 다만 logic 오류는 human이 user path 직접 trace 필수.

---

## Q2 — Reference-driven (실제 웹 학습/모방) 접근의 실제 효과

### 결론: **표면 70% / 기능 UX <40%** (WebArena 벤치마크)

> "AI primarily transfers SURFACE visuals (layouts, styles, components) but rarely underlying UX patterns like adaptive journeys, decision boundaries, or cross-channel consistency."

### 도구별 구현
| 도구 | 메커니즘 | 평가 |
|---|---|---|
| v0 (Vercel) | 스크린샷/이미지 → React/Tailwind | 시각 잘 mimic, UX 흐름은 수동 보정 |
| Lovable | Multi-agent: 비주얼 → Figma-like spec → 코드 | "shallow clones" — 60%+ 산출물 retention 위해 rework |
| Bolt.new | Stacks (사전학습 UI 키트) | "pretty but broken" (YouTube teardown 2026) |
| Galileo AI | 스케치/스크린샷 → 디자인/코드 | enterprise 시도 후 end-to-end mismatch로 **abandoned** |
| Builder.io Visual Copilot | 라이브 사이트에서 컴포넌트 추출 | 컴포넌트 수준만 |
| Anthropic Claude vision | 스크린샷 분석 → 코드 | 공식: "Vision strong on visuals, weak on latent logic" |

### 한계 4가지
1. **Visual bias**: 픽셀은 베끼지만 의도(왜 이 흐름이 churn 줄이는지) 못 베낌
2. **No true learning**: behavioral data transfer 없음, static screen만
3. **Scalability**: design system → "experience system" 진화 못 따라감, accessibility 누락
4. **Dark patterns**: 윤리 reasoning 없이 setn persuasion 패턴 amplify

### Anthropic/OpenAI 공식 가이드
- **Anthropic (Claude 2025)**: "reference-driven prompting" 권장하되 vision → reasoning chain 필수
- **OpenAI (GPT-4o 2024)**: "use references for vibe inspiration; iterate with user testing as AI hallucinates interactions"

### 2026 UX 패널 결론
> "AI replaces screens, not designers" — 속도 2x, 품질은 oversight 없이는 떨어짐.

---

## Q3 — ICP-loop 자동 검증 (페르소나가 빌드 결과 직접 사용)

### 시장 상태: **정형 framework 아직 미정착** (perplexity 자체 명시)

벤치마크 (Harness 비교, real-world web tasks):
| 도구 | 성공률 |
|---|---|
| Harness AI Test Automation | 86% |
| Browser-Use | 64% |
| OpenAI Operator | 45% |
| Anthropic Computer Use | 41% |

### 발견된 도구
- **Playwright agents** — 자동화 testing framework
- **Browser-Use** — open source AI 브라우저 자동화
- **Anthropic Computer Use API** (Claude) — vision 기반 GUI 조작
- **Mabl, Testomat, QAWolf** — AI E2E 테스팅 SaaS

### 효과
- "Contextual awareness" — 진짜 UI 변화 vs 렌더링 차이 구분 가능
- "Autonomous test exploration" — 새 path 동적 발견, 빠르게 변하는 앱에서 버그 발견
- Behavior-based testing — clickstream/analytics 데이터로 실 사용 패턴 시뮬

### 핵심 갭
> "persona-driven E2E testing with vision feedback inside agent loops appears to be actively developed but **not yet comprehensively published in accessible benchmark papers or tool documentation**"

= **ARC가 직접 발명할 자리.** 시장 정답 없음.

---

## Q4 — 2025-2026 AI 빌드 도구 비교 (end-to-end 작동 axis)

### 결론: **진짜 end-to-end (비개발자 + 결제 + 일상 user journey 작동) 도구 거의 없음**

| 도구 | 메커니즘 | 약점 | 비개발자 launch 사례 |
|---|---|---|---|
| Lovable | TS/React + DB + auth + deploy 풀생성 | 결제/no-key 보안 위해 dev tweak 필요 | 없음 (postmortem 0) |
| v0 Vercel | Next.js + 1-click Vercel deploy | 개발자 지향, payments/auth 수동 config | 없음 |
| Bolt.new | WebContainer (브라우저 내) zero-setup | prototype tier만 | 없음 (투자자 데모만) |
| Replit Agent | Full-stack + DB + hosting + auth | 복잡 결제 안 됨 | 없음 |
| Cursor (agent) | 코드베이스 인식 IDE | 코딩 스킬 필수 | 비개발자 X |
| Claude Code (subagents) | 미상세 | — | 없음 |
| Devin | 미상세 | — | 없음 |
| Windsurf | UI-rich React | 코드 출력 | 없음 |
| **Bubble** (기존 베테랑) | Visual no-code, AI starter, 결제/DB/auth | drag-drop 학습 곡선 | **있음** (multi-sided 앱, 결제) |
| **Taskade Genesis** (2026 신규) | 즉시 deploy, agent + DB + automation | 복잡 결제 미검증 | **150,000+ 앱 deploy 주장** |
| Knack | prompt → CRM/portal | 결제/journey 수동 보정 | CRM/dashboard 사례 (결제 X) |

### 핵심 인사이트
- "Living Software Platforms" (Taskade Genesis, Bubble) = end-to-end에 가장 가까움
- 코드 생성 도구 (Lovable, v0, Bolt, Cursor) = prototype 강점, 비개발자 끝까지 X
- **결제 작동 비개발자 launch의 postmortem 0건** (모든 도구 공통) = 시장 갭

---

## Q5 — 실 성공 사례 (비개발자 ICP 도달)

### 결론: **조건 다 맞는 case study 0건** (perplexity 자체 명시)

발견된 비스무리 사례:
- **Bubble AI App Generator**: 데이터 모델/UI/워크플로우 자연어 생성. end-user traction 사례 없음.
- **Lovable**: 비개발자 founder 대상 풀 웹앱. 사용자 테스트/실패/지표 보고 없음.
- **Glide**: 스프레드시트 → 모바일 앱. field team/sales rep 대상. 2024-2026 case study 없음.
- **FlutterFlow**: Flutter 앱. **enterprise 사용자 300% 증가** 보고. end-user fit 디테일 없음.

### 일반 트렌드 (벤치마크 X, 단순 통계)
- "80% digital products는 non-developer가 만듦" (Elementor 통계)
- Elementor가 글로벌 웹사이트 13% 점유

### 시사점
**"비개발자 + 결제 + 매끄러운 daily journey"의 공개 success postmortem 자체가 시장에 없음** = ARC가 풀면 그 자체가 사업 + PR 자산.

---

## ARC 정합성 평가 (Lian용)

### 이미 ARC에 박혀 있는 것 (~50%)
- 사례 학습 (raw/molds/external 6개) — Q2 첫 axis 부분 정합
- "비개발자 ICP 보호" Reach Gate — Q1 해결법 (3) "user-fit oracle"과 정합
- 30줄 cap, generic 금지 — Q1 해결법 (1) "context trap 회피"와 정합

### perplexity가 들고 온 새 발견 (3개)

1. **Reference-driven 한계 객관 수치 (<40% 기능 UX)** — ARC raw/molds/ 단독 의존 위험성 정량화. 채택 = 사례 학습은 "표면 디자인용"으로 명시 + 별도 기능 UX 검증 axis 필수.
2. **ICP-loop 자동 검증 framework 시장 미정착 = ARC가 직접 발명** — 빌드 끝 후 ARC 자체가 ICP 페르소나로 Anthropic Computer Use / Browser-Use / Playwright로 회원가입→첫 가치→결제 자동 시뮬, 실패 시 재빌드. **이게 ARC의 차별화 핵심.**
3. **"비개발자 end-to-end 결제 작동 launch postmortem 0건"** — ARC가 1건만 만들어도 시장 자산. test_run_001 (동네미용실) / test_run_002 (1인 솔로 워커) 어느 쪽으로 가든 첫 사례 가치 큼.

### 새로 박을 ARC 룰 후보 (Lian 결정 대기)

- **(R1)** Phase 2 빌드 끝 후 **ICP-loop 자동 검증 단계 강제**. 회원가입→첫 가치→결제 클릭 시뮬 PASS 안 하면 빌드 미완료. 도구: Anthropic Computer Use 또는 Playwright.
- **(R2)** raw/molds/ 사례 사용 시 명시: "표면 디자인 베끼기용. 기능 UX는 별도 검증 axis로 들어감." (CLAUDE.md L7 보강)
- **(R3)** 사례에서 빌드로 갈 때 "user-fit oracle 체크리스트" prompt 강제: no API keys visible / mobile-first / no CLI / no env var 노출 / 회원가입 단계 ≤3 / 결제 클릭 ≤3.

### perplexity가 못 들고 온 것 (한계)
- Q3, Q5는 답 약함 (시장 정답 자체가 없음). 깊은 영어권 forum (HN Show HN, Indie Hackers, Reddit r/SaaS) 직접 다이브 / GitHub trending 직접 조사 = 추가 검색 필요할 수 있음.

---

## 출처 통합 (38개)

### Q1 (실패 패턴) — 7
1. https://stackoverflow.blog/2026/01/28/are-bugs-and-incidents-inevitable-with-ai-coding-agents/
2. https://www.penligent.ai/hackinglabs/ai-agents-hacking-in-2026-defending-the-new-execution-boundary/
3. https://arxiv.org/pdf/2601.15195 (Where Do AI Coding Agents Fail)
4. https://www.youtube.com/watch?v=DIEAEiyceCo (Why Your AI Coding Agent Will Fail in Production)
5. https://www.youtube.com/watch?v=awV2kJzh8zk (Your AI Agent Fails 97.5%)
6. https://substack.com/home/post/p-187176375
7. https://www.fox.com/watch/clip/fmc-4o3uys5pvstzg2z0/

### Q2 (reference-driven) — 7
1. https://tblocks.com/articles/ux-ui-trends/
2. https://thegradient.com/thinking/ai-in-2026-five-product-shifts-well-have-to-design-for
3. https://uxdesign.cc/the-most-popular-experience-design-trends-of-2026-3ca85c8a3e3d
4. https://think.design/blog/dark-patterns-in-ai-2026/
5. https://www.youtube.com/watch?v=whdhrJkZEKA
6. https://www.youtube.com/watch?v=xu_mWjuXUfw
7. https://blog.prototypr.io/ux-ui-design-trends-for-2026-from-ai-to-xr-to-vibe-creation-7c5f8e35dc1d

### Q3 (ICP-loop) — 7
1. https://www.accelirate.com/ai-testing-agents/
2. https://www.harness.io/blog/ai-agents-vs-real-world-web-tasks-harness-leads-the-way-in-enterprise-test-automation
3. https://onereach.ai/blog/why-testing-is-critical-for-ai-agents/
4. https://www.mabl.com/blog/ai-agent-frameworks-end-to-end-test-automation
5. https://qawerk.com/blog/manual-vs-automated-testing-ai-agents/
6. https://testomat.io/blog/ai-agent-testing/
7. https://wopee.io/blog/ai-testing-agents/

### Q4 (도구 비교) — 8
1. https://www.knack.com/blog/ai-app-builder-guide/
2. https://lovable.dev/guides/top-ai-platforms-app-development-2026
3. https://www.zite.com/blog/ai-web-app-builder
4. https://www.taskade.com/blog/ai-app-builders
5. https://hygraph.com/blog/ai-web-development-tools
6. https://checkmarx.com/learn/ai-security/top-12-ai-developer-tools-in-2026-for-security-coding-and-quality/
7. https://amitray.com/ai-coding-tools-2026-comparison/
8. https://www.qawolf.com/blog/the-12-best-ai-testing-tools-in-2026

### Q5 (실 성공 사례) — 9
1. https://elementor.com/blog/ai-web-app-builder/
2. https://flatlogic.com/blog/10-best-ai-app-builders/
3. https://productschool.com/blog/artificial-intelligence/ai-business-use-cases
4. https://gaincafe.com/blog/best-ai-app-builders-2026
5. https://www.superblocks.com/blog/ai-app-generation
6. https://www.knack.com/blog/web-app-ideas/
7. https://mindster.com/mindster-blogs/future-ready-ai-app-ideas/
8. https://tech-stack.com/blog/ai-app-ideas-13-for-2025/
9. https://www.nocode.mba/articles/best-ai-app-builders-2026
