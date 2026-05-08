# FitLib Quarterly Roadmap

**Purpose:** Define the specific features, milestones, and goals for each quarter.

**Owner:** You (updated quarterly)

**Current Timeline:** Q1 2026 → Q4 2026 + Q1 2027 preview

Last reviewed: 2026-05-08

---

## Status legend (added in 2026-05-08 audit)

- `[shipped]` — done in main; verifiable in code today.
- `[wip]` — partially built; functional in places, missing in others.
- `[planned]` — original target still standing, not yet started.
- `[stretch]` — exploratory; reconsider before committing time.

For a single-pane view of what is actually shipped today, see `/Users/enes/fitlibvault-main/CAPABILITIES.md`. For the live build snapshot, `DEVELOPMENT_PROGRESS.md`.

---

## 🎯 Q1 2026: Foundation & Launch (Jan - Mar 2026)

**Goal:** Get product live with 100+ nodes from Obsidian vault

### Infrastructure Setup (Week 1-2)
- `[shipped]` Firebase project creation (Firestore + Auth) — `firestore.rules`, `firebase-applet-config.json`
- `[shipped]` Algolia search service (optional; activates when env vars set) — `src/lib/algoliaService.ts`
- `[shipped]` Vercel deployment pipeline — `vercel.json` + `docs/VERCEL_DEPLOYMENT_CHECKLIST.md`. Project provisioning is the remaining op step.
- `[planned]` GitHub Actions CI/CD — not present today
- `[shipped]` Stripe account + webhook configuration — `server.ts /api/stripe/webhook`, test mode wired

**Time Budget:** 10 hours (setup weeks)

### Data Migration (Week 1-2)
- `[shipped]` Obsidian extraction script — `scripts/extractVault.ts`
- `[shipped]` Tested with 678 nodes (far exceeded the 105-node Q1 target) — see `stats.json`
- `[wip]` Wikilink resolution — 5,568 resolved, 542 broken; ongoing operator follow-up via `interlink_validator.py`
- `[shipped]` Citation extraction — 985 attached, all DOI / PMID-validated by the pipeline
- `[shipped]` Firestore deploy via `scripts/importData.ts` (admin importer panel on Dashboard)

**Time Budget:** 8 hours

### Web App Updates (Week 2-3)
- `[shipped]` React app reads from static content bridge with Firestore fallback — `src/services/nodeService.ts`
- `[shipped]` Algolia search service — `src/lib/algoliaService.ts` (optional via env vars)
- `[shipped]` Free tier restriction — 5 nodes (not 50; tightened during Q1)
- `[shipped]` Premium paywall + Stripe integration — `PremiumPaywall.tsx`, `stripeService.ts`
- `[planned]` ConvertKit email signup — not present today

**Time Budget:** 12 hours

### Launch Week (Week 4)
- `[shipped]` Landing page (`pages/Landing.tsx`) — live counters, four-pillar showcase
- `[planned]` ProductHunt submission
- `[planned]` Reddit posts
- `[planned]` Twitter thread launch
- `[planned]` Email to friends / network

**Time Budget:** 5 hours (marketing prep)

### Q1 Success Criteria
```
[planned] 500+ signups (ProductHunt launch)
[planned] 50+ premium conversions ($400 MRR)
[shipped] 678 nodes live with 985 citations (target: 105 / 1,200 — exceeded node count, undershot citation density target)
[planned] <100ms search latency (not yet measured in production)
[planned] 99.9% uptime (no production traffic yet)
[shipped] Zero critical bugs in current main
```

---

## 🎯 Q2 2026: Scale & Monetization (Apr - Jun 2026)

**Goal:** Grow to 2,000+ users, launch B2B API, 10+ API customers

### Product Improvements (Week 1-4)
- `[shipped]` Mobile responsiveness — Tailwind v4 throughout, tested in browser at standard breakpoints
- `[shipped]` Dark mode toggle — `src/lib/theme.ts` + `useTheme()` hook
- `[planned]` Offline PDF export (premium feature)
- `[shipped]` Bookmark/note system — `src/lib/favorites.ts` (localStorage), `recentlyViewed.ts`
- `[planned]` Citation export (BibTeX/APA)
- `[wip]` Advanced search filters — series/category filter present in `LibraryExplorer.tsx`; credibility / study-type filters not yet

**Time Budget:** 16 hours (ongoing feature work)

### B2B API Launch (Week 3-6)
- [ ] Design REST API endpoints
- [ ] Implement API authentication (API keys)
- [ ] Rate limiting (tiered by subscription)
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Beta launch to 3-5 coaches

**Time Budget:** 20 hours (API development)

### Content Growth (Week 1-13)
- [ ] Publish 25 new topics (2/week)
- [ ] Improve worst-performing topics (<4.0 quality)
- [ ] Add 200+ new citations
- [ ] Update all topics with new research

**Time Budget:** 52 hours (content: 4 hours/week)

### Email Marketing (Week 1-13)
- [ ] ConvertKit sequence: "5-part fitness science basics"
- [ ] Weekly education emails (research breakdowns)
- [ ] Premium upsell sequence
- [ ] API outreach campaign (50 coaches)

**Time Budget:** 8 hours (setup + sequences)

### Q2 Success Criteria
```
✅ 2,000+ total signups (4x growth)
✅ 120+ premium subscribers ($960 MRR)
✅ 5+ API customers ($300+ MRR)
✅ $1,260+ combined MRR
✅ 130 total nodes (25 new)
✅ <2% monthly churn rate
✅ 8+ avg citations per topic
```

---

## 🎯 Q3 2026: Product-Market Fit (Jul - Sep 2026)

**Goal:** Reach 5,000 users, prove API model, 10+ API customers

### Retention & Engagement (Week 1-13)
- `[shipped]` Reading streak — `userProgress/{uid}.studyStreak` tracked server-side, surfaced on Dashboard
- `[shipped]` Knowledge graph visualisations — `KnowledgeGraph.tsx` + `AmbientGraph.tsx`
- `[planned]` Personalised recommendations engine
- `[planned]` Expert Q&A section
- `[planned]` Mobile app (React Native or PWA-first)

**Time Budget:** 24 hours (engagement features)

### API Growth (Week 1-13)
- [ ] API customer support playbook
- [ ] Webhook notifications (real-time updates)
- [ ] White-label option for Enterprise tier
- [ ] Cold email campaign (100 founders)
- [ ] 10 paying customers target

**Time Budget:** 12 hours (sales + support)

### Content Expansion (Week 1-13)
- [ ] Publish 30 new topics (2-3/week)
- [ ] Reach 160 total nodes
- [ ] 1,500+ total citations
- [ ] Improve 10 lowest-quality topics

**Time Budget:** 60 hours (4-5 hours/week)

### Analytics & Insights (Week 1-13)
- [ ] Implement Looker Studio dashboard
- [ ] Cohort analysis (retention by signup source)
- [ ] Feature usage analytics
- [ ] Search behavior insights

**Time Budget:** 6 hours (dashboard setup)

### Q3 Success Criteria
```
✅ 5,000+ total signups (2.5x growth)
✅ 450+ premium subscribers ($3,600 MRR)
✅ 10+ API customers ($1,200-2,000 MRR)
✅ $4,800-5,600 combined MRR
✅ 160 total nodes (55 new this quarter)
✅ Mobile app launched (beta)
✅ <2% monthly churn (improving)
✅ 4.2+ average quality score
```

---

## 🎯 Q4 2026: Profitability & Sustainability (Oct - Dec 2026)

**Goal:** Reach $2,000+ MRR, establish sustainable 7-8 hr/week operation

### Revenue Optimization (Week 1-13)
- [ ] Premium price test ($9.99/mo variant)
- [ ] Annual subscription promotion (save 20%)
- [ ] API upsell strategy (Starter → Pro migrations)
- [ ] Corporate/Enterprise outreach (10 targets)

**Time Budget:** 8 hours (optimization)

### Operational Excellence (Week 1-13)
- [ ] Automation systems (reduce manual work)
- [ ] Standard operating procedures for all processes
- [ ] Customer support templates + chatbot (for common questions)
- [ ] Content review pipeline (minimize time per topic)

**Time Budget:** 12 hours (systems building)

### Content Maturity (Week 1-13)
- [ ] Publish 30 new topics (2-3/week)
- [ ] Reach 210+ total nodes
- [ ] All topics with 8+ citations
- [ ] Quarterly content audit

**Time Budget:** 60 hours (4-5 hours/week)

### Year 1 Wrap-up (Week 13)
- [ ] Document learnings (what worked, what didn't)
- [ ] Plan Year 2 strategy
- [ ] Celebrate milestones with team
- [ ] Prepare for next year

**Time Budget:** 4 hours

### Q4 Success Criteria
```
✅ $2,000+ combined MRR (4x Q1 target)
✅ Profitable operation (>70% gross margin)
✅ 7-8 hours/week sustainable (goal achieved)
✅ 500+ premium subscribers
✅ 20+ API customers
✅ 210+ total nodes
✅ 2,000+ total citations
✅ <1.5% monthly churn
✅ 99.9%+ uptime maintained
✅ Zero critical bugs
```

---

## 📅 Q1 2027 Preview (Jan - Mar 2027)

**Goal:** Transition to "scale mode" / prepare for Year 2

### Potential Features (Not Committed Yet)
- [ ] Community forums (coaches sharing insights)
- [ ] AI-powered coaching assistant (experimental)
- [ ] Advanced analytics dashboard (for coaches)
- [ ] Integration with popular coaching platforms
- [ ] Certification program (fitness professionals)

### Potential Expansions
- [ ] International content (non-English languages)
- [ ] Podcast (audio versions of topics)
- [ ] Video explainers (YouTube channel)
- [ ] Expert contributors (compensation model)

### Year 2 Revenue Goals (Preliminary)
```
Target: $50,000+ ARR

Breakdown:
├─ Premium subscriptions: $25,000
├─ API licensing: $20,000
├─ Premium features: $5,000+
└─ Partner revenue: TBD
```

---

## 🎯 Key Milestones (Year 1)

| Milestone | Target Date | Success Metric |
|-----------|-------------|----------------|
| **Product Launch** | End of Q1 | 500 signups |
| **First API Customer** | End of Q2 | $299 MRR |
| **10 API Customers** | End of Q3 | $1,000+ API MRR |
| **$2,000 MRR** | End of Q4 | Combined revenue |
| **210+ Topics** | End of Q4 | Content library |
| **5,000 Users** | End of Q4 | Total reach |
| **Profitability** | End of Q4 | Sustainable business |

---

## 📊 Quarterly Budget Allocation (7-8 hours/week avg)

### Q1 (Launch Priority)
```
Features/Setup:    35 hours
Content:           20 hours
Marketing:         5 hours
Total:             60 hours (launch is intensive)
```

### Q2-Q4 (Sustainable)
```
Content Creation:  40% (4 hours/week)
Product Features:  30% (3 hours/week)
API/B2B:          15% (1.5 hours/week)
Maintenance:       15% (1.5 hours/week)
Total:             ~32 hours/week (within 7-8 hrs = need to batch/automate)

Note: This assumes 4 weeks/month, 7-8 hours/week = 28-32 hours total
```

---

## 🚀 Decision Points (Review Quarterly)

**End of Q1:** 
- Is 10% conversion rate achievable? If <5%: Redesign free tier
- Is ProductHunt launch successful? If <300 signups: Plan paid ads

**End of Q2:**
- Are API customers interested? If 0 by Q2 end: Pivot to freemium focus only
- Is content keeping up? If <25 new topics: Reduce other priorities

**End of Q3:**
- Is product-market fit clear? If <4.5k users: Double down on acquisition
- Should we hire help? If burnout obvious: Consider contractor for content

**End of Q4:**
- Year 2 strategy: Scale or pivot?
- Profitability achieved? If >$2,000 MRR: Plan for growth
- If <$1,000 MRR: Consider repositioning/pricing changes

---

## 📝 How to Update This Document

**Every Quarter:**
1. Review what actually happened vs. plan
2. Celebrate wins (even small ones)
3. Document why things didn't go as expected
4. Adjust next quarter's plan accordingly
5. Commit update to GitHub

**Example Update:**
```
Q2 2026 ACTUAL RESULTS:
├─ Signups: 2,100 (target: 2,000) ✅
├─ Premium: 110 (target: 120) ⚠️ Slightly below
├─ API customers: 3 (target: 5) ⚠️ Need to push harder
├─ New topics: 22 (target: 25) ✅ Close enough
├─ MRR: $1,220 (target: $1,260) ✅ Nearly hit

LEARNINGS:
├─ API sales are slower than expected (need better positioning)
├─ Reddit channel is converting better than expected (invest more)
├─ Content creation is on track (keep 2/week pace)

ADJUSTMENTS FOR Q3:
├─ Add 3-hour weekly dedicated to API outreach
├─ Increase Reddit marketing budget
├─ Reduce feature work (32 → 24 hours/week)
└─ Increase content to 3/week (if pipeline works)
```

---

## ⚠️ Risk Mitigation

**Risk: Content can't keep up (burnout)**
```
Mitigation:
├─ Start with 1 topic/week (conservative)
├─ Batch content creation (2-hour blocks)
├─ Build templates to speed up process
├─ Hire freelance writers if hitting 5+ topics/week
```

**Risk: API customers don't materialize**
```
Mitigation:
├─ Launch freemium successfully first (base revenue)
├─ Don't force API—let market demand it
├─ If Q2 ends with 0 API: Pause API, focus on freemium
└─ Revisit B2B in Q4
```

**Risk: Churn increases over time**
```
Mitigation:
├─ Quarterly emails to inactive users
├─ Monthly feature releases (show progress)
├─ Premium community (coaches helping each other)
└─ Price anchoring (show value vs. competitors)
```

---

**Last Updated:** 2026-05-08
**Next Review:** 2026-07-01 (Q2 end)
**Owner:** You
**Version:** 1.1 (status tags added)

*This roadmap is flexible. Adjust based on real data each quarter.*

---

## What unexpectedly shipped ahead of schedule (delta from Q1 plan)

These items were not on the Q1 plan but landed during Q1:

- **Reader system** — `StackedReader`, `NoteReader`, `RecallSection`, `NoteHoverCard`, `EvidencePill`, `AmbientGraph`. Original plan deferred multi-panel reading to "Future Phases".
- **Active recall + FSRS** — `clozeGen.ts`, `srs.ts`, IndexedDB persistence. 508 cards generated automatically. Not in original Q1.
- **Automation pipeline (7 phases)** — `seamless_update_pipeline.py` with PubMed-backed rewrite, citation audit, DOI fixer, interlink validator, staged promotion. Not in original Q1; delivered through 354 promotions on 2026-05-08.
- **Content scope** — 678 nodes vs 105 target. Bridge architecture made it cheap to ship the full vault.

These items lagged the Q1 plan:

- **GitHub Actions CI/CD** — still not present.
- **Production deploy on Vercel** — project not provisioned yet (test builds only).
- **Live Stripe products** — test mode only.
- **ConvertKit / email capture** — not built.
- **ProductHunt / Reddit launch** — not yet.
