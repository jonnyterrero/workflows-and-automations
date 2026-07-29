# Cursor install (laptop + desktop)

Versioned exports live in this folder (`skills/`, `agents/`). Source of truth remains `../skills` and `../agents/manifest.yaml`.

## Refresh export

From `agent-team/`:

```bash
python scripts/sync_cursor_export.py
```

## Install on this machine

```bash
python scripts/install_cursor_local.py --dry-run   # preview
python scripts/install_cursor_local.py             # copy into ~/.cursor
```

On Windows this uses `%USERPROFILE%\.cursor\skills` and `%USERPROFILE%\.cursor\agents`.
On macOS/Linux it uses `$HOME/.cursor/skills` and `$HOME/.cursor/agents`.

Restart Cursor or start a new agent chat so skills/agents are picked up.

## Dual-machine sync

1. Push `workflows-and-automations` from the machine you edited on.
2. Pull on the other machine.
3. Run `sync_cursor_export.py` (if exports were not committed) then `install_cursor_local.py`.

Committed `cursor/` exports mean you can install immediately after pull without regenerating, as long as you did not change SoT skills without re-exporting.
