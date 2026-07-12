# CI / Automation

## Workflows
- **`ai-research.yml`**: manual dispatch with `topic` → RESEARCH + SYNTHESIS + PR
- **`nightly-research.yml`**: scheduled cron; append dated briefs

## Required Checks
- **Lint** (TS/ESLint, Py/ruff)
- **Tests** (vitest/jest, pytest)
- **Typecheck** (tsc --noEmit)

## PR Standards
- Include **SYNTHESIS.md** as PR body
- Link issues with **`Fixes #<id>`** where valid

## CI/CD Implementation

### GitHub Actions Workflows

#### AI Research Workflow
```yaml
# .github/workflows/ai-research.yml
name: AI Research
on:
  workflow_dispatch:
    inputs:
      topic:
        description: "Research topic"
        required: true
        type: string
      branch:
        description: "Target branch"
        required: true
        default: "ai/research-${{ github.run_id }}"
        type: string

jobs:
  research:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Lint TypeScript
        run: npm run lint

      - name: Type check
        run: npm run typecheck

      - name: Run tests
        run: npm test

      - name: Research with Perplexity
        env:
          PPLX_API_KEY: ${{ secrets.PPLX_API_KEY }}
        run: |
          npx ts-node scripts/research.ts "${{ github.event.inputs.topic }}" > RESEARCH.md

      - name: Synthesize with OpenAI
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          npx ts-node scripts/synthesize.ts RESEARCH.md > SYNTHESIS.md

      - name: Create branch and commit
        run: |
          git config user.name "AI Research Bot"
          git config user.email "ai-research@users.noreply.github.com"
          git switch -c "${{ github.event.inputs.branch }}"
          git add RESEARCH.md SYNTHESIS.md
          git commit -m "AI: research & synthesis for ${{ github.event.inputs.topic }}"
          git push --set-upstream origin "${{ github.event.inputs.branch }}"

      - name: Open PR
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr create \
            --title "AI: ${{ github.event.inputs.topic }}" \
            --body-file SYNTHESIS.md \
            --base main \
            --head "${{ github.event.inputs.branch }}"
```

#### Nightly Research Workflow
```yaml
# .github/workflows/nightly-research.yml
name: Nightly Research
on:
  schedule:
    - cron: "15 2 * * *"  # 02:15 UTC nightly
  workflow_dispatch:  # Allow manual trigger

jobs:
  nightly:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Lint TypeScript
        run: npm run lint

      - name: Type check
        run: npm run typecheck

      - name: Run tests
        run: npm test

      - name: Research & summarize
        env:
          PPLX_API_KEY: ${{ secrets.PPLX_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          # Create dated brief
          DATE=$(date -u +%F)
          npx ts-node scripts/research.ts "Open issues summary & related papers" \
            > docs/nightly/${DATE}.md
          
          # Create synthesis
          npx ts-node scripts/synthesize.ts docs/nightly/${DATE}.md \
            > docs/nightly/${DATE}-syn.md

      - name: Commit nightly research
        run: |
          git config user.name "AI Research Bot"
          git config user.email "ai-research@users.noreply.github.com"
          git add docs/nightly
          git commit -m "Nightly AI research - $(date -u +%F)" || exit 0
          git push
```

#### Quality Checks Workflow
```yaml
# .github/workflows/quality-checks.yml
name: Quality Checks
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Lint TypeScript
        run: npm run lint

      - name: Lint Python
        run: |
          pip install ruff
          ruff check school/ --fix

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run typecheck

  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run TypeScript tests
        run: npm test

      - name: Run Python tests
        run: |
          pip install pytest
          pytest school/ --cov=src
```

### Package.json Scripts
```json
{
  "scripts": {
    "lint": "eslint . --ext .ts,.js --fix",
    "lint:check": "eslint . --ext .ts,.js",
    "typecheck": "tsc --noEmit",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "test:watch": "vitest --watch",
    "quality": "npm run lint:check && npm run typecheck && npm test",
    "pre-commit": "npm run quality"
  }
}
```

### ESLint Configuration
```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "prefer-const": "error",
    "no-var": "error"
  },
  "ignorePatterns": ["dist/", "node_modules/", "*.js"]
}
```

### Prettier Configuration
```json
// .prettierrc
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "quoteProps": "as-needed",
  "trailingComma": "es5",
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```

### TypeScript Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noEmit": true
  },
  "include": ["scripts/**/*", "assistant/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

## PR Standards Implementation

### PR Template
```markdown
<!-- .github/pull_request_template.md -->
## Changes
[Description of changes made]

## Research
- [ ] Research conducted with Perplexity
- [ ] Synthesis generated with OpenAI
- [ ] Results documented in SYNTHESIS.md

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No breaking changes

## Quality Checks
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Code coverage maintained
- [ ] Documentation updated

## Issues
Fixes #<issue_number>

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No console.log statements
- [ ] No hardcoded secrets
```

### PR Body Generator
```typescript
// assistant/formatters/pr-body-generator.ts
export class PRBodyGenerator {
  static generatePRBody(synthesis: string, issueNumber?: number): string {
    const body = `## Changes
Based on AI research and synthesis:

${synthesis}

## Research
- [x] Research conducted with Perplexity
- [x] Synthesis generated with OpenAI
- [x] Results documented in SYNTHESIS.md

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No breaking changes

## Quality Checks
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Code coverage maintained
- [ ] Documentation updated

${issueNumber ? `## Issues
Fixes #${issueNumber}` : ''}

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No console.log statements
- [ ] No hardcoded secrets

---
*Generated by AI Research System on ${new Date().toISOString().split('T')[0]}*
`;

    return body;
  }
}
```

### Issue Linking
```typescript
// assistant/formatters/issue-linker.ts
export class IssueLinker {
  static linkIssues(prBody: string, issueNumbers: number[]): string {
    if (issueNumbers.length === 0) {
      return prBody;
    }

    const issueLinks = issueNumbers.map(num => `Fixes #${num}`).join('\n');
    
    return prBody.replace(
      '## Issues',
      `## Issues\n${issueLinks}`
    );
  }

  static extractIssueNumbers(text: string): number[] {
    const issuePattern = /#(\d+)/g;
    const matches = text.match(issuePattern);
    
    if (!matches) {
      return [];
    }

    return matches.map(match => parseInt(match.replace('#', '')));
  }
}
```

## Automation Scripts

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
# Run quality checks before committing

echo "Running pre-commit checks..."

# Check for secrets
if grep -r -E "(password|token|key|secret)\s*[:=]\s*['\"][^'\"]+['\"]" --exclude-dir=.git .; then
    echo "❌ Found potential secrets in code!"
    exit 1
fi

# Run linting
echo "Running linter..."
npm run lint:check
if [ $? -ne 0 ]; then
    echo "❌ Linting failed!"
    exit 1
fi

# Run type checking
echo "Running type check..."
npm run typecheck
if [ $? -ne 0 ]; then
    echo "❌ Type checking failed!"
    exit 1
fi

# Run tests
echo "Running tests..."
npm test
if [ $? -ne 0 ]; then
    echo "❌ Tests failed!"
    exit 1
fi

echo "✅ All pre-commit checks passed!"
exit 0
```

### Quality Check Script
```typescript
// scripts/quality-check.ts
import { execSync } from 'child_process';

interface QualityCheck {
  name: string;
  command: string;
  required: boolean;
}

const checks: QualityCheck[] = [
  {
    name: 'Linting',
    command: 'npm run lint:check',
    required: true
  },
  {
    name: 'Type Checking',
    command: 'npm run typecheck',
    required: true
  },
  {
    name: 'Tests',
    command: 'npm test',
    required: true
  },
  {
    name: 'Coverage',
    command: 'npm run test:coverage',
    required: false
  }
];

async function runQualityChecks(): Promise<void> {
  console.log('🔍 Running quality checks...\n');

  let allPassed = true;

  for (const check of checks) {
    try {
      console.log(`Running ${check.name}...`);
      execSync(check.command, { stdio: 'inherit' });
      console.log(`✅ ${check.name} passed\n`);
    } catch (error) {
      console.error(`❌ ${check.name} failed\n`);
      if (check.required) {
        allPassed = false;
      }
    }
  }

  if (allPassed) {
    console.log('🎉 All quality checks passed!');
    process.exit(0);
  } else {
    console.log('💥 Some quality checks failed!');
    process.exit(1);
  }
}

if (require.main === module) {
  runQualityChecks();
}
```

### Automated PR Creation
```typescript
// scripts/create-pr.ts
import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { PRBodyGenerator, IssueLinker } from '../assistant/formatters';

async function createPR(topic: string, issueNumber?: number): Promise<void> {
  try {
    // Read synthesis file
    const synthesis = readFileSync('SYNTHESIS.md', 'utf-8');
    
    // Generate PR body
    const prBody = PRBodyGenerator.generatePRBody(synthesis, issueNumber);
    
    // Create PR
    const prCommand = `gh pr create --title "AI: ${topic}" --body "${prBody}" --base main --head ai/research-${Date.now()}`;
    
    execSync(prCommand, { stdio: 'inherit' });
    
    console.log('✅ PR created successfully!');
  } catch (error) {
    console.error('❌ Failed to create PR:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  const topic = process.argv[2];
  const issueNumber = process.argv[3] ? parseInt(process.argv[3]) : undefined;
  
  if (!topic) {
    console.error('Usage: npm run create-pr <topic> [issue-number]');
    process.exit(1);
  }
  
  createPR(topic, issueNumber);
}
```

## Workflow Status Badges

### README Badges
```markdown
# AI Research Repository

[![CI/CD](https://github.com/username/ai-research-repo/workflows/Quality%20Checks/badge.svg)](https://github.com/username/ai-research-repo/actions)
[![Research](https://github.com/username/ai-research-repo/workflows/AI%20Research/badge.svg)](https://github.com/username/ai-research-repo/actions)
[![Nightly](https://github.com/username/ai-research-repo/workflows/Nightly%20Research/badge.svg)](https://github.com/username/ai-research-repo/actions)
[![Coverage](https://codecov.io/gh/username/ai-research-repo/branch/main/graph/badge.svg)](https://codecov.io/gh/username/ai-research-repo)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
```

### Status Checks
```yaml
# .github/workflows/status-checks.yml
name: Status Checks
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  status:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run all checks
        run: npm run quality

      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ All quality checks passed!'
            })
```
