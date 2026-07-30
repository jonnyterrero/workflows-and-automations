#!/usr/bin/env python3
"""Offline tests for fetch_repo_activity parsing.

The network paths cannot be exercised in sandboxes that block github.com, so the
feed parsing, windowing, and summary cleanup are tested against a fixture that
mirrors GitHub's real Atom shape.

Run: python3 .claude/skills/content-engine/scripts/test_fetch_repo_activity.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_repo_activity as mod  # noqa: E402

SCRIPT = Path(__file__).resolve().parent / "fetch_repo_activity.py"

RELEASES_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Release notes from modelcontextprotocol</title>
  <entry>
    <id>tag:github.com,2008:Repository/1/2026-07-28</id>
    <updated>2026-07-28T16:47:49Z</updated>
    <link rel="alternate" type="text/html" href="https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28"/>
    <title>2026-07-28</title>
    <content type="html">&lt;p&gt;Stable release of the &lt;strong&gt;2026-07-28&lt;/strong&gt; revision.&lt;/p&gt;</content>
    <author><name>example-maintainer</name></author>
  </entry>
  <entry>
    <id>tag:github.com,2008:Repository/1/2024-01-01</id>
    <updated>2024-01-01T00:00:00Z</updated>
    <link rel="alternate" type="text/html" href="https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2024-01-01"/>
    <title>2024-01-01</title>
    <content type="html">&lt;p&gt;Ancient release.&lt;/p&gt;</content>
    <author><name>example-maintainer</name></author>
  </entry>
</feed>
"""

failures: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        failures.append(f"{label}: got {got!r}, want {want!r}")
    else:
        print(f"ok   {label}")


def main() -> int:
    entries = mod.atom_entries(RELEASES_ATOM)
    check("parses both entries", len(entries), 2)
    check("entry title", entries[0]["title"], "2026-07-28")
    check(
        "entry url",
        entries[0]["url"],
        "https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28",
    )
    check("entry author", entries[0]["author"], "example-maintainer")
    check("html stripped from summary", entries[0]["summary"], "Stable release of the 2026-07-28 revision.")

    # Windowing drops entries older than the cutoff.
    cutoff = datetime(2026, 7, 1, tzinfo=timezone.utc)
    check("window drops stale entry", len(mod.within_window(entries, cutoff, 15)), 1)
    check("max_entries caps output", len(mod.within_window(entries, datetime(2000, 1, 1, tzinfo=timezone.utc), 1)), 1)

    # Undated entries are kept rather than silently dropped.
    check("undated entry kept", len(mod.within_window([{"updated": ""}], cutoff, 15)), 1)

    check("parse_dt handles Z suffix", mod.parse_dt("2026-07-28T16:47:49Z"), datetime(2026, 7, 28, 16, 47, 49, tzinfo=timezone.utc))
    check("parse_dt rejects junk", mod.parse_dt("not-a-date"), None)
    check("clean_text handles None", mod.clean_text(None), "")
    check("clean_text unescapes entities", mod.clean_text("&lt;b&gt;a&amp;b&lt;/b&gt;"), "a&b")
    check("clean_text marks truncation", mod.clean_text("x" * 50, limit=10).endswith("[truncated]"), True)

    # --print-urls must work without any network access.
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--print-urls", "--repo", "huggingface/diffusers"],
        capture_output=True,
        text=True,
    )
    check("print-urls exit code", proc.returncode, 0)
    lines = [ln for ln in proc.stdout.strip().splitlines() if ln]
    check("print-urls filters to one repo", len(lines), 2)
    check(
        "print-urls emits releases feed",
        lines[0].endswith("https://github.com/huggingface/diffusers/releases.atom"),
        True,
    )

    # An unknown repo filter is an error, not an empty success.
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--print-urls", "--repo", "nope/nope"],
        capture_output=True,
        text=True,
    )
    check("unknown repo filter fails", proc.returncode, 1)

    # sources.json must stay valid and complete.
    config = json.loads((Path(SCRIPT).resolve().parents[1] / "sources.json").read_text(encoding="utf-8"))
    check("sources.json has entries", len(config["sources"]) >= 1, True)
    for source in config["sources"]:
        for key in ("owner", "repo", "label", "niche", "why_it_matters"):
            check(f"{source.get('repo', '?')} has {key}", key in source, True)

    print()
    if failures:
        print(f"FAILED ({len(failures)})")
        for line in failures:
            print(f"  {line}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
