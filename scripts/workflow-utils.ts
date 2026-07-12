/**
 * Shared utilities for GitHub Actions workflows
 * Provides consistent error handling, logging, and git operations
 */

export interface WorkflowConfig {
  actor: string;
  repository: string;
  actionsPat?: string;
  githubToken?: string;
}

export class WorkflowLogger {
  private prefix: string;

  constructor(prefix: string = '[WORKFLOW]') {
    this.prefix = prefix;
  }

  info(message: string): void {
    console.log(`${this.prefix} ✅ ${message}`);
  }

  warn(message: string): void {
    console.warn(`${this.prefix} ⚠️  ${message}`);
  }

  error(message: string, error?: unknown): void {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error(`${this.prefix} ❌ ${message}`);
    if (error) {
      console.error(`${this.prefix} 🔍 Details: ${errorMsg}`);
    }
  }

  step(name: string): void {
    console.log(`\n${this.prefix} 📋 Step: ${name}`);
  }

  progress(message: string): void {
    console.log(`${this.prefix} ⏳ ${message}`);
  }
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  try {
    return JSON.stringify(error);
  } catch {
    return String(error);
  }
}

export function validateRequiredEnv(envVar: string, value: string | undefined, required: boolean = true): void {
  if (required && !value) {
    throw new Error(`Required environment variable ${envVar} is not set`);
  }
  if (value) {
    console.log(`✅ ${envVar} is set (${value.substring(0, 8)}...)`);
  }
}

export interface GitConfig {
  actor: string;
  actionsPat: string;
  repository: string;
}

export function configureGit(config: GitConfig): void {
  const { execSync } = require('child_process');
  
  // Clear any existing credentials
  execSync('git config --global --unset-all http.https://github.com/.extraheader || true', { stdio: 'inherit' });
  execSync('git config --local --unset-all http.https://github.com/.extraheader || true', { stdio: 'inherit' });
  
  // Set user info
  execSync(`git config --global user.name "${config.actor}"`, { stdio: 'inherit' });
  execSync(`git config --global user.email "${config.actor}@users.noreply.github.com"`, { stdio: 'inherit' });
  
  // Configure remote with PAT
  execSync('git remote remove origin || true', { stdio: 'inherit' });
  execSync(
    `git remote add origin https://${config.actor}:${config.actionsPat}@github.com/${config.repository}.git`,
    { stdio: 'inherit' }
  );
}

export function createTimestampedBranch(prefix: string): string {
  const date = new Date();
  const timestamp = date.toISOString()
    .replace(/T/, '-')
    .replace(/\..+/, '')
    .replace(/:/g, '');
  return `${prefix}-${timestamp}`;
}

