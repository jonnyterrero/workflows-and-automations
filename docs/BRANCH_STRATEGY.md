# Branch Strategy Guide

## Overview

All AI helper workflows now use consistent, reusable branches instead of creating new timestamped branches each run.

## Workflow Branches

Each workflow type has its own dedicated branch:

| Workflow | Branch Name | Purpose |
|----------|-------------|---------|
| Homework Help | `workflow/homework-help` | All homework assistance results |
| AI Research | `workflow/ai-research` | General research findings |
| Nightly Research | `workflow/nightly-research` | Overnight research archives |
| Art Inspiration | `workflow/art-inspiration` | Art project guidance |
| Project Assistant | `workflow/project-assistant` | Personal project help |
| AI Research & PR | `workflow/ai-research-pr` | Research with automatic PRs |

## How It Works

### Before (Old Behavior):
- Each workflow run created: `homework-20250115-143022`
- Each workflow run created: `research-20250115-143045`
- Result: Many branches, hard to track latest results

### After (New Behavior):
- All homework runs update: `workflow/homework-help`
- All research runs update: `workflow/ai-research`
- Result: One branch per workflow type, easy to track

## Benefits

✅ **Easier Tracking**: Always know where latest results are
✅ **Better History**: See evolution of research over time on same branch
✅ **Cleaner Repo**: Fewer branches to manage
✅ **PR Management**: One PR per workflow type, updated over time
✅ **Quick Access**: Check `workflow/homework-help` for latest homework help

## Usage

### Viewing Latest Results

```bash
# Check latest homework help
git checkout workflow/homework-help
cat school/MAP2302/HW1/README.md

# Check latest research
git checkout workflow/ai-research
cat RESEARCH.md

# Check latest nightly research
git checkout workflow/nightly-research
ls docs/nightly/
```

### Creating PRs

Each workflow branch can have an open PR to `main`:
1. Workflow updates its branch
2. PR is automatically updated (if exists)
3. You review and merge when ready
4. Branch stays open for next workflow run

### Manual Cleanup

If you want to start fresh on a workflow branch:

```bash
# Delete and recreate (local)
git branch -D workflow/homework-help
git checkout -b workflow/homework-help
git push --force origin workflow/homework-help
```

## Branch Protection

The `main` branch is protected (see `.github/BRANCH_PROTECTION.md`):
- ✅ Requires PR before merging
- ✅ Requires approval (even from yourself)
- ✅ Requires status checks to pass
- ✅ Prevents force pushes
- ✅ Prevents direct commits

## Workflow Behavior

### When Branch Doesn't Exist:
1. Workflow creates the branch
2. Commits changes
3. Pushes to remote

### When Branch Exists:
1. Workflow fetches latest
2. Checks out the branch
3. Adds new commit
4. Updates remote branch

### Force Push Safety:
- Uses `--force-with-lease` (safer)
- Falls back to `--force` if needed
- Prevents accidental overwrites

## Best Practices

1. **Review Before Merging**: Always review PRs before merging to main
2. **Keep PRs Open**: Let PRs stay open, they'll update automatically
3. **Regular Cleanup**: Periodically archive old research if needed
4. **Use Branch Names**: Reference branches by name in conversations

## Troubleshooting

### "Branch already exists locally"
```bash
git branch -D workflow/homework-help
git fetch origin
git checkout workflow/homework-help
```

### "Updates were rejected"
The workflow will automatically handle conflicts, but if needed:
```bash
git pull origin workflow/homework-help
# Resolve conflicts if any
git push origin workflow/homework-help
```

### Want to see all workflow branches
```bash
git branch -r | grep workflow/
```

## Integration with Main Branch Protection

Since `main` is protected:
- All changes must go through PRs
- Each workflow branch can have its own PR
- You control when to merge AI-generated content
- Better safety and review process

