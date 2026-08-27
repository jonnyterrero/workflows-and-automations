# PowerShell script to upload GitHub rulesets
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\upload-rulesets.ps1

param(
    [string]$Token = $env:GITHUB_TOKEN,
    [string]$Owner = "jonnyterrero",
    [string]$Repo = "JonnyJr"
)

if (-not $Token) {
    Write-Host "❌ GITHUB_TOKEN environment variable not set" -ForegroundColor Red
    Write-Host "💡 Set it with: `$env:GITHUB_TOKEN = 'your_token'" -ForegroundColor Yellow
    Write-Host "💡 Or run: gh auth login" -ForegroundColor Yellow
    exit 1
}

$baseUrl = "https://api.github.com/repos/$Owner/$Repo/rulesets"
$headers = @{
    "Accept" = "application/vnd.github+json"
    "Authorization" = "Bearer $Token"
    "X-GitHub-Api-Version" = "2022-11-28"
}

Write-Host "📤 Uploading GitHub rulesets..." -ForegroundColor Green
Write-Host ""

# Upload main branch protection
Write-Host "1️⃣  Uploading main branch protection..." -ForegroundColor Cyan
$mainRules = Get-Content ".github\rulesets\main-branch-protection.json" -Raw -ErrorAction Stop
try {
    $response = Invoke-RestMethod -Uri $baseUrl -Method POST -Headers $headers -Body $mainRules -ContentType "application/json"
    Write-Host "   ✅ Main branch protection uploaded (ID: $($response.id))" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "   💡 Ruleset may already exist. Check Settings → Rules → Rulesets" -ForegroundColor Yellow
    }
}

Write-Host ""

# Upload workflow branches rules
Write-Host "2️⃣  Uploading workflow branches rules..." -ForegroundColor Cyan
$workflowRules = Get-Content ".github\rulesets\workflow-branches-rules.json" -Raw -ErrorAction Stop
try {
    $response = Invoke-RestMethod -Uri $baseUrl -Method POST -Headers $headers -Body $workflowRules -ContentType "application/json"
    Write-Host "   ✅ Workflow branches rules uploaded (ID: $($response.id))" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "   💡 Ruleset may already exist. Check Settings → Rules → Rulesets" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Upload complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Verify rulesets:" -ForegroundColor Cyan
Write-Host "   https://github.com/$Owner/$Repo/settings/rules" -ForegroundColor Yellow

