#!/usr/bin/env python3
"""Export SoT skills + manifest into versioned agent-team/cursor/ for Cursor."""
from __future__ import annotations

import re
from pathlib import Path

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise SystemExit("PyYAML required: pip install -r requirements.txt") from e

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
MANIFEST = ROOT / "agents" / "manifest.yaml"
OUT_SKILLS = ROOT / "cursor" / "skills"
OUT_AGENTS = ROOT / "cursor" / "agents"
COMMONS = SKILLS / "team-commons" / "SKILL.md"


def strip_frontmatter(text: str) -> tuple[dict, str]:
    """Parse name/description with regex so unquoted colons in descriptions are safe."""
    if not text.startswith("---\n"):
        return {}, text
    _, fm, body = text.split("---", 2)
    meta: dict = {}
    for key in ("name", "description"):
        m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
        if m:
            meta[key] = m.group(1).strip().strip("\"'")
    ver = re.search(r'version:\s*"([^"]+)"', fm)
    if ver:
        meta["version"] = ver.group(1)
    return meta, body.lstrip("\n")


def compose_skill(slug: str) -> str:
    src = (SKILLS / slug / "SKILL.md").read_text(encoding="utf-8")
    meta, body = strip_frontmatter(src)
    _, commons_body = strip_frontmatter(COMMONS.read_text(encoding="utf-8"))
    name = meta.get("name", slug)
    desc = meta.get("description", f"Jonny agent skill: {slug}")
    # Quote description for valid YAML when it contains colons
    ver = meta.get("version", "2.1.0")
    return (
        f"---\nname: {name}\ndescription: \"{desc}\"\n"
        f"metadata:\n  version: \"{ver}\"\n"
        f"  source: agent-team\n---\n\n"
        f"{body.rstrip()}\n\n"
        f"---\n\n# Shared team commons (composed)\n\n"
        f"{commons_body.rstrip()}\n"
    )


def tool_summary(profile: str) -> str:
    if profile == "coding":
        return "Prefer implementation tools; ask before bash/write/edit."
    if profile == "coordinator":
        return "Read/search only; delegate to specialists."
    if profile == "audit":
        return "Read/search + bash (ask); do not silently implement remediations."
    return "Read/search + bash (ask); research and advise."


def write_agent_md(spec: dict, release: str) -> None:
    slug = spec["slug"]
    body = f"""---
name: {spec['display_name']}
description: {spec['description']}
model: {spec['model']}
---

# {spec['display_name']}

Release `{release}`. Source of truth: `agent-team/skills/{spec['skill']}/SKILL.md`.

## Role
Apply the `{spec['skill']}` workflow plus `team-commons` rules. Stay in role boundaries and recommend delegation when another specialist owns the primary deliverable.

## Model hint
`{spec['model']}` (effort: {spec['effort']})

## Tools policy
{tool_summary(spec['tool_profile'])}

## Skill
Use the Cursor skill exported at `cursor/skills/{spec['skill']}/SKILL.md` (also installed under `~/.cursor/skills/{spec['skill']}/` after `install_cursor_local.py`).
"""
    path = OUT_AGENTS / f"{slug}.md"
    path.write_text(body, encoding="utf-8")


def write_coordinator(m: dict) -> None:
    routing = (ROOT / "docs" / "ROUTING_MATRIX.md").read_text(encoding="utf-8")
    c = m["coordinator"]
    body = f"""---
name: {c['display_name']}
description: {c['description']}
model: {c['model']}
---

# {c['display_name']}

Release `{m['release']}`.

## Role
Route by primary deliverable. Delegate bounded specialist work. Synthesize disagreements. Require authorization for consequential actions.

## Model hint
`{c['model']}` (effort: {c['effort']})

## Tools policy
{tool_summary('coordinator')}

## Routing matrix

{routing}
"""
    (OUT_AGENTS / "coordinator.md").write_text(body, encoding="utf-8")


def main() -> None:
    m = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    OUT_SKILLS.mkdir(parents=True, exist_ok=True)
    OUT_AGENTS.mkdir(parents=True, exist_ok=True)

    # Export commons alone + each specialist composed with commons
    commons_out = OUT_SKILLS / "team-commons"
    commons_out.mkdir(parents=True, exist_ok=True)
    (commons_out / "SKILL.md").write_text(COMMONS.read_text(encoding="utf-8"), encoding="utf-8")
    print("exported team-commons")

    for spec in m["specialists"]:
        slug = spec["skill"]
        dest = OUT_SKILLS / slug
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "SKILL.md").write_text(compose_skill(slug), encoding="utf-8")
        write_agent_md(spec, m["release"])
        print("exported", slug)

    write_coordinator(m)
    print("exported coordinator")
    print(f"Cursor export complete -> {ROOT / 'cursor'}")


if __name__ == "__main__":
    main()
