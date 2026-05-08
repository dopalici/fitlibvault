# Script Status Matrix

Last reviewed: 2026-05-08

Scope: every `*.py` under `organized_library/automation_tools/`. There are 31 scripts in total — 7 active, 5 conditional, 17 legacy / experimental, 2 support modules.

Status legend:

- `active`: used in the current recommended SOP (`WORKFLOW.md`).
- `conditional`: callable but path-fragile or depends on env / config not enforced by the SOP.
- `legacy`: older / experimental utility; superseded by something in the active set.
- `support`: imported as a module by other scripts; not a standalone entry point.

## Active

- `automation_scripts/seamless_update_pipeline.py`
  - path-stable end-to-end orchestrator
  - enforces sequence + promotion validation gate before apply
  - `--validate-interlinks` runs `interlink_validator.py` before promotion
  - `--staged-apply` switches the apply step to the per-file confirmed flow
- `processing_scripts/process_fitness_library.py`
  - CLI works (`--help` verified)
  - core rewrite engine; now ranks PubMed studies by composite quality +
    relevance + recency, exposes `--min-relevance`, `--min-quality`,
    `--top-studies`, `--lookback-years` gates
- `automation_scripts/promote_rewritten_to_og.py`
  - CLI works (`--help` verified)
  - bulk OG replacement workflow; preserved as a fallback
- `automation_scripts/staged_promotion.py`
  - per-file y/s/d/q promotion with date stamping, atomic write, link
    integrity gate, JSONL history, dated confirmed-archive move
- `utility_scripts/citation_validation_audit.py`
  - scans rewritten notes (`rewritten_*.md` by default) and validates DOI/PMID links in one run
- `utility_scripts/citation_doi_fixer.py`
  - reads audit output and proposes DOI keep/normalize/remove actions
- `utility_scripts/interlink_validator.py`
  - validates every `[[wikilink]]` against the vault, flags broken / stub
    / duplicate targets and emits JSON + Markdown + optional CSV reports

## Conditional

- `automation_scripts/master_automation.py`
  - CLI works (`--help` verified)
  - depends on correct `--base-dir` layout and API key
- `automation_scripts/run_complete_automation.py`
  - fails from repo root due to path assumptions:
    - expects `ultra_optimized_processor.py` as sibling
    - expects `process_fitness_library.py` in base dir
- `processing_scripts/ultra_optimized_processor.py`
  - used by `run_complete_automation.py`
- `monitoring_scripts/research_discovery.py`
  - depends on API config and network access
- `validation_scripts/quality_scorer.py`
  - usable for citation scoring workflows

## Legacy / Experimental (kept, not default)

- `replace_with_rewritten.py` (creates backups and replaces in cwd)
- `automation_scripts/automation_pipeline.py`
- `processing_scripts/content_enhancer.py`
- `processing_scripts/expert_content_processor.py`
- `processing_scripts/manual_enhanced_processor.py`
- `processing_scripts/local_template_processor.py`
- `processing_scripts/process_remaining_b.py`
- `monitoring_scripts/api_cost_monitor.py`
- `monitoring_scripts/cost_controlled_processor.py`
- `monitoring_scripts/monitoring.py`
- `validation_scripts/validate_citations.py`
- `validation_scripts/citation_validator.py`
- `analysis_tools.py`
- `enhanced_depth_processor.py`
- `organize_fitness_library.py`
- `utility_scripts/update_links_for_organization.py`
- `test_scripts/test_suite.py`
- `test_scripts/simple_test.py`
- `test_scripts/demo_test.py`

## Shared Support Modules

- `utility_scripts/config.py` — central `ConfigManager` with `APIConfig` / `ProcessingConfig` / `DatabaseConfig` / `QualityConfig` / `SystemConfig` dataclasses. Imported by `research_discovery.py`, `database.py`, `monitoring.py`, `quality_scorer.py`. Not used in the active SOP because none of those callers are.
- `utility_scripts/database.py` — async SQLite layer (citations, file processing, quality metrics). Schema-only today; no active script writes to it.

These are imported / config modules rather than standalone operational entry points.

## Test scripts

- `test_scripts/test_process_fitness_library_phase1.py` — pytest unit tests for the rewrite engine's evidence ranking. Run manually before changes to `process_fitness_library.py`.
- `test_scripts/test_suite.py` — comprehensive (legacy) pytest suite touching `research_discovery`, `quality_scorer`, `content_enhancer`, `database`, `automation_pipeline`, `monitoring`, `config`. Many of those modules are legacy, so the suite has not been kept in sync.
- `test_scripts/simple_test.py`, `test_scripts/demo_test.py` — incomplete scratch scripts; useful as references only.

## Outputs cheat-sheet

When the active SOP runs, these artefacts land in `organized_library/processed_archive/processed_notes/`:

- `rewritten_*.md` — staging files (one per source note) until promoted.
- `citation_audit_report.json`, `citation_audit_links.csv` — citation HTTP audit.
- `citation_doi_fix_suggestions.json` — DOI fix suggestions.
- `interlink_audit_report.json`, `interlink_audit.md`, `interlink_audit_links.csv` (optional) — wikilink validation.

Promotion artefacts:

- Vault-root OG file overwritten in place.
- `organized_library/processed_archive/confirmed_archive/<YYYY-MM-DD>/rewritten_*.md` — promoted source archived per day.
- `organized_library/automation_tools/promotion_history.jsonl` — JSONL audit log; 354 rows as of 2026-05-08.

Website artefacts (when `--build-content` is set):

- `web app fitlib/public/content/{index.json, nodes/*.json, series/*.json, stats.json, cards.json, cards/*.json}`.
