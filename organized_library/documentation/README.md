# Documentation — Library Reference Folder

Last reviewed: 2026-05-08

This folder collects long-form reference documents that did not fit into either the web app's `docs/` (which is operational) or the automation tools' `tools/` (which is runbook-style). Some entries here are **historical processing reports** preserved as snapshots; others are **content-style overview notes** that live alongside the rest of the vault.

For the operating documentation that this project actually runs on, see:

- `/Users/enes/fitlibvault-main/CAPABILITIES.md` — single-pane capability overview.
- `/Users/enes/fitlibvault-main/web app fitlib/docs/` — web app operational docs.
- `/Users/enes/fitlibvault-main/organized_library/automation_tools/` and `tools/` — pipeline docs.

---

## What is in this folder

The 35 markdown files break into four categories.

### A. Project context (start here if you are an AI assistant or new contributor)

- **`CLAUDE_PROJECT_CONTEXT.md`** — primer covering project goals, content stats, three-layer architecture, and current pipeline. **Refreshed 2026-05-08.**
- **`fitlib.md`** — short branding / pitch note used as a "what is FitLib" reference.
- **`README.md`** (this file) — index.

### B. Strategic / business docs (snapshots; superseded by the web app's `docs/VISION.md` etc.)

- **`FITNESS_LIBRARY_BUSINESS_DEVELOPMENT_GUIDE.md`** — original business strategy (Q1 2026 framing, $100K+ IP value, three-phase roll-out).
- **`PROJECT_NEXT_STEPS_ACTION_PLAN.md`** — tactical execution roadmap from project inception.

### C. Frontend / UX exploration (pre-React-port; archival)

- **`FRONTEND_IMPLEMENTATION.md`** — cyberpunk terminal interface concept.
- **`LOVABLE_AI_PROMPT.md`** and **`LOVABLE_AI_PROMPT_UPDATED.md`** — Lovable.dev prompts used to scaffold the original frontend.

These describe a pre-React design language. The shipped frontend uses a paper-on-ink minimalist aesthetic and is built in React 19 + Tailwind v4. Treat these as historical references.

### D. Processing reports (point-in-time records of automation runs)

- **`COMPLETE_REPLACEMENT_REPORT.md`** — 331-file enhancement run (2025-06-05).
- **`FINAL_PROCESSING_REPORT.md`** — A30–A65 batch report.
- **`B_section_enhanced_completion_report.md`** — Resistance Training section (B1–B78) enhancement.
- **`citation_validation_report.md`** and **`cost_controlled_report.md`** — pipeline run outputs.

These are dated and intentionally preserved. They are not refreshed — for current pipeline activity see `automation_tools/promotion_history.jsonl` and `automation_tools/CHANGELOG-*.md`.

### E. Content-style overview notes (live alongside vault content)

- **`Appendix References and Meta-information.md`** — bibliography conventions and meta-information for the library.
- **`D. Weight Management.md`**, **`D1. Evidence-Based Weight Loss Principles.md`**, **`D2. Diet Adherence and Behavior Change.md`**, **`D3. Weight Maintenance After Loss.md`** — D-series notes that also have copies at the vault root.
- **`EXL. Exercise Library.md`** — exercise-library index note.
- **`G-VII. Anatomy, Physiology & Biomechanics (More Applied).md`** and the **G-VII-1 / G-VII-2 / G-VII-3** subfiles — supplementary anatomy / kinesiology / neurophysiology notes.
- **`IX8`–`IX15`** — injury-management series (return-to-play, load management, movement quality, psychological aspects, technology, team-based, screening, chronic).
- **`Z1. Understanding this Zettelkasten.md`**, **`Z2. Practical Implementation Guide.md`**, **`Z3. Cultural & Historical Perspectives on Fitness.md`** — Zettelkasten-style reflection and meta-guidance notes.
- **`template.md`** — boilerplate template for new notes.

These are content notes, not project docs. The publishing pipeline picks them up the same way it picks up vault-root notes.

---

## Format notes

- All files use markdown.
- Internal links use `[[Topic Name]]` Obsidian-style wikilink format.
- Content notes follow the canonical seven-section schema (Quick Takeaway → Key Points → Deep Dive → Research Evidence → Practical Applications → Common Mistakes → Related Concepts) defined in `web app fitlib/src/lib/noteSchema.ts`.
- For the schema details and authoring rules, see `web app fitlib/docs/SOP_CONTENT.md`.

---

## When you should *not* read these files

- If you are looking for what the project **does today**, read `CAPABILITIES.md` instead — most of the historical reports here describe earlier phases.
- If you want the **active automation pipeline**, read `organized_library/automation_tools/HOW_IT_WORKS.md` and `tools/WORKFLOW.md`.
- If you want the **business / financial plan**, the canonical version is `web app fitlib/docs/VISION.md` and `web app fitlib/docs/BUSINESS_MODEL.md`.

This folder is reference, not operations.
