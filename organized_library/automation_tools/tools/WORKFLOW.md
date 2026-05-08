# Workflow (SOP)

Last reviewed: 2026-05-08

This is the recommended safe cycle for rewriting, validating, and promoting notes. Pair with `SCRIPT_STATUS.md` for the per-script status matrix and `../HOW_IT_WORKS.md` for the per-phase mechanics. For project-wide context, see `/Users/enes/fitlibvault-main/CAPABILITIES.md`.

The flow described below was last exercised on 2026-05-08 with **354 promotions** (`promotion_history.jsonl`).

## Preferred One-Command Pipeline

Run the full sequence with safety gates and per-file confirmation:

```bash
python3 "organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py" \
  --section C \
  --validate-interlinks --interlink-fail-on broken \
  --apply --staged-apply \
  --build-content
```

What this runs, in order:

- rewrite notes (PubMed-ranked evidence packet)
- citation audit
- DOI fix suggestions
- interlink validation (`--validate-interlinks`)
- promotion dry-run validation
- per-file confirmed promotion (`--staged-apply`) — interactive y/s/d/q.
  Pair with `--staged-auto-yes` for headless runs that still respect the
  validation gates.
- website content build (`--build-content`)

## Pause and resume long runs

**Pause (stop the job)**

- If it is running in a terminal you control: press **Ctrl+C** once and wait a few seconds.
- From another terminal, find and stop it:

```bash
pgrep -fl seamless_update_pipeline
pgrep -fl process_fitness_library
# Then:
kill <PID>
# If it refuses to exit:
kill -9 <PID>
```

Nothing is corrupted mid-note: each finished note leaves a full `rewritten_<same-name>.md` under `organized_library/processed_archive/processed_notes/`.

**Resume without redoing finished notes**

Use **`--refresh-only-stale`** so files that already have a fresh rewritten copy are skipped:

```bash
export ANTHROPIC_API_KEY='your-key-here'
python3 "organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py" \
  --section ALL \
  --refresh-only-stale \
  --stale-days 1 \
  --continue-on-error \
  --validate-interlinks --interlink-fail-on never \
  --apply --staged-auto-yes \
  --build-content
```

Notes rewritten within the last **`--stale-days`** window are skipped; anything that never got a `rewritten_*.md`, or whose rewritten file is older than that window, is processed again.

**Skip the exercise library (EXL) and start at section F**

Sorted filenames put every `EXL…` note before `F1.`. To bypass EXL entirely and continue from the first **F1** topic note:

```bash
python3 "organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py" \
  --section ALL \
  --exclude-name-prefix EXL \
  --resume-from-name "F1." \
  …same flags as above…
```

Use **`F.`** instead of **`F1.`** if you also want the overview file `F. Optimal Performance Factors.md` included at the start of the F block.

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

## 4) Validate Interlink Integrity

`python3 "organized_library/automation_tools/utility_scripts/interlink_validator.py" --scope rewritten --fail-on broken`

Review (full vault):

`python3 "organized_library/automation_tools/utility_scripts/interlink_validator.py" --scope vault --write-csv`

Outputs:
- `organized_library/processed_archive/processed_notes/interlink_audit_report.json`
- `organized_library/processed_archive/processed_notes/interlink_audit.md`

Resolve every entry in the "Broken Links" section before applying.

## 5) Validate Promotion (Dry Run)

`python3 "organized_library/automation_tools/automation_scripts/promote_rewritten_to_og.py"`

Fix all failed entries before apply.

## 6) Promote to OG (per-file confirmation)

```bash
python3 "organized_library/automation_tools/automation_scripts/staged_promotion.py" --interactive
```

Interactive prompts: `y` accept / `s` skip / `d` show full diff / `q` quit.
On accept the script:

- stamps the file with today's `(Updated: <date>)` and adds an
  `## Update Log` entry
- atomically replaces the OG file
- moves the rewritten file into
  `organized_library/processed_archive/confirmed_archive/<YYYY-MM-DD>/`
- writes a JSONL row to
  `organized_library/automation_tools/promotion_history.jsonl`

Headless variant: append `--auto-yes`. Bulk fallback (no per-file prompt):
`promote_rewritten_to_og.py --apply`.

## 7) Rebuild Website Content

Run npm commands from **`web app fitlib`** only; the vault/repo root has no `package.json`.

```bash
cd "web app fitlib"
npm run content:build
```

Local preview:

```bash
cd "web app fitlib"
npm run dev
```

## 8) Verify

- Confirm key nodes in `fitlib_export.json`
- Confirm node payload in `web app fitlib/public/content/nodes/*.json`
- Confirm cloze card payload in `web app fitlib/public/content/cards/*.json`
- Spot check critical links render correctly in app
- Spot check Reader mode + stacked links + recall cards in app
- For broken or stub wikilinks in rewritten notes, see `organized_library/processed_archive/processed_notes/interlink_audit.md` (re-run `interlink_validator.py` after edits).
- For DOI / citation link health, see `citation_audit_report.json` and `citation_audit_links.csv` in the same folder.

## 9) Commit and Push

- Commit once validation passes
- Push branch and open PR if needed
