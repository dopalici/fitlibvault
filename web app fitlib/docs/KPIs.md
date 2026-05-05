# FitLib Key Performance Indicators (KPIs)

**Purpose:** Define the metrics that measure FitLib's success and guide strategic decisions.

**Frequency:** Tracked weekly, reviewed monthly, used for quarterly adjustments

**Owner:** You (monitor these metrics every Friday)

---

## 📊 Dashboard Snapshot

**Current Status (Template for you to fill)**

```
Week Ending: [YYYY-MM-DD]

USER METRICS:
├─ Total signups (cumulative): ___ (target: 500 Month 1)
├─ Active users (DAU): ___ (target: 100+ Month 1)
├─ Premium subscribers: ___ (target: 50 by Month 3)
├─ Premium conversion rate: __% (target: 8-10%)
└─ Monthly churn rate: __% (target: <2%)

REVENUE METRICS:
├─ MRR from subscriptions: $___ (target: $400 Month 1)
├─ MRR from API: $____ (target: $0 Month 1, $300 Month 6)
├─ Total MRR: $_____ (target: $400 Month 1 → $2,000 Month 12)
└─ CAC (Customer Acquisition Cost): $___ (target: <$50)

CONTENT METRICS:
├─ Total nodes: ___ (target: 105+ from vault)
├─ New nodes published: ___ (target: 2/week)
├─ Average citations per node: ___ (target: 8+)
├─ Wikilink resolution rate: __% (target: >95%)
└─ Content quality score: __/5 (target: >4.0)

ENGAGEMENT METRICS:
├─ Avg session duration: ___ min (target: >3 min)
├─ Pages per session: ___ (target: >2)
├─ Knowledge graph interactions: ___ (target: >50%)
├─ Search queries per day: ___ (target: >100)
└─ Email list growth: ___ (target: +50/week)

BUSINESS HEALTH:
├─ Uptime: __% (target: 99.9%)
├─ Search latency: ___ ms (target: <100ms)
├─ Support response time: ___ hours (target: <24h)
└─ API availability: __% (target: 99.99%)
```

---

## 🎯 User Acquisition Metrics

### Primary Metric: Total Signups

```
DEFINITION: Cumulative count of all users who created an account

TARGETS:
Month 1:   500 signups
Month 2:   1,000 cumulative
Month 3:   1,500 cumulative
Month 6:   3,000 cumulative
Month 12:  5,000 cumulative

HOW TO TRACK:
├─ Firebase: Users → User count
├─ Segment: Track signup event in analytics
├─ Dashboard: Create Looker Studio dashboard

WEEKLY ACTION:
├─ Monday: Check previous week's signups
├─ Compare vs. target (500 / 4 = 125/week target Month 1)
├─ If below target: Increase marketing spend
└─ If above target: Document what worked, scale it
```

### Secondary Metric: Signups by Channel

```
DEFINITION: Where users are coming from

TRACK FOR:
├─ ProductHunt (launch week: expect 200-300)
├─ Reddit (r/fitness, r/bodyweightfitness)
├─ Twitter/X (organic mentions)
├─ Email list (ConvertKit)
├─ Direct/Referral
├─ SEO (if any)
└─ Paid ads (if any)

TARGET:
ProductHunt: 200-300 (launch week only)
Reddit: 50-75/month
Twitter: 30-50/month
Email: 20-40/month
Direct/Referral: 50+ (indicates quality)

ANALYSIS:
├─ Which channel has best LTV?
├─ Which channel has best conversion rate?
├─ Where to invest more marketing?
```

---

## 💰 Revenue Metrics

### Primary Metric: Monthly Recurring Revenue (MRR)

```
DEFINITION: Predictable revenue per month (subscriptions only)

CALCULATION:
MRR = (# Premium subscribers × $7.99) + (API customers × ASP)

Example:
50 premium × $7.99 = $400
3 API customers × $233 avg = $700
Total MRR = $1,100

TARGETS:
Month 1:   $0-400 (launch month)
Month 3:   $400-600 (initial traction)
Month 6:   $1,000-1,500 (growth)
Month 12:  $2,000+ (sustainable)

WEEKLY ACTION:
├─ Check # of new premium conversions
├─ Calculate new MRR
├─ Compare vs. target
├─ If below: Improve landing page copy, increase free tier value
├─ If above: Celebrate, consider raising price test
```

### Secondary Metric: Premium Conversion Rate

```
DEFINITION: % of users who upgrade to premium (Monthly)

CALCULATION:
Conversion Rate = (# New Premium Conversions) / (# Signups) × 100

Example:
50 new signups in Month 1
5 converted to premium
5 / 50 = 10% conversion rate

TARGETS:
Month 1:   10% (early adopters are high-intent)
Month 3:   8% (as broader audience joins)
Month 6:   9% (optimized onboarding)
Month 12:  10-12% (matured product)

BENCHMARKS:
├─ SaaS average: 2-5% (we're targeting higher)
├─ Examine.com: ~10% (our benchmark)
├─ Premium app average: 3-8%

WEEKLY ACTION:
├─ Monitor daily conversions
├─ If trending down (<5%): Run landing page tests
├─ If trending up (>12%): Document what changed
├─ A/B test free tier value vs. premium features
```

### Tertiary Metric: Customer Acquisition Cost (CAC)

```
DEFINITION: How much you spend to acquire 1 paying customer

CALCULATION:
CAC = Total Marketing Spend / # New Premium Customers

Example:
Spent $200 on ProductHunt launch
Got 40 premium customers
CAC = $200 / 40 = $5 per customer (EXCELLENT)

TARGETS:
Month 1:   <$100 (ProductHunt organic)
Month 3:   <$50 (Reddit/Twitter organic)
Month 6:   <$75 (mix of organic + small ads)
Month 12:  <$100 (can afford more spend)

RULE:
CAC should be <LTV/3 (payback period <3 months)

CALCULATION OF LTV:
Premium LTV = (Monthly Subscription) / (Monthly Churn Rate)
Example: $7.99 / 0.02 = $400 LTV
Safe CAC = $400 / 3 = $133

WEEKLY ACTION:
├─ Track marketing spend (organic = $0)
├─ Calculate CAC weekly
├─ If rising: Check where money going, ROI each channel
├─ If excellent (<$20): Double down on that channel
```

---

## 👥 Engagement Metrics

### Primary Metric: Monthly Active Users (MAU)

```
DEFINITION: # of unique users with >1 session in the month

TARGETS:
Month 1:   200 MAU
Month 3:   500 MAU
Month 6:   1,500 MAU
Month 12:  3,000+ MAU

HOW TO TRACK:
Firebase Analytics → Engaged Users → Monthly

WEEKLY ACTION:
├─ Check Thursday (before Friday review)
├─ Compare vs. target
├─ Track trend (going up = good)
└─ If down: Email inactive users, add new features
```

### Secondary Metric: Premium Subscriber Churn Rate

```
DEFINITION: % of premium subscribers who cancel each month

CALCULATION:
Churn = (# Canceled Subscriptions) / (# Previous Month Subscribers) × 100

Example:
Started Month 3 with 50 premium subscribers
5 canceled during month
Churn = 5 / 50 = 10% (TOO HIGH)

TARGETS:
Month 1-3: <5% (expect some early churn)
Month 6+:  <2% (mature churn rate)
Year 2+:   <1.5% (best in class)

FORMULA:
LTV = (Monthly Subscription) / (Monthly Churn Rate)
Example: $7.99 / 0.02 = $399.50 LTV (3-month payback)

WEEKLY ACTION:
├─ Monitor cancellations daily
├─ If churn >3%: Survey canceling users
│  ├─ Why did you leave?
│  ├─ What would bring you back?
│  └─ Plan feature improvements
├─ Send "we miss you" email to canceled users
└─ Improve onboarding to increase sticky features
```

### Tertiary Metric: Daily Active Users (DAU)

```
DEFINITION: # of unique users with >1 session that day

CALCULATION:
DAU = Unique sessions / Unique users per day

TARGETS:
Month 1:   50-100 DAU
Month 3:   200-300 DAU
Month 6:   500+ DAU

WEEK-OVER-WEEK GROWTH:
Target: 15-20% WoW (week-over-week) growth
├─ Month 1: Doubling each week (100% WoW)
├─ Month 3: 30% WoW
├─ Month 6: 10-15% WoW
├─ Month 12: 5-10% WoW (growth slowing is normal)

DAILY DASHBOARD:
```
Monday-Friday:
├─ DAU: 150 (target: 150)
├─ Session length: 4 min (target: 3+ min)
└─ Pages/session: 2.5 (target: 2+)

Weekend (Fri-Sun):
├─ DAU: 50 (lower, expected)
├─ Focus on weekday metrics
```

---

## 📈 Content Metrics

### Primary Metric: Total Published Nodes

```
DEFINITION: Number of knowledge base topics (from vault)

TARGETS:
Month 1:   105 nodes (from your Obsidian vault)
Month 3:   130 nodes (105 + 25 new)
Month 6:   160 nodes (105 + 55 new)
Month 12:  210+ nodes (105 + 105 new)

GROWTH RATE:
Target: 2-3 new topics per week
├─ Conservative: 1/week = 50/year
├─ Realistic: 2/week = 100/year
├─ Ambitious: 3/week = 150/year

WEEKLY ACTION:
├─ Track new topics published
├─ If falling behind: Block 4 hours for content
├─ Celebrate milestones (150, 200, 250 topics)
```

### Secondary Metric: Average Citations per Topic

```
DEFINITION: (Total citations) / (Total topics)

TARGETS:
Month 1:   9 citations/topic (1,200 citations / 105 nodes)
Month 3:   10 citations/topic
Month 6:   11 citations/topic
Month 12:  12+ citations/topic

IMPORTANCE:
├─ More citations = Higher credibility
├─ Minimum: 8 citations per topic (non-negotiable)
├─ Ideal: 10-15 citations per topic
└─ Target: Average 95%+ quality score

WEEKLY ACTION:
├─ Monitor avg citations
├─ If <8 on new topics: Require more research before publishing
├─ Celebrate high-citation topics (15+)
```

### Tertiary Metric: Content Quality Score

```
DEFINITION: Average quality rating of all published content

CALCULATION:
Quality Score = Avg of all individual topic scores (1-5 scale)

Scoring Rubric:
5 = Exceptional (8+ citations, expert reviewed, actionable)
4 = Very Good (8+ citations, accurate, mostly actionable)
3 = Good (5-8 citations, accurate, somewhat actionable)
2 = Fair (3-5 citations, mostly accurate, limited actionable)
1 = Poor (<3 citations, inaccurate, not actionable)

TARGETS:
Month 1:   4.2 / 5.0 (from vault, pre-reviewed)
Month 3:   4.0 / 5.0 (new content maintains standard)
Month 6:   4.1 / 5.0 (continuous improvement)
Month 12:  4.2+ / 5.0 (mature content library)

WEEKLY ACTION:
├─ Rate new topics on 1-5 scale
├─ If below 4.0: Require revision before publishing
├─ Monitor lowest-scoring topics (improve them)
├─ Get peer review for scores <4.0
```

---

## 🔍 Search & Discovery Metrics

### Primary Metric: Search Queries per Day

```
DEFINITION: Total number of searches users perform

TARGETS:
Month 1:   50-100 searches/day
Month 3:   200-300 searches/day
Month 6:   500+ searches/day
Month 12:  1,000+ searches/day

IMPORTANCE:
├─ Shows engagement depth
├─ Indicates if users find what they need
├─ High search = good content + UX

WEEKLY ACTION:
├─ Track in Algolia dashboard
├─ Analyze top searches
│  ├─ Which topics getting searched?
│  ├─ Are results helpful?
│  ├─ Create new content for missing queries
└─ Monitor search latency (<100ms target)
```

### Secondary Metric: Avg Session Duration

```
DEFINITION: Average time user spends per session

TARGETS:
Month 1:   2-3 minutes
Month 3:   3-4 minutes
Month 6:   4-5 minutes
Month 12:  5+ minutes

GOAL:
├─ Want users reading deeply
├─ Longer sessions = higher engagement
├─ Longer sessions = lower churn

WEEKLY ACTION:
├─ Track in Firebase Analytics
├─ If dropping: Check if content load time increased
├─ If low: Improve graph visualization / UX
└─ Celebrate >5 min (indicates stickiness)
```

---

## 💼 API/B2B Metrics

### Primary Metric: API Customers

```
DEFINITION: Number of paying API customers

TARGETS:
Month 1-5: 0 (building, beta)
Month 6:   3 customers
Month 9:   10 customers
Month 12:  15+ customers

EXPANSION REVENUE:
├─ Goal: Each customer expands 10-20% annually
├─ Example: Customer starts on Starter ($299)
│  → Year 2: Upgrades to Pro ($699)
│  → LTV: $998+ (2 years)

WEEKLY ACTION:
├─ Track every new API signup (even if beta/free)
├─ Monthly: Reach out to all API customers
├─ Celebrate signing first paying API customer
├─ Monitor API usage patterns
```

### Secondary Metric: API Revenue

```
DEFINITION: Monthly revenue from API subscriptions

CALCULATION:
API MRR = (# Starter × $25) + (# Pro × $58) + (# Enterprise × $167)

Example:
5 Starter: 5 × $25 = $125
8 Pro: 8 × $58 = $464
1 Enterprise: 1 × $167 = $167
Total API MRR = $756

TARGETS:
Month 6:   $100-300 (initial customers)
Month 9:   $1,000+ (scaling)
Month 12:  $1,500-2,000+ (solid business)

WEEKLY ACTION:
├─ Track each API customer
├─ Monitor churn (goal: 0% first year)
├─ Upsell: Contact customers approaching tier limits
└─ Support: Ensure API response times <200ms
```

---

## 📱 Technical Metrics

### Uptime / Reliability

```
DEFINITION: % of time website is accessible (24/7)

TARGET: 99.9% uptime (11.7 hours downtime/month)

HOW TO TRACK:
├─ Vercel: Built-in uptime monitoring
├─ Firebase: Dashboard alerts
├─ Algolia: Health checks

WEEKLY ACTION:
├─ Check status page
├─ If any downtime: Document root cause
├─ If recurring issue: Fix permanently
└─ Alert users if extended outage
```

### Search Latency

```
DEFINITION: Time between user search query and results (Algolia)

TARGET: <100ms average, <500ms p99

HOW TO TRACK:
├─ Algolia analytics dashboard
├─ Vercel performance metrics
├─ Google Analytics

WEEKLY ACTION:
├─ Check Algolia dashboard
├─ If trending up (>200ms): Optimize query
│  ├─ Check index size
│  ├─ Check facet filters
│  └─ May need to upgrade Algolia plan
└─ Monitor during heavy usage (evening)
```

---

## 📋 Monthly KPI Review Template

**First Friday of each month, fill out:**

```
MONTH: [Month/Year]

USER METRICS:
├─ Total signups (cumulative): ___ vs target ___
├─ Premium subscribers: ___ vs target ___
├─ Premium conversion rate: __% vs target ___%
├─ Monthly churn: __% vs target __%
└─ Trend: ✅ On track / ⚠️ Slightly behind / ❌ Off track

REVENUE METRICS:
├─ MRR: $____ vs target $____
├─ API customers: __ vs target __
├─ CAC: $____ vs target $____
└─ Trend: ✅ On track / ⚠️ Slightly behind / ❌ Off track

CONTENT METRICS:
├─ Total nodes: ___ vs target ___
├─ New nodes published: ___ vs target ___
├─ Quality score: __/5 vs target 4.0+
└─ Trend: ✅ On track / ⚠️ Slightly behind / ❌ Off track

ENGAGEMENT METRICS:
├─ MAU: ___ vs target ___
├─ DAU: ___ vs target ___
├─ Session duration: __ min vs target 3+ min
└─ Trend: ✅ On track / ⚠️ Slightly behind / ❌ Off track

TECHNICAL METRICS:
├─ Uptime: __% (target 99.9%)
├─ Search latency: __ ms (target <100ms)
└─ API uptime: __% (target 99.99%)

TOP 3 WINS THIS MONTH:
1. [Achievement]
2. [Achievement]
3. [Achievement]

TOP 3 ISSUES:
1. [Problem + plan to fix]
2. [Problem + plan to fix]
3. [Problem + plan to fix]

PRIORITIES NEXT MONTH:
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]
```

---

## 🎯 Cohort Analysis (Advanced)

**Track user retention by signup cohort:**

```
MONTH 1 COHORT (500 users):
├─ Week 1 retention: 60% (300 active)
├─ Week 2 retention: 45% (225 active)
├─ Month 1 retention: 40% (200 active)
├─ Month 2 retention: 30% (150 active)
└─ Month 3 retention: 25% (125 active)

GOAL: Improve Month 3 retention to 35% (175 users)

ACTION: Identify why 75% churn in first month
├─ Is onboarding clear?
├─ Is free tier valuable enough?
├─ Is search working well?
├─ Is content up to standard?
└─ Improve weakest point
```

---

**Last Updated:** 2026-05-03  
**Review Schedule:** Weekly (Fridays), Monthly (1st Friday)  
**Owner:** You  
**Version:** 1.0

*These KPIs drive all strategic decisions. Review them every Friday.*
