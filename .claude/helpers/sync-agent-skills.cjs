#!/usr/bin/env node
/**
 * Sync the canonical agent-team skills into the project skill directory.
 *
 * agents/agent-team/skills/<name>/SKILL.md is the source of truth; .claude/skills/ is
 * what Claude Code actually discovers at session start. This copies the former
 * onto the latter so a session always loads the committed version rather than
 * whatever an installer left on one machine.
 *
 * Runs on SessionStart. No dependencies, no network, never deletes anything
 * outside the skill folders it owns.
 */
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const SRC = path.join(REPO_ROOT, 'agents', 'agent-team', 'skills');
const DEST = path.join(REPO_ROOT, '.claude', 'skills');

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else if (entry.isFile()) out.push(full);
  }
  return out;
}

function main() {
  if (!fs.existsSync(SRC)) {
    console.log('[agent-skills] no agents/agent-team/skills directory — nothing to sync');
    return;
  }

  let copied = 0;
  let unchanged = 0;
  for (const file of walk(SRC)) {
    const rel = path.relative(SRC, file);
    const target = path.join(DEST, rel);
    const data = fs.readFileSync(file);
    if (fs.existsSync(target) && fs.readFileSync(target).equals(data)) {
      unchanged += 1;
      continue;
    }
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, data);
    copied += 1;
  }

  const skills = fs
    .readdirSync(SRC, { withFileTypes: true })
    .filter((e) => e.isDirectory()).length;
  console.log(
    `[agent-skills] ${skills} agent skills available` +
      (copied ? ` (${copied} refreshed, ${unchanged} current)` : ' (all current)')
  );
}

try {
  main();
} catch (err) {
  // A sync failure must never block a session from starting.
  console.log(`[agent-skills] sync skipped: ${err.message}`);
}
