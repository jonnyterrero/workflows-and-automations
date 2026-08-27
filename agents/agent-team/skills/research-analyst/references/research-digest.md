# Reference: research-digest

**When to load:** Use when the user pastes or describes web search research output and wants it converted into a structured, citable artifact. Triggers on: - "I searched the web and got this..." - "Here's what the search said about X, structure this" - "Digest this research into something I can use" - "Turn this…

# $research-digest — Ingest & Structure Web Research

Convert raw web search output into a structured, reusable research artifact —
tagged, graded, and linked to the appropriate project context.

## Usage

```
$research-digest <paste search output or describe the search topic>
```

---

## Workflow

### 1. Parse the Input

Before structuring anything, identify:

- **Search topic**: What question was searched? Reconstruct the query if not stated.
- **Source quality**: Are citations academic (PubMed, IEEE, Nature) or general (news, blog, Reddit)?
- **Information type**: Factual claims, mechanism explanations, data/statistics, opinions, procedures?
- **Completeness**: Does the output appear to be a full answer, or a fragment?

If the input is unclear or incomplete, ask: *"What specific question did you search? I'll need that to calibrate the evidence grading."*

---

### 2. Classify Under Project Context

Map the content to one of the active projects or domains:

| Domain Tag | Use When |
|---|---|
| `[MINDMAP]` | Mental wellness, mood tracking, health data logging, wearable integration |
| `[GASTROGUARD]` | Gut health, GI signals, biosensors, dietary guidance, FDA/SaMD |
| `[SKINTRACK]` | Dermatology, skin condition tracking, imaging, ML on skin data |
| `[HEARTWIRE-OS]` | Personal productivity, knowledge systems, study systems |
| `[BME-COURSEWORK]` | Biomedical engineering academic content |
| `[SIGNALS-DSP]` | Signal processing, filters, transforms — cross-project |
| `[INFRA]` | Supabase, Vercel, Docker, deployment, DevOps |
| `[GENERAL]` | No specific project mapping |

Apply **all** tags that apply. A finding about HRV biosensors maps to both `[MINDMAP]` and `[GASTROGUARD]`.

---

### 3. Extract & Grade Claims

For each distinct factual claim or mechanism in the source:

**Evidence Grade:**
```
A — Systematic review, meta-analysis, or RCT with large N
B — Single peer-reviewed study, clinical guideline, or well-sourced technical doc
C — Secondary source, reputable journalism, or expert blog (no primary citation)
D — Anecdotal, unverified, or web synthesis with no traceable source
```

Present as a structured claim block:

```
CLAIM: [one sentence, precise statement of the finding]
GRADE: [A / B / C / D]
SOURCE: [publication / outlet name + URL if available]
CONFIDENCE: [High / Medium / Low — your assessment of result accuracy here]
NOTES: [any caveats, contradictions in the source, or scope limitations]
```

---

### 4. Generate the Research Note

Output structure:

```markdown
# Research Note: [Topic]

**Date:** [today]
**Search Query (reconstructed):** [what was likely asked]
**Project Tags:** [MINDMAP] [GASTROGUARD] etc.
**Source Type:** Academic / Technical / General / Mixed

---

## Key Findings

### Finding 1: [Headline claim]
- **Evidence Grade:** B
- **Source:** [Name + URL]
- **Summary:** [2–3 sentence synthesis]
- **Project Relevance:** [how this applies to tagged projects, specifically]

### Finding 2: ...

---

## Mechanism / Background
[If the results explained a mechanism — a biological pathway, algorithm, protocol —
 reconstruct it clearly with your own labeled diagram description if helpful]

---

## Gaps & Open Questions
- [ ] What is still unknown or contested in this area?
- [ ] What would a follow-up search look like?
- [ ] What primary source should be tracked down?

---

## Action Items
- [ ] [Concrete next step tied to a project — e.g., "Add HRV proxy feature to MindMap data model"]
- [ ] [Follow-up search: "search: [suggested query]"]
- [ ] [Paper to read: [Author, Year, title if extractable]]

---

## Raw Notes
[Preserve any verbatim quotes from the source you may need to re-reference,
 kept short — never reproduce more than a sentence for copyright reasons]
```

---

### 5. Flag Quality Issues

Inline alerts to add if applicable:

```
⚠️ GRADE-D CLAIM — No traceable primary source. Do not cite in project documentation.
⚠️ SOURCE HALLUCINATION RISK — Statistic with no URL; verify before using.
⚠️ SCOPE MISMATCH — This study used a non-human model; applicability to [project] is limited.
⚠️ REGULATORY FLAG — This claim is medically adjacent. See $regulatory-brief before acting.
```

---

### 6. Suggest Follow-Up Searches

Generate 2–3 targeted search follow-up queries based on the gaps identified:

```
FOLLOW-UP 1: "[exact suggested query]"
  → Target: [what this will clarify]
  → Expected source type: [academic / technical / regulatory]

FOLLOW-UP 2: ...
```

---

## Output

A complete, copy-pasteable research note in Markdown, ready for:
- Notion page drop-in
- GitHub repo `/docs/research/` entry
- Project README reference section

---

## Tips

- Paste the full response including citations — the raw citations are the most valuable part.
- If results cited something important but paywalled, say so — suggest PubMed, Sci-Hub, or preprint alternatives.
- Use `GRADE: D` aggressively. Web synthesis without a traceable URL is D-grade by default.
- For medically adjacent findings, always append: *"This is informational, not clinical guidance."*
