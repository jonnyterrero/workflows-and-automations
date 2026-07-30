"""Assemble complete agent definitions from YAML prompts + the tool registry.

Split of responsibility:

* ``agents/*.agent.yaml`` owns the parts a human writes and reviews — the
  system prompt, the model, and which built-in tools are enabled.
* ``fdr.tools.registry`` owns the custom tool JSON schemas, because those have
  to match the handler signatures exactly.

Neither duplicates the other, so they cannot drift. This module joins them into
the payload Managed Agents expects.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from fdr.config import PROJECT_ROOT
from fdr.tools import registry

AGENTS_DIR = PROJECT_ROOT / "agents"

# Slug -> YAML filename. Slugs match fdr.tools.registry constants.
AGENT_FILES: dict[str, str] = {
    registry.THEME_SCOUT: "theme-scout.agent.yaml",
    registry.EVIDENCE_ANALYST: "evidence-analyst.agent.yaml",
    registry.RISK_ANALYST: "risk-valuation-analyst.agent.yaml",
    registry.COMMITTEE: "investment-committee.agent.yaml",
}

# The manager synthesises; it must not run its own uncited research. Enforced
# as a capability check rather than a prompt instruction.
FORBIDDEN_TOOLS: dict[str, frozenset[str]] = {
    registry.COMMITTEE: frozenset({"web_search", "web_fetch", "bash"}),
    registry.EVIDENCE_ANALYST: frozenset({"web_search"}),
    registry.RISK_ANALYST: frozenset({"web_search"}),
}

ENVIRONMENT_FILE = "research.environment.yaml"

# Delegation order. The committee coordinates these; Managed Agents allows
# exactly one level, so none of them may have a roster of their own.
SPECIALIST_SLUGS: tuple[str, ...] = (
    registry.THEME_SCOUT,
    registry.EVIDENCE_ANALYST,
    registry.RISK_ANALYST,
)


def load_agent_yaml(slug: str, agents_dir: Path | None = None) -> dict[str, Any]:
    directory = agents_dir or AGENTS_DIR
    path = directory / AGENT_FILES[slug]
    if not path.exists():
        raise FileNotFoundError(f"agent definition missing: {path}")
    return yaml.safe_load(path.read_text())


def load_environment(agents_dir: Path | None = None) -> dict[str, Any]:
    directory = agents_dir or AGENTS_DIR
    return yaml.safe_load((directory / ENVIRONMENT_FILE).read_text())


def enabled_builtin_tools(definition: dict[str, Any]) -> set[str]:
    """Built-in tools an agent can actually call, after config is applied."""
    enabled: set[str] = set()
    for tool in definition.get("tools", []):
        if tool.get("type") != "agent_toolset_20260401":
            continue
        default_on = bool(tool.get("default_config", {}).get("enabled", True))
        configs = {c["name"]: c for c in tool.get("configs", [])}
        # Every tool in the built-in toolset, so a default-on agent is scored
        # against the full surface rather than only what it names.
        universe = {
            "bash", "read", "write", "edit",
            "glob", "grep", "web_fetch", "web_search",
        } | set(configs)
        for name in universe:
            if configs.get(name, {}).get("enabled", default_on):
                enabled.add(name)
    return enabled


def build_agent_payload(
    slug: str,
    agents_dir: Path | None = None,
    roster: list[str] | None = None,
) -> dict[str, Any]:
    """The full ``POST /v1/agents`` body for one agent."""
    definition = load_agent_yaml(slug, agents_dir)

    payload: dict[str, Any] = {
        "name": definition["name"],
        "model": definition["model"],
        "system": definition["system"],
        "tools": list(definition.get("tools", [])) + registry.tools_for(slug),
    }
    if description := definition.get("description"):
        payload["description"] = description

    if roster:
        # Coordinator roster, injected once the specialists have IDs.
        payload["multiagent"] = {"type": "coordinator", "agents": list(roster)}

    return payload


def validate_definition(slug: str, agents_dir: Path | None = None) -> list[str]:
    """Structural checks. Returns human-readable problems; empty means valid."""
    problems: list[str] = []
    definition = load_agent_yaml(slug, agents_dir)

    for required in ("name", "model", "system"):
        if not definition.get(required):
            problems.append(f"{slug}: missing required field '{required}'")

    model = definition.get("model")
    if isinstance(model, dict) and not model.get("id"):
        problems.append(f"{slug}: model object has no 'id'")

    enabled = enabled_builtin_tools(definition)
    for forbidden in FORBIDDEN_TOOLS.get(slug, frozenset()):
        if forbidden in enabled:
            problems.append(
                f"{slug}: '{forbidden}' is enabled but this agent must not have it"
            )

    # A specialist with its own roster would imply two-level delegation, which
    # Managed Agents rejects at create time.
    if slug in SPECIALIST_SLUGS and definition.get("multiagent"):
        problems.append(f"{slug}: specialists must not declare a multiagent roster")

    declared_custom = {t["name"] for t in definition.get("tools", []) if t.get("type") == "custom"}
    if declared_custom:
        problems.append(
            f"{slug}: custom tools must come from the registry, not the YAML "
            f"(found {sorted(declared_custom)})"
        )

    return problems


def validate_all(agents_dir: Path | None = None) -> list[str]:
    problems: list[str] = []
    for slug in AGENT_FILES:
        problems.extend(validate_definition(slug, agents_dir))
    return problems
