# Observability

- On **API failure**: continue workflow and post a **concise** PR comment with status and next steps
- **Mask secrets** in logs
- Keep **research/synthesis diffs small**; roll additional chunks to follow-up commits

## Observability Implementation

### API Failure Handling
```typescript
// assistant/observability/api-failure-handler.ts
export class APIFailureHandler {
  private githubToken: string;
  private repoOwner: string;
  private repoName: string;

  constructor(githubToken: string, repoOwner: string, repoName: string) {
    this.githubToken = githubToken;
    this.repoOwner = repoOwner;
    this.repoName = repoName;
  }

  async handleAPIFailure(
    error: Error,
    context: {
      prNumber?: number;
      workflow?: string;
      step?: string;
    }
  ): Promise<void> {
    console.error(`API failure in ${context.step}:`, error.message);
    
    // Continue workflow - don't fail the entire process
    if (context.prNumber) {
      await this.postPRComment(context.prNumber, {
        status: 'partial_success',
        error: error.message,
        nextSteps: this.getNextSteps(error, context)
      });
    }
  }

  private async postPRComment(prNumber: number, status: {
    status: string;
    error: string;
    nextSteps: string[];
  }): Promise<void> {
    const comment = `## 🔄 Workflow Status: ${status.status}

**Error**: ${status.error}

**Next Steps**:
${status.nextSteps.map(step => `- ${step}`).join('\n')}

---
*Automated status update - ${new Date().toISOString()}*`;

    try {
      await fetch(`https://api.github.com/repos/${this.repoOwner}/${this.repoName}/issues/${prNumber}/comments`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.githubToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ body: comment })
      });
    } catch (error) {
      console.error('Failed to post PR comment:', error);
    }
  }

  private getNextSteps(error: Error, context: any): string[] {
    if (error.message.includes('rate limit')) {
      return [
        'Wait for rate limit to reset',
        'Retry the workflow in 1 hour',
        'Consider using different API keys'
      ];
    }
    
    if (error.message.includes('authentication')) {
      return [
        'Check API key configuration',
        'Verify token permissions',
        'Update secrets in repository settings'
      ];
    }
    
    if (error.message.includes('network')) {
      return [
        'Check network connectivity',
        'Retry the workflow',
        'Verify API endpoint availability'
      ];
    }
    
    return [
      'Review error logs',
      'Check API service status',
      'Retry the workflow'
    ];
  }
}
```

### Secret Masking in Logs
```typescript
// assistant/observability/secret-masker.ts
export class SecretMasker {
  private static secretPatterns = [
    /(?:password|pwd|pass)\s*[:=]\s*['"]?([^'"\s]+)['"]?/gi,
    /(?:token|key|secret)\s*[:=]\s*['"]?([^'"\s]+)['"]?/gi,
    /(?:api_key|apikey)\s*[:=]\s*['"]?([^'"\s]+)['"]?/gi,
    /(?:private_key|privatekey)\s*[:=]\s*['"]?([^'"\s]+)['"]?/gi,
    /(?:secret_key|secretkey)\s*[:=]\s*['"]?([^'"\s]+)['"]?/gi,
    /Bearer\s+([a-zA-Z0-9_-]+)/gi,
    /Authorization:\s*Bearer\s+([a-zA-Z0-9_-]+)/gi
  ];

  static maskSecrets(text: string): string {
    let maskedText = text;
    
    this.secretPatterns.forEach(pattern => {
      maskedText = maskedText.replace(pattern, (match, secret) => {
        const maskedSecret = secret.length > 8 
          ? `${secret.substring(0, 4)}***${secret.substring(secret.length - 4)}`
          : '***';
        return match.replace(secret, maskedSecret);
      });
    });
    
    return maskedText;
  }

  static logSafely(message: string, data?: any): void {
    const safeMessage = this.maskSecrets(message);
    const safeData = data ? this.maskSecrets(JSON.stringify(data)) : undefined;
    
    console.log(safeMessage, safeData);
  }

  static createSafeLogger(context: string) {
    return {
      info: (message: string, data?: any) => {
        this.logSafely(`[${context}] INFO: ${message}`, data);
      },
      error: (message: string, error?: Error) => {
        const safeMessage = this.maskSecrets(message);
        const safeError = error ? {
          message: this.maskSecrets(error.message),
          stack: this.maskSecrets(error.stack || '')
        } : undefined;
        
        console.error(`[${context}] ERROR: ${safeMessage}`, safeError);
      },
      warn: (message: string, data?: any) => {
        this.logSafely(`[${context}] WARN: ${message}`, data);
      }
    };
  }
}
```

### Diff Management
```typescript
// assistant/observability/diff-manager.ts
export class DiffManager {
  private static MAX_DIFF_SIZE = 1000; // characters
  private static MAX_COMMIT_SIZE = 5000; // characters

  static shouldSplitDiff(content: string): boolean {
    return content.length > this.MAX_DIFF_SIZE;
  }

  static splitContent(content: string): {
    initial: string;
    followUp: string[];
  } {
    if (!this.shouldSplitDiff(content)) {
      return { initial: content, followUp: [] };
    }

    const lines = content.split('\n');
    const initialLines = lines.slice(0, Math.floor(lines.length / 2));
    const followUpLines = lines.slice(Math.floor(lines.length / 2));

    return {
      initial: initialLines.join('\n'),
      followUp: this.chunkContent(followUpLines.join('\n'))
    };
  }

  private static chunkContent(content: string): string[] {
    const chunks: string[] = [];
    const lines = content.split('\n');
    
    let currentChunk: string[] = [];
    let currentSize = 0;
    
    for (const line of lines) {
      if (currentSize + line.length > this.MAX_DIFF_SIZE && currentChunk.length > 0) {
        chunks.push(currentChunk.join('\n'));
        currentChunk = [];
        currentSize = 0;
      }
      
      currentChunk.push(line);
      currentSize += line.length;
    }
    
    if (currentChunk.length > 0) {
      chunks.push(currentChunk.join('\n'));
    }
    
    return chunks;
  }

  static createCommitStrategy(content: string): {
    strategy: 'single' | 'split';
    commits: Array<{
      message: string;
      content: string;
      isFollowUp: boolean;
    }>;
  } {
    if (content.length <= this.MAX_COMMIT_SIZE) {
      return {
        strategy: 'single',
        commits: [{
          message: 'AI: research and synthesis',
          content,
          isFollowUp: false
        }]
      };
    }

    const { initial, followUp } = this.splitContent(content);
    
    const commits = [
      {
        message: 'AI: initial research and synthesis',
        content: initial,
        isFollowUp: false
      },
      ...followUp.map((chunk, index) => ({
        message: `AI: additional research findings (${index + 1}/${followUp.length})`,
        content: chunk,
        isFollowUp: true
      }))
    ];

    return {
      strategy: 'split',
      commits
    };
  }
}
```

### Workflow Status Tracking
```typescript
// assistant/observability/workflow-tracker.ts
export class WorkflowTracker {
  private logger: ReturnType<typeof SecretMasker.createSafeLogger>;
  private failureHandler: APIFailureHandler;

  constructor(githubToken: string, repoOwner: string, repoName: string) {
    this.logger = SecretMasker.createSafeLogger('WorkflowTracker');
    this.failureHandler = new APIFailureHandler(githubToken, repoOwner, repoName);
  }

  async trackStep(
    stepName: string,
    operation: () => Promise<any>,
    context: { prNumber?: number; workflow?: string }
  ): Promise<any> {
    this.logger.info(`Starting step: ${stepName}`);
    
    try {
      const result = await operation();
      this.logger.info(`Step completed: ${stepName}`);
      return result;
    } catch (error) {
      this.logger.error(`Step failed: ${stepName}`, error as Error);
      
      // Handle API failures gracefully
      await this.failureHandler.handleAPIFailure(error as Error, {
        ...context,
        step: stepName
      });
      
      // Continue workflow - don't throw
      return null;
    }
  }

  async trackResearch(
    topic: string,
    context: { prNumber?: number }
  ): Promise<string | null> {
    return this.trackStep('research', async () => {
      const research = await this.performResearch(topic);
      return research;
    }, context);
  }

  async trackSynthesis(
    inputFile: string,
    context: { prNumber?: number }
  ): Promise<string | null> {
    return this.trackStep('synthesis', async () => {
      const synthesis = await this.performSynthesis(inputFile);
      return synthesis;
    }, context);
  }

  private async performResearch(topic: string): Promise<string> {
    // Implementation for research
    throw new Error('Research implementation needed');
  }

  private async performSynthesis(inputFile: string): Promise<string> {
    // Implementation for synthesis
    throw new Error('Synthesis implementation needed');
  }
}
```

### GitHub Actions Integration
```yaml
# .github/workflows/observable-research.yml
name: Observable AI Research
on:
  workflow_dispatch:
    inputs:
      topic:
        description: "Research topic"
        required: true

jobs:
  research:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
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

      - name: Research with observability
        env:
          PPLX_API_KEY: ${{ secrets.PPLX_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          npx ts-node scripts/observable-research.ts "${{ github.event.inputs.topic }}"

      - name: Handle failures gracefully
        if: failure()
        run: |
          echo "Workflow failed, but continuing..."
          # Post status comment to PR if exists
          npx ts-node scripts/post-failure-status.ts
```

### Observable Research Script
```typescript
// scripts/observable-research.ts
import { WorkflowTracker } from '../assistant/observability/workflow-tracker';
import { DiffManager } from '../assistant/observability/diff-manager';
import { writeFileSync } from 'fs';

async function main() {
  const topic = process.argv[2];
  if (!topic) {
    console.error('Usage: npm run observable-research <topic>');
    process.exit(1);
  }

  const tracker = new WorkflowTracker(
    process.env.GITHUB_TOKEN!,
    process.env.GITHUB_REPOSITORY_OWNER!,
    process.env.GITHUB_REPOSITORY!.split('/')[1]
  );

  const context = {
    prNumber: process.env.PR_NUMBER ? parseInt(process.env.PR_NUMBER) : undefined,
    workflow: 'observable-research'
  };

  try {
    // Track research step
    const research = await tracker.trackResearch(topic, context);
    
    if (research) {
      // Check if we need to split the diff
      const strategy = DiffManager.createCommitStrategy(research);
      
      if (strategy.strategy === 'single') {
        writeFileSync('RESEARCH.md', research);
        console.log('Research saved to RESEARCH.md');
      } else {
        // Handle split commits
        console.log('Large research content detected, splitting into multiple commits');
        
        // Save initial content
        writeFileSync('RESEARCH.md', strategy.commits[0].content);
        
        // Save follow-up chunks
        strategy.commits.slice(1).forEach((commit, index) => {
          writeFileSync(`RESEARCH-${index + 1}.md`, commit.content);
        });
      }
    }

    // Track synthesis step
    const synthesis = await tracker.trackSynthesis('RESEARCH.md', context);
    
    if (synthesis) {
      const strategy = DiffManager.createCommitStrategy(synthesis);
      
      if (strategy.strategy === 'single') {
        writeFileSync('SYNTHESIS.md', synthesis);
        console.log('Synthesis saved to SYNTHESIS.md');
      } else {
        console.log('Large synthesis content detected, splitting into multiple commits');
        
        writeFileSync('SYNTHESIS.md', strategy.commits[0].content);
        
        strategy.commits.slice(1).forEach((commit, index) => {
          writeFileSync(`SYNTHESIS-${index + 1}.md`, commit.content);
        });
      }
    }

    console.log('Observable research workflow completed');
  } catch (error) {
    console.error('Workflow failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
```

### Status Comment Templates
```typescript
// assistant/observability/status-templates.ts
export class StatusTemplates {
  static getPartialSuccessTemplate(error: string, nextSteps: string[]): string {
    return `## 🔄 Workflow Status: Partial Success

**Issue**: ${error}

**Next Steps**:
${nextSteps.map(step => `- ${step}`).join('\n')}

**Status**: Workflow continued with limited functionality

---
*Automated status update - ${new Date().toISOString()}*`;
  }

  static getFailureTemplate(error: string, nextSteps: string[]): string {
    return `## ❌ Workflow Status: Failed

**Error**: ${error}

**Next Steps**:
${nextSteps.map(step => `- ${step}`).join('\n')}

**Status**: Workflow failed, manual intervention required

---
*Automated status update - ${new Date().toISOString()}*`;
  }

  static getSuccessTemplate(summary: string): string {
    return `## ✅ Workflow Status: Success

**Summary**: ${summary}

**Status**: All steps completed successfully

---
*Automated status update - ${new Date().toISOString()}*`;
  }
}
```

### Log Configuration
```typescript
// assistant/observability/logger-config.ts
export class LoggerConfig {
  static configureLogging(): void {
    // Configure console logging with secret masking
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;

    console.log = (...args: any[]) => {
      const maskedArgs = args.map(arg => 
        typeof arg === 'string' ? SecretMasker.maskSecrets(arg) : arg
      );
      originalLog(...maskedArgs);
    };

    console.error = (...args: any[]) => {
      const maskedArgs = args.map(arg => 
        typeof arg === 'string' ? SecretMasker.maskSecrets(arg) : arg
      );
      originalError(...maskedArgs);
    };

    console.warn = (...args: any[]) => {
      const maskedArgs = args.map(arg => 
        typeof arg === 'string' ? SecretMasker.maskSecrets(arg) : arg
      );
      originalWarn(...maskedArgs);
    };
  }
}
```

## Usage Examples

### Basic Observability
```typescript
// Example usage in research script
import { WorkflowTracker } from './assistant/observability/workflow-tracker';
import { LoggerConfig } from './assistant/observability/logger-config';

// Configure logging
LoggerConfig.configureLogging();

// Create tracker
const tracker = new WorkflowTracker(
  process.env.GITHUB_TOKEN!,
  process.env.GITHUB_REPOSITORY_OWNER!,
  process.env.GITHUB_REPOSITORY!.split('/')[1]
);

// Track workflow steps
await tracker.trackResearch('AI Safety', { prNumber: 123 });
await tracker.trackSynthesis('RESEARCH.md', { prNumber: 123 });
```

### Error Handling
```typescript
// Example of graceful error handling
try {
  const result = await apiCall();
  console.log('API call successful');
} catch (error) {
  // Log safely without exposing secrets
  SecretMasker.logSafely('API call failed', { error: error.message });
  
  // Continue workflow
  console.log('Continuing with fallback...');
}
```

### Diff Management
```typescript
// Example of managing large diffs
const content = 'Very long research content...';
const strategy = DiffManager.createCommitStrategy(content);

if (strategy.strategy === 'split') {
  console.log('Splitting content into multiple commits');
  strategy.commits.forEach((commit, index) => {
    console.log(`Commit ${index + 1}: ${commit.message}`);
  });
}
```
