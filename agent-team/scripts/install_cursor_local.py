#!/usr/bin/env python3
"""Install agent-team skills into the local Cursor or Claude Code user dirs.

Uses HOME / USERPROFILE — never hardcodes a machine-specific absolute path.

  --target cursor  (default)  cursor/skills + cursor/agents -> ~/.cursor/
  --target claude              skills/                      -> ~/.claude/skills/

Cursor gets the adapted export; Claude Code gets the canonical `skills/`
folders, which are already in Claude Agent Skill format.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_SKILLS = ROOT / "cursor" / "skills"
SRC_AGENTS = ROOT / "cursor" / "agents"
SRC_CLAUDE_SKILLS = ROOT / "skills"


def user_home(dirname: str) -> Path:
    base = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not base:
        raise SystemExit("Neither USERPROFILE nor HOME is set")
    return Path(base) / dirname


def copy_tree(src: Path, dest: Path, *, dry_run: bool) -> int:
    if not src.exists():
        raise SystemExit(f"Missing export at {src}. Run sync_cursor_export.py first.")
    n = 0
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        target = dest / rel
        print(f"{'DRY ' if dry_run else ''}{path} -> {target}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description="Install agent-team skills locally")
    ap.add_argument("--dry-run", action="store_true", help="Print targets without copying")
    ap.add_argument(
        "--target",
        choices=("cursor", "claude"),
        default="cursor",
        help="Install into ~/.cursor (default) or ~/.claude/skills",
    )
    ap.add_argument(
        "--skills-only",
        action="store_true",
        help="Install skills only (cursor target)",
    )
    ap.add_argument(
        "--agents-only",
        action="store_true",
        help="Install agents only (cursor target)",
    )
    args = ap.parse_args()

    if args.target == "claude":
        skills_dest = user_home(".claude") / "skills"
        print(f"Claude Code skills: {skills_dest}")
        total = copy_tree(SRC_CLAUDE_SKILLS, skills_dest, dry_run=args.dry_run)
        print(f"{'Would install' if args.dry_run else 'Installed'} {total} files")
        return

    home = user_home(".cursor")
    skills_dest = home / "skills"
    agents_dest = home / "agents"
    print(f"Cursor home: {home}")

    total = 0
    if not args.agents_only:
        total += copy_tree(SRC_SKILLS, skills_dest, dry_run=args.dry_run)
    if not args.skills_only:
        total += copy_tree(SRC_AGENTS, agents_dest, dry_run=args.dry_run)
    print(f"{'Would install' if args.dry_run else 'Installed'} {total} files")


if __name__ == "__main__":
    main()
