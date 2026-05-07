# FitLib Business Model Canvas

## 📋 Overview

This document outlines how FitLib creates, delivers, and captures value across two distinct product lines:
1. **FitLib Web App** (B2C) - Freemium knowledge base + premium subscriptions
2. **FitLib Extractor API** (B2B) - Software licensing for coaches/platforms

---

## 🎯 Value Proposition

### For Individual Users (Freemium Web App)
| Feature | Value | Why Matters |
|---------|-------|------------|
| **Free Tier** | Access to 50 foundational topics | Learn basics without paywall |
| | Basic graph visualization | Visual learning > text |
| | 5 searches/day | Protects server costs |
| | | |
| **Premium Tier ($7.99/mo)** | All 500+ topics | Complete knowledge base |
| | Unlimited search | No friction for power users |
| | PDF export + offline access | Use research without internet |
| | Bookmarks & note system | Track personal learning journey |
| | Citation export (BibTeX/APA) | Helps with papers/presentations |
| | Reading progress tracking | Gamification + motivation |

**Why $7.99?** Undercuts Examine.com ($15/mo) while maintaining margin

### For Fitness Coaches/Platforms (B2B API)
| Tier | Value | Target Customer |
|------|-------|-----------------|
| **Starter ($299/yr)** | 100 requests/day API access | Solo coaches, small gyms |
| | 1 API key | One integration |
| | JSON export of 500+ nodes | Build custom apps |
| | | |
| **Pro ($699/yr)** | 10K requests/day | Growing coaching platforms |
| | 3 API keys | Multiple integrations |
| | Webhook notifications | Real-time syncing |
| | Dedicated Slack support | Priority communication |
| | | |
| **Enterprise ($1,999/yr)** | Unlimited requests | Large platforms, SaaS companies |
| | Unlimited API keys | Multiple teams |
| | White-label option | Rebrand as their own |
| | Custom data exports | Integration flexibility |
| | Dedicated account manager | Strategic partnership |

**Why API licensing?** Coaches need research data; we sell it at 10% of their profit.

---

## 💰 Revenue Streams

### Stream 1: Premium Subscriptions (B2C)
```
Model: Recurring subscription ($7.99/month or $79/year)

Year 1 Conservative Projection:
- Month 1-3: 500 signups → 50 premium (10%) = $400 MRR
- Month 4-6: 1,500 cumulative → 120 premium (8%) = $960 MRR
- Month 7-9: 3,000 cumulative → 270 premium (9%) = $2,160 MRR
- Month 10-12: 5,000 cumulative → 400 premium (8%) = $3,200 MRR

Blended: ~50% annual subscribers (save 20%) + 50% monthly

Year 1 Revenue: $1,500 + $960 + $2,160 + $3,200 = $7,820
(Conservative: assumes churn, viral doesn't happen)

Year 1 Optimistic: $15,000-20,000
```

### Stream 2: API Licensing (B2B)
```
Model: Annual subscription (tiered by usage)

Year 1 Target:
- Month 6: Launch API beta with 3 customers @ $299 = $900 MRR
- Month 9: 10 customers (mix of tiers) = $2,000 MRR
- Month 12: 15 customers = $3,500 MRR

Blended ASP (Average Selling Price): ~$233/customer/month
(Assuming 60% Starter, 30% Pro, 10% Enterprise)

Year 1 Revenue: $900 + $2,000 + $3,500 = $6,400
```

### Stream 3: Premium Features (Future)
```
Launched Year 2+:
- Coaching template library ($3/mo addon)
- Client integration (coaches manage clients' progress)
- Advanced analytics dashboard
- AI coaching assistant

Estimated Year 2 contribution: $2,000-5,000
```

### **Total Year 1 Revenue: $10,000-15,000**

---

## 📊 Cost Structure

### Fixed Costs (Monthly)
```
Infrastructure:
├─ Vercel hosting: $20
├─ Firestore: $25 (scales with data, capped at $100)
├─ Algolia search: $45
├─ Stripe fees: ~5% of revenue (included in COGS)
├─ Email/marketing: $25
└─ Domain + misc: $10
Total: ~$125/month = $1,500/year
```

### Variable Costs (Per Customer)
```
Per Premium Subscriber:
├─ Stripe fee: $0.30 + 2.9%
├─ Server cost: ~$0.10/month
├─ Support time: ~$0.50/month (average)
└─ Total COGS: ~$1.20/customer/month

Per API Customer:
├─ Stripe fee: ~$20 (2.9% of $699)
├─ Infrastructure (bandwidth): ~$10-50/month
├─ Support time: ~$50/month
└─ Total COGS: ~$80-120/customer/month (high margin still)
```

### One-Time Costs (Year 1)
```
Development:
├─ Your time extraction system: $0 (already done)
├─ Database design: $0 (you do it)
├─ Stripe integration: $0
├─ Landing page: $200 template
└─ Total: ~$200
```

---

## 📈 Gross Margin Analysis

### Premium Subscriptions
```
Revenue per subscriber: $7.99/month
COGS per subscriber: $1.20/month
Gross profit: $6.79/month
Gross margin: 85%
```

### API Licensing
```
Example: Pro tier ($699/year = $58.25/month)
COGS: ~$100/month (varies, assume high support needed)
Gross profit: -$42/month initially (break-even year 2)
BUT: Easier scaling, higher LTV

Total blended gross margin Year 1: ~70%
Improving to 80%+ as customer base grows
```

---

## 🎯 Customer Segments

### Primary: Freemium Web App
```
Persona 1: Fitness Enthusiast
├─ Age: 18-35
├─ Pain: Too much misinformation online
├─ Solution: Trustworthy knowledge base
├─ Acquisition: Reddit, TikTok, ProductHunt
├─ LTV: $50-200 (if they upgrade)

Persona 2: Personal Trainer
├─ Age: 25-45
├─ Pain: Need research to educate clients
├─ Solution: Cite real studies to build credibility
├─ Acquisition: Instagram, fitness forums
├─ LTV: $500+ (long-term premium)
```

### Secondary: B2B API
```
Persona 3: Coaching Platform
├─ Company: TrainHeroic, Strong app, CoachLogic
├─ Pain: Building research content is expensive
├─ Solution: License your 500+ nodes via API
├─ Acquisition: Cold email, partnerships
├─ LTV: $3,000-10,000/year (long-term contracts)

Persona 4: Fitness App
├─ Company: Nutritional tracking, gym management
├─ Pain: Need credible fitness content to differentiate
├─ Solution: White-label FitLib knowledge
├─ Acquisition: Strategic partnerships
├─ LTV: $5,000-50,000/year (high value)
```

---

## 🛣️ Channels

### Acquisition Channels (Freemium)
```
1. Product Hunt launch (Day 0)
   ├─ Cost: $0 (organic)
   ├─ Expected: 500-1,000 signups in week 1
   └─ LTV potential: High

2. Reddit (r/fitness, r/fitmeals, etc.)
   ├─ Post research insights, link to app
   ├─ Cost: $0 organic, $500-1,000 if ads
   └─ Expected: 100-200 signups/month

3. Twitter/Academic community
   ├─ Share research breakdowns (threads)
   ├─ Cost: $0 (organic, 2 hours/week)
   └─ Expected: 50-100 signups/month

4. Email list (ConvertKit free)
   ├─ Grow to 1,000 by Month 3
   ├─ Convert at 2-5% rate
   └─ Expected: 20-50 conversions/month

5. SEO/Content (Long-term)
   ├─ Rank for "fitness research," "exercise science"
   ├─ Cost: $0 (organic)
   ├─ Timeline: 3-6 months to see results
   └─ Expected: 100+ signups/month by Month 9
```

### B2B Acquisition Channels (API)
```
1. Cold email to 100 fitness coaches
   ├─ Personalized: "I see you coach athletes, want free access?"
   ├─ Cost: $0 (your time, 2 hours)
   └─ Expected: 3-5 conversations

2. Partnerships with platforms
   ├─ "We'll integrate FitLib API into your app"
   ├─ Cost: Revenue share negotiation
   └─ Expected: 1-2 major partnerships Year 1

3. LinkedIn B2B ads
   ├─ Target fitness app founders
   ├─ Cost: $500/month budget
   └─ Expected: 2-5 qualified leads/month

4. Industry events (fitness conferences)
   ├─ Sponsor booth, demo API
   ├─ Cost: $2,000-5,000 (optional Year 1)
   └─ Expected: 5-10 leads
```

---

## 🤝 Partnerships & Resources

### Key Partnerships Needed
```
1. Firebase/GCP
   ├─ Current: Using Firebase free tier
   ├─ Year 1: Pay $25-50/month as you scale
   └─ Value: Serverless infrastructure

2. Algolia
   ├─ Current: Essential for search
   ├─ Cost: $45/month (non-negotiable)
   └─ Value: 10x better search than Firestore native

3. Stripe
   ├─ Current: Payment processing
   ├─ Fee: 2.9% + $0.30 per transaction
   └─ Value: Handles all billing complexity

4. Vercel
   ├─ Current: React hosting
   ├─ Cost: $20/month (hobby tier free, but pro for production)
   └─ Value: Zero-downtime deployments

5. Obsidian Sync (Optional)
   ├─ Your vault sync service
   ├─ Cost: $5/month (mobile + cloud sync)
   └─ Value: Automated vault backups
```

### Key Resources (You Provide)
```
1. Your time: 7-8 hours/week
2. Domain expertise: Fitness research knowledge
3. Existing codebase: React app already built
4. Obsidian vault: 100+ topics (your IP)
5. GitHub: Version control + deployment automation
```

---

## 🎯 Key Success Factors

```
1. Premium Conversion Rate
   ├─ Target: 8-12%
   ├─ Lever: Landing page copy, free tier value
   └─ Impact: $400 → $2,000 MRR

2. Content Quality
   ├─ Target: 95%+ citation accuracy
   ├─ Lever: Automation system + review process
   └─ Impact: Trust → retention

3. API Unit Economics
   ├─ Target: Break-even at 5 customers
   ├─ Lever: Tiered pricing (Starter low support cost)
   └─ Impact: Scalable revenue

4. Customer Acquisition Cost
   ├─ Target: <$50 CAC for freemium
   ├─ Lever: Organic channels (ProductHunt, Reddit)
   └─ Impact: LTV:CAC ratio >3:1

5. Churn Rate
   ├─ Target: <2% monthly
   ├─ Lever: Product quality, email engagement
   └─ Impact: Predictable recurring revenue
```

---

## 📊 Financial Summary (Year 1)

| Metric | Conservative | Optimistic |
|--------|--------------|-----------|
| **Users** | 5,000 | 10,000 |
| **Premium Subscribers** | 400 | 800 |
| **API Customers** | 15 | 30 |
| **MRR (Month 12)** | $3,500 | $7,000 |
| **ARR (Year 1)** | $15,000 | $30,000 |
| **Gross Margin** | 70% | 75% |
| **Net (After ops)** | $8,000 | $20,000 |
| **CAC Payback** | 2-3 months | <2 months |

---

## 🔄 Decision-Making with This Model

**Use this canvas to:**
- "Should I build feature X?" → Check if it improves value prop
- "Should I spend money on Y?" → Check if ROI aligns with growth goals
- "Am I on track?" → Compare metrics to projections above
- "What should I prioritize?" → What impacts revenue most?

**Rule:** If it doesn't move one of the metrics above, it's a distraction.
