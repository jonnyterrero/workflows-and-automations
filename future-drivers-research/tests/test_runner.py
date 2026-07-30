"""Session-driver helpers.

The full loop needs a live session, but the parts that are easy to get wrong —
payload coercion and multiagent thread routing — are pure and tested here.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from fdr import runner


class TestToolPayloadCoercion:
    def test_dict_input_passes_through(self):
        event = SimpleNamespace(input={"symbol": "NVDA"})

        assert runner._tool_payload(event) == {"symbol": "NVDA"}

    def test_json_string_input_is_parsed(self):
        event = SimpleNamespace(input=json.dumps({"symbol": "ETN"}))

        assert runner._tool_payload(event) == {"symbol": "ETN"}

    def test_malformed_json_yields_empty_payload_not_a_crash(self):
        """A bad payload must reach the handler as an error, not kill the run."""
        event = SimpleNamespace(input="{not json")

        assert runner._tool_payload(event) == {}

    def test_missing_input_yields_empty_payload(self):
        assert runner._tool_payload(SimpleNamespace()) == {}


class TestResultEvent:
    def test_result_is_serialised_as_text_content(self):
        event = SimpleNamespace(id="sevt_1", input={})
        payload = runner._result_event(event, {"ok": True})

        assert payload["type"] == "user.custom_tool_result"
        assert payload["custom_tool_use_id"] == "sevt_1"
        assert json.loads(payload["content"][0]["text"]) == {"ok": True}

    def test_thread_id_is_echoed_for_subagent_calls(self):
        """Routes the result back to the delegated thread that is waiting."""
        event = SimpleNamespace(id="sevt_2", input={}, session_thread_id="sthr_9")
        payload = runner._result_event(event, {})

        assert payload["session_thread_id"] == "sthr_9"

    def test_thread_id_is_omitted_on_the_primary_thread(self):
        event = SimpleNamespace(id="sevt_3", input={}, session_thread_id=None)

        assert "session_thread_id" not in runner._result_event(event, {})

    def test_non_serialisable_values_do_not_raise(self):
        from datetime import datetime

        event = SimpleNamespace(id="sevt_4", input={})
        payload = runner._result_event(event, {"when": datetime.now()})

        assert isinstance(payload["content"][0]["text"], str)


class TestBlockText:
    def test_text_blocks_are_extracted(self):
        assert runner._block_text(SimpleNamespace(type="text", text="hello")) == "hello"

    def test_non_text_blocks_are_ignored(self):
        assert runner._block_text(SimpleNamespace(type="tool_use")) == ""


class TestSessionResult:
    def test_transcript_joins_into_text(self):
        result = runner.SessionResult(session_id="sesn_1", transcript=["a", "b"])

        assert result.text == "a\nb"


class TestPreconditions:
    def test_missing_ids_fail_loudly(self, monkeypatch):
        monkeypatch.delenv("FDR_COMMITTEE_AGENT_ID", raising=False)
        monkeypatch.delenv("FDR_ENVIRONMENT_ID", raising=False)
        from fdr import config

        config.get_settings(refresh=True)

        with pytest.raises(RuntimeError, match="provision_agents"):
            runner.run_session("research NVDA")
