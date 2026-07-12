@echo off
REM JonnyJr Bootstrap Script for Windows
REM Sets up the repository for development

echo 🚀 Bootstrapping JonnyJr repository...

REM Check if we're in a git repository
if not exist ".git" (
    echo ❌ Not in a git repository. Please run this from the project root.
    exit /b 1
)

REM Check for required tools
echo 🔍 Checking for required tools...

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 20+ from https://nodejs.org
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.10+ from https://python.org
    exit /b 1
)

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm not found. Please install Node.js which includes npm
    exit /b 1
)

echo ✅ All required tools found

REM Install dependencies
echo 📦 Installing dependencies...

REM Install root dependencies
npm install

REM Install TypeScript package dependencies
cd packages\ts
npm install
cd ..\..

REM Install Python dependencies
cd packages\py
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
cd ..\..

REM Set up environment
echo 🔧 Setting up environment...

if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env with your actual API keys
) else (
    echo ✅ .env file already exists
)

REM Run initial checks
echo 🧪 Running initial checks...

REM TypeScript checks
cd packages\ts
npm run typecheck
npm run lint
cd ..\..

REM Python checks
cd packages\py
call .venv\Scripts\activate
python -m pytest --version
cd ..\..

REM Markdown linting
npm run lint:md

echo 🎉 Bootstrap completed successfully!
echo.
echo Next steps:
echo 1. Edit .env with your API keys
echo 2. Run 'npm run test' to run all tests
echo 3. Run 'npm run build' to build the project
echo 4. Check out docs/USAGE.md for usage instructions
