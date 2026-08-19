# PowerShell script to delete old workflow branches via GitHub CLI
# Run with: powershell -ExecutionPolicy Bypass -File .\scripts\cleanup-old-branches.ps1

Write-Host "🧹 Cleaning up old workflow branches..." -ForegroundColor Green

# Old branches to delete
$oldBranches = @(
    "ai/research",
    "ai/research-20251024-064106",
    "ai/research-20251024-064708",
    "ai/research-20251024-070349",
    "ai/research-20251024-072756",
    "ai/research-20251030-051605",
    "art-20251030-053249",
    "art-20251030-061114",
    "homework-20251030-062743",
    "homework-20251030-063645",
    "project-20251030-064939",
    "project-20251030-064952",
    "project-20251030-070208"
)

$deleted = 0
$failed = 0

foreach ($branch in $oldBranches) {
    Write-Host "`n🗑️  Attempting to delete: $branch" -ForegroundColor Yellow
    
    # Try using gh CLI
    $result = gh api repos/:owner/:repo/git/refs/heads/$branch -X DELETE 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Deleted: $branch" -ForegroundColor Green
        $deleted++
    } else {
        Write-Host "   ❌ Failed to delete: $branch" -ForegroundColor Red
        Write-Host "   💡 You may need to delete this manually via GitHub web UI" -ForegroundColor Cyan
        Write-Host "   📍 https://github.com/jonnyterrero/JonnyJr/branches" -ForegroundColor Cyan
        $failed++
    }
}

Write-Host "`n📊 Summary:" -ForegroundColor Green
Write-Host "   Deleted: $deleted branches" -ForegroundColor Green
Write-Host "   Failed: $failed branches" -ForegroundColor $(if ($failed -gt 0) { "Yellow" } else { "Green" })

if ($failed -gt 0) {
    Write-Host "`n💡 To delete remaining branches manually:" -ForegroundColor Cyan
    Write-Host "   1. Go to: https://github.com/jonnyterrero/JonnyJr/branches" -ForegroundColor Cyan
    Write-Host "   2. Find each branch in the list" -ForegroundColor Cyan
    Write-Host "   3. Click the trash icon to delete" -ForegroundColor Cyan
    Write-Host "   4. Confirm deletion" -ForegroundColor Cyan
}

