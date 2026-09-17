# Second Brain — Social Media Layer

Turns official platform data exports (Instagram, X/Twitter) into LLM-ready context:
a normalized archive, a distilled content pack for writing in my voice, and
upload-ready chunks for ChatGPT / Claude / Perplexity Projects.

Sibling of [`../second-brain-chief-of-staff/`](../second-brain-chief-of-staff/) —
that layer is planning and knowledge management; this layer is **social presence and
content generation**. Same brain, different lobe.

Complements the hub skills [`.claude/skills/content-engine/`](../../.claude/skills/content-engine)
(repo-activity → YouTube/blog) and [`.claude/skills/content-production/`](../../.claude/skills/content-production)
(narration + assembly). This layer is the *personal IG/X voice* those pipelines
should not invent.

## Privacy model — code in git, data local

**Only the pipeline lives in this repo.** This GitHub repo is public. Posting history,
likes, saves, searches, follower lists, and the generated voice profile **never get
committed**. The `.gitignore` in this folder enforces that. Raw platform exports stay
in a working folder outside git (default: `Downloads\Social media clone`).

## Pipeline

```
raw exports (IG/X zips, unzipped)
        │  build_second_brain.py
        ▼
normalized JSONL archive (one clean record/line, per account, per type)
        │  build_content_pack.py
        ▼
content_pack/ — voice_profile, content log, inspiration, cadence (md + json)
        │  prepare_uploads.py
        ▼
_prepared_uploads/ — ordered zip chunks + UPLOAD_INDEX.md for web LLMs
```

`refresh_second_brain.ps1` runs all three steps and syncs markdown into the
Obsidian vault — the single command after every new export drop.

## Setup

1. Keep unzipped platform exports in a working folder **outside this repo**.
   Default: `C:\Users\JTerr\Downloads\Social media clone`.
2. Optional: copy `config.example.json` → `config.local.json` and edit `data_root`
   / `vault` (gitignored). Or set `SOCIAL_BRAIN_ROOT` / `SOCIAL_BRAIN_VAULT`.
3. From `scripts/`, run `refresh_second_brain.ps1` (or double-click
   `Refresh second brain.bat`).
4. Wire the generated `content_pack/` into Claude / ChatGPT / Perplexity —
   see [`docs/WIRE_INTO_LLMS.md`](docs/WIRE_INTO_LLMS.md).

You do **not** copy these scripts into the working folder. They read and write
the data folder via `scripts/paths.py`.

## Contents

| Path | What |
| ---- | ---- |
| `scripts/paths.py` | Resolves the local data folder + vault (env / config.local.json / defaults) |
| `scripts/build_second_brain.py` | Normalize raw exports → JSONL + markdown tables per account |
| `scripts/build_content_pack.py` | Distill archive → voice profile, content log, taste, cadence |
| `scripts/prepare_uploads.py` | De-dupe + chunk into ordered upload zips (`--max-mb`, `--all`, `--include-dms`) |
| `scripts/refresh_second_brain.ps1` | One-command refresh: all three builds + Obsidian vault sync |
| `docs/SECOND_BRAIN_INDEX.md` | Master index — layout, record schema, how an LLM should consume it |
| `docs/AUTOMATED_CONTENT_WORKFLOW.md` | Content-engine workflow (system prompt template, task prompts, cadence loop) |
| `docs/WIRE_INTO_LLMS.md` | Per-surface setup: Claude/ChatGPT Projects, Perplexity Spaces, MCP, playbook |
| `.claude/skills/draft-content/` | Cursor/Claude skill that drafts in the generated voice (hub copy) |

## Record schema (normalized JSONL)

`account, type, timestamp, datetime, url, username, text, hashtags, media_uris, extra, source_file`

Record types include: `own_post`, `own_reel`, `own_story`, `repost`, `post_comment`,
`saved_post`, `saved_music`, `liked_post`, `following`, `follower`, `interest`,
`not_interested`, `profile_change`, `search_keyword`, `video_watched`, and more.
DMs and media binaries are excluded by default at every stage.
