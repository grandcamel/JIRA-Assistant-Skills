"""Pytest configuration and fixtures for the help-only sufficiency arm.

The sufficiency arm answers: is the Entry-Point Hint alone
(skills/jira/SKILL.md, shipped via the plugin manifest) enough for a
model to complete representative jira-as tasks? The model under test gets
nothing else: no other skill, no tool besides Bash and Skill (Skill is
required to load the plugin's SKILL.md at all -- see runner.py), no
project context from this repository, and a `jira-as` on PATH forced into
its `simulation` transport with no credentials in the environment, so
nothing it runs can reach a live Jira site.

This arm launches the real `claude` binary and spends real tokens, so it
never runs silently: it requires the explicit E2E_SUFFICIENCY=1 opt-in
(see `_sufficiency_gate` below), rather than inferring "enabled" from
whatever credentials happen to be present.
"""

import os
import subprocess
from pathlib import Path

import pytest

from tests.harness_env import build_harness_env

from .runner import SufficiencyRunner

DEFAULT_MODEL = "claude-sonnet-5"

# Explicit opt-in required to run this arm at all. Do NOT infer "enabled"
# from ANTHROPIC_API_KEY or ~/.claude/credentials.json: a `claude auth
# login` keeps OAuth credentials in the system keychain, which would
# otherwise make the arm look "enabled" and skip silently through some
# other path, with no visible signal in a test run.
E2E_SUFFICIENCY_VAR = "E2E_SUFFICIENCY"


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
    """
    Whether the sufficiency arm should run for real -- gated on the
    explicit E2E_SUFFICIENCY=1 opt-in only. See the module docstring for
    why this is not inferred from ambient credentials.
    """
    return os.environ.get(E2E_SUFFICIENCY_VAR) == "1"


@pytest.fixture(scope="session", autouse=True)
def _sufficiency_gate(e2e_enabled):
    """
    Never let the arm run silently.

    Without E2E_SUFFICIENCY=1, every test in this directory is skipped
    with a loud reason naming the variable -- not a quiet pass. With the
    variable set, this probes `claude --version` once per session and
    FAILS (not skips) if the binary is missing, times out, or errors: an
    operator who explicitly opted in asked for a real run, and a missing
    or broken CLI is a setup defect, not something to quietly skip past.
    """
    if not e2e_enabled:
        pytest.skip(
            f"Sufficiency arm disabled: set {E2E_SUFFICIENCY_VAR}=1 to run "
            "it (it launches the real `claude` binary and spends real "
            "tokens)."
        )

    try:
        probe = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        pytest.fail(
            f"{E2E_SUFFICIENCY_VAR}=1 was set but the `claude` binary is "
            "not on PATH; install/authenticate Claude Code before running "
            "the sufficiency arm."
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"{E2E_SUFFICIENCY_VAR}=1 was set but `claude --version` did "
            "not respond within 30s."
        )

    if probe.returncode != 0:
        pytest.fail(
            f"{E2E_SUFFICIENCY_VAR}=1 was set but `claude --version` "
            f"exited {probe.returncode}: {probe.stderr.strip()[:500]}"
        )


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
    invocation re-run from its transcript) executes under. Built by the
    shared tests/harness_env.py allowlist (also used by the routing
    check), not by denylisting a copy of the whole environment: only
    PATH, HOME, TERM and LANG (the last two if present) are ever copied,
    plus JIRA_AS_TRANSPORT forced to simulation so jira-as never dials out
    to a live site regardless of what it's told.
    """
    return build_harness_env()


@pytest.fixture(scope="session")
def sufficiency_runner(
    repo_root,
    sufficiency_timeout,
    sufficiency_model,
    simulation_env,
    _sufficiency_gate,
):
    """
    Build the runner that drives Claude Code with ONLY the shipped plugin
    (skills/jira/SKILL.md) and the Bash and Skill tools installed.
    Depending on `_sufficiency_gate` guarantees the opt-in/probe runs
    first.
    """
    return SufficiencyRunner(
        plugin_dir=repo_root,
        timeout=sufficiency_timeout,
        model=sufficiency_model,
        env=simulation_env,
    )
