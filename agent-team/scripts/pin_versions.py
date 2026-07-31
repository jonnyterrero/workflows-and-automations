#!/usr/bin/env python3
"""Pin agents off `latest` onto the concrete skill versions recorded at upload.

Agents are created with `version: latest` on every attached skill, which means a
later `upload_skills.py --update-existing` silently changes the behaviour of
already-accepted agents. This repoints each agent at the exact skill versions in
dist/skill_ids.json, so accepted behaviour stays put until you re-pin.

Coordinator roster entries are already pinned to specialist agent versions at
creation time; this script does not touch them.

  python scripts/pin_versions.py            # dry run, shows the mapping
  python scripts/pin_versions.py --execute
  python scripts/pin_versions.py --unpin --execute   # back to latest
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_IDS = ROOT / "dist" / "skill_ids.json"
AGENT_IDS = ROOT / "dist" / "agent_ids.json"
MANIFEST = ROOT / "agents" / "manifest.yaml"


def load_manifest() -> dict:
    try:
        import yaml

        return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    except ImportError:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from generate_agent_templates import load_manifest as lm

        return lm()


def main() -> None:
    ap = argparse.ArgumentParser(description="Pin or unpin agent skill versions")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--unpin", action="store_true", help="Revert every skill to `latest`")
    args = ap.parse_args()

    for path in (SKILL_IDS, AGENT_IDS):
        if not path.exists():
            raise SystemExit(f"Missing {path.name}. Upload skills and deploy agents first.")

    skills = json.loads(SKILL_IDS.read_text(encoding="utf-8"))["skills"]
    agents = json.loads(AGENT_IDS.read_text(encoding="utf-8"))["specialists"]
    m = load_manifest()
    commons = m["commons_skill"]

    plan = []
    for spec in m["specialists"]:
        slug = spec["slug"]
        if slug not in agents:
            print(f"SKIP {slug}: no live agent id")
            continue
        attached = [commons, spec["skill"]]
        missing = [s for s in attached if s not in skills]
        if missing:
            raise SystemExit(f"Missing skill ids for {slug}: {missing}")
        payload = [
            {
                "type": "custom",
                "skill_id": skills[s]["skill_id"],
                "version": "latest" if args.unpin else str(skills[s]["version"]),
            }
            for s in attached
        ]
        plan.append((slug, agents[slug]["agent_id"], attached, payload))

    verb = "unpin" if args.unpin else "pin"
    print(f"Plan: {verb} {len(plan)} agents")
    for slug, agent_id, attached, payload in plan:
        versions = ", ".join(f"{s}@{p['version']}" for s, p in zip(attached, payload))
        print(f"  {slug} ({agent_id}): {versions}")

    if not args.execute:
        print("\nDry run only. Re-run with --execute to apply.")
        return
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    import anthropic

    client = anthropic.Anthropic()
    failures = []
    for slug, agent_id, _attached, payload in plan:
        try:
            a = client.beta.agents.update(agent_id, skills=payload)
            print(f"OK {slug} -> agent version {a.version}")
        except Exception as exc:
            failures.append({"agent": slug, "error": repr(exc)})
            print(f"FAIL {slug}: {exc}")

    if failures:
        raise SystemExit(f"{len(failures)} agent(s) failed to {verb}")
    print(f"\n{len(plan)} agents {verb}ned.")
    if not args.unpin:
        print("Re-run after any upload_skills.py --update-existing to move the pin forward.")


if __name__ == "__main__":
    main()
