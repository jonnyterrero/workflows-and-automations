# Reference: project-research-intake

**When to load:** Project Research Intake. Use this skill to intake, classify, and organize any new material added to the Exact Sciences project/folder in web search. Use when the user asks for help with project research intake.

# Skill: Project Research Intake

## Purpose
Use this skill to intake, classify, and organize any new material added to the project/folder in search.

## When to Use
Use this whenever a new PDF, article, dataset, protocol, code snippet, notebook, image, or note is added to the project.

## Operating Rules
1. Identify the material type:
   - Research paper
   - Dataset
   - Protocol/SOP
   - Code or notebook
   - Internal note
   - Regulatory/clinical reference
   - Background reading
2. Extract the core metadata:
   - Title
   - Author/source
   - Date/version
   - Field/topic
   - Main claim or purpose
   - Methods used
   - Data type
   - Limitations
3. Classify the material by project relevance:
   - Directly actionable
   - Background context
   - Validation/reference source
   - Low relevance
4. Summarize the file in three layers:
   - 3-sentence executive summary
   - Technical summary
   - Actionable next steps

## Output Format
```markdown
# Intake Summary: [File Name]

## 1. Metadata
- Title:
- Source:
- Date:
- Type:
- Topic Area:

## 2. Executive Summary
[Three concise sentences.]

## 3. Technical Summary
[Methods, concepts, equations, models, protocols, or data structure.]

## 4. Project Relevance
- Relevance Level: High / Medium / Low
- Why it matters:
- How it can be used:

## 5. Limitations / Risks
- [Limitation 1]
- [Limitation 2]

## 6. Action Items
- [ ] Action 1
- [ ] Action 2
- [ ] Action 3
```

## Quality Standard
Do not summarize vaguely. Preserve technical details, units, assumptions, and terminology. If the source is weak or unclear, say so directly.
