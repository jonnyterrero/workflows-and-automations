#!/bin/bash
# Script to fix common markdownlint issues
# This can be run manually or integrated into CI

echo "Fixing markdown files..."

# Fix markdown files using markdownlint-cli if available
if command -v markdownlint &> /dev/null; then
    markdownlint '**/*.md' --ignore node_modules --ignore dist --fix
    echo "✅ Auto-fixed markdown files"
else
    echo "⚠️  markdownlint-cli not found. Install with: npm install -g markdownlint-cli"
fi

echo "Done!"

