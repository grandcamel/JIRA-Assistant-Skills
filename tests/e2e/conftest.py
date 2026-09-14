"""Pytest configuration and fixtures for the help-only sufficiency arm.

The sufficiency arm answers spec L94's question: is the Entry-Point Hint
alone (skills/jira/SKILL.md, shipped via the plugin manifest) enough for a
model to complete representative jira-as tasks? The model under test gets
nothing else: no other skill, no other tool besides Bash, and a `jira-as`
on PATH forced into its `simulation` transport with no credentials in the
environment, so nothing it runs can reach a live Jira site.
"""

import os
from pathlib import Path

import pytest

from .runner import SufficiencyRunner

DEFAULT_MODEL = "claude-sonnet-5"

# Credential variables that must never reach the sandboxed subprocess.
CREDENTIAL_ENV_VARS = (
    "JIRA_SITE_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_API_TOKEN_PRODUCTION",
    "JIRA_API_TOKEN_DEVELOPMENT",
)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--sufficiency-timeout",
        action="store",
        default=os.environ.get("SUFFICIENCY_TEST_TIMEOUT", "120"),
        help="Timeout per trial in seconds",
    )
    parser.addoption(
        "--sufficiency-model",
        action="store",
        default=os.environ.get("SUFFICIENCY_TEST_MODEL", DEFAULT_MODEL),
        help="Claude model to use for the sufficiency arm",
    )


@pytest.fixture(scope="session")
def e2e_enabled():
    """Check if the sufficiency arm should run (needs `claude` and `jira-as`)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    claude_dir = Path.home() / ".claude"
    has_claude_auth = bool(api_key) or bool(
        claude_dir.exists() and (claude_dir / "credentials.json").exists()
    )
    return has_claude_auth


@pytest.fixture(scope="session")
def repo_root():
    """The shipped plugin's own directory: manifest + skills/jira/SKILL.md."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def test_cases_path(repo_root):
    """Path to the seven representative tasks."""
    return repo_root / "tests" / "e2e" / "test_cases.yaml"


@pytest.fixture(scope="session")
def sufficiency_timeout(request):
    return int(request.config.getoption("--sufficiency-timeout"))


@pytest.fixture(scope="session")
def sufficiency_model(request):
    return request.config.getoption("--sufficiency-model")


@pytest.fixture(scope="session")
def simulation_env():
    """
    The environment the model's Claude Code process (and every jira-as
    invocation re-run from its transcript) executes under: no Jira
    credentials of any kind, and JIRA_AS_TRANSPORT forced to simulation so
    jira-as never dials out to a live site regardless of what it's told.
    """
    env = {k: v for k, v in os.environ.items() if k not in CREDENTIAL_ENV_VARS}
    env["JIRA_AS_TRANSPORT"] = "simulation"
    return env


@pytest.fixture(scope="session")
def sufficiency_runner(
    repo_root, sufficiency_timeout, sufficiency_model, simulation_env, e2e_enabled
):
    """
    Build the runner that drives Claude Code with ONLY the shipped plugin
    (skills/jira/SKILL.md) and the Bash tool installed.
    """
    if not e2e_enabled:
        pytest.skip("Sufficiency arm disabled (no API key or OAuth credentials)")

    return SufficiencyRunner(
        plugin_dir=repo_root,
        timeout=sufficiency_timeout,
        model=sufficiency_model,
        env=simulation_env,
    )
