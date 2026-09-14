"""
Offline unit tests for tests/harness_env.py's build_harness_env() (review
fix, JAS-55). No subprocess is launched anywhere in this file.
"""

from tests.harness_env import build_harness_env


def test_present_keys_are_copied_and_transport_is_forced(monkeypatch):
    """PATH, HOME, TERM and LANG, when present, are copied verbatim, and
    JIRA_AS_TRANSPORT is always forced to simulation."""
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setenv("HOME", "/home/operator")
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setenv("LANG", "en_US.UTF-8")

    env = build_harness_env()

    assert env["PATH"] == "/usr/bin:/bin"
    assert env["HOME"] == "/home/operator"
    assert env["TERM"] == "xterm-256color"
    assert env["LANG"] == "en_US.UTF-8"
    assert env["JIRA_AS_TRANSPORT"] == "simulation"
    assert len(env) == 5, f"unexpected extra keys leaked through: {env}"


def test_absent_optional_keys_are_omitted_and_credentials_never_pass_through(
    monkeypatch,
):
    """
    TERM/LANG are simply omitted when absent (no KeyError). Credential
    variables -- named ones, and anything else starting with JIRA_ or
    ANTHROPIC_ -- never appear in the built environment even when set in
    the calling process's own environment.
    """
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("HOME", "/home/operator")
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.delenv("LANG", raising=False)

    # Credentials and lookalikes that must never leak through.
    monkeypatch.setenv("JIRA_SITE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_EMAIL", "operator@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "secret-token")  # noqa: S105
    monkeypatch.setenv("JIRA_DEFAULT_PROJECT", "PROJ")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-secret")  # noqa: S105
    monkeypatch.setenv("JIRA_SOME_FUTURE_VAR", "should-never-appear")
    monkeypatch.setenv("ANTHROPIC_SOME_FUTURE_VAR", "should-never-appear")

    env = build_harness_env()

    assert "TERM" not in env
    assert "LANG" not in env
    assert env["PATH"] == "/usr/bin"
    assert env["HOME"] == "/home/operator"
    assert env["JIRA_AS_TRANSPORT"] == "simulation"

    for leaked in (
        "JIRA_SITE_URL",
        "JIRA_EMAIL",
        "JIRA_API_TOKEN",
        "JIRA_DEFAULT_PROJECT",
        "ANTHROPIC_API_KEY",
        "JIRA_SOME_FUTURE_VAR",
        "ANTHROPIC_SOME_FUTURE_VAR",
    ):
        assert leaked not in env, f"{leaked} leaked into the harness environment"

    assert len(env) == 3, f"unexpected extra keys leaked through: {env}"
