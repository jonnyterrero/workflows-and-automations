# Quick Setup: Branch Protection

## 1. Set Up Branch Protection (5 minutes)

### Via GitHub Web UI:

1. Go to: `https://github.com/YOUR_USERNAME/JonnyJr/settings/branches`
2. Under "Branch protection rules", click **Add rule**
3. Branch name pattern: `main`
4. Check these boxes:
   - ✅ **Require a pull request before merging**
     - ✅ Require approvals: **1**
     - ✅ Dismiss stale reviews: **Yes**
   - ✅ **Require status checks to pass before merging**
     - ✅ Require branches to be up to date: **Yes**
     - Select: `Rules CI` (if available)
   - ✅ **Require conversation resolution before merging**
   - ✅ **Do not allow bypassing the above settings**
   - ✅ **Include administrators**
   - ❌ **Allow force pushes**: Unchecked
   - ❌ **Allow deletions**: Unchecked
5. Click **Create**

### Verify It Works:
```bash
# Try to push directly to main (should fail)
git checkout main
git commit --allow-empty -m "test"
git push origin main
# Should get: "remote: error: GH006: Protected branch update failed"
```

## 2. Workflow Branches Are Ready

All workflows now use consistent branches:
- `workflow/homework-help` - Homework results
- `workflow/ai-research` - Research findings  
- `workflow/nightly-research` - Nightly archives
- `workflow/art-inspiration` - Art projects
- `workflow/project-assistant` - Project help
- `workflow/ai-research-pr` - Research with PRs

**Each workflow:**
- Updates its own branch (not main)
- Creates/updates a PR automatically
- Requires your approval to merge

## 3. How It Works Now

### When You Run a Workflow:
1. Workflow runs on its dedicated branch
2. Commits results to that branch
3. Creates PR if new, updates PR if exists
4. PR appears in your repository
5. You review and approve
6. Merge to main when ready

### Benefits:
✅ **Main is protected** - No accidental commits
✅ **All changes reviewed** - PRs required
✅ **Consistent branches** - Easy to find latest results
✅ **PR history** - See all AI helper outputs in one place

## 4. Workflow Branch Overview

| Branch | Latest Results | Open PR? |
|--------|---------------|----------|
| `workflow/homework-help` | Latest homework help | Auto-created/updated |
| `workflow/ai-research` | Latest research | Manual PR creation |
| `workflow/nightly-research` | Latest nightly archive | Manual PR creation |
| `workflow/art-inspiration` | Latest art help | Auto-created/updated |
| `workflow/project-assistant` | Latest project help | Auto-created/updated |
| `workflow/ai-research-pr` | Latest research with PR | Auto-created/updated |

## 5. Next Steps

After setting up branch protection:
1. Run any workflow (e.g., Homework Help)
2. Check for PR creation
3. Review the PR
4. Approve and merge when satisfied
5. Next workflow run updates the same branch and PR

## Need Help?

See full documentation:
- `.github/BRANCH_PROTECTION.md` - Detailed protection rules
- `docs/BRANCH_STRATEGY.md` - Branch strategy explanation

