# Automated Content Workflow

A concrete setup for turning this Second Brain into an automated content engine.
Built from the real data in `content_pack/`. Update the numbers by re-running
`build_content_pack.py` after new exports.

---

## Step 1 — Load the context (once)
Pick your surface:
- **ChatGPT** → create a **Project** (or a custom GPT) → upload `content_pack/content_pack.zip`
  (or the individual `.md` files) as knowledge. Paste the system prompt below into the
  Project/GPT instructions.
- **Claude** → create a Project → add the same files → paste the system prompt.
- **Automation (Make / n8n / Zapier)** → feed `content_pack/content_pack.json` to the LLM
  node as context; it holds the same profile in machine-readable form.

## Step 2 — System prompt (ready to paste)
> You are my content assistant. You write in **my** voice for `[primary account]` and
> can adapt for `[secondary accounts]` when asked.
>
> **Voice:** `[tone descriptors]`. Captions average `[N]` characters for quick posts —
> match the length to the format. Core vocabulary leans: `[from voice_profile.md]`.
> Signature emojis: `[from voice_profile.md]` — use sparingly, never forced.
> Hashtags: `[rate]`. Identity themes over time: `[from bio history in voice_profile.md]`.
>
> **Taste / vibe:** my saved-music skews `[artists from saved_inspiration.md]` — use for
> reel/story audio suggestions.
>
> **Avoid:** the vibes in `topics_interests.md` under "not interested" and "see less".
>
> *(Template — fill the `[placeholders]` from your generated `content_pack/` files; the
> filled-in personal version stays local, outside this public repo.)*
>
> **Rules:** never invent facts about my life beyond what's in the knowledge files; when unsure,
> ask or leave a `[bracketed placeholder]`. Give 3 options unless I ask for one. Keep it real,
> not corporate.

## Step 3 — Reusable task prompts
- **Caption from a photo/idea:** "Here's what the post is about: `<idea>`. Give me 3 captions in
  my voice — one short, one medium, one reflective."
- **Batch ideation:** "Using `my_content_log.md` and `saved_inspiration.md`, propose 10 post
  ideas that fit my themes but that I haven't done yet."
- **Repurpose:** "Turn this IG caption into a tweet in my X voice (see `x_twitter.md`)."
- **Story prompts:** "Give me 5 story hooks/questions in my voice for this week."

## Step 4 — Cadence (from `audience_cadence.md`)
- Busiest posting day historically: **Monday**. Use it as the anchor for a weekly slot.
- Recommended starter rhythm: 1 feed post + 3–4 stories/week; draft on Sunday, publish Monday.
- Keep a running content calendar; feed completed posts back into the brain on the next export.

## Step 5 — Keep it fresh (the loop)
1. Every month or two, request new exports (Instagram, X, later TikTok).
2. Drop the new export folders in the local working folder (`SOCIAL_BRAIN_ROOT`,
   default `Downloads\Social media clone`).
3. From `automations/second-brain-social-media/scripts/`, run `refresh_second_brain.ps1`.
4. Re-upload the changed `content_pack/` files to your Project/GPT. Done.

## Notes / options
- **Publishing** is intentionally NOT automated here — drafts are generated for your review, and
  you post them yourself. If you later want auto-posting, that needs the Instagram Graph API
  (business/creator account) or a scheduler like Buffer/Later; say the word and we'll scope it.
- Everything stays local; nothing is sent anywhere except the LLM surface you choose to upload to.
