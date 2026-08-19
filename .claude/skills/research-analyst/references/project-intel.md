# Reference: project-intel

**When to load:** Use when the user wants competitive, market, or product intelligence to inform project direction using web search as the research layer. Triggers on: - "Who are the competitors for [product]?" - "What's the market landscape for [health-tech category]?" - "Is there already a product that does X?" -…

# $project-intel — Competitive & Market Intelligence Brief

Structure web research into a strategic intelligence brief — competitors,
user pain points, market gaps, differentiation angles, and product positioning.

## Usage

```
$project-intel <product/category> [for <project>] [focus: competitor | market | user-pain | differentiation | all]
```

---

## Workflow

### 1. Define the Intelligence Scope

```
PRODUCT:      [your product name and one-sentence description]
CATEGORY:     [market category — "gut health app" / "mood tracker" / "skin tracking"]
FOCUS:        [what kind of intelligence is most needed right now]
BUILD STAGE:  [pre-build ideation / MVP validation / post-MVP expansion]
AUDIENCE:     [B2C wellness / B2B clinical / HCP-facing / research]
GEOGRAPHY:    [US / global / specific market]
```

**Focus modes and what they produce:**
- `competitor` → Feature comparison table, positioning map, user review synthesis
- `market` → TAM/SAM estimates, growth trends, funding activity, regulatory tailwinds
- `user-pain` → Underserved needs, top app store complaints, community frustration patterns
- `differentiation` → Whitespace analysis, defensible angle identification
- `all` → Full brief across all four dimensions

---

### 2. Generate Search Query Plan

#### Competitor Discovery Queries
```
QUERY C1: "[category] app [year] market leaders top products"
  → Get: Named competitors with user base/funding if available

QUERY C2: "[category] app iOS Android reviews complaints problems 2024 2025"
  → Get: User pain points from reviews, Reddit, Twitter/X

QUERY C3: "[specific competitor] [category] app features pricing limitations"
  → Get: Detailed feature breakdown of top 2–3 competitors

QUERY C4: "[competitor] shutdown OR pivot OR acquired 2023 2024"
  → Get: Graveyard signals — what failed and why
```

#### Market Size & Trends Queries
```
QUERY M1: "[category] market size 2024 2025 TAM growth forecast"
  → Get: Market sizing estimates (treat with skepticism — see Tips)

QUERY M2: "[category] consumer behavior trends [target demographic]"
  → Get: Behavioral patterns, adoption drivers, churn reasons

QUERY M3: "[category] venture capital investment funding 2023 2024 2025"
  → Get: Where money is flowing in the space — proxy for opportunity
```

#### User Pain Point Queries
```
QUERY U1: "Reddit [category] app complaints [subreddit if known: r/ibs / r/mentalhealth]"
  → Get: Unfiltered user frustrations

QUERY U2: "[competitor app name] negative reviews one star app store"
  → Get: Failure modes users actually experience

QUERY U3: "[category] what do users want feature request most requested"
  → Get: Demand signals from actual users
```

#### Whitespace / Differentiation Queries
```
QUERY D1: "[category] unsolved problem gap opportunity"
  → Get: Stated gaps in the literature and product landscape

QUERY D2: "[category] clinical professional consumer crossover"
  → Get: B2B2C angle — do clinical professionals want this?

QUERY D3: "[category] hardware integration wearable sensor integration"
  → Get: Hardware-software bridge opportunities (relevant to BME angle)
```

---

### 3. Competitor Matrix

After research is available, build:

```markdown
## Competitor Matrix: [Category]

| Competitor | Core Feature | Audience | Business Model | Weakness | Funding |
|---|---|---|---|---|---|
| [Name] | [1-liner] | [B2C/B2B/clinical] | [freemium/sub/$X/mo] | [top complaint] | [$X Series A / bootstrapped / unknown] |
| [Name] | | | | | |
| [Name] | | | | | |

**Graveyard (failed products):**
- [Name] — [why it failed, year]
- [Name] — [why it failed, year]
```

---

### 4. Feature Gap Analysis

Map what exists vs. what's missing:

```markdown
## Feature Landscape

| Feature | [Comp A] | [Comp B] | [Comp C] | [Your Product] |
|---|---|---|---|---|
| Symptom logging | ✅ | ✅ | ✅ | Planned |
| Wearable integration | ❌ | Partial | ❌ | **Differentiator** |
| ML-based insights | ❌ | ✅ | ❌ | Planned |
| Clinical/HCP sharing | ❌ | ❌ | ❌ | **Whitespace** |
| Biosignal input | ❌ | ❌ | ❌ | **Differentiator** |
| Evidence-graded recs | ❌ | ❌ | ❌ | **Whitespace** |
| Open data export | ❌ | ❌ | ✅ | Planned |

**Legend:** ✅ Fully shipped | Partial — limited | ❌ Absent | **Bold** — opportunity
```

---

### 5. User Pain Point Synthesis

Structure the complaints and desires from community research:

```markdown
## User Pain Points: [Category Apps]

### Top Complaints (from reviews + community research)
1. **[Pain]** — [frequency signal: multiple sources / widespread / isolated]
   - Evidence: [where this came from — Reddit thread, 1-star reviews, etc.]
   - Severity: [Critical — stops use | High — causes friction | Low — annoyance]

2. **[Pain]** — ...

### Underserved Needs (stated desires with no product solution)
1. **[Need]** — [source + frequency]
2. **[Need]** — ...

### Jobs-to-be-Done
[What is the user actually trying to accomplish that existing apps fail to deliver?]
Format: "When I [situation], I want to [motivation], so I can [outcome]"
- "When I have a flare, I want to quickly log what I ate and how I feel, so I can identify my triggers without hours of journaling."
- [...]
```

---

### 6. Whitespace & Differentiation Analysis

```markdown
## Strategic Whitespace

### Unoccupied Positions
1. **[Position]:** [Why it's empty — technical barrier / regulatory / market timing]
   - Feasibility for [Your Product]: [High / Medium / Low]
   - Why you specifically can occupy this: [your BME background / hardware access / tech stack]

2. **[Position]:** ...

### Your Defensible Angles
[Based on your actual capabilities — honest assessment]

| Angle | Why you can own it | Why others can't easily copy |
|---|---|---|
| Hardware + software integration | BME background + Arduino/ESP32 competency | Requires EE/BME expertise most dev teams lack |
| Evidence-graded recommendations | Academic research access + biomedical rigor | Requires discipline most consumer apps skip |
| Privacy-first architecture | Supabase RLS + no-data-sell model | Requires deliberate architecture from day one |
| [Other angle] | | |

### Positioning Statement (draft)
```
For [target user] who [pain point],
[Product name] is the [category] that [key differentiator]
unlike [competitor], which [weakness].
```
```

---

### 7. Market Signals

```markdown
## Market Signals

### Growth Indicators
- [Signal 1 — e.g., "Gut health supplement market grew X% YoY"]
- [Signal 2 — funding rounds, acquisitions]
- [Signal 3 — regulatory tailwinds or headwinds]

### Adoption Barriers
- [Barrier 1 — e.g., "Users don't log consistently past week 2"]
- [Barrier 2 — e.g., "Clinical integration requires EHR partnership"]

### Timing Analysis
[Is this the right time to build? What's changed in the last 12 months?]
```

---

### 8. Output: Project Intelligence Brief

```markdown
# Project Intelligence Brief: [Product / Category]
**Date:** [today]
**Project:** [GASTROGUARD / MINDMAP / SKINTRACK / etc.]
**Research method:** web search + structured synthesis
**Confidence:** [High / Medium / Low — based on source quality]

## Summary (3 sentences)
[Competitive landscape. Key whitespace. Your move.]

## Competitor Matrix
[From Step 3]

## Feature Gap Analysis
[From Step 4]

## User Pain Points
[From Step 5]

## Whitespace & Differentiation
[From Step 6]

## Market Signals
[From Step 7]

## Recommended Positioning
[Positioning statement + 3 priority features to build first]

## What This Changes About the Roadmap
- [Specific adjustment to current plans based on this research]
- [Feature to deprioritize — competitor already owns it well]
- [Feature to accelerate — clear whitespace + high user demand]
```

---

## Tips

- App store reviews on iOS/Android are the highest-signal user pain point source. Try: *"[App Name] iOS reviews 2024 1 star complaints"* — these are real users, not press releases.
- Market size numbers from web search are almost always vendor-report citations — treat them as directional signals only, not as investable facts.
- The **graveyard query** (failed competitors) is the most underused. What failed and why is more informative than what succeeded.
- Your BME background is a genuine differentiator in health-tech — frame it in every positioning statement. Consumer apps are built by CS engineers; you can credibly speak the biology.
- Don't over-research. Intelligence that doesn't change a decision is waste. Ask: "What would I do differently if I learned X?" If the answer is "nothing," skip that query.
- Run the Reddit queries with Reddit focus explicitly. The unfiltered community signal is usually more honest than any market report.
