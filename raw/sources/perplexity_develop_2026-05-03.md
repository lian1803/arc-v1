# perplexity 메타 검색 — ARC 디벨롭 방법 (5쿼리 3차)

date: 2026-05-03
source: Perplexity sonar-pro 5쿼리 (Lian 지시 — "방향 맞으니 디벨롭 어떻게 할지 외부 찾기")
status: 변환 재료. 매뉴얼화 X. 원본은 `.tmp_pplx_out_dev/` 5개 파일.
배경: 1차(buildgap), 2차(solopreneur standard) 이은 3차. ARC가 외부 정론 정합 확인 후 "그래서 어떻게 디벨롭?" 답 찾기.

---

## 핵심 발견 (BLUF)

1. **현재 ARC = 1인 시스템 자연 진화 day 1-5 단계.** 정상. 더 디벨롭 = 룰 X, 사례 채우기.
2. **새 룰 vs 새 사례 기준 (정론)**: 3+ 프로젝트에서 같은 패턴 실패 = 룰. 단발 성공 = 사례. → 사업 0건 끝난 ARC는 룰 추가 금지, 사례 추가가 맞음.
3. **★ Anti-pattern 경고**: "Pilot Graveyard" = 프로토타입 12-24개월 iteration, launch 0건. **ARC가 지금 정확히 이 위험.** (test_run_001 architecture 완성 후 빌드 멈춤)
4. **Knowledge agent 정론** = CLAUDE.md + Cursor .cursorrules. ARC 이미 갖고 있음. 추가 옵션 = MCP/Obsidian RAG/LangGraph (단 LangGraph는 multi-agent = enterprise 패턴 재발 위험).
5. **사례 라이브러리 표준 포맷**: YAML (goal/setup/actions/outcomes/lessons/tags) + 폴더(successful/failed/internal/benchmarks) + 100-200 cap + 매년 80% archive.
6. **Q4 spec framework 비교 답 없음** — perplexity 직접 명시: "search results에 BMAD/OpenSpec/Spec Kit 자료 없음. 직접 GitHub 검색 권장."

---

## Q1 — 1인 시스템 자연 진화 단계 (★ 가장 중요)

### 시간순 진화 패턴
| 단계 | 시스템 모습 | 액션 |
|---|---|---|
| **Day 1** | CLAUDE.md 3-5 룰 + /knowledge 1-2 샘플 + /cases 1 사례 | GitHub cursor-rules starter 복사. Claude Pro $20/월. |
| **1st 사업 끝** | + 2-3 프로젝트 룰 + 사례 1개 추가. 실패 prompt prune. | "Markdown 출력 / 간결 / 사용자 voice 참조" 같은 룰 |
| **5th 사업 끝** | sub-file로 분리 (`rules/marketing.md`, `rules/dev.md`). 사례 10-15개 카테고리. `voice.md` 추가 | brand consistency용 |
| **10th 사업 끝** | root `index.md`, /sample 20+ vetted, /knowledge 자동 요약 | Pieter Levels 식 모듈러 |

### 유지 vs 제거 (80/20 룰)
| 카테고리 | 유지 | 제거 |
|---|---|---|
| 룰 | CLAUDE.md, 도메인별 sub-rules | 단발성 tweak |
| 지식 | voice.md, 핵심 fact | 만료 데이터 |
| 사례 | top 10-20 vetted | 중복, 실패 |

### 새 룰 vs 새 사례 기준 (★)
- **새 룰 추가 시점**: 3+ 프로젝트에서 같은 패턴 실패 (예: "코드 prompt에 항상 error-handling 포함" — 같은 버그 반복 후)
- **새 사례 추가 시점**: 단발 성공 (예: 고전환 이메일 chain — `/cases`에 metadata와 함께 archive)
- 결정 포인트: **반복 행동 = 룰, 영감 = 사례**

### Bloat 신호 + 컷백
- prompt 30초+ / AI 룰 무시 (hallucination 20% 증가) / 파일 100개+ / 재사용률 30% 미만
- 컷백: AI 자체에게 "redundancy 요약 시켜" → top 80/20만 남김 → 룰 master CLAUDE.md로 merge → archive 외부 (Notion 등)
- 6개월 주기 reset (10시간/주 회복 보고)

### 출처 한계
정론 출처는 일반 가이드 (entrepreneurloop, prometai). Pieter Levels GitHub/podcast 직접 인용 못 잡음. 익명 indie hacker writeup이 패턴 일치.

---

## Q2 — Knowledge agent / Context engineering 구체 구현

### 정론 도구 (스타 수 + activity)

| 도구 | GitHub / 위치 | 스타 | 핵심 기능 | 1인 적합성 |
|---|---|---|---|---|
| **Packmind** | github.com/packmind-ai/packmind | ~2.5k | CLAUDE.md 자동 생성 from commit history. 67% repo 채택 (Greptile 2025) | ★★★ — ARC와 결 정합 |
| **Cursor .cursorrules** | (built-in) | — | `.cursor/rules/` + MEMORY/RULE 형식 | ★★★ — ARC가 사실상 이미 |
| **Anthropic CLAUDE.md** | (built-in `claude /init`) | — | Skills + Conventions + Workflow 섹션 | ★★★ — ARC가 이미 |
| **Obsidian + Claude RAG** | langchain-ai/obsidian-rag | ~3k | vault embedding + Claude 쿼리 | ★★ — ARC raw/molds 보강 가능 |
| **Notion + Claude** | anthropic-contrib/notion-rag-claude | ~900 | API → Claude prompt | ★ — Notion 의존 |
| **LangGraph** | langchain-ai/langgraph | 12k | checkpointer로 세션 state 보존 | ❌ — multi-agent orchestration = enterprise 패턴 |
| **CrewAI** | crewAIInc/crew-ai | 15k | role-based agent 35 LOC | ❌ — multi-agent = 1인 X |

### ARC에 적용
- 이미 Anthropic CLAUDE.md + raw/molds + memory 갖고 있음 = **추가 도입 X 필요**
- 향후 사례 50+ 되면 Obsidian + RAG 검토 (semantic search)
- LangGraph/CrewAI = 의도적 배제 (1인 ≠ multi-agent)

### Cursor .cursorrules 예시 (참고)
```
# .cursorrules
RULE: Always load project playbook from CLAUDE.md
RULE: Use /skill docker-validate for container work
MEMORY: Commit patterns - prefer async/await over callbacks
```

### Anthropic CLAUDE.md 표준 형식 (참고)
```
# CLAUDE.md: Project Context & Skills
## Conventions
- Use TypeScript with strict mode
- PRs require 80% test coverage
## Skills
/docker-validate: Check base images (script: validate.sh)
## Workflow
Always reference commit history for patterns.
```

→ ARC CLAUDE.md는 다른 결 (3원칙 + 라우터 + Reach Gate). 둘 다 정답 — ARC는 "사례 라우팅" 강조, Anthropic 표준은 "convention + skill" 강조. ARC식 유지가 정합.

---

## Q3 — 사례 라이브러리 best practice (★ raw/molds 디벨롭 가이드)

### (a) 사례 표준 포맷 (YAML)
```yaml
goal: 동네미용실 단골 기억 도구 빌드
setup: Next.js + Convex + Clerk + Toss + Solapi
actions:
  - Day 1-2: PIN 인증 + 기본 라우팅
  - Day 3-4: 손님 카드 + 메모
  - Day 5-7: 알림톡 cron + 발송
outcomes:
  success_metrics: 베타 5명, 알림톡 발송 100건
  failures: PIN 분실 시 재설정 흐름 누락
lessons:
  - PIN dual-track 인증은 정수민 OK, but recovery 흐름 필요
  - Solapi 검수 1-3일 = MVP 일정 buffer 필수
tags: [korea, b2c, mobile-first, alimtalk, 1-person-shop]
```

→ **ARC raw/molds/{my,external,failed}/ 모든 파일에 위 헤더 박기 권장.** 현재 baemin.md 등은 비정형 (서사) — 점진적 전환.

### (b) 조직: hybrid folder + tag + semantic search
- 폴더 (이미 ARC): `/successful` (my), `/external`, `/failed`
- 태그: 검색 가능한 metadata
- semantic search: 50+ 사례 시 도입 (Obsidian Smart Connections / Claude vault 쿼리)
- **flat 구조, 폴더당 50-100 cap**

### (c) 매칭 전략
- < 50 사례: 수동 (folder + tag scan)
- 50+: semantic search 자동 ("이 새 프로젝트에 가장 비슷한 5개 사례 매칭")
- hybrid 효율적: 자동 top 5 → 수동 review → 30% 에러 감소

### (d) 새 사례 vs 기존 참조
- **70% match (goal/setup/outcome)** = 참조
- **새 실패 / 돌파 / 외부 변화 (예: 2026 AI 스택 변경)** = 추가
- 적응 시간 <2시간 = skip / >2시간 = diff와 함께 추가 ("Like Case#42 but Supabase → Railway")

### (e) Bloat 방지
- 매년 80% archive
- AI 주간 요약 ("top 10 패턴 추출, 나머지 archive")
- 100-200 active cap
- "Lego blocks" 마인드셋 — 모듈/swap, 비축 X

---

## Q4 — Spec framework 비교 (★ 정보 부족)

### perplexity 직접 답 (인용)
> "I cannot provide the comprehensive comparison you've requested. The search results available don't contain the specific information needed to answer your query accurately."

### 언급된 이름들 (deep dive 자료 X)
- BMAD-Method
- OpenSpec
- Spec Kit
- Agent OS
- Taskmaster
- AgentMD
- ai-codex

### 추천 (perplexity 자체 권고)
- "직접 GitHub 검색 + Reddit (r/programming, r/LocalLLM, r/solopreneur) + HN 토론" 권장
- ARC식 자체 시스템이 이미 정합 → spec framework 흡수보다 자체 진화 우선

---

## Q5 — Anti-pattern: 시스템이 사업을 잡아먹는 함정 (★ ARC 경고)

### 정확한 1인 사례는 perplexity가 못 찾음 — enterprise parallel만

### Closest 패턴 — "Pilot Graveyard"
> "AI 프로토타입 12-24개월 iteration, production launch 0건. '아직 모델 train 중' / '알고리즘 다듬는 중' 변명 반복."

→ **ARC 현재 상태와 정합:**
- 4/29: external mold 6개 + test_run_001 architecture 완성 + test_run_002 pains 5개
- 4/30: ARC 자체 점검 (perplexity 메타질문) + hook 3개
- 5/1-5/3: 3일 공백 + 또 ARC 자체 디벨롭 검색 (오늘)
- **사업 launch: 0건**

### 다른 Symptom
- **Field blindness** — relational/power dynamics 무시 → silent fail
- **Dead-end persistence** — flawed conversation 계속 이어감, 새로 시작 X
- **Over-orchestration** — 완벽 정확도 추구, 복잡 agent, heavy framework로 stall

### 살아남은 자 discipline
- "Think LLM as AI intern" — 자기 review 항상
- "Start simple, no framework"
- "Reset ruthlessly" — dead-end thread 버리고 다시
- (1:3 ratio 같은 명시 룰은 정론에 없음, 산업 통념)

### Productivity Theater 패턴
- 시스템/도구 fetishize
- "secret sauce prompt" 신화
- 65% 실패는 사람/프로세스인데 tech (모델/데이터) 탓
- → ARC가 빠질 위험: "또 perplexity로 검색해야지" / "또 한 번 더 룰 박아야지" / "또 ARC 점검해야지"

---

## ARC 정합성 평가 + 다음 액션

### 외부 정론 정합 (유지)
- ✅ ARC = day 1-5 자연 단계
- ✅ CLAUDE.md 30줄 cap = lean 정합
- ✅ 사례 기반 = Q3 정답
- ✅ sub-agent 빼기 결정 = Q2 정합 (LangGraph/CrewAI 의도적 배제와 결 같음)
- ✅ tools/sim/ luna 5개 carry over = Q3 "사례 = Lego block" 정합

### 외부 정론에 따라 추가 액션
- 🔧 **(즉시) raw/molds/failed/ 채우기** — luna 3개 carry (audit-over-reporting / cloudflare-pitfalls / agentic-subagent-failure). 0건 → 3건.
- 🔧 **(즉시) raw/molds/external/ 보강** — luna cloudflare_recipes 1개 carry. 6 → 7건.
- 🔧 **(단기) raw/molds/ 표준 YAML 헤더 적용** — 신규부터. 기존 6개는 lazy 전환.
- 🔧 **(단기) projects/test_run_002/PLAN.md 작성** — 5개 후보 중 1개 (인보이스 자동독촉 추천) 골라 1장 SPEC. 빌드 진입.

### ★ Anti-pattern 회피 룰 (ARC에 박을지 Lian 결정)
- **(R-ship)** "사업 launch 1건 전까지 ARC 자체 디벨롭 작업 동결." 시스템 vs 사업 = 사업 우선. 시스템은 사업 진행 중 막히는 자리에서만 evolve.
- **(R-ratio)** "시스템 변경 1번 = 사업 출시 3번 룰" (정론에 명시 X, 산업 통념). ARC가 지금 1:0 (시스템만 변경, 사업 출시 0).

### 의도적 미채택
- spec framework (BMAD/OpenSpec 등) 도입 — 자료 부족 + 자체 시스템 정합 우선
- LangGraph / CrewAI / multi-agent orchestration — enterprise 패턴 재발
- 사례 자동 요약 / RAG / Obsidian 연동 — 50+ 사례 도달 후 검토
- 사례 표준 YAML 헤더 강제 (legacy 6개 일괄 변환) — lazy 전환이 정합

---

## 출처 통합 (29개)

### Q1 (자연 진화) — 8
1. https://www.youtube.com/watch?v=9KHiKfrmKvU
2. https://www.metaintro.com/blog/ai-tools-solopreneurs-productivity-triple-output-2026
3. https://prometai.app/blog/solopreneur-tech-stack-2026
4. https://entrepreneurloop.com/ai-tools-to-scale-solo-business/
5. https://www.anything.com/blog/best-ai-tools-for-solopreneurs-2026
6. https://f3fundit.com/ai-project-management-stack-solopreneurs-2026-guide/
7. https://www.taskade.com/blog/one-person-companies
8. https://get-alfred.ai/blog/best-ai-tools-for-solopreneurs

### Q2 (knowledge agent) — 7
1. https://www.youtube.com/watch?v=o8ZURWxsEiY
2. https://www.agilesoftlabs.com/blog/2026/03/langchain-vs-crewai-vs-autogen-top-ai
3. https://a-listware.com/fr/blog/how-to-create-an-ai-agent
4. https://handsonarchitects.com/blog/2026/ai-toolset-for-software-architect-2026q1/
5. https://packmind.com/context-engineering-ai-coding/what-is-contextops/
6. https://www.langchain.com/state-of-agent-engineering
7. https://maven.com/p/453e73/ai-agents-agentic-workflows-your-2026-roadmap

### Q3 (사례 라이브러리) — 5
1. https://prometai.app/blog/solopreneur-tech-stack-2026
2. https://f3fundit.com/ai-project-management-stack-solopreneurs-2026-guide/
3. https://bestpractice.ai/ai-use-cases
4. https://www.anything.com/blog/best-ai-tools-for-solopreneurs-2026
5. https://www.youtube.com/watch?v=KA4Crfp79ns

### Q4 (spec framework) — 답 부족 — 8
(perplexity가 deep dive 자료 못 찾음 — 직접 GitHub 검색 권장)
1. https://www.youtube.com/watch?v=b6cbxSaa4U4
2. https://uvik.net/blog/agentic-ai-frameworks/
3-8. (multi-agent runtime framework 위주, spec framework X)

### Q5 (anti-pattern) — 6
1. https://age-of-product.com/ai-transformation-anti-patterns/
2. https://www.scrum.org/resources/blog/ai-transformation-anti-patterns-and-how-diagnose-them
3. https://dev.to/lingodotdev/ai-coding-anti-patterns-6-things-to-avoid-for-better-ai-coding-f3e
4. https://hugobowne.substack.com/p/episode-59-patterns-and-anti-patterns-340
5. https://simonwillison.net/guides/agentic-engineering-patterns/anti-patterns/
6. https://www.youtube.com/watch?v=emBhYB294X0
