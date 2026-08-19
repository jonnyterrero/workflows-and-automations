# Workflow Usage Guide

## Overview

All research workflows are now **manual-only** (workflow_dispatch), giving you full control over when research runs.

## Available Workflows

### 1. AI Research Workflow
**File**: `.github/workflows/ai-research.yml`

**Purpose**: Quick research on any topic

**How to Run**:
1. Go to **Actions** tab in GitHub
2. Select **AI Research Workflow**
3. Click **Run workflow**
4. Fill in:
   - **Topic**: What to research (e.g., "biomaterials synthesis", "differential equations")
   - **Category**: Select from dropdown (Personal Projects, Reflections, Math & Coding, Sciences)

**Output**: 
- Creates `RESEARCH.md` in root
- Commits to a new branch: `research-YYYYMMDD-HHMMSS`
- Includes course-specific context and resources if applicable

---

### 2. Nightly Research Workflow
**File**: `.github/workflows/nightly-research.yml`

**Purpose**: Overnight research that archives findings with date stamps

**How to Run**:
1. Go to **Actions** tab in GitHub
2. Select **Nightly Research**
3. Click **Run workflow**
4. Fill in:
   - **Topic**: Research topic (default: "Open issues summary & related papers")
   - **Archive Date**: Optional date (YYYY-MM-DD), defaults to today

**Output**:
- Saves to `docs/nightly/YYYY-MM-DD.md` (research)
- Saves to `docs/nightly/YYYY-MM-DD-syn.md` (synthesis)
- Commits to branch: `nightly-research-YYYYMMDD-HHMMSS`

**Best Use Cases**:
- Research before bedtime for review in morning
- Weekly research summaries
- Archiving research by date

---

### 3. AI Research & PR Workflow
**File**: `.github/workflows/ai-research-pr.yml`

**Purpose**: Research + synthesis + automatic PR creation

**How to Run**:
1. Go to **Actions** tab in GitHub
2. Select **AI Research & PR**
3. Click **Run workflow**
4. Fill in:
   - **Topic**: What to research
   - **Branch**: Branch name (default: "ai/research")

**Output**:
- Creates `RESEARCH.md` and `SYNTHESIS.md`
- Creates branch with timestamp
- Attempts to auto-create PR (falls back to manual instructions if needed)

**Best Use Cases**:
- When you want immediate PR review
- Research that needs collaboration
- Work that should be tracked in PRs

---

### 4. Homework Help Workflow
**File**: `.github/workflows/homework-help.yml`

**Purpose**: Course-specific homework assistance (optimized with your courses)

**How to Run**:
1. Go to **Actions** tab
2. Select **Homework Help**
3. Fill in:
   - **Course**: Course code (e.g., MAP2302, BME3100C)
   - **Assignment**: Assignment name (e.g., "HW1 - Laplace Transforms")
   - **Category**: Select appropriate category

**Output**:
- Saves to `school/<COURSE>/<assignment>/`
- Creates README.md, RESEARCH.md, SYNTHESIS.md
- Includes course-specific resources and context

---

## Workflow Comparison

| Workflow | Research | Synthesis | PR Creation | Archives | Best For |
|----------|----------|-----------|-------------|----------|----------|
| AI Research | ✅ | ❌ | ❌ | ❌ | Quick research |
| Nightly Research | ✅ | ✅ | ❌ | ✅ | Overnight research |
| AI Research & PR | ✅ | ✅ | ✅ | ❌ | Research + collaboration |
| Homework Help | ✅ | ✅ | ✅ | ❌ | Course assignments |

## Tips

### Running Research Before Bed
Use **Nightly Research** workflow with your topic. Results will be ready in the morning, archived by date.

### Quick Research
Use **AI Research Workflow** for immediate research needs. Results commit to a branch you can review.

### Course Work
Always use **Homework Help** for assignments - it includes:
- Course-specific prompts
- Relevant resources
- Proper file organization
- Course context

### Collaboration
Use **AI Research & PR** when you want:
- Automatic PR creation
- Team review
- Discussion on findings

## Troubleshooting

### "ACTIONS_PAT not set" Warning
If you see this, the workflow ran but couldn't commit. To enable auto-commit:
1. Go to Repository **Settings** → **Secrets and variables** → **Actions**
2. Add secret: `ACTIONS_PAT` with a GitHub Personal Access Token
3. Token needs `repo` scope and SSO enabled (if required)

### Workflow Not Appearing
- Make sure you're on the `main` branch (or default branch)
- Check that workflow files are in `.github/workflows/`
- Refresh the Actions tab

### Research Quality Issues
- Be specific in your topic
- Use course codes for course-related research
- Check `RESEARCH.md` output for details
- Resources are automatically included when relevant

