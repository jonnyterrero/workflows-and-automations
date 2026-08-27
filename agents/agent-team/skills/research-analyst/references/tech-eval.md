# Reference: tech-eval

**When to load:** Use when the user needs to evaluate a technology decision using web search as the research layer. Triggers on: - "Should I use X or Y for [project]?" - "What's the best library for [task]?" - "Help me evaluate [framework / tool / API]" - "I searched the web for [tech] — help me decide" - Any…

# $tech-eval — Structured Technology Evaluation

Convert web research into a rigorous, opinionated technology decision artifact —
tradeoff matrix, stack-fit analysis, recommendation, and migration path.

## Usage

```
$tech-eval <"X vs Y" or "best tool for Z"> [for <project>] [constraint: <constraints>]
```

---

## Workflow

### 1. Frame the Decision

Before evaluating, confirm the decision shape:

```
DECISION:      [X vs Y / pick from field / validate single choice]
PROJECT:       [MINDMAP / GASTROGUARD / SKINTRACK / INFRA / etc.]
LAYER:         [Frontend / Backend / DB / DevOps / ML / Embedded / Auth / etc.]
CONSTRAINTS:   [cost / bundle size / TypeScript support / Supabase compatibility / license / etc.]
LOCK-IN RISK:  [High — core infra | Medium — swappable adapter | Low — utility function]
DECISION TYPE: [Greenfield / Replacing existing / Evaluating addition to current stack]
```

If the user pasted search results, extract these from context.  
If not, generate the search query plan first (Step 2), then return here.

---

### 2. Generate Search Query Plan (if research not yet done)

```
QUERY 1: "[Option A] vs [Option B] [layer] [year] comparison"
  → Get: feature comparison, community consensus, known pitfalls

QUERY 2: "[Option A] [project-relevant stack, e.g., Next.js App Router / Supabase / Python FastAPI] compatibility"
  → Get: Integration friction, known issues, official support status

QUERY 3: "[Option A] production scale performance benchmarks [year]"
  → Get: Quantitative data — bundle size, latency, throughput, memory

QUERY 4: "[Option A] known issues migration problems 2024 2025"
  → Get: Current pain points, breaking changes, deprecation risk

QUERY 5: "[Option B]" — repeat queries 2–4 for the other candidate(s)

QUERY 6: "[decision domain] best practice [specific stack] 2025"
  → Get: What the community has converged on
```

---

### 3. Build the Tradeoff Matrix

After research is available (pasted or retrieved), structure:

```markdown
## Tradeoff Matrix: [Decision Title]

| Dimension | [Option A] | [Option B] | Weight | Winner |
|---|---|---|---|---|
| TypeScript support | Native, full types | Partial, @types needed | High | A |
| Bundle size | 4.2kB gzipped | 18kB gzipped | Medium | A |
| Supabase compatibility | First-class | Manual adapter | High | A |
| Learning curve | Low (familiar pattern) | Medium (new paradigm) | Low | A |
| Community / ecosystem | Large, active | Small, niche | Medium | A |
| License | MIT | Apache 2.0 | Low | Tie |
| Long-term maintenance | Corporate-backed | Solo maintainer | High | A |
| Performance | [benchmark data] | [benchmark data] | Medium | B |
| Lock-in risk | High (proprietary API) | Low (standard interface) | High | B |
| Cost (at scale) | Free tier → $X/mo | Free open source | Medium | B |
```

**Weight values:** High = decision-critical | Medium = matters but not blocking | Low = nice-to-have

---

### 4. Stack-Fit Analysis

Evaluate how each option fits the existing ecosystem:

```markdown
## Stack-Fit Analysis

### Current Stack (relevant layer)
- Runtime: Node 20 / Python 3.11
- Framework: Next.js 14 App Router
- DB: Supabase (PostgreSQL, Auth, RLS, Realtime)
- ORM/Client: Supabase JS client (direct) — Prisma being deprecated
- Deploy: Vercel (Edge Functions + Serverless)
- Types: TypeScript strict mode

### [Option A] — Stack Fit Assessment
- Compatibility: [specific version tested / known to work with Next.js App Router]
- Integration points: [what it touches in the current stack]
- Breaking changes required: [Yes / No — list if yes]
- Env constraints: [Edge-compatible? Server-only? Client-safe?]
- Known conflicts: [any known issues with other current deps]

### [Option B] — Stack Fit Assessment
[Same structure]
```

---

### 5. Risk Assessment

For each candidate:

```
RISK — DEPENDENCY HEALTH
  [Option A]: [npm weekly downloads / GitHub stars / last commit / # maintainers]
  [Option B]: [same]
  
RISK — BREAKING CHANGES
  [Option A]: [Major version release cadence; recent migration burden?]
  [Option B]: [same]

RISK — LOCK-IN
  [Option A]: [What changes if you want to swap this out in 18 months?]
  [Option B]: [same]

RISK — SECURITY SURFACE
  [Option A]: [Known CVEs in last 12 months? Auth handling? Data exposure risk?]
  [Option B]: [same]
```

---

### 6. Recommendation

**Be opinionated. Do not hedge.** State the recommendation clearly:

```markdown
## Recommendation: [Option A / Option B / Neither — use [X] instead]

**Verdict:** [One sentence. "Use Option A." or "Neither — the right answer is X."]

**Primary reason:** [The single strongest argument for the decision]

**Secondary reasons:**
1. [Reason 2]
2. [Reason 3]

**Accept this tradeoff:** [What you're giving up; state it clearly]

**Conditions that would reverse this:** 
- [If you later need X, reconsider]
- [If your scale hits Y, the cost model breaks]

**Technical debt flagged:** TECH DEBT: [anything about this choice that will need revisiting]
```

---

### 7. Implementation Path

If a decision is made, output the first concrete steps:

```markdown
## Implementation Path

### Install
```bash
npm install [package]@[exact-version]  # pin to major.minor at minimum
```

### Minimal Integration (Next.js App Router pattern)
```typescript
// [file path]: [minimal working example, typed, annotated]
```

### Environment Variables Needed
```
[VAR_NAME]=  # [description, where to get it]
```

### Tests Required
- [ ] [Unit test for core integration point]
- [ ] [Integration test with Supabase / Vercel / relevant infra]

### Rollback Plan
[How to remove or replace this if it fails in production]
```

---

## Decision Governance

Every significant tech decision should be recorded as an Architecture Decision Record (ADR):

```markdown
# ADR-[N]: [Decision Title]

**Date:** [today]
**Status:** Accepted
**Deciders:** [Jonny]

## Context
[Why was this decision needed?]

## Decision
[What was chosen and why]

## Consequences
[What changes; what technical debt is introduced]

## Alternatives Considered
[What was rejected and why]
```

Drop ADRs in `/docs/decisions/` in the relevant project repo.

---

## Tips

- Use broad web search (not academic-only) for library/framework decisions — you want current GitHub/npm/dev discourse.
- Cross-check any benchmark claim against a dated source: library performance shifts with every major version.
- If results show enthusiastic praise with no caveats, run the query: *"[option] problems issues 2025"* — the criticism queries surface the real picture.
- Anything touching Supabase Auth, RLS, or Vercel Edge Functions needs explicit compatibility verification — don't assume.
