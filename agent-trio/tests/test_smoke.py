"""Smoke tests that don't hit the OpenAI API.

Verify imports, agent construction, tool registration, and that the runner
can be instantiated. Real end-to-end runs require OPENAI_API_KEY and live
network, so they're left for the user.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_build_all_agents():
    from agent_trio.agents.second_brain_agent import build_second_brain_agent
    from agent_trio.agents.trading_agent import build_trading_agent
    from agent_trio.agents.research_agent import build_research_agent

    atlas = build_second_brain_agent()
    trader = build_trading_agent()
    scholar = build_research_agent()

    assert atlas.name == "Atlas"
    assert trader.name == "TradeDesk"
    assert scholar.name == "Scholar"

    # Atlas must expose handoffs to both specialists.
    handoff_targets = {h.agent_name for h in atlas.handoffs}
    assert {"TradeDesk", "Scholar"}.issubset(handoff_targets)

    # Each agent has tools registered.
    assert len(atlas.tools) >= 5
    assert len(trader.tools) >= 5
    assert len(scholar.tools) >= 3

    # Trading agent has both guardrail layers wired.
    assert atlas.handoffs and trader.input_guardrails and trader.output_guardrails


def test_local_task_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STORE_DIR", str(tmp_path))
    # reload to pick up env
    from agent_trio.tools import notion_tools
    import importlib
    importlib.reload(notion_tools)

    # use the underlying functions (FunctionTool is not callable directly)
    add = notion_tools.add_task.__wrapped__ if hasattr(notion_tools.add_task, "__wrapped__") else notion_tools.add_task
    # Fallback: call the underlying python via .params_json_schema -> we call internal helpers
    # Easier: exercise the JSON store helpers directly.
    notion_tools._save("tasks", [])
    assert notion_tools._load("tasks") == []
