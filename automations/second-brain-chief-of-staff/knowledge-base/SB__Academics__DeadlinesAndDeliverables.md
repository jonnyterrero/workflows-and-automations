---
Title: Deadlines and Deliverables
Type: Academic Operations
Domain: Academics
Date: 2026-04-21
Keywords: deadlines, exams, labs, deliverables, risk
Summary: Operational timeline of upcoming deliverables with risk level and preparation lead time.
---

## Context
- Purpose: Single source of truth for due dates across courses and research obligations.
- Update cadence: daily quick check + Sunday full refresh.

## Key Ideas
- Recommended columns: Item, Course/Project, Due Date, Effort, Dependency, Risk, Next Step.
- Lead-time rules: exams (10 days), lab reports (3 days), coding assignments (5 days), reading memos (2 days).
- Risk flags: RED if no started draft by 50% of runway; YELLOW if dependencies unresolved.

## Decisions
- Use rolling 14-day horizon for active scheduling and 45-day horizon for awareness.
- Break every deliverable into draft-review-final stages.
- Lock a hard buffer: submit 12 hours before official deadline when possible.

## Constraints
- Some due dates shift with professor announcements; verification required weekly.
- Shared-team deliverables depend on others’ response latency.
- Competing exam clusters may force triage.

## Open Questions
- Which upcoming deadlines are under-scoped relative to true effort?
- Are there hidden dependencies (TA feedback, data collection, teammate code)?
- What can be pre-committed this week to reduce next week’s load?

## Next Actions
- Populate the table with exact dates from LMS/syllabi tonight.
- Add risk color tags and runway percentages.
- Set automated reminders at T-7, T-3, T-1 days.
