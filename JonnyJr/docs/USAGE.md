# How to Use the Assistant (Plain English)

- **Research**: turn a topic into a brief with sources.
- **Synthesis**: produce a plan, tasks, and PR body.
- **Reminders/School**: create Issues with due dates.
- **Coding**: Cursor suggests files/tests to create.

Where things go:
- Briefs → `docs/briefs/*`
- Plans → `docs/plans/*`
- School → `school/<course>/<assignment>/*`

Privacy: keys live in `.env` locally and in GitHub Secrets for CI. No personal data committed.

### Windows Quick Start
- Run: `powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1`
- Then: `npm -w @jonnyjr/ts run test` and `pytest -q` (from venv).

Example artifacts

docs/briefs/sample-brief.md and docs/plans/sample-plan.md (use the samples from my previous message).