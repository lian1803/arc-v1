---
name: planning_jtbd
description: JTBD framework reference (Christensen / Ulwick / Moesta) — job statements, Four Forces, ODI score, critique.
source: https://hbr.org/2016/09/know-your-customers-jobs-to-be-done
authored_by: research_lead
verified_by: knowledge_reverify_20260421_session5_round2
orchestrated_by: seoyeon
created_at: 2026-04-21
last_reviewed: 2026-04-21
---

# Jobs-to-be-Done (JTBD) — Framework Reference

> "People don't buy a quarter-inch drill; they buy a quarter-inch hole."
> Customers "hire" products to make progress in a specific circumstance.

## Core Thesis (Christensen, HBR 2016)

A "job" is the progress a person is trying to make in a particular circumstance — functional, emotional, AND social dimensions together. Products are hired/fired based on how well they get the job done. Segmenting by demographics (age/income/persona) systematically misses the causal mechanism; segmenting by job-in-circumstance does not.

Source: Christensen, Hall, Dillon, Duncan. "Know Your Customers' Jobs to Be Done." HBR, Sep 2016. https://hbr.org/2016/09/know-your-customers-jobs-to-be-done (accessed 2026-04-21; header + authors verified, full body paywalled)

## Three Schools (Often Confused)

| School | Lead | Unit of analysis | Primary method |
|---|---|---|---|
| Christensen / Switch | Moesta (co-author) | moment of "switch" | timeline interview |
| ODI | Ulwick / Strategyn | ~50-150 outcome statements | importance × satisfaction survey |
| Jobs-as-Progress | Klement | emotional/identity progress | push/pull narrative |

Source: Ulwick. "Turn Customer Input into Innovation." HBR, Jan 2002. https://hbr.org/2002/01/turn-customer-input-into-innovation (accessed 2026-04-21)
Source: Strategyn ODI overview. https://strategyn.com/jobs-to-be-done/ (accessed 2026-04-21)
Source: Christensen Institute. https://www.christenseninstitute.org/theory/jobs-to-be-done/ (accessed 2026-04-21)

## Job Statement Formula

`{verb} + {object of the verb} + {contextual clarifier}`

Examples (illustrative — author-constructed, not from cited interviews):
- Correct: "밤에 아이 재우고 나서 20분 안에 스스로를 리셋하기"
- Wrong (feature-shaped): "명상 앱을 쓰기"
- Wrong (demographic): "30대 워킹맘이 앱을 쓰기"

If the verb names a product category, the statement is already solution-biased.

## Four Forces of Progress (Moesta, The Re-Wired Group)

Every switch is the net of four vectors:
1. **Push** of the current situation
2. **Pull** of the new solution
3. **Anxiety** about the new solution
4. **Habit** of the present

Progress occurs only when Push + Pull > Anxiety + Habit. Teams chronically over-invest in Pull (features) and under-invest in reducing Anxiety (trial, money-back, social proof).

Source: Moesta & Spiek. *Demand-Side Sales 101*. Lioncrest, 2020. ISBN 978-1544509976.
Source: Re-Wired Group milkshake case. https://therewiredgroup.com/case-studies/milkshakes/ (accessed 2026-04-21)

## ODI Opportunity Score (Ulwick / Strategyn)

Outcome statement: `{minimize|increase} + {metric} + {object} + {clarifier}`.
Example: "Minimize the time to identify ingredients about to expire."

Customers rate each outcome on Importance (1-10) and Satisfaction (1-10). Wikipedia's canonical formulation:

```
Opportunity = Importance + max(Importance - Satisfaction, 0)
```

Importance is deliberately double-weighted. High opportunity = important outcome, poorly satisfied today. Threshold bands (e.g., "> 12 under-served") vary by implementation; Ulwick's *What Customers Want* (McGraw-Hill, 2005) is the canonical book source.

Source: Wikipedia, "Outcome-Driven Innovation." https://en.wikipedia.org/wiki/Outcome-Driven_Innovation (accessed 2026-04-21; formula quoted verbatim)

## Framework Critique (Read Before @import)

1. **Milkshake study directly challenged by Ulwick.** Ulwick argues Christensen mislabels context as job — "long commute" is circumstance, not goal; the real job is "get breakfast on the go" (https://strategyn.com/market-segmentation-is-soured-by-milkshake-marketing/, accessed 2026-04-21). Two schools disagree on what a job even IS.
2. **ODI success-rate figures are vendor-reported.** No peer-reviewed replication of Strategyn's commercial claims.
3. **Schools diverge on method.** Moesta qualitative interview vs. Ulwick quantitative survey produce different artifacts; do not blend carelessly.
4. **JTBD can become unfalsifiable.** Any observed behavior can be retrofitted with a plausible job statement. Guard: require pre-committed predictions before synthesis.

## When to Use in ARC

- `parts/planning/agents/market_analyst.md` — map JTBD before competitor analysis; competitors only compete for the same job.
- `parts/marketing/agents/growth_marketer.md` — ad copy must reference the job's circumstance + forces, not the demographic. See also `marketing_spin_challenger.md` for discovery question discipline.
- `parts/research/agents/insight_extractor.md` — convert interview quotes into job-in-circumstance statements.

## Non-Goals

This file does NOT cover:
- **Interview mechanics** (question sequencing, recording, transcription) — see `research_team_playbook.md` + Moesta *Demand-Side Sales 101* Ch. 3-4.
- **Quantitative ODI survey design** — requires statistical sampling competence; treat this file as conceptual primer only.
- **Positioning or pricing derivation** — JTBD informs both but does not produce them. See `marketing_spin_challenger.md` and future `planning_positioning.md`.
- **Persona / demographic modeling** — JTBD is explicitly opposed to persona-first segmentation (Anti-Pattern 1).

## Anti-Patterns

1. **Demographic segmentation masquerading as JTBD.** "30대 직장인 여성 targeting" is a Census row. Test: statement must survive persona removal.
2. **Solution-shaped job statements.** "명상 앱 사용" names the solution. If you can't describe the job without naming your product, you haven't found it.
3. **Ignoring Anxiety.** Better features raise Pull but rarely overcome Anxiety; trial, money-back, and social proof often beat more features.

## Confidence Notes

- HBR 2016 + HBR 2002: header/author/date verified; full body paywalled (primary, acceptable).
- Strategyn overview + milkshake-critique page: URL-verified; vendor-authored, congruent with HBR 2002.
- Wikipedia ODI: formula verbatim; secondary but reproducible.
- Christensen Institute + Re-Wired Group: URL-verified institutional/primary sources.
- **Removed in this patch**: strategyn.com/jobs-to-be-done-outcome-driven-innovation/ (404); jobstobedone.org/radio/... episode-specific quote (not located on homepage). See `shared/message_pool/strategy/20260421_knowledge-patch/edits.md`.
