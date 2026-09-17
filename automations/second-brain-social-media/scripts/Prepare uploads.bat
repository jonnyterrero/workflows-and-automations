@echo off
REM Double-click to prepare upload-ready second-brain chunks from this folder.
cd /d "%~dp0"
python "%~dp0prepare_uploads.py" %*
echo.
echo Done. See the _prepared_uploads folder and UPLOAD_INDEX.md.
pause
