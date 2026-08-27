# Reference: lit-sweep

**When to load:** Use when the user wants to conduct a structured literature review using web search as the primary discovery tool. Triggers on: - "I need to do a lit review on X for [project]" - "Find me papers / studies on X" - "What does the research say about X?" - "Help me search for academic sources on X" -…

# $lit-sweep — Structured Literature Review

Design and execute a systematic literature sweep using web/academic search as the discovery engine. Produces a structured query plan, evidence matrix, and synthesis table.

## Usage

```
$lit-sweep <topic> [for <project>] [scope: broad | focused | update]
```

**Scope modes:**
- `broad` — Initial landscape mapping; no prior knowledge assumed
- `focused` — Targeted search around a specific mechanism or claim
- `update` — Find what's new in the last 12–24 months on a known topic

---

## Workflow

### 1. Define the Review Scope

Before generating queries, confirm:

```
TOPIC:      [precise topic — not "gut health" but "IBS biomarkers measurable via wearable sensor"]
PURPOSE:    [why: feature research / course assignment / project validation / regulatory support]
PROJECT:    [MINDMAP / GASTROGUARD / SKINTRACK / BME-COURSEWORK / etc.]
TIME BOUND: [all time / last 5 years / last 2 years]
DEPTH:      [breadth mapping / mechanistic depth / clinical evidence only / implementation-focused]
```

If any are missing and they materially affect the query design, ask once before proceeding.

---

### 2. Generate Search Query Plan

Design a tiered query set. Each query is optimized for hybrid search (web + academic):

#### Tier 1 — Landscape Queries (run first)
High-level; establish vocabulary, key researchers, dominant frameworks.

```
QUERY L1: "[topic] overview mechanisms 2020–2025"
  → Goal: Identify key subfields and terminology
  → Expected return: Review articles, Wikipedia-level synthesis

QUERY L2: "[topic] systematic review OR meta-analysis"
  → Goal: Find highest-evidence synthesis papers
  → Expected return: PubMed, Cochrane, IEEE Xplore citations
```

#### Tier 2 — Mechanism Queries (run after L1)
Drill into the specific biological, physical, or computational mechanisms.

```
QUERY M1: "[specific mechanism from L1] pathway signal [domain-specific term]"
  → Goal: Mechanistic depth
  → Expected return: Journal articles, textbook refs

QUERY M2: "[mechanism] clinical evidence human studies"
  → Goal: Separate animal/in-vitro from clinical evidence
```

#### Tier 3 — Implementation / Applied Queries (run after M-tier)
How has this been built, measured, or deployed?

```
QUERY A1: "[topic] sensor measurement wearable OR embedded system"
  → Goal: Find hardware/measurement approaches

QUERY A2: "[topic] machine learning model prediction accuracy"
  → Goal: Find ML applications in the domain

QUERY A3: "[topic] FDA regulatory submission SaMD"
  → Goal: Regulatory landscape (for medically adjacent topics)
```

#### Tier 4 — Gap & Contradiction Queries
Surface what the field does NOT yet know.

```
QUERY G1: "[topic] limitations challenges open problems"
QUERY G2: "[topic] conflicting evidence controversy"
```

**Total query budget:** 6–10 queries per sweep. Run in order; adjust Tier 3–4 based on Tier 1–2 returns.

---

### 3. Execute + Capture Output

For each query you run:
- Copy the **full response including citations**
- Note the **query used** (the tool sometimes rephrases — capture the actual query)
- Flag whether you used academic focus mode or general web search

Paste results back to Claude using `$research-digest` for each response, OR
paste all results at once with this skill for a unified synthesis pass.

---

### 4. Build the Evidence Matrix

After all queries are complete, compile:

```markdown
## Evidence Matrix: [Topic]

| Claim | Evidence Grade | Source | Notes | Project Relevance |
|---|---|---|---|---|
| [Claim 1] | A | [Author, Year] | RCT, N=200 | [GASTROGUARD] feature X |
| [Claim 2] | B | [Author, Year] | Single study, animal model | Limited translation |
| [Claim 3] | C | [Outlet] | Expert review, no primary data | Background only |
| [Claim 4] | D | [web synthesis] | No traceable source | Do not cite |
```

---

### 5. Build the Synthesis Summary

Structure:

```markdown
## Literature Synthesis: [Topic]

### What is established (Grade A/B consensus)
- [Finding 1]
- [Finding 2]

### What is contested or limited
- [Finding with conflicting evidence]
- [Finding valid only under specific conditions]

### What is unknown / under-researched
- [Gap 1 — framed as a research question]
- [Gap 2]

### Implications for [Project]
- [Specific product feature this supports or challenges]
- [Data to collect / not collect based on evidence base]
- [Regulatory / safety consideration if medically adjacent]
```

---

### 6. Output Deliverables

| Deliverable | Format | Use |
|---|---|---|
| Query Plan | Markdown list | Copy-paste ready for your search workflow |
| Evidence Matrix | Markdown table | Drop into Notion or project `/docs/research/` |
| Synthesis Summary | Markdown prose | Use in README, proposal, or report |
| Follow-up Queries | Numbered list | Next session's literature sweep |
| Citation List | Numbered references | Copy into LaTeX, Word, or Notion |

---

## Evidence Grading Reference

```
A — Systematic review, meta-analysis, RCT (large N, human subjects)
B — Single peer-reviewed study (human), clinical guideline, standards document
C — Peer-reviewed review article, expert consensus, reputable technical documentation
D — Secondary source (blog, news), web synthesis with no traceable URL, anecdotal
```

Apply the **lower grade** when a source is ambiguous. Err conservative, especially for GastroGuard
where clinical claims carry regulatory weight.

---

## Biomedical-Specific Tips

- Always run a **human subjects filter** query for any GastroGuard claim: *"[finding] human study clinical evidence"*
- For gut health / biosignal topics, check: PubMed, Nature Digital Medicine, NPJ Digital Medicine, Biosensors and Bioelectronics
- Animal models and in-vitro studies are **Grade B at best** — never extrapolate to clinical claims without a human study
- If results show only D-grade evidence for a core feature assumption, that is an existential project risk — flag immediately

---

## Example

```
$lit-sweep gut motility wearable biosensor for GASTROGUARD scope: broad
```

→ Generates 8 tiered queries  
→ After you paste search results: produces evidence matrix + synthesis  
→ Output: Notion-ready research artifact with regulatory flags
