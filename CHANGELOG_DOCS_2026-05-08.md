# Documentation refresh — 2026-05-08

This changelog covers a project-wide documentation pass requested on 2026-05-08. Every doc in `web app fitlib/docs/`, `web app fitlib/`, `organized_library/automation_tools/`, and `organized_library/documentation/` was audited against the live filesystem and rewritten where it had drifted from reality.

## Why this pass

The project had grown across three independent layers (vault, automation pipeline, web app) and existing docs reflected the state of each layer at different points in time. KPIs and roadmap files described aspirational targets without distinguishing them from shipped capabilities; SOPs described scripts that were no longer the active entry point; the automation README pointed to a 3-phase pipeline while the code had moved to 7 phases.

This pass establishes one consistent picture of *what is built today*, with aspirational targets clearly tagged as such, and adds a single canonical capabilities file at the repo root.

## Source of truth used

- `fitlib_export.json` (re-exported 2026-05-08T16:15Z): 678 nodes, 985 citations, 542 broken wikilinks.
- `web app fitlib/public/content/stats.json`: 678 nodes, 985 citations, 5,568 wikilinks, 508 cloze cards (41.7 % coverage), evidence quality 1,109 High / 260 Medium / 0 Low / 42 Unknown.
- `automation_tools/promotion_history.jsonl`: 354 promotions on 2026-05-08.
- Direct read of every Python script under `automation_tools/` and every TypeScript module under `web app fitlib/src/` and `web app fitlib/scripts/`.

## What changed

### Created (new files)

- `CAPABILITIES.md` — single-pane overview of every capability the project has today, with file paths and entry points. Anchor doc; first stop for new contributors.
- `CHANGELOG_DOCS_2026-05-08.md` — this file.

### Rewritten (replaced contents)

Web app top level:

- `web app fitlib/README.md` — refreshed feature list, exact env-var matrix, full route list, Docker / Vercel commands.
- `web app fitlib/INTEGRATION.md` — light pass to match the seven-phase pipeline language and confirm nothing in the wiring guide has rotted.

Web app `docs/`:

- `docs/README.md` — index now matches the actual files in the folder, distinguishes operating-system docs (KPIs, roadmap, SOPs) from technical-reference docs (production / Vercel checklists, knowledge-reader SOP).
- `docs/SOP_CONTENT.md` — describes the actual 7-section schema enforced by `noteSchema.ts`, the rewrite path through `process_fitness_library.py`, and the staged-promotion handoff.
- `docs/SOP_EXTRACTION.md` — replaces the older "extraction process" narrative with concrete details of `scripts/extractVault.ts` (what it scans, how it parses citations, what JSON it emits) and the build-bridge handoff.
- `docs/SOP_KNOWLEDGE_READER_SYSTEMS.md` — kept structure; updated module paths, FSRS config (`request_retention 0.9`, `maximum_interval 365`), card-coverage reality (41.7 %), and added a section on the limitations (local-only FSRS state, partial series shards).
- `docs/DEVELOPMENT_PROGRESS.md` — replaces the Phase-2-complete snapshot with a current-state inventory: what is shipped, what is wired but inactive (Algolia, `@google/genai`), what is roadmap.
- `docs/PRODUCTION_LAUNCH_CHECKLIST.md` — expanded from 30-line skeleton to the full preflight checklist (env vars, smoke tests, Stripe webhook test, Firestore rules deploy, content bridge regenerate, Vercel deploy verify).
- `docs/ROADMAP.md` — kept the quarter structure but tagged each line item as `[shipped]`, `[in progress]`, `[planned]`, `[stretch]` so it is now usable as a status board.
- `docs/KPIs.md` — every metric now flags `current` (read from `stats.json` / `promotion_history.jsonl` / Firebase) vs `target` (from VISION / BUSINESS_MODEL). No targets were lowered; the framing just stops conflating planned with delivered.
- `docs/AI_ASSISTED_MANAGEMENT.md` — light pass; added a pointer to `WEEKLY_STANDUP_TEMPLATE.md` and a note that the AI loop currently runs through external tools (Cline / Claude Code), not through `@google/genai` in the SPA.

Automation tools:

- `organized_library/automation_tools/README.md` — replaces the 3-phase narrative. New version: full 7-phase pipeline, recommended one-command run, where each artefact lands, link to `tools/SCRIPT_STATUS.md` and `tools/WORKFLOW.md`.
- `organized_library/automation_tools/HOW_IT_WORKS.md` — phase-by-phase mechanics (now matches the script call order in `seamless_update_pipeline.py`); explicit "what we do not do" section listing unwired modules (cost gating, database, monitoring).
- `organized_library/automation_tools/tools/README.md` — expanded one-pager pointer; quick links to the workflow and the status matrix.
- `organized_library/automation_tools/tools/SCRIPT_STATUS.md` — definitive matrix of every Python script in the directory tree (37 files), each tagged `active` / `conditional` / `legacy` / `support` / `test` with the entry-point shape and whether it appears in the active SOP.
- `organized_library/automation_tools/tools/WORKFLOW.md` — refreshed runbook: one-command path, granular per-phase commands, pause/resume strategy, verification checklist, commit-and-push template.

Library documentation:

- `organized_library/documentation/README.md` — replaced auto-categorised file listing with a curated index that mirrors the actual contents (28 docs grouped by purpose: indices, processing reports, frontend prompts, project-context primers).
- `organized_library/documentation/CLAUDE_PROJECT_CONTEXT.md` — refreshed counts and statuses: 678 published nodes, 575 root subnotes, 946 organised-library notes, 354 promotions on 2026-05-08, three-layer architecture (vault / pipeline / app) instead of the old "ready for business development" framing.

### Untouched (intentionally)

These are point-in-time records or aspirational documents whose value is in being a snapshot. They are linked from the new docs but were not rewritten:

- `docs/VISION.md` — three-year vision, kept verbatim.
- `docs/BUSINESS_MODEL.md` — pricing model, kept verbatim.
- `docs/MARKET_ANALYSIS.md` — competitive landscape snapshot, kept verbatim.
- `docs/WEEKLY_STANDUP_TEMPLATE.md` — operational template, kept verbatim.
- `docs/VERCEL_DEPLOYMENT_CHECKLIST.md` — verified accurate against `vercel.json` and `package.json`, no changes needed.
- `organized_library/documentation/COMPLETE_REPLACEMENT_REPORT.md`, `FINAL_PROCESSING_REPORT.md`, `B_section_enhanced_completion_report.md` — historical processing reports, dated and intentionally preserved.
- `organized_library/documentation/LOVABLE_AI_PROMPT*.md`, `FRONTEND_IMPLEMENTATION.md` — pre-React-port artefacts, archived in place.
- `organized_library/automation_tools/CHANGELOG-2026-05-05.md`, `CHANGELOG-2026-05-07.md` — pipeline release notes, kept verbatim.

## Discrepancies surfaced (now reflected in docs)

These are the gaps between what older docs claimed and what the codebase actually does. They are now explicit in the rewritten files; flagging them here for completeness.

1. **Active automation pipeline is `seamless_update_pipeline.py`, not `master_automation.py` or `run_complete_automation.py`.** The latter two have path-fragility issues and are not in the recommended SOP.
2. **The pipeline has 7 phases, not 3.** Older `HOW_IT_WORKS.md` described rewrite → audit → promote; the live pipeline adds DOI fix, interlink validation, promotion dry-run, and website rebuild.
3. **Cost gating, monitoring, and database persistence are not active.** `api_cost_monitor.py`, `monitoring.py`, and `database.py` exist but are not wired to the SOP.
4. **`@google/genai` is declared but not used in the SPA.** No source file imports it. Any AI assistance happens through external tooling, not in-app.
5. **`research_discovery.py` and `quality_scorer.py` have full multi-API implementations**, but `process_fitness_library.py` uses its own simpler PubMed integration. The advanced versions are reachable only through the legacy `automation_pipeline.py`.
6. **Static content bridge holds 678 nodes**, not the "2027 nodes extracted" claim from older `DEVELOPMENT_PROGRESS.md`. The 2027 number reflected an intermediate extraction that included sub-headings and stub pages; the current bridge (and Firestore import) are 678 canonical nodes.
7. **`buildClozeCards` covers 41.7 % of nodes**, not 100 %. Cards only generate where Key Points contain numeric / acronym / quantitative content. This is a feature of the heuristic, not a bug; previously docs were silent about it.
8. **Series shards in `public/content/series/` exist for A, B, C, E, Other — D and F nodes are folded into "Other".** The Library UI still renders all sections.
9. **354 files were promoted on 2026-05-08** (per `promotion_history.jsonl`). The current `processed_archive/processed_notes/` still has 235 rewritten artefacts; `confirmed_archive/2026-05-08/` is where promoted sources live.
10. **No CI exists today.** Lint, build, and the Phase-1 pytest suite are run manually.

## Verification

After this pass, the following statements are checkable against the filesystem:

- Every script named in `automation_tools/tools/SCRIPT_STATUS.md` exists at the path given.
- Every route named in `web app fitlib/README.md` is registered in `web app fitlib/server.ts`.
- Every env var in `docs/PRODUCTION_LAUNCH_CHECKLIST.md` is read by `server.ts`, `vite.config.ts`, or a `src/lib/*.ts` module.
- Every metric in `docs/KPIs.md` flagged as `current` is sourced from `stats.json`, `promotion_history.jsonl`, or a Firebase collection.
- Every file linked from `CAPABILITIES.md` exists at its given path.

## Follow-ups (not done in this pass)

- **CI** — adding a GitHub Action to run `npm run lint && npm run build` plus the Python pytest suite would catch drift between docs and code automatically.
- **Series shards** — regenerate D and F shards in `buildContentBridge.ts` so the precomputed series listing matches the schema in the UI.
- **Cross-device FSRS sync** — currently roadmap; would require pushing the IndexedDB store into Firestore with conflict resolution.
- **Cost gating in the SOP** — wire `api_cost_monitor.py` into `seamless_update_pipeline.py` so a `--cost-cap` flag aborts a run before it overshoots Anthropic spend.
