# SOP — Content Authoring & Publishing

Last reviewed: 2026-05-08

This is the canonical workflow for adding or improving a single note in the FitLib vault and getting it onto the live site. It describes what is actually wired today, end-to-end.

---

## What this SOP produces

A new or updated `*.md` file at the vault root that:

1. Conforms to the seven-section schema enforced by `web app fitlib/src/lib/noteSchema.ts`.
2. Has citations attached, validated against DOI / PubMed.
3. Has at least three outbound `[[wikilinks]]` that resolve.
4. Has been promoted through `staged_promotion.py` (date-stamped, atomically written, archived).
5. Is in the next `npm run content:build` snapshot, and therefore visible in the SPA after redeploy.

---

## The schema (this is the only valid template)

```markdown
### [ID]. [Title]
**ID:** [UNIQUE-ID]
**Created:** YYYY-MM-DD
**Updated:** YYYY-MM-DD

## Quick Takeaway
1–2 sentence plain-English actionable summary.

## Key Points
- Bottom-line claim 1
- Bottom-line claim 2
- ...

## Deep Dive
2–3 paragraphs of mechanistic exposition.

### Subtopic 1
Explanation with research reference.

### Subtopic 2
Explanation with research reference.

## Research Evidence

**Author et al. (Year).**
- Title: ...
- Journal: ...
- Type: Meta-Analysis | RCT | Systematic Review | Review
- DOI: https://doi.org/...
- Key finding: ...
- Sample size: N = ...
- Quality rating: High | Medium | Low

(Repeat per citation.)

## Practical Applications
- Application 1 (with example)
- Application 2 (with example)

## Common Mistakes
⚠️ Mistake 1 — explanation
⚠️ Mistake 2 — explanation

## Related Concepts
Understanding [[A2. Related Topic]] supports [[B3. Another Topic]].

## Update Log
- YYYY-MM-DD: What changed
```

The parser at `src/lib/noteSchema.ts` is case-insensitive on heading text but strict on heading level. Any section not in the schema is rendered raw at the bottom of the note.

---

## Recommended path: let the automation pipeline rewrite

For most updates the cheapest route is *not* writing the note from scratch — it is creating or editing a stub at the vault root and letting `process_fitness_library.py` rewrite it with PubMed-backed evidence.

```bash
# 1. Create the stub
cat > "/Users/enes/fitlibvault-main/X3. New Topic Title.md" <<'EOF'
### X3. New Topic Title
**ID:** X3-NEW-TOPIC
**Created:** 2026-05-08

## Quick Takeaway
Working hypothesis or one-sentence summary.

## Key Points
- (leave a few bullets the rewrite should expand on)

## Related Concepts
[[X1. Existing Topic]]
EOF

# 2. Run the pipeline for just this note
cd /Users/enes/fitlibvault-main
python3 organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py \
  --section X --start-num 3 --end-num 3 \
  --validate-interlinks --interlink-fail-on broken \
  --apply --staged-apply \
  --build-content
```

The pipeline performs all seven phases described in `organized_library/automation_tools/HOW_IT_WORKS.md`:

1. Rewrite via `process_fitness_library.py` (PubMed search + Claude composition).
2. HTTP-validate every DOI / PMID via `citation_validation_audit.py`.
3. Suggest fixes for broken citations via `citation_doi_fixer.py`.
4. Validate every `[[wikilink]]` via `interlink_validator.py`.
5. Dry-run promotion via `promote_rewritten_to_og.py`.
6. Stage the actual promotion via `staged_promotion.py` (per-file y/s/d/q with date stamping).
7. Rebuild the static content bridge via `npm run content:build`.

The note appears in the SPA after the next `vite build` + redeploy.

---

## Manual path: hand-author a note

When the topic is sensitive, controversial, or you want full editorial control, write the note by hand at the vault root and skip the rewrite phase:

```bash
python3 organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py \
  --section X --start-num 3 --end-num 3 \
  --skip-rewrite \
  --validate-interlinks --interlink-fail-on broken \
  --build-content
```

This still runs the citation audit, DOI fix suggestions, and interlink validation against your hand-written file. It just does not call the rewrite engine.

---

## Topic selection guide

The active gaps as of 2026-05-08 (compared against shipped sections):

| Section | Current | Notes |
|---|---|---|
| A — Foundational Concepts | 65 | Mature; only fill confirmed gaps |
| B — Resistance Training | 70 | Strong; add only at request |
| C — Nutrition & Diet | 106 | Strongest; only revisit / refresh |
| D — Weight Management | 3 | **Heavy gap** — high-value target |
| E — Cardio / Endurance | 15 | Mid; expand E15+ for endurance methods |
| F — Optimal Performance | 34 | Mid; expand to F45 with sleep / autonomic / mental |
| G — Special Populations | 16 | Mid; add G17+ for clinical conditions |
| H — Body Composition | 3 | **Heavy gap** — visceral / lean-mass / metabolic syndrome |
| I — Hormones & Fitness | 3 | **Heavy gap** — endocrine cascades |
| J — Technology | 10 | Mid; expand wearables / DEXA / VO2 hardware |
| K — Elite Performance | 12 | Sufficient |
| L — Cross-Training | 4 | Light; expand to L8+ |
| M — Recovery | 10 | Mid; expand to M15+ |
| N — Long-Term Development | 10 | Sufficient |
| O — Integrated Approaches | 8 | Light |
| P — Ethics | 10 | Sufficient |
| Q — Key Overviews | 8 | Sufficient |
| X — Sports-Specific | 30 | Strong |

Selection criteria, in priority order:

1. Fills an evidence-rich gap (≥5 high-quality studies in PubMed).
2. Connects to ≥3 existing notes for wikilink density.
3. Practical applicability — coaches / lifters can act on it.
4. Closes a paywall objection — covers something users specifically want unlocked.

Skip if: covered already, only 1–2 weak studies, niche audience (<100 lifters care), or fundamentally subjective.

---

## Citations — quality bar

Per note, target:

- **Minimum 8 citations** (the rewrite engine targets `--top-studies 5` evidence picks but you can manually keep more).
- At least **1 meta-analysis or systematic review**.
- **>70 % published in the last 5 years** (configurable via `--lookback-years`).
- **No low-quality study used as the primary support** for a claim.
- All citations **DOI- or PMID-resolvable**. The audit will fail otherwise.

Quality rubric used by `process_fitness_library.py`:

- Meta-analysis of RCTs → 0.95
- Systematic review → 0.92
- Multiple RCTs → 0.90
- Single RCT → 0.85
- Observational → 0.70
- Single small study → 0.60
- Case report → 0.40

---

## Wikilinks — rules that will not break

- Use the **exact node title** including series prefix: `[[A2. Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE)]]`.
- Match is case-insensitive but punctuation-sensitive.
- **Minimum 3 outbound** wikilinks per note. Place them in `Related Concepts` and inside `Deep Dive` where the analogue is mentioned.
- Bidirectional: if A1 links to A2, A2 should link back. The interlink validator will not auto-fail this, but it will surface candidates in `interlink_audit.md`.
- The static bridge will report broken links in `stats.json::brokenWikilinks`. The current count is 542; reducing it is an explicit operational goal.

---

## Style

- Active voice, present tense.
- Specific numbers (`0.8 g/kg`), not vague qualifiers (`about a gram`).
- No marketing language, no absolutes (`never`, `always`).
- Word count target: **1,200 – 2,000** per note.
- Quick Takeaway: **30 – 50 words**.
- Key Points: **5 – 8 bullets** — the cloze generator pulls from this section, so dense quantitative bullets produce more cards.

---

## Pre-publish checklist

Run through this before invoking `--apply`:

```
Schema:
[ ] All 7 sections present in this order: Quick Takeaway, Key Points, Deep Dive, Research Evidence, Practical Applications, Common Mistakes, Related Concepts
[ ] **ID:** front-matter line present
[ ] Created and Updated dates current

Content:
[ ] 1,200+ words
[ ] 8+ citations with DOI / PMID
[ ] 3+ outbound wikilinks
[ ] Update Log entry for this revision

Validation (run the pipeline in dry-run first):
[ ] Citation audit JSON has 0 invalid DOIs (or all flagged for replace in the DOI fix suggestions)
[ ] Interlink audit shows the new note's outbound links as `ok` (not `stub` or `broken`)
[ ] Promotion dry-run shows the file as ready

Operator:
[ ] You have read the rewritten file in `processed_archive/processed_notes/`
[ ] No hallucinated citations (cross-check at least 3 random DOIs in your browser)
```

---

## What `staged_promotion.py` does on accept

For each rewritten file the operator accepts, the script performs these actions atomically:

1. Stamps the OG note title with `(Updated: YYYY-MM-DD)`.
2. Appends a one-line `## Update Log` entry with citation deltas (new DOIs added, recommendations changed).
3. Atomically replaces the OG file (write-temp → fsync → rename).
4. Moves the rewritten source into `organized_library/processed_archive/confirmed_archive/<YYYY-MM-DD>/` so it cannot be re-promoted.
5. Appends a JSONL row to `organized_library/automation_tools/promotion_history.jsonl`:

```json
{"timestamp":"2026-05-08T15:39:32Z","promotion_date":"2026-05-08","file":"A. Foundational Concepts.md","id":"Foundation-Index-001","title":"Foundation Topics Index","new_dois":0,"new_pmids":0,"recommendation_delta":0,"rewritten_path":"...","og_path":"...","dry_run":false,"archived_to":"..."}
```

That JSONL is the operational source of truth for what was promoted, when, and what changed.

---

## Update cadence

- **Per release** — anything you author this week.
- **Quarterly** — refresh top-traffic notes (top 20 from analytics) with newer evidence.
- **Annually** — full audit; re-run the pipeline against every note older than one year and accept the rewrite if citations have moved on.

---

## Where each piece lives

| Concern | File |
|---|---|
| Schema parser | `web app fitlib/src/lib/noteSchema.ts` |
| Cloze generator | `web app fitlib/src/lib/clozeGen.ts` |
| Rewrite engine | `organized_library/automation_tools/processing_scripts/process_fitness_library.py` |
| Pipeline orchestrator | `organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py` |
| Citation audit | `organized_library/automation_tools/utility_scripts/citation_validation_audit.py` |
| DOI fix suggestions | `organized_library/automation_tools/utility_scripts/citation_doi_fixer.py` |
| Interlink validator | `organized_library/automation_tools/utility_scripts/interlink_validator.py` |
| Staged promotion | `organized_library/automation_tools/automation_scripts/staged_promotion.py` |
| Promotion history | `organized_library/automation_tools/promotion_history.jsonl` |
| Pipeline mechanics | `organized_library/automation_tools/HOW_IT_WORKS.md` |
| Pipeline runbook | `organized_library/automation_tools/tools/WORKFLOW.md` |

---

## Cross-references

- Reader / FSRS / cards operations: `SOP_KNOWLEDGE_READER_SYSTEMS.md`.
- Bridge / extraction internals: `SOP_EXTRACTION.md`.
- Quality targets: `KPIs.md` § "Content Metrics".
- Roadmap line items: `ROADMAP.md` § "Content".
