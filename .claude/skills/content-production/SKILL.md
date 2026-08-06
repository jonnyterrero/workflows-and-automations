---
name: content-production
description: Turns an approved content-engine draft into a rendered video using ElevenLabs narration, Higgsfield visuals, and ffmpeg assembly, plus upload-ready YouTube metadata.
metadata:
  version: "1.0.0"
  status: initial
  reviewed: "2026-07-30"
---

# Content Production

## Purpose
Take a script that `content-engine` already sourced and verified, and produce a finished video file plus upload-ready metadata. This skill spends money on every run; the workflow is built around that fact.

## Use this skill when
- A `content-engine` draft has been reviewed and approved for production.
- An existing rendered run needs re-assembly, a new aspect ratio, or corrected narration.

## Do not use this skill when
- The script has not been reviewed. Generation costs are per-call and non-refundable; never render an unapproved draft.
- The user only wants a script, titles, or thumbnails. That is `content-engine` plus `youtube-agent`.

## The division of labour
Asset generation runs through MCP tools driven by the model. Assembly is a deterministic script that calls no paid API. Keep that boundary: it means a failed render costs nothing to retry.

```
draft -> narration (ElevenLabs MCP) -> captions -> scene plan
      -> visuals (Higgsfield MCP)   -> manifest.json
      -> assemble_video.py (ffmpeg) -> final.mp4 + upload metadata
```

## Cost gate - read before any generation step
Before the first paid call in a run, state plainly: how many narration calls, how many video generations, the approximate total runtime being generated, and roughly what that costs on the user's plan. Then stop and get explicit confirmation.

Re-confirm if the plan grows mid-run. Never loop generation unattended, and never regenerate an asset that already exists on disk without saying so.

## Step 1: Set up the run
Work in `7-automations/content-engine/runs/<YYYY-MM-DD>/<slug>/`, alongside the draft that produced it. Create `assets/`. Record the source draft path in the manifest's `source_draft` field so the render is traceable to its script.

## Step 2: Narration
Use the ElevenLabs MCP. Feed it the spoken-word script only - strip section headers, visual directions, and citation markers, or the voice will read them aloud.

Save to `assets/narration.mp3`. Note the resulting duration; it drives everything downstream.

## Step 3: Captions
Produce `assets/captions.srt` (or `.ass` if you want styling baked in) timed to the narration. Two routes, following the split MoneyPrinterTurbo uses:

- **Fast**: derive timings from the TTS output directly.
- **Accurate**: transcribe the rendered narration with Whisper and use those timestamps.

Prefer the accurate route for anything long-form; drift is very visible.

## Step 4: Scene plan
Break the script into scenes, each with a duration and a visual prompt. Rules that matter:

- **Scene durations must sum to at least the narration length.** If they fall short, ffmpeg's `-shortest` truncates the voiceover and the video ends mid-sentence. `assemble_video.py --check` warns about this when ffprobe is available, but plan for it up front.
- Aim for 5-12s per scene. Longer reads as a slideshow; shorter burns generation budget for little gain.
- Each scene's prompt should serve the line being spoken over it. Record that intent in the scene's `covers` field.

## Step 5: Visuals
Use the Higgsfield MCP, one generation per scene, saving to `assets/scene-NN.mp4`. Record which model produced each clip in the scene's `source` field - you will want to know what worked.

This is the expensive step. Generate a single scene first and show it to the user before committing to the rest.

## Step 6: Manifest
Write `manifest.json`. See `templates/manifest.example.json` for the full shape.

Aspect presets: `16:9` (1920x1080), `9:16` (1080x1920), `1:1` (1080x1080).

Validate before rendering:

```bash
python3 .claude/skills/content-production/scripts/assemble_video.py <run>/manifest.json --check
```

## Step 7: Assemble
```bash
# inspect the exact ffmpeg commands without running them
python3 .claude/skills/content-production/scripts/assemble_video.py <run>/manifest.json --dry-run

# render
python3 .claude/skills/content-production/scripts/assemble_video.py <run>/manifest.json
```

Scene clip audio is dropped by design; narration is the voice and `audio.music` is an optional bed ducked to `music_gain_db` (default -22 dB). On failure the script keeps intermediates in `.work/` and tells you which stage broke.

## Step 8: Upload metadata
Write `upload-metadata.json` from `templates/upload-metadata.example.json`, drawing title, description, tags, and chapters from the `content-engine` draft rather than inventing them.

```bash
python3 .claude/skills/content-production/scripts/upload_youtube.py <run>/upload-metadata.json
```

That is a dry run. Uploading needs `--confirm`, an OAuth client, and the optional Google deps.

**The constraint that governs this step:** uploads from an API project that has not passed a YouTube compliance audit are locked to private, permanently, whatever `privacyStatus` you send. Private staging works fine and is genuinely useful - upload, review in Studio, publish by hand. Public automated publishing requires passing the audit first. Never tell the user a video will go live when it will not.

## Output contract
- Run directory with `assets/`, `manifest.json`, `upload-metadata.json`, `final.mp4`
- Scene table: id, duration, model used, what it covers
- Total runtime and narration-versus-video duration check
- Generation cost summary: calls made, per service
- Explicit statement of upload status and whether publishing is gated

## Quality gate
Ship only if: narration fits inside the scene total, captions stay in sync at the end of the video, the render plays with audio, and no unapproved script reached a paid call.

## Example triggers
- "Produce the MCP spec video from today's content-engine run."
- "Re-render that run at 9:16 for shorts."
- "Generate narration and one test scene so I can hear the voice."
