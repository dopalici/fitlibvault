# Automation Tools Change Log - 2026-05-05

## Scope

Changes made today inside `organized_library/automation_tools`.

## Committed Changes (already pushed)

### Added

- `automation_scripts/promote_rewritten_to_og.py`
  - New safe promotion script to move `rewritten_*.md` content into OG vault files **without renaming**.
  - Includes dry-run validation mode and `--apply` mode.
  - Validates required structure and ID consistency before replacement.

- `conflict_review_report.json`
  - Generated conflict report for ID/title collisions.
  - Splits semantic conflicts vs punctuation-only conflicts for manual review.

## Current Uncommitted Changes (local, not pushed yet)

### Updated

- `README.md`
  - Rewritten to reflect the current real workflow and active scripts.
  - Added quick-start commands and documentation map.

- `HOW_IT_WORKS.md`
  - Rewritten to document the actual 3-phase flow:
    1) rewrite,
    2) validate,
    3) promote.
  - Added notes about orchestrator caveats and exporter behavior.

### Added Folder

- `tools/`
  - `tools/README.md`
  - `tools/SCRIPT_STATUS.md`
  - `tools/WORKFLOW.md`

These documents provide:
- active/conditional/legacy script inventory,
- biweekly operational process,
- practical source-of-truth docs for running automation safely.

## Notes

- This changelog captures only work within `organized_library/automation_tools`.
- Repository-wide content/export changes were performed separately outside this folder.
