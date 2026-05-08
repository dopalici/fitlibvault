# Automation Tools Change Log - 2026-05-07

## Scope

Operator-driven hardening pass over `organized_library/automation_tools/`
to address three gaps:

1. The PubMed search query and study-quality ranking were too shallow to
   reliably surface "the most relatable studies with the highest credibility
   score".
2. There was no tool that confirmed every Obsidian `[[wikilink]]` resolved
   to a real, non-stub file (so wikilinks could land on title-only or empty
   shadow files).
3. Promotion was all-or-nothing: there was no way to confirm each rewrite
   per file, no real timestamp on each push, and no audit trail to prevent
   stale rewrites from being re-applied.

## Added

- `utility_scripts/interlink_validator.py`
  - Builds a basename → file index over the vault. By default excludes
    duplicate sorted-views under `organized_library/<topic>/`,
    `processed_archive/`, `original_backup/`, build artefacts and venvs.
  - Walks every `[[wikilink]]` in scope (`vault`, `rewritten`, or
    `organized`) and labels each as `ok`, `stub`, `shadowed`, or `broken`.
  - Fuzzy-matches broken links against the vault index and emits the
    closest candidate as a suggestion.
  - Outputs `interlink_audit_report.json`, `interlink_audit.md`, and an
    optional `interlink_audit_links.csv`.
  - `--fail-on broken` (or `any`) fails the pipeline before promotion when
    a wikilink would land on an empty stub.
  - Smoke test on the current vault returned 8,089 / 8,436 OK (95.9%),
    79 stubs, 268 broken with suggestions, 18 stub files surfaced for
    cleanup.
- `automation_scripts/staged_promotion.py`
  - Per-file confirmation flow (`y / s / d / q`) with diff preview,
    citation deltas, recommendation deltas, and a wikilink integrity gate.
  - Stamps the OG file's `(Updated: <date>)` tag with today's ISO date and
    appends a one-line entry to `## Update Log` on each accept.
  - Atomic write (write-temp → fsync → `os.replace`) so an interrupted
    promotion can never corrupt a vault file.
  - Moves accepted `rewritten_*.md` files into
    `organized_library/processed_archive/confirmed_archive/<YYYY-MM-DD>/`
    so the same change cannot be re-applied next run.
  - Writes a JSONL row per push to
    `organized_library/automation_tools/promotion_history.jsonl`
    (timestamp, ID, file, deltas, archive path).
  - `--auto-yes` mode for headless runs; `--list-only` mode for dry
    queue inspection.

## Updated

- `processing_scripts/process_fitness_library.py`
  - PubMed search composition now combines title tokens, section-domain
    hints (`A → exercise physiology`, `C → sports nutrition`, `M →
    exercise recovery`, etc.), and topical keyword expansion (e.g.
    `vo2 → vo2max training`).
  - PubMed query is filtered to humans + strong study designs (RCT /
    Meta-Analysis / Systematic Review / Clinical Trial / Review) with a
    configurable lookback window.
  - Multi-factor study scoring:
    - `quality_score = 0.6 * design_strength + 0.4 * journal_weight`
    - `relevance_score = Jaccard(study title, note title)`
    - `recency_score` decays over years
    - `composite_score = 0.5 * quality + 0.3 * relevance + 0.2 * recency`
  - New CLI gates: `--min-relevance`, `--min-quality`, `--top-studies`,
    `--lookback-years`.
  - Evidence brief now exposes per-study scores so Claude can prefer
    higher-scoring sources when building `## Research Evidence`.
  - `StudyEvidence` dataclass extended with `relevance_score`,
    `quality_score`, `composite_score` fields and the cache stores them.
- `automation_scripts/seamless_update_pipeline.py`
  - New flags: `--validate-interlinks`, `--interlink-fail-on`,
    `--staged-apply`, `--staged-auto-yes`, `--min-relevance`,
    `--min-quality`, `--top-studies`, `--lookback-years`.
  - When `--validate-interlinks` is set, runs `interlink_validator.py`
    against the rewritten staging directory before promotion.
  - When `--staged-apply` is set, the apply step runs
    `staged_promotion.py` instead of the bulk script. Interactive by
    default; `--staged-auto-yes` accepts every file that passes
    validation gates.
- `README.md`, `HOW_IT_WORKS.md`, `tools/SCRIPT_STATUS.md`,
  `tools/WORKFLOW.md`
  - Documented the new evidence ranking, interlink validator, and staged
    promotion flow. Added a non-blocking File Format Optimisation
    Proposal in `README.md`.

## Notes

- `promote_rewritten_to_og.py` is unchanged and remains the bulk fallback.
  All new behaviour lives in `staged_promotion.py` and the validator;
  nothing existing was removed.
- Default exclusions in the interlink validator (the per-topic mirror
  folders, build artefacts, venvs, processing reports) bring the vault
  scan down from a noisy 21k-link / 14.6k-shadow report to a clean
  8.4k-link / 0-shadow report.
