# FitLib — Knowledge-base + Learning-science integration

This document tells you exactly how the new modules wire into the existing
Vite/React 19 app, what to install, what changed in the build pipeline, and
how to drop the new reader into `Library.tsx` without breaking anything you
already have.

## TL;DR

```bash
cd "web app fitlib"
npm install ts-fsrs dexie
npm run content:build       # now also emits cloze cards
npm run dev
```

`Library.tsx` is now wired with three modes:

- `Reader` (new stacked mode)
- `Graph View` (legacy graph explorer)
- `Card View` (legacy card listing)

The graph and cards views are still available.

## What landed

```
web app fitlib/
├── src/
│   ├── lib/
│   │   ├── noteSchema.ts       # parses your structured note schema -> typed sections
│   │   ├── clozeGen.ts         # Key Points -> fill-in-the-blank cards
│   │   ├── srs.ts              # FSRS-4 + IndexedDB review history
│   │   └── noteStack.ts        # ?stack=A1,A2 URL-driven navigation
│   └── components/
│       ├── EvidencePill.tsx    # High/Medium/Low/Unknown evidence badges
│       ├── NoteHoverCard.tsx   # Wikipedia-style [[wikilink]] popover
│       ├── AmbientGraph.tsx    # frozen-layout graph background, drifts on rAF
│       ├── NoteReader.tsx      # section-aware reader (TLDR, Key Points, Evidence, …)
│       ├── RecallSection.tsx   # the "test yourself" block (active retrieval)
│       └── StackedReader.tsx   # multi-column reader with the graph behind it
├── scripts/
│   ├── buildClozeCards.ts      # NEW: emits public/content/cards/*.json
│   └── buildContentBridge.ts   # PATCHED: now also runs buildClozeCards
└── INTEGRATION.md              # you are here
```

`Library.tsx` is now updated to use `NoteReader` and `StackedReader`, including
admin-access gating logic.

## Install the two new dependencies

```bash
cd "web app fitlib"
npm install ts-fsrs dexie
```

Why these two:

- **`ts-fsrs`** — FSRS-4 spaced-repetition scheduler. Empirically beats SM-2.
- **`dexie`** — typed IndexedDB wrapper. Local-first review history; no backend.

Both are small, well-maintained, and pure ES modules.

## Build pipeline changes

`scripts/buildContentBridge.ts` now imports and runs `buildClozeCards` after
the node JSON files are written. You don't need to call anything new — your
existing command:

```bash
npm run content:build
```

…now produces:

```
public/content/index.json
public/content/series/{A,B,C,…}.json
public/content/nodes/{nodeId}.json
public/content/cards.json              # NEW — aggregate cloze cards
public/content/cards/{nodeId}.json     # NEW — per-node cloze cards
```

You can also run the cards step on its own:

```bash
npx tsx scripts/buildClozeCards.ts
```

The script is deterministic — card ids are FNV-1a hashes of
`(nodeId, index, span, point)` so rebuilds preserve SRS history.

## Library integration status

This is now fully implemented in your codebase:

- Added `Reader` view mode and button in `Library.tsx`
- Added `StackedReader` render branch
- Replaced old markdown drawer body with `NoteReader`
- Preserved graph and card modes
- Preserved paywall for non-admin, non-premium users

## Admin access mode

You can grant full access without premium by email allowlist.

1. Set in `.env.local`:

```bash
VITE_ADMIN_EMAILS=you@example.com,second-admin@example.com
```

2. Log in with one of these emails.
3. Library shows an Admin badge and unlocks all nodes.

The check is implemented in:

- `src/lib/env.ts` (`adminEmails` parse)
- `src/lib/admin.ts` (`isAdminEmail`)
- `src/pages/Library.tsx` (admin + premium full-access logic)

## Historical wiring notes (kept for reference)

Your existing `Library.tsx` toggles between graph view and a drawer-on-top.
You have two options.

### Option A — minimal, keep current Library structure

Replace the drawer block with `<NoteReader>` while keeping the graph view as a
separate mode. This gives you the section-aware rendering and recall cards
without changing navigation.

```tsx
import { NoteReader } from '../components/NoteReader';

// Inside Library, replace the drawer's `<ReactMarkdown components={...}>` block:
{selectedNodeDetail && (
  <motion.div /* same drawer wrapper as today */>
    <NoteReader
      node={selectedNodeDetail}
      index={nodes}
      isFocused
      onClose={() => setSelectedNodeId(null)}
      onWikilinkOpen={(_from, target) => handleNodeAccess(target)}
    />
  </motion.div>
)}
```

That alone gives you: structured sections, evidence pills, common-mistakes
callouts, and the bottom-of-note recall cards. Zero routing changes.

### Option B — full layered experience (recommended)

Add a third view mode (`'reader'`) that uses `<StackedReader>`. Cards and
graph remain as they are.

```tsx
import { StackedReader } from '../components/StackedReader';
import { nodeService } from '../services/nodeService';

const [viewMode, setViewMode] = useState<'graph' | 'cards' | 'reader'>('reader');

// In the main area, add the third branch:
{viewMode === 'reader' && (
  <StackedReader
    nodes={nodes}
    fetchNode={async (id) => nodeService.getNodeById(id)}
    initialStack={selectedNodeId ? [selectedNodeId] : []}
  />
)}
```

Add a third button to the view-mode toggle in the header bar:

```tsx
<button
  onClick={() => setViewMode('reader')}
  className={cn(
    "px-4 py-1.5 rounded-md text-xs font-bold transition-all",
    viewMode === 'reader' ? "bg-blue-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"
  )}
>
  Reader
</button>
```

The StackedReader manages its own URL state via `?stack=…` so back/forward
work naturally — no extra wiring.

## Pedagogy controls you can dial

In `src/lib/srs.ts`:

- `request_retention: 0.9` — target recall probability. Lower (0.85) means
  longer intervals and easier reviews; higher (0.93) means more frequent
  reviews and stronger memory. 0.9 is the sweet spot for desirable difficulty.
- `maximum_interval: 365` — caps card intervals at a year. Bump to 730 for
  long-tail content if your learners stay around.

In `src/lib/clozeGen.ts`:

- The candidate weights (numeric ranges = 5, percentages = 4, acronyms = 3,
  capitalised noun phrases = 1) decide what gets blanked out. Tune the weights
  to favour the kind of information your learners need to recall. If you find
  cards are too easy, increase the noun-phrase weight so longer multi-word
  spans get blanked.

## Performance notes

- `AmbientGraph` runs the d3-force simulation **once** on mount, freezes the
  layout, caches it in `localStorage` keyed by node-set hash, then animates
  with a tiny per-frame transform offset. CPU is near-zero on mobile.
- `NoteHoverCard` uses a 180ms enter delay to avoid flicker when scanning.
- All new components are SSR-safe except `srs.ts`, which gates Dexie behind
  `typeof window !== 'undefined'` checks via the lifecycle pattern.

## Testing the recall pipeline

1. Open any note in the StackedReader. The recall block appears at the bottom
   of the focused column.
2. Type an answer (or click "Show answer"), then rate it.
3. Refresh the page. The card you reviewed will be due again at the FSRS-
   computed interval. The store survives refresh because reviews live in
   IndexedDB.
4. To inspect: in DevTools → Application → IndexedDB → `fitlib-srs` →
   `cards` and `reviews`.

## Future hooks

A few extension points the architecture supports without further refactoring:

- **"Explain it like I'm…" toggle.** Pre-generate three reading levels of the
  Deep Dive at content build time using your existing Anthropic pipeline,
  store them as `content.beginner`, `content.practitioner`, `content.researcher`
  in the node JSON, and `NoteReader` can swap them on a state toggle.
- **Daily review queue.** `getDueCards(undefined, 20)` from `srs.ts` returns
  the global queue across all notes; render it as a `/review` route.
- **Pretest hook.** Add a one-question `<input type="range">` above the
  Quick Takeaway in `NoteReader.tsx` for a curiosity-gap pretest. Even
  failed pretests improve retention (Richland et al. 2009).

## What was *not* changed

To stay surgical, the following remain exactly as they were:

- `KnowledgeGraph.tsx` — still used by graph-only view.
- `wikilinks.ts` — `NoteReader` reuses `buildWikilinkResolver` and
  `convertWikilinksToMarkdown` directly.
- `nodeService.ts`, `firestoreService.ts`, `algoliaService.ts`.
- The Vite config and content build outputs (additive only).

If you decide to migrate to Next.js later for SEO and MDX, the only files
that need re-platforming are the readers and the build script — the
parser, generator, and SRS modules are framework-agnostic.
