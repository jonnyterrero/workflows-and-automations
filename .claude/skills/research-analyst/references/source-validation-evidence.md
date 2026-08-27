# Reference: source-validation-evidence

**When to load:** Source Validation and Evidence Ranking. Use this skill to evaluate the credibility, usefulness, and limitations of sources inside the Exact Sciences project. Use when the user asks for help with source validation evidence.

# Skill: Source Validation and Evidence Ranking

## Purpose
Use this skill to evaluate the credibility, usefulness, and limitations of sources inside the project.

## When to Use
Use this whenever search produces search results, summaries, papers, clinical references, technical articles, or web sources.

## Evidence Ranking
Rank each source using this hierarchy:

1. Primary peer-reviewed research
2. Systematic reviews / meta-analyses
3. Clinical guidelines or regulatory documents
4. Official documentation / institutional sources
5. Reputable textbooks or technical references
6. Industry white papers
7. News articles
8. Blogs, forums, unsourced commentary

## Evaluation Criteria
For each source, evaluate:
- Authority: Who produced it?
- Date: Is it current enough?
- Method quality: Are methods transparent?
- Data quality: Is the sample size, dataset, or validation adequate?
- Bias/conflict: Any commercial or ideological incentives?
- Reproducibility: Can the method/results be checked?
- Applicability: Does it apply to this exact project?

## Required Output Format
```markdown
# Source Validation Report

## Source: [Title]
- Citation / URL:
- Source Type:
- Evidence Rank: 1-8
- Date:
- Field:

## Credibility Assessment
- Authority:
- Method Quality:
- Data Quality:
- Reproducibility:
- Bias / Conflicts:

## Project Usefulness
- Usefulness: High / Medium / Low
- Best use case:
- What NOT to use it for:

## Key Takeaways
1. [Takeaway 1]
2. [Takeaway 2]
3. [Takeaway 3]

## Limitations
- [Limitation 1]
- [Limitation 2]

## Verdict
[Keep / Use with caution / Exclude]
```

## Red Flags
Reject or downgrade sources that:
- Make strong claims without data
- Lack methods
- Use outdated clinical or regulatory information
- Confuse correlation with causation
- Generalize beyond the study population
- Have obvious commercial bias without disclosure

## Standard
Do not treat all sources equally. A polished article with weak evidence is still weak evidence.
