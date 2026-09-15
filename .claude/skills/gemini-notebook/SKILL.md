---
name: gemini-notebook
description: "Drive Google's Gemini Notebook (formerly NotebookLM) programmatically — create notebooks, add sources, query them, generate audio/video/slides, download artifacts, and share. Use when the user wants to add material to, build, or pull from a Gemini/NotebookLM notebook."
metadata:
  version: "1.0.0"
  status: initial
  reviewed: "2026-09-15"
  upstream: "https://github.com/jacob-bd/gemini-notebook-mcp-cli"
  package: "notebooklm-mcp-cli"
---

# Gemini Notebook (NotebookLM) Skill

## Purpose
Automate Google Gemini Notebook / NotebookLM through the `notebooklm-mcp-cli`
package, exposed here as the `gemini-notebook` MCP server (tools appear as
`mcp__gemini-notebook__*`). Also usable directly via the `nlm` CLI.

## Use this skill when
- The user wants to **add a source** (URL, file, pasted text, or Google Drive
  doc) to a Gemini/NotebookLM notebook.
- Creating a new notebook, listing notebooks, or querying/chatting against a
  notebook's sources.
- Generating studio artifacts (audio overview, video, slides) or downloading
  them.
- Sharing a notebook or running cross-notebook / batch / pipeline operations.

## Do not use this skill when
- The user means a different notebook product (Jupyter, OneNote, etc.).
- No notebook context exists and the task is plain research — use a research
  skill and only push results here if the user asks.

## One-time setup (must run on the user's own machine, not in a remote session)

```bash
# Install the CLI + MCP server (creates `nlm` and `notebooklm-mcp` executables)
uv tool install notebooklm-mcp-cli      # or: pipx install notebooklm-mcp-cli

# Authenticate — opens a browser for Google sign-in and stores cookies
nlm login
```

- The `gemini-notebook` MCP server is registered in the repo's `.mcp.json` as
  `uvx --from notebooklm-mcp-cli notebooklm-mcp`, so `uvx` bootstraps the
  package without a global install. `uv` must be on `PATH`.
- **Auth caveat:** `nlm login` requires an interactive browser and Google
  account. It **cannot** be completed inside a non-interactive remote/cloud
  session. Log in once locally; the stored session is then reused.
- **Enterprise only** — set env vars if using a Vertex/Enterprise deployment:
  `NOTEBOOKLM_BASE_URL`, `NOTEBOOKLM_PROJECT_ID`, `NOTEBOOKLM_LOCATION`
  (`global` | `us` | `eu`). Consumer accounts need none of these.

## Key tools (43 total; names as exposed by the MCP server)
- **Notebooks:** `notebook_list`, `notebook_create`
- **Sources (the core "add to my notebook" flow):** `source_add`,
  `source_sync_drive`
- **Query / chat:** `notebook_query`, `chat_list`, `chat_get`, `chat_export`,
  `cross_notebook_query`
- **Studio generation:** `studio_create` (audio / video / slides),
  `studio_revise`
- **Artifacts:** `download_artifact`, `download_all_artifacts`
- **Research:** `research_start`
- **Sharing:** `notebook_share_*`
- **Orchestration / misc:** `batch`, `pipeline`, `tag`, `usage_get`

Exact argument shapes vary by tool — confirm with `nlm <command> --help` or the
upstream README rather than guessing signatures.

## Typical workflow: add material to a notebook
1. `notebook_list` — find the target notebook, or `notebook_create` a new one.
2. `source_add` — attach the URL / file / text (or `source_sync_drive` for a
   Drive doc) to that notebook.
3. Confirm with `notebook_query` that the source is indexed and answerable.
4. If the user wants an artifact, `studio_create` then `download_artifact`.

## Safety / conventions
- Do not create notebooks or add sources the user did not ask for; sharing
  (`notebook_share_*`) is outward-facing — confirm recipients first.
- If the MCP tools are unavailable (auth not completed, `uv` missing), say so
  and fall back to documenting the exact `nlm` commands for the user to run
  locally, rather than reporting silent failure.
