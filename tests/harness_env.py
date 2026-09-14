"""
Shared subprocess-environment builder for the two live harnesses: the
help-only sufficiency arm (tests/e2e/) and the two-skill routing check
(skills/jira/tests/test_routing.py).

Both harnesses launch the real `claude` binary as a subprocess. Its
environment is built from an ALLOWLIST, not a denylist: copying
os.environ and removing a handful of named credential variables would
still let anything else through unexamined -- another JIRA_*/ANTHROPIC_*
variable, or an unrelated secret the operator happens to have exported.
"""

import os

# The only variables ever copied from the operator's own environment.
# PATH is required to find the `claude` and `jira-as` binaries at all.
# HOME is required for Claude Code's own authentication, whose OAuth
# credentials live under ~/.claude/ -- without it the subprocess cannot
# authenticate even though nothing Jira-related is at stake.
_REQUIRED_PASSTHROUGH_VARS = ("PATH", "HOME")

# Copied only when present; terminal/locale-sensitive output only, no
# secrets.
_OPTIONAL_PASSTHROUGH_VARS = ("TERM", "LANG")

JIRA_AS_TRANSPORT_VALUE = "simulation"


def build_harness_env() -> dict[str, str]:
    """
    Build the environment for a harness subprocess: the model's `claude`
    invocation, and the same-transport replay of any jira-as command it
    produced.

    Contains exactly: PATH and HOME (copied from the operator's own
    environment), TERM and LANG (copied only if present), and
    JIRA_AS_TRANSPORT=simulation. Never JIRA_SITE_URL, JIRA_EMAIL,
    JIRA_API_TOKEN, JIRA_DEFAULT_PROJECT, ANTHROPIC_API_KEY, or any other
    variable whose name starts with JIRA_ or ANTHROPIC_ -- including ones
    this function does not yet know the name of, which is why the
    allowlist copies only named variables instead of filtering a copy of
    the whole environment.
    """
    env: dict[str, str] = {}

    for name in _REQUIRED_PASSTHROUGH_VARS:
        if name in os.environ:
            env[name] = os.environ[name]

    for name in _OPTIONAL_PASSTHROUGH_VARS:
        if name in os.environ:
            env[name] = os.environ[name]

    env["JIRA_AS_TRANSPORT"] = JIRA_AS_TRANSPORT_VALUE

    # Defense in depth: even though only a fixed allowlist was copied
    # above, assert no credential-shaped variable ever ends up in the
    # built environment, in case a future edit widens the allowlist by
    # mistake.
    for name in env:
        if name == "JIRA_AS_TRANSPORT":
            continue
        assert not name.startswith("JIRA_") and not name.startswith("ANTHROPIC_"), (
            f"build_harness_env leaked a credential-shaped variable: {name}"
        )

    return env
