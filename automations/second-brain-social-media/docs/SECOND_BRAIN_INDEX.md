# Social Media Second Brain — Master Index

Single entry point for **any LLM** (ChatGPT, Claude, Cursor, Gemini) that needs
context on the operator's social presence. Everything is derived from official
platform data exports. Raw exports are never modified. DMs and media binaries
are excluded from all outputs.

Data is generated locally by `scripts/build_second_brain.py` +
`scripts/build_content_pack.py`. This file describes the layout; it does not
contain the records.

## Accounts (filled by the local build)

| Platform | Account | Role |
|----------|---------|------|
| Instagram | `[primary handle]` | Primary voice |
| Instagram | `[secondary handle]` | Reference |
| X (Twitter) | `[x handle]` | Reference (light use) |

Accounts are kept **separate** and tagged by an `account` field — nothing is silently merged.

## Two ways to consume this

### 1. `content_pack/` — the daily driver (START HERE)
Distilled, human- and LLM-readable context tuned for **content generation**. Small enough to
drop wholesale into a ChatGPT Project, a custom GPT's knowledge, or a Claude project.
- `00_START_HERE.md` — snapshot + suggested system prompt seed
- `voice_profile.md` — how I write (emojis, vocabulary, caption length, bio/name history, real samples)
- `my_content_log.md` — every post/reel/story I've published, with captions
- `saved_inspiration.md` — accounts I save from, recurring themes, **music/audio taste**
- `topics_interests.md` — interests, searches, and **"not interested" avoid-signals**
- `audience_cadence.md` — audience size, locations, when I post
- `[secondary]_reference.md` — condensed second IG account
- `x_twitter.md` — X voice + top tweets by engagement
- `content_pack.json` — machine-readable version of all the above (for Make/n8n/Zapier)
- `content_pack.zip` — all of the above in one upload

### 2. `_upload_batches/` + `<account>/` — the full archive (deep dives)
Complete, faithful record of everything. Use when you need raw fidelity, not a summary.
- `<account>/normalized/<type>.jsonl` — one clean record per line (full fidelity)
- `<account>/normalized/_all.jsonl` — every record for that account
- `<account>/markdown/<type>.md` — browsable tables (capped at 500 rows)
- `<account>/manifest.json` — counts + exactly what was scanned/skipped
- `_upload_batches/<account>/*.zip` — the raw JSON, chunked for upload (json only, no media/DMs)

## Canonical record schema (normalized JSONL)
`account, type, timestamp, datetime, url, username, text, hashtags, media_uris, extra, source_file`

Record `type` values include: own_post, own_post_archived, own_reel, own_story, repost,
post_comment, reel_comment, saved_post, saved_collection, saved_music, liked_post,
liked_comment, following, follower, close_friend, favorited_profile, interest, topic,
topic_see_less, not_interested, profile_change, location, search_keyword, profile_search,
search_recent, video_watched, post_viewed, ad_category.

## How an LLM should use this
- **Writing content in my voice** → read `content_pack/voice_profile.md` (+ `x_twitter.md`). Match tone, length, emoji density; favor my vocabulary; respect the avoid-signals in `topics_interests.md`.
- **Ideas / what resonates** → `saved_inspiration.md` (taste), `my_content_log.md` (what I already do), `x_twitter.md` "top tweets by engagement".
- **Scheduling** → `audience_cadence.md`.
- **Deep/factual lookups** → query the per-type `.jsonl` files under `<account>/normalized/`.

## Rebuilding after new exports
From `scripts/` (data folder is resolved by `paths.py`, not by copying scripts around):
```bash
python build_second_brain.py     # re-normalize raw exports -> JSONL/MD/zips
python build_content_pack.py     # distill -> content_pack/ (+ folds in X if present)
```
Or run `refresh_second_brain.ps1` to do both, re-chunk uploads, and sync the Obsidian vault.
To add TikTok (or any new source), add a `(glob, type)` to `REGISTRY` and map it in `PARSERS`.
