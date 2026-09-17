# Wiring the Second Brain into Claude, ChatGPT, and Perplexity

One-time setup per surface. All three are account-level (Projects/Spaces), so they
work identically on web, desktop apps, and mobile.

The files to upload are always the same **9 files** from `content_pack\`:
`00_START_HERE.md`, `voice_profile.md`, `my_content_log.md`, `saved_inspiration.md`,
`topics_interests.md`, `audience_cadence.md`, `juicedupjonnyy_reference.md`,
`x_twitter.md`, `content_pack.json`.

---

## The system prompt (paste into every surface)

> You are my content assistant. You write in **my** voice for `[primary account]`
> (primary) and can adapt for `[secondary accounts]` when asked.
> All facts about me come from the knowledge files — read `voice_profile.md` before
> writing anything.
>
> **Voice:** `[tone descriptors]`. Quick captions average `[N]` characters, but match
> length to format. Core vocabulary: `[from voice_profile.md]`. Signature emojis:
> `[from voice_profile.md]` — use sparingly, never forced. Hashtags: `[rate]`.
> Identity arc from my bio history: `[from voice_profile.md]`.
>
> **Taste:** saved music skews `[artists from saved_inspiration.md]` — use for
> reel/story audio picks.
>
> **Avoid:** everything under "not interested" and "see less" in `topics_interests.md`.
>
> **Rules:** never invent facts about my life beyond the knowledge files; when unsure,
> ask or leave a `[bracketed placeholder]`. Give 3 options unless I ask for one.
> Keep it real, not corporate.

*(Template — every `[placeholder]` is derived automatically by `build_content_pack.py`;
fill from your generated `content_pack/voice_profile.md`. The filled-in personal version
stays local, outside this public repo.)*

---

## Claude (web or desktop)

1. claude.ai → **Projects** → New project → name it `Content Studio`.
2. Project knowledge → upload the 9 `content_pack\` files **individually** (Claude
   does not unpack zips).
3. Set project instructions → paste the system prompt above.
4. Every chat inside the project now has the full context. Works in the desktop and
   mobile apps automatically.

**If you install Claude Desktop later** (bonus — live file access, no re-uploads):
add a filesystem MCP server to `%APPDATA%\Claude\claude_desktop_config.json`.
Point it at your local working folder (`SOCIAL_BRAIN_ROOT`; on this machine the
default is `Downloads\Social media clone`):

```json
{
  "mcpServers": {
    "second-brain": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "[path to your local social-brain working folder]"
      ]
    }
  }
}
```

Then Claude Desktop can read `voice_profile.md`, query the JSONL archive, and always
see the freshest build — no re-uploading after refreshes.

## ChatGPT (web or desktop)

1. chatgpt.com → **Projects** → New project → `Content Studio`.
2. Project files → upload the 9 `content_pack\` files (skip the zips here too —
   individual files index better for retrieval).
3. Project instructions → paste the system prompt.
4. Optional deep archive: also upload `_prepared_uploads\` chunks 02–06 if you want
   ChatGPT to answer factual questions about your full posting history.
5. Alternative: build a **custom GPT** ("My Content Studio") with the same files as
   knowledge + the same instructions — useful if you want to share it across chats
   without opening the project each time.

## Perplexity

1. perplexity.ai → **Spaces** → Create space → `Content Studio`.
2. Add files → the 9 `content_pack\` files (file upload needs Pro).
3. Space instructions (under "AI instructions") → paste the system prompt.
4. Use the Space when you want **research + voice combined** — e.g. "what's trending
   in [topic] this week; give me 3 takes in my voice." Perplexity searches live web,
   then filters through your voice profile.

---

## After every `refresh_second_brain.ps1` run

Local agents (Cursor / Claude Code / Codex) and Obsidian update automatically.
For the web surfaces, replace the changed files (usually just `my_content_log.md`,
`voice_profile.md`, `audience_cadence.md`) in each Project/Space.

---

## What to actually do with it — the playbook

**Daily / weekly content:**
- "3 captions for this photo: [describe]. One short, one medium, one reflective."
- "5 story hooks in my voice for this week."
- "Draft Monday's post — check `my_content_log.md` so it's not a repeat theme."
- "Suggest reel audio for [mood] from my saved-music taste."

**Ideation & strategy:**
- "10 post ideas that fit my themes but that I haven't done yet."
- "What themes recur in my top-engagement content? What should I double down on?"
- "Plan a 4-week content calendar around my Monday anchor + 3–4 stories/week."

**Repurposing:**
- "Turn this IG caption into a tweet in my X voice."
- "Turn this long reflective caption into a Substack intro paragraph."

**Self-analysis (the second-brain angle):**
- "From my bio history and content log, how has my identity/presentation evolved
  2022 → 2026?"
- "What do my saves and likes say I consume but never post about?" (content gap)
- "Compare my two IG accounts — what belongs where?"

**Automation (Make / n8n / Zapier):**
- Feed `content_pack\content_pack.json` into the LLM node as context — same profile,
  machine-readable. Example flow: Notion idea board → LLM node (with the JSON +
  system prompt) → 3 caption drafts → back to Notion/Telegram for approval.
  Publishing stays manual by design.
