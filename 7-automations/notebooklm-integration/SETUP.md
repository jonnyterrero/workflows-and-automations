# NotebookLM Integration — Local Setup (Windows)

Get NotebookLM working *through Claude* on your own machine. This does **not** run in
Claude on the web / a hosted session — NotebookLM has no API, so the `notebooklm-mcp`
server automates a real Chrome window signed into your Google account. That requires a
visible browser and your login, which only exist locally.

## Prerequisites

- **Node.js ≥ 18** — check with `node -v`
- **Google Chrome** (stable). A bundled Chromium is used as fallback, but real Chrome is preferred.
- A **Google account** with NotebookLM access.
- **Claude Code** (desktop app or CLI) running on this machine.

## 1. Wire up the MCP server

Already done in this repo — the `notebooklm` server is declared in the root
[`.mcp.json`](../../.mcp.json):

```json
"notebooklm": {
  "command": "cmd",
  "args": ["/c", "npx", "-y", "notebooklm-mcp@latest"],
  "env": { "NOTEBOOKLM_PROFILE": "full" },
  "autoStart": false
}
```

Open Claude Code **with this repo as the working folder** so it picks up `.mcp.json`.
(If you'd rather register it globally instead of per-repo, add the same block to
`~/.claude.json` under `mcpServers`.)

The `cmd /c npx` wrapper is the reliable pattern on Windows — it matches how
`claude-flow` is already configured in this repo.

## 2. First run — start the server

In Claude Code, confirm the server is discoverable (`/mcp` lists servers, or just ask
Claude to call the `get_health` tool). The first `npx` call downloads
`notebooklm-mcp@latest`, so give it a moment.

## 3. One-time Google login

Ask Claude to run the **`setup_auth`** tool. This opens a **visible Chrome window**:

1. Log into your Google account and open NotebookLM.
2. Finish within ~10 minutes (the login window times out).
3. Cookies are cached at `%APPDATA%\notebooklm-mcp\chrome_profile\` — you won't need to
   repeat this each session. When it eventually expires, run **`re_auth`**.

> Multiple Google accounts: the server supports an `--account` flag; add it to the
> `args` array if you need to pin a specific profile.

## 4. Verify

Ask Claude to:
1. `get_health` → should report authenticated.
2. `list_notebooks` → should return your library (empty is fine on a fresh account).

Once those work, use the [`SKILL.md`](SKILL.md) workflows: add sources, ask grounded
questions, generate Audio Overviews, or load the second-brain knowledge base.

## Perplexity (already wired)

Your `.mcp.json` also declares the `perplexity` server. To use it locally, set a
`PERPLEXITY_API_KEY` environment variable (get a key from
<https://www.perplexity.ai/account/api/group>). It's the same official server that's
already available in Claude on the web, so this only matters for the local setup.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `notebooklm` tools don't appear | Open Claude Code in this repo (so `.mcp.json` loads), or add the block to `~/.claude.json`. Run `/mcp` to confirm it's listed. |
| `npx` "command not found" | Node/npm not on PATH — reinstall Node ≥ 18, reopen the terminal. |
| Login window never appears | You're on a headless/remote box. First-time `setup_auth` needs a real desktop; on a headless Linux server use `xvfb-run`. WSL1 is unsupported (use WSL2 + WSLg on Win 11). |
| Answers stop working after a while | Session cookies expired — run `re_auth`. |
| "too many sessions" | Default cap is 10; run `close_session` / `reset_session`, or raise `MAX_SESSIONS`. |
| Want fewer tools exposed | Set `NOTEBOOKLM_PROFILE` to `minimal` or `standard` instead of `full`. |

## Caveats

- **Unofficial.** No Google API is involved; NotebookLM UI changes can break the server.
- **Credential storage is plain.** Your login lives in the Chrome profile dir above with
  no extra encryption — treat that folder like a saved browser session.
- Source: <https://github.com/PleasePrompto/notebooklm-mcp>
