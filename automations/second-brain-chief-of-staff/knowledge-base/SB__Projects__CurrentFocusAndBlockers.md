---
Title: Current Focus and Blockers
Type: Project Execution
Domain: Engineering Projects
Date: 2026-04-21
Keywords: focus, blockers, execution, dependencies
Summary: Execution board for immediate priorities, blockers, and unblock plans.
---

## Context
- Objective: convert project intent into weekly shipping behavior.
- Current sprint window: 2 weeks.

## Key Ideas
- Focus A: Jonny Study App weekly planner + task sequencing UX.
- Focus B: GlucoLoop data schema draft + synthetic dataset tests.
- Focus C: Automation cleanup for note ingestion and tagging pipeline.
- Blockers must be concrete: missing spec, missing data, unclear ownership, unresolved bug.

## Decisions
- Blocker log examples:
  - Study App: unclear state model for recurring tasks.
  - GlucoLoop: uncertain clinical assumptions for glucose dynamics simplification.
  - Automation: parser fails on mixed markdown/pdf extraction outputs.
- Escalation path: if blocked >3 days, reduce scope or request expert input.

## Constraints
- Time fragmentation across too many repositories.
- Domain uncertainty in biomedical assumptions.
- Incomplete test harness slows confident iteration.

## Open Questions
- Which blocker, if solved first, unlocks the most downstream progress?
- What scope cuts keep momentum without harming project integrity?
- What can be converted to a one-hour spike instead of a multi-day rabbit hole?

## Next Actions
- Define one weekly ship target per active project.
- Add blocker-owner-deadline fields to sprint board.
- Reserve one weekly architecture review slot to prevent chaotic builds.
