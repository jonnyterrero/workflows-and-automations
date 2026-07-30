---
name: notebooklm-integration
description: Use when the user wants to work with Google NotebookLM through Claude — create or manage notebooks, add sources, ask questions grounded in their sources, or generate/download Audio Overviews. Backed by the notebooklm-mcp server (browser automation over a logged-in Google account). Also use when feeding the second-brain knowledge base into a NotebookLM notebook.
---

# NotebookLM Integration

Drives Google NotebookLM via the `notebooklm-mcp` server. There is **no official NotebookLM API** — this server automates a real Chrome window signed into the user's Google account, so a one-time interactive login is required and the tools only work where a browser + Google session exist (the user's own machine, not a hosted/web session).

Tools appear as `mcp__notebooklm__*` once the server is running. If they are not present, the server isn't wired up or auth hasn't been done — send the user to [SETUP.md](SETUP.md).

## Preflight (do this first, every session)

1. Call `get_health` to confirm the server is up and authenticated.
2. If health reports no auth / expired session, tell the user to run `setup_auth` (opens a visible Chrome; they have ~10 min to log into Google). Do not retry blindly — a failed login just times out.

## Tool reference

| Goal | Tool | Notes |
| --- | --- | --- |
| Confirm server + login | `get_health` | Run before anything else |
| First-time Google login | `setup_auth` | Opens visible Chrome; user logs in manually |
| Re-login after expiry | `re_auth` | Same flow when cookies go stale |
| List existing notebooks | `list_notebooks` | Returns names + ids in the local library |
| Create / register a notebook | `add_notebook` | Adds a notebook to the managed library |
| Pick the active notebook | `select_notebook` | All source/Q&A ops act on the selected one |
| Add a source | `add_source` | URL, pasted text, or file the notebook ingests |
| Ask a grounded question | `ask_question` | Returns an answer **with citations** to sources |
| Generate an Audio Overview | `generate_audio` | Kicks off NotebookLM's podcast-style audio |
| Download the audio | `download_audio` | Retrieves the generated file |
| Search the library | `search_notebooks` | Find a notebook by keyword |
| Rename / edit metadata | `update_notebook` | |
| Remove from library | `remove_notebook` | Does not delete from Google, only unmanages |
| Library stats | `get_library_stats` | Counts, sizes |
| Session hygiene | `list_sessions`, `close_session`, `reset_session` | Max 10 concurrent sessions by default |
| Data cleanup | `cleanup_data` | Clears local cached data |

## Core workflows

### Ask a question grounded in sources
1. `get_health` → `select_notebook` (or `add_notebook` + `add_source` first)
2. `ask_question` with the user's question
3. Return the answer **and surface the citations** — the point of NotebookLM is grounded, sourced answers. Never drop the citations.

### Build a notebook from sources, then generate audio
1. `add_notebook` → `select_notebook`
2. `add_source` once per source (loop; add them one at a time and confirm each landed)
3. Optional: `ask_question` to sanity-check the notebook understood the material
4. `generate_audio` → wait → `download_audio`

### Feed the second-brain knowledge base into NotebookLM
The `7-automations/second-brain-chief-of-staff` automation produces markdown KB files
(`knowledge-base/SB__*.md`). To turn that into a queryable/audio notebook:
1. `add_notebook` named e.g. "Second Brain — Operating System"
2. `select_notebook`
3. `add_source` for each `SB__*.md` file the user wants in scope
4. `ask_question` to query across the whole brain, or `generate_audio` for a spoken briefing

## Rules & cautions

- **Never fabricate NotebookLM output.** If a tool isn't available or a call fails, say so — do not invent notebook contents, answers, or citations.
- **One source at a time.** `add_source` is per-source; confirm each succeeded before moving on.
- **Audio is slow.** `generate_audio` can take minutes. Kick it off, then check/download; don't spin.
- **Unofficial + fragile.** This is browser automation; NotebookLM UI changes can break it. On repeated failures, check `get_health` and suggest `re_auth` before deeper debugging.
- **Login is local and manual.** You cannot complete Google login for the user — only trigger `setup_auth`; they finish it in the Chrome window.

## Setup

Local install, Windows-specific steps, and the `.mcp.json` wiring live in [SETUP.md](SETUP.md).
The server is already declared in the repo's root `.mcp.json` under the `notebooklm` key.
