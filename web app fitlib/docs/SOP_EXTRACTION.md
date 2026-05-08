# SOP — Vault Extraction & Content Bridge

Last reviewed: 2026-05-08

This is the operational doc for the vault → JSON bridge that feeds the SPA. Everything described here is implemented in `web app fitlib/scripts/`.

---

## What "extraction" means in FitLib

Two distinct extractions exist, and they are easy to confuse:

| Name | Script | Output | Used by |
|---|---|---|---|
| **Vault export** | `scripts/extractVault.ts` | `fitlib_export.json` (single mega-file) | Used by `scripts/importData.ts` to push into Firestore. Also a portable backup. |
| **Static content bridge** | `scripts/buildContentBridge.ts` | `public/content/{index.json, nodes/<id>.json, series/<S>.json, stats.json, cards.json, cards/<id>.json}` | Used by the SPA at runtime. This is the read path. |

The bridge builder calls `extractVault()` internally, then shards the result for static serving and runs `buildClozeCards.ts` at the end.

If you change a note in the vault, you almost always want `buildContentBridge.ts`, not `extractVault.ts` directly.

---

## Triggering an extraction

Default — invoked by the build:

```bash
cd "web app fitlib"
npm run content:build              # bridge only
npm run build                      # bridge + Vite production build
```

Standalone (occasional):

```bash
cd "web app fitlib"
FITLIB_VAULT_PATH=/Users/enes/fitlibvault-main npx tsx scripts/extractVault.ts
```

Via the automation pipeline (recommended after content updates):

```bash
python3 organized_library/automation_tools/automation_scripts/seamless_update_pipeline.py \
  --section A --start-num 1 --end-num 65 \
  --apply --staged-apply \
  --build-content
```

The `--build-content` flag is what shells out to `npm run content:build` from inside the pipeline.

---

## What `extractVault.ts` does

For each `.md` file under `FITLIB_VAULT_PATH` (default: parent of `web app fitlib`):

1. Read frontmatter (`---` delimited YAML at the top, if present).
2. Derive the node ID: prefer the explicit `**ID:**` line; fall back to a slug of the filename.
3. Parse the content into the canonical sections (`noteSchema.ts` schema). The seven recognised section headings are: `Quick Takeaway`, `Key Points`, `Deep Dive`, `Research Evidence`, `Practical Applications`, `Common Mistakes`, `Related Concepts`. Heading match is case-insensitive on text, strict on level.
4. Extract every `[[wikilink]]` from the content. Resolve against an in-memory map of `{title-or-id → canonical id}`. Unresolved targets are added to the `brokenWikilinks` count.
5. Extract every citation block under `Research Evidence`. Recognised pattern (regex):
   ```
   **<Author>. (<Year>). <Title>. <Journal>. Quality rating: High|Medium|Low
   ```
6. Compute a credibility score from the evidence-quality field.
7. Compute outbound `links[]` (resolved wikilink targets).
8. Compute an excerpt of up to 220 chars from the body for `NodeSummary`.

Output (`fitlib_export.json`) shape:

```json
{
  "version": "1.0",
  "exported_at": "<ISO timestamp>",
  "total_nodes": 678,
  "total_citations": 985,
  "broken_wikilinks": 542,
  "validation_warnings": 678,
  "nodes": [ /* full NodeData objects */ ]
}
```

This file is also kept at the repo root (`/Users/enes/fitlibvault-main/fitlib_export.json`) as a portable snapshot.

---

## What `buildContentBridge.ts` does

```
extractVault()
   │
   ▼
normalize each node:
   - excerpt to 220 chars
   - cap link list
   - tag-clean
   │
   ▼
shard:
   public/content/index.json          ← all 678 NodeSummary entries
   public/content/nodes/<id>.json     ← full body per node (678 files)
   public/content/series/<S>.json     ← grouped summaries by series letter
   │
   ▼
aggregate:
   public/content/stats.json          ← totals, evidence quality histogram, broken-wikilink count
   │
   ▼
buildClozeCards():
   public/content/cards.json          ← aggregate cloze deck (all cards across all nodes)
   public/content/cards/<id>.json     ← per-node cloze cards (lazy-loaded by RecallSection)
```

Series sharding currently produces files for **A, B, C, E, Other**. Notes in D, F, G, H, I, J, K, L, M, N, O, P, Q, X are folded into `Other`. The Library UI does not depend on the series shards at runtime — it filters off the `series` field in `index.json` — so this is purely a precomputed-size optimisation.

`stats.json` shape (current values from 2026-05-08):

```json
{
  "generatedAt": "2026-05-08T16:15:49.616Z",
  "totalNodes": 678,
  "totalCitations": 985,
  "averageCredibility": 0.50,
  "totalLinks": 5568,
  "series": [
    {"series":"Other","total":312,"totalLinks":2039,"averageCredibility":0.50},
    {"series":"E",    "total":118,"totalLinks":1736,"averageCredibility":0.50},
    {"series":"C",    "total":110,"totalLinks":1074,"averageCredibility":0.50},
    {"series":"B",    "total":72, "totalLinks":368, "averageCredibility":0.50},
    {"series":"A",    "total":66, "totalLinks":351, "averageCredibility":0.50}
  ],
  "totalCards": 508,
  "cardCoverage": 0.4174,
  "evidenceQuality": {"High":1109,"Medium":260,"Low":0,"Unknown":42},
  "totalEvidenceEntries": 1411,
  "brokenWikilinks": 542
}
```

---

## What `buildClozeCards.ts` does

For every per-node JSON file:

1. Parse the `Key Points` section.
2. Walk each bullet sentence and identify candidate spans:
   - Numeric ranges (e.g. `0.8–1.0 g/kg`) — weight 5
   - Percentages / quantities (e.g. `12 %`, `200 mg`) — weight 4
   - Acronyms (e.g. `BMR`, `RPE`, `1RM`) — weight 3
   - Capitalised noun phrases (e.g. `Sliding Filament Theory`) — weight 1
3. Generate one cloze card per span.
4. Stable card ID via FNV-1a hash of `(nodeId, index, span, point)`. **Crucial property: rebuilds preserve IDs**, so FSRS review history in IndexedDB survives content changes that do not touch the underlying span text.

Output:

- `public/content/cards.json` — every card across every node. Used by graph / dashboard for aggregate stats.
- `public/content/cards/<id>.json` — per-node card list. Lazy-loaded by `RecallSection.tsx` when a note is focused.

Coverage today: **508 cards across 678 nodes (41.7 %)**. Notes whose Key Points lack numeric / acronym / quantitative content produce zero cards. This is by design and is documented in `KPIs.md`.

---

## What `importData.ts` does

```bash
cd "web app fitlib"
FIREBASE_SERVICE_ACCOUNT_KEY="$(cat firebase-service-account.json)" \
  npx tsx scripts/importData.ts
```

1. Read `fitlib_export.json` (must be present; run `extractVault.ts` first).
2. Init `firebase-admin` from the service-account JSON in `FIREBASE_SERVICE_ACCOUNT_KEY`.
3. Batch writes (450 ops per batch, just under the 500-op Firestore limit) to:
   - `nodes/{id}` — full `NodeData` minus citations
   - `nodes/{id}/citations/{citationId}` — one document per citation

This is needed because:

- The SPA falls back to Firestore reads if the static bridge is unreachable.
- The Express backend's `/api/nodes` and `/api/nodes/:id` routes read from Firestore.
- The admin `DataImporter` component on the Dashboard wraps this script behind a UI for one-click reseed.

Run after every significant batch of promotions to keep Firestore in sync with the bridge.

---

## Validation gates

Each extraction produces these pass / warn signals, all recorded in `stats.json` and the Vite build log:

| Check | Where | Today's value |
|---|---|---|
| Total nodes extracted | `total_nodes` | 678 |
| Citations parsed | `total_citations` | 985 |
| Wikilinks resolved | `totalLinks` | 5,568 |
| Wikilinks broken | `brokenWikilinks` | 542 — operator follow-up |
| Card coverage | `cardCoverage` | 0.4174 — by design |
| Evidence quality | `evidenceQuality` | 1,109 High / 260 Medium / 0 Low / 42 Unknown |

The build does **not** fail on broken wikilinks. The interlink validator (run during the automation pipeline, not the bridge) is the gate that *can* fail builds via `--interlink-fail-on broken`.

---

## Failure modes & fixes

**Bridge build fails with "FITLIB_VAULT_PATH not found"**
→ Set the env var or run from inside `web app fitlib/` (the script defaults to its parent).

**Bridge build succeeds but a new note is missing from the SPA**
→ Confirm the note has a `**ID:**` line. Without it, the slug derivation may collide with an existing node, or the file may be silently skipped if it is in `processed_archive/processed_notes/` (the bridge ignores `rewritten_*.md` and backup artefacts).

**`stats.json::brokenWikilinks` jumped after a content batch**
→ Run `python3 organized_library/automation_tools/utility_scripts/interlink_validator.py --scope vault --write-csv` and review `interlink_audit.md`. Most often this is a renamed note breaking inbound links.

**`importData.ts` errors with "Permission denied" or "default credentials"**
→ `FIREBASE_SERVICE_ACCOUNT_KEY` is missing or malformed. The script logs the cause; the most common case is shell quoting eating quotes inside the JSON.

**Cards count drops on rebuild**
→ Spans changed in a Key Point. The FNV-1a hash includes the span text, so editing a Key Point invalidates the card and FSRS history is dropped *for that card only*. Other cards in the same note are preserved.

---

## Schedule

| Trigger | What runs |
|---|---|
| You change one note | `npm run content:build` (≈ 5–10 s) |
| You ran the automation pipeline | The `--build-content` flag triggers the bridge automatically |
| You want Firestore in sync | `extractVault.ts` then `importData.ts` |
| Production deploy | `npm run build` does the bridge as part of the production build |

---

## Cross-references

- Schema definitions used here: `web app fitlib/src/lib/noteSchema.ts`.
- The reader / cloze / FSRS systems that consume the bridge: `SOP_KNOWLEDGE_READER_SYSTEMS.md`.
- Authoring workflow that feeds the bridge: `SOP_CONTENT.md`.
- Pipeline that handles bulk extraction + promotion: `organized_library/automation_tools/HOW_IT_WORKS.md` and `tools/WORKFLOW.md`.
