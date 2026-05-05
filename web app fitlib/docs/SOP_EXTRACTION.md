# SOP: Obsidian Extraction Workflow

**Purpose:** Document the process for extracting content from your Obsidian vault, validating it, and deploying to production.

**Owner:** You (developer)  
**Frequency:** Triggered by vault changes OR manual weekly sync  
**Time Required:** 15 minutes (fully automated)  
**Success Criteria:** All 100+ nodes exported, wikilinks resolved, zero data loss

---

## 📋 Process Overview

```
Vault Update
    ↓
Trigger Extraction Script
    ↓
Parse Markdown Files
    ↓
Validate Data Integrity
    ↓
Resolve Wikilinks
    ↓
Extract Citations
    ↓
Generate fitlib_export.json
    ↓
Test Quality Gates
    ↓
Deploy to Firestore + Algolia
    ↓
Monitor & Alert
```

---

## 🚀 Step-by-Step Execution

### Step 1: Trigger Extraction
**Time: 2 minutes**

#### Option A: Automated (Recommended)
```bash
# Create GitHub Actions workflow (auto-runs on git push)
.github/workflows/extract-vault.yml

on: [push]
jobs:
  extract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Extract Obsidian Vault
        run: npm run extract:vault
      - name: Deploy to Firestore
        run: npm run deploy:data
```

#### Option B: Manual
```bash
# Run from project root
npm run extract:vault

# Or with watch mode (auto-re-extract on changes)
npm run extract:watch
```

---

### Step 2: Parse Markdown Files
**Time: 5 minutes (automated)**

**Script:** `scripts/extractVault.ts`

**Input:** All `.md` files in `/Users/enes/fitlibvault-main/`

**Process:**
```typescript
for each markdown file:
  1. Read file content
  2. Extract frontmatter (ID, created date, etc.)
  3. Parse heading structure
  4. Extract "Quick Takeaway" section
  5. Extract "Key Points" section
  6. Extract "Deep Dive" section
  7. Extract "Research Evidence" section
  8. Extract "Practical Applications" section
  9. Extract "Common Mistakes" section
  10. Extract "Related Concepts" section (contains [[wikilinks]])
  11. Store as NodeData object
```

**Expected Output:** Array of 100+ NodeData objects

---

### Step 3: Validate Data Integrity
**Time: 3 minutes**

**Validation Checklist:**

```javascript
✅ All required fields present:
   ├─ id (A1, B1, C1, etc.)
   ├─ title (non-empty string)
   ├─ series ('A' | 'B' | 'C' | 'E' | 'Other')
   ├─ content (markdown, >100 chars)
   └─ citations (array, each with DOI)

✅ Content quality checks:
   ├─ Title matches file name
   ├─ Content length >500 chars
   ├─ At least 1 citation per topic
   ├─ No broken formatting (valid markdown)
   └─ No duplicate content across nodes

✅ Citation quality checks:
   ├─ Author field populated
   ├─ Year field populated
   ├─ DOI or PubmedId present
   ├─ Study type is valid (Meta-Analysis, RCT, Review, Systematic Review)
   ├─ Credibility score between 0-1
   └─ Quality breakdown fields complete

⚠️ Warnings (logged, not errors):
   ├─ Missing citations (flag for manual review)
   ├─ Unusually short content (<200 chars)
   ├─ Old update date (>6 months)
   └─ Low credibility score (<0.6)
```

**If validation fails:**
```
1. Log error with node ID
2. Send alert email
3. Do NOT deploy to production
4. Rollback to last known good state
5. Require manual fix
```

---

### Step 4: Resolve Wikilinks
**Time: 2 minutes**

**Purpose:** Convert `[[A1. Energy Balance]]` → node_id: `A1`

**Process:**
```typescript
for each node:
  for each wikilink [[like_this]]:
    1. Extract link text: "like_this"
    2. Match against all node titles (fuzzy match)
    3. If found: store target node ID
    4. If NOT found:
       ├─ Log as "broken link"
       ├─ Add to wikilink_validation_report
       ├─ Mark for manual review
```

**Example:**
```markdown
Input:  [[A2. Basal Metabolic Rate (BMR)]]
Output: { target: "A2", label: "BMR and TDEE" }

Input:  [[B1. Progressive Overload]]
Output: { target: "B1", label: "Progressive Overload" }

Input:  [[NonExistentNode]]
Output: { broken: true, target: "NonExistentNode" }
       → Flagged in validation report
```

---

### Step 5: Extract Citations
**Time: 3 minutes**

**Source:** "Research Evidence" section of each node

**Process:**
```typescript
Parse citation blocks:

**Study Author, Year**
├─ Extract author (e.g., "Schoenfeld BJ")
├─ Extract year (e.g., "2021")
├─ Extract full title
├─ Extract journal name
├─ Extract DOI (if present)
├─ Extract study_type (detected from text)
├─ Calculate credibility_score:
│  ├─ If Meta-Analysis: 0.95
│  ├─ If RCT: 0.90
│  ├─ If Review: 0.85
│  ├─ If Systematic Review: 0.92
│  └─ Otherwise: 0.70
├─ Extract bias_risk (Low/Medium/High)
└─ Extract automationValidated (true/false)
```

**Example Parse:**
```
Input Text:
"Schoenfeld BJ, et al. (2021). Evidence-based guidelines for protein 
intake in older adults. Nutrients, 95(4), 989-994. 
DOI: https://doi.org/10.3390/nu13062021
Study type: Meta-Analysis
Evidence quality: High"

Output Object:
{
  id: "c1",
  author: "Schoenfeld BJ",
  year: 2021,
  title: "Evidence-based guidelines for protein intake in older adults",
  journal: "Nutrients",
  doi: "10.3390/nu13062021",
  type: "Meta-Analysis",
  credibilityScore: 0.98,
  qualityBreakdown: {
    studyDesign: 5,
    evidenceQuality: 5,
    biasRisk: "Low",
    automationValidated: true
  }
}
```

---

### Step 6: Generate fitlib_export.json
**Time: 2 minutes**

**Output Structure:**
```json
{
  "metadata": {
    "version": "1.0",
    "exported_at": "2026-05-03T14:30:00Z",
    "total_nodes": 105,
    "total_citations": 1200,
    "broken_wikilinks": 3,
    "validation_warnings": 12
  },
  
  "nodes": [
    {
      "id": "A1",
      "title": "A1. Energy Balance",
      "series": "A",
      "content": "# Markdown content...",
      "credibilityScore": 0.92,
      "citationCount": 5,
      "citations": [...],
      "links": ["A2", "C1", "B3"],
      "tags": ["energy", "metabolism"],
      "metadata": {
        "createdDate": "2025-04-23",
        "updatedDate": "2025-01-08",
        "updateLog": "Restructured for accessibility..."
      }
    },
    // ... 104 more nodes
  ],
  
  "wikilink_validation": {
    "total_wikilinks": 450,
    "resolved": 447,
    "broken": [
      {
        "source_node": "A1",
        "broken_link": "D1. Nonexistent",
        "issue": "Node D1 not found in vault"
      }
    ]
  }
}
```

**File saved to:** `scripts/data/fitlib_export.json`

---

### Step 7: Test Quality Gates
**Time: 2 minutes**

**Automated Tests:**
```bash
npm run test:extraction

Tests run:
✅ JSON structure validation
✅ All required fields present
✅ No duplicate node IDs
✅ All series values valid (A/B/C/E)
✅ Citation count > 0 per node
✅ Credibility scores between 0-1
✅ Wikilink resolution >95%
✅ Content length >100 chars per node
✅ No circular wikilink references
✅ File size < 50MB (archive safety)
```

**Success Criteria:**
```
✅ All 100+ nodes parsed
✅ Wikilink resolution >95% (broken <5)
✅ Citation validation >90%
✅ Zero file corruption
✅ All tests passing
```

**If Tests Fail:**
```
STOP - Do NOT deploy
1. Log failure details
2. Send alert email with issues
3. Require manual review
4. Fix validation issues
5. Re-run tests
6. Only then proceed to deployment
```

---

### Step 8: Deploy to Firestore + Algolia
**Time: 3 minutes**

#### Deploy to Firestore:
```bash
npm run deploy:firestore

Steps:
1. Connect to Firebase project
2. Create "nodes" collection (if not exists)
3. For each node in fitlib_export.json:
   ├─ Convert to Firestore document
   ├─ Set document ID = node.id
   ├─ Batch write (for performance)
4. Create "citations" subcollection
5. Index fields for search:
   ├─ title
   ├─ content
   ├─ series
   ├─ tags
   └─ credibilityScore
6. Verify write success
7. Log operation metrics
```

#### Deploy to Algolia:
```bash
npm run deploy:algolia

Steps:
1. Connect to Algolia API
2. Create/update "fitlib_nodes" index
3. Batch upload all nodes:
   ├─ node_id
   ├─ title
   ├─ content (searchable)
   ├─ series
   ├─ tags (faceted)
   ├─ credibilityScore (sortable)
   └─ citation_count
4. Set index settings:
   ├─ Searchable attributes: title, content
   ├─ Facets: series, tags, credibilityScore ranges
   ├─ Ranking: credibilityScore DESC, updated DESC
5. Verify index health
```

**Deployment Checklist:**
```
✅ Firestore write: <5 seconds
✅ Algolia index: <10 seconds
✅ All 100+ nodes deployed
✅ Search queries responding
✅ No data loss (compare row counts)
✅ Version updated in metadata
```

---

### Step 9: Monitor & Alert
**Time: Continuous**

**Monitoring Metrics:**
```
Real-time dashboard (Vercel/Firebase):
├─ Total nodes: 105 (target: 100+)
├─ Total citations: 1,200 (target: 1,000+)
├─ Broken wikilinks: 3 (target: <5)
├─ Last extraction: 2 hours ago (target: <1 week)
├─ Firestore usage: 0.5% (alert if >80%)
├─ Algolia usage: 2% (alert if >80%)
└─ Search latency: 45ms (alert if >500ms)

Alerts triggered if:
├─ Extraction fails
├─ Firestore write fails
├─ Algolia sync fails
├─ Broken wikilinks >10%
├─ Citation validation <80%
└─ Data size changes >20%
```

**Alert Channels:**
```
1. Email: Send daily summary
2. Slack (optional): Real-time alerts
3. GitHub: Log as issue if critical
4. Analytics dashboard: Visible 24/7
```

---

## 🔄 Weekly Sync Process (Recommended Schedule)

**Every Friday at 5 PM (auto or manual):**

```bash
# Full extraction + deployment
npm run extraction:full

# Generates report
✅ Extraction: 105 nodes (0 new since last week)
✅ Citations: 1,200 total (20 new)
✅ Wikilinks: 447 resolved, 3 broken
✅ Deployment: Success
✅ Data integrity: 100%
✅ Search sync: Complete
```

---

## ⚙️ Implementation Checklist

- [ ] Build `scripts/extractVault.ts` (Node.js script)
- [ ] Add validation logic
- [ ] Add wikilink resolution
- [ ] Add citation extraction
- [ ] Create Firestore deployment script
- [ ] Create Algolia sync script
- [ ] Add test suite
- [ ] Set up GitHub Actions workflow
- [ ] Create monitoring dashboard
- [ ] Document failure recovery procedures
- [ ] Test with current vault (100+ nodes)

---

## 🚨 Troubleshooting

### Issue: "Wikilink not resolving"
```
Cause: Node title doesn't exactly match wikilink text
Solution: 
  1. Check exact spelling/spacing
  2. Use fuzzy matching (80% similarity threshold)
  3. Log as broken, flag for manual review
```

### Issue: "Firestore write timeout"
```
Cause: Too many documents being written simultaneously
Solution:
  1. Reduce batch size (500 → 250 documents)
  2. Add 100ms delay between batches
  3. Retry failed batches
```

### Issue: "Algolia index not updated"
```
Cause: API key invalid or quota exceeded
Solution:
  1. Check API key in environment variables
  2. Verify Algolia quota (45/month free)
  3. Upgrade plan if necessary
  4. Clear old index and re-sync
```

---

## 📊 Success Metrics

**Track these weekly:**
```
Metric                      Target    Current   Status
─────────────────────────────────────────────────────
Extraction time             <5 min    3 min     ✅
Nodes exported              100+      105       ✅
Wikilinks resolved          >95%      97.1%     ✅
Citations per node          8-12      9.5       ✅
Deployment success          100%      100%      ✅
Broken links                <5        3         ✅
Data integrity              100%      100%      ✅
Search latency              <100ms    45ms      ✅
```

---

## 🔐 Backup & Recovery

**Daily backups:**
```
1. Firestore automatic backups (built-in)
2. Algolia backup (copy to S3)
3. GitHub commit (vault + export)
4. Local copy (latest fitlib_export.json)
```

**Recovery procedure (if corruption occurs):**
```
1. Restore Firestore from backup
2. Restore Algolia from backup
3. Re-run extraction script
4. Validate all data
5. Test in staging before production
```

---

## 📝 Documentation

**Keep these updated:**
- [ ] Extraction script README
- [ ] Environment variables documentation
- [ ] GitHub Actions workflow diagram
- [ ] Firestore schema documentation
- [ ] Algolia configuration documentation
- [ ] Troubleshooting guide

---

**Last Updated:** 2026-05-03  
**Next Review:** 2026-06-01  
**Owner:** You  
**Version:** 1.0
