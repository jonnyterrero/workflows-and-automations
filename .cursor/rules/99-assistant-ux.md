# Assistant UX Rules

## Quick Questions
- Answer in **5–8 lines**; then give **1–2 "Do this next"** commands
- If a command requires a file, propose the **exact path and filename**

## Scheduling & Reminders
- When I say **"remind me…"**, generate a GitHub Issue using this template:

**Title**: `[Reminder] <what> — <YYYY-MM-DD HH:mm local>`
**Labels**: `type:reminder`
**Body**:
- What: <one-line>
- When: <ISO 8601>
- Auto-cron suggestion: <`15 14 * * 1-5`>
- Optional notification path (Actions/BuildShip)

## School Projects
- **Default folder**: `school/<course>/<assignment>/`
- Include **`README.md`** with problem restatement, derivation steps, and references (Chicago style if required)

## GitHub Issue Template

### Reminder Issue Template
```yaml
# .github/ISSUE_TEMPLATE/reminder.yml
name: Reminder
description: Create a scheduled reminder
labels: ["type:reminder"]
body:
  - type: input
    id: what
    attributes: { label: What to remind, placeholder: "Submit lab report" }
    validations: { required: true }
  - type: input
    id: when
    attributes: { label: When (ISO 8601), placeholder: "2025-10-28T14:00:00-04:00" }
    validations: { required: true }
  - type: textarea
    id: notes
    attributes: { label: Notes }
```

## Assistant UX Implementation

### Quick Response Handler
```typescript
// assistant/ux/quick-response.ts
export class QuickResponseHandler {
  static generateQuickResponse(
    question: string,
    answer: string,
    nextActions: string[]
  ): string {
    const response = `${answer}

**Do this next:**
${nextActions.map(action => `- ${action}`).join('\n')}`;

    return response;
  }

  static generateFileCommand(filePath: string, content: string): string {
    return `Create file: \`${filePath}\`\n\`\`\`\n${content}\n\`\`\``;
  }

  static generateDirectoryCommand(dirPath: string): string {
    return `Create directory: \`${dirPath}\``;
  }
}
```

### Reminder Generator
```typescript
// assistant/ux/reminder-generator.ts
export class ReminderGenerator {
  static generateReminderIssue(
    what: string,
    when: string,
    notes?: string
  ): {
    title: string;
    body: string;
    labels: string[];
  } {
    const date = new Date(when);
    const localTime = date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });

    const title = `[Reminder] ${what} — ${localTime}`;
    
    const cronSuggestion = this.generateCronSuggestion(date);
    
    const body = `## Reminder Details

**What**: ${what}
**When**: ${when}
**Auto-cron suggestion**: \`${cronSuggestion}\`

${notes ? `**Notes**: ${notes}` : ''}

## Optional Notification Path
- [ ] GitHub Actions
- [ ] BuildShip workflow
- [ ] Email notification
- [ ] Slack notification

---
*Generated: ${new Date().toISOString()}*`;

    return {
      title,
      body,
      labels: ['type:reminder']
    };
  }

  private static generateCronSuggestion(date: Date): string {
    const hour = date.getHours();
    const minute = date.getMinutes();
    const dayOfWeek = date.getDay();
    
    // Generate cron for specific time
    if (dayOfWeek >= 1 && dayOfWeek <= 5) {
      // Weekday
      return `${minute} ${hour} * * 1-5`;
    } else {
      // Weekend
      return `${minute} ${hour} * * ${dayOfWeek === 0 ? 0 : 6}`;
    }
  }
}
```

### School Project Generator
```typescript
// assistant/ux/school-project-generator.ts
export class SchoolProjectGenerator {
  static generateProjectStructure(
    course: string,
    assignment: string,
    requirements: {
      problemStatement: string;
      derivationSteps: string[];
      references: Array<{
        author: string;
        year: number;
        title: string;
        source: string;
      }>;
      citationStyle?: 'chicago' | 'apa' | 'mla';
    }
  ): {
    directory: string;
    files: Array<{
      path: string;
      content: string;
    }>;
  } {
    const directory = `school/${course}/${assignment}/`;
    
    const files = [
      {
        path: `${directory}README.md`,
        content: this.generateREADME(requirements)
      },
      {
        path: `${directory}solution.m`,
        content: this.generateMATLABSolution(requirements)
      },
      {
        path: `${directory}analysis.py`,
        content: this.generatePythonAnalysis(requirements)
      }
    ];

    return { directory, files };
  }

  private static generateREADME(requirements: any): string {
    const citations = this.formatCitations(requirements.references, requirements.citationStyle);
    
    return `# ${requirements.problemStatement}

## Problem Statement
${requirements.problemStatement}

## Approach
[Methodology and approach used to solve the problem]

## Derivation Steps
${requirements.derivationSteps.map((step, index) => `${index + 1}. ${step}`).join('\n')}

## Implementation
[Code, algorithms, or procedures used]

## Results
[Findings, outcomes, and analysis]

## References
${citations}

## Ethics Statement
[If applicable: ethical considerations, data protection measures]

---
*Course: [Course Code] | Assignment: [Assignment Name] | Due: [Date]*`;
  }

  private static formatCitations(
    references: Array<{ author: string; year: number; title: string; source: string }>,
    style: string = 'chicago'
  ): string {
    if (style === 'chicago') {
      return references.map(ref => 
        `${ref.author}. ${ref.year}. "${ref.title}." ${ref.source}.`
      ).join('\n');
    } else if (style === 'apa') {
      return references.map(ref => 
        `${ref.author} (${ref.year}). ${ref.title}. ${ref.source}.`
      ).join('\n');
    } else if (style === 'mla') {
      return references.map(ref => 
        `${ref.author}. "${ref.title}." ${ref.source}, ${ref.year}.`
      ).join('\n');
    }
    
    return references.map(ref => `${ref.author} (${ref.year}). ${ref.title}. ${ref.source}.`).join('\n');
  }

  private static generateMATLABSolution(requirements: any): string {
    return `% ${requirements.problemStatement}
% Solution for assignment

function solution()
    % Set random seed for reproducibility
    rng(42);
    
    % Problem parameters
    % [Define problem parameters here]
    
    % Solution implementation
    % [Implement solution here]
    
    % Results
    % [Display results here]
end

% Helper functions
function result = helperFunction(input)
    % Helper function implementation
    result = input;
end`;
  }

  private static generatePythonAnalysis(requirements: any): string {
    return `#!/usr/bin/env python3
"""
${requirements.problemStatement}
Solution for assignment
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def main():
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Problem parameters
    # [Define problem parameters here]
    
    # Solution implementation
    # [Implement solution here]
    
    # Results
    # [Display results here]

if __name__ == "__main__":
    main()`;
  }
}
```

### UX Response Templates
```typescript
// assistant/ux/response-templates.ts
export class ResponseTemplates {
  static getQuickResponseTemplate(): string {
    return `## Quick Answer
[5-8 line answer]

**Do this next:**
- [Action 1 with exact file path]
- [Action 2 with exact file path]`;
  }

  static getReminderTemplate(): string {
    return `## Reminder Created
**Title**: [Reminder] <what> — <YYYY-MM-DD HH:mm local>
**Labels**: type:reminder
**Body**: 
- What: <one-line>
- When: <ISO 8601>
- Auto-cron suggestion: <cron expression>
- Optional notification path (Actions/BuildShip)

**Do this next:**
- Create GitHub issue with the above template
- Set up automation if needed`;
  }

  static getSchoolProjectTemplate(): string {
    return `## School Project Created
**Directory**: school/<course>/<assignment>/
**Files**: README.md, solution.m, analysis.py

**Do this next:**
- Create directory: \`school/<course>/<assignment>/\`
- Create file: \`school/<course>/<assignment>/README.md\`
- Create file: \`school/<course>/<assignment>/solution.m\``;
  }
}
```

### Command Generator
```typescript
// assistant/ux/command-generator.ts
export class CommandGenerator {
  static generateFileCommand(filePath: string, content: string): string {
    return `Create file: \`${filePath}\`\n\`\`\`\n${content}\n\`\`\``;
  }

  static generateDirectoryCommand(dirPath: string): string {
    return `Create directory: \`${dirPath}\``;
  }

  static generateGitCommand(command: string): string {
    return `Run: \`${command}\``;
  }

  static generateNPMCommand(command: string): string {
    return `Run: \`npm ${command}\``;
  }

  static generatePythonCommand(command: string): string {
    return `Run: \`python ${command}\``;
  }

  static generateMATLABCommand(command: string): string {
    return `Run: \`matlab -batch "${command}"\``;
  }
}
```

## Usage Examples

### Quick Question Response
```typescript
// Example: "How do I set up TypeScript?"
const response = QuickResponseHandler.generateQuickResponse(
  "How do I set up TypeScript?",
  "Install TypeScript globally with npm install -g typescript. Create a tsconfig.json file with your configuration. Use tsc to compile TypeScript files to JavaScript.",
  [
    "Run: `npm install -g typescript`",
    "Create file: `tsconfig.json`"
  ]
);
```

### Reminder Creation
```typescript
// Example: "remind me to submit lab report tomorrow at 2pm"
const reminder = ReminderGenerator.generateReminderIssue(
  "Submit lab report",
  "2025-10-28T14:00:00-04:00",
  "Make sure to include all calculations and references"
);

// Output:
// Title: [Reminder] Submit lab report — 2025-10-28 14:00
// Labels: type:reminder
// Body: [Generated reminder body]
```

### School Project Creation
```typescript
// Example: "Create a project for MAP2302 assignment 3"
const project = SchoolProjectGenerator.generateProjectStructure(
  "MAP2302",
  "assignment-3",
  {
    problemStatement: "Solve the differential equation y' + y = x",
    derivationSteps: [
      "Identify the equation type",
      "Find the integrating factor",
      "Solve the homogeneous equation",
      "Find the particular solution"
    ],
    references: [
      {
        author: "Smith, John",
        year: 2023,
        title: "Differential Equations",
        source: "Academic Press"
      }
    ],
    citationStyle: "chicago"
  }
);
```

### Command Generation
```typescript
// Example commands
const fileCommand = CommandGenerator.generateFileCommand(
  "src/index.ts",
  "console.log('Hello World');"
);

const dirCommand = CommandGenerator.generateDirectoryCommand(
  "school/MAP2302/assignment-3/"
);

const gitCommand = CommandGenerator.generateGitCommand(
  "git add . && git commit -m 'Add assignment 3'"
);
```

## Integration with Workflows

### GitHub Actions Integration
```yaml
# .github/workflows/reminder-handler.yml
name: Reminder Handler
on:
  issues:
    types: [opened]
    labels: ['type:reminder']

jobs:
  process-reminder:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Process reminder
        run: |
          npx ts-node scripts/process-reminder.ts \
            --issue-number ${{ github.event.issue.number }} \
            --repository ${{ github.repository }}
```

### Reminder Processing Script
```typescript
// scripts/process-reminder.ts
import { ReminderGenerator } from '../assistant/ux/reminder-generator';

async function processReminder(issueNumber: number, repository: string): Promise<void> {
  // Get issue details
  const issue = await getIssue(issueNumber, repository);
  
  // Extract reminder details
  const what = issue.body.match(/\*\*What\*\*: (.+)/)?.[1];
  const when = issue.body.match(/\*\*When\*\*: (.+)/)?.[1];
  
  if (what && when) {
    // Create scheduled workflow
    await createScheduledWorkflow(what, when);
    
    // Set up notifications
    await setupNotifications(issueNumber, repository);
  }
}

if (require.main === module) {
  const issueNumber = parseInt(process.argv[2]);
  const repository = process.argv[3];
  
  processReminder(issueNumber, repository);
}
```
