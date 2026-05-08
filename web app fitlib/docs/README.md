# FitLib — Web App Documentation

Last reviewed: 2026-05-08

This folder contains the operating documentation for the FitLib web app: how to ship it, how to author content, how to operate the reader / FSRS systems, and what targets the business is pointed at.

For a single-pane summary of what the *whole* project (vault + automation pipeline + web app) actually does today, read `/Users/enes/fitlibvault-main/CAPABILITIES.md` first.

---

## Where to start

| If you want to… | Read |
|---|---|
| Understand everything FitLib can do today | `/Users/enes/fitlibvault-main/CAPABILITIES.md` |
| See the current build state | `DEVELOPMENT_PROGRESS.md` |
| Run the web app locally | `../README.md` |
| Author or improve a single note | `SOP_CONTENT.md` |
| Understand the vault → JSON bridge | `SOP_EXTRACTION.md` |
| Operate the reader / cards / FSRS | `SOP_KNOWLEDGE_READER_SYSTEMS.md` |
| Wire up the new reader modules | `../INTEGRATION.md` |
| Ship to production | `PRODUCTION_LAUNCH_CHECKLIST.md` then `VERCEL_DEPLOYMENT_CHECKLIST.md` |
| Track KPIs | `KPIs.md` |
| Plan the next quarter | `ROADMAP.md` |
| Run the weekly review | `WEEKLY_STANDUP_TEMPLATE.md`, `AI_ASSISTED_MANAGEMENT.md` |
| Pitch the business | `VISION.md`, `BUSINESS_MODEL.md`, `MARKET_ANALYSIS.md` |

---

## File-by-file index

### Strategic (read first if you are new)

- **`VISION.md`** — three-year vision, mission, core values; aspirational financial goals (3-year target: $50K+ ARR, 50,000+ users).
- **`BUSINESS_MODEL.md`** — pricing tiers (Premium $7.99/mo, API $299–1,999/yr), unit economics, customer segments.
- **`MARKET_ANALYSIS.md`** — competitive landscape (Examine.com, Stronger by Science, PubMed) and FitLib's positioning.

### Build & shipping

- **`DEVELOPMENT_PROGRESS.md`** — current build snapshot. What is shipped, what is wired but inactive, what is roadmap.
- **`PRODUCTION_LAUNCH_CHECKLIST.md`** — preflight checklist before any production deploy. Env vars, smoke tests, Stripe webhook test, rollback plan.
- **`VERCEL_DEPLOYMENT_CHECKLIST.md`** — Vercel-specific deploy steps.

### Authoring & operations (SOPs)

- **`SOP_CONTENT.md`** — canonical workflow for adding or improving a note. Schema, recommended pipeline path, citation rules, wikilink rules.
- **`SOP_EXTRACTION.md`** — how the vault → JSON bridge works (`extractVault.ts`, `buildContentBridge.ts`, `buildClozeCards.ts`, `importData.ts`).
- **`SOP_KNOWLEDGE_READER_SYSTEMS.md`** — operational doc for the Reader / FSRS / cloze systems. Admin bypass, recall workflow, build expectations, troubleshooting.

### Direction & metrics

- **`ROADMAP.md`** — quarterly plan. Each line item now tagged `[shipped]`, `[wip]`, `[planned]`, or `[stretch]`.
- **`KPIs.md`** — metrics. Each metric tagged `[current]` (measurable today) or `[target]` (aspirational).
- **`AI_ASSISTED_MANAGEMENT.md`** — how the operator runs weekly metric reviews and strategic adjustments through AI tooling (currently external — Cline / Claude Code — not in-app).
- **`WEEKLY_STANDUP_TEMPLATE.md`** — Friday standup template; feeds `AI_ASSISTED_MANAGEMENT.md` review loop.

---

## Reading order for a brand-new operator

1. `/Users/enes/fitlibvault-main/CAPABILITIES.md` — what exists.
2. `DEVELOPMENT_PROGRESS.md` — what state it is in.
3. `../README.md` — get it running locally.
4. `SOP_KNOWLEDGE_READER_SYSTEMS.md` — feel the reader operationally.
5. `SOP_CONTENT.md` and `SOP_EXTRACTION.md` — understand the content pipeline.
6. `PRODUCTION_LAUNCH_CHECKLIST.md` — what is required before shipping.
7. `KPIs.md` and `ROADMAP.md` — direction.

For the operations side of the *vault* and the *automation pipeline*, hop over to:

- `/Users/enes/fitlibvault-main/organized_library/automation_tools/README.md`
- `/Users/enes/fitlibvault-main/organized_library/automation_tools/HOW_IT_WORKS.md`
- `/Users/enes/fitlibvault-main/organized_library/automation_tools/tools/SCRIPT_STATUS.md`
- `/Users/enes/fitlibvault-main/organized_library/automation_tools/tools/WORKFLOW.md`

---

## Notes on this index

- The 2026-05-08 audit refreshed every doc here (see `/Users/enes/fitlibvault-main/CHANGELOG_DOCS_2026-05-08.md`).
- Targets and aspirational numbers in `VISION.md`, `BUSINESS_MODEL.md`, and the unflagged sections of `KPIs.md` / `ROADMAP.md` are intentionally kept; the audit only added explicit current-vs-target tagging in those docs.
- If you find a claim in a doc that contradicts the codebase, the codebase is the source of truth — fix the doc.
