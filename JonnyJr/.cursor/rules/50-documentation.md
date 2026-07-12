# Documentation Rules

## Always Generate
- **`docs/briefs/<topic>.md`**: 250-word brief + sources
- **`docs/plans/<topic>.md`**: task list, dependencies, risks
- **`CHANGELOG.md`**: on release branches (auto-summarized)

## School Projects
- **`docs/school/<course>/<assignment>/README.md`**
  - Problem statement, approach, derivation, references (no copyrighted dumps)
- Include **PRISMA/ethics** where applicable for biomaterials/systematic reviews

## Documentation Templates

### Brief Template
```markdown
# Brief: <Topic>

## Summary
[250-word concise summary of the topic, key findings, and implications]

## Key Points
- Point 1: [Brief explanation]
- Point 2: [Brief explanation]
- Point 3: [Brief explanation]

## Sources
1. [Author, Year] - [Title] - [URL/DOI]
2. [Author, Year] - [Title] - [URL/DOI]
3. [Author, Year] - [Title] - [URL/DOI]

## Next Steps
- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3

---
*Generated: [Date] | Topic: [Topic] | Status: [Draft/Review/Published]*
```

### Plan Template
```markdown
# Plan: <Topic>

## Overview
[Brief description of the project/initiative]

## Tasks
### Phase 1: [Phase Name]
- [ ] Task 1: [Description] - [Estimated time]
- [ ] Task 2: [Description] - [Estimated time]
- [ ] Task 3: [Description] - [Estimated time]

### Phase 2: [Phase Name]
- [ ] Task 1: [Description] - [Estimated time]
- [ ] Task 2: [Description] - [Estimated time]

## Dependencies
- **External**: [Dependency description]
- **Internal**: [Dependency description]
- **Resources**: [Resource requirements]

## Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | High/Medium/Low | High/Medium/Low | [Mitigation strategy] |
| [Risk 2] | High/Medium/Low | High/Medium/Low | [Mitigation strategy] |

## Timeline
- **Start Date**: [Date]
- **Milestone 1**: [Date] - [Description]
- **Milestone 2**: [Date] - [Description]
- **Completion**: [Date]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

---
*Created: [Date] | Owner: [Name] | Status: [Planning/In Progress/Completed]*
```

### School Project Template
```markdown
# <Course>: <Assignment Title>

## Problem Statement
[Clear description of the problem to be solved]

## Approach
[Methodology and approach used to solve the problem]

## Derivation
[Mathematical derivations, equations, and calculations]

## Implementation
[Code, algorithms, or procedures used]

## Results
[Findings, outcomes, and analysis]

## References
1. [Author, Year] - [Title] - [Journal/Conference] - [DOI/URL]
2. [Author, Year] - [Title] - [Journal/Conference] - [DOI/URL]

## Ethics Statement
[If applicable: PRISMA guidelines, ethical considerations, etc.]

---
*Course: [Course Code] | Assignment: [Assignment Name] | Due: [Date]*
```

### CHANGELOG Template
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements

## [1.0.0] - 2024-01-15

### Added
- Initial release
- Core functionality

### Changed
- Breaking changes

### Fixed
- Initial bug fixes
```

## Documentation Automation

### Auto-Generate Briefs
```typescript
// scripts/generate-brief.ts
import { writeFileSync } from 'fs';
import { PerplexityClient } from './api-client';

async function generateBrief(topic: string): Promise<void> {
  const client = new PerplexityClient(process.env.PPLX_API_KEY!);
  const research = await client.research(topic);
  
  const brief = `# Brief: ${topic}

## Summary
${research.summary}

## Key Points
${research.keyPoints.map(point => `- ${point}`).join('\n')}

## Sources
${research.sources.map((source, i) => `${i + 1}. ${source}`).join('\n')}

## Next Steps
- [ ] Review and validate findings
- [ ] Implement recommendations
- [ ] Schedule follow-up research

---
*Generated: ${new Date().toISOString().split('T')[0]} | Topic: ${topic} | Status: Draft*
`;

  const filename = `docs/briefs/${topic.toLowerCase().replace(/\s+/g, '-')}.md`;
  writeFileSync(filename, brief);
  console.log(`Brief generated: ${filename}`);
}
```

### Auto-Generate Plans
```typescript
// scripts/generate-plan.ts
import { writeFileSync } from 'fs';
import { OpenAIClient } from './api-client';

async function generatePlan(topic: string): Promise<void> {
  const client = new OpenAIClient(process.env.OPENAI_API_KEY!);
  const plan = await client.generatePlan(topic);
  
  const planDoc = `# Plan: ${topic}

## Overview
${plan.overview}

## Tasks
${plan.tasks.map(phase => `
### ${phase.name}
${phase.tasks.map(task => `- [ ] ${task.description} - ${task.estimate}`).join('\n')}
`).join('\n')}

## Dependencies
${plan.dependencies.map(dep => `- **${dep.type}**: ${dep.description}`).join('\n')}

## Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
${plan.risks.map(risk => `| ${risk.description} | ${risk.probability} | ${risk.impact} | ${risk.mitigation} |`).join('\n')}

## Timeline
- **Start Date**: ${plan.startDate}
- **Completion**: ${plan.completionDate}

## Success Criteria
${plan.criteria.map(criterion => `- [ ] ${criterion}`).join('\n')}

---
*Created: ${new Date().toISOString().split('T')[0]} | Owner: AI Assistant | Status: Planning*
`;

  const filename = `docs/plans/${topic.toLowerCase().replace(/\s+/g, '-')}.md`;
  writeFileSync(filename, planDoc);
  console.log(`Plan generated: ${filename}`);
}
```

### Auto-Generate CHANGELOG
```typescript
// scripts/generate-changelog.ts
import { writeFileSync, readFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';

function generateChangelog(): void {
  const commits = execSync('git log --oneline --since="1 month ago"', { encoding: 'utf-8' });
  const commitLines = commits.trim().split('\n');
  
  const changes = {
    added: [],
    changed: [],
    fixed: [],
    removed: []
  };
  
  commitLines.forEach(commit => {
    const message = commit.split(' ').slice(1).join(' ');
    if (message.startsWith('feat:')) {
      changes.added.push(message.replace('feat:', '').trim());
    } else if (message.startsWith('fix:')) {
      changes.fixed.push(message.replace('fix:', '').trim());
    } else if (message.startsWith('refactor:')) {
      changes.changed.push(message.replace('refactor:', '').trim());
    } else if (message.startsWith('remove:')) {
      changes.removed.push(message.replace('remove:', '').trim());
    }
  });
  
  const changelog = `# Changelog

## [Unreleased]

### Added
${changes.added.map(item => `- ${item}`).join('\n')}

### Changed
${changes.changed.map(item => `- ${item}`).join('\n')}

### Fixed
${changes.fixed.map(item => `- ${item}`).join('\n')}

### Removed
${changes.removed.map(item => `- ${item}`).join('\n')}

---
*Generated: ${new Date().toISOString().split('T')[0]}*
`;

  writeFileSync('CHANGELOG.md', changelog);
  console.log('CHANGELOG.md generated');
}
```

## School Project Documentation

### PRISMA Template (for Systematic Reviews)
```markdown
# PRISMA Checklist: <Review Title>

## Title
[Review title]

## Abstract
[Structured abstract following PRISMA guidelines]

## Introduction
[Background and rationale]

## Methods
### Eligibility Criteria
- **Inclusion**: [Criteria]
- **Exclusion**: [Criteria]

### Information Sources
- [Database 1]
- [Database 2]
- [Other sources]

### Search Strategy
[Detailed search strategy]

### Study Selection
[Process for study selection]

### Data Collection Process
[Data extraction methods]

### Data Items
[Variables collected]

### Risk of Bias Assessment
[Methods for assessing bias]

### Synthesis Methods
[Statistical methods used]

## Results
[Study selection, characteristics, and synthesis results]

## Discussion
[Interpretation and implications]

## References
[All included studies and other references]

## Ethics Statement
[Ethical considerations and approvals]

---
*PRISMA Checklist completed: [Date] | Reviewers: [Names]*
```

### Ethics Template
```markdown
# Ethics Statement: <Project Title>

## Ethical Considerations
[Description of ethical issues and considerations]

## Approval
- **Institutional Review Board**: [Approval number/status]
- **Informed Consent**: [Process and documentation]
- **Data Protection**: [Measures taken]

## Conflicts of Interest
[Declaration of any conflicts]

## Funding
[Source of funding and any potential conflicts]

---
*Ethics Review: [Date] | Approved by: [Authority]*
```

## Documentation Commands

### Generate All Documentation
```bash
# Generate brief for topic
npm run docs:brief "AI Safety Research"

# Generate plan for project
npm run docs:plan "Implement ML Pipeline"

# Generate changelog
npm run docs:changelog

# Generate school project docs
npm run docs:school "MAP2302" "Assignment 3"
```

### Documentation Structure
```
docs/
├── briefs/
│   ├── ai-safety-research.md
│   └── ml-pipeline.md
├── plans/
│   ├── ai-safety-research.md
│   └── ml-pipeline.md
├── school/
│   ├── MAP2302/
│   │   └── assignment-3/
│   │       └── README.md
│   └── CS101/
│       └── project-1/
│           └── README.md
└── CHANGELOG.md
```
