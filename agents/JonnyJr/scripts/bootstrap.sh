#!/bin/bash

# JonnyJr Bootstrap Script
# Sets up the repository for development

set -e

echo "🚀 Bootstrapping JonnyJr repository..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from the project root."
    exit 1
fi

# Check for required tools
echo "🔍 Checking for required tools..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 20+ from https://nodejs.org"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.10+ from https://python.org"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js which includes npm"
    exit 1
fi

echo "✅ All required tools found"

# Install dependencies
echo "📦 Installing dependencies..."

# Install root dependencies
npm install

# Install TypeScript package dependencies
cd packages/ts
npm install
cd ../..

# Install Python dependencies
cd packages/py
python3 -m venv .venv
source .venv/bin/activate || .venv/Scripts/activate
pip install -r requirements.txt
cd ../..

# Set up environment
echo "🔧 Setting up environment..."

if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your actual API keys"
else
    echo "✅ .env file already exists"
fi

# Run initial checks
echo "🧪 Running initial checks..."

# TypeScript checks
cd packages/ts
npm run typecheck
npm run lint
cd ../..

# Python checks
cd packages/py
source .venv/bin/activate || .venv/Scripts/activate
python -m pytest --version
cd ../..

# Markdown linting
npm run lint:md

echo "🎉 Bootstrap completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Run 'npm run test' to run all tests"
echo "3. Run 'npm run build' to build the project"
echo "4. Check out docs/USAGE.md for usage instructions"
