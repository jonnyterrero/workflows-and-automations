# Content Engine - setup and operation

On-demand skill for turning tracked repo activity into YouTube packages and written posts.

## Tracked repos

Configured in `sources.json`:

| Repo | Role |
|------|------|
| `modelcontextprotocol/modelcontextprotocol` | MCP spec + docs; dated revision releases |
| `modelcontextprotocol/servers` | Reference servers; "you can now connect X" stories |
| `huggingface/transformers` | New model architectures, early search demand |
| `huggingface/diffusers` | Image/video pipelines; best visual payoff |
| `higgsfield-ai/higgsfield` | Distributed training framework; evergreen, low activity |

Add a repo by appending an entry with `owner`, `repo`, `label`, `niche`, `default_branch`, and `why_it_matters`. Set `"enabled": false` to mute one without deleting its notes. `scripts/test_fetch_repo_activity.py` checks that every entry has the required fields.

### Two naming traps

- **Higgsfield.** The GitHub repo is the open-source distributed *training* framework, last released `v0.0.4-rc` in March 2024. The Higgsfield *video-generation product* is a separate commercial service with no public repo. Content must never treat repo activity as product news.
- **MCP revisions.** Releases are dated (`2026-07-28`), and RC tags publish next to stable ones. Always state which you mean.

## Why the repos are not "attached" as sources

Attaching them to a Claude Code session was attempted and is not possible here:

- `add_repo` rejects them: cross-owner adds are unsupported while the session holds `jonnyterrero` repos. A session can only add repos from its existing owner.
- The GitHub MCP server denies them: session scope is `jonnyterrero/workflows-and-automations` only.

Neither matters for this workflow. These are public repos, and content generation needs their *published activity*, not a working checkout. To actually browse one, start a new session with that repo as the initial source.

## Transports

Where the fetch runs determines what works. Verified 2026-07-30 in Claude Code on the web:

| Host | Status |
|------|--------|
| `github.com` (Atom feeds) | 403 for direct HTTP; reachable via the **WebFetch** tool |
| `api.github.com` | 403 for direct HTTP; blocked for the GitHub MCP too |
| `raw.githubusercontent.com` | 200 - reachable directly, good for READMEs, changelogs, docs |

So:

- **In a restricted session**, list the feeds and fetch them with WebFetch:

  ```bash
  python3 .claude/skills/content-engine/scripts/fetch_repo_activity.py --print-urls
  ```

- **On your laptop or in CI** (open egress), run the fetcher directly:

  ```bash
  # Atom feeds, no token
  python3 .claude/skills/content-engine/scripts/fetch_repo_activity.py --days 14

  # REST API: full release bodies, higher rate limits with a token
  export GITHUB_TOKEN=...   # a read-only public-repo token is enough
  python3 .claude/skills/content-engine/scripts/fetch_repo_activity.py --days 14 --api
  ```

Flags: `--repo owner/name` (repeatable), `--days N`, `--max-entries N`, `--out PATH`, `--print-urls`.

Exit codes: `0` success, `1` config error, `2` every source failed.

Requires only the Python 3 standard library.

## Where output goes

| Kind | Path | In git |
|------|------|--------|
| Activity digests | `.claude/skills/content-engine/.cache/` | no - gitignored |
| Drafts | `automations/content-engine/runs/<YYYY-MM-DD>/` | yes |

## Tests

```bash
python3 .claude/skills/content-engine/scripts/test_fetch_repo_activity.py
```

Covers feed parsing, date windowing, HTML cleanup, `--print-urls`, filter errors, and `sources.json` completeness. The network paths cannot be exercised where `github.com` is blocked, so parsing is tested against a fixture matching GitHub's real Atom shape.

## Making it recurring (later)

Two ready templates. Both are inert until you act on them.

### Option A - scheduled Routine

Wakes a session on a schedule, so it can both collect and write drafts. Ask Claude:

> Create a Routine named "weekly content run", cron `0 13 * * 1`, that runs the content-engine skill for the last 14 days across all enabled sources and drafts a long-form YouTube package plus an X thread for the top candidate.

Notes:
- Cron is UTC. `0 13 * * 1` is Monday 13:00 UTC.
- Use a fresh session per firing so each run starts clean.
- A restricted environment still needs the WebFetch path, which a Routine-driven session has.

### Option B - GitHub Actions

`templates/scheduled/content-engine.yml` collects the digest weekly and commits it. Activate with:

```bash
cp .claude/skills/content-engine/templates/scheduled/content-engine.yml \
   .github/workflows/content-engine.yml
```

Runners have open egress, so the `--api` path works. The workflow stops at the data layer; the file's trailing comment shows where to add model-driven draft generation and which secret it needs.

## Relationship to youtube-agent

`content-engine` sources and verifies the substance. `youtube-agent` owns hook construction, retention structure, and packaging discipline. Any YouTube output should apply both.
