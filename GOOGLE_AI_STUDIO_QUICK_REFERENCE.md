# 📋 Google AI Studio Quick Reference Card

**Print this and keep it handy!**

---

## The 7-Prompt Workflow at a Glance

```
┌──────────────────────────────────────────────────────────────────┐
│ GOOGLE AI STUDIO WORKFLOW - 1 PAGE CHEAT SHEET                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│ PREP (5 min):                                                     │
│ ✓ Run: python3 export_for_google_ai_studio.py                   │
│ ✓ Open: https://aistudio.google.com/                             │
│ ✓ Create project: "FitLib Web App"                               │
│                                                                    │
├──────────────────────────────────────────────────────────────────┤
│ PROMPTS (35 min total - 5 min each)                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│ 1️⃣  PROJECT OVERVIEW                                             │
│    ├─ Copy from: GOOGLE_AI_STUDIO_PROMPTS.md, line 34            │
│    ├─ Paste into: Google AI Studio                               │
│    ├─ Send & wait                                                │
│    └─ Generates: Architecture plan                               │
│                                                                    │
│ 2️⃣  KNOWLEDGE GRAPH COMPONENT                                    │
│    ├─ Copy from: GOOGLE_AI_STUDIO_PROMPTS.md, line 93            │
│    ├─ Paste into: Google AI Studio                               │
│    ├─ Send & wait                                                │
│    └─ Generates: KnowledgeGraph.tsx                              │
│                                                                    │
│ 3️⃣  BACKEND API ENDPOINTS                                        │
│    ├─ Copy from: GOOGLE_AI_STUDIO_PROMPTS.md, line 155           │
│    ├─ Reference: database_schema.sql                             │
│    ├─ Paste into: Google AI Studio                               │
│    ├─ Send & wait                                                │
│    └─ Generates: Express.js API routes                           │
│                                                                    │
│ 4️⃣  USER DASHBOARD UI                                            │
│    ├─ Copy from: GOOGLE_AI_STUDIO_PROMPTS.md, line 220           │
│    ├─ Paste into: Google AI Studio                               │
│    ├─ Send & wait                                                │
│    └─ Generates: Dashboard.tsx + subcomponents                   │
│                                                                    │
│ 5️⃣  CITATION CREDIBILITY DISPLAY                                 │
│    ├─ Copy from: GOOGLE_AI_STUDIO_PROMPTS.md, line 263           │
│    ├─ Paste into: Google AI Studio                               │
│    ├─ Send & wait                                                │
│    └─ Generates: CitationCard.tsx                                │
│                                                                    │
│ 6️⃣  ABOUT US / AUTOMATION TRANSPARENCY PAGE                      │
│    ├─ Copy from: GOOGLE_AI_STUDIO_PROMPTS.md, line 315           │
│    ├─ Reference: organized_library/automation_tools/README.md    │
│    ├─ Paste into: Google AI Studio                               │
│    ├─ Send & wait                                                │
│    └─ Generates: About.tsx page                                  │
│                                                                    │
│ 7️⃣  MOBILE RESPONSIVENESS & PERFORMANCE                          │
│    ├─ Copy from: GOOGLE_AI_STUDIO_PROMPTS.md, line 365           │
│    ├─ Paste into: Google AI Studio                               │
│    ├─ Send & wait                                                │
│    └─ Generates: Mobile optimizations for all components         │
│                                                                    │
├──────────────────────────────────────────────────────────────────┤
│ ORGANIZE GENERATED CODE (20 min)                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│ Create folder structure:                                          │
│ fitlib-web-app/                                                  │
│ ├── frontend/src/components/                                      │
│ │   ├── KnowledgeGraph.tsx        ← from Prompt 2               │
│ │   ├── CitationCard.tsx          ← from Prompt 5               │
│ │   └── Dashboard.tsx             ← from Prompt 4               │
│ ├── frontend/src/pages/                                          │
│ │   └── About.tsx                 ← from Prompt 6               │
│ ├── backend/src/routes/                                          │
│ │   └── api.js                    ← from Prompt 3               │
│ └── database/schema.sql           ← your existing file          │
│                                                                    │
├──────────────────────────────────────────────────────────────────┤
│ DEPLOY (30 min)                                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│ 1. Import data:                                                  │
│    node backend/import-data.js                                   │
│                                                                    │
│ 2. Frontend to Vercel:                                           │
│    cd frontend && vercel deploy                                  │
│                                                                    │
│ 3. Backend to Railway:                                           │
│    cd backend && railway init && railway up                      │
│                                                                    │
│ 4. Database on Supabase:                                         │
│    Run database_schema.sql in Supabase SQL editor                │
│                                                                    │
│ 🎉 LIVE!                                                         │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Which Files Reference What Data

| Prompt | References | File | Lines |
|--------|-----------|------|-------|
| 1 | Tech stack, goals | GOOGLE_AI_STUDIO_PROMPTS.md | 34-89 |
| 2 | Component architecture | GOOGLE_AI_STUDIO_PROMPTS.md | 93-151 |
| 3 | **Database structure** | database_schema.sql | all |
| 4 | User features | GOOGLE_AI_STUDIO_PROMPTS.md | 220-259 |
| 5 | Citation structure | fitlib_export.json | (reference format) |
| 6 | **Automation credibility** | organized_library/automation_tools/README.md | all |
| 7 | Performance specs | GOOGLE_AI_STUDIO_PROMPTS.md | 365-416 |

---

## Copy-Paste Locations

**Quick lookup for each prompt:**

```bash
# Prompt 1: Line 36-89 of GOOGLE_AI_STUDIO_PROMPTS.md
grep -n "Create a modern" GOOGLE_AI_STUDIO_PROMPTS.md

# Prompt 2: Line 96-151
grep -n "COMPONENT: \`KnowledgeGraph.tsx\`" GOOGLE_AI_STUDIO_PROMPTS.md

# Prompt 3: Line 157-216
grep -n "BASE URL: /api/v1" GOOGLE_AI_STUDIO_PROMPTS.md

# Prompt 4: Line 222-259
grep -n "LAYOUT: 3-column" GOOGLE_AI_STUDIO_PROMPTS.md

# Prompt 5: Line 265-311
grep -n "COMPONENT: \`CitationCard.tsx\`" GOOGLE_AI_STUDIO_PROMPTS.md

# Prompt 6: Line 317-361
grep -n "PAGE SECTIONS:" GOOGLE_AI_STUDIO_PROMPTS.md

# Prompt 7: Line 367-416
grep -n "MOBILE ADAPTATIONS:" GOOGLE_AI_STUDIO_PROMPTS.md
```

---

## What You'll Generate (Output Summary)

| Prompt | Output Size | File | Purpose |
|--------|-------------|------|---------|
| 1 | 500-1000 words | Plan | Architecture overview |
| 2 | 300-500 lines | .tsx | D3.js visualization |
| 3 | 200-400 lines | .js | Express routes |
| 4 | 300+ lines | .tsx | Dashboard UI |
| 5 | 200-300 lines | .tsx | Citation display |
| 6 | 250-350 lines | .tsx | About/transparency page |
| 7 | 100-200 lines | Various | Mobile/perf updates |

**Total code generated: ~1500-2500 lines**

---

## Troubleshooting Quick Fixes

| Problem | Fix |
|---------|-----|
| Incomplete code | Ask: "Complete the error handling" |
| Missing imports | Ask: "Add all imports at the top" |
| Code doesn't match schema | Reference: "Use this schema: [paste schema]" |
| Component not responding | Ask: "Add onClick handlers" |
| Styling looks wrong | Ask: "Use Tailwind CSS classes from theme" |
| Graph too slow | Ask: "Limit initial nodes to 200" |
| Mobile broken | Ask: "Show mobile-responsive version" |

---

## Success Checklist

- [ ] Ran export script
- [ ] Opened Google AI Studio
- [ ] Created "FitLib Web App" project
- [ ] Sent all 7 prompts in order
- [ ] Organized code into project structure
- [ ] Set up database
- [ ] Imported data
- [ ] Deployed frontend
- [ ] Deployed backend
- [ ] Tested knowledge graph
- [ ] Tested on mobile
- [ ] 🎉 Live and working!

---

## Timeline Estimate

| Step | Time |
|------|------|
| Export data | 1 min |
| 7 prompts (5 min each) | 35 min |
| Organize code | 15 min |
| Setup database | 10 min |
| Deploy frontend | 10 min |
| Deploy backend | 10 min |
| Testing | 10 min |
| **TOTAL** | **~90 min** |

---

## Key Reminders

✅ **DO:**
- Copy ENTIRE prompts (including all backticks)
- Wait for AI to finish before sending next prompt
- Reference files in follow-ups (e.g., "use this schema: [paste]")
- Ask for clarification if anything seems wrong
- Test each component as you go

❌ **DON'T:**
- Upload files to Google AI Studio (it doesn't accept them)
- Edit prompts (use them as-is)
- Send multiple prompts at once
- Forget to import your data into the database
- Deploy without testing

---

**You're ready! Start with Prompt #1 now.** 🚀
