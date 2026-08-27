# Jonny Agent Team — Static Publication Audit

**Audit date:** 2026-07-28  
**Original scope:** 13 `.skill.md` files, one raw team ZIP, one packaging script, one API upload script.  
**Result:** **Not publish-ready as submitted; release-candidate after the corrections in this package.** Runtime acceptance testing in Claude Console/API is still required.

## Executive finding

The original files are concise, readable, and generally strong role descriptions. Their frontmatter names and descriptions meet the basic custom-skill limits. However, they are **skills**, not deployable Managed Agent definitions. A real Managed Agent also requires a model, system prompt, tools/permission policy, optional MCP servers, attached skill IDs, and an environment/session strategy.

## Original-package blockers

| Severity | Finding | Impact | Corrective action in v2 |
|---|---|---|---|
| Critical | No Managed Agent definitions | Uploading the Markdown files does not create a multi-agent team | Added 13 specialist agent YAML templates, deployment helper, and coordinator template |
| High | Combined router skill misrepresented as “all agents at once” | Creates one oversized skill, not isolated agents; broad trigger and context contention | Removed combined router from release path; individual skills plus true coordinator roster |
| High | No eval suite | Trigger accuracy, boundary behavior, and output quality are unmeasured | Added three baseline evals per skill plus routing matrix |
| High | High-stakes modules lack mandatory current-source workflow | Legal, tax, investment, trading, vendor/API answers may be stale or unsupported | Added jurisdiction/date/data timestamp, primary-source, uncertainty, and no-execution controls |
| High | Tool permissions are unspecified | Coding or MCP tools could run with overly broad defaults | Added least-privilege tool profiles and `always_ask` for Bash/write/edit where consequential |
| Medium | Role overlap is unresolved | Architect/SWE/Backend/Auditor and BME/Math may duplicate or contradict work | Added ownership and conflict-precedence matrix |
| Medium | Stale/personal context | BME file says graduating May 2026; multiple files hardcode personal employment/product details | Corrected academic context and moved personal facts out of general role logic |
| Medium | Packaging script drops future resources | It rebuilds ZIPs using only generated `SKILL.md` | Replacement packages each complete skill folder recursively |
| Medium | Upload helper uses manual file lists and is fragile on Windows/path-prefix rules | Skill upload can fail when folder path does not match frontmatter | Replacement uses official `anthropic.lib.files_from_dir` and matching directory names |
| Low | Mandatory output formats are too rigid | Simple questions can produce bloated reports | Revised output contracts adapt depth to task complexity |

## Skill-by-skill original assessment

| Skill | Original status | Main issues corrected |
|---|---|---|
| Architect | Strong | Clarified design vs implementation ownership; added vendor verification and authorization boundary |
| Backend Dev | Strong | Added rollback, least privilege, privacy, version detection, and production-write confirmation |
| BME Tutor | Needs correction | Stale graduation context, missing Physics minor, academic-integrity/lab-data controls, stronger research method |
| Business Consultant | Good | Added evidence hierarchy, regulated-claim risk, and measurable hypothesis discipline |
| Code Auditor | Strong | Added scope limitations, threat model, exact-evidence rules, current CVE verification, defensive-only boundary |
| CPA-CFO | Good | Added basis/reconciliation, PII controls, no account actions, actual-vs-forecast separation |
| Investment Portfolio | Needs correction | Added timestamped current data, objective/risk inputs, source hierarchy, no execution/guarantees |
| Legal | Needs correction | Added jurisdiction/effective date, primary authorities, no final enforceability claims, privacy controls |
| Math Tutor | Strong | Reduced rigid output requirements, clarified BME boundary, added tool-as-verifier rule |
| Senior SWE | Strong | Removed false “10+ YOE” claim, removed hardcoded runtime assumptions, added repo detection and write gates |
| Tax Auditor | Needs correction | Added tax year/jurisdiction, official source hierarchy, PII restrictions, no filing/evasion |
| Trading | Needs correction | Added timestamp/data status, no leverage encouragement/execution, hypothetical vs live separation |
| YouTube | Good | Added copyright, disclosure, synthetic-media, regulated-claim, and analytics-freshness controls |

## Script audit

### Original `compress_skills.py`
- Syntax-valid.
- Individual ZIP layout logic was directionally correct.
- The combined skill path is not a real multi-agent deployment and conflicts with focused-skill guidance.
- The script rebuilds each upload from only `SKILL.md`, so future `scripts/`, `references/`, and `assets/` would be lost.
- Validation did not fully enforce folder/name matching, reserved words, secret scanning, or recommended size limits.

### Original `upload_skills_api.py`
- Syntax-valid but not runtime-tested because no API key/SDK was available in the audit environment.
- It manually extracts ZIPs and passes a list of local `Path` objects. The current official Python pattern uses `anthropic.lib.files_from_dir`, which also avoids known path-prefix/Windows issues.
- It creates duplicates on repeated runs and has no version/update manifest.

## Release package contents

- `skills/` — 13 revised, focused Agent Skills.
- `dist/skills/` — individually uploadable ZIPs with SHA-256 checksums.
- `agents/` — Managed Agent YAML templates with current model IDs, attached-skill placeholders, and permission policies.
- `agents/coordinator.template.yaml` — true Managed Agents coordinator roster template.
- `evals/` — baseline positive, boundary, and freshness evals for every skill.
- `docs/ROUTING_MATRIX.md` — ownership and conflict precedence.
- `scripts/build_skills.py` — validates and packages full skill folders.
- `scripts/upload_skills.py` — dry-run-first skill uploader/versioner.
- `scripts/deploy_agents.py` — dry-run-first specialist and coordinator creator.

## Remaining acceptance gates

This package is statically valid and internally consistent, but it should not be labeled production-certified until you:
1. Upload each skill and run its three baseline evals.
2. Add at least five realistic prompts and two adversarial prompts per high-risk skill.
3. Confirm every agent uses the intended tool permissions in Console.
4. Attach only required MCP servers and vault credentials.
5. Run routing tests through the coordinator and inspect subagent event traces.
6. Pin accepted skill and agent versions instead of using `latest` in production.
7. Add a license and public privacy statement if you distribute these outside your private workspace.
