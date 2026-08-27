# Branch Protection Setup Guide

## Overview

This guide explains how to protect your `main` branch to ensure all changes go through pull requests and proper review.

## GitHub Branch Protection Rules

### Option 1: Using GitHub UI (Recommended)

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Branches**
3. Under "Branch protection rules", click **Add rule** or edit the rule for `main`
4. Configure the following settings:

#### Basic Settings:
- **Branch name pattern**: `main` (or `master` if that's your default)
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: **1** (or more if you want)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners (if you have CODEOWNERS file)

#### Status Checks:
- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Select required checks:
    - `Rules CI` (if you have linting/type checking)
    - `docs-ci` (if you have docs validation)
    - Any other CI workflows you want to require

#### Additional Settings:
- ✅ **Require conversation resolution before merging**
- ✅ **Do not allow bypassing the above settings**
- ✅ **Include administrators** (applies rules to you too)
- ✅ **Allow force pushes**: **Off** (recommended: never allow force pushes)
- ✅ **Allow deletions**: **Off** (prevents accidental deletion)

### Option 2: Using GitHub CLI

```bash
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Rules CI","docs-ci"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

### Option 3: Using GitHub API (via curl)

```bash
curl -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.github.com/repos/YOUR_USERNAME/JonnyJr/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["Rules CI", "docs-ci"]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews": true
    },
    "allow_force_pushes": false,
    "allow_deletions": false
  }'
```

## Recommended Protection Rules

### For Main Branch:
```yaml
Branch: main
Rules:
  - Require PR before merging: Yes
  - Required approvals: 1
  - Require status checks: Yes
    - Rules CI (type checking, linting)
    - docs-ci (documentation validation)
  - Require branches up to date: Yes
  - Require conversation resolution: Yes
  - Do not allow bypassing: Yes
  - Include administrators: Yes
  - Allow force pushes: No
  - Allow deletions: No
```

## Workflow Branches

All AI helper workflows now use consistent branch names:
- `workflow/homework-help` - Homework assistance results
- `workflow/ai-research` - General AI research
- `workflow/nightly-research` - Overnight research archives
- `workflow/art-inspiration` - Art project inspiration
- `workflow/project-assistant` - Personal project help
- `workflow/ai-research-pr` - Research with PR creation

These branches are updated (not recreated) each time a workflow runs, making it easier to:
- Track latest results per workflow type
- See history of changes
- Create PRs from these branches to main

## Setting Up CODEOWNERS (Optional)

Create `.github/CODEOWNERS` to automatically assign reviewers:

```
# Default owner
* @jonnyterrero

# Protect critical files
/.github/workflows/ @jonnyterrero
/scripts/ @jonnyterrero
```

## Testing Branch Protection

1. Make a change directly on `main` branch
2. Try to push: Should be blocked
3. Create a feature branch
4. Make changes and push
5. Create a PR: Should work
6. Try to merge without approval: Should be blocked
7. Approve the PR: Should allow merge

## Workflow Integration

All workflows now:
- Push to their dedicated workflow branches (not main)
- Create PRs from workflow branches to main
- Require your approval before merging to main
- Respect branch protection rules

## Benefits

✅ **Safety**: No accidental pushes to main
✅ **Review**: All changes go through PRs
✅ **Quality**: Status checks must pass
✅ **History**: Better git history and tracking
✅ **Control**: You decide when to merge AI-generated content

## Troubleshooting

### "Updates were rejected because the tip of your current branch is behind"
- This means someone else pushed to main
- Pull latest: `git pull origin main`
- Rebase or merge your changes

### "Required status check is missing"
- Wait for CI to complete
- Check Actions tab for workflow status
- Re-run failed workflows if needed

### "At least 1 approving review is required"
- You need to approve your own PR (if you enabled that)
- Or wait for required reviewer

### Cannot merge even after approval
- Check if branch is up to date
- Update branch from main first
- Ensure all status checks pass

