# GitHub Rulesets Setup Instructions

## Overview

These JSON files can be uploaded to GitHub to protect your repository and configure rules for AI helper workflows.

## Files

1. **`main-branch-protection.json`** - Protects main branch (requires PRs, approvals)
2. **`workflow-branches-rules.json`** - Allows workflow/* branches to be updated by GitHub Actions
3. **`prevent-old-branch-pattern.json`** - Prevents creating old timestamped branch patterns

## How to Upload

### Method 1: GitHub Web UI (Easiest)

1. Go to your repository: **https://github.com/jonnyterrero/JonnyJr**
2. Navigate to: **Settings** → **Rules** → **Rulesets**
3. Click **New ruleset** → **Branch ruleset**
4. For each JSON file:
   - Copy the entire contents
   - Paste into the ruleset editor
   - Click **Create**

### Method 2: GitHub CLI

```bash
# Install GitHub CLI if needed: https://cli.github.com/

# Authenticate
gh auth login

# Upload main branch protection
gh api repos/jonnyterrero/JonnyJr/rulesets \
  --method POST \
  --input .github/rulesets/main-branch-protection.json

# Upload workflow branches rules
gh api repos/jonnyterrero/JonnyJr/rulesets \
  --method POST \
  --input .github/rulesets/workflow-branches-rules.json

# Upload old branch pattern prevention (optional)
gh api repos/jonnyterrero/JonnyJr/rulesets \
  --method POST \
  --input .github/rulesets/prevent-old-branch-pattern.json
```

### Method 3: Direct API (PowerShell)

```powershell
# Set your token
$token = "your_github_pat_token"
$headers = @{
    "Accept" = "application/vnd.github+json"
    "Authorization" = "Bearer $token"
    "X-GitHub-Api-Version" = "2022-11-28"
}

# Upload main branch protection
$mainRules = Get-Content .github\rulesets\main-branch-protection.json -Raw
Invoke-RestMethod -Uri "https://api.github.com/repos/jonnyterrero/JonnyJr/rulesets" `
    -Method POST -Headers $headers -Body $mainRules -ContentType "application/json"

# Upload workflow branches
$workflowRules = Get-Content .github\rulesets\workflow-branches-rules.json -Raw
Invoke-RestMethod -Uri "https://api.github.com/repos/jonnyterrero/JonnyJr/rulesets" `
    -Method POST -Headers $headers -Body $workflowRules -ContentType "application/json"
```

## What Each Ruleset Does

### 1. Main Branch Protection

**Protects:** `main` and `master` branches

**Rules:**
- ❌ **Blocks deletion** - Cannot delete main branch
- ❌ **Blocks force pushes** - No non-fast-forward pushes
- ✅ **Requires PR** - Must merge via pull request
- ✅ **Requires 1 approval** - At least one reviewer must approve
- ✅ **Dismisses stale reviews** - New commits require re-approval
- ✅ **Requires conversation resolution** - All PR comments must be resolved
- ✅ **Requires status checks** - CI must pass (Rules CI)

**Result:** Main branch is fully protected, all changes go through PRs

### 2. Workflow Branches Rules

**Applies to:** `workflow/*` branches (e.g., `workflow/homework-help`)

**Rules:**
- ❌ **Blocks deletion** - Prevents accidental deletion
- ✅ **Allows force pushes** - Workflows can update branches
- ✅ **Allows updates** - GitHub Actions can push changes
- ✅ **Bypass for integrations** - GitHub Actions can bypass restrictions

**Result:** Workflow branches can be updated by GitHub Actions but protected from manual deletion

### 3. Prevent Old Branch Patterns (Optional)

**Applies to:** Old timestamped branch patterns

**Rules:**
- ❌ **Blocks creation** - Cannot create branches matching old patterns
- ❌ **Blocks updates** - Existing old branches cannot be updated

**Result:** Forces use of new `workflow/*` naming convention

## Verification

After uploading, verify rulesets are active:

1. Go to **Settings** → **Rules** → **Rulesets**
2. You should see all three rulesets listed
3. Test by trying to push directly to main (should fail)
4. Test by running a workflow (should succeed on workflow/* branches)

## Customization

### Change Approval Count

Edit `main-branch-protection.json`:
```json
"required_approving_review_count": 2  // Change from 1 to 2
```

### Add Status Checks

Edit `main-branch-protection.json`:
```json
"required_status_checks": [
  { "context": "Rules CI" },
  { "context": "docs-ci" },
  { "context": "build" }
]
```

### Add Code Owner Review

Edit `main-branch-protection.json`:
```json
"require_code_owner_review": true
```

### Allow Force Push to Workflows

Edit `workflow-branches-rules.json`:
```json
{
  "type": "non_fast_forward",
  "parameters": {}  // Empty = allows force pushes
}
```

## Troubleshooting

### "Invalid ruleset JSON"
- Validate JSON syntax at jsonlint.com
- Ensure all required fields are present
- Check for trailing commas

### "Cannot push to workflow branch"
- Verify workflow branches ruleset is uploaded
- Check bypass_actors includes Integration
- Ensure GitHub Actions has write permissions

### "Cannot merge PR"
- Verify main branch protection is active
- Check if approval is required
- Ensure status checks are passing
- Resolve any required conversations

## Notes

- Rulesets work together: more specific rules (workflow/*) override general rules (main)
- GitHub Actions can bypass rules if configured in bypass_actors
- Rulesets are evaluated in order (most specific first)
- You can have multiple rulesets for different branch patterns

