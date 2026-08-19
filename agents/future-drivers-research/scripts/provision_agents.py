#!/usr/bin/env python3
"""Create or update the four agents and their shared environment.

This is setup, run once — not part of the request path. Agents are persistent,
versioned objects; sessions reference them by ID. Creating agents per run would
accumulate orphans and defeat the versioning that lets you pin a session to a
known-good configuration.

The three specialists are created first because the committee's coordinator
roster needs their IDs.

    python scripts/provision_agents.py            # create or update, print IDs
    python scripts/provision_agents.py --dry-run  # print payloads, call nothing

Export the printed IDs (or put them in .env) so the runner can find them.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fdr import definitions, errors  # noqa: E402
from fdr.config import get_settings  # noqa: E402


def _find_existing(client, name: str) -> object | None:
    """Locate an agent by name so re-runs update instead of duplicating."""
    for agent in client.beta.agents.list():
        if getattr(agent, "name", None) == name:
            return agent
    return None


def _upsert_agent(client, payload: dict, dry_run: bool) -> tuple[str, int | None]:
    name = payload["name"]
    if dry_run:
        print(json.dumps(payload, indent=2)[:2000])
        return f"dry-run-{name.lower().replace(' ', '-')}", None

    existing = _find_existing(client, name)
    if existing is None:
        agent = client.beta.agents.create(**payload)
        print(f"created  {name}  {agent.id}  v{agent.version}")
    else:
        agent = client.beta.agents.update(existing.id, **payload)
        print(f"updated  {name}  {agent.id}  v{agent.version}")
    return agent.id, agent.version


def _upsert_environment(client, dry_run: bool) -> str:
    config = definitions.load_environment()
    if dry_run:
        print(json.dumps(config, indent=2))
        return "dry-run-env"

    for env in client.beta.environments.list():
        if getattr(env, "name", None) == config["name"]:
            print(f"reusing  environment  {env.id}")
            return env.id

    env = client.beta.environments.create(
        name=config["name"],
        config=config["config"],
        description=config.get("description"),
    )
    print(f"created  environment  {env.id}")
    return env.id


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print payloads, call nothing.")
    args = parser.parse_args()

    problems = definitions.validate_all()
    if problems:
        print("Agent definitions are invalid:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"validated {len(definitions.AGENT_FILES)} agent definitions\n")

    client = None
    if not args.dry_run:
        settings = get_settings()
        if not settings.anthropic_api_key:
            print(
                "ANTHROPIC_API_KEY is unset. Set it, run `ant auth login`, "
                "or use --dry-run.",
                file=sys.stderr,
            )
            return 1
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        environment_id = _upsert_environment(client, args.dry_run)

        roster: list[str] = []
        for slug in definitions.SPECIALIST_SLUGS:
            payload = definitions.build_agent_payload(slug)
            agent_id, _ = _upsert_agent(client, payload, args.dry_run)
            roster.append(agent_id)

        committee_payload = definitions.build_agent_payload(
            definitions.registry.COMMITTEE, roster=roster
        )
        committee_id, _ = _upsert_agent(client, committee_payload, args.dry_run)
    except Exception as exc:  # noqa: BLE001 - reported, not swallowed
        print(f"\nProvisioning stopped: {errors.explain(exc)}", file=sys.stderr)
        return 1

    print("\nAdd these to your .env:\n")
    print(f"FDR_ENVIRONMENT_ID={environment_id}")
    print(f"FDR_COMMITTEE_AGENT_ID={committee_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
