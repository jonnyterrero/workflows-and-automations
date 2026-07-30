#!/usr/bin/env python3
"""Install versioned agent-team/cursor exports into the local Cursor user dirs.

Uses HOME / USERPROFILE — never hardcodes a machine-specific absolute path.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_SKILLS = ROOT / "cursor" / "skills"
SRC_AGENTS = ROOT / "cursor" / "agents"


def cursor_home() -> Path:
    base = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not base:
        raise SystemExit("Neither USERPROFILE nor HOME is set")
    return Path(base) / ".cursor"


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
    ap = argparse.ArgumentParser(description="Install agent-team Cursor exports locally")
    ap.add_argument("--dry-run", action="store_true", help="Print targets without copying")
    ap.add_argument(
        "--skills-only",
        action="store_true",
        help="Install skills only",
    )
    ap.add_argument(
        "--agents-only",
        action="store_true",
        help="Install agents only",
    )
    args = ap.parse_args()
    home = cursor_home()
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
