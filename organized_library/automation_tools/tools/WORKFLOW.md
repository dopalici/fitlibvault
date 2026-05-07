# Workflow (SOP)

This is the recommended safe cycle for rewriting, validating, and promoting notes.

## Preferred One-Command Pipeline

Run the full sequence with safety gates:

`python3 "organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py" --section C --apply --build-content`

What this runs, in order:
- rewrite notes
- citation audit
- DOI fix suggestions
- promotion dry-run validation
- promotion apply (if `--apply`)
- website content build (if `--build-content`)

## 1) Rewrite

Run section-based rewrites into processed archive:

`python3 "organized_library/automation_tools/processing_scripts/process_fitness_library.py" --section C --input-dir "/Users/enes/fitlibvault-main" --output-dir "/Users/enes/fitlibvault-main/organized_library/processed_archive/processed_notes" --api-key "$ANTHROPIC_API_KEY"`

## 2) Citation Audit

`python3 "organized_library/automation_tools/utility_scripts/citation_validation_audit.py" --file-glob "rewritten_*.md"`

Review:
- `organized_library/processed_archive/processed_notes/citation_audit_report.json`
- `organized_library/processed_archive/processed_notes/citation_audit_links.csv`

## 3) DOI Fix Suggestions

`python3 "organized_library/automation_tools/utility_scripts/citation_doi_fixer.py"`

Review:
- `organized_library/processed_archive/processed_notes/citation_doi_fix_suggestions.json`

## 4) Validate (Dry Run)

`python3 "organized_library/automation_tools/automation_scripts/promote_rewritten_to_og.py"`

Fix all failed entries before apply.

## 5) Promote to OG

`python3 "organized_library/automation_tools/automation_scripts/promote_rewritten_to_og.py" --apply`

This updates OG content in place without changing filenames.

## 6) Rebuild Website Content

`cd "web app fitlib" && npm run content:build`

## 7) Verify

- Confirm key nodes in `fitlib_export.json`
- Confirm node payload in `web app fitlib/public/content/nodes/*.json`
- Confirm cloze card payload in `web app fitlib/public/content/cards/*.json`
- Spot check critical links render correctly in app
- Spot check Reader mode + stacked links + recall cards in app

## 8) Commit and Push

- Commit once validation passes
- Push branch and open PR if needed
