# Reference: project-synthesis-next-actions

**When to load:** Project Synthesis and Next Actions. Use this skill to synthesize the current Exact Sciences project folder into a clear status report and execution plan. Use when the user asks for help with project synthesis next actions.

# Skill: Project Synthesis and Next Actions

## Purpose
Use this skill to synthesize the current project folder into a clear status report and execution plan.

## When to Use
Use this after adding several files, completing a research pass, reviewing code, or reaching a project checkpoint.

## Synthesis Logic
Organize project knowledge into:
1. What is known
2. What is supported by strong evidence
3. What is uncertain
4. What needs verification
5. What should be built or researched next

## Required Output Format
```markdown
# Exact Sciences Project Synthesis

## 1. Current Project Goal
[State the goal in one precise paragraph.]

## 2. What We Know
- [Known fact 1]
- [Known fact 2]
- [Known fact 3]

## 3. Strongest Evidence
| Claim | Supporting Source | Evidence Strength | Notes |
|---|---|---|---|
|  |  | High/Medium/Low |  |

## 4. Open Questions
| Question | Why It Matters | How to Resolve | Priority |
|---|---|---|---|
|  |  |  | High/Medium/Low |

## 5. Risks / Weak Points
- [Risk 1]
- [Risk 2]
- [Risk 3]

## 6. Next Actions
### Immediate
- [ ] Task 1
- [ ] Task 2

### This Week
- [ ] Task 1
- [ ] Task 2

### Later
- [ ] Task 1
- [ ] Task 2

## 7. Decision Log
| Decision | Reason | Trade-Off | Date |
|---|---|---|---|
|  |  |  |  |
```

## Project Discipline Rules
- Separate evidence from interpretation.
- Do not hide uncertainty.
- Convert vague next steps into concrete actions.
- Flag weak sources before they contaminate project conclusions.
- Keep a decision log so the project does not drift.

## Final Check
Before finishing, answer:
1. What is the strongest conclusion?
2. What is the weakest assumption?
3. What is the next action that produces the most leverage?
