#!/usr/bin/env python3
"""Generate agents/*.template.yaml from agents/manifest.yaml (single SoT)."""
from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:  # minimal fallback without PyYAML
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "agents" / "manifest.yaml"
OUT_DIR = ROOT / "agents"
ROUTING = ROOT / "docs" / "ROUTING_MATRIX.md"


def load_manifest() -> dict:
    text = MANIFEST.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    # Minimal YAML subset parser for this manifest only
    return _parse_simple(text)


def _parse_simple(text: str) -> dict:
    """Fallback when PyYAML is missing: use regex-light structure we control."""
    import re

    release = re.search(r'^release:\s*"([^"]+)"', text, re.M).group(1)
    team = re.search(r"^team:\s*(\S+)", text, re.M).group(1)
    commons = re.search(r"^commons_skill:\s*(\S+)", text, re.M).group(1)
    sys_m = re.search(r"^system_template:\s*>-\n((?:  .+\n)+)", text, re.M)
    system_template = " ".join(ln.strip() for ln in sys_m.group(1).splitlines())

    def block(name: str) -> str:
        m = re.search(rf"^{name}:\n((?:  .+\n)+)", text, re.M)
        return m.group(1) if m else ""

    def fields(block_text: str) -> dict:
        out = {}
        for key in (
            "slug",
            "display_name",
            "description",
            "model",
            "effort",
            "tool_profile",
            "skill",
        ):
            m = re.search(rf"^\s+{key}:\s*(.+)$", block_text, re.M)
            if m:
                out[key] = m.group(1).strip().strip("\"'")
        return out

    coord = fields(block("coordinator"))
    specs = []
    for m in re.finditer(r"^- slug: (.+)$", text, re.M):
        start = m.start()
        nxt = re.search(r"^- slug:", text[m.end() :], re.M)
        end = m.end() + nxt.start() if nxt else len(text)
        chunk = text[start:end]
        specs.append(fields("  " + chunk.replace("- slug:", "  slug:", 1)))
        specs[-1]["slug"] = m.group(1).strip()
    return {
        "release": release,
        "team": team,
        "commons_skill": commons,
        "system_template": system_template,
        "coordinator": coord,
        "specialists": specs,
    }


def tools_yaml(profile: str) -> str:
    if profile == "coding":
        return """tools:
  - type: agent_toolset_20260401
    default_config:
      permission_policy:
        type: always_allow
    configs:
      - name: bash
        permission_policy:
          type: always_ask
      - name: write
        permission_policy:
          type: always_ask
      - name: edit
        permission_policy:
          type: always_ask"""
    if profile == "coordinator":
        return """tools:
  - type: agent_toolset_20260401
    default_config:
      enabled: false
    configs:
      - name: read
        enabled: true
      - name: glob
        enabled: true
      - name: grep
        enabled: true
      - name: web_search
        enabled: true
      - name: web_fetch
        enabled: true"""
    # research / audit
    return """tools:
  - type: agent_toolset_20260401
    default_config:
      enabled: false
    configs:
      - name: read
        enabled: true
      - name: glob
        enabled: true
      - name: grep
        enabled: true
      - name: web_search
        enabled: true
      - name: web_fetch
        enabled: true
      - name: bash
        enabled: true
        permission_policy:
          type: always_ask"""


def env_placeholder(slug: str) -> str:
    return "${SKILL_ID_" + slug.upper().replace("-", "_") + "}"


def agent_placeholder(slug: str) -> str:
    return "${AGENT_ID_" + slug.upper().replace("-", "_") + "}"


def write_specialist(m: dict, spec: dict) -> None:
    system = m["system_template"].format(
        display_name=spec["display_name"], skill=spec["skill"]
    )
    skill_id = env_placeholder(spec["skill"])
    commons_id = env_placeholder(m["commons_skill"])
    content = f"""# Generated from agents/manifest.yaml — do not edit by hand.
# Run: python scripts/generate_agent_templates.py
# Replace skill ID placeholders after uploading skills.
name: {spec['display_name']}
description: {spec['description']}
model:
  id: {spec['model']}
  effort: {spec['effort']}
system: >-
  {system}
{tools_yaml(spec['tool_profile'])}
skills:
  - type: custom
    skill_id: {commons_id}
    version: latest
  - type: custom
    skill_id: {skill_id}
    version: latest
metadata:
  team: {m['team']}
  specialist: {spec['slug']}
  release: "{m['release']}"
"""
    path = OUT_DIR / f"{spec['slug']}.template.yaml"
    path.write_text(content, encoding="utf-8")
    print("wrote", path.name)


def write_coordinator(m: dict) -> None:
    routing = ROUTING.read_text(encoding="utf-8").strip() if ROUTING.exists() else ""
    # Keep routing compact in system: first principles + table header reminder
    system = (
        "You are the coordinator for Jonny's specialist agent team. Classify each request "
        "by its primary deliverable and use the routing matrix below. Delegate only bounded "
        "tasks that materially benefit from specialization or parallelism. Do not call every "
        "agent. Preserve specialist independence: implementation agents do not erase auditor "
        "findings, and high-stakes legal, tax, financial, trading, or health claims require "
        "current evidence and explicit uncertainty. Synthesize one coherent answer, identify "
        "disagreements, and state which agents and sources were used. Consequential writes, "
        "deployments, financial actions, legal filings, tax filings, or account changes require "
        "explicit user authorization and appropriate human review.\n\n"
        "ROUTING MATRIX:\n" + routing
    )
    # YAML folded scalar — escape nothing special if we use literal block
    agents_block = "\n".join(
        f"    - type: agent\n      id: {agent_placeholder(s['slug'])}\n"
        f"      # Pin version after acceptance testing."
        for s in m["specialists"]
    )
    # Use literal block for long system
    content = f"""# Generated from agents/manifest.yaml — do not edit by hand.
# Run: python scripts/generate_agent_templates.py
# Create specialist agents first and replace every AGENT_ID placeholder.
name: {m['coordinator']['display_name']}
description: {m['coordinator']['description']}
model:
  id: {m['coordinator']['model']}
  effort: {m['coordinator']['effort']}
system: |
{chr(10).join('  ' + line if line else '' for line in system.splitlines())}
{tools_yaml('coordinator')}
multiagent:
  type: coordinator
  agents:
{agents_block}
metadata:
  team: {m['team']}
  role: coordinator
  release: "{m['release']}"
"""
    path = OUT_DIR / "coordinator.template.yaml"
    path.write_text(content, encoding="utf-8")
    print("wrote", path.name)


def main() -> None:
    m = load_manifest()
    for spec in m["specialists"]:
        write_specialist(m, spec)
    write_coordinator(m)
    print(f"Generated {len(m['specialists'])} specialists + coordinator (release {m['release']})")


if __name__ == "__main__":
    main()
