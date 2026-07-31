# Jonny Claude Agent Team v2.1.0

Portable specialist skills + Managed Agents + Cursor exports. Lives in this repo so laptop and desktop stay in sync via git.

## Layout

| Path | Role |
|------|------|
| `skills/` | Source-of-truth Agent Skills (Claude + Cursor) |
| `skills/team-commons/` | Shared evidence, delegation, write-gate policy |
| `agents/manifest.yaml` | Single roster (models, tools, skills) |
| `agents/*.template.yaml` | Generated Managed Agent templates |
| `config/operator.context.yaml` | Optional personal academic context (no secrets) |
| `cursor/` | Versioned Cursor skills/agents export |
| `docs/ROUTING_MATRIX.md` | Ownership and conflict precedence |
| `docs/DEPLOYMENT_STATUS.md` | Live deploy state, MCP needs, kill switches, remaining steps |
| `evals/` | Baseline trigger/boundary/freshness fixtures |
| `scripts/` | Build, upload, deploy, generate, Cursor sync/install |

## Fast path (both machines)

```bash
cd agent-team
pip install -r requirements.txt
python scripts/generate_agent_templates.py   # after editing manifest.yaml
python scripts/build_skills.py
python scripts/sync_cursor_export.py
python scripts/install_cursor_local.py       # copies into ~/.cursor on this machine
```

### Claude Managed Agents

```bash
python scripts/upload_skills.py              # dry run
python scripts/upload_skills.py --execute    # needs ANTHROPIC_API_KEY

# Specialists first, so evals can gate the coordinator
python scripts/deploy_agents.py --phase specialists --execute
python scripts/run_evals.py --skill trading-agent
python scripts/deploy_agents.py --phase coordinator --execute

python scripts/pin_versions.py --execute     # move off skill version `latest`
```

`--phase all` (the default) creates specialists and coordinator in one pass and
skips the gate. `deploy_agents.py` has no reuse check, so running it on a second
machine creates a duplicate team — copy `dist/agent_ids.json` across instead.
`upload_skills.py` is safe to re-run; it matches on title and reports `reused`.

### Evals

```bash
python scripts/run_evals.py --skill deep-researcher
python scripts/run_evals.py --skill trading-agent --ids adversarial-1,realistic-4
python scripts/run_evals.py --coordinator          # team-routing.json
python scripts/run_evals.py --all
```

Sessions park silently on `always_ask` tools: the agent emits `agent.tool_use`,
the session goes idle, and nothing else happens until a `user.tool_confirmation`
event arrives. The runner answers those automatically (`--tool-policy deny` by
default) so suites finish unattended. It records responses into
`dist/eval_results/` rather than grading them — compare against `expected_output`.

### Local install

```bash
python scripts/install_cursor_local.py                    # -> ~/.cursor
python scripts/install_cursor_local.py --target claude    # -> ~/.claude/skills (this machine only)
python scripts/install_cursor_local.py --target project   # -> <repo>/.claude/skills (committed)
```

**Every new Claude Code session already loads the 15 skills** — the `project`
copy lives in `.claude/skills/`, is committed, and Claude Code discovers it on
open. Nothing has to be installed first, on any machine or in a web session.
A `SessionStart` hook (`.claude/helpers/sync-agent-skills.cjs`) re-copies
`agent-team/skills/` over that directory at start, so editing the canonical
source is enough — a stale project copy self-heals on the next session.

Run `--target project` yourself only when you want the refresh committed in the
same change as the source edit. `--target claude` is now optional; if you keep a
`~/.claude/skills/` copy it can drift from the repo, so prefer removing it.

`dist/skill_ids.json` and `dist/agent_ids.json` are gitignored — each Anthropic workspace gets its own IDs. Rebuild ZIPs with `build_skills.py`; do not commit them.

Pin accepted skill and agent versions in Console after your first acceptance pass. Avoid relying on `latest` in production.

After `sync_cursor_export.py`, run `install_cursor_local.py` on each machine (uses `%USERPROFILE%\.cursor` / `$HOME/.cursor` — no hardcoded user paths). Or open this repo as a workspace and point Cursor at `agent-team/cursor/`.

See [`cursor/INSTALL.md`](./cursor/INSTALL.md).

## Edit workflow

1. Change domain logic in `skills/<slug>/SKILL.md`.
2. Change shared policy in `skills/team-commons/SKILL.md`.
3. Change models/tools/roster in `agents/manifest.yaml`, then run `generate_agent_templates.py`.
4. Refresh Cursor export with `sync_cursor_export.py`, and the project copy with
   `install_cursor_local.py --target project`.
5. Commit and push; pulling on the other machine is enough for Claude Code —
   only Cursor still needs `install_cursor_local.py` re-run.

## Security

Read `docs/SECURITY.md` and `AUDIT_REPORT.md`. High-stakes agents (legal, tax, trading, investment) require current sources and explicit uncertainty. No execution of trades, filings, or production writes without user authorization.
