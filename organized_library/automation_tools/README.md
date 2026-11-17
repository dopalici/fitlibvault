# Automation Tools

Last reviewed: 2026-05-08

Python automation that rewrites, validates, and promotes fitness markdown notes
without breaking the Obsidian interlink graph. For a single-pane summary of the
whole project, see `/Users/enes/fitlibvault-main/CAPABILITIES.md`. For per-script
status, `tools/SCRIPT_STATUS.md`. For the operator runbook, `tools/WORKFLOW.md`.

Recent activity: **354 promotions on 2026-05-08** (see `promotion_history.jsonl`).

## Current Status

- Primary rewrite engine: `processing_scripts/process_fitness_library.py`
  - PubMed search now combines title + section domain hint + topic keywords
  - Studies are filtered to humans + strong study designs and ranked by a
    composite score (0.5 × quality + 0.3 × relevance + 0.2 × recency)
  - `--min-relevance`, `--min-quality`, `--top-studies`, `--lookback-years`
    expose tunable gates so only the most relatable + credible studies pass
- Bulk promotion (legacy, all-or-nothing): `automation_scripts/promote_rewritten_to_og.py`
- **Per-file confirm + date stamping** (recommended): `automation_scripts/staged_promotion.py`
- **Interlink validator**: `utility_scripts/interlink_validator.py`
- End-to-end runner: `automation_scripts/seamless_update_pipeline.py`
- Citation QA: `utility_scripts/citation_validation_audit.py` and
  `utility_scripts/citation_doi_fixer.py`
- Legacy replacement flow: `replace_with_rewritten.py` (kept for reference)

## SOP (Run Order)

1. **Recommended one-command run** (rewrite → audit → DOI fix → interlink check
   → dry-run promotion validation → per-file confirmed promotion → website
   rebuild). Staged apply is the default mode and pauses on each file for
   y / s / d / q so you can inspect each change before it touches the OG file:

   ```bash
   python3 "organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py" \
     --section A --start-num 1 --end-num 65 \
     --validate-interlinks --interlink-fail-on broken \
     --apply \
     --build-content
   ```

   Headless variant (no prompts, accept everything that passes validation):

   ```bash
   ... --apply --staged-auto-yes
   ```

2. **Granular mode** (manual per phase):
   - rewrite: `python3 "organized_library/automation_tools/processing_scripts/process_fitness_library.py" --section A --input-dir "/Users/enes/fitlibvault-main" --output-dir "/Users/enes/fitlibvault-main/organized_library/processed_archive/processed_notes" --api-key "$ANTHROPIC_API_KEY"`
   - citation audit: `python3 "organized_library/automation_tools/utility_scripts/citation_validation_audit.py" --file-glob "rewritten_*.md"`
   - DOI fix suggestions: `python3 "organized_library/automation_tools/utility_scripts/citation_doi_fixer.py"`
   - **interlink integrity** (full vault scan): `python3 "organized_library/automation_tools/utility_scripts/interlink_validator.py" --scope vault --write-csv`
   - **interlink integrity** (rewritten staging only, pre-promotion): `python3 "organized_library/automation_tools/utility_scripts/interlink_validator.py" --scope rewritten --fail-on broken`
   - promote dry-run: `python3 "organized_library/automation_tools/automation_scripts/promote_rewritten_to_og.py"`
   - **per-file confirmed promote**: `python3 "organized_library/automation_tools/automation_scripts/staged_promotion.py" --interactive`
   - bulk promote (legacy): `python3 "organized_library/automation_tools/automation_scripts/promote_rewritten_to_og.py" --apply`
   - website rebuild: `cd "web app fitlib" && npm run content:build`

## Confirmation + Audit Trail

`staged_promotion.py` is the answer to "I want to confirm each update before
it replaces the OG file, and I want a real timestamp on every push":

- Builds an in-memory map of every markdown file in the vault and flags stubs
  (empty / title-only). Any rewrite whose `[[wikilinks]]` resolve to broken
  targets or stubs is **blocked** unless `--allow-link-issues` is set.
- Shows a unified diff preview, plus citation/recommendation deltas, before
  asking y / s / d / q.
- On accept it:
  1. Rewrites the `(Updated: …)` tag in-place with today's ISO date
  2. Appends a one-line entry to the note's `## Update Log`
  3. Atomically replaces the OG file (write-temp → fsync → rename, so an
     interrupted run can never corrupt the file)
  4. Moves the source `rewritten_*.md` into
     `organized_library/processed_archive/confirmed_archive/<YYYY-MM-DD>/`
     so the same change cannot be re-applied next run
  5. Appends a JSONL row to `organized_library/automation_tools/promotion_history.jsonl`
     (timestamp, ID, file, citation deltas, archive path)

## Documentation Map

- Script status matrix: `tools/SCRIPT_STATUS.md`
- Operational workflow: `tools/WORKFLOW.md`
- Internal mechanics: `HOW_IT_WORKS.md`
- Web app integration + learning system wiring: `web app fitlib/INTEGRATION.md`
- Reader/admin/FSRS owner SOP: `web app fitlib/docs/SOP_KNOWLEDGE_READER_SYSTEMS.md`

## File Format Optimisation (implemented)

The format hardening work is now active across the toolchain:

- **YAML frontmatter is the metadata source of truth** for notes:

  ```yaml
  ---
  id: A10-HORMONAL-RESPONSES
  created: 2025-04-23
  updated: 2026-05-07
  section: A
  tags: [physiology, hormones]
  ---
  ```

  Parsers in automation scripts now read YAML first with bold-inline fallback.
  The migration utility (`utility_scripts/migrate_to_yaml_frontmatter.py`)
  converted existing notes in one pass.

- **Canonical wikilinks are enforced** by stripping `.md` from link targets.
  Use `utility_scripts/wikilink_md_strip.py` (dry-run by default) to clean any
  regressions. The validator also normalizes `.md` targets and reports them as
  non-canonical instead of hard-broken when resolvable.

- **Section-index stubs were remediated** by adding real overview content to
  low-word root index notes and removing duplicate basename mirrors in
  `organized_library/<topic>/` for the affected sections.

- **Staged promotion is the default apply path** in
  `automation_scripts/seamless_update_pipeline.py`. Accepted rewrites are moved
  into `organized_library/processed_archive/confirmed_archive/<YYYY-MM-DD>/`
  by `staged_promotion.py`, preventing re-promotion clutter.

## Notes

- The website exporter now prefers frontmatter `id` and carries `created` /
  `updated` into the content bridge payload (with explicit bold metadata
  fallback for legacy notes).
- Keep OG filenames stable to preserve Obsidian interlinks. Promotion never
  renames files, only rewrites their content.
