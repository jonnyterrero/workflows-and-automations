# Ruflo / Claude Flow plugin (local upload folder)

This folder is assembled for upload as a Claude plugin (Claude Code / Claude app).

## Contents
- `.claude-plugin/` — manifest (`plugin.json`), marketplace metadata, docs
- `commands/` — slash command definitions (from the repo `.claude/commands`)
- `agents/` — agent definitions (from the repo `.claude/agents`)
- `hooks/hooks.json` — hook configuration
- `.claude/skills/` — bundled skills (optional; matches upstream layout)

Zip this folder (see ZIP note below) and use the app's plugin upload flow.

## ZIP
- Select the **inner** folder contents, or zip **claude-ruflo-plugin-upload** itself.
- On Windows: right-click the folder → Compress to ZIP, or:
  `Compress-Archive -Path '...\\claude-ruflo-plugin-upload\\*' -DestinationPath '...\\claude-ruflo-plugin.zip'`

After install, restart the app. MCP tools may still require `npx claude-flow@alpha` / Node per `plugin.json`.
