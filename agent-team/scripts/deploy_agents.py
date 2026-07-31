#!/usr/bin/env python3
"""Create specialist Managed Agents from uploaded skill IDs, then create a coordinator.

Dry-run by default. Driven by agents/manifest.yaml so YAML and API create cannot drift.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "agents" / "manifest.yaml"
IDS = ROOT / "dist" / "skill_ids.json"
OUT = ROOT / "dist" / "agent_ids.json"
ROUTING = ROOT / "docs" / "ROUTING_MATRIX.md"
OPERATOR = ROOT / "config" / "operator.context.yaml"


def load_manifest() -> dict:
    try:
        import yaml

        return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    except ImportError:
        # Same subset parser as generate_agent_templates.py
        from generate_agent_templates import load_manifest as lm

        return lm()


def tools(profile: str) -> list:
    if profile == "coding":
        return [
            {
                "type": "agent_toolset_20260401",
                "default_config": {"permission_policy": {"type": "always_allow"}},
                "configs": [
                    {"name": "bash", "permission_policy": {"type": "always_ask"}},
                    {"name": "write", "permission_policy": {"type": "always_ask"}},
                    {"name": "edit", "permission_policy": {"type": "always_ask"}},
                ],
            }
        ]
    enabled = ["read", "glob", "grep", "web_search", "web_fetch"]
    configs = [{"name": n, "enabled": True} for n in enabled]
    if profile in {"research", "audit"}:
        configs.append(
            {"name": "bash", "enabled": True, "permission_policy": {"type": "always_ask"}}
        )
    return [
        {
            "type": "agent_toolset_20260401",
            "default_config": {"enabled": False},
            "configs": configs,
        }
    ]


def operator_note() -> str:
    if not OPERATOR.exists():
        return ""
    text = OPERATOR.read_text(encoding="utf-8")
    # Avoid requiring PyYAML: pull academic notes line if present
    m = re.search(r'status:\s*"([^"]+)"', text)
    notes = re.search(r'notes:\s*"([^"]+)"', text)
    parts = []
    if m:
        parts.append(f"Operator academic context: {m.group(1)}.")
    if notes:
        parts.append(notes.group(1))
    return (" " + " ".join(parts)) if parts else ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument(
        "--phase",
        choices=("specialists", "coordinator", "all"),
        default="all",
        help=(
            "specialists: create specialists only, then stop so evals can gate the "
            "coordinator. coordinator: create the coordinator from the specialist IDs "
            "already in dist/agent_ids.json. all: both in one pass (default)."
        ),
    )
    args = ap.parse_args()
    m = load_manifest()
    if args.phase == "coordinator":
        print(f"Plan: create coordinator only (release {m['release']})")
    elif args.phase == "specialists":
        print(f"Plan: create {len(m['specialists'])} specialists, no coordinator (release {m['release']})")
    else:
        print(f"Plan: create {len(m['specialists'])} specialists + coordinator (release {m['release']})")
    if not args.execute:
        print("Dry run only. Review agents/manifest.yaml and generated templates first.")
        print("Requires dist/skill_ids.json only in --execute mode.")
        return
    if not IDS.exists():
        raise SystemExit("Missing dist/skill_ids.json. Run upload_skills.py --execute first.")
    data = json.loads(IDS.read_text(encoding="utf-8"))["skills"]
    commons = m["commons_skill"]
    needed = [commons] + [s["skill"] for s in m["specialists"]]
    missing = [s for s in needed if s not in data]
    if missing:
        raise SystemExit(f"Missing skill IDs: {missing}")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    import anthropic

    client = anthropic.Anthropic()
    made = {}
    note = operator_note()
    if args.phase == "coordinator":
        if not OUT.exists():
            raise SystemExit(
                "Missing dist/agent_ids.json. Run --phase specialists --execute first."
            )
        made = json.loads(OUT.read_text(encoding="utf-8"))["specialists"]
        missing_specialists = [s["slug"] for s in m["specialists"] if s["slug"] not in made]
        if missing_specialists:
            raise SystemExit(f"Missing specialist agent IDs: {missing_specialists}")
        print(f"Reusing {len(made)} specialist agent IDs from {OUT.name}")
    for spec in m["specialists"] if args.phase != "coordinator" else []:
        system = m["system_template"].format(
            display_name=spec["display_name"], skill=spec["skill"]
        )
        if spec["skill"] == "bme-tutor-agent" and note:
            system = system + note
        skills = [
            {
                "type": "custom",
                "skill_id": data[commons]["skill_id"],
                "version": "latest",
            },
            {
                "type": "custom",
                "skill_id": data[spec["skill"]]["skill_id"],
                "version": "latest",
            },
        ]
        a = client.beta.agents.create(
            name=spec["display_name"],
            model={"id": spec["model"], "effort": spec["effort"]},
            system=system,
            description=spec["description"],
            tools=tools(spec["tool_profile"]),
            skills=skills,
            metadata={
                "team": m["team"],
                "specialist": spec["slug"],
                "release": m["release"],
            },
        )
        made[spec["slug"]] = {"agent_id": a.id, "version": a.version}
        print("OK", spec["slug"], a.id, a.version)

    if args.phase == "specialists":
        OUT.parent.mkdir(parents=True, exist_ok=True)
        prior = {}
        if OUT.exists():
            prior = json.loads(OUT.read_text(encoding="utf-8"))
        payload = {"specialists": made}
        if prior.get("coordinator"):
            payload["coordinator"] = prior["coordinator"]
        OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("Wrote", OUT)
        print(
            f"\n{len(made)} specialists created. Coordinator NOT created.\n"
            "Run the specialist evals, then: python scripts/deploy_agents.py "
            "--phase coordinator --execute"
        )
        return

    routing = ROUTING.read_text(encoding="utf-8") if ROUTING.exists() else ""
    coord_system = (
        "You coordinate Jonny's specialist agent team. Route by primary deliverable, "
        "delegate only bounded useful work, preserve auditor independence, require current "
        "evidence for high-stakes claims, synthesize disagreements, and require authorization "
        "for consequential writes or external actions.\n\nROUTING MATRIX:\n" + routing
    )
    coord = client.beta.agents.create(
        name=m["coordinator"]["display_name"],
        model={"id": m["coordinator"]["model"], "effort": m["coordinator"]["effort"]},
        system=coord_system,
        description=m["coordinator"]["description"],
        tools=tools("coordinator"),
        multiagent={
            "type": "coordinator",
            "agents": [
                {"type": "agent", "id": v["agent_id"], "version": v["version"]}
                for v in made.values()
            ],
        },
        metadata={"team": m["team"], "role": "coordinator", "release": m["release"]},
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "specialists": made,
                "coordinator": {"agent_id": coord.id, "version": coord.version},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
