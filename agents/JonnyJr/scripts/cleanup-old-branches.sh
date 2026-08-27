#!/bin/bash
# Script to delete old workflow branches via GitHub CLI
# Run with: bash scripts/cleanup-old-branches.sh

echo "🧹 Cleaning up old workflow branches..."

# Old branches to delete
branches=(
    "ai/research"
    "ai/research-20251024-064106"
    "ai/research-20251024-064708"
    "ai/research-20251024-070349"
    "ai/research-20251024-072756"
    "ai/research-20251030-051605"
    "art-20251030-053249"
    "art-20251030-061114"
    "homework-20251030-062743"
    "homework-20251030-063645"
    "project-20251030-064939"
    "project-20251030-064952"
    "project-20251030-070208"
)

deleted=0
failed=0

for branch in "${branches[@]}"; do
    echo ""
    echo "🗑️  Attempting to delete: $branch"
    
    # Try using gh CLI
    if gh api repos/:owner/:repo/git/refs/heads/"$branch" -X DELETE 2>/dev/null; then
        echo "   ✅ Deleted: $branch"
        ((deleted++))
    else
        echo "   ❌ Failed to delete: $branch"
        echo "   💡 You may need to delete this manually via GitHub web UI"
        echo "   📍 https://github.com/jonnyterrero/JonnyJr/branches"
        ((failed++))
    fi
done

echo ""
echo "📊 Summary:"
echo "   Deleted: $deleted branches"
echo "   Failed: $failed branches"

if [ $failed -gt 0 ]; then
    echo ""
    echo "💡 To delete remaining branches manually:"
    echo "   1. Go to: https://github.com/jonnyterrero/JonnyJr/branches"
    echo "   2. Find each branch in the list"
    echo "   3. Click the trash icon to delete"
    echo "   4. Confirm deletion"
fi

