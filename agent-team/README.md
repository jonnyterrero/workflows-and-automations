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
python scripts/deploy_agents.py              # dry run
python scripts/deploy_agents.py --execute
```

`dist/skill_ids.json` and `dist/agent_ids.json` are gitignored — each Anthropic workspace gets its own IDs. Rebuild ZIPs with `build_skills.py`; do not commit them.

Pin accepted skill and agent versions in Console after your first acceptance pass. Avoid relying on `latest` in production.

### Cursor

After `sync_cursor_export.py`, run `install_cursor_local.py` on each machine (uses `%USERPROFILE%\.cursor` / `$HOME/.cursor` — no hardcoded user paths). Or open this repo as a workspace and point Cursor at `agent-team/cursor/`.

See [`cursor/INSTALL.md`](./cursor/INSTALL.md).

## Edit workflow

1. Change domain logic in `skills/<slug>/SKILL.md`.
2. Change shared policy in `skills/team-commons/SKILL.md`.
3. Change models/tools/roster in `agents/manifest.yaml`, then run `generate_agent_templates.py`.
4. Refresh Cursor export with `sync_cursor_export.py`.
5. Commit and push; pull on the other machine and re-run install.

## Security

Read `docs/SECURITY.md` and `AUDIT_REPORT.md`. High-stakes agents (legal, tax, trading, investment) require current sources and explicit uncertainty. No execution of trades, filings, or production writes without user authorization.
