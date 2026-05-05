# 🎯 Google AI Studio Workflow - Step-by-Step Guide

## Understanding Google AI Studio

**Important:** Google AI Studio (aistudio.google.com) is a **text-based conversation interface**, not a traditional file upload platform. You will:
- ✅ Paste content as TEXT into conversation prompts
- ✅ Reference your data structures in the text
- ✅ Have AI generate code based on descriptions
- ❌ NOT upload files directly to the interface

This guide walks you through the exact process.

---

## Part 1: Pre-Flight Checklist (5 minutes)

Before you start, gather these items:

### Files You Need Ready

**1. Export your data** (Run this first):
```bash
cd /Users/enes/fitlibvault-main
python3 export_for_google_ai_studio.py
```

This creates `fitlib_export.json` (~50-100MB). You don't need to submit this to Google AI Studio—it's reference data for your backend later.

**2. Open these files in your editor** (read-only reference):
- `database_schema.sql` — Your PostgreSQL structure (keep this open to copy sections)
- `GOOGLE_AI_STUDIO_PROMPTS.md` — Your 7 prompts (you'll copy-paste from here)
- `organized_library/automation_tools/README.md` — Your automation credibility docs

**3. Have Google AI Studio open:**
- Visit: https://aistudio.google.com/
- Sign in with your Google account
- Create new project: "FitLib Web App"

---

## Part 2: Step-by-Step Interface Walkthrough

### Step 1: Access Google AI Studio

```
1. Go to: https://aistudio.google.com/
2. Click "Sign in" (top right)
3. Select your Google account
4. Click "New project" (or "Create new")
5. Name it: "FitLib Web App"
```

Your screen should look like:
```
┌─────────────────────────────────────────┐
│ FitLib Web App          [Settings] [Share] │
├─────────────────────────────────────────┤
│                                             │
│ (Large text input area)                     │
│                                             │
│ [Send] button at bottom                    │
└─────────────────────────────────────────┘
```

### Step 2: Copy Prompt #1

Go to `GOOGLE_AI_STUDIO_PROMPTS.md` in your editor and:
1. Find: **PROMPT 1: Project Overview & Architecture**
2. Select the entire prompt text (from `Create a modern...` to the last backtick)
3. Copy it (Cmd+C)

### Step 3: Paste into Google AI Studio

In the Google AI Studio text box:
1. Paste the prompt (Cmd+V)
2. Review it
3. Click **[Send]** button
4. Wait for response (30-60 seconds)

Google AI will generate a detailed architecture plan and project structure.

### Step 4: Review & Save Output

The AI's response will appear below your prompt. You can:
- ✅ Copy the response
- ✅ Save to a text file
- ✅ Ask follow-up questions

**Continue to Prompt #2** with the same process.

---

## Part 3: What Each Prompt Needs

Here's what data each prompt references:

| Prompt # | Title | What It Needs | Where to Get It |
|----------|-------|---------------|-----------------|
| 1 | Project Overview | Project goals, tech stack | Prompt is self-contained |
| 2 | Knowledge Graph | Component architecture | Prompt is self-contained |
| 3 | Backend API | Database structure | Use database_schema.sql |
| 4 | Dashboard UI | User flow requirements | Prompt is self-contained |
| 5 | Citations | Citation data structure | Reference fitlib_export.json format |
| 6 | About Us | Automation credibility | Reference automation_tools/README.md |
| 7 | Mobile/Performance | Device specs, bundle targets | Prompt is self-contained |

**Important Note:** You're NOT uploading these files. You're referencing their structure in your prompts.

---

## Part 4: The 7-Prompt Sequence

### Prompt #1: Project Architecture (5 minutes)
**Location:** GOOGLE_AI_STUDIO_PROMPTS.md, line 34
- **What it does:** Sets up the entire project structure
- **AI will generate:** Folder structure, config files, architecture diagram
- **Action:** Copy, paste, send
- **Expected output:** 500-1000 words of architecture plan

### Prompt #2: Knowledge Graph Component (5 minutes)
**Location:** GOOGLE_AI_STUDIO_PROMPTS.md, line 93
- **What it does:** Creates the interactive D3.js visualization
- **AI will generate:** Complete KnowledgeGraph.tsx component
- **Action:** Copy, paste, send
- **Expected output:** 300-500 lines of React TypeScript code

### Prompt #3: Backend API Endpoints (5 minutes)
**Location:** GOOGLE_AI_STUDIO_PROMPTS.md, line 155
- **What it does:** Designs REST API with database queries
- **AI will generate:** Express.js routes with SQL integration
- **Action:** Copy, paste, send
- **Expected output:** Complete API router file (200-400 lines)

### Prompt #4: User Dashboard UI (5 minutes)
**Location:** GOOGLE_AI_STUDIO_PROMPTS.md, line 220
- **What it does:** Creates user dashboard components
- **AI will generate:** React Dashboard.tsx with Tailwind CSS
- **Action:** Copy, paste, send
- **Expected output:** Dashboard component + sub-components (300+ lines)

### Prompt #5: Citation Credibility Display (5 minutes)
**Location:** GOOGLE_AI_STUDIO_PROMPTS.md, line 263
- **What it does:** Creates citation card components
- **AI will generate:** CitationCard.tsx with styling
- **Action:** Copy, paste, send
- **Expected output:** Citation component with animations (200-300 lines)

### Prompt #6: About Us / Automation Page (5 minutes)
**Location:** GOOGLE_AI_STUDIO_PROMPTS.md, line 315
- **What it does:** Creates transparency page explaining your automation system
- **AI will generate:** AboutUs.tsx component with sections
- **Action:** Copy, paste, send (reference your automation_tools/README.md for credibility details)
- **Expected output:** About page component (250-350 lines)

### Prompt #7: Mobile & Performance (5 minutes)
**Location:** GOOGLE_AI_STUDIO_PROMPTS.md, line 365
- **What it does:** Optimizes everything for mobile and performance
- **AI will generate:** Mobile-responsive updates and optimization checklist
- **Action:** Copy, paste, send
- **Expected output:** Responsive design patterns + performance optimizations

---

## Part 5: What to Expect After Each Prompt

### After Prompt #1 (Architecture)
✅ You'll see:
- Project folder structure
- Technology choices explained
- File organization plan
- Integration strategy

💡 **What to do:** Ask follow-up questions if anything is unclear

### After Prompt #2 (Knowledge Graph)
✅ You'll see:
- Complete KnowledgeGraph.tsx code
- D3.js force simulation setup
- Event handlers (click, hover, drag)
- Styling/colors defined

💡 **What to do:** Copy this code into `frontend/src/components/KnowledgeGraph.tsx`

### After Prompt #3 (API)
✅ You'll see:
- Express.js route definitions
- PostgreSQL queries
- Middleware setup
- Error handling

💡 **What to do:** Copy into `backend/src/routes/api.js`

### After Prompt #4 (Dashboard)
✅ You'll see:
- Dashboard layout component
- Sub-components (Continue Reading, Progress, etc.)
- State management hooks
- Tailwind CSS classes

💡 **What to do:** Copy into `frontend/src/pages/Dashboard.tsx` and components folder

### After Prompt #5 (Citations)
✅ You'll see:
- CitationCard.tsx component
- Props interface
- Styling with credibility colors
- Responsive design

💡 **What to do:** Copy into `frontend/src/components/CitationCard.tsx`

### After Prompt #6 (About Us)
✅ You'll see:
- About page with sections
- Animation code
- Trust badges and metrics
- Links to your automation docs

💡 **What to do:** Copy into `frontend/src/pages/About.tsx`

### After Prompt #7 (Mobile)
✅ You'll see:
- Mobile adaptations for all components
- Service worker setup
- Performance optimization checklist
- Accessibility improvements

💡 **What to do:** Update all components with mobile-responsive versions

---

## Part 6: Downloading & Organizing Generated Code

### Option A: Google AI Studio Export
After all 7 prompts, Google AI Studio may offer:
1. **[Download Project]** button → saves complete project as ZIP
2. **[View on GitHub]** → pushes to GitHub repo
3. Copy-paste individual responses

### Option B: Manual Organization (Most Common)
Google AI generates code in text responses. Organize like this:

```
fitlib-web-app/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── KnowledgeGraph.tsx    (from Prompt #2)
│   │   │   ├── CitationCard.tsx      (from Prompt #5)
│   │   │   ├── Dashboard.tsx         (from Prompt #4)
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── About.tsx             (from Prompt #6)
│   │   │   └── ...
│   │   └── ...
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── src/
│   │   ├── routes/
│   │   │   └── api.js               (from Prompt #3)
│   │   └── ...
│   ├── package.json
│   └── ...
│
└── database/
    └── schema.sql                   (your existing file)
```

### How to Download Google AI Studio Responses
Each response has a **copy icon** (⎘) in the top-right:
1. Click the copy icon
2. Paste into a `.ts` or `.tsx` file
3. Save in the appropriate folder

Or use keyboard shortcut:
- Click the code block
- Cmd+A (select all)
- Cmd+C (copy)
- Paste into your IDE

---

## Part 7: Setting Up Your Backend with the Export Data

After generating code, import your actual content:

### Step 1: Set up database
```bash
# Create PostgreSQL database
createdb fitlib_db

# Import schema
psql fitlib_db < database_schema.sql
```

### Step 2: Import export data
Create `backend/import-data.js`:

```javascript
const fs = require('fs');
const db = require('./database-connection');

const data = JSON.parse(fs.readFileSync('/Users/enes/fitlibvault-main/fitlib_export.json'));

async function importData() {
  for (const node of data.nodes) {
    await db.query(
      'INSERT INTO nodes (id, title, series, content, credibility_score) VALUES ($1, $2, $3, $4, $5)',
      [node.id, node.title, node.series, node.content, node.credibilityScore]
    );
  }
  
  // ... repeat for citations, links, etc.
  console.log('✅ Data imported successfully');
}

importData().catch(console.error);
```

Then run:
```bash
node backend/import-data.js
```

---

## Part 8: Deployment (After Code Generation)

### Frontend Deployment (Vercel)
```bash
cd frontend
vercel deploy
# Vercel will ask for settings, accept defaults
```

### Backend Deployment (Railway)
```bash
cd backend
railway init
railway up
```

### Database (Supabase)
1. Create account: https://supabase.com
2. Create project
3. Run your schema in SQL editor
4. Update backend's DATABASE_URL

---

## Troubleshooting

### Problem: Google AI generates incomplete code
**Solution:** Ask follow-up questions like:
- "Complete the error handling section"
- "Add TypeScript interfaces for this component"
- "Show the database query for this endpoint"

### Problem: Code doesn't match your database schema
**Solution:** In your follow-up, reference the schema:
"Make sure all API queries match this PostgreSQL schema: [paste relevant schema section]"

### Problem: Missing component imports
**Solution:** Ask Google AI: "Add all necessary import statements at the top of this component"

### Problem: Can't find the code in responses
**Solution:** Ask Google AI: "Generate the complete KnowledgeGraph.tsx file with all imports and exports"

---

## Summary: The Actual Workflow

```
1. Run: python3 export_for_google_ai_studio.py
2. Open: https://aistudio.google.com/
3. Create new project: "FitLib Web App"
4. For each of 7 prompts:
   - Copy from GOOGLE_AI_STUDIO_PROMPTS.md
   - Paste into Google AI Studio
   - Send
   - Copy response
   - Organize into project structure
5. Set up database and import data
6. Deploy frontend to Vercel
7. Deploy backend to Railway
8. 🎉 Live!
```

---

## Next: You're Ready!

1. ✅ You have all 7 prompts ready in `GOOGLE_AI_STUDIO_PROMPTS.md`
2. ✅ You have export data ready with `export_for_google_ai_studio.py`
3. ✅ You have database schema ready
4. ✅ You have credibility documentation in `automation_tools/README.md`

**The workflow is now clear. Start with Prompt #1 and work through all 7 in sequence.**

Each prompt takes 5 minutes, total time: ~30-40 minutes to generate a complete codebase.

Then deployment takes another 30 minutes.

**Total time from scratch to live: ~2.5 hours** ✨

---

## Quick Reference: Open These Files

Keep these open in your editor while working:

1. **GOOGLE_AI_STUDIO_PROMPTS.md** — Copy-paste source
2. **database_schema.sql** — Reference for backend prompts
3. **organized_library/automation_tools/README.md** — For Prompt #6
4. **Google AI Studio browser tab** — Where you paste

That's it. You're ready to begin! 🚀
