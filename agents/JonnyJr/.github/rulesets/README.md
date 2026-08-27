# GitHub Rulesets for Branch Protection

This directory contains JSON ruleset files that can be uploaded to GitHub to protect your repository branches.

## Quick Start

**Use this file:** `main-branch-protection.json` (no status checks required)

If you want to require CI checks later, use: `main-branch-protection-with-checks.json`

## Available Rulesets

### 1. `main-branch-protection.json` ⭐ **Recommended**
**Protects:** `main` and `master` branches

**Rules:**
- ✅ Prevents branch deletion
- ✅ Prevents force pushes (non-fast-forward)
- ✅ Requires pull requests before merging
- ✅ Requires 1 approval
- ✅ Dismisses stale reviews
- ✅ Requires conversation resolution
- ❌ **No status checks** (you can add them later in the UI)

**Use this for:** Protecting your main branch without requiring CI checks

### 2. `main-branch-protection-with-checks.json`
**Same as above but includes:**
- ✅ Requires status checks to pass (check-rules)

**Use this for:** When you want to require CI checks to pass before merging

### 3. `workflow-branches-rules.json` - Workflow Branch Rules
**Protects:** `workflow/*` branches (e.g., `workflow/homework-help`)

**Rules:**
- ✅ Prevents accidental deletion
- ✅ Allows force pushes (for workflow updates)
- ✅ Allows updates from workflows

**Use this for:** AI helper workflow branches that need to be updated by GitHub Actions

### 4. `prevent-old-branch-pattern.json` - Prevent Old Branch Patterns (Optional)
**Prevents:** Creating branches with old timestamped patterns

**Rules:**
- ❌ Blocks creation of `ai/research-*`, `art-*`, `homework-*`, etc.
- ❌ Blocks updates to existing old branches

**Use this for:** Enforcing the new `workflow/*` naming convention

## How to Upload

### Option 1: GitHub Web UI (Easiest)

1. Go to: **Settings** → **Rules** → **Rulesets**
2. Click **New ruleset** → **Branch ruleset**
3. Copy and paste the JSON content from `main-branch-protection.json`
4. Adjust as needed
5. Click **Create**

### Option 2: PowerShell Script

```powershell
$env:GITHUB_TOKEN = "your_token_here"
powershell -ExecutionPolicy Bypass -File .\scripts\upload-rulesets.ps1
```

### Option 3: GitHub CLI

```bash
gh api repos/jonnyterrero/JonnyJr/rulesets \
  --method POST \
  --input .github/rulesets/main-branch-protection.json

gh api repos/jonnyterrero/JonnyJr/rulesets \
  --method POST \
  --input .github/rulesets/workflow-branches-rules.json
```

## Adding Status Checks Later

If you want to require CI checks after creating the ruleset:

1. Go to **Settings** → **Rules** → **Rulesets**
2. Click on your "Main Branch Protection" ruleset
3. Click **Edit**
4. Under **Status checks**, check **Require status checks to pass before merging**
5. Select the checks you want (e.g., `check-rules` from your Rules CI workflow)
6. Save

Or use the `main-branch-protection-with-checks.json` file which includes status checks.

## What Each Ruleset Does

### Main Branch Protection
- **Prevents**: Direct commits, force pushes, deletions
- **Requires**: Pull requests with approval
- **Allows**: Merging approved PRs only

### Workflow Branches
- **Prevents**: Accidental deletion
- **Allows**: Force pushes (for workflow updates)
- **Allows**: Automatic updates from GitHub Actions

## Troubleshooting

### "Required status checks cannot be empty"
- **Solution**: Use `main-branch-protection.json` (no status checks)
- Or add actual status checks that exist in your repository

### "Cannot push to branch"
- Check if ruleset is too restrictive
- Verify bypass actors are configured
- Check if PR requirements are blocking

### "Workflow can't push"
- Ensure workflow branches ruleset allows updates
- Check GitHub Actions has proper permissions
- Verify PAT has repo write access

### Status Check Names
GitHub uses the **job name** (not workflow name) as the status check name. Check your workflow files for job names like:
- `check-rules` (from rules-ci.yml)
- `build`
- `test`
- etc.

## Notes

- Rulesets work alongside (not instead of) branch protection rules
- More restrictive rules take precedence
- You can have multiple rulesets for different branch patterns
- Rulesets are evaluated in order (more specific first)
- You can add status checks later through the GitHub UI
