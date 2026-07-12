# Cleanup Old Workflow Branches

## Issue

Repository rules are preventing automatic deletion of old branches via `git push --delete`. These branches need to be deleted manually through the GitHub web UI.

## Old Branches to Delete

The following branches are old timestamped branches that should be deleted (they're being replaced by the new `workflow/*` branch strategy):

### AI Research Branches:
- `ai/research` (old format)
- `ai/research-20251024-064106`
- `ai/research-20251024-064708`
- `ai/research-20251024-070349`
- `ai/research-20251024-072756`
- `ai/research-20251030-051605`

### Art Inspiration Branches:
- `art-20251030-053249`
- `art-20251030-061114`

### Homework Help Branches:
- `homework-20251030-062743`
- `homework-20251030-063645`

### Project Assistant Branches:
- `project-20251030-064939`
- `project-20251030-064952`
- `project-20251030-070208`

## How to Delete (Recommended)

### Option 1: Via GitHub Web UI (Easiest)

1. Go to: **https://github.com/jonnyterrero/JonnyJr/branches**
2. Find each branch in the list
3. Click the **🗑️ trash icon** next to each branch
4. Confirm deletion

### Option 2: Using GitHub CLI

If you have `gh` CLI installed:

```bash
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup-old-branches.ps1

# Linux/Mac
bash scripts/cleanup-old-branches.sh
```

Or manually with `gh`:

```bash
gh api repos/jonnyterrero/JonnyJr/git/refs/heads/ai/research -X DELETE
gh api repos/jonnyterrero/JonnyJr/git/refs/heads/ai/research-20251024-064106 -X DELETE
# ... repeat for each branch
```

### Option 3: Bulk Delete Script

Run the cleanup script:

```powershell
# PowerShell
.\scripts\cleanup-old-branches.ps1
```

## Why Delete These?

- **Old Strategy**: These used timestamped branch names (e.g., `homework-20251030-062743`)
- **New Strategy**: Now using consistent `workflow/*` branches (e.g., `workflow/homework-help`)
- **Clutter**: Too many old branches make it hard to find current work
- **Cleanup**: Keep repository organized and easier to navigate

## After Cleanup

Once deleted, you'll only have:
- `main` (protected branch)
- `workflow/homework-help` (when first workflow runs)
- `workflow/ai-research` (when first workflow runs)
- `workflow/nightly-research` (when first workflow runs)
- `workflow/art-inspiration` (when first workflow runs)
- `workflow/project-assistant` (when first workflow runs)
- `workflow/ai-research-pr` (when first workflow runs)

Much cleaner! 🎉

## Note

If you get repository rule violations, you may need to:
1. Temporarily adjust branch protection rules
2. Delete branches via web UI (bypasses some restrictions)
3. Wait for branches to auto-delete if they have auto-deletion enabled

