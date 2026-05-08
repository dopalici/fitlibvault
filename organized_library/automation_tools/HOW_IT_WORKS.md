# How It Works

This automation stack has seven phases:

1. Rewrite markdown notes (with PubMed-driven evidence packet)
2. Audit citation links
3. Generate DOI-fix suggestions
4. Validate Obsidian interlink integrity
5. Validate rewrite structure and IDs
6. Promote rewritten content into OG files (per-file confirm or bulk apply)
7. Build website content + cloze cards for learning workflows

## 1) Rewrite Phase

Script: `processing_scripts/process_fitness_library.py`

- Reads source notes from `--input-dir`
- Rewrites with Anthropic using a strict template
- Preserves `[[wikilinks]]`
- Validates section presence and citation link shape
- Writes `rewritten_*.md` to `--output-dir`

### Evidence Search and Quality Ranking

Before each rewrite the engine asks PubMed for recent studies and forwards
the strongest ones to Claude:

- **Search composition**: title-derived tokens, the section-domain hint
  (`A → exercise physiology`, `C → sports nutrition`, `M → exercise
  recovery`, etc.), and topical keyword expansion (e.g. "vo2" →
  `vo2max training`).
- **PubMed query** is filtered to humans and to strong study designs
  (RCT / Meta-Analysis / Systematic Review / Clinical Trial / Review),
  with a configurable `--lookback-years` window.
- **Multi-factor scoring** per study:
  - `quality_score = 0.6 * design_strength + 0.4 * journal_weight`
  - `relevance_score = Jaccard(title tokens, note title tokens)`
  - `recency_score` decays over years
  - `composite_score = 0.5 * quality + 0.3 * relevance + 0.2 * recency`
- **Filtering and ranking**: studies whose `relevance_score < --min-relevance`
  or `quality_score < --min-quality` are dropped, then the remaining studies
  are sorted by composite score; the top `--top-studies` are forwarded.
- The evidence brief now includes the per-study scores so Claude can prefer
  the highest-ranked sources when building the `## Research Evidence` block.

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

## 4) Interlink Integrity Phase

Script: `utility_scripts/interlink_validator.py`

- Builds a basename → file index over the vault (default excludes the
  duplicate sorted-views under `organized_library/<topic>` plus
  `processed_archive`, `original_backup`, build artefacts and venvs).
- Walks every `[[wikilink]]` in the chosen scope (`vault`, `rewritten`, or
  `organized`) and labels each as `ok`, `stub` (target exists but is empty
  / title-only), `shadowed` (multiple files share the basename), or
  `broken` (no resolvable target — emits a fuzzy-match suggestion).
- Outputs `interlink_audit_report.json`, `interlink_audit.md`, and an
  optional `interlink_audit_links.csv`.
- `--fail-on broken` (or `any`) makes the pipeline halt before writing to
  the OG files when interlinks would land on empty stubs.

## 5) Promotion Validation Phase

Script: `automation_scripts/promote_rewritten_to_og.py` (dry-run by default)

- Scans `rewritten_*.md`
- Checks required sections
- Checks ID consistency against OG target file
- Produces a ready/failed/skipped summary

## 6) Promotion Phase (two modes)

### a. Bulk apply (legacy)

Script: `automation_scripts/promote_rewritten_to_og.py --apply`

- Copies every passing rewritten file into the matching OG filename at
  vault root. Same name in/out so wikilinks remain stable.

### b. Per-file confirmed apply (recommended)

Script: `automation_scripts/staged_promotion.py`

For each rewritten file the script:

- runs structural + ID validation
- resolves every `[[wikilink]]` against the vault index and **blocks**
  promotion when any link would land on a missing or stub target
- shows a unified diff, citation deltas, and recommendation deltas
- prompts y / s / d / q (or auto-accepts under `--auto-yes`)

On accept it:

- updates the in-file `(Updated: <date>)` tag with today's ISO date
- appends a one-line entry to `## Update Log`
- atomically replaces the OG file (write-temp → fsync → rename)
- moves the source `rewritten_*.md` into
  `organized_library/processed_archive/confirmed_archive/<YYYY-MM-DD>/`
- appends a JSONL audit row to
  `organized_library/automation_tools/promotion_history.jsonl`

The combination of date stamping, history JSONL, and confirmed-archive move
gives every push a real timestamp and prevents stale rewrites from sneaking
back in on later runs.

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

## 7) Website Build + Learning Cards Phase

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
