# SOP — Knowledge Reader + Learning Systems

Purpose: explain every reader / FSRS / cloze system in plain operational terms so you can run, debug, and evolve it without context-switching to read source code.

Last reviewed: 2026-05-08

Current capacity (`public/content/stats.json`): 678 nodes, 985 citations, 5,568 wikilinks, 508 cards (41.7 % coverage), evidence quality 1,109 High / 260 Medium / 0 Low / 42 Unknown.

---

## 1) System map (what talks to what)

1. Markdown notes are processed into JSON (`content:build`).
2. Reader UI loads node JSON from `public/content`.
3. `noteSchema.ts` parses each note section into a typed model.
4. `clozeGen.ts` converts key points into recall cards.
5. `srs.ts` registers/reviews cards via FSRS and stores progress in IndexedDB.
6. `StackedReader` handles panel-stack reading and ambient graph background.
7. Access control is decided by premium status OR admin email allowlist.

---

## 2) Files and responsibilities

### Parsing and learning logic

- `src/lib/noteSchema.ts`
  - Parses canonical sections from markdown content
  - Source of truth for all section-level UX

- `src/lib/clozeGen.ts`
  - Builds cloze cards from key points
  - Includes answer grading helper

- `src/lib/srs.ts`
  - FSRS scheduler + Dexie persistence
  - Exposes card registration, due queue, review recording, stats

- `src/lib/noteStack.ts`
  - URL stack state helper (`?stack=...`)
  - Enables multi-panel reading with browser back/forward support

### UI components

- `src/components/StackedReader.tsx`
  - Layered reading mode
  - Ambient graph + stacked note columns + hover preview

- `src/components/NoteReader.tsx`
  - Structured rendering for one note
  - Includes `RecallSection` when focused

- `src/components/RecallSection.tsx`
  - Input-based retrieval, grading, FSRS rating buttons

- `src/components/AmbientGraph.tsx`
  - Dim graph background behind content panels
  - Frozen layout + low-cost drift animation

- `src/components/NoteHoverCard.tsx`
  - Quick linked-note preview to reduce context-switching

- `src/components/EvidencePill.tsx`
  - Visual high/medium/low/unknown evidence quality marker

### Build pipeline

- `scripts/buildContentBridge.ts`
  - Main content bridge build
  - Now invokes card build stage

- `scripts/buildClozeCards.ts`
  - Generates:
    - `public/content/cards.json`
    - `public/content/cards/{nodeId}.json`

---

## 3) Access control SOP (premium + admin)

### Rule

Full access if:

- premium subscription is active, OR
- logged-in user email exists in `VITE_ADMIN_EMAILS`

### Setup

In `.env.local`:

```bash
VITE_ADMIN_EMAILS=you@example.com,second-admin@example.com
```

### Verification checklist

1. Sign in with an admin email from the list.
2. Go to Library.
3. Confirm admin badge is visible in sidebar.
4. Confirm locked nodes are no longer locked.
5. Confirm no paywall shows when opening any node.

---

## 4) Reader mode SOP

### How to use

1. Open Library.
2. Select `Reader` mode in header.
3. Click a node from sidebar.
4. Click any wikilink in content; next note opens as right-side panel.
5. Use browser back to step through stack history.

### Operational expectations

- URL should include `?stack=...`
- Rightmost panel is the active learning context
- Recall section appears in focused panel

### If panel stack fails

1. Ensure node IDs in links resolve to existing nodes.
2. Check `node.links` payload for selected node.
3. Confirm `StackedReader` receives a non-empty `nodes` list.

---

## 5) Recall + FSRS SOP

### Daily loop

1. Open a note in focused reader panel.
2. Scroll to Recall section.
3. Attempt answer first (do not reveal immediately).
4. Rate each card (`Again` / `Hard` / `Good` / `Easy`).
5. Repeat consistently over days.

### Data persistence

- Storage: IndexedDB (`fitlib-srs`)
- Tables:
  - `cards`
  - `reviews`

### Debug steps

1. Open browser DevTools → Application → IndexedDB.
2. Confirm DB `fitlib-srs` exists.
3. After rating cards, confirm new review rows are inserted.

---

## 6) Content build SOP (with cards)

Run from `web app fitlib`:

```bash
npm run content:build
```

Expected outputs:

- `public/content/index.json`
- `public/content/nodes/*.json`
- `public/content/series/*.json`
- `public/content/cards.json`
- `public/content/cards/*.json`

If cards are missing:

1. Verify `buildContentBridge.ts` runs `buildCards()`.
2. Verify nodes exist in `public/content/nodes`.
3. Run standalone:

```bash
npx tsx scripts/buildClozeCards.ts
```

---

## 7) Owner weekly checklist (15 min)

1. Run `npm run content:build`.
2. Open Library in Reader mode.
3. Spot-check 3 notes:
   - sections render correctly
   - wikilink panel opens
   - recall cards appear
4. Sign in as admin and verify full access still works.
5. Run `npm run lint`.
6. Record findings in weekly standup doc.

---

## 8) Known constraints

- FSRS history is local browser storage (IndexedDB store `fitlib-srs`). Switching device loses progress. Cross-device sync is roadmap, not built.
- Reader mode currently enforces access based on the node list `Library.tsx` passes in. The 5-node free tier is enforced there; everything inside `StackedReader` assumes access has already been gated.
- Admin bypass depends on exact email match (normalised to lowercase) against `VITE_ADMIN_EMAILS`.
- Cloze cards exist for **41.7 %** of nodes — only notes whose Key Points contain numeric / acronym / quantitative spans produce cards. This is by design; tune `clozeGen.ts` weights to widen coverage.
- Series shards in `public/content/series/` cover only A, B, C, E, Other today. The Library UI does not depend on the shards (it filters off `index.json`), so this is invisible to users.
- FSRS config: `request_retention 0.9`, `maximum_interval 365 days`. Tune in `srs.ts` only after reading the FSRS-4 paper.

---

## 9) Upgrade path (when ready)

1. Add cloud sync for SRS reviews (Firestore per-user collection).
2. Add dedicated `/review` route for due cards queue.
3. Add reading-level toggles (Beginner/Practitioner/Researcher) in `NoteReader`.
4. Add analytics for recall completion rate and retention trend.

