Why upload failed before
------------------------
The Git repo root only has .claude-plugin/marketplace.json (marketplace manifest).
Each real plugin lives under .claude/plugins/<name>/ and has .claude-plugin/plugin.json.

This folder is the repomix-MCP plugin only (recommended first). It includes:
  .claude-plugin/plugin.json
  .mcp.json

Optional: also upload repomix-commands and repomix-explorer from sibling folders in this workspace.

Official install: /plugin marketplace add yamadashy/repomix
Docs: https://github.com/yamadashy/repomix
