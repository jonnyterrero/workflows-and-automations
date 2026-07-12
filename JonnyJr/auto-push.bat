@echo off
REM Auto-push script for GitHub
REM Run this script to automatically commit and push changes

echo 🚀 Auto-push script starting...

REM Check if we're in a git repository
if not exist ".git" (
    echo ❌ Not in a git repository. Please run this from your project root.
    exit /b 1
)

REM Add all changes
echo 📁 Adding all changes...
git add .

REM Check if there are changes to commit
git status --porcelain > temp_status.txt
set /p status=<temp_status.txt
del temp_status.txt

if "%status%"=="" (
    echo ℹ️  No changes to commit.
    exit /b 0
)

REM Commit changes
echo 💾 Committing changes...
git commit -m "Auto-commit: %date% %time%"

if errorlevel 1 (
    echo ❌ Failed to commit changes.
    exit /b 1
)

REM Get current branch
for /f "tokens=*" %%i in ('git branch --show-current') do set currentBranch=%%i

REM Check if origin remote exists
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo ❌ No remote origin found. Please set up your GitHub repository:
    echo   git remote add origin https://github.com/yourusername/yourrepo.git
    echo   git push -u origin main
    exit /b 1
)

REM Push to GitHub
echo 🌐 Pushing to origin/%currentBranch%...
git push origin %currentBranch%

if errorlevel 1 (
    echo ❌ Failed to push to GitHub. Please check your connection and credentials.
    echo You may need to set up your GitHub remote:
    echo   git remote add origin https://github.com/yourusername/yourrepo.git
    echo   git push -u origin main
) else (
    echo ✅ Successfully pushed to GitHub!
)

echo 🎉 Auto-push script completed!
