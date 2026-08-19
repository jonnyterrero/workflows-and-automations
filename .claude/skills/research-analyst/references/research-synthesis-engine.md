# Reference: research-synthesis-engine

**When to load:** Use this skill for all scientific and engineering research tasks in the Exact Sciences folder. Produces structured, source-grounded research notes that rigorously separate facts, assumptions, interpretations, and uncertainty. Trigger for: - Literature reviews and concept surveys (any STEM field) -…

# Scientific Research Synthesis Engine

The failure mode in AI-assisted research is confident vagueness: summaries
that sound authoritative but cannot be traced to sources, verified, or used
to make real decisions. Every output from this skill is structured to prevent
that failure.

---

## Step 0 — search Query Construction (Before Searching)

Before returning a synthesized answer, construct the most precise search
queries possible. Vague queries return vague results.

### Query Construction Rules
```
1. Use domain-specific terminology, not plain language
   BAD:  "how does the brain process pain"
   GOOD: "nociceptive signal transduction ascending pain pathway spinal cord"

2. Include technique/method name when comparing approaches
   BAD:  "which imaging method is better"
   GOOD: "fMRI vs EEG spatial temporal resolution comparison neuroscience"

3. Anchor to primary literature signals
   Add: "review", "meta-analysis", "systematic review", OR a specific journal
   Example: "drug nanoparticle delivery BBB penetration systematic review 2020-2024"

4. Limit scope by time when recency matters
   Example: "CRISPR base editing off-target effects 2022 2023 2024"

5. Include the application domain
   Example: "impedance spectroscopy biofilm detection electrochemical biosensor BME"
```

### search Search Templates by Task

| Task | Template Query |
|---|---|
| Concept explanation | "[term] mechanism review [year range] [subdomain]" |
| Method comparison | "[method A] vs [method B] [metric] [application] systematic review" |
| Material properties | "[material] [property] experimental characterization [application domain]" |
| Algorithm benchmark | "[algorithm] benchmark [dataset] comparison [metric] [year]" |
| Clinical/biomedical | "[condition/device] [outcome metric] clinical trial OR systematic review" |
| Computational method | "[numerical method] convergence accuracy [problem class] comparison" |

---

## Required Output Structure

### 1. Research Question
Restate the question in precise technical language. Identify the sub-domain.
```
Research Question: [exact restatement]
Domain:           [e.g., BME > Biosensors > Electrochemical Detection]
Scope:            [specific aspect being investigated]
```

### 2. Direct Answer
State the strongest, most defensible answer first. Do not bury the conclusion.
If the evidence is genuinely mixed, say so here — do not hedge defensively if
the evidence is actually clear. Format:
```
Current consensus: [what the evidence shows]
Confidence level:  [High / Moderate / Low / Contested — see framework below]
```

**Confidence Framework:**
- **High**: Multiple independent peer-reviewed sources agree; reproducible results; no major contradictions
- **Moderate**: Evidence generally consistent but limited in scope (small N, single study type, narrow conditions)
- **Low**: Limited direct evidence; extrapolated from related findings; indirect support only
- **Contested**: Evidence actively conflicts across credible sources; field unsettled

### 3. Key Concepts
For each core term in the research question:
```
Term:          [exact name]
Definition:    [precise technical definition]
Why it matters: [role in the research question]
Misconception: [most common misunderstanding; only include if documented]
```

### 4. Evidence Summary
Organize by thematic claim, not by source. For each claim:
```
Claim:         [specific, falsifiable statement]
Evidence:      [what study/data/theory supports it; include N, design, effect size if available]
Source type:   [RCT / in vitro / computational / review / textbook / standard]
Confidence:    [High / Moderate / Low / Contested]
Limitation:    [what this evidence does NOT show; scope conditions]
```

### 5. Method or Approach Comparison
When comparing two or more approaches, always include a structured table:

| Approach | Mechanism | Sensitivity/Accuracy | Speed/Cost | Limitations | Best Use Case |
|---|---|---|---|---|---|

Add a row for your recommended choice with a one-sentence justification.

### 6. Critical Analysis Checklist
Apply these filters to every source used:

```
Sample size:          Is N sufficient for the claimed conclusion?
Study design:         RCT > cohort > case study > anecdote
Controls:             Was there a proper control group?
Reproducibility:      Have results been replicated independently?
Confounders:         Were known confounders accounted for?
Measurement quality: How was the outcome measured? What are error bounds?
Claim scope:          Do conclusions exceed what the data supports?
Conflict of interest: Industry funding, author affiliations?
Publication year:     Is the methodology still current, or superseded?
```

### 7. Red Flags (Flag Explicitly, Never Suppress)
```
[ ] Overclaiming: conclusions exceed the data
[ ] No control group
[ ] n < 20 for a quantitative claim
[ ] Correlation stated as causation
[ ] Mechanistic claim without mechanistic evidence
[ ] Outdated standard (check against current guidelines)
[ ] Industry-sponsored with undisclosed conflict
[ ] Single lab, never replicated
```
If any flag fires, mark it clearly in the output. Do not omit it for readability.

### 8. Practical Implications
State how the evidence affects:
- Design choices (materials, methods, architectures, protocols)
- Experimental decisions (controls, measurement approach, sample size)
- Future study direction
- Engineering trade-offs

Be concrete: "This implies that X should be used instead of Y when Z condition holds."

### 9. Open Questions
Categorize each uncertainty:
```
Missing data:     [gap because no study has measured it]
Conflicting data: [gap because studies disagree and neither is definitive]
Developing field: [gap because the science is still maturing]
```

### 10. Next Research Steps
Actionable, specific next steps. Not vague ("do more research"):
```
Search terms:     ["[specific query string]", ...]
Databases:        [PubMed / IEEE Xplore / Web of Science / arXiv / Google Scholar]
Papers to find:   [author, title fragment, or DOI if known]
Experiments:      [what to run and what variable to measure]
Tools to check:   [software, databases, standards documents]
Skill to activate: [which Exact Sciences skill to load next]
```

---

## Source Priority Hierarchy

Use sources in this order for factual claims:

| Priority | Source Type | When to Use |
|---|---|---|
| 1 | Peer-reviewed primary research | Core quantitative claims |
| 2 | Systematic reviews / meta-analyses | Comparing across studies |
| 3 | Authoritative textbooks (recognized publisher/OER) | Established theory and definitions |
| 4 | University course materials | Pedagogical framing |
| 5 | Government / standards bodies (NIH, IEEE, NIST, FDA) | Regulatory, safety, clinical |
| 6 | Technical documentation | Tool/software-specific facts |
| 7 | Reputable professional orgs | Context and practice norms |
| 8 | News / blogs | Context only — never for core claims |

### Citation Format
For every factual claim, provide traceability:
```
[Authors] ([Year]). [Title fragment]. [Journal/Source]. [DOI or URL if stable]
Why this source: [one sentence — what specifically it contributes]
```

---

## Domain-Specific Source Notes

| Domain | Best Primary Sources | Key Journals / Databases |
|---|---|---|
| Biomedical Engineering | NIH, PubMed, IEEE EMBC | IEEE TBME, Biomaterials, Acta Biomaterialia |
| Chemistry | ACS, RSC, NIST WebBook | JACS, Angewandte Chemie, J. Phys. Chem. |
| Neuroscience | PubMed, Allen Brain Atlas | Nature Neurosci., J. Neurosci., NeuroImage |
| Computational / Numerical | arXiv, ACM, SIAM | J. Comput. Phys., SIAM J. Sci. Comput. |
| Machine Learning | arXiv, Papers With Code | NeurIPS, ICML, ICLR proceedings |
| Signals & Systems | IEEE Xplore | IEEE Trans. Signal Processing |

---

## Quality Gate

A research synthesis is complete only if it includes:
- [ ] Precise research question with domain tag
- [ ] Direct answer with explicit confidence rating
- [ ] Key concepts defined with misconceptions flagged
- [ ] Evidence organized by claim with source type and limitations
- [ ] Comparison table (when comparing approaches)
- [ ] Red flags section completed (suppress nothing)
- [ ] Concrete next steps with specific search queries

Vague summaries are not acceptable output.
