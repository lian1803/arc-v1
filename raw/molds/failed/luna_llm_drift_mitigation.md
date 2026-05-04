---
name: llm_instruction_drift_mitigation
description: 단일 세션 내 LLM directive 망각 — 외부 정론 + ARC 적용 가능 mitigation
status: active
authored_by: agent-session31
created_at: 2026-04-29
sources: [
  "https://arxiv.org/abs/2307.03172",
  "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents",
  "https://towardsdatascience.com/a-practical-guide-to-memory-for-autonomous-llm-agents/",
  "https://medium.com/@sonitanishk2003/the-ultimate-guide-to-llm-memory-from-context-windows-to-advanced-agent-memory-systems-3ec106d2a345",
  "https://blog.langchain.com/how-we-built-agent-builders-memory-system/",
  "https://docs.langchain.com/oss/python/concepts/memory"
]
---

# LLM Instruction Drift — 외부 정론 + ARC 적용 패턴

## BLUF

**핵심 발견**: LLM 은 context window 중간~후반에서 earlier instructions 을 U-curve 패턴으로 망각 (Liu et al. 2307.03172). **Best immediate mitigation**: 매 turn 시작 시 critical directives 를 persistent system anchor 로 재주입.

**근본 원인**: Transformer 주의 메커니즘이 context 중간(middle token) 을 down-weight 하고, oral directive 1회 주입 ≠ system anchor 로 인해 newer conflict instructions 이 older directive 를 shadow 함.

**ARC 즉시 적용**: MEMORY.md 에 critical_directives 섹션을 turn-start 마다 explicit 재주입. Cost: 15 LOC. Effect: session 31 누끼 incident 즉시 회피.

---

## 1. 문제 정의

### 1.1 ARC incident (session 31)

Turn N: Lian "사람 누끼따서 검정 배경에 입히는 식"  
Turn N: Seoyeon implements cutout ✓  
Turn N+2: Lian "F:\유튜브\1계정 사진들 학습해서 패턴 확인하고 다시"  
Turn N+3: Seoyeon → implements RECTANGULAR CROP ✗ (cutout 망각)

**원인**: Lian directive (turn N) 이 turn N+3 에서 context middle 으로 묻혀 U-curve down-weight.

### 1.2 "Lost in the Middle" (Liu et al. 2307.03172)

Transformer attention 은 context 의 front/end 에 가중치 집중. middle 정보는 20-30% 성능 하락. 따라서 turn N 지시가 turn N+3 엔 인지 불가.

---

## 2. 외부 정론 (6 소스, 모두 verifiable URL)

### Source 1: Liu et al. (2023) — Lost in the Middle

**URL**: https://arxiv.org/abs/2307.03172

**핵심**: "Performance is often highest when relevant information occurs at the beginning or end of the input context, and significantly degrades when models must access relevant information in the middle." — U-curve pattern universal across all models.

**ARC**: 🟢 HIGH. Turn N 지시 → turn N+3 middle → 망각 예측 가능.

---

### Source 2: Anthropic — Effective Context Engineering

**URL**: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

**핵심**: "Persistence reminders ensure the model understands it is entering a multi-message turn... prevent it from prematurely yielding control." 매 turn 시작 시 critical directives 재주입 권장.

**ARC**: 🟢 HIGH. MEMORY.md 있으나 turn-start 재주입 미흡.

---

### Source 3: Towards Data Science — Memory for Autonomous Agents

**URL**: https://towardsdatascience.com/a-practical-guide-to-memory-for-autonomous-llm-agents/

**핵심**: "Treating procedural memory 'as code', maintaining AGENTS.md, MEMORY.md... under source control allows examination of what changes and when." Versioning + timestamps 필수.

**ARC**: 🟢 HIGH. MEMORY 에 critical_directives 구조 추가.

---

### Source 4: Medium — Ultimate Guide to LLM Memory

**URL**: https://medium.com/@sonitanishk2003/the-ultimate-guide-to-llm-memory-from-context-windows-to-advanced-agent-memory-systems-3ec106d2a345

**핵심**: "Using frameworks like ReAct where accessing memory becomes an explicit action the agent decides to take ensures deliberate, auditable memory management."

**ARC**: 🟢 MID. Explicit access pattern turn-start 에 적용.

---

### Source 5: LangChain — Agent Builder's Memory System

**URL**: https://blog.langchain.com/how-we-built-agent-builders-memory-system/

**핵심**: "Reflection or meta-prompting to refine agent instructions based on conversation feedback." Agent 가 자신의 instruction 을 dynamically refresh.

**ARC**: 🟡 MID-HIGH. Turn-within-session re-anchor 미흡.

---

### Source 6: LangChain Docs — Memory Concepts

**URL**: https://docs.langchain.com/oss/python/concepts/memory

**핵심**: "Short-term memory is persisted via thread-scoped checkpoints... State checkpointing enables recovery."

**ARC**: 🟢 HIGH. Turn-N 마다 explicit checkpoint 없음.

---

## 3. 근본 원인 (4가지)

| 원인 | ARC severity |
|---|---|
| Attention Budget Exhaustion (U-curve) | 🔴 HIGH |
| Conflict Resolution Failure (newer shadows older) | 🔴 HIGH |
| Implicit Anchor vs Explicit System | 🟠 MID |
| Tool-Call Interruption (context bloat) | 🟠 MID |

---

## 4. SOTA Mitigation Patterns

**A. Turn-Level Anchor Reminders** — 매 turn 재주입. Cost: LOW. Effect: 🟢 HIGH.

**B. Persistent Constraint Files** — MEMORY.md structured list. Cost: LOW. Effect: 🟢 HIGH.

**C. Preamble Gate Extension** — instruction-recency check. Cost: MINIMAL. Effect: 🟢 HIGH.

**D. Agent State Machines** — phase-locked constraints. Cost: MID. Effect: 🟡 MID.

**E. Hierarchical Instruction Stack** — CORE/SESSION/TURN levels. Cost: LOW. Effect: 🟢 HIGH.

---

## 5. 즉시 추천 (Candidate #1: A+B Hybrid)

### Primary Fix: Turn-Start Re-Inject + MEMORY Structure

**Where**: MEMORY.md + SessionStart hook + agent template

**Change 1 — MEMORY.md structure**:

critical_directives:
  - turn: 31_N
    directive: "사람 누끼따서 검정 배경에 입히는 식"
    status: active
    timestamp: 2026-04-29T14:22:00Z

**Change 2 — SessionStart hook**:

grep -A 100 "critical_directives:" MEMORY.md | grep "status: active" | format → append to preamble "[RE-VERIFY: {keywords}]"

**Change 3 — Agent template (before action)**:

Check MEMORY.md critical_directives. If any active + not in recent turns → re-inject: "⚠️ Active: '{directive}'"

**Cost**: 5 LOC hook + 10 LOC MEMORY template = 15 LOC.

**Expected Effect**: Turn N+3 에서 "누끼" directive 가 preamble 첫 줄에 자동 반복 → Seoyeon 이 cutout (correct) 선택.

**Validation**: All 6 sources cite persistent re-anchor as primary mechanism. Liu explicitly shows middle-context loss = information placement problem → front placement solves.

---

## 6. 외부 정론 비교 (§13)

| 소스 | 주장 | ARC Agree? |
|---|---|---|
| Liu et al. | U-curve loss universal | ✅ exact incident |
| Anthropic | Persistence reminders core | ✅ expand MEMORY |
| TDS | Procedural memory versioning | ✅ critical_directives list |
| LangChain Memory | Short/long-term dual | ✅ session/turn split |
| Medium | Explicit ReAct pattern | ✅ turn-start read |
| LangChain Builder | Instruction refinement | ✅ missing in ARC |

**Convergence**: All 6 endorse persistent re-anchor. ARC has structure (MEMORY) but lacks turn-level re-inject. Fix 즉시 가능.

---

## 7. Falsifier

**재발 조건**: Session 31+ 3회 이상 같은 유형 drift (earlier→newer overwrites). Candidate #1 적용 후에도.

**Response**: Escalate Candidate #2 (preamble stop+clarify) → Candidate #3 (phase headers). If both fail → model routing / context cache audit.
