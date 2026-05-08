# Tools docs

Last reviewed: 2026-05-08

Operational documentation for `organized_library/automation_tools/`. Read these first before running anything from the pipeline.

## What is in this folder

- **`SCRIPT_STATUS.md`** — every Python script in the automation tree with a status tag (`active` / `conditional` / `legacy` / `support`). The single matrix you should consult before deciding whether to call a script.
- **`WORKFLOW.md`** — operator runbook. The recommended one-command pipeline, granular per-phase commands, pause / resume strategy, verification checklist, commit-and-push template.
- **`README.md`** (this file) — index pointing at the above plus cross-links to the rest of the documentation.

## Cross-references

- Pipeline overview + per-phase mechanics → `../HOW_IT_WORKS.md`.
- Rationale and current status → `../README.md`.
- Recent pipeline release notes → `../CHANGELOG-2026-05-05.md`, `../CHANGELOG-2026-05-07.md`.
- Project-wide capability summary → `/Users/enes/fitlibvault-main/CAPABILITIES.md`.
- Web-app side of the bridge (build / Reader / FSRS) → `/Users/enes/fitlibvault-main/web app fitlib/INTEGRATION.md` and `/Users/enes/fitlibvault-main/web app fitlib/docs/SOP_KNOWLEDGE_READER_SYSTEMS.md`.

## Active SOP entry points (the only scripts you should call directly)

- **Primary orchestrator:** `../automation_scripts/seamless_update_pipeline.py`.
- **Per-file confirmed promotion:** `../automation_scripts/staged_promotion.py`.
- **Bulk dry-run / fallback promotion:** `../automation_scripts/promote_rewritten_to_og.py`.
- **Rewrite engine** (called by the orchestrator, but can be called standalone): `../processing_scripts/process_fitness_library.py`.
- **Citation QA:** `../utility_scripts/citation_validation_audit.py`, `../utility_scripts/citation_doi_fixer.py`.
- **Wikilink integrity:** `../utility_scripts/interlink_validator.py`.

Everything else in the tree is conditional, legacy, or a support module — do not call them directly without first reading `SCRIPT_STATUS.md`.
