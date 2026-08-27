"""The agent definitions encode safety properties. These tests hold them in place.

Several constraints in the brief are enforced by *withholding capability* rather
than by prompt instruction — most importantly, the committee manager having no
web access. A prompt can be talked out of a rule; a missing tool cannot. These
tests fail if someone re-enables one.
"""
from __future__ import annotations

import pytest

from fdr import definitions
from fdr.tools import registry


class TestValidation:
    def test_all_definitions_are_valid(self):
        assert definitions.validate_all() == []

    def test_every_agent_file_exists_and_parses(self):
        for slug in definitions.AGENT_FILES:
            document = definitions.load_agent_yaml(slug)
            assert document["name"]
            assert document["system"].strip()

    def test_environment_is_defined(self):
        environment = definitions.load_environment()

        assert environment["config"]["type"] == "cloud"


class TestCapabilityBoundaries:
    def test_committee_cannot_search_or_fetch_the_web(self):
        """The manager synthesises specialist evidence; it does no own research."""
        enabled = definitions.enabled_builtin_tools(
            definitions.load_agent_yaml(registry.COMMITTEE)
        )

        assert "web_search" not in enabled
        assert "web_fetch" not in enabled

    def test_scout_can_search_the_web(self):
        """Discovery is the one role that legitimately needs open search."""
        enabled = definitions.enabled_builtin_tools(
            definitions.load_agent_yaml(registry.THEME_SCOUT)
        )

        assert "web_search" in enabled
        assert "web_fetch" in enabled

    def test_analysts_cannot_web_search(self):
        """Keeps them anchored on primary documents rather than commentary."""
        for slug in (registry.EVIDENCE_ANALYST, registry.RISK_ANALYST):
            enabled = definitions.enabled_builtin_tools(definitions.load_agent_yaml(slug))
            assert "web_search" not in enabled, slug
            assert "web_fetch" in enabled, slug

    @pytest.mark.parametrize("slug", sorted(definitions.AGENT_FILES))
    def test_forbidden_tools_are_absent(self, slug):
        enabled = definitions.enabled_builtin_tools(definitions.load_agent_yaml(slug))
        forbidden = definitions.FORBIDDEN_TOOLS.get(slug, frozenset())

        assert not (enabled & forbidden)


class TestToolWiring:
    def test_only_the_committee_can_score_or_persist(self):
        """Specialists supply evidence; only the manager finalises."""
        privileged = {"score_dossier", "save_dossier", "record_decision", "detect_changes"}

        for slug in definitions.AGENT_FILES:
            names = {tool["name"] for tool in registry.tools_for(slug)}
            if slug == registry.COMMITTEE:
                assert privileged <= names
            else:
                assert not (names & privileged), slug

    def test_evidence_analyst_owns_the_filings_tools(self):
        names = {tool["name"] for tool in registry.tools_for(registry.EVIDENCE_ANALYST)}

        assert {"sec_recent_filings", "sec_company_facts", "compute_fundamentals"} <= names

    def test_risk_analyst_owns_the_valuation_tools(self):
        names = {tool["name"] for tool in registry.tools_for(registry.RISK_ANALYST)}

        assert {"get_market_snapshot", "valuation_context"} <= names

    def test_scout_has_no_valuation_capability(self):
        """Structurally prevents the Scout from ranking candidates."""
        names = {tool["name"] for tool in registry.tools_for(registry.THEME_SCOUT)}

        assert "valuation_context" not in names
        assert "get_market_snapshot" not in names
        assert "score_dossier" not in names

    def test_every_registered_tool_is_assigned_to_an_agent(self):
        assigned = {name for spec in registry.TOOL_SPECS for name in ([spec.name] if spec.agents else [])}

        assert assigned == set(registry.REGISTRY)

    def test_yaml_does_not_declare_custom_tools(self):
        """Custom schemas come from the registry, so the two cannot drift."""
        for slug in definitions.AGENT_FILES:
            tools = definitions.load_agent_yaml(slug).get("tools", [])
            assert not [t for t in tools if t.get("type") == "custom"], slug


class TestPayloadAssembly:
    def test_payload_merges_builtin_and_custom_tools(self):
        payload = definitions.build_agent_payload(registry.EVIDENCE_ANALYST)
        types = [tool["type"] for tool in payload["tools"]]

        assert "agent_toolset_20260401" in types
        assert "custom" in types

    def test_payload_carries_model_and_system(self):
        payload = definitions.build_agent_payload(registry.RISK_ANALYST)

        assert payload["model"]["id"] == "claude-opus-5"
        assert "bear case" in payload["system"].lower()

    def test_committee_roster_is_injected(self):
        payload = definitions.build_agent_payload(
            registry.COMMITTEE, roster=["agent_a", "agent_b", "agent_c"]
        )

        assert payload["multiagent"]["type"] == "coordinator"
        assert payload["multiagent"]["agents"] == ["agent_a", "agent_b", "agent_c"]

    def test_specialists_have_no_roster(self):
        """Managed Agents permits one delegation level; a nested roster is rejected."""
        for slug in definitions.SPECIALIST_SLUGS:
            assert "multiagent" not in definitions.build_agent_payload(slug)

    def test_custom_tool_schemas_are_well_formed(self):
        for spec in registry.TOOL_SPECS:
            schema = spec.input_schema
            assert schema["type"] == "object"
            assert "properties" in schema
            for required in schema.get("required", []):
                assert required in schema["properties"], f"{spec.name}: {required}"


class TestPromptDiscipline:
    @pytest.mark.parametrize("slug", sorted(definitions.AGENT_FILES))
    def test_no_agent_is_told_to_produce_recommendations(self, slug):
        system = definitions.load_agent_yaml(slug)["system"].lower()

        # Phrases that would indicate the prompt asks for a trade call. The
        # prompts do mention these words when forbidding them, so we look for
        # instruction-shaped usage.
        assert "you should recommend buying" not in system
        assert "issue a price target" not in system

    def test_scout_is_forbidden_from_ranking(self):
        system = definitions.load_agent_yaml(registry.THEME_SCOUT)["system"].lower()

        assert "do not rank" in system

    def test_committee_is_told_not_to_self_score(self):
        system = definitions.load_agent_yaml(registry.COMMITTEE)["system"].lower()

        assert "score_dossier" in system
        assert "not yours to do" in system
