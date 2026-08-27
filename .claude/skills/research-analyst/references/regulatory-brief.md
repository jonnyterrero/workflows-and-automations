# Reference: regulatory-brief

**When to load:** Use when the user needs to research regulatory, compliance, or legal landscape for any medically adjacent feature, product, or claim using web search. Triggers on: - "What FDA rules apply to [feature]?" - "Is [feature] considered a medical device?" - "What are the HIPAA requirements for [data…

# $regulatory-brief — FDA / SaMD / HIPAA Research Brief

Structure web research into a regulatory intelligence brief covering
classification risk, applicable frameworks, evidence requirements, and the
compliance gap between current product state and regulatory readiness.

## Usage

```
$regulatory-brief <feature or product> [jurisdiction: US / EU / both]
```

**Disclaimer — prepend to every output:**
> ⚠️ This brief is informational only. It is not legal or regulatory advice.  
> All compliance decisions must be reviewed by a qualified regulatory affairs  
> professional before submission, publication, or clinical use.

---

## Workflow

### 1. Define the Regulatory Surface

Before researching, map exactly what is being evaluated:

```
PRODUCT/FEATURE:  [exact description — "dietary recommendation engine" not "GastroGuard"]
HEALTH CLAIM:     [what specific claim is being made or implied?]
USER POPULATION:  [general wellness users / patients with diagnosed condition / HCP-facing]
DATA COLLECTED:   [symptom logs / biosignals / lab values / images / demographics]
OUTPUT TYPE:      [informational display / recommendation / alert / diagnosis / treatment suggestion]
JURISDICTION:     [United States / European Union / Both]
```

**The health claim is the regulatory trigger.** Frame it precisely:
- "This app helps you track symptoms" → lower risk
- "This app recommends dietary changes for IBS management" → FDA SaMD territory
- "This app diagnoses your condition" → Class II/III device classification risk

---

### 2. Generate Search Query Plan

```
QUERY R1: "FDA Software as Medical Device [product type] classification 2024"
  → Goal: Current classification landscape for this product category
  → Target source: FDA.gov guidance documents, regulatory affairs publications

QUERY R2: "FDA SaMD intended use [health claim] risk-based classification"
  → Goal: Where does this specific claim fall in FDA's risk framework?
  → Target: FDA's Digital Health Center of Excellence guidance

QUERY R3: "[product category] FDA 510(k) predicate device exempt OR premarket"
  → Goal: Is this product category exempt, 510(k), or PMA-level?
  → Target: FDA device databases, regulatory firm white papers

QUERY R4: "HIPAA compliance [data types collected] mobile health app requirements"
  → Goal: Data privacy obligations for the data being collected
  → Target: HHS.gov, HIPAA compliance guides for digital health

QUERY R5: "FTC health claims digital health wellness app enforcement"
  → Goal: Marketing / advertising compliance — what claims cross the FTC line?
  → Target: FTC guidance, enforcement action summaries

QUERY R6: "EU MDR [product category] classification digital health software 2024"
  → Goal: European compliance requirements (if relevant)
  → Target: EU MDR Article 51, Annex VIII classification rules

QUERY R7: "[product category] clinical validation requirements evidence"
  → Goal: What evidence base is needed to support the claims being made?
  → Target: FDA guidance on clinical performance testing for SaMD
```

---

### 3. FDA SaMD Risk Classification Framework

Apply FDA's two-axis risk model to the product:

```markdown
## FDA SaMD Classification Analysis

### Axis 1 — Healthcare Situation / Condition
[ ] Critical — immediately life-threatening / irreversible (cardiac, sepsis)
[ ] Serious — requires timely intervention (chronic disease management)
[ ] Non-serious — general wellness, logging, informational

### Axis 2 — Significance of Information Provided
[ ] Treat / Diagnose — drives diagnosis or treatment decision
[ ] Drive Clinical Management — informs clinical workflow
[ ] Inform Clinical Management — supplements clinical information
[ ] Non-clinical decision support — wellness only

### Risk Class (from intersection):
```

| | Non-serious | Serious | Critical |
|---|---|---|---|
| **Inform** | Class I | Class II | Class II |
| **Drive Mgmt** | Class II | Class II | Class III |
| **Treat/Diagnose** | Class II | Class III | Class III |

```markdown
**This product maps to: Class [I / II / III]**

Class I — Generally exempt from premarket review
Class II — 510(k) clearance typically required (or De Novo pathway)
Class III — Premarket Approval (PMA) required — highest regulatory burden

**Basis for classification:**
- Healthcare situation: [Serious — IBS is a chronic condition requiring ongoing management]
- Information significance: [Drive Clinical Management — dietary recs that change patient behavior]
- Therefore: Class II — 510(k) or De Novo pathway likely required IF clinical claims are made
```

---

### 4. Clinical Claims Risk Map

Every product feature should be explicitly classified:

```markdown
## Feature-Level Claims Analysis

| Feature | Claim Type | Regulatory Risk | Mitigation |
|---|---|---|---|
| Symptom logging | Informational display | Low — no recommendation | None needed; include disclaimer |
| Trend visualization | Informational display | Low | "Not medical advice" footer |
| Dietary suggestion | Wellness recommendation | Medium | Evidence-grade recommendations; no diagnosis language |
| "You may have IBS" output | Implied diagnosis | HIGH — SaMD trigger | Remove or reframe entirely |
| "Consult your doctor" CTA | Referral prompt | Low | Standard safe harbor language |
| Biosignal interpretation | Clinical inference | HIGH — Class II+ risk | Requires clinical validation before shipping |
```

---

### 5. Compliance Gap Analysis

Current product state vs. regulatory readiness:

```markdown
## Compliance Gap Analysis: [Product] — [Date]

### Current State
- [ ] Privacy policy exists
- [ ] Terms of service exists
- [ ] Health claim language reviewed by counsel
- [ ] HIPAA BAA in place (if applicable)
- [ ] Data encryption at rest + in transit
- [ ] User data deletion flow implemented
- [ ] IRB / clinical study for validation (if Class II+)
- [ ] Quality Management System (QMS) in place (Class II+)
- [ ] FDA pre-submission meeting conducted (if Class II+)

### Gaps (Priority Order)

**P0 — Blocking (must resolve before launch):**
1. [Specific gap — e.g., "Dietary recommendation engine constitutes Class II SaMD without clinical validation"]
2. [Specific gap — e.g., "No HIPAA BAA with Supabase for PHI storage"]

**P1 — High (must resolve before commercial activity):**
1. [Gap]

**P2 — Medium (should resolve within 6 months):**
1. [Gap]

**P3 — Low (nice-to-have / monitor):**
1. [Gap]
```

---

### 6. Safe Harbor Language Reference

Language patterns that reduce regulatory risk:

```
SAFE — "Track and log your gut health symptoms"
SAFE — "View trends in your symptom history over time"
SAFE — "Research suggests that [X dietary approach] may benefit [Y population]"
SAFE — "Consult your healthcare provider before making dietary changes"

RISKY — "Optimize your gut health with our AI recommendations"
RISKY — "Based on your symptoms, you may have [condition]"
RISKY — "Our algorithm detects early signs of [condition]"
RISKY — "Clinically proven to improve [outcome]" (without clinical data)
RISKY — "Medical-grade [anything]" (without clearance)
```

---

### 7. Output: Regulatory Intelligence Brief

```markdown
# Regulatory Brief: [Product / Feature]
**Date:** [today]
**Jurisdiction:** US / EU / Both
**Preparer:** Research synthesis via web research + Claude
**Status:** DRAFT — For internal planning only; not legal advice

## Executive Summary
[2–3 sentence plain-language summary of regulatory posture and primary risk]

## Classification Analysis
[Result of Step 3]

## Claims Risk Map
[Table from Step 4]

## Compliance Gap Analysis
[Result of Step 5]

## Recommended Actions
1. [Specific, ordered, actionable items]

## Regulatory Resources
- [FDA Digital Health Center of Excellence URL]
- [Relevant FDA guidance document]
- [Relevant HHS/HIPAA resource]

## Expert Referral Recommended
[ ] Regulatory affairs specialist consultation before [specific decision point]
[ ] Healthcare attorney review of health claims language
[ ] IRB consultation for any data involving clinical populations
```

---

## Tips

- **The safest product is one that never makes a diagnosis.** Shift all language to logging, tracking, and "consult your HCP."
- Web search regulatory coverage is general — always verify against **FDA.gov directly** and the current version of guidance documents (they change).
- Use academic-focused web search for regulatory queries — you want .gov and official publications, not blog opinions.
- GastroGuard's highest risk surface: any output that could be interpreted as "you have X condition." Treat this as P0 from day one.
- Class I wellness apps have shipped without FDA clearance for years — this is a strategic decision, not just a legal one. Know the risk you're accepting.
