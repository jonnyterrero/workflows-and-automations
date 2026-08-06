# Content Production - setup and operation

Turns an approved `content-engine` draft into a rendered video and upload-ready metadata.

`content-engine` decides *what* to make and sources it. `content-production` makes it. `youtube-agent` owns packaging discipline for both.

## One-time setup

### 1. Higgsfield MCP (visuals)

Hosted, OAuth, no API key:

```bash
claude mcp add --transport http --scope user higgsfield https://mcp.higgsfield.ai/mcp
```

First use opens a browser to sign in. Verify with `claude mcp list` or `/mcp`. Gives ~30 image and video models (Soul, Cinema Studio, Kling, Veo, Minimax Hailuo, Seedream, Flux). Works in Cursor via the same URL in its MCP settings.

### 2. ElevenLabs MCP (voice)

Official server, runs locally, needs a key:

```bash
claude mcp add elevenlabs --scope user -- uvx elevenlabs-mcp
```

Put `ELEVENLABS_API_KEY` in your shell environment. If you would rather scope it to this repo, add it to `.mcp.json` with env substitution, matching the existing `perplexity` entry:

```json
"elevenlabs": {
  "command": "uvx",
  "args": ["elevenlabs-mcp"],
  "env": { "ELEVENLABS_API_KEY": "${ELEVENLABS_API_KEY}" }
}
```

Never the literal key. `CLAUDE.md` forbids it and `.mcp.json` is committed.

### 3. ffmpeg (assembly)

```bash
# macOS
brew install ffmpeg
# Debian/Ubuntu
sudo apt install ffmpeg
# Windows
winget install Gyan.FFmpeg
```

`ffprobe` ships with it and enables the narration-length check. Assembly needs nothing else - the script is stdlib only.

### 4. YouTube upload (optional, and constrained)

```bash
uv pip install google-api-python-client google-auth-oauthlib
```

In Google Cloud Console: enable **YouTube Data API v3**, create an OAuth client of type **Desktop app**, download the JSON, and keep it outside the repo.

## The upload constraint

Worth being blunt about, because it determines what "automated" can mean here:

> Uploads from an API project that has not passed a compliance audit are locked to **private** - permanently, regardless of the `privacyStatus` you send. This applies to unverified projects created after 28 July 2020.

Lifting it means submitting the [YouTube API Services Audit and Quota Extension Form](https://support.google.com/youtube/contact/yt_api_form) and passing a review of your business and API client.

Until then the workable pattern is: **render and upload as private, review in YouTube Studio, publish by hand.** Everything upstream of publishing automates fully.

Quota: 10,000 units/day by default. `videos.insert` has historically cost ~1600 units (about 6 uploads/day); Google has reduced this and there is now a separate uploads bucket. Published figures contradict each other - check the Quota Calculator for your own project rather than trusting any number, including this one.

## Running a production

```bash
RUN=7-automations/content-engine/runs/2026-07-30/mcp-spec

# 1. validate the manifest and assets
python3 .claude/skills/content-production/scripts/assemble_video.py $RUN/manifest.json --check

# 2. inspect the ffmpeg commands without running them
python3 .claude/skills/content-production/scripts/assemble_video.py $RUN/manifest.json --dry-run

# 3. render
python3 .claude/skills/content-production/scripts/assemble_video.py $RUN/manifest.json

# 4. upload metadata dry run
python3 .claude/skills/content-production/scripts/upload_youtube.py $RUN/upload-metadata.json

# 5. upload as private
python3 .claude/skills/content-production/scripts/upload_youtube.py $RUN/upload-metadata.json \
  --client-secrets ~/.config/youtube/client_secret.json --confirm
```

Exit codes for `assemble_video.py`: `0` ok, `1` bad manifest or missing assets, `3` ffmpeg absent, `4` ffmpeg failed (intermediates kept in `.work/`).

## Run layout

```
7-automations/content-engine/runs/<date>/<slug>/
├── manifest.json              # assembly plan (committed)
├── upload-metadata.json       # YouTube metadata (committed)
├── assets/                    # narration, clips, captions (gitignored)
├── .work/                     # ffmpeg intermediates (gitignored, auto-removed)
└── final.mp4                  # render (gitignored)
```

Manifests and metadata are committed because they are small and describe the run. Media is gitignored - do not put video blobs in git.

## Where the design came from

Patterns taken from the references, with what each contributed:

| Source | Borrowed |
|--------|----------|
| [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | Six-stage pipeline shape; 9:16 / 16:9 presets; fast-vs-Whisper caption split; normalize-then-concat assembly |
| [AI-Content-Studio](https://github.com/naqashafzal/AI-Content-Studio) | Styled caption burn-in; SEO metadata and chapters as a distinct stage; direct Data API publishing |
| [awesome-faceless](https://github.com/sasharun/awesome-faceless) | ElevenLabs as hero voice; separating B-roll generation from editing |
| [github.com/topics/video-generator](https://github.com/topics/video-generator) | Modular stage separation; platform-specific aspect handling |

Deliberate divergences: no GUI, no bundled stock-footage scraper, and no unattended publish loop. Generation is gated behind explicit confirmation because every call costs money, and publishing is gated because YouTube gates it.

## Testing

```bash
python3 .claude/skills/content-production/scripts/test_assemble_video.py
```

Covers manifest validation, duration accounting, ffmpeg command construction for both aspect ratios, audio mixing with and without a music bed, subtitle filter selection and escaping, the command plan shape, and CLI behaviour without ffmpeg installed.

ffmpeg execution itself is not tested - the commands are asserted instead, so the suite runs anywhere. Verify a real render once locally after installing ffmpeg.
