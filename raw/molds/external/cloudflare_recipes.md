---
name: cloudflare_recipes
description: Canonical wrangler + D1 + KV + R2 + Pages recipes for ARC development agents; includes known failure modes.
source: Cloudflare official docs (see source_urls); OpenNext docs; community reports.
source_urls:
  - https://developers.cloudflare.com/pages/framework-guides/nextjs/ssr/get-started/
  - https://developers.cloudflare.com/d1/get-started/
  - https://developers.cloudflare.com/kv/get-started/
  - https://developers.cloudflare.com/r2/api/workers/workers-api-usage/
  - https://opennext.js.org/cloudflare/get-started
authored_by: seoyeon (development strategy-lead delegate)
verified_by: eunho-verifier_20260421_session10_m2 (37/40 PASS)
orchestrated_by: seoyeon
created_at: 2026-04-21
last_reviewed: 2026-04-21
---

# Cloudflare Recipes — wrangler / D1 / KV / R2 / Pages

> Single source of truth for ARC Cloudflare infra commands. `deploy_engineer.md` reads this first.
> All URLs live-fetched 2026-04-21. Re-verify if `last_reviewed` > 90 days old.

## 1. Stack Choice (frozen per decisions/2026-04-21_system-bootstrap.md §4)

- **Runtime**: Cloudflare Workers (not Pages Functions — Cloudflare's Next.js guide as of 2026-04-21 moved to Workers + `@opennextjs/cloudflare` adapter; `next-on-pages` is deprecated).
- **Data**: D1 (SQLite-compatible) for relational, KV for cache/session tokens, R2 for objects/files.
- **Deploy**: `wrangler` CLI only. `wrangler@^3.x` pinned in `package.json`.

## 2. wrangler.toml / wrangler.jsonc — minimal template

For a Next.js app deployed via `@opennextjs/cloudflare` (source: opennext.js.org/cloudflare/get-started), the canonical config is `wrangler.jsonc`:

```jsonc
{
  "main": ".open-next/worker.js",
  "name": "arc-project-slug",
  "compatibility_date": "2024-12-30",
  "compatibility_flags": ["nodejs_compat", "global_fetch_strictly_public"],
  "assets": { "directory": ".open-next/assets", "binding": "ASSETS" }
}
```

For plain Worker projects without Next.js, use `wrangler.toml`:

```toml
name = "arc-project-slug"
main = "src/index.ts"
compatibility_date = "2024-12-30"

[[d1_databases]]
binding = "DB"
database_name = "arc-project-slug-db"
database_id = "REPLACE_WITH_D1_ID"

[[kv_namespaces]]
binding = "CACHE"
id = "REPLACE_WITH_KV_PROD_ID"
preview_id = "REPLACE_WITH_KV_PREVIEW_ID"

[[r2_buckets]]
binding = "ASSETS_BUCKET"
bucket_name = "arc-project-slug-assets"

[env.preview]
[env.production]
```

**Rationale:** dual-env (`preview` + `production`) is mandatory per `deploy_engineer.md §Constraints` — single-env deploy = auto REWRITE.

## 3. D1 — create DB + run migrations

```bash
npx wrangler@latest d1 create arc-project-slug-db    # paste database_id into wrangler.toml
npx wrangler d1 execute arc-project-slug-db --local  --file=./migrations/0001_init.sql   # ALWAYS local first
npx wrangler d1 execute arc-project-slug-db --remote --file=./migrations/0001_init.sql   # only after local passes
```

**Forward-only migrations:** `0001_init.sql`, `0002_*.sql`, never re-ordered. D1 remote DDL lacks reliable transactional rollback — `deploy_engineer.md` forbids down-migrations.

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch())
);
```

## 4. KV — namespace + binding

```bash
npx wrangler kv namespace create CACHE             # → id = production
npx wrangler kv namespace create CACHE --preview   # → preview_id
```

Put both `id` and `preview_id` into `[[kv_namespaces]]` (see §2). Access: `env.CACHE.put(k, v)` / `env.CACHE.get(k)`. **Caveat:** KV is eventually consistent (~60s); not for read-your-writes (use D1).

## 5. R2 — bucket + binding

```bash
npx wrangler r2 bucket create arc-project-slug-assets
```

Binding shown in §2. Access: `env.ASSETS_BUCKET.put(key, body)` / `env.ASSETS_BUCKET.get(key)`.

## 6. Next.js on Workers — deploy via OpenNext

Cloudflare's Next.js framework guide (as of 2026-04-21) redirects to the OpenNext adapter.

```bash
npx @opennextjs/cloudflare migrate                   # one-time bootstrap for existing app
# OR
npm install @opennextjs/cloudflare@latest && npm install --save-dev wrangler@latest
# package.json scripts:
#   "preview": "opennextjs-cloudflare build && opennextjs-cloudflare preview"
#   "deploy":  "opennextjs-cloudflare build && opennextjs-cloudflare deploy"
npm run preview    # local edge-accurate preview
npm run deploy     # ships to Cloudflare Workers
```

**Observation (per DOCTRINE §5 label):** older `@cloudflare/next-on-pages` is deprecated — remove `setupDevPlatform()` calls on migration.

## 7. Secrets (never commit)

```bash
npx wrangler secret put CF_API_TOKEN     # prompted, stored encrypted; listed in dashboard, never in repo
```
Access: `env.CF_API_TOKEN`.

## 8. Common Failure Modes (verifier grep-targets)

| Failure | Symptom | Root cause | Fix |
|---|---|---|---|
| Binding name mismatch | 500, no stacktrace | `env.USERS_KV` in code but wrangler binding is `USER_KV` | Exact-match rename on both sides; add CI grep check |
| Local vs remote D1 drift | "works local, 500 remote" | Migration ran local only, forgot `--remote` | Runbook: local then remote, both logged to cost_log.jsonl |
| Preview vs production namespace swap | Session data missing in prod | `id` / `preview_id` swapped | Copy-paste wrangler output directly; never hand-type |
| Wrangler version mismatch | Build passes locally, fails CI | `wrangler@latest` floats past breaking change | Pin `wrangler@^3.x` in package.json |
| Pages build timeout | Deploy stalls > 20 min | Large image assets in `public/` | Move to R2, reference via binding |
| `nodejs_compat` missing | `ReferenceError: process is not defined` | Compat flag not set | Add `"nodejs_compat"` to `compatibility_flags` |
| CF_API_TOKEN scope too narrow | `AuthenticationError: 10001` | Token missing Pages:Edit or D1:Edit | Recreate token with Account-level Workers+D1+KV+R2 edit perms |

## 9. Non-Goals + Devil's Advocate

- **Non-Goals:** no AWS/Vercel/Supabase fallback (decisions §4); no Pages-Functions-only recipe (deprecated); no multi-region strategy (global-edge by default); no custom-domain DNS walkthrough (Lian handles in dashboard).
- **Weakness 1:** Cloudflare-only = vendor lock. Pricing > 3× or outage > 4h on revenue re-opens `decisions/2026-04-21_system-bootstrap.md §Change Conditions`.
- **Weakness 2:** OpenNext is third-party. Next.js release may break it first. Mitigation: pin `next` + test `preview` before `deploy`.

