# perplexity 메타 검색 — 1인 창업가 AI 빌드 표준 (5쿼리 2차)

date: 2026-05-03
source: Perplexity sonar-pro 5쿼리 (Lian 지시 — "luna 줄일까 ARC 디벨롭할까 방향 결정용")
status: 변환 재료. 매뉴얼화 X. ARC 정합 부분만 발췌 적용. 원본은 `.tmp_pplx_out_solo/` 5개 파일.
배경: 5/3 1차 검색(`perplexity_meta_buildgap_2026-05-03.md`)에 이은 2차. 1차는 "AI 빌드 도구 갭", 2차는 "1인 창업가 표준" 각도.

---

## 핵심 발견 (BLUF)

1. **Luna 줄일 게 아님. 방향 자체가 enterprise 패턴.** 1인 정답 = "최소 룰 + 사례 기반" (Q3). ARC 디벨롭이 정답.
2. **시장 표준 도구 스택 = Cursor + Claude (또는 Claude Code) + Notion 스펙.** Pieter Levels / Marc Lou / Tony Dinh / Jon Yongfook / Arvid Kahl 전원 거의 동일 (Q1).
3. **Spec-Driven Development (SDD) + vibe coding 결합이 현재 정론.** 순수 체크리스트 단독 성공 사례 0건 (Q4).
4. **Context Engineering** (CLAUDE.md, 구조화 메모리, knowledge agent)이 2026 핵심 — cold start 방지 (Q4).
5. **1인 SaaS 표준 단계**: 30일 검증(랜딩+인터뷰+5 pre-sale) → 2-8주 MVP → 베타 5-20명 → 첫 매출 3-4개월. 30일 내 20 signup 못 받으면 폐기 (Q2).
6. **Sweet spot = 1-3 core services 집중 + Pieter Levels "one big folder, one stack, no over-engineering"** (Q5).

---

## Q1 — 실제 1인 창업가들 도구 스택 (Pieter Levels 외)

| 창업가 | 스택 | 워크플로우 | 새 SaaS 시작 시 | overload 회피 |
|---|---|---|---|---|
| **Pieter Levels** (Nomad List, Photo AI) | Cursor + Claude | 매일 Cursor 자동 코드 + 20-30% 마케팅 AI | **Notion AI = product manager (스펙 먼저)** → Cursor MVP (이전 2-6개월 → 몇 주) | Cursor의 "cloud agents" 프로젝트별 분리 |
| **Marc Lou** (ShipFast 외 다수) | Cursor Pro + Claude Code + v0 | 주간 "ship sprint", multi-file edit | Claude로 경쟁사 분석 → Cursor agentic 빌드 | 프로젝트별 Cursor 탭 + 파일 업로드 제한 |
| **Tony Dinh** (Black Magic, Typing Mind) | Cursor + Claude | 매일 cloud automation, "유지=감독만" | Claude = "research analyst" → Cursor scaffold | Cursor agent 플랫폼 ($1.2B ARR), repo별 격리 |
| **Jon Yongfook** (Bannerbear) | Claude Code (SWE-bench 80.8%) + Cursor | Claude 자동 review + Cursor scaffold | Claude 경쟁사 분석 → Cursor 며칠 MVP | Claude 1M 컨텍스트, 제품별 deep dive |
| **Arvid Kahl** / Daniel Vassallo | Cursor/Claude Code + Notion AI 스펙 + Perplexity 인텔 | 5-10% 주간 마케팅 + Cursor 병렬 MVP | Notion AI 로드맵 → Claude research → Cursor (26% 빠름) | role-specific AI |
| Dan Koe / Justin Welsh / Pat Walls | (코딩 도구 명시 X, 마케팅 AI 위주) | — | — | — |

### 공통 패턴
- **Cursor + Claude (또는 Claude Code) + Notion 스펙** — 전원 동일
- **"AI = 내 개발팀"** 마인드셋
- **프로젝트별 컨텍스트 격리** (탭/repo/cloud agent 단위)
- **Claude를 "research analyst"로** 쓰고, Cursor를 "build hand"로 분리

### Aider 언급 없음. 2026 indie hacker 지배적 도구 = Cursor + Claude Code.

---

## Q2 — 1인 SaaS 표준 워크플로우 (idea → 첫 매출)

### 표준 타임라인
| 단계 | 기간 | 핵심 지표 | 죽일/살릴 기준 |
|---|---|---|---|
| **(a) 검증** | 30일 | 랜딩 + 인터뷰 10-20명 + **5명 pre-sale** | 30일 내 20 signup X = **폐기** |
| **(b) 빌드 첫 단계** | 1-2주 | 랜딩 + waitlist 먼저 (full MVP X) | "build-first 대비 첫 매출 40% 빠름" |
| **(c) MVP 빌드** | 2-8주 | 입력 1개 / 출력 3개로 좁힘. Next.js+Supabase+Stripe+Vercel ($30-100/월) | — |
| **(d) 런칭** | 베타 5-20명 | Twitter 스레드 + Reddit/Slack 커뮤니티 + build-in-public | Product Hunt/SEO 우선 X — 좁은 traction 우선 |
| **(e) 첫 매출** | 3-4개월 | 첫 10명 = pre-sale + 베타 conversion + 커뮤니티 | $20-80/월 가격, $5K+ MRR median |
| **(f) 죽이거나 계속** | — | <10-20 signup OR 5% 이상 churn = 죽임 / 5-10 결제 베타 OR $5K MRR 추세 = 계속 | $4.2K median MRR (micro-SaaS) |

### 구체 사례
- **Content repurposing tool** (podcast → LinkedIn): 랜딩 → 30일 검증 (20 signup + 10-20 인터뷰) → 5-6주 베타 → 입력 1개(podcast audio) / 출력 3개 (LinkedIn/뉴스레터/스크립트)
- **Dunning recovery SaaS**: SaaS 창업가 Slack 그룹 immerse → 불만이 곧 마케팅 카피 → 6-8주 베타 (5-10명)
- **AI RFP agent**: 커뮤니티 listening + 5명 50% pre-sale → Twitter 스레드로 첫 100명

### 미리 결제(pre-sale) 패턴
- 5명한테 50% 할인으로 미리 결제 받기 = 가장 강한 검증
- "사람이 진짜 돈을 낸다" = 인터뷰 10번보다 강한 신호

---

## Q3 — Heavy 룰북 vs Minimal — 1인 정론 (★ ARC 방향 결정 답)

### 결론 (직접 인용)
> "**For 1-person teams and solopreneurs in AI-assisted software development, the industry consensus favors minimal rules + example/case-based prompting (lean style)** over heavy rule books + many specialized sub-agents (enterprise multi-agent style)."

### Lean vs Heavy 비교표

| 측면 | Lean (최소 룰 + 사례) | Heavy (룰북 + sub-agent) |
|---|---|---|
| **누구에게** | 솔로프러너, 빠른 prototype, daily coding | 팀/엔터프라이즈, 대규모 legacy 마이그레이션 |
| **장점** | 비용 $36-87/월, 3x 속도 | scale 신뢰성, 품질 게이트 |
| **핵심 패턴** | 문제를 LLM 친화적 chunk로 분해, 학습을 prompt에 embed | recursive agent, graph, 며칠 prompt 투자 |

### Heavy가 1인을 망치는 4가지 실패 모드 (★ Luna 진단)

1. **Iteration Trap** — AI 출력 고치는데 학습 누적 안 됨. "you can't reuse it." (Luna 142개 에이전트 매번 cold)
2. **Overhead Drowning** — 50인 팀용 PM 워크플로우가 1인의 정신적 부담 (Luna PENDING.md 28KB)
3. **No Quality Feedback** — 자동 테스트/안돈 없으면 AI YOLO, 인간 review 강요 (Luna §1 35/40 룰이 이 시도)
4. **Abstraction Loss** — 시스템화 의존하다 시스템 깊이 이해 잃음 (Luna가 자기 시스템 운영에 빠짐)

### Heavy가 효과 시작점
- **10명+ 팀** — 일관된 실행 + 수백 코드 segment 처리
- **1-5명 = setup 시간이 산출 능가** = 1인은 절대 X

### ARC 결론
- ARC 30줄 cap, 사례 기반, "사고 → 새 룰 X" = **외부 정론과 정확히 일치**
- Luna = enterprise 패턴, 1인이 가져갈 게 X (줄여도 본질 안 바뀜)

---

## Q4 — Spec-Driven Development (SDD) — 토글식의 정답

### 결론 (직접 인용)
> "Spec-driven development (SDD) is the **most effective methodology** for 2026 solo SaaS development. It significantly outperforms pure checklist or decision-tree approaches."

### SDD 3단계
1. **Requirements Definition** — 무엇을 만들지
2. **Design Planning** — 어떻게 만들지
3. **Structured Implementation** — 코드

### 효과 사례
- Built In 팀: SDD로 multi-OS 실시간 알림 기능을 **2주 → 2일**로 단축
- "주요 기능 / 아키텍처 변경 / 새 시스템 컴포넌트"에 가장 효과
- 그 다음 단계 = "vibe coding"으로 iterate/refine

### Context Engineering = 2026 핵심 차별
> "**Context engineering has replaced prompt engineering** as the most critical solo founder skill in 2026."

구성:
- **CLAUDE.md** 파일 — AI 세션마다 자동 로드
- **MCP 서버** — 외부 데이터/도구 연결
- **RAG 파이프라인** — 검색 기반 컨텍스트 주입
- **구조화 메모리 시스템** — 의사결정/지식 영구 저장
- **Knowledge agent** 패턴 — 별도 에이전트가 지식 저장만 담당, "Claude Code 세션마다 cold start 방지"

### 체크리스트 단독 = 정론에 의해 부정
> "**No documented success cases for pure checklist-driven, decision-tree, or BDD approaches as primary methodologies for solo SaaS in 2024-2026.**"

이유: 체크리스트는 architectural context를 보존 X → 매 세션 cold start → AI에게 매번 architectural choice 다시 brief해야

### Hybrid Best Practice (가장 효과)
- **큰 결정 = SDD spec으로 못 박기**
- **디테일 = vibe coding으로 즉흥**

### Spec-driven 프레임워크 현황 (2026 초)
- OpenSpec, BMAD, Spec Kit, Agent OS, Taskmaster — 채택 편차 큼 (한 곳 6개월 863% 성장, 다른 곳 18%)
- 솔로 operator 효과 데이터는 아직 없음

---

## Q5 — Sweet spot — 1인 시스템 minimum viable

### 결론
> "Solopreneurs achieve a minimum viable system sweet spot through **extreme simplicity** — focusing on **1-3 core services**, basic automations, and minimal tools that prioritize **revenue-generating activities over complexity**."

### (a) Chaos → 구조 추가 사례
- SYSTEMology case: "수익 위한 minimum 활동 수" 식별 → simple 시스템만 박음 → scalable
- 일반: MVP 시작 → baby step iterate → AI assistant for admin (basic automation)

### (b) Over-engineering → 줄임 사례
- "Productivity theater" — 복잡한 service buffet / 추적 만들다 성장 멈춤
- 살아남은 자: 1-3 profitable offering으로 컷
- "Simple scales, complex fails"

### (c) 살아남은 자 공통 도구
- **PM**: 단일 backlog (Linear-inspired) 또는 CRM 1개
- **자동화**: AI for admin / 마케팅 sequence / 1-3 core services tiered
- **습관**: 아침 계획 + 저녁 review, niche 집중, 매출 metric만 추적 (lead, conversion, margin)
- **공통**: "one folder simplicity" > multi-tool sprawl

### (d) Dual Operating System
- **Build mode** = scalable asset 만들기 (digital product, automation)
- **Operate mode** = 표준 시스템으로 client delivery
- 분리 = burnout 방지. 나머지는 tech가 80% 처리

### (e) Pieter Levels 철학
> **"One big folder, one stack, no over-engineering."**

- 단일 directory에 모든 프로젝트 (Carrd, simple script 수준)
- tools bloat 없이 빠르게 launch
- 카운터 사례: 복잡한 offer/metric 만들다 망한 솔로 vs Levels 식 winner (MVP + automation 으로 multi-business scale)

---

## ARC 정합성 평가 (Lian 결정용)

### 외부 정론과 일치 (유지)
- ✅ **30줄 cap CLAUDE.md** — Lean style 정확. Heavy 룰북 안 만들기.
- ✅ **사례 기반 (raw/molds/)** — example-based prompting 정답.
- ✅ **"사고 → 새 룰 X"** (CLAUDE.md L25) — over-engineering 회피.
- ✅ **Reach Gate** — Pieter Levels "no over-engineering"과 정합.

### 외부 정론에 비추어 빼야 할 것
- ❌ **Phase 2 "sub-agent 호출" 룰 (MODES.md L13)** — 1인이 sub-agent 망 만들면 enterprise 패턴 재발. Cursor/Claude 단일 대화로 충분. **삭제 또는 명시: "Lian + Claude/Cursor 1대1, sub-agent X."**

### 외부 정론에 따라 추가 후보
- 🔧 **(R-spec)** SDD spec 1장 형식 (Pieter Levels 식 Notion 한 페이지 수준) — projects/{이름}/SPEC.md 룰. 기능 ≤3 / ICP / 핵심 흐름 / 죽일 기준만.
- 🔧 **(R-context)** Context Engineering — CLAUDE.md + raw/molds + memory 가 이미 ARC에 있음. **추가 X 필요.** 단 "knowledge agent" 패턴 = 별도 에이전트가 학습 저장만 — ARC에선 raw/molds/my/ + raw/molds/failed/ 가 이 역할 (현재 비어있음, 채워야 함).
- 🔧 **(R-kill)** "30일 검증 → 20 signup OR 5 pre-sale 못 받으면 폐기" 룰 — projects/{이름}/SPEC.md 의 "죽일 기준" 항목으로.

### Luna에서 carry over할 가치 있는 것 (룰 X, 단순 기록 형식만)
- `decisions/` 폴더 — architectural decision record (1인이 미래 자기에게 보내는 메모)
- 단 luna의 17 헌법 + 35/40 rubric 같은 무거운 룰은 X

### 의도적 미채택
- **Sub-agent 망** (luna parts/agents 142개) — enterprise 패턴
- **rubric 35/40 자동 채점** — Heavy 패턴
- **체크리스트만 쌓기** — Q4 정론 위반 (성공 사례 0건)

---

## 다음 한 동작 후보 (Lian 결정)

- **(가)** 통합본 박고 → ARC CLAUDE.md/MODES.md 살짝 수정 (sub-agent 빼고 SPEC.md 룰 추가) → test_run_002 시작
- **(나)** 통합본만 박고 — Lian이 정독 후 결정
- **(다)** 통합본 + ARC 수정 + 시뮬 도구도 같이 만들기 시작

추천: **(가)**. 시뮬은 1인 정론에 비추어 보류 — "1인은 그냥 쓰고 안 되면 직접 고쳐"가 가까움. Pieter Levels도 시뮬 없음.

---

## 출처 통합 (34개)

### Q1 (실제 1인 창업가) — 7
1. https://findskill.ai/learn-ai-for-entrepreneurs/
2. https://vibehackers.io/blog/best-ai-coding-assistants
3. https://www.buildmvpfast.com/blog/free-ai-tools-indie-hackers-2026
4. https://www.youtube.com/watch?v=-f9IHOXy61Y
5. https://www.thesuccessfulprojects.com/indie-hackers-build-saas-with-no-code-and-ai/
6. https://thevibepreneur.com/blog/5-ai-coding-tools-feb-2026
7. https://github.com/topics/indie-hacker

### Q2 (표준 워크플로우) — 9
1. https://lovable.dev/guides/micro-saas-ideas-for-solopreneurs-2026
2. https://superframeworks.com/articles/best-micro-saas-ideas-solopreneurs
3. https://www.youtube.com/watch?v=uQY15RkYrh8
4. https://www.buildmvpfast.com/blog/profitable-saas-ideas-solo-founders-2026
5. https://entrepreneurloop.com/bootstrapped-saas-ideas-founders-2026/
6. https://ideaproof.io/lists/micro-saas-ideas
7. https://www.galaxywing.com/how-to-build-a-saas-mvp-in-8-weeks-a-founders-guide/
8. https://wearepresta.com/profitable-ai-business-ideas-2026-strategies-for-sustainable-growth/
9. https://millipixels.com/blog/micro-saas-startup-ideas-2026

### Q3 (Heavy vs Lean) — 4
1. https://www.lean.org/the-lean-post/articles/industrializing-ai-for-software-development/
2. https://stormy.ai/blog/lean-solopreneur-stack-app-development-guide
3. https://f3fundit.com/ai-project-management-stack-solopreneurs-2026-guide/
4. https://rudyct.com/ai/Lean%20AI%20How%20Innovative%20Startups%20Use%20Artificial%20Intelligence%20to%20Grow%20by%20Lomit%20Patel-2020.pdf

### Q4 (SDD vs 체크리스트) — 8
1. https://arxiv.org/abs/2602.00180
2. https://www.mynameisfeng.com/blog/ai-solopreneur-tech-stack-in-2026-what-actually-works-at-scale
3. https://builtin.com/articles/spec-driven-development-ai-assisted-software-engineering
4. https://www.nxcode.io/resources/news/one-person-unicorn-context-engineering-solo-founder-guide-2026
5. https://www.youtube.com/watch?v=b6cbxSaa4U4
6. https://f3fundit.com/ai-project-management-stack-solopreneurs-2026-guide/
7. https://lovable.dev/guides/micro-saas-ideas-for-solopreneurs-2026
8. https://crazyburst.com/ai-saas-solo-founder-success-stories-2026/

### Q5 (Sweet spot) — 6
1. https://readingraphics.com/guide-solopreneur-how-to-start-one-person-business/
2. https://www.youtube.com/watch?v=1cKzRc-wYaQ
3. https://bask.health/blog/solopreneur-business-model
4. https://kenyarmosh.com/blog/scaling-solopreneur-business/
5. https://www.lifestarr.com/podcast/chatgpt-spills-the-beans-on-being-a-successful-solopreneur
6. https://offers.hubspot.com/1m-solopreneur-mvp
