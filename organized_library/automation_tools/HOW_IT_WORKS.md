# How It Works

This automation stack has six phases:

1. Rewrite markdown notes
2. Audit citation links
3. Generate DOI-fix suggestions
4. Validate structure and IDs
5. Promote rewritten content into OG files without renaming
6. Build website content + cloze cards for learning workflows

## 1) Rewrite Phase

Script: `processing_scripts/process_fitness_library.py`

- Reads source notes from `--input-dir`
- Rewrites with Anthropic using a strict template
- Preserves `[[wikilinks]]`
- Validates section presence and citation link shape
- Writes `rewritten_*.md` to `--output-dir`

## 2) Citation Audit Phase

Script: `utility_scripts/citation_validation_audit.py`

- Scans `rewritten_*.md` files (or a custom glob)
- Extracts DOI/PMID links and validation warnings
- Performs bulk link checks
- Writes:
  - `citation_audit_report.json`
  - `citation_audit_links.csv`

## 3) DOI Suggestion Phase

Script: `utility_scripts/citation_doi_fixer.py`

- Reads `citation_audit_report.json`
- Re-validates invalid/error DOI entries
- Produces suggestion actions (`keep`, `normalize`, `remove_or_replace`)
- Writes `citation_doi_fix_suggestions.json`

## 4) Validation Phase

Script: `automation_scripts/promote_rewritten_to_og.py` (dry-run by default)

- Scans `rewritten_*.md`
- Checks required sections
- Checks ID consistency against OG target file
- Produces a ready/failed/skipped summary

## 5) Promotion Phase

Script: `automation_scripts/promote_rewritten_to_og.py --apply`

- Copies rewritten content into matching OG filename at vault root
- Does not rename files
- Keeps interlink targets stable

## Optional Orchestrators

- `automation_scripts/seamless_update_pipeline.py`: primary end-to-end runner (path-stable, deterministic sequence)
- `automation_scripts/master_automation.py`: section-batch orchestration
- `automation_scripts/run_complete_automation.py`: higher-level orchestration with optimization hooks

`run_complete_automation.py` currently expects sibling scripts in the same working directory and can fail when launched from repo root without path adjustments.

## Website Export Compatibility

Website export behavior now:

- prefers explicit markdown metadata IDs (`**ID:**`)
- ignores rewritten and backup artifacts
- resolves duplicate candidates by canonical-path priority

This prevents backup/staging files from overriding OG website content.

## 6) Website Build + Learning Cards Phase

Scripts:

- `web app fitlib/scripts/buildContentBridge.ts`
- `web app fitlib/scripts/buildClozeCards.ts`

Pipeline outputs:

- `web app fitlib/public/content/index.json`
- `web app fitlib/public/content/nodes/*.json`
- `web app fitlib/public/content/series/*.json`
- `web app fitlib/public/content/cards.json`
- `web app fitlib/public/content/cards/*.json`

This enables:

- structured Reader mode rendering
- stacked wikilink navigation
- FSRS-spaced recall cards generated from key points
