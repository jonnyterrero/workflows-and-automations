# refresh_second_brain.ps1
# One command to refresh the Social Media Second Brain after dropping in new exports:
#   1. Re-normalize raw exports        (build_second_brain.py)
#   2. Re-distill the content pack     (build_content_pack.py)
#   3. Re-chunk zips for web LLMs      (prepare_uploads.py)
#   4. Sync markdown into the Obsidian vault
#
# Scripts live in this repo. Data lives in SOCIAL_BRAIN_ROOT (never committed).
# Usage:  .\refresh_second_brain.ps1    (or double-click "Refresh second brain.bat")

$ErrorActionPreference = "Stop"
$Scripts = $PSScriptRoot
$Layer = Split-Path $Scripts -Parent

function Read-LocalConfig {
    $cfgPath = Join-Path $Layer "config.local.json"
    if (Test-Path $cfgPath) {
        return Get-Content $cfgPath -Raw | ConvertFrom-Json
    }
    return $null
}

$cfg = Read-LocalConfig
if (-not $env:SOCIAL_BRAIN_ROOT) {
    if ($cfg -and $cfg.data_root) {
        $env:SOCIAL_BRAIN_ROOT = $cfg.data_root
    } else {
        $env:SOCIAL_BRAIN_ROOT = "C:\Users\JTerr\Downloads\Social media clone"
    }
}
$DataRoot = $env:SOCIAL_BRAIN_ROOT

if ($env:SOCIAL_BRAIN_VAULT) {
    $Vault = $env:SOCIAL_BRAIN_VAULT
} elseif ($cfg -and $cfg.vault) {
    $Vault = $cfg.vault
} else {
    $Vault = "C:\Users\JTerr\OneDrive\Programming Projects\Heartwire\heartwire\The Batcave\05 Jonnys HQ\Social Media Second Brain"
}

if (-not (Test-Path $DataRoot)) {
    throw "Data folder not found: $DataRoot`nSet SOCIAL_BRAIN_ROOT or copy config.example.json to config.local.json."
}

Set-Location $DataRoot
Write-Host "Data root: $DataRoot" -ForegroundColor DarkGray
Write-Host "Vault:     $Vault" -ForegroundColor DarkGray

Write-Host "`n[1/4] Re-normalizing raw exports (build_second_brain.py)..." -ForegroundColor Cyan
python (Join-Path $Scripts "build_second_brain.py")
if ($LASTEXITCODE -ne 0) { throw "build_second_brain.py failed (exit $LASTEXITCODE)" }

Write-Host "`n[2/4] Rebuilding content pack (build_content_pack.py)..." -ForegroundColor Cyan
python (Join-Path $Scripts "build_content_pack.py")
if ($LASTEXITCODE -ne 0) { throw "build_content_pack.py failed (exit $LASTEXITCODE)" }

Write-Host "`n[3/4] Re-chunking upload zips (prepare_uploads.py)..." -ForegroundColor Cyan
python (Join-Path $Scripts "prepare_uploads.py") --root $DataRoot
if ($LASTEXITCODE -ne 0) { throw "prepare_uploads.py failed (exit $LASTEXITCODE)" }

Write-Host "`n[4/4] Syncing markdown into Obsidian vault..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path `
    "$Vault\Content Pack", `
    "$Vault\Archive Tables\jxnnys.wrld", `
    "$Vault\Archive Tables\juicedupjonnyy" | Out-Null

Copy-Item "$DataRoot\content_pack\*.md" "$Vault\Content Pack\" -Force
foreach ($account in @("jxnnys.wrld", "juicedupjonnyy")) {
    $src = Join-Path $DataRoot "$account\markdown"
    if (-not (Test-Path $src)) {
        $src = Join-Path $DataRoot "second-brain-instagram\$account\markdown"
    }
    if (Test-Path $src) {
        Copy-Item "$src\*.md" "$Vault\Archive Tables\$account\" -Force
    }
}
Copy-Item (Join-Path $Layer "docs\AUTOMATED_CONTENT_WORKFLOW.md") "$Vault\" -Force
Copy-Item (Join-Path $Layer "docs\WIRE_INTO_LLMS.md") "$Vault\" -Force

$count = (Get-ChildItem $Vault -Recurse -File -Filter *.md).Count
Write-Host "`nDone. $count markdown files in vault: $Vault" -ForegroundColor Green
Write-Host @"

Local agents (Cursor / Claude Code / Codex) pick up the refresh automatically.
Manual step for web LLMs (see docs\WIRE_INTO_LLMS.md):
  - Claude Project / ChatGPT Project / Perplexity Space -> replace the changed
    content_pack\ files (usually my_content_log, voice_profile, audience_cadence)
"@
