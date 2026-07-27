"""Setup ergonomics: .env loading and actionable API error messages.

Both were added after hitting the failures for real during first provisioning.
"""
from __future__ import annotations

from fdr import config, errors


class TestDotenvLoading:
    def test_values_are_loaded_into_the_environment(self, tmp_path, monkeypatch, real_load_dotenv):
        env_file = tmp_path / ".env"
        env_file.write_text("FDR_TEST_KEY=value-from-file\n")
        monkeypatch.delenv("FDR_TEST_KEY", raising=False)

        real_load_dotenv(env_file)

        import os

        assert os.environ["FDR_TEST_KEY"] == "value-from-file"

    def test_real_environment_wins_by_default(self, tmp_path, monkeypatch, real_load_dotenv):
        """An explicit export must always beat the file."""
        env_file = tmp_path / ".env"
        env_file.write_text("FDR_TEST_KEY=from-file\n")
        monkeypatch.setenv("FDR_TEST_KEY", "from-shell")

        real_load_dotenv(env_file)

        import os

        assert os.environ["FDR_TEST_KEY"] == "from-shell"

    def test_override_forces_the_file_value(self, tmp_path, monkeypatch, real_load_dotenv):
        env_file = tmp_path / ".env"
        env_file.write_text("FDR_TEST_KEY=from-file\n")
        monkeypatch.setenv("FDR_TEST_KEY", "from-shell")

        real_load_dotenv(env_file, override=True)

        import os

        assert os.environ["FDR_TEST_KEY"] == "from-file"

    def test_comments_blanks_and_quotes_are_handled(self, tmp_path, monkeypatch, real_load_dotenv):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# a comment\n\nFDR_QUOTED=\"quoted value\"\nFDR_PLAIN=plain\nnot_a_pair\n"
        )
        for key in ("FDR_QUOTED", "FDR_PLAIN"):
            monkeypatch.delenv(key, raising=False)

        real_load_dotenv(env_file)

        import os

        assert os.environ["FDR_QUOTED"] == "quoted value"
        assert os.environ["FDR_PLAIN"] == "plain"

    def test_values_containing_equals_are_preserved(self, tmp_path, monkeypatch, real_load_dotenv):
        """API keys and tokens routinely contain '='."""
        env_file = tmp_path / ".env"
        env_file.write_text("FDR_TOKEN=abc=def=ghi\n")
        monkeypatch.delenv("FDR_TOKEN", raising=False)

        real_load_dotenv(env_file)

        import os

        assert os.environ["FDR_TOKEN"] == "abc=def=ghi"

    def test_missing_file_is_not_an_error(self, tmp_path, real_load_dotenv):
        real_load_dotenv(tmp_path / "nonexistent.env")


class TestErrorExplanations:
    def test_billing_failure_points_at_billing(self):
        exc = Exception(
            "Error code: 400 - {'error': {'message': 'Your credit balance is too low "
            "to access the Anthropic API.'}}"
        )
        explanation = errors.explain(exc)

        assert "no credits" in explanation
        assert "billing" in explanation
        assert errors.is_explained(exc)

    def test_billing_failure_says_rerunning_is_safe(self):
        """Provisioning is idempotent; users should know that before panicking."""
        exc = Exception("Your credit balance is too low")

        assert "re-running is safe" in errors.explain(exc)

    def test_stale_agent_id_points_at_reprovisioning(self):
        exc = Exception("Error code: 400 - {'error': {'message': 'Invalid agent ID.'}}")

        assert "provision_agents.py" in errors.explain(exc)

    def test_bad_key_points_at_the_key(self):
        exc = Exception("authentication_error: invalid x-api-key")
        explanation = errors.explain(exc)

        assert "ANTHROPIC_API_KEY" in explanation

    def test_unrecognised_errors_pass_through_unchanged(self):
        exc = Exception("something entirely unexpected")

        assert errors.explain(exc) == "something entirely unexpected"
        assert not errors.is_explained(exc)
