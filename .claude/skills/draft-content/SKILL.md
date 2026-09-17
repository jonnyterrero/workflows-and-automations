---
name: draft-content
description: Draft Instagram captions, story hooks, tweets, and post ideas in Jonny's personal voice using the Social Media Second Brain. Use when the user asks for social media content, captions, post ideas, story prompts, tweets, or anything in my voice for Instagram or X.
---

# Draft Content (personal voice)

Companion to `content-engine` (repo-activity YouTube/blog) and
`content-production` (narration + assembly). This skill writes **personal IG/X**
in the operator's voice. Do not invent a voice; load the generated pack.

## Context loading (always do this first)

Working folder (exports + generated pack), first match:

1. `$SOCIAL_BRAIN_ROOT`
2. `automations/second-brain-social-media/config.local.json` → `data_root`
3. `C:\Users\JTerr\Downloads\Social media clone`

Read from `<data_root>/content_pack/`:

1. `voice_profile.md` — always (tone, vocabulary, emoji set, caption lengths)
2. Then, based on the task:
   - Captions / posts → `my_content_log.md` (what already exists)
   - Ideation → `saved_inspiration.md` + `topics_interests.md`
   - Scheduling → `audience_cadence.md`
   - Tweets / X → `x_twitter.md`
   - Second account → the `*_reference.md` file in the pack

For deep factual lookups (e.g. "have I ever posted about X?"), query the JSONL at
`<data_root>/<account>/normalized/` instead of guessing.

If the pack is missing, tell the user to run
`automations/second-brain-social-media/scripts/refresh_second_brain.ps1`.

## Voice rules

- Match `voice_profile.md`. Not corporate.
- Quick captions follow the pack's average length; reflective ones can run long.
- Hashtags: almost never unless the pack shows otherwise.
- Emojis: from the profile's signature set, sparingly, never forced.
- Respect avoid-signals under "not interested" / "see less" in `topics_interests.md`.
- **Never invent facts about the operator's life.** When unsure, leave a `[bracketed placeholder]` or ask.

## Output format

- Give 3 options unless asked for one: one short, one medium, one reflective.
- For story prompts: 5 hooks/questions.
- For audio suggestions: pull from the saved-music taste in `saved_inspiration.md`.
- Default account is the primary in the pack; adapt for the secondary or X only when asked.

## Cadence

Use `audience_cadence.md`. Starter rhythm if the pack agrees: 1 feed post + 3–4
stories/week. Publishing is manual — output drafts for review, never auto-post.

## Related

- Pipeline: `automations/second-brain-social-media/`
- Planning layer: `automations/second-brain-chief-of-staff/`
- Wiring web LLMs: `automations/second-brain-social-media/docs/WIRE_INTO_LLMS.md`
