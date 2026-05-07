# Script Status Matrix

Scope: `organized_library/automation_tools/**/*.py`

Status legend:

- `active`: used in current recommended workflow
- `conditional`: callable but dependent on setup/path assumptions
- `legacy`: older/experimental utility; not part of default flow

## Active

- `automation_scripts/seamless_update_pipeline.py`
  - path-stable end-to-end orchestrator
  - enforces sequence + promotion validation gate before apply
- `processing_scripts/process_fitness_library.py`
  - CLI works (`--help` verified)
  - core rewrite engine
- `automation_scripts/promote_rewritten_to_og.py`
  - CLI works (`--help` verified)
  - safe OG replacement workflow
- `utility_scripts/citation_validation_audit.py`
  - scans rewritten notes (`rewritten_*.md` by default) and validates DOI/PMID links in one run
- `utility_scripts/citation_doi_fixer.py`
  - reads audit output and proposes DOI keep/normalize/remove actions

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

- `utility_scripts/config.py`
- `utility_scripts/database.py`

These are imported/config modules rather than standalone operational entrypoints.
