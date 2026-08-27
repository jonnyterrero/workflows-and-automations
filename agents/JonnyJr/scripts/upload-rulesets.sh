#!/bin/bash
# Bash script to upload GitHub rulesets
# Usage: bash scripts/upload-rulesets.sh

set -e

TOKEN="${GITHUB_TOKEN:-}"
OWNER="${GITHUB_OWNER:-jonnyterrero}"
REPO="${GITHUB_REPO:-JonnyJr}"

if [ -z "$TOKEN" ]; then
    echo "❌ GITHUB_TOKEN environment variable not set"
    echo "💡 Set it with: export GITHUB_TOKEN='your_token'"
    echo "💡 Or run: gh auth login"
    exit 1
fi

BASE_URL="https://api.github.com/repos/$OWNER/$REPO/rulesets"

echo "📤 Uploading GitHub rulesets..."
echo ""

# Upload main branch protection
echo "1️⃣  Uploading main branch protection..."
if curl -s -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" \
  -d @.github/rulesets/main-branch-protection.json \
  "$BASE_URL" > /tmp/ruleset-response.json 2>&1; then
    RULESET_ID=$(jq -r '.id' /tmp/ruleset-response.json 2>/dev/null || echo "unknown")
    echo "   ✅ Main branch protection uploaded (ID: $RULESET_ID)"
else
    echo "   ❌ Failed to upload main branch protection"
    cat /tmp/ruleset-response.json
    echo ""
    echo "   💡 Ruleset may already exist. Check Settings → Rules → Rulesets"
fi

echo ""

# Upload workflow branches rules
echo "2️⃣  Uploading workflow branches rules..."
if curl -s -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" \
  -d @.github/rulesets/workflow-branches-rules.json \
  "$BASE_URL" > /tmp/ruleset-response.json 2>&1; then
    RULESET_ID=$(jq -r '.id' /tmp/ruleset-response.json 2>/dev/null || echo "unknown")
    echo "   ✅ Workflow branches rules uploaded (ID: $RULESET_ID)"
else
    echo "   ❌ Failed to upload workflow branches rules"
    cat /tmp/ruleset-response.json
    echo ""
    echo "   💡 Ruleset may already exist. Check Settings → Rules → Rulesets"
fi

echo ""
echo "✅ Upload complete!"
echo ""
echo "📋 Verify rulesets:"
echo "   https://github.com/$OWNER/$REPO/settings/rules"

