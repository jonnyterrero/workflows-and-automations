# Reference: data-extraction-tables

**When to load:** Data Extraction and Table Building. Use this skill to extract structured data from papers, PDFs, reports, notes, or datasets into reusable Markdown tables. Use when the user asks for help with data extraction tables.

# Skill: Data Extraction and Table Building

## Purpose
Use this skill to extract structured data from papers, PDFs, reports, notes, or datasets into reusable Markdown tables.

## When to Use
Use this for:
- Extracting study variables
- Comparing methods
- Building literature review matrices
- Pulling experimental parameters
- Organizing biomarker, assay, or clinical information
- Creating project-ready tables from messy notes

## Extraction Rules
1. Preserve exact units.
2. Preserve sample sizes.
3. Preserve model names, assay names, software versions, and statistical tests.
4. Distinguish reported facts from interpretation.
5. Mark missing information as `Not reported`, not blank.
6. Never invent values.

## Standard Table Templates

### Literature Matrix
```markdown
| Source | Year | Objective | Dataset/Sample | Method | Key Finding | Limitations | Project Use |
|---|---:|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |
```

### Experimental Parameter Table
```markdown
| Parameter | Value | Unit | Source Location | Notes |
|---|---:|---|---|---|
|  |  |  |  |  |
```

### Model / Algorithm Comparison
```markdown
| Model | Input Features | Output | Strengths | Weaknesses | Validation Used | Best Use Case |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |
```

### Dataset Audit Table
```markdown
| Dataset | File Type | Rows | Columns | Missing Data | Target Variable | Risks | Ready for Analysis? |
|---|---|---:|---:|---|---|---|---|
|  |  |  |  |  |  |  |  |
```

## Required Output Format
```markdown
# Extracted Data: [Topic/File]

## Extraction Goal
[State what information was extracted and why.]

## Structured Table
[Insert relevant table.]

## Notes on Ambiguity
- [Ambiguity 1]
- [Ambiguity 2]

## Follow-Up Actions
- [ ] Verify source page/section
- [ ] Cross-check against another source
- [ ] Add to project database/literature matrix
```

## Quality Standard
A table is only useful if it is traceable. Include source location whenever possible: page, section, figure, table number, or paragraph context.
