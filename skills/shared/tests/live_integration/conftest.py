"""
Conftest for shared live integration tests.

Re-exports fixtures for use in skill-specific live tests.
"""

from .fixtures import (
    fresh_test_issue,
    issue_helper,
    jira_client,
    jira_connection,
    jira_info,
    sbx_profile,
    search_helper,
    skip_if_cloud,
    skip_if_container,
    skip_if_no_jira,
    test_issue,
    test_project,
    test_project_key,
)

# Re-export all fixtures for pytest discovery
__all__ = [
    "jira_connection",
    "jira_client",
    "jira_info",
    "test_project_key",
    "test_project",
    "test_issue",
    "fresh_test_issue",
    "issue_helper",
    "search_helper",
    "sbx_profile",
    "skip_if_no_jira",
    "skip_if_container",
    "skip_if_cloud",
]


def pytest_terminal_summary(terminalreporter, config):
    """Keep cleanup acceptance visible even with pytest's default capture."""
    summary = getattr(config, "_sbx_cleanup_summary", None)
    if summary:
        terminalreporter.write_line(summary)
