# Agent Call Patterns

## Perplexity (Research)
- **Inputs**: topic, constraints, desired outputs (links, pros/cons, numbers)
- **Require**: source list. Prefer diverse domains
- **Output**: `docs/briefs/<topic>.md` with "Key Findings" and "Open Questions"

## OpenAI (Synthesis)
- **Inputs**: research text + goal (build plan, code skeleton, test plan)
- **Output blocks** (always in order):
  1) Project brief (≤250 words)
  2) Task list (checkboxes)
  3) File changes (paths + snippets)
  4) Test plan
  5) PR body

## Guardrails
- If external API usage is suggested, also emit **`.env.example`** keys and a `README` setup snippet

## Perplexity Research Patterns

### Research Input Template
```typescript
interface ResearchInput {
  topic: string;
  constraints: string[];
  desiredOutputs: {
    links: boolean;
    prosCons: boolean;
    numbers: boolean;
    comparisons: boolean;
  };
  domainFocus: string[];
}

// Example usage
const researchInput: ResearchInput = {
  topic: "AI Safety in Autonomous Vehicles",
  constraints: [
    "Focus on 2023-2024 research",
    "Include regulatory perspectives",
    "Consider ethical implications"
  ],
  desiredOutputs: {
    links: true,
    prosCons: true,
    numbers: true,
    comparisons: true
  },
  domainFocus: ["academic", "industry", "regulatory", "ethical"]
};
```

### Perplexity Research Implementation
```typescript
// assistant/api-clients/perplexity.ts
export class PerplexityClient {
  constructor(private apiKey: string) {}

  async research(input: ResearchInput): Promise<ResearchResult> {
    const prompt = this.buildResearchPrompt(input);
    
    const response = await fetch("https://api.perplexity.ai/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        model: "pplx-7b-chat",
        messages: [
          {
            role: "user",
            content: prompt
          }
        ],
        search_domain_filter: ["web"]
      })
    });

    const data = await response.json();
    return this.parseResearchResult(data);
  }

  private buildResearchPrompt(input: ResearchInput): string {
    return `Research this topic: ${input.topic}

Constraints: ${input.constraints.join(', ')}

Required outputs:
- Links: ${input.desiredOutputs.links ? 'Yes' : 'No'}
- Pros/Cons: ${input.desiredOutputs.prosCons ? 'Yes' : 'No'}
- Numbers/Statistics: ${input.desiredOutputs.numbers ? 'Yes' : 'No'}
- Comparisons: ${input.desiredOutputs.comparisons ? 'Yes' : 'No'}

Focus on diverse domains: ${input.domainFocus.join(', ')}

Provide sources from multiple domains and include "Key Findings" and "Open Questions" sections.`;
  }
}
```

### Research Output Format
```markdown
# Brief: <Topic>

## Key Findings
[Main research findings with supporting evidence]

## Open Questions
[Unresolved questions and areas for further research]

## Sources
1. [Academic Source] - [Title] - [URL]
2. [Industry Source] - [Title] - [URL]
3. [Regulatory Source] - [Title] - [URL]

## Pros and Cons
### Advantages
- [Advantage 1]
- [Advantage 2]

### Disadvantages
- [Disadvantage 1]
- [Disadvantage 2]

## Statistics and Numbers
- [Key statistic 1]
- [Key statistic 2]

## Comparisons
[Comparative analysis of different approaches]

---
*Generated: [Date] | Sources: [Count] | Domains: [List]*
```

## OpenAI Synthesis Patterns

### Synthesis Input Template
```typescript
interface SynthesisInput {
  researchText: string;
  goal: 'build_plan' | 'code_skeleton' | 'test_plan' | 'pr_body';
  context?: {
    projectType: string;
    techStack: string[];
    timeline: string;
    constraints: string[];
  };
}

// Example usage
const synthesisInput: SynthesisInput = {
  researchText: "Research findings about AI safety...",
  goal: 'build_plan',
  context: {
    projectType: 'web_application',
    techStack: ['TypeScript', 'React', 'Node.js'],
    timeline: '2 weeks',
    constraints: ['budget_limited', 'team_size_3']
  }
};
```

### OpenAI Synthesis Implementation
```typescript
// assistant/api-clients/openai.ts
export class OpenAIClient {
  constructor(private apiKey: string) {}

  async synthesize(input: SynthesisInput): Promise<SynthesisResult> {
    const prompt = this.buildSynthesisPrompt(input);
    
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          {
            role: "user",
            content: prompt
          }
        ]
      })
    });

    const data = await response.json();
    return this.parseSynthesisResult(data);
  }

  private buildSynthesisPrompt(input: SynthesisInput): string {
    return `Based on this research: ${input.researchText}

Goal: ${input.goal}
Context: ${JSON.stringify(input.context, null, 2)}

Provide output in this exact format:

1) Project brief (≤250 words)
2) Task list (checkboxes)
3) File changes (paths + snippets)
4) Test plan
5) PR body

Ensure all outputs are actionable and specific.`;
  }
}
```

### Synthesis Output Format
```markdown
# Synthesis: <Project Name>

## 1. Project Brief
[Concise project description ≤250 words]

## 2. Task List
- [ ] Task 1: [Description]
- [ ] Task 2: [Description]
- [ ] Task 3: [Description]

## 3. File Changes
### New Files
- `src/components/NewComponent.tsx`
  ```typescript
  // Code snippet
  ```

- `tests/NewComponent.test.tsx`
  ```typescript
  // Test code snippet
  ```

### Modified Files
- `src/App.tsx`
  ```typescript
  // Changes to existing file
  ```

## 4. Test Plan
### Unit Tests
- [ ] Test component rendering
- [ ] Test user interactions
- [ ] Test error handling

### Integration Tests
- [ ] Test API integration
- [ ] Test data flow
- [ ] Test error scenarios

### E2E Tests
- [ ] Test complete user journey
- [ ] Test cross-browser compatibility

## 5. PR Body
### Changes
- Added new component for [purpose]
- Implemented [feature] with [details]
- Updated [existing functionality]

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

### Deployment
- [ ] Staging deployment successful
- [ ] Production deployment ready

---
*Generated: [Date] | Goal: [Goal] | Context: [Context]*
```

## Guardrails Implementation

### Environment Variables Guardrail
```typescript
// assistant/guardrails/env-guardrail.ts
export function checkForExternalAPIs(code: string): {
  hasExternalAPIs: boolean;
  requiredEnvVars: string[];
  setupInstructions: string;
} {
  const apiPatterns = [
    /process\.env\.(\w+)/g,
    /API_KEY/g,
    /SECRET/g,
    /TOKEN/g
  ];
  
  const foundVars = new Set<string>();
  apiPatterns.forEach(pattern => {
    const matches = code.match(pattern);
    if (matches) {
      matches.forEach(match => {
        if (match.startsWith('process.env.')) {
          foundVars.add(match.replace('process.env.', ''));
        } else {
          foundVars.add(match);
        }
      });
    }
  });
  
  const hasExternalAPIs = foundVars.size > 0;
  const requiredEnvVars = Array.from(foundVars);
  
  const setupInstructions = hasExternalAPIs ? `
## Environment Setup

### Required Environment Variables
${requiredEnvVars.map(varName => `- ${varName}: [Your ${varName} value]`).join('\n')}

### Setup Instructions
1. Copy \`.env.example\` to \`.env\`
2. Fill in the required environment variables
3. Run \`npm install\` to install dependencies
4. Run \`npm start\` to start the application

### Security Notes
- Never commit \`.env\` files to version control
- Use different API keys for development and production
- Rotate API keys regularly
` : '';
  
  return {
    hasExternalAPIs,
    requiredEnvVars,
    setupInstructions
  };
}
```

### .env.example Generation
```typescript
// assistant/formatters/env-example.ts
export function generateEnvExample(requiredVars: string[]): string {
  const envExample = `# Environment Variables
# Copy this file to .env and fill in your values

${requiredVars.map(varName => `# ${varName} - [Description]
${varName}=your_${varName.toLowerCase()}_here
`).join('\n')}

# Optional variables
# DEBUG=true
# LOG_LEVEL=info
`;

  return envExample;
}
```

### README Setup Snippet
```typescript
// assistant/formatters/readme-setup.ts
export function generateSetupSnippet(requiredVars: string[]): string {
  return `## Setup

### Prerequisites
- Node.js 18+
- npm or yarn
- API keys for external services

### Installation
\`\`\`bash
# Clone the repository
git clone <repository-url>
cd <project-name>

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Start the application
npm start
\`\`\`

### Required API Keys
${requiredVars.map(varName => `- **${varName}**: [Where to get this key]`).join('\n')}

### Development
\`\`\`bash
# Run in development mode
npm run dev

# Run tests
npm test

# Build for production
npm run build
\`\`\`
`;
}
```

## Agent Call Examples

### Perplexity Research Call
```typescript
// Example of calling Perplexity for research
const researchCall = {
  topic: "Machine Learning in Healthcare",
  constraints: [
    "Focus on 2023-2024 developments",
    "Include regulatory compliance",
    "Consider privacy implications"
  ],
  desiredOutputs: {
    links: true,
    prosCons: true,
    numbers: true,
    comparisons: true
  },
  domainFocus: ["academic", "industry", "regulatory", "healthcare"]
};

const result = await perplexityClient.research(researchCall);
// Outputs to docs/briefs/machine-learning-healthcare.md
```

### OpenAI Synthesis Call
```typescript
// Example of calling OpenAI for synthesis
const synthesisCall = {
  researchText: "Research findings about ML in healthcare...",
  goal: 'build_plan',
  context: {
    projectType: 'healthcare_application',
    techStack: ['Python', 'TensorFlow', 'FastAPI'],
    timeline: '3 months',
    constraints: ['HIPAA_compliance', 'real_time_processing']
  }
};

const result = await openaiClient.synthesize(synthesisCall);
// Outputs structured plan with tasks, code, and tests
```

## Integration with Workflows

### GitHub Action Integration
```yaml
# .github/workflows/agent-research.yml
name: Agent Research
on:
  workflow_dispatch:
    inputs:
      topic:
        description: "Research topic"
        required: true
      goal:
        description: "Synthesis goal"
        required: true
        default: "build_plan"

jobs:
  research:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      
      # Perplexity Research
      - name: Research with Perplexity
        env:
          PPLX_API_KEY: ${{ secrets.PPLX_API_KEY }}
        run: |
          npx ts-node scripts/research.ts "${{ github.event.inputs.topic }}"
      
      # OpenAI Synthesis
      - name: Synthesize with OpenAI
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          npx ts-node scripts/synthesize.ts \
            --goal "${{ github.event.inputs.goal }}" \
            --input RESEARCH.md
      
      # Generate documentation
      - name: Generate Documentation
        run: |
          npx ts-node scripts/generate-docs.ts \
            --topic "${{ github.event.inputs.topic }}" \
            --goal "${{ github.event.inputs.goal }}"
      
      # Check for external APIs and generate setup
      - name: Generate Setup Files
        run: |
          npx ts-node scripts/generate-setup.ts
      
      # Commit results
      - name: Commit Results
        run: |
          git config user.name ci
          git config user.email ci@users.noreply.github.com
          git add .
          git commit -m "Agent research: ${{ github.event.inputs.topic }}"
          git push
```
