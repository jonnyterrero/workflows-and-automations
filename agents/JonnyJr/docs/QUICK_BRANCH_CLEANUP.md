# Quick Branch Cleanup Guide

## Fastest Way to Delete Old Branches

Since repository rules prevent automatic deletion, use the GitHub web UI:

### Step-by-Step:

1. **Go to Branches Page**:
   - Visit: https://github.com/jonnyterrero/JonnyJr/branches
   - Or: Your Repo → Click "branches" link (shows branch count)

2. **Delete Each Branch**:
   - Find the branch in the list
   - Click the **🗑️ trash icon** on the right
   - Confirm deletion

3. **Bulk Delete** (if available):
   - Select multiple branches with checkboxes
   - Click "Delete" button

### Branches to Delete:

**All of these should be deleted** (they're replaced by `workflow/*` branches):

```
ai/research
ai/research-20251024-064106
ai/research-20251024-064708
ai/research-20251024-070349
ai/research-20251024-072756
ai/research-20251030-051605
art-20251030-053249
art-20251030-061114
homework-20251030-062743
homework-20251030-063645
project-20251030-064939
project-20251030-064952
project-20251030-070208
```

**Keep these:**
- `main` (always keep)
- `workflow/*` branches (new strategy - will be created when workflows run)

### Why Can't I Delete via Git?

Repository rulesets protect branches from deletion via `git push --delete`. This is actually a good thing - it prevents accidental deletion. The web UI allows you to override this for cleanup.

### After Cleanup

Once deleted, your branch list will be much cleaner, showing only:
- `main` branch
- `workflow/*` branches (as workflows run)

This makes it much easier to find and manage your AI helper outputs!

