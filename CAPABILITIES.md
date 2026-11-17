---
updated: YYYY-MM-DD
section: C
---
# FitLib — Project Capabilities

**Audit date:** 2026-05-08
**Source of truth:** filesystem inspection of `/Users/enes/fitlibvault-main` and the live build artifacts in `web app fitlib/public/content/`.
**Scope:** what this codebase can actually do today. Aspirational targets live in `web app fitlib/docs/{ROADMAP.md,VISION.md,KPIs.md}`.

This document is the single best place to start if you want to understand the system end-to-end. Each section names the concrete files and entry points.

---

## 1. Project shape

FitLib is three layers stacked on the same vault:

1. **Content vault** — an Obsidian-style markdown library (`/Users/enes/fitlibvault-main/*.md` plus `organized_library/`).
2. **Automation pipeline** — Python scripts under `organized_library/automation_tools/` that rewrite notes with PubMed-backed evidence, validate citations, validate wikilinks, and promote rewrites into the vault.
3. **Web app** — a React 19 + Vite SPA (`web app fitlib/`) served by an Express backend; reads its content from a static JSON bridge generated from the vault, persists user state in Firebase, and bills via Stripe.

Each layer is independently runnable. The pipeline produces vault notes. The vault produces a content bridge. The bridge feeds the SPA.

---

## 2. Content vault (current contents)

Authoritative numbers from `fitlib_export.json` (re-exported 2026-05-08T16:15Z) and `stats.json`:

| Metric | Value |
|---|---|
| Notes published to web app | **678** |
| Citations attached | **985** |
| Wikilinks resolved | **5,568** |
| Cloze cards generated | **508** (covering 41.7% of nodes) |
| Evidence entries (graded) | 1,411 (High 1,109 / Medium 260 / Low 0 / Unknown 42) |
| Broken wikilinks (last extract) | 542 |

Vault structure:

| Layer | Path | Notes |
|---|---|---|
| Letter sections (root) | `*.md` at repo root | 18 sections (A–X), **575** subnotes total |
| Sorted views | `organized_library/<topic>/` | 25 topical folders, **946** notes (duplicate of root, sorted by domain) |
| Exercise library | `organized_library/exercise_library/` | **101** exercise notes (`EXL-01` … `EXL-101`) |
| Key overviews | `organized_library/key_overviews/` | 9 high-level Q-series summaries |
| Long-term development | `organized_library/long_term_development/` | 11 N-series notes |
| Original backups | `organized_library/original_backup/` | 331 timestamped pre-rewrite copies |
| Processed staging | `organized_library/processed_archive/processed_notes/` | 235 `rewritten_*.md` and section reports |
| Confirmed promotion archive | `organized_library/processed_archive/confirmed_archive/` | Per-day folders of promoted rewrites (354 entries dated 2026-05-08) |

Top-level letter section coverage:

| Section | Title | Count |
|---|---|---|
| A | Foundational Concepts | 65 (A1–A65) |
| B | Resistance Training | 70 (B1–B78) |
| C | Nutrition & Diet | 106 (C1–C105) |
| D | Weight Management | 3 (D1–D3) |
| E | Cardiovascular / Endurance | 15 (E1–E14) |
| F | Optimal Performance Factors | 34 (F1–F33) |
| G | Special Populations | 16 (G1–G16) |
| H | Body Composition | 3 (H1–H3) |
| I | Hormones & Fitness | 3 (I1–I3) |
| J | Technology in Fitness | 10 (J1–J10) |
| K | Elite Performance | 12 (K1–K12) |
| L | Cross-Training & Functional | 4 (L1–L4) |
| M | Recovery Strategies | 10 (M1–M9) |
| N | Long-Term Development | 10 (N1–N10) |
| O | Integrated Approaches | 8 (O1–O8) |
| P | Ethical Considerations | 10 (P1–P10) |
| Q | Key Topic Overviews | 8 (Q1–Q7) |
| X | Sports-Specific Training | 30 (X1–X20) |

Each promoted note follows a fixed schema (parser: `web app fitlib/src/lib/noteSchema.ts`):

- **Quick Takeaway** — single-paragraph TL;DR
- **Key Points** — bulleted bottom-line claims (used to generate cloze cards)
- **Deep Dive** — long-form mechanistic exposition
- **Research Evidence** — graded citation list (High / Medium / Low quality)
- **Practical Applications** — actionable guidance
- **Common Mistakes** — pitfalls callouts (rendered as warning blocks in the reader)
- **Related Concepts** — outbound `[[wikilinks]]`

---

## 3. Web app — what the SPA can do today

**Path:** `web app fitlib/`
**Stack:** React 19, Vite 6, TypeScript 5.8, Express 4, Tailwind v4, react-router-dom 7.
**Entrypoints:** `server.ts` (dev + prod server), `src/main.tsx` (SPA), `vite.config.ts` (build).

### 3.1 Pages and routes (from `src/App.tsx`)

| Route | Component | What it shows |
|---|---|---|
| `/` | `pages/Landing.tsx` | Hero, live library counters, four pedagogy pillars, CTAs to Library and About |
| `/library` | `pages/Library.tsx` | Main reading surface — three view modes (Reader / Graph / Cards), sidebar explorer, paywall enforcement |
| `/dashboard` | `pages/Dashboard.tsx` | Learner mission control — due cards, recent, favourites, FSRS stats, Google sign-in, admin importer |
| `/about` | `pages/About.tsx` | Transparency page — evidence-quality breakdown, series breakdown, links back into the library |

### 3.2 Reader system (`StackedReader` mode)

`src/components/StackedReader.tsx` implements horizontally-scrolling stacked panels (Andy-Matuschak style). State is encoded in the URL: `?stack=A1,A2,A3` opens A1, A2, A3 side by side. Hook: `src/lib/noteStack.ts` (`useNoteStack()`).

Per-note rendering by `src/components/NoteReader.tsx`:

- Section-aware markdown rendering driven by `parseNoteSections()` (`src/lib/noteSchema.ts`)
- Evidence pills (High / Medium / Low / Unknown) via `EvidencePill.tsx`
- Common-mistake callouts (warning blocks) via `NoteReader`
- Wikilink interception — clicks open in the next stack column instead of navigating away
- Hover preview popover via `NoteHoverCard.tsx` (180 ms enter delay)
- Recall block at the bottom (active retrieval) via `RecallSection.tsx`

### 3.3 Graph view (`KnowledgeGraph` mode)

`src/components/KnowledgeGraph.tsx` — D3 force simulation over the full link graph. Nodes coloured by series (A/B/C/E/Other), zoom/pan, neighbour-dimming on hover, click-to-open in the reader. Background ambient version (`AmbientGraph.tsx`) caches its layout to localStorage so the home page renders instantly on repeat visits.

### 3.4 Card view (active recall + spaced repetition)

| Module | File | Behaviour |
|---|---|---|
| Card generator | `src/lib/clozeGen.ts` | Pulls Key-Point sentences and converts numeric ranges (×5), percentages/quantities (×4), acronyms (×3), and noun phrases (×1) into fill-in-the-blank cards. Stable IDs via FNV-1a hash of (nodeId, index, span, point) so review history survives rebuilds. |
| Scheduler | `src/lib/srs.ts` | FSRS-4 (`ts-fsrs` package). `request_retention: 0.9`, `maximum_interval: 365`. Persists review history in IndexedDB via Dexie (`fitlib-srs` store). |
| Recall surface | `src/components/RecallSection.tsx` | Bottom-of-note "test yourself" block — input → check → grade → schedule. Records review through `recordReview()`. |
| Aggregate stats | `src/lib/srs.ts::getLearnerStats()` | Drives the dashboard widgets (cards due, reviewed in last 7d, retention rate). |

### 3.5 Auth, paywall, payments

| Concern | File(s) | What it does |
|---|---|---|
| Firebase Auth (Google sign-in) | `src/lib/firebase.ts`, `pages/Dashboard.tsx`, `pages/Library.tsx` | One-click Google OAuth; auth state drives library access |
| Admin allowlist | `src/lib/admin.ts` | `isAdminEmail()`, `isAdminUser()`. Sources: `VITE_ADMIN_EMAILS` env, `VITE_DEV_ADMIN=true`, dev mode |
| Paywall gating | `pages/Library.tsx`, `components/PremiumPaywall.tsx` | Free users see 5 nodes; admins / premium see all |
| Stripe checkout | `src/lib/stripeService.ts` → `POST /api/create-checkout-session` | Monthly + annual price IDs in `PREMIUM_TIER` constant |
| Subscription verify | `verifySubscription()` → `GET /api/check-subscription` | Server reads Firestore `users/{uid}.premium` |
| Webhook | `server.ts` `POST /api/stripe/webhook` | Handles `checkout.session.completed`, `customer.subscription.deleted`, `customer.subscription.paused`. Raw-body parsing (must precede `express.json()`). |

### 3.6 Express backend (`server.ts`)

Nine routes, all production-wired:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check incl. Firestore connectivity |
| GET | `/api/nodes` | List nodes (filter: category, series, limit, search) |
| GET | `/api/nodes/:id` | Single node + citations subcollection |
| GET | `/api/users/:userId/progress` | Completed nodes, favourites, study streak, total reading time |
| POST | `/api/users/:userId/progress` | Record `complete` / `favorite` / `unfavorite`; updates streak via Firestore transaction |
| POST | `/api/create-checkout-session` | Stripe checkout session for a price ID |
| GET | `/api/check-subscription` | Premium status by user ID |
| GET | `/api/analytics/:userId` | Completion rate, study streak, per-series progress |
| POST | `/api/stripe/webhook` | Stripe lifecycle handler |

Required env vars: `PORT`, `NODE_ENV`, `FIREBASE_SERVICE_ACCOUNT_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`. Vite middleware in dev, static serving + SPA fallback in prod.

### 3.7 Persistence model

Two backends, used in parallel:

- **Static content bridge** (read path) — `web app fitlib/public/content/{index.json,nodes/<id>.json,cards.json,cards/<id>.json,series/<series>.json,stats.json}`. The SPA reads from this first; Firestore is fallback.
- **Firestore** (write path + auth state) — collections defined by `firestore.rules`:
  - `nodes/{id}` (public read, admin write) and `nodes/{id}/citations/{cid}`
  - `users/{uid}` (owner-write with field whitelist)
  - `userProgress/{uid}` (owner-write)
  - `admins/{aid}` (allowlist for `isAdmin()` rule)
- **IndexedDB (Dexie)** — `fitlib-srs` store for FSRS review history (local-only; no cross-device sync today).
- **localStorage** — favourites, recently-viewed, ambient-graph layout cache, theme.

### 3.8 Search

- **Local search** — `src/lib/algoliaService.ts` is fully wired (`AlgoliaSearchService` singleton, faceted search). Activates only when `VITE_ALGOLIA_APP_ID` + `VITE_ALGOLIA_SEARCH_KEY` + `VITE_ALGOLIA_INDEX_NAME` are set. Without them the app falls back to in-memory text matching over `index.json`.

### 3.9 Build pipeline (`scripts/`)

| Script | Inputs | Outputs |
|---|---|---|
| `extractVault.ts` | `FITLIB_VAULT_PATH` (default: parent of web app dir) | `fitlib_export.json` (full vault dump with frontmatter, wikilinks, citations) |
| `buildContentBridge.ts` | Vault scan + `extractVault()` | `public/content/index.json`, `public/content/nodes/<id>.json`, `public/content/series/<S>.json`, `public/content/stats.json`. Calls `buildClozeCards` at the end. |
| `buildClozeCards.ts` | Per-node JSON files | `public/content/cards.json` + `public/content/cards/<id>.json` |
| `importData.ts` | `fitlib_export.json` | Firestore — batched (450 ops) writes to `nodes/{id}` and `nodes/{id}/citations/{cid}`. Requires `FIREBASE_SERVICE_ACCOUNT_KEY`. |

`npm run content:build` runs the bridge; `npm run build` runs `content:build` then `vite build`.

### 3.10 Deployment surfaces

- **Vercel** — `vercel.json` (SPA rewrite to `index.html`); deployment doc in `docs/VERCEL_DEPLOYMENT_CHECKLIST.md`.
- **Docker** — multi-stage `Dockerfile` (Node 18-alpine, non-root `fitlib:nodejs`, `/api/health` healthcheck, port 3000) and `docker-compose.yml` (`fitlib-app` plus optional `redis` and `prometheus` profiles).
- Built artefacts already exist in `web app fitlib/dist/` (last build present).

### 3.11 Declared but unused

- `@google/genai` — listed as a dependency, no source file imports it. Reserved for future AI features.
- `code` and `claude` packages — listed but unused.

---

## 4. Automation pipeline — what it can do today

**Path:** `organized_library/automation_tools/`
**Primary entry point:** `automation_scripts/seamless_update_pipeline.py`
**Promotion history:** `automation_tools/promotion_history.jsonl` (354 promotions on 2026-05-08).

### 4.1 The seven-phase pipeline

```
process_fitness_library.py    →  rewrite (PubMed + Claude)
citation_validation_audit.py  →  HTTP-validate every DOI/PMID
citation_doi_fixer.py         →  suggest keep / normalize / remove for broken DOIs
interlink_validator.py        →  classify every [[wikilink]] (ok / stub / shadowed / broken)
promote_rewritten_to_og.py    →  dry-run promotion (sanity gate)
staged_promotion.py           →  per-file y/s/d/q with date stamping + JSONL audit
npm run content:build         →  rebuild static bridge for the SPA
```

`seamless_update_pipeline.py` is the path-stable orchestrator that runs this end-to-end with flags:

```bash
python3 organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py \
  --section A --start-num 1 --end-num 65 \
  --validate-interlinks --interlink-fail-on broken \
  --apply --staged-apply \
  --build-content
```

Resumable via `--refresh-only-stale --stale-days 14`. Range filters: `--section`, `--start-num`, `--end-num`, `--exclude-name-prefix`, `--resume-from-name`.

### 4.2 Phase capabilities in detail

**Rewrite (`processing_scripts/process_fitness_library.py`)**

- Loads a vault note, extracts ID, section letter, existing citations.
- Queries PubMed eUtils with the title + a section-domain hint (A → exercise physiology, C → sports nutrition, …) plus auto-extracted keywords.
- Filters to humans + RCT / Meta-Analysis / Systematic Review / Clinical Trial.
- Ranks studies by `0.5 × quality + 0.3 × relevance + 0.2 × recency` with tunable gates: `--min-relevance`, `--min-quality`, `--top-studies` (default 5), `--lookback-years` (default 4).
- Caches PubMed results under `.cache/` keyed by query.
- Sends top studies + the original note to Claude and asks for a rewrite that conforms to the fixed template (Quick Takeaway → Key Points → Deep Dive → Research Evidence → Practical → Mistakes → Related).
- Writes `rewritten_<original-filename>.md` to `processed_archive/processed_notes/`.
- Logs to `fitness_library_processing.log`.

**Citation audit (`utility_scripts/citation_validation_audit.py`)**

- Walks `rewritten_*.md`, extracts every DOI and PMID via regex.
- Concurrent HTTP HEAD/GET to `https://doi.org/<doi>` and `https://pubmed.ncbi.nlm.nih.gov/<pmid>/` (default 12 workers, 10 s timeout).
- Emits `citation_audit_report.json` (per-file summary) and `citation_audit_links.csv` (row per link with status).

**DOI fixer (`utility_scripts/citation_doi_fixer.py`)**

- Reads the audit report, retries failing DOIs with normalized variants.
- Emits `citation_doi_fix_suggestions.json` with `keep` / `normalize` / `remove_or_replace` actions per citation.
- Read-only — never modifies files. Suggestions are surfaced to the operator during `staged_promotion.py`.

**Interlink validator (`utility_scripts/interlink_validator.py`)**

- Scans every `[[wikilink]]` in the chosen scope (`vault`, `rewritten`, or `organized`).
- Classifies each as `ok`, `stub` (target exists but is too short to count as content), `shadowed` (multiple files share that name), or `broken`.
- Emits `interlink_audit_report.json`, human-readable `interlink_audit.md`, and an optional CSV.
- Can gate promotion via `--fail-on broken` or `--fail-on any`.

**Promotion validate (`automation_scripts/promote_rewritten_to_og.py` without `--apply`)**

- Bulk dry-run: prints how many `rewritten_*.md` files have a matching OG file at the vault root.

**Promotion apply (`automation_scripts/staged_promotion.py --interactive`)**

For each rewritten file the operator gets `[y]es / [s]kip / [d]iff / [q]uit`. On accept the script:

1. Stamps the OG note with `(Updated: YYYY-MM-DD)` in the title.
2. Appends a one-line `## Update Log` entry with citation deltas.
3. Atomically replaces the OG file (write-temp → fsync → rename).
4. Moves the rewritten source into `processed_archive/confirmed_archive/<YYYY-MM-DD>/` so it cannot be re-promoted.
5. Appends a JSONL row to `automation_tools/promotion_history.jsonl` (timestamp, ID, file, citation deltas, archive path).

`--auto-yes` is supported for headless full-section runs.

**Website rebuild (`--build-content` flag)**

- `seamless_update_pipeline.py` shells out to `npm run content:build` inside `web app fitlib/`, regenerating the static bridge that the SPA reads.

### 4.3 Active vs legacy scripts

The active production set (the only scripts wired into the recommended SOP):

```
automation_scripts/seamless_update_pipeline.py   primary orchestrator
automation_scripts/staged_promotion.py           per-file confirmed promotion
automation_scripts/promote_rewritten_to_og.py    bulk fallback / dry-run
processing_scripts/process_fitness_library.py    rewrite engine (PubMed + Claude)
utility_scripts/citation_validation_audit.py     DOI/PMID HTTP audit
utility_scripts/citation_doi_fixer.py            DOI fix suggestions
utility_scripts/interlink_validator.py           wikilink integrity
```

The conditional set (work in some setups, not in current SOP):

```
automation_scripts/master_automation.py          older batch orchestrator
automation_scripts/run_complete_automation.py    path-fragile orchestrator
processing_scripts/ultra_optimized_processor.py  token-saving prompt builder (used by run_complete_automation)
monitoring_scripts/research_discovery.py         multi-API search (PubMed + CrossRef + Semantic Scholar)
validation_scripts/quality_scorer.py             GRADE/bias quality scorer
validation_scripts/validate_citations.py         older variant of the audit
```

The legacy set (kept for reference; not reachable from the SOP):

```
analysis_tools.py, enhanced_depth_processor.py, organize_fitness_library.py,
replace_with_rewritten.py, automation_pipeline.py,
processing_scripts/{content_enhancer.py, expert_content_processor.py,
  local_template_processor.py, manual_enhanced_processor.py, process_remaining_b.py},
monitoring_scripts/{api_cost_monitor.py, cost_controlled_processor.py, monitoring.py},
validation_scripts/citation_validator.py,
utility_scripts/{config.py (referenced only), database.py (unused),
  update_links_for_organization.py},
test_scripts/{demo_test.py, simple_test.py, test_suite.py}
```

See `automation_tools/tools/SCRIPT_STATUS.md` for a row-per-script status matrix.

### 4.4 What the pipeline does NOT do

- **Cost gating** — `api_cost_monitor.py` exists but is not wired into the SOP. Operators must manage Anthropic spend externally.
- **Database persistence** — `utility_scripts/database.py` exists but is unused. All artefacts are flat files.
- **Alerting / monitoring** — `monitoring_scripts/monitoring.py` is sophisticated but inactive.
- **CI** — there is no GitHub Actions / pre-commit hook today. Tests in `test_scripts/test_process_fitness_library_phase1.py` and `test_suite.py` are only run manually.

---

## 5. Documentation surface

| Path | Role |
|---|---|
| `CAPABILITIES.md` (this file) | What the project can do today |
| `CHANGELOG_DOCS_2026-05-08.md` | What this audit changed |
| `web app fitlib/README.md` | Web app developer quickstart |
| `web app fitlib/INTEGRATION.md` | Reader / SRS / cloze module wiring guide |
| `web app fitlib/docs/README.md` | Docs index for the web app's operating system |
| `web app fitlib/docs/VISION.md` | 3-year goals (aspirational) |
| `web app fitlib/docs/BUSINESS_MODEL.md` | Pricing tiers, gross margin, unit economics |
| `web app fitlib/docs/MARKET_ANALYSIS.md` | Competitor landscape, positioning |
| `web app fitlib/docs/ROADMAP.md` | Quarter-by-quarter plan (aspirational) |
| `web app fitlib/docs/KPIs.md` | Tracked metrics + targets (mostly aspirational) |
| `web app fitlib/docs/DEVELOPMENT_PROGRESS.md` | Build status — what is shipped vs in progress |
| `web app fitlib/docs/AI_ASSISTED_MANAGEMENT.md` | How the operator uses AI for weekly reviews |
| `web app fitlib/docs/SOP_CONTENT.md` | How to author / improve a single note |
| `web app fitlib/docs/SOP_EXTRACTION.md` | How `extractVault.ts` works and how to run it |
| `web app fitlib/docs/SOP_KNOWLEDGE_READER_SYSTEMS.md` | Reader / FSRS / cloze operations |
| `web app fitlib/docs/PRODUCTION_LAUNCH_CHECKLIST.md` | Pre-launch smoke tests |
| `web app fitlib/docs/VERCEL_DEPLOYMENT_CHECKLIST.md` | Vercel-specific deploy steps |
| `web app fitlib/docs/WEEKLY_STANDUP_TEMPLATE.md` | Friday standup template |
| `organized_library/automation_tools/README.md` | Pipeline overview + run order |
| `organized_library/automation_tools/HOW_IT_WORKS.md` | Per-phase mechanics |
| `organized_library/automation_tools/tools/SCRIPT_STATUS.md` | Active / conditional / legacy matrix |
| `organized_library/automation_tools/tools/WORKFLOW.md` | Operator runbook |
| `organized_library/automation_tools/CHANGELOG-*.md` | Pipeline release notes |
| `organized_library/documentation/README.md` | Library docs index |
| `organized_library/documentation/CLAUDE_PROJECT_CONTEXT.md` | Whole-project context primer |

---

## 6. Operating model — how the parts work together

A typical content-update cycle:

1. Operator edits or adds an OG note at the vault root.
2. Operator runs `seamless_update_pipeline.py --section <X> --staged-apply --validate-interlinks --build-content`.
3. The pipeline rewrites with PubMed evidence, validates citations, validates wikilinks, and lets the operator confirm each promotion.
4. Promoted notes overwrite the vault root in place. The static content bridge (`web app fitlib/public/content/`) is regenerated.
5. The next `vite build` ships those changes to Vercel.

A typical learner cycle (web app):

1. Sign in via Google (Firebase Auth).
2. Browse / search / open a note in `StackedReader`.
3. Read → take the recall block at the bottom → cards register in IndexedDB via FSRS.
4. Dashboard surfaces due cards, recently viewed, favourites, streak, retention rate.
5. Free users hit a 5-node paywall and can upgrade through Stripe; admins / premium see everything.

---

## 7. Known constraints (today)

- **Card coverage is 41.7%** — `buildClozeCards` only generates cards for notes whose Key Points contain numeric / acronym / quantitative content. Text-heavy sections produce zero cards.
- **D and F series are folded into "Other"** in the public content bridge — only A, B, C, E series JSON exists in `public/content/series/`. The Library UI still renders all sections; only the precomputed series shards are partial.
- **542 wikilinks are broken** at last extract. `interlink_validator.py` reports the candidates; `staged_promotion.py` is the supported way to address them.
- **FSRS state is local-only.** A learner who switches devices loses their review history. Cross-device sync is roadmap, not built.
- **Algolia is wired but optional.** Without `VITE_ALGOLIA_*` env vars the app uses in-memory text search only.
- **`@google/genai` is declared but unused.** Any AI-assisted features in the live SPA still go through the operator-driven pipeline, not the app.
- **No CI.** Lint, build, and the Phase 1 pytest suite run manually.

---

## 8. Where to go next

- New to the project → read this file, then `web app fitlib/README.md`, then `organized_library/automation_tools/HOW_IT_WORKS.md`.
- Operating the pipeline → `organized_library/automation_tools/tools/WORKFLOW.md`.
- Shipping the app → `web app fitlib/docs/PRODUCTION_LAUNCH_CHECKLIST.md` then `VERCEL_DEPLOYMENT_CHECKLIST.md`.
- Authoring a note → `web app fitlib/docs/SOP_CONTENT.md`.
- Targets and direction → `web app fitlib/docs/VISION.md`, `ROADMAP.md`, `KPIs.md`.
