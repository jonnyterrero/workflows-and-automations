---
Title: Social Media Second Brain Layer
Type: Content Pipeline
Domain: Second Brain
Date: 2026-09-17
Keywords: social media, voice, instagram, content pack, obsidian
Summary: Points the chief-of-staff layer at the social-media pipeline — a sibling lobe that turns platform exports into a local voice pack without committing personal records.
---

## Context
- The Second Brain in this hub has two lobes:
  1. **Chief of staff** (`automations/second-brain-chief-of-staff/`) — planning, retrieval, weekly execution.
  2. **Social media** (`automations/second-brain-social-media/`) — Instagram/X export ingest, voice distillation, LLM wiring.
- Generated records (captions, likes, saves, follows) stay in a local working folder. This public repo holds only scripts and templates.

## Key Ideas
- Content generation must read `content_pack/voice_profile.md` before drafting.
- Avoid-signals in `topics_interests.md` are constraints, not suggestions.
- Publishing stays manual; this layer drafts and schedules, it does not post.
- Refresh after new platform exports: `automations/second-brain-social-media/scripts/refresh_second_brain.ps1`.

## Decisions
- Treat social-media as a sibling of chief-of-staff, not a nested GPT knowledge dump.
- Handoff caption/story/tweet work to the `draft-content` skill.
- Handoff repo-activity YouTube/blog work to `content-engine` / `content-production`.
- Never commit `content_pack/`, JSONL archives, or raw exports.

## Constraints
- Local data root defaults to `Downloads\Social media clone` unless `SOCIAL_BRAIN_ROOT` or `config.local.json` overrides it.
- Vault readable copy: `The Batcave/05 Jonnys HQ/Social Media Second Brain/`.
- Web LLM Projects (Claude / ChatGPT / Perplexity) need a manual re-upload after refresh.

## Open Questions
- When should TikTok export ingest land in `REGISTRY`?
- Should Make/n8n consume `content_pack.json` before any auto-posting is even considered?

## Next Actions
- After each export drop, run the refresh script and replace changed pack files in web Projects.
- When drafting social content, invoke `draft-content` instead of inventing a voice.
