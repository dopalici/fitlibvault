# Automation Tools

This folder contains Python automation used to rewrite, validate, and promote fitness markdown notes.

## Current Status

- Primary rewrite engine: `processing_scripts/process_fitness_library.py`
- Safe promotion workflow: `automation_scripts/promote_rewritten_to_og.py`
- Primary end-to-end runner: `automation_scripts/seamless_update_pipeline.py`
- Legacy replacement flow: `replace_with_rewritten.py` (kept for reference, not preferred)
- Orchestrators:
  - `automation_scripts/master_automation.py` (callable, section orchestration)
  - `automation_scripts/run_complete_automation.py` (currently path-sensitive; see `tools/SCRIPT_STATUS.md`)

## SOP (Run Order)

1. Run the full deterministic pipeline (recommended):
   - `python3 "organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py" --section A --start-num 1 --end-num 65 --apply --build-content`
2. Optional granular mode (manual per phase):
   - rewrite: `python3 "organized_library/automation_tools/processing_scripts/process_fitness_library.py" --section A --input-dir "/Users/enes/fitlibvault-main" --output-dir "/Users/enes/fitlibvault-main/organized_library/processed_archive/processed_notes" --api-key "$ANTHROPIC_API_KEY"`
   - audit: `python3 "organized_library/automation_tools/utility_scripts/citation_validation_audit.py" --file-glob "rewritten_*.md"`
   - DOI suggestions: `python3 "organized_library/automation_tools/utility_scripts/citation_doi_fixer.py"`
   - promote dry run: `python3 "organized_library/automation_tools/automation_scripts/promote_rewritten_to_og.py"`
   - promote apply: `python3 "organized_library/automation_tools/automation_scripts/promote_rewritten_to_og.py" --apply`
   - website rebuild: `cd "web app fitlib" && npm run content:build`

## Documentation Map

- Script status matrix: `tools/SCRIPT_STATUS.md`
- Operational workflow: `tools/WORKFLOW.md`
- Internal mechanics: `HOW_IT_WORKS.md`
- Web app integration + learning system wiring: `web app fitlib/INTEGRATION.md`
- Reader/admin/FSRS owner SOP: `web app fitlib/docs/SOP_KNOWLEDGE_READER_SYSTEMS.md`
- Citation QA utilities:
  - `utility_scripts/citation_validation_audit.py`
  - `utility_scripts/citation_doi_fixer.py`

## Notes

- The website exporter now prefers explicit `**ID:**` metadata and ignores rewritten/backup artifacts.
- Keep OG filenames stable to preserve Obsidian interlinks.
