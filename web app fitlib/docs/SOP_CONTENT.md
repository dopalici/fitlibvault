# SOP: Content Curation & Publishing Workflow

**Purpose:** Document the process for researching, writing, reviewing, and publishing new fitness content to the knowledge base.

**Owner:** You (researcher/writer)  
**Frequency:** 1-3 new topics per week  
**Time Required:** 2-4 hours per topic (research + writing + linking)  
**Success Criteria:** 95%+ citation accuracy, >8 citations per topic, proper wikilinks

---

## 📋 Content Creation Pipeline

```
Topic Selection
    ↓
Research & Literature Review
    ↓
Outline Structure
    ↓
Write Markdown
    ↓
Add Citations (with validation)
    ↓
Create Wikilinks
    ↓
Peer Review (optional)
    ↓
Publish to Obsidian Vault
    ↓
Trigger Extraction + Deployment
```

---

## 🎯 Step-by-Step Process

### Step 1: Topic Selection
**Time: 15 minutes**

**How to Choose Topics:**

```
Priority Tiers:

TIER 1: Foundational (Series A)
├─ A1-A50: Core physiology, biomechanics, training principles
├─ Rationale: Users need these to understand everything else
├─ Frequency: Cover 80% of concepts

TIER 2: Training Applications (Series B)
├─ B1-B80: Specific training methods, periodization, techniques
├─ Rationale: Coaches use these for programming
├─ Frequency: 15% of new content

TIER 3: Nutrition & Recovery (Series C)
├─ C1-C105: Nutrition, supplements, recovery strategies
├─ Rationale: Completes the knowledge base
├─ Frequency: 5% of new content
```

**Selection Criteria:**
```
✅ Fills a gap in existing knowledge base
✅ Backed by strong research (>5 high-quality studies)
✅ Practical application (not just theoretical)
✅ Connects to 3+ existing topics (for wikilinks)
✅ High-value content (impacts 1,000+ users)

❌ Avoid if:
├─ Already covered in existing nodes
├─ Weak research (only 1-2 low-quality studies)
├─ Niche topic (only 100 people care)
├─ Controversial (too subjective for evidence-based approach)
```

**Example Topic Selection:**
```
GOOD: "Protein Timing Myth" 
├─ Gap: Coaches still believe in anabolic window
├─ Research: 15+ RCTs showing 30-min window is myth
├─ Application: Coaches can confidently tell clients when to eat
├─ Connections: A1 (Energy Balance), B3 (Hypertrophy), C1 (Calories)
└─ Value: 10,000+ coaches × $50 better programming = $500K value

WEAK: "Exotic Supplement XYZ"
├─ Gap: Maybe, but very niche
├─ Research: Only 2 studies, both low quality
├─ Application: Few coaches care
├─ Value: 100 users max
```

---

### Step 2: Research & Literature Review
**Time: 60-120 minutes**

**Research Workflow:**

```
Step A: Identify Key Questions
├─ What is this topic?
├─ Why does it matter for fitness?
├─ What are the key mechanisms?
├─ What are practical applications?
├─ What are common misconceptions?

Step B: Search Literature (30 minutes)
├─ PubMed (pubmed.ncbi.nlm.nih.gov)
│  ├─ Search query: "protein synthesis aging"
│  ├─ Filter: Last 5 years, humans, English
│  ├─ Export: 20-50 abstracts
│
├─ Google Scholar (scholar.google.com)
│  ├─ Cross-check results
│  ├─ Find related citations
│  ├─ Identify meta-analyses (high value)
│
└─ Semantic Scholar (semanticscholar.org)
   ├─ Find highly-cited papers
   ├─ Identify research clusters
   └─ Find best review articles

Step C: Screen & Select (30 minutes)
├─ Read abstracts: 20-50
├─ Select high-quality: 15-20
│  ├─ Meta-analyses (highest priority)
│  ├─ Systematic reviews (high priority)
│  ├─ RCTs (good)
│  ├─ Reviews (supplement with RCTs)
│  └─ Exclude: editorials, opinion pieces
│
└─ Create list of sources

Step D: Deep Read (30-60 minutes)
├─ Read full text of 8-12 best papers
├─ Extract:
│  ├─ Key findings
│  ├─ Sample sizes
│  ├─ Study quality
│  ├─ Limitations
│  └─ DOI/PubmedID
│
└─ Note: Synthesize findings into narrative
```

**Research Quality Checklist:**
```
✅ Minimum 8 citations per topic
✅ At least 1 meta-analysis
✅ Recent studies (>70% from last 5 years)
✅ Mix of study types (RCTs, reviews, observational)
✅ No low-quality evidence as primary support
✅ Contradictions noted & contextualized
```

---

### Step 3: Outline Structure
**Time: 15 minutes**

**Standard Template (required format):**

```markdown
### [ID]. [Title]
**ID:** [UNIQUE-ID]
**Created:** YYYY-MM-DD

## Quick Takeaway
[1-2 sentence summary, plain English, actionable]

## Key Points
- Point 1 (most important)
- Point 2
- Point 3
- ...

## Deep Dive
[2-3 paragraphs explaining the concept in detail]

### [Subtopic 1]
[Explanation with research reference]

### [Subtopic 2]
[Explanation with research reference]

## Research Evidence

**[Author] et al. ([Year]).**
- Title: [Full title]
- Journal: [Journal Name]
- Type: [Meta-Analysis|RCT|Review|Systematic Review]
- DOI: [https://doi.org/...]
- Key finding: [Brief summary]
- Evidence quality: [High|Medium|Low]

## Practical Applications
- Application 1 (with example)
- Application 2 (with example)
- Application 3 (with example)

## Common Mistakes
⚠️ Mistake 1 (with explanation)
⚠️ Mistake 2 (with explanation)

## Related Concepts
Understanding [[A2. Related Topic]] helps with [[B3. Another Topic]].

## Update Log
- YYYY-MM-DD: What changed
```

---

### Step 4: Write Markdown
**Time: 60-90 minutes**

**Writing Style Guide:**

```
TONE: Expert + Accessible
├─ Write like explaining to a smart friend
├─ Avoid jargon (or define it immediately)
├─ Use analogies for complex concepts
├─ Balance detail with readability

STRUCTURE:
├─ Short paragraphs (2-3 sentences)
├─ Clear topic sentences
├─ Numbers/data when possible
├─ Avoid marketing speak

LANGUAGE:
✅ Use active voice
✅ Use present tense
✅ Use specific numbers ("0.8g/kg" not "about a gram")
✅ Use precise terms
✅ Use bold for key concepts

❌ Avoid:
├─ Emotional language ("this will CHANGE your LIFE")
├─ Absolute statements ("never do this")
├─ Outdated references ("as everyone knows...")
├─ Unclear pronouns ("it" without antecedent)

EXAMPLE (Bad):
"Protein is really important and you should eat lots of it."

EXAMPLE (Good):
"Protein intake of 0.8-1.0 g/kg body weight daily supports 
muscle protein synthesis when combined with resistance training."
```

**Word Count Targets:**
```
Quick Takeaway: 30-50 words
Key Points: 5-8 bullets
Deep Dive: 500-1,000 words
Practical Applications: 200-300 words
Common Mistakes: 150-250 words
───────────────────────────
Total: 1,200-2,000 words per topic
```

---

### Step 5: Add Citations (With Validation)
**Time: 45 minutes**

**Citation Format (Required):**

```markdown
**[Author Initials] [Last Name] et al. ([Year]).**
- Title: "[Exact title from paper]"
- Journal: "[Journal name]"
- Type: [Meta-Analysis|RCT|Systematic Review|Review]
- DOI: https://doi.org/[xxxx]
- Key finding: "[1-2 sentence summary of main result]"
- Study design: [Brief design note]
- Sample size: [N = X participants]
- Quality rating: [High|Medium|Low]
- Evidence for automation: [automationValidated: true|false]

Example:
**Schoenfeld BJ, et al. (2021).**
- Title: "Evidence-based guidelines for protein intake in older adults"
- Journal: Nutrients
- Type: Meta-Analysis
- DOI: https://doi.org/10.3390/nu13062021
- Key finding: "Higher protein intake (>1.0 g/kg) necessary to maintain 
  muscle mass in aging population"
- Sample size: N = 35 RCTs reviewed
- Quality rating: High
- Evidence for automation: automationValidated: true
```

**Citation Validation Process:**

```
For each citation:
1. Verify DOI exists and is active
   ├─ Search: https://doi.org/[DOI]
   ├─ Should resolve to PubMed/journal
   └─ If broken: note as "unverified"

2. Verify study type
   ├─ Meta-Analysis: Claims to review 10+ studies
   ├─ Systematic Review: Structured search methodology
   ├─ RCT: Random assignment to conditions
   ├─ Review: Narrative summary of literature
   └─ Other: Note exact type

3. Verify author names
   ├─ Match first author exactly
   ├─ Check year matches publication year
   └─ Verify journal name

4. Rate evidence quality
   ├─ Meta-Analysis of RCTs: High (0.95)
   ├─ Multiple RCTs: High (0.90)
   ├─ Single RCT: Medium-High (0.85)
   ├─ Systematic review: High (0.92)
   ├─ Observational studies: Medium (0.70)
   ├─ Single study: Low-Medium (0.60)
   └─ Case reports: Low (0.40)

5. Check for automation flag
   ├─ automationValidated: true
   │  └─ (future: automated extraction from CrossRef API)
   └─ automationValidated: false
      └─ (manually verified citations)
```

**Target: 8-12 citations per topic minimum**

---

### Step 6: Create Wikilinks
**Time: 15 minutes**

**Wikilink Rules:**

```
FORMAT:
[[A2. Basal Metabolic Rate (BMR)]]
    ↑ Matches exact node title
    
USAGE:
- Link to topics that build on this one
- Link to related mechanisms
- Link to practical applications
- Link from "Deep Dive" sections
- Link from "Related Concepts" section

RULES:
✅ Use exact node title (case-sensitive)
✅ Include series prefix (A1, B3, C25)
✅ At least 3 outbound links per topic
✅ Bidirectional links (if A1 links to A2, A2 should link back)

EXAMPLES:
"Understanding [[A2. Basal Metabolic Rate (BMR)]] helps..."
"This relates to [[B3. Hypertrophy Training Principles]]"
"See also [[C1. Caloric Targets]] for application"

VALIDATION:
1. Check target node exists in vault
2. Match exact spelling/spacing
3. Extract link in "Related Concepts" section
4. Validate during extraction (broken links flagged)
```

---

### Step 7: Peer Review (Optional but Recommended)
**Time: 30 minutes**

**Review Checklist:**

```
By: External expert (exercise scientist, researcher, coach)

CONTENT ACCURACY:
☐ Claims supported by cited research
☐ No misrepresentation of studies
☐ Correct terminology
☐ Proper interpretation of findings

WRITING QUALITY:
☐ Clear and accessible language
☐ Logical flow
☐ Proper grammar/spelling
☐ Formatting consistent

COMPLETENESS:
☐ All major subtopics covered
☐ Sufficient citations (8+)
☐ Practical applications included
☐ Common mistakes addressed

FEEDBACK TEMPLATE:
"Content accuracy: ✅ High
Clarity: ✅ Good
Completeness: ✅ All major points covered
Suggestions: [Any edits needed]
Approved: YES / NEEDS REVISION"
```

---

### Step 8: Publish to Obsidian Vault
**Time: 10 minutes**

**Process:**

```bash
1. Create new file: /Users/enes/fitlibvault-main/[ID]. [Title].md
2. Paste formatted markdown
3. Add frontmatter:
   ID: [A1, B3, C25, etc.]
   Created: YYYY-MM-DD
   Updated: YYYY-MM-DD
4. Save file
5. Commit to Git: git add . && git commit -m "Add [ID]. [Title]"
6. Push to GitHub: git push origin main

Optional: Sync to Obsidian mobile
├─ If using Obsidian Sync: Auto-syncs
├─ If using iCloud: Manual sync (Ctrl+S)
└─ If using Git: Pull on other devices
```

---

### Step 9: Trigger Extraction + Deployment
**Time: 5 minutes**

```bash
# Automated (if using GitHub Actions)
# Just push and GitHub Actions runs:
# - Extract vault
# - Deploy to Firestore
# - Update Algolia
# - Deploy web app

# Manual (if no CI/CD)
npm run extract:vault
npm run deploy:firestore
npm run deploy:algolia
```

**Verification:**
```
Check these within 5 minutes:
✅ New topic appears in web app search
✅ Citation display works
✅ Wikilinks resolve to other topics
✅ Knowledge graph updated with new connections
✅ Mobile app refreshed
```

---

## 📊 Content Quality Metrics

**Track for each new topic:**

| Metric | Target | How to Measure |
|--------|--------|--------|
| Wikilinks | 3+ | Count [[links]] in markdown |
| Citations | 8+ | Count [Study] blocks |
| Citation avg quality | >0.85 | Sum quality scores / count |
| Word count | 1,200-2,000 | Word count in markdown |
| Readability | Grade 10-12 | Flesch-Kincaid grade level |
| Peer review | 1+ expert | Get feedback before publishing |
| Update log | Complete | Document changes made |

---

## 🎯 Weekly Content Goals

```
FREQUENCY TARGET:

Conservative: 1 new topic/week
├─ Time: 4 hours/week
├─ Add 52 topics/year
└─ Reach 150+ total by Year 1

Ambitious: 3 new topics/week
├─ Time: 12 hours/week (may not fit 7-8 hr schedule)
├─ Add 156 topics/year
└─ Reach 250+ total by Year 1

RECOMMENDED: 2 topics/week
├─ Time: 8 hours/week
├─ Add 104 topics/year
├─ Reach 200+ total by Year 1
└─ Sustainable with university schedule
```

---

## ✅ Pre-Publish Checklist

Before hitting "Publish":

```
Content:
☐ All sections filled (Quick Takeaway through Update Log)
☐ 1,200+ words
☐ 8+ citations with full metadata
☐ 3+ wikilinks to related topics

Citations:
☐ All DOIs verified (links work)
☐ Author names match exactly
☐ Years correct
☐ Study types accurate
☐ Quality scores assigned

Formatting:
☐ Markdown renders correctly
☐ No broken links
☐ Proper heading hierarchy
☐ No spelling errors

Wikilinks:
☐ All links target existing nodes
☐ Exact title match (case-sensitive)
☐ Minimum 3 outbound links
☐ Bidirectional links in place

Before publishing to production:
☐ Peer reviewed by 1+ expert
☐ All feedback addressed
☐ Final proofread
☐ File saved to vault
☐ Git commit with message
```

---

## 🔄 Content Update Schedule

**Revisit & Update Topics:**

```
Monthly: Review popular topics for outdated research
├─ Check if new meta-analyses published
├─ Update if major findings change

Quarterly: Deep review of 5-10 foundational topics
├─ Add new citations
├─ Update wikilinks
├─ Refresh explanations

Annually: Complete audit
├─ Review all 100+ topics
├─ Update citations >1 year old
├─ Improve lowest-scoring topics
```

---

**Last Updated:** 2026-05-03  
**Next Review:** 2026-06-01  
**Owner:** You  
**Version:** 1.0
