// Combine TS (Istanbul) + Python (coverage.py XML) coverage into one README badge.
import fs from "fs";

const README = "README.md";
const tsSummary = "packages/ts/coverage/coverage-summary.json";
const pyXml = "packages/py/coverage.xml";

function readTs() {
  try {
    const data = JSON.parse(fs.readFileSync(tsSummary, "utf8"));
    const lines = data.total?.lines;
    if (!lines) return null;
    return { covered: lines.covered ?? 0, total: lines.total ?? 0 };
  } catch {
    return null;
  }
}

function readPy() {
  try {
    const xml = fs.readFileSync(pyXml, "utf8");
    // coverage.py XML has root <coverage lines-valid="X" lines-covered="Y" ...>
    const validMatch = xml.match(/lines-valid="(\d+)"/);
    const covMatch = xml.match(/lines-covered="(\d+)"/);
    if (!validMatch || !covMatch) return null;
    const total = parseInt(validMatch[1], 10);
    const covered = parseInt(covMatch[1], 10);
    return { covered, total };
  } catch {
    return null;
  }
}

function combine(a, b) {
  const parts = [a, b].filter(Boolean);
  if (parts.length === 0) return null;
  const covered = parts.reduce((s, p) => s + p.covered, 0);
  const total = parts.reduce((s, p) => s + p.total, 0);
  if (total === 0) return 0;
  return Math.round((covered / total) * 100);
}

function colorFor(pct) {
  if (pct >= 90) return "brightgreen";
  if (pct >= 80) return "green";
  if (pct >= 70) return "yellowgreen";
  if (pct >= 60) return "yellow";
  if (pct >= 50) return "orange";
  return "lightgrey";
}

const ts = readTs();
const py = readPy();
const pct = combine(ts, py);

if (pct == null) {
  console.log("Coverage not found; leaving README unchanged.");
  process.exit(0);
}

const color = colorFor(pct);
const md = fs.readFileSync(README, "utf8");

// Ensure there is a badge stub to replace; if not, insert one under the title.
let updated = md;
const badgeRe = /!\[Coverage\]\(https:\/\/img\.shields\.io\/badge\/coverage-[^)]+\.svg\)/;
const newBadge = `![Coverage](https://img.shields.io/badge/coverage-${pct}%25-${color}.svg)`;

if (badgeRe.test(md)) {
  updated = md.replace(badgeRe, newBadge);
} else {
  updated = md.replace(/^#\s+[^\n]+\n?/, (h) => `${h}${newBadge}\n`);
}

if (updated !== md) {
  fs.writeFileSync(README, updated);
  console.log(`Updated README coverage badge to ${pct}%`);
} else {
  console.log("README coverage badge already up-to-date.");
}
