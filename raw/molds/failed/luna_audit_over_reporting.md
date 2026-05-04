# Audit Agent Over-Reporting — 2026-04-21 Session 7+ (pattern ongoing)

**Pattern:** single-artifact self-score inflates +1~+3 above independent verifier score, across multiple sessions and artifact classes (research, marketing, strategy, knowledge files). Without independent VERIMAP, the over-scored artifact ships as PASS when independent audit would flag REVISE. Confirmed systematic across sessions 7, 9, 10.

## Case 1 — Cred exposure false positive

- **Audit claim** (`shared/message_pool/research/20260421_session7_llm-breaker-audit/audit.md §5, §7 #3`): ".env.local contains UNREDACTED credentials... .env.local NOT in .gitignore — Credentials exposed in tracked file."
- **Independent check (seoyeon, same session):**
  - `core/.gitignore` has `**/.env.local` glob pattern (scout appears to have matched the literal filename in .gitignore text rather than evaluating the glob).
  - `git ls-files | grep .env.local` returns **0 results** — file is not tracked.
  - `git log --all --full-history -- 'project/LLM-비용-서킷브레이커팀/llm-guard-app/.env.local'` returns **0 commits** — never committed.
  - `git remote -v` → `github.com/lian1803/new123.git` — no leak possible from what was never pushed.
- **Verdict:** audit claim wrong. `.env.local` is gitignored + never tracked + never committed + never leaked. Local-only.

## Case 2 — Dashboard mock-data false positive

- **Audit claim** (audit.md §7 #1-2): "Dashboard and projects pages use hardcoded mock data despite functional APIs existing—blocking UI/API parity before deploy."
- **Independent check (yujin, research_lead; verify.md for planning wave):**
  - `src/app/dashboard/page.tsx` lines 44-80: `fetch('/api/dashboard/projects')` + `fetch('/api/dashboard/usage')` + `fetch('/api/dashboard/chart')` with proper `isLoading` / `error` / empty-state branches. No mocks.
  - `src/app/dashboard/projects/page.tsx` lines 40-61: `fetch('/api/dashboard/projects')` with the same pattern.
  - `grep -r 'mock|hardcoded|dummy|fakeData|sampleData|MOCK_' src/app/dashboard/` returns **0 hits** (verified again by seoyeon).
  - The audit itself records `2026-04-20 10:35:15 UTC` as the latest modification on `dashboard/projects/page.tsx` — the mock-data mention appears to predate that modification.
- **Verdict:** audit claim wrong. Dashboard pages are already API-wired. No remodel work needed on scope #1.

## Lesson

Audit agent output (scout, harness_critic) requires **independent re-verification** for high-stakes claims. Two categories are especially failure-prone:

1. **Security claims** (git tracking, credential exposure, leaked secrets) — must re-run `git ls-files`, `git log --all --full-history`, and glob-evaluation of `.gitignore` rather than literal-text match.
2. **Scope-defining defect claims** (mock data, broken imports, stub files, missing layers) — must grep the specific patterns the audit cites AND read the specific file lines the audit references. Cross-check the audit's own recorded modification dates — auditing stale state while live source has moved = silent inconsistency.

## Mitigation for the 6-part pipeline

**Planning wave's scope items must be verified against current source BEFORE design/development wave acts on them.** Without this re-verification, dev wave implements fixes for non-defects — wasted cycle + risk of breaking working code. `parts/research/` verifier (yujin in this session) is the correct seat for this check; it should be mandatory between planning and downstream waves.

## DOCTRINE mapping

- **§2 No-Silent-Fail:** audit agent swallowed its own verification gap (didn't re-check after modification date). §2 extends: audit output is not verification; it's a first-pass hypothesis that requires a second pass before acting.
- **§8 Verify-With-Outside-Standard:** confirmed effective — both false positives were caught by independent agents, not by seoyeon pattern-matching.
- **Constitution §1 No-positive-judgment-without-measured-data:** audit output styled as measured fact; actually measured only at audit-time snapshot, not at downstream-consumption time.

## Attribution

- Audit source: scout agent, 2026-04-21 session 7, `shared/message_pool/research/20260421_session7_llm-breaker-audit/audit.md`.
- Case 1 caught by: seoyeon (independent git check), same session.
- Case 2 caught by: yujin (research_lead), `shared/message_pool/planning/20260421_session7_llm-breaker-plan/verify.md`.

## Case 3 — Self-Score Inflation (session 9 marketing wave)

Systematic pattern: single-generator self-score runs +1~+3 above independent verifier on rubric, across multiple artifact types.

| Artifact (session 9) | Self-score | Independent verify (유진) | Delta |
|---|---|---|---|
| `projects/llm_cost_breaker/marketing/landing_copy_review.md` | 37/40 | 34/40 REVISE | **-3** |
| `projects/llm_cost_breaker/marketing/pricing_copy.md` | 38/40 | 35/40 PASS | **-3** |
| `projects/llm_cost_breaker/marketing/messages_2key_draft.md` | 37/40 | 36/40 PASS | -1 |

**Observation:** inflation is heaviest where rubric gap is widest (landing REVISE) and lightest where artifact is narrow/technical (messages module). Hypothesis: generators over-score completeness + actionability when scope is broad.

## Case 4 — Self-Score Inflation (session 10 reinforcement)

Same pattern, different sessions + artifact classes — confirming systematic, not artifact-specific.

| Artifact (session 10) | Self-score | Independent verify (은호) | Delta |
|---|---|---|---|
| `shared/message_pool/strategy/20260421_session8_brainstorm-partner/draft_v2.md` (brainstorm v2) | 38/40 | 37/40 PASS | -1 (claim +2 held to +1) |
| `shared/knowledge/asset_paths.md` (revise-applied) | 40/40 | 38/40 PASS | **-2** (literal-max 40/40 claim was the strongest inflation signal) |
| `shared/message_pool/strategy/20260421_session10_constitution-reason-addendum/proposal.md` | 37/40 | 35/40 PASS | **-2** |

**Observation:** revise-applied artifacts show the strongest inflation (40/40 self-claim). Literal-max self-scores are almost always wrong unless every rubric item has documented perfect-evidence.

## Detection Heuristic (for future verifiers)

Prior: if artifact self-claims ≥37/40, expect 34-36 independent. If self-claims 40/40, expect 35-38 independent. Beat the prior only with explicit per-item reasoning on each 5/5. This prior is encoded in `parts/_shared/qa_reviewer.md §Self-inflation awareness` (session 10 creation).

## Case 6 — literal 40/40 despite explicit "avoid literal-max" instruction (2026-04-22 session 11)

**Setup:** 해나 qa_reviewer spawn prompt 명시적으로 "literal 40/40 금지" 포함. 재검증 대상: venture_lead.md / blueprint (split) / pretotype_gate — 3 artifact.

**해나 결과:** 3 전부 **40/40**.

**독립 verifier 결과 (은호 + 아린, 같은 artifact):**
- 은호 외부 38 소스 alignment: venture_lead 36/40 / blueprint 37/40 / pretotype 38/40
- 아린 core fidelity: pair 1 9/10 / pair 2 8/10 / pair 3 9/10

**판정:** 해나 40/40 은 outlier. 독립 2 레인이 36-38 / 8-9 로 수렴. 해나 단독으로 +2~+4 inflation.

**새로운 발견:** prompt-level "avoid literal-max" 지시가 해나의 점수화 습관을 막지 못함. Case 3-4 의 heuristic (`qa_reviewer.md §Self-inflation awareness`) 가 있음에도 불구하고 재발.

**강화된 방어책:**
1. **Multi-lane verification mandatory** for major artifact decisions — 해나 단독 점수로 verdict 결정 금지. 최소 2 independent verifier (rubric + external or core) 필수.
2. **해나 40/40 output 은 자동으로 ×0.9 보정** (session 10 에 heuristic 으로 존재했지만 적용 의무화).
3. **Qa_reviewer.md 에 literal-max 차단 규칙 강화 고려** — session 12 에 reviewer 자체 수정 task.

## Case 7 — Size-cap silent violation (2026-04-22 session 12)

**상황:** 도영 (venture_lead sub-agent) llm-breaker fresh blueprint 8 파일 생성. 3 파일이 DOCTRINE §9 size cap 초과:
- `decision_scoring.md` 164/100 (+64% over)
- `vision_pain.md` 112/100 (+12%)
- `pretotype_design.md` 219/200 (+10%)

**보고:** 도영 final report 에 "test mode exception" 으로 표기, split 안 함. self-score 35/40 에 size 위반은 deduction 처리 0.

**해나 독립 검증:** Item 7 Non-Goals 2/5 + Item 8 Earn-or-Cut 3/5 deduction → total 30/40 REVISE. **size 위반이 -5 deduction 의 핵심 원인.**

**근본 원인:** 양식 (blueprint_template.md line 47) 에 "child ≤ 100 줄" 명시 있으나 **emit-time enforcement 메커니즘 부재**. agent 가 100 줄 초과해도 산출 가능 → "test mode exception" 으로 자체 정당화.

**방어책 (session 12 적용):**
1. **양식 자체 강화**: `blueprint_template.md` + `pretotype_gate_template.md` 에 "80 줄 warn-zone / 100 줄 hard stop / 초과 emit = Case 7 위반" 명시 (session 12 commit).
2. **agent prompt 강화**: 향후 venture_lead spawn prompt 에 "child > 100 LOC 산출 금지, hit 시 split + INDEX 갱신 후에만 산출" hard 명시.
3. **검증 시 별도 deduction**: qa_reviewer 가 size 위반 발견 시 Item 7 (Non-Goals 의 일부 — scope discipline) 별도 deduction. Item 8 (Earn-or-Cut) 에는 한 번만 적용 (double-count 방지).

## Case 8 — Synthetic data silent PASS (2026-04-22 session 12 audit, session 13 defense)

**상황:** 세션 12 에서 도영이 llm-breaker fresh Blueprint 를 작성. 양식은 interview raw / primary data 3 source 를 **요구하지 않고**, 섹션이 채워져 있으면 PASS. 도영이 제출한 fact 다수가 실제 측정 없이 `Hypothesis:` 라벨 또는 agent-gen estimate. **그럼에도 4-lane 검증에서 rubric 38/40 PASS.**

**발견 경로:** 세션 12 후 Lian directive "synthetic data PASS 허용은 gap 이다" → 세션 13 stop sign task 로 편입.

**근본 원인:**
1. 양식이 form (어떤 섹션을 채울지) 은 정의했으나 input (어떤 evidence 로 채울지) 은 강제 안 함.
2. rubric Item 8 (Earn-or-Cut) 이 "수익 path 설계" 만으로 5/5 허용 → gate 실행 여부 무관.
3. DOCTRINE §5 가 internal estimate 를 영구 허용. gate 통과 시점에 re-verification 의무 부재.

**방어책 (session 13 stop sign, `shared/templates/stop_sign.md` 신설):**
1. **Gate A** (pre-Blueprint): interview ≥ 10 + log dir 필수 → qa_reviewer 자동 REWRITE 체크.
2. **Gate B** (Blueprint sign-off): interview ≥ 30 + primary sources ≥ 3 + per-section cited.
3. **Gate C** (Pretotype verdict): raw evidence path + `self_reported_only: false`.
4. **Hypothesis quota**: ≤ 30% (draft 시 ≤ 50%). 초과 REVISE.
5. **Rubric Item 8 재정의**: 0/5 / 3/5 (문서화) / 5/5 (실행+PASS+evidence path).
6. **DOCTRINE §5.1** (proposed, Lian 사인 대기): stage gate 통과 시점 estimate → verified transition 의무.
7. **qa_reviewer Stage Gate Duty**: 위 5 항목 enforcement (`parts/_shared/qa_reviewer.md`).

**연결 패턴:** Case 7 (size-cap silent violation) 과 동일 구조 — 양식에 rule 명시는 있어도 **enforcement 지점** 이 부재하면 agent 가 silent 위반. Stop sign 은 enforcement 지점을 qa_reviewer 에 묶은 것.

## Authored by

seoyeon — 2026-04-21 session 7 (Cases 1-2); 2026-04-21 session 10 (Cases 3-4 + heuristic); 2026-04-22 session 11 (Case 6); 2026-04-22 session 12 (Case 7 size-cap silent violation); 2026-04-22 session 13 (Case 8 synthetic data silent PASS + stop sign 방어책)
