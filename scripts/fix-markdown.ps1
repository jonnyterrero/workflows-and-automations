# PowerShell script to fix markdown files
# Run with: powershell -ExecutionPolicy Bypass -File .\scripts\fix-markdown.ps1

Write-Host "Fixing markdown files..." -ForegroundColor Green

# Try to run markdownlint if available
if (Get-Command markdownlint -ErrorAction SilentlyContinue) {
    markdownlint '**/*.md' --ignore node_modules --ignore dist --fix
    Write-Host "✅ Auto-fixed markdown files" -ForegroundColor Green
} elseif (Test-Path "node_modules\.bin\markdownlint.cmd") {
    & "node_modules\.bin\markdownlint.cmd" '**/*.md' --ignore node_modules --ignore dist --fix
    Write-Host "✅ Auto-fixed markdown files" -ForegroundColor Green
} else {
    Write-Host "⚠️  markdownlint-cli not found. Run: npm install" -ForegroundColor Yellow
}

Write-Host "Done!" -ForegroundColor Green

