# Handoff: research-analyst Claude skill

**Date:** 2026-08-17
**Status:** Packaging complete. Ready to upload to Claude.ai. Not yet live-tested in the dashboard.
**GitHub repo:** [jonnyterrero/workflows-and-automations](https://github.com/jonnyterrero/workflows-and-automations)
**In this repo:** `agent-team/skills/research-analyst/` (source of truth for laptop/desktop sync)

Use this file on desktop. Do not put it inside `research-analyst/` or it will get zipped into the skill.

**Desktop pull:**

```bash
cd /path/to/workflows-and-automations
git pull origin main
```

Then build the Claude upload zip (do not commit the zip; `*.zip` is gitignored):

```bash
cd agent-team
python scripts/build_skills.py
# output: dist/skills/research-analyst.zip
```

---

## Goal

Turn the research-analyst agent pack into a Claude dashboard skill with **top-down progressive disclosure**:

1. YAML metadata (name + description) loads first
2. `SKILL.md` is the orchestrator
3. One file from `references/` loads per pipeline step — not the whole folder

---

## What was broken

The file you pointed at:

`research-analyst/references.skill.md.zip`

was invalid for Claude upload:

- Files sat at the **zip root** (`SKILL.md` + `references/`)
- Claude requires the **skill folder** at the zip root: `research-analyst/SKILL.md`
- Zip name did not match the skill name
- `SKILL.md` was only a thin index, so Claude had no load-order rules

That broken zip was **deleted**.

---

## What is done

- Rewrote `research-analyst/SKILL.md` as the top-down orchestrator
- Kept all 10 reference files (content unchanged)
- Description is **180 characters** (Claude.ai limit is 200)
- `name: research-analyst` matches the folder name (kebab-case)
- Built a valid zip with folder-at-root structure

Verified zip contents:

```
research-analyst.zip
└── research-analyst/
    ├── SKILL.md
    └── references/
        ├── data-extraction-tables.md
        ├── lit-sweep.md
        ├── project-intel.md
        ├── project-research-intake.md
        ├── project-synthesis-next-actions.md
        ├── regulatory-brief.md
        ├── research-digest.md
        ├── research-synthesis-engine.md
        ├── source-validation-evidence.md
        └── tech-eval.md
```

---

## Paths (upload these)

**Upload this zip (preferred):**

`C:\Users\JTerr\OneDrive\Programming Projects\Skills for AI's\claude-agent-packs\_zips\research-analyst.zip`

**Duplicate copy (same bytes):**

`C:\Users\JTerr\OneDrive\Programming Projects\Skills for AI's\claude-agent-packs\research-analyst.zip`

**Editable source (keep clean — SKILL.md + references only):**

`C:\Users\JTerr\OneDrive\Programming Projects\Skills for AI's\claude-agent-packs\research-analyst\`

---

## Upload on desktop

1. Open Claude.ai (Pro / Max / Team / Enterprise; code execution must be on)
2. Settings → Customize → Skills
3. Upload skill → choose `_zips\research-analyst.zip`
4. Toggle **research-analyst** ON
5. Start a new chat and test (skills often do not attach mid-thread)

If upload fails, the usual causes are: zip has files at root instead of `research-analyst/`, folder name ≠ `name` field, missing `SKILL.md`, description > 200 chars, or zip too large. This zip is ~28 KB.

---

## How the skill is supposed to behave

Default pipeline (skip finished steps; never skip evidence grading):

1. Scope the question (`SKILL.md` only)
2. Query plan → `references/lit-sweep.md`
3. Intake sources → `references/project-research-intake.md`
4. Validate → `references/source-validation-evidence.md`
5. Extract tables → `references/data-extraction-tables.md`
6. Synthesize → `references/research-synthesis-engine.md`
   - If user pasted raw search output → `references/research-digest.md`
7. Next actions → `references/project-synthesis-next-actions.md`

Specialty lanes (replace the middle steps):

- FDA / SaMD / HIPAA → `regulatory-brief.md`
- Competitors / market → `project-intel.md`
- Tooling / stack choice → `tech-eval.md`

Every answer must split **Fact / Interpretation / Assumption / Unknown**, grade evidence A–D, and refuse invented citations.

---

## Test prompts

Use a fresh chat after the skill is toggled on:

1. `Do a focused lit sweep on wearable gut motility biosensors for GastroGuard. Grade evidence and separate fact from interpretation.`
2. `I pasted search results below. Digest them into a research note with grades and follow-up queries.`
3. `Is a dietary recommendation engine for IBS SaMD? Give a regulatory brief, informational only.`

Pass if Claude: loads the skill, does not dump all 10 refs, grades sources, and labels unknowns.

---

## If you edit on desktop, re-zip like this

Do **not** zip the contents of the folder. Zip the folder itself so the archive root is `research-analyst/`.

PowerShell:

```powershell
$pack = "C:\Users\JTerr\OneDrive\Programming Projects\Skills for AI's\claude-agent-packs"
$staging = Join-Path $env:TEMP "research-analyst-skill-pack"
$src = Join-Path $pack "research-analyst"
$zip = Join-Path $pack "_zips\research-analyst.zip"

if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $staging "research-analyst") | Out-Null
Copy-Item "$src\SKILL.md" "$staging\research-analyst\SKILL.md"
Copy-Item "$src\references" "$staging\research-analyst\references" -Recurse

if (Test-Path $zip) { Remove-Item $zip -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($staging, $zip)
Copy-Item $zip (Join-Path $pack "research-analyst.zip") -Force
Remove-Item $staging -Recurse -Force
```

Keep these out of the zip:

- this handoff file
- any `.zip` inside `research-analyst/`
- README files, notes, `.DS_Store`

After edits, check:

- `name` still `research-analyst`
- description still ≤ 200 characters
- all `references/*.md` links in `SKILL.md` still exist
- zip entries start with `research-analyst/` not `SKILL.md`

---

## Known leftovers / not done

These are real, not polish:

1. **Not tested in Claude.ai yet.** First desktop job is upload + the three prompts above.
2. **Reference files still say "Exact Sciences"** in intake / validation / next-actions. Product tags (`GASTROGUARD`, `MINDMAP`, `SKINTRACK`, etc.) are still hardcoded in lit-sweep, digest, intel, tech-eval. Fine if you want this as a personal skill; genericize if you want it reusable.
3. **Other agent packs in this repo were not converted.** Same zip-root bug likely exists if you made more `*.skill.md.zip` files.
4. **No Cursor/Claude Code install** of this skill was done (`~/.claude/skills/` or `.cursor/skills/`). Dashboard zip ≠ Claude Code skill dir. Copy the folder if you also want it in Claude Code.
5. **No git commit.** Nothing was committed.

---

## Constraints to keep

| Rule | Value |
|---|---|
| Skill name | `research-analyst` only (lowercase, hyphens) |
| Folder name | must match `name` |
| `SKILL.md` filename | case-sensitive `SKILL.md` |
| Description | ≤ 200 chars on Claude.ai |
| Zip root | `research-analyst/SKILL.md` |
| Load model | one reference at a time |
| Regulatory / clinical | informational only |

---

## Suggested next session (desktop)

1. Upload `_zips\research-analyst.zip` and toggle on
2. Run the three test prompts
3. If Claude loads every reference file, tighten the load-order section in `SKILL.md` and re-zip
4. Optional: strip "Exact Sciences" + unused project tags from references
5. Optional: repeat this packaging pattern for `bme-tutor` next (README listed it as install-order #1)

---

## Source of truth

- Orchestrator: `claude-agent-packs\research-analyst\SKILL.md`
- Details: `claude-agent-packs\research-analyst\references\`
- Ship artifact: `claude-agent-packs\_zips\research-analyst.zip`
- Pack README (install map for all 15 agents): `claude-agent-packs\README.md`
