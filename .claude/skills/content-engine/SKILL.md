---
name: content-engine
description: Turns tracked AI repo activity (MCP, Hugging Face, Higgsfield) into YouTube packages and written posts. Use for repo-driven content runs, release roundups, and content calendars.
metadata:
  version: "1.0.0"
  status: initial
  reviewed: "2026-07-30"
---

# Content Engine

## Purpose
Convert real shipping activity in tracked repositories into publish-ready content: faceless YouTube packages (long-form plus shorts) and written posts (blog, X thread, LinkedIn). Every claim traces back to a specific release, commit, or diff.

## Use this skill when
- The user asks for a content run, release roundup, or "what should I make this week" from the tracked repos.
- A specific release or repo needs to become a video package, thread, or post.
- The content calendar needs filling from actual repo activity rather than invented topics.

## Do not use this skill when
- The topic has no basis in the tracked repos and no research tool is available; do not manufacture a news peg.
- The user wants analytics diagnosis of published videos; that is `youtube-agent` territory with user-supplied metrics.

## Tracked sources
Defined in `sources.json` alongside this skill. Currently: MCP spec/docs, MCP reference servers, HF Transformers, HF Diffusers, Higgsfield.

Read `why_it_matters` on each source before triaging - it states what kind of story that repo tends to produce.

Two caveats to carry into any content:
- `higgsfield-ai/higgsfield` is the open-source distributed **training** framework, last released v0.0.4-rc in March 2024. It is evergreen/background material, not news. It is **not** the Higgsfield video-generation product, which has no public repo. Never conflate them.
- MCP spec releases are dated revisions (e.g. `2026-07-28`), and RC tags publish alongside stable ones. Check which you are describing.

## Step 1: Choose scope
Confirm or infer: which repos, lookback window (default 14 days), and which output formats. Do not ask if the request already implies them.

## Step 2: Pull activity
Transport depends on where the session runs. Establish this before collecting.

- **Claude Code on the web / restricted sandboxes**: direct HTTP to `github.com` and `api.github.com` is blocked (403), so the fetch script cannot reach them. Get the feed list, then fetch each URL with **WebFetch**:

```bash
python3 .claude/skills/content-engine/scripts/fetch_repo_activity.py --print-urls
```

  WebFetch each releases/commits feed and keep the entries, their dates, and their URLs. `raw.githubusercontent.com` is reachable directly, so use it for README, changelog, and docs files when you need deeper detail.

- **Laptop, desktop, or GitHub Actions** (open egress): run the script and read the digest it writes.

```bash
# Atom feeds, no token needed
python3 .claude/skills/content-engine/scripts/fetch_repo_activity.py --days 14

# REST API: full release bodies, needs GITHUB_TOKEN for comfortable rate limits
python3 .claude/skills/content-engine/scripts/fetch_repo_activity.py --days 14 --api
```

Useful flags: `--repo owner/name` (repeatable), `--max-entries N`, `--out PATH`.

If a source returns errors, say so in the run summary. Never fill the gap with recalled or assumed activity.

## Step 3: Triage into story candidates
For each candidate, record: the repo, the specific release/commit, its URL, its date, what actually changed, and who it affects. Then rank by content potential:

- **Strong**: new capability, new model, breaking change, new named thing people will search for.
- **Medium**: meaningful performance or DX improvement, notable bugfix with user-visible impact.
- **Skip**: dependency bumps, CI changes, typo fixes, internal refactors - unless they aggregate into a "state of the repo" angle.

Prefer three well-evidenced candidates over ten thin ones. State explicitly when a window is genuinely quiet; a slow week is a real finding, not a prompt to inflate.

## Step 4: Generate the requested formats
Use the scaffolds in `templates/`:

| Format | Template |
|--------|----------|
| Long-form YouTube package | `templates/youtube-long.md` |
| Shorts cutdown | `templates/youtube-short.md` |
| Blog post | `templates/blog-post.md` |
| X thread | `templates/x-thread.md` |
| LinkedIn post | `templates/linkedin-post.md` |

For any YouTube output, also apply the `youtube-agent` skill: it owns hook construction, retention structure, title/thumbnail discipline, and packaging rules. This skill supplies the sourced substance; `youtube-agent` shapes it.

Write drafts to `7-automations/content-engine/runs/<YYYY-MM-DD>/`, one file per deliverable. Keep the digest out of git; drafts are worth keeping.

## Step 5: Evidence check before delivering
- Every factual claim maps to a digest entry with a URL. Anything else is labelled clearly as opinion, prediction, or hypothesis.
- No invented search volume, CTR, RPM, retention, download counts, or benchmark numbers. If a benchmark is quoted, it comes from the release notes and is attributed there.
- Version numbers, model names, tags, and dates are copied from the source, not remembered.
- Speculation about a project's roadmap is framed as speculation.

## Output contract
- Run summary: window, repos pulled, sources that failed, candidate count
- Ranked story candidates with source URLs and dates
- The requested drafts, one per format
- Citation list: every URL used
- Suggested calendar placement, when a calendar is in scope

## Quality gate
A run ships only if: every factual claim is traceable to a source URL, the title/hook promise matches what the body delivers, and quiet windows are reported as quiet rather than padded.

## Scheduling
On-demand by default. `SETUP.md` in this directory has ready-to-use templates for a scheduled Routine and a GitHub Actions workflow when you want it recurring.

## Example triggers
- "Do a content run on the last two weeks of MCP and Hugging Face."
- "Turn the newest MCP spec revision into a video package and an X thread."
- "What is worth making from Diffusers this week?"
