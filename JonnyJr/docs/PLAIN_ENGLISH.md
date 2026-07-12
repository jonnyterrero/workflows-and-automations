# How to Use This Assistant (Plain English)

## What it does
- **Research** a topic from the web → saves a brief with sources.
- **Synthesize** a plan → creates tasks, test ideas, and a PR body.
- **Reminders** and **School tasks** → create Issues with due dates.
- **Code help** → suggests files & tests in Cursor.

## Quick Start
1) Ask for something (e.g., "remind me to submit HW1 on Oct 28 at 2pm").
2) Create an Issue using the Reminder template (title + due date).
3) If you need research, go to GitHub → Actions → **AI Research & PR** → enter the topic.
4) Review the Pull Request; accept changes if helpful.

## Privacy & Security
- Keys are kept locally in `.env` and in GitHub Secrets for CI.
- No grades, medical info, or home addresses are stored in the repo.
- Research sources are public links; remove any you don't want shared.

## Where things go
- **Briefs** → `docs/briefs/*`
- **Plans** → `docs/plans/*`
- **School work** → `school/<course>/<assignment>/*`
- **MATLAB** → scripts in `school/MATLAB/*`

## Troubleshooting
- If a workflow fails, see "Actions" logs. You can re-run it after fixing `.env` or secrets.
