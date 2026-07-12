# Architecture & Folders

## Folders
- **`scripts/`**: CLI tools (ts-node, python)
- **`assistant/`**: reusable helpers (api clients, formatters)
- **`workflows/`**: YAML or BuildShip exports (optional mirror of .github/workflows)
- **`docs/`**: briefs, plans, nightly research
- **`school/`**: MATLAB/Python notebooks + results
- **`.cursor/rules/`**: these files

## AI Artifacts Flow
1) **Perplexity** → `RESEARCH.md` (web-grounded)
2) **OpenAI** → `SYNTHESIS.md` (plan, issues, PR body, tests)
3) **GitHub Action** → commit on `ai/*` branch + open PR

## Issue Labels (standardize)
- **`type:schedule`**, **`type:reminder`**, **`type:research`**, **`type:build`**
- **`course:MAP2302`**, **`course:Biomaterials`**, etc.
- **`area:matlab`**, **`area:python`**, **`area:typescript`**, **`area:arduino`**

## Project Structure

```
ai-research-repo/
├── scripts/                    # CLI tools
│   ├── research.ts             # Perplexity research
│   ├── synthesize.ts           # OpenAI synthesis
│   ├── open_pr.ts              # GitHub PR creation
│   └── generate-docs.ts        # Documentation generation
├── assistant/                  # Reusable helpers
│   ├── api-clients/
│   │   ├── perplexity.ts      # Perplexity API client
│   │   ├── openai.ts          # OpenAI API client
│   │   └── github.ts          # GitHub API client
│   ├── formatters/
│   │   ├── markdown.ts         # Markdown formatting
│   │   ├── issue-template.ts   # Issue template generation
│   │   └── pr-template.ts      # PR template generation
│   └── utils/
│       ├── date-utils.ts       # Date/time utilities
│       ├── file-utils.ts       # File operations
│       └── validation.ts      # Input validation
├── workflows/                  # Workflow exports
│   ├── ai-research-pr.yml      # Manual research workflow
│   ├── nightly-research.yml    # Automated nightly research
│   └── buildship-exports/      # BuildShip workflow exports
├── docs/                       # Documentation
│   ├── briefs/                 # Research briefs
│   │   ├── ai-safety.md
│   │   └── ml-pipeline.md
│   ├── plans/                  # Project plans
│   │   ├── ai-safety.md
│   │   └── ml-pipeline.md
│   └── nightly/                # Nightly research archives
│       ├── 2024-01-15.md
│       └── 2024-01-16.md
├── school/                     # Academic work
│   ├── MAP2302/               # Differential Equations
│   │   ├── assignment-1/
│   │   │   ├── README.md
│   │   │   ├── solution.m
│   │   │   └── results/
│   │   └── assignment-2/
│   ├── Biomaterials/           # Biomaterials course
│   │   ├── project-1/
│   │   │   ├── README.md
│   │   │   ├── analysis.py
│   │   │   └── results/
│   │   └── project-2/
│   └── CS101/                 # Computer Science
│       ├── project-1/
│       └── project-2/
├── .cursor/                    # Cursor rules
│   └── rules/
│       ├── 00-style.md
│       ├── 10-testing.md
│       ├── 20-architecture.md
│       ├── 30-assistant-persona.md
│       ├── 40-testing.md
│       └── 50-documentation.md
├── .github/                    # GitHub workflows
│   └── workflows/
│       ├── ai-research.yml
│       ├── nightly-research.yml
│       └── ai-research-pr.yml
├── RESEARCH.md                # Generated research
├── SYNTHESIS.md               # Generated synthesis
├── CHANGELOG.md               # Project changelog
├── package.json               # Dependencies
└── README.md                  # Project documentation
```

## AI Artifacts Flow Implementation

### 1. Perplexity Research Flow
```typescript
// scripts/research.ts
import { PerplexityClient } from '../assistant/api-clients/perplexity';
import { MarkdownFormatter } from '../assistant/formatters/markdown';

async function researchFlow(topic: string): Promise<void> {
  const client = new PerplexityClient(process.env.PPLX_API_KEY!);
  const formatter = new MarkdownFormatter();
  
  // Step 1: Research with Perplexity
  const research = await client.research(topic);
  
  // Step 2: Format as markdown
  const formatted = formatter.formatResearch(research);
  
  // Step 3: Save to RESEARCH.md
  writeFileSync('RESEARCH.md', formatted);
}
```

### 2. OpenAI Synthesis Flow
```typescript
// scripts/synthesize.ts
import { OpenAIClient } from '../assistant/api-clients/openai';
import { IssueTemplateFormatter } from '../assistant/formatters/issue-template';

async function synthesisFlow(inputFile: string): Promise<void> {
  const client = new OpenAIClient(process.env.OPENAI_API_KEY!);
  const formatter = new IssueTemplateFormatter();
  
  // Step 1: Read research
  const research = readFileSync(inputFile, 'utf-8');
  
  // Step 2: Synthesize with OpenAI
  const synthesis = await client.synthesize(research);
  
  // Step 3: Format as synthesis
  const formatted = formatter.formatSynthesis(synthesis);
  
  // Step 4: Save to SYNTHESIS.md
  writeFileSync('SYNTHESIS.md', formatted);
}
```

### 3. GitHub Action Flow
```yaml
# .github/workflows/ai-research-pr.yml
name: AI Research & PR
on:
  workflow_dispatch:
    inputs:
      topic:
        description: "Research topic"
        required: true
      branch:
        description: "Target branch"
        required: true
        default: "ai/research-${{ github.run_id }}"

jobs:
  research:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      
      # Step 1: Research with Perplexity
      - name: Research
        env:
          PPLX_API_KEY: ${{ secrets.PPLX_API_KEY }}
        run: npx ts-node scripts/research.ts "${{ github.event.inputs.topic }}"
      
      # Step 2: Synthesize with OpenAI
      - name: Synthesize
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: npx ts-node scripts/synthesize.ts RESEARCH.md
      
      # Step 3: Create branch and commit
      - name: Create Branch
        run: |
          git switch -c "${{ github.event.inputs.branch }}"
          git add RESEARCH.md SYNTHESIS.md
          git commit -m "AI: research & synthesis for ${{ github.event.inputs.topic }}"
          git push --set-upstream origin "${{ github.event.inputs.branch }}"
      
      # Step 4: Open PR
      - name: Open PR
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr create --title "AI: ${{ github.event.inputs.topic }}" \
            --body-file SYNTHESIS.md \
            --base main \
            --head "${{ github.event.inputs.branch }}"
```

## Issue Label System

### Label Categories
```typescript
// assistant/formatters/issue-template.ts
export const ISSUE_LABELS = {
  types: [
    'type:schedule',    // Scheduled tasks
    'type:reminder',    // Reminders
    'type:research',    // Research tasks
    'type:build',       // Build/CI tasks
    'type:bug',         // Bug reports
    'type:feature'      // Feature requests
  ],
  courses: [
    'course:MAP2302',   // Differential Equations
    'course:Biomaterials', // Biomaterials
    'course:CS101',     // Computer Science
    'course:Physics',   // Physics
    'course:Chemistry'  // Chemistry
  ],
  areas: [
    'area:matlab',      // MATLAB work
    'area:python',      // Python work
    'area:typescript',  // TypeScript work
    'area:arduino',     // Arduino projects
    'area:research',    // Research work
    'area:documentation' // Documentation
  ]
};

export function generateIssueLabels(topic: string, course?: string, area?: string): string[] {
  const labels: string[] = [];
  
  // Add type label based on topic
  if (topic.includes('schedule') || topic.includes('due')) {
    labels.push('type:schedule');
  } else if (topic.includes('research')) {
    labels.push('type:research');
  } else {
    labels.push('type:reminder');
  }
  
  // Add course label
  if (course) {
    labels.push(`course:${course}`);
  }
  
  // Add area label
  if (area) {
    labels.push(`area:${area}`);
  }
  
  return labels;
}
```

### Issue Template Generation
```typescript
// assistant/formatters/issue-template.ts
export function generateIssueTemplate(topic: string, course?: string, area?: string): string {
  const labels = generateIssueLabels(topic, course, area);
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + 7); // Default 1 week from now
  
  return `---
labels: ${labels.join(', ')}
dueDate: ${dueDate.toISOString()}
---

# ${topic}

## Description
[Brief description of the task]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Notes
[Additional notes or context]

---
*Created: ${new Date().toISOString().split('T')[0]} | Labels: ${labels.join(', ')}*
`;
}
```

## School Project Structure

### MATLAB Projects
```
school/MAP2302/assignment-1/
├── README.md              # Problem statement, approach, derivation
├── solution.m            # Main solution file
├── helper_functions.m    # Helper functions
├── test_calculations.m    # Test cases
├── results/              # Generated results
│   ├── plots/            # MATLAB figures
│   ├── data/             # Exported data
│   └── reports/          # Generated reports
└── references/           # Reference materials
```

### Python Projects
```
school/Biomaterials/project-1/
├── README.md              # Problem statement, approach, derivation
├── analysis.py           # Main analysis script
├── data_processing.py     # Data processing functions
├── visualization.py      # Plotting functions
├── tests/                # Test files
│   ├── test_analysis.py
│   └── test_processing.py
├── results/              # Generated results
│   ├── plots/            # Generated plots
│   ├── data/             # Processed data
│   └── reports/          # Generated reports
└── requirements.txt       # Python dependencies
```

## Workflow Integration

### BuildShip Integration
```typescript
// workflows/buildship-exports/ai-research-workflow.json
{
  "name": "AI Research Workflow",
  "description": "Automated research and synthesis workflow",
  "triggers": [
    {
      "type": "manual",
      "name": "Start Research",
      "inputs": [
        {
          "name": "topic",
          "type": "string",
          "required": true
        }
      ]
    }
  ],
  "steps": [
    {
      "name": "Research",
      "type": "api",
      "config": {
        "url": "https://api.perplexity.ai/chat/completions",
        "method": "POST",
        "headers": {
          "Authorization": "Bearer {{PPLX_API_KEY}}"
        }
      }
    },
    {
      "name": "Synthesize",
      "type": "api",
      "config": {
        "url": "https://api.openai.com/v1/chat/completions",
        "method": "POST",
        "headers": {
          "Authorization": "Bearer {{OPENAI_API_KEY}}"
        }
      }
    }
  ]
}
```

## Documentation Commands

### Generate Documentation
```bash
# Generate brief
npm run docs:brief "AI Safety Research"

# Generate plan
npm run docs:plan "Implement ML Pipeline"

# Generate school project
npm run docs:school "MAP2302" "Assignment 3"

# Generate issue
npm run docs:issue "Complete differential equations homework" "MAP2302" "matlab"
```

### Package.json Scripts
```json
{
  "scripts": {
    "docs:brief": "ts-node scripts/generate-brief.ts",
    "docs:plan": "ts-node scripts/generate-plan.ts",
    "docs:school": "ts-node scripts/generate-school-docs.ts",
    "docs:issue": "ts-node scripts/generate-issue.ts",
    "docs:changelog": "ts-node scripts/generate-changelog.ts"
  }
}
```
