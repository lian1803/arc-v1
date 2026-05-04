---
date: 2026-04-21
domain: development
severity: high
root_cause_category: deploy-blind-spot / silent-pass-on-first-deploy
recorded_from: seeded from Cloudflare docs + community tutorials (pre-incident; DOCTRINE §8 verifier grep target)
verified_by: seed-by-seoyeon (Cloudflare docs accessed 2026-04-21; extension protocol §Pattern 5+ awaits real incidents)
---

# Cloudflare Deploy — Common Pitfalls (Seed) — 2026-04-21 Session 10

**Scope:** pre-seeded from Cloudflare docs to prevent silent pass on known pitfalls at first real deploy. Extend per real incident (append-only per DOCTRINE §6).

**Why seed, not wait for real incidents:** failure-memory grep (agent_template.md §Failure-Memory Check, DOCTRINE §8) finds nothing on empty archive. First deploy with no memory = full blind. Community tutorials + Cloudflare docs already enumerate these 4 patterns — seeding them costs ~160 LOC and prevents 4 classes of silent pass. This file's claims are grounded in Cloudflare's own documentation; it is NOT a record of a real incident yet. First real-incident entry will be appended as §Pattern 5+ below (Extension Protocol).

**Relation to `cloudflare_recipes.md`:** the recipes file is the positive template ("how to deploy"). This file is the negative template ("how deploys silently break"). Verifiers must grep BOTH before passing a deploy artifact.

---

## Pattern 1 — wrangler version / compat_date mismatch

- **Pattern:** local `wrangler` CLI version ships a config schema / compat_date window that disagrees with the project's `wrangler.toml`, so `wrangler deploy` either silently applies a stale runtime or rejects unsupported fields.
- **Concrete example (docs-grounded):** Cloudflare docs state "As of Wrangler v3.91.0 Wrangler supports both JSON (`wrangler.json` or `wrangler.jsonc`) and TOML (`wrangler.toml`) for its configuration file" — a project authored on v3.91+ using `wrangler.jsonc` will fail to parse on an older wrangler pinned in CI. Similarly, docs instruct "When you start your project, you should always set `compatibility_date` to the current date" — a `compatibility_date` newer than the local wrangler's bundled runtime table is an undefined / silently-downgraded state (docs do NOT enumerate the error text; forward-compat handling is unaddressed in the compat-date reference).
- **Detection signal:** `wrangler deploy` emits config-parse errors on unknown fields, OR deploy succeeds but runtime behavior diverges from local `wrangler dev`. `Community-reported:` silent downgrade to older compat behavior when compat_date > local wrangler's release date — not explicitly documented in the compat-date reference page as of access 2026-04-21.
- **Prevention:** Pin `wrangler` to a version in `package.json` / `pyproject.toml` devDependencies. Preflight: `npx wrangler --version` must be `>=` the version documented in `shared/knowledge/cloudflare_recipes.md`. Bump compat_date only when local wrangler is also bumped; never push a future-dated compat_date.

## Pattern 2 — D1 local-vs-remote confusion

- **Pattern:** `wrangler d1` commands default-route to a target that the operator did not intend, so migrations applied locally never reach production (or vice versa — prod gets an ad-hoc manual migration that diverges from `migrations/`).
- **Concrete example (docs-grounded):** Cloudflare D1 docs define `--local` as "Execute commands/files against a local DB for use with wrangler dev" and `--remote` as "Execute commands/files against a remote D1 database for use with remote bindings or your deployed Worker". Both `wrangler d1 execute` and `wrangler d1 migrations apply` accept the flag pair. Running `wrangler d1 migrations apply DB` without a flag → operator assumes "it migrated" → deploy later fails because prod schema is still empty.
- **Detection signal:** deployed Worker errors `D1_ERROR: no such table: <name>` (or similar) despite `wrangler d1 migrations apply` running green locally. `not verified at 2026-04-21 — docs do not specify the default flag behavior`: "The documentation does not specify a default target (local or remote) when neither `--local` nor `--remote` flags are provided" (verbatim from fetch, access 2026-04-21). Do NOT assume either default — always pass the flag.
- **Prevention:** ARC convention — every `wrangler d1` invocation in a script or runbook MUST specify `--local` or `--remote` explicitly. No bare `wrangler d1 migrations apply DB`. After every `--remote` apply, follow with `wrangler d1 execute DB --remote --command "SELECT name FROM sqlite_master WHERE type='table'"` to prove schema landed. `Community-reported:` local state stored under `.wrangler/state/` directory — not confirmed in the d1 wrangler-commands doc page fetched 2026-04-21; treat as folk knowledge pending doc grounding.

## Pattern 3 — Pages build timeout with OpenNext / Next.js

- **Pattern:** Cloudflare Pages build job exceeds the platform build window (cap exists; exact minutes not surfaced on the build-configuration page fetched 2026-04-21) on heavy Next.js builds — typical failure mode on first deploy of an OpenNext-adapted Next.js app with image optimization + cold cache.
- **Concrete example (docs-grounded):** Pages build-configuration docs list Next.js presets: `npx @cloudflare/next-on-pages@1` → output dir `.vercel/output/static`, OR `npx next build` → output dir `out` (static export). First run has no build cache, so pnpm install + Next compile + next-on-pages adapter all run serially. `not verified at 2026-04-21 — fetch failed to surface the numeric timeout`: the build-configuration page fetched did not state "20 minutes" or any specific minute-cap (the 20min figure in the task prompt is `Community-reported:` and not grounded at the page fetched).
- **Detection signal:** Pages build log ends mid-compile with a timeout message (exact text not confirmed from the page fetched; verify at real-incident time). Build succeeds locally via `npx @cloudflare/next-on-pages@1` but fails in CI.
- **Prevention:** Before first Pages deploy, time the full build locally: `time npx @cloudflare/next-on-pages@1` — if >10 min locally, either (a) trim image-optimization scope, (b) split routes to smaller Workers, or (c) pre-build locally and deploy prebuilt artifacts via `wrangler pages deploy ./dist`. Log the preflight duration to `shared/knowledge/cost_log.jsonl` for every project's first deploy.

## Pattern 4 — KV namespace ID mismatch preview vs prod

- **Pattern:** `[[kv_namespaces]]` entry has `id` (production) but missing or incorrectly-set `preview_id`, so `wrangler dev --remote` either errors on missing preview_id or — worse — silently reuses `id` and dev-mode writes corrupt production KV.
- **Concrete example (docs-grounded):** wrangler configuration docs define `id` as "The ID of the KV namespace" (required) and `preview_id` as "The preview ID of this KV namespace. This option is **required** when using `wrangler dev --remote`." (verbatim). Fallback rule verbatim: "If developing locally, this is an optional field. `wrangler dev` will use this ID for the KV namespace. Otherwise, `wrangler dev` will use `id`." → if the operator forgets `preview_id` and runs plain `wrangler dev`, dev writes fall through to the prod `id`.
- **Detection signal:** `wrangler dev --remote` fails outright with preview_id-required error (exact text not surfaced in the fetched doc section; confirm at incident time). Silent-fail variant: plain `wrangler dev` succeeds but KV reads in dev return values the operator does not remember seeding → dev was reading prod.
- **Prevention:** ARC convention — every `[[kv_namespaces]]` block in any project's `wrangler.toml` MUST declare both `id` and `preview_id`, pointing to DIFFERENT namespaces. Preflight grep: `grep -A3 'kv_namespaces' wrangler.toml | grep -c '_id'` must equal `2 * (number of kv_namespaces blocks)`. Same rule extends to `[[d1_databases]]` and `[[r2_buckets]]` preview fields (not yet grounded in this file; add when real-incident data lands).

---

## Extension Protocol

Every real deploy failure in `projects/*/development/` adds a new `## Pattern N — {slug}` section here, following the 4-line template (Pattern / Example / Detection / Prevention). Owner: 태민 (deploy_engineer, Phase 3+ agent per `parts/development/CLAUDE.md` roster — not yet instantiated as of 2026-04-21 session 10). Until 태민 exists, Seoyeon is the interim author.

Real-incident entries MUST include:
- `**Incident date:**` actual failure date (not seed date 2026-04-21).
- `**Project:**` `projects/{name}/` path.
- `**Source log:**` link to the deploy log / error output in-repo (NOT a paraphrase).
- `**Status:**` `verified` (grounded in captured log) vs `post-mortem-hypothesis` (reconstructed after the fact).

Remove or downgrade seeded patterns only if a real incident produces a contradicting grounded finding — never to "clean up".

---

## Sources

All URLs accessed 2026-04-21.

- Pattern 1 — https://developers.cloudflare.com/workers/wrangler/configuration/ (wrangler.toml spec, v3.91.0 JSON/TOML note) + https://developers.cloudflare.com/workers/configuration/compatibility-dates/ ("current date" guidance; no forward-compat error doc). Fetch status: both SUCCESS with partial coverage (no explicit error text surfaced).
- Pattern 2 — https://developers.cloudflare.com/d1/wrangler-commands/ (`--local` / `--remote` flag definitions, default behavior undefined). Fetch status: SUCCESS with partial (`.wrangler/state/` path absent from page).
- Pattern 3 — https://developers.cloudflare.com/pages/configuration/build-configuration/ (Next.js presets: `@cloudflare/next-on-pages@1` + `.vercel/output/static`). Fetch status: PARTIAL — page did not surface numeric build timeout; 20min figure downgraded to `Community-reported:`.
- Pattern 4 — https://developers.cloudflare.com/workers/wrangler/configuration/#kv-namespaces (`id` required, `preview_id` required for `--remote`, fallback rule verbatim). Fetch status: SUCCESS after primary KV bindings URL (https://developers.cloudflare.com/kv/api/workers-kv-bindings/) returned HTTP 404; recovered via the configuration-page anchor.

Fetch failures logged to `shared/knowledge/cost_log.jsonl` (2026-04-21 session 10 seed, tool=webfetch, cost_usd=0.0).

**Verifier grep note (DOCTRINE §8):** on every deploy-related verification, grep this file for the 4 pattern headers. Any deploy artifact that touches `wrangler.toml`, `[[kv_namespaces]]`, `[[d1_databases]]`, or a Pages build-command must be cross-checked against the Prevention line of the matching pattern. Missing preflight evidence → REVISE blocker.
