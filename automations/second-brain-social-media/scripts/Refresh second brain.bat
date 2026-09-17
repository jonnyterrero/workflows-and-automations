@echo off
REM Double-click to refresh the entire Social Media Second Brain
REM (rebuild archive + content pack + upload zips, then sync to Obsidian vault).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0refresh_second_brain.ps1"
pause
